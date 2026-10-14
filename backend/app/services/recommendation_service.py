import math
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Product, InventoryBatch, Supplier, AppSetting
from app.schemas import ReorderRecommendation
from app.forecasting.pipeline import ForecastingPipeline
from app.core.config import settings


class RecommendationService:

    @staticmethod
    def generate_reorder_recommendations(
        db: Session,
        planning_horizon_days: int = 14,
        current_date: Optional[date] = None
    ) -> List[ReorderRecommendation]:
        """
        Computes deterministic inventory replenishment suggestions using lead-time demand,
        forecast daily velocity, and safety stock formulas:
        - Lead Time Demand = Daily Demand * Lead Time (days)
        - Safety Stock = ceil(Safety Factor * sqrt(Lead Time) * std_dev) or ceil(Daily Demand * Lead Time * 0.5)
        - Reorder Point = Lead Time Demand + Safety Stock
        - Target Stock = Daily Demand * (Lead Time + Planning Horizon) + Safety Stock
        - Suggested Order = max(0, Target Stock - Current Stock)
        """
        if current_date is None:
            current_date = date.today()

        products = db.query(Product).filter(Product.is_active == True).all()
        recommendations: List[ReorderRecommendation] = []

        for prod in products:
            # 1. Eligible current stock
            eligible_batches = db.query(InventoryBatch).filter(
                InventoryBatch.product_id == prod.id,
                InventoryBatch.current_quantity > 0,
                InventoryBatch.status == "active",
                (InventoryBatch.expiry_date == None) | (InventoryBatch.expiry_date >= current_date)
            ).all()
            current_stock = sum(b.current_quantity for b in eligible_batches)

            # 2. Supplier lead time
            lead_time = prod.supplier.lead_time_days if prod.supplier else settings.DEFAULT_LEAD_TIME_DAYS
            supplier_name = prod.supplier.name if prod.supplier else "Standard Supplier"

            # 3. Demand velocity from historical sales & forecasting
            sales_df = ForecastingPipeline.get_product_daily_sales(db, prod.id, lookback_days=30, end_date=current_date)
            daily_quantities = sales_df["quantity"].values
            daily_demand = float(sales_df["quantity"].mean()) if len(sales_df) > 0 else 0.0

            # 4. Safety Stock & Reorder Point Calculations
            lead_time_demand = math.ceil(daily_demand * lead_time)
            # Safety stock covers demand variability during lead time
            std_dev = float(sales_df["quantity"].std()) if len(sales_df) > 1 else (daily_demand * 0.3)
            if math.isnan(std_dev):
                std_dev = daily_demand * 0.3

            safety_factor = settings.DEFAULT_SAFETY_STOCK_FACTOR  # e.g., 1.5 (~93% service level)
            calculated_safety_stock = math.ceil(safety_factor * math.sqrt(max(1, lead_time)) * std_dev)
            safety_stock = max(int(prod.reorder_threshold * 0.5), calculated_safety_stock)

            reorder_point = max(prod.reorder_threshold, lead_time_demand + safety_stock)

            # 5. Target stock level for order horizon
            calculated_horizon_target = math.ceil(daily_demand * (lead_time + planning_horizon_days)) + safety_stock
            target_stock = max(reorder_point + int(reorder_point * 0.5), calculated_horizon_target)
            suggested_quantity = max(0, target_stock - current_stock) if current_stock <= reorder_point else 0

            # 6. Urgency classification and documented rationale
            if current_stock == 0:
                urgency = "critical"
                reason = (
                    f"Stockout detected! Current eligible stock is 0. Expected lead time is {lead_time} days. "
                    f"Immediate order of {suggested_quantity} {prod.unit} recommended."
                )
            elif current_stock <= reorder_point:
                urgency = "critical" if current_stock <= safety_stock else "moderate"
                reason = (
                    f"Current stock ({current_stock} {prod.unit}) is at or below reorder point ({reorder_point} {prod.unit}). "
                    f"Covers {math.floor(current_stock / max(0.1, daily_demand))} days of estimated demand."
                )
            else:
                urgency = "healthy"
                reason = (
                    f"Stock is healthy ({current_stock} {prod.unit}). Sufficient to cover lead time and safety buffer. "
                    f"Reorder point is {reorder_point} {prod.unit}."
                )
                suggested_quantity = 0

            recommendations.append(
                ReorderRecommendation(
                    product_id=prod.id,
                    product_name=prod.name,
                    sku=prod.sku,
                    current_stock=current_stock,
                    daily_demand_estimate=round(daily_demand, 2),
                    lead_time_days=lead_time,
                    safety_stock=safety_stock,
                    reorder_point=reorder_point,
                    suggested_order_quantity=suggested_quantity,
                    reason=reason,
                    urgency=urgency,
                    supplier_name=supplier_name
                )
            )

        # Sort: critical first, then moderate, then healthy
        priority = {"critical": 0, "moderate": 1, "healthy": 2}
        recommendations.sort(key=lambda r: (priority[r.urgency], -r.suggested_order_quantity))
        return recommendations

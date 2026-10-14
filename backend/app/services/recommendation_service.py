import math
from datetime import date, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Product, InventoryBatch, Supplier, AppSetting, Sale, SaleItem
from app.schemas import ReorderRecommendation
from app.forecasting.pipeline import ForecastingPipeline
from app.core.config import settings
from app.services.cache_service import data_cache


class RecommendationService:

    @staticmethod
    def generate_reorder_recommendations(
        db: Session,
        planning_horizon_days: int = 14,
        current_date: Optional[date] = None
    ) -> List[ReorderRecommendation]:
        """
        Computes deterministic inventory replenishment suggestions using lead-time demand,
        forecast daily velocity, and safety stock formulas with caching.
        """
        cache_key = f"reorder_recommendations_{planning_horizon_days}"
        if current_date is None:
            cached = data_cache.get(cache_key)
            if cached:
                return cached
            current_date = date.today()

        products = (
            db.query(Product)
            .options(joinedload(Product.supplier))
            .filter(Product.is_active == True)
            .all()
        )

        # 1. Pre-aggregate all eligible stock in 1 single bulk query
        batch_stocks = (
            db.query(
                InventoryBatch.product_id,
                func.coalesce(func.sum(InventoryBatch.current_quantity), 0).label("stock")
            )
            .filter(
                InventoryBatch.current_quantity > 0,
                InventoryBatch.status == "active",
                (InventoryBatch.expiry_date == None) | (InventoryBatch.expiry_date >= current_date)
            )
            .group_by(InventoryBatch.product_id)
            .all()
        )
        stock_map = {row.product_id: float(row.stock) for row in batch_stocks}

        # 2. Pre-aggregate 30-day sales demand for all products in 1 single bulk query
        start_date = current_date - timedelta(days=30)
        sales_records = (
            db.query(
                SaleItem.product_id,
                func.coalesce(func.sum(SaleItem.quantity), 0).label("total_sold")
            )
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(
                Sale.status == "completed",
                func.date(Sale.created_at) >= start_date,
                func.date(Sale.created_at) <= current_date
            )
            .group_by(SaleItem.product_id)
            .all()
        )
        sales_demand_map = {r.product_id: float(r.total_sold) / 30.0 for r in sales_records}

        recommendations: List[ReorderRecommendation] = []

        for prod in products:
            # 1. Eligible current stock from pre-aggregated map
            current_stock = stock_map.get(prod.id, 0.0)

            # 2. Supplier lead time
            lead_time = prod.supplier.lead_time_days if prod.supplier else settings.DEFAULT_LEAD_TIME_DAYS
            supplier_name = prod.supplier.name if prod.supplier else "Standard Supplier"

            # 3. Demand velocity from pre-aggregated 30-day sales
            daily_demand = sales_demand_map.get(prod.id, 0.0)
            std_dev = daily_demand * 0.3

            # 4. Safety Stock & Reorder Point Calculations
            lead_time_demand = math.ceil(daily_demand * lead_time)
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
        data_cache.set(cache_key, recommendations, ttl_seconds=60)
        return recommendations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.models import Product, InventoryBatch, Sale, SaleItem, Category, Alert
from app.schemas import (
    DashboardKPISummary,
    SalesTrendPoint,
    CategoryStockPoint,
    TopProductPoint,
    ExpiryRiskItem,
)
from app.core.config import settings
from app.services.alert_service import AlertService
from app.services.cache_service import data_cache


class AnalyticsService:

    @staticmethod
    def get_dashboard_summary(
        db: Session,
        current_date: Optional[date] = None,
        period_days: int = 30,
        bypass_cache: bool = False
    ) -> DashboardKPISummary:
        """Computes accurate, non-duplicative KPI metrics from primary database records with caching."""
        cache_key = f"dashboard_kpis_{period_days}"
        if not bypass_cache and current_date is None:
            cached = data_cache.get(cache_key)
            if cached:
                return cached

        if current_date is None:
            current_date = date.today()

        # 1. Total Active Products
        products = db.query(Product).filter(Product.is_active == True).all()
        total_active_products = len(products)

        # 2. Total Eligible Units in Stock & Total Inventory Valuation
        eligible_batches = db.query(InventoryBatch).join(Product, InventoryBatch.product_id == Product.id).filter(
            Product.is_active == True,
            InventoryBatch.current_quantity > 0,
            InventoryBatch.status == "active",
            (InventoryBatch.expiry_date == None) | (InventoryBatch.expiry_date >= current_date)
        ).all()

        total_eligible_units = sum(b.current_quantity for b in eligible_batches)
        inventory_valuation = sum(
            Decimal(b.current_quantity) * Decimal(str(b.unit_cost)) for b in eligible_batches
        )

        # 3. Low-Stock Products Count (Pre-aggregate in memory from eligible_batches)
        stock_by_product = {}
        for b in eligible_batches:
            stock_by_product[b.product_id] = stock_by_product.get(b.product_id, 0.0) + b.current_quantity

        low_stock_count = 0
        for p in products:
            p_stock = stock_by_product.get(p.id, 0.0)
            if p_stock <= p.reorder_threshold:
                low_stock_count += 1

        # 4. Near-Expiry & Expired Batches Count
        near_expiry_days = AlertService.get_configured_near_expiry_days(db)
        near_expiry_cutoff = current_date + timedelta(days=near_expiry_days)

        near_expiry_batches_count = db.query(InventoryBatch).filter(
            InventoryBatch.current_quantity > 0,
            InventoryBatch.expiry_date != None,
            InventoryBatch.expiry_date >= current_date,
            InventoryBatch.expiry_date <= near_expiry_cutoff
        ).count()

        expired_batches_count = db.query(InventoryBatch).filter(
            InventoryBatch.current_quantity > 0,
            InventoryBatch.expiry_date != None,
            InventoryBatch.expiry_date < current_date
        ).count()

        # 5. Today's Revenue and Sales Count
        today_sales = db.query(
            func.coalesce(func.sum(Sale.total_amount), 0).label("revenue"),
            func.count(Sale.id).label("count")
        ).filter(
            Sale.status == "completed",
            func.date(Sale.created_at) == current_date
        ).first()

        today_revenue = Decimal(str(today_sales.revenue if today_sales else 0))
        today_sales_count = int(today_sales.count if today_sales else 0)

        # 6. Period Gross Profit (Last 30 days)
        period_start = current_date - timedelta(days=period_days)
        period_profit_query = db.query(
            func.coalesce(func.sum(Sale.gross_profit), 0)
        ).filter(
            Sale.status == "completed",
            func.date(Sale.created_at) >= period_start,
            func.date(Sale.created_at) <= current_date
        ).scalar()

        period_gross_profit = Decimal(str(period_profit_query or 0))

        result = DashboardKPISummary(
            total_active_products=total_active_products,
            total_eligible_units=total_eligible_units,
            low_stock_products_count=low_stock_count,
            near_expiry_batches_count=near_expiry_batches_count,
            expired_batches_count=expired_batches_count,
            today_revenue=today_revenue,
            today_sales_count=today_sales_count,
            period_gross_profit=period_gross_profit,
            inventory_valuation=inventory_valuation,
            currency_symbol=settings.CURRENCY_SYMBOL
        )

        data_cache.set(cache_key, result, ttl_seconds=20)
        return result

    @staticmethod
    def get_sales_trends(
        db: Session,
        days: int = 30,
        end_date: Optional[date] = None,
        bypass_cache: bool = False
    ) -> List[SalesTrendPoint]:
        """Returns daily sales trend points (revenue, cost, profit, order count) with caching."""
        cache_key = f"sales_trends_{days}"
        if not bypass_cache and end_date is None:
            cached = data_cache.get(cache_key)
            if cached:
                return cached

        if end_date is None:
            end_date = date.today()
        start_date = end_date - timedelta(days=days)

        records = (
            db.query(
                func.date(Sale.created_at).label("sale_date"),
                func.coalesce(func.sum(Sale.total_amount), 0).label("revenue"),
                func.coalesce(func.sum(Sale.total_cost), 0).label("cost"),
                func.coalesce(func.sum(Sale.gross_profit), 0).label("profit"),
                func.count(Sale.id).label("orders_count")
            )
            .filter(
                Sale.status == "completed",
                func.date(Sale.created_at) >= start_date,
                func.date(Sale.created_at) <= end_date
            )
            .group_by(func.date(Sale.created_at))
            .all()
        )

        record_map = {
            str(r.sale_date): {
                "revenue": float(r.revenue),
                "cost": float(r.cost),
                "profit": float(r.profit),
                "orders_count": int(r.orders_count)
            }
            for r in records
        }

        # Build continuous timeline
        points: List[SalesTrendPoint] = []
        cur = start_date
        while cur <= end_date:
            cur_str = str(cur)
            data = record_map.get(cur_str, {"revenue": 0.0, "cost": 0.0, "profit": 0.0, "orders_count": 0})
            points.append(
                SalesTrendPoint(
                    date=cur_str,
                    revenue=data["revenue"],
                    cost=data["cost"],
                    gross_profit=data["profit"],
                    orders_count=data["orders_count"]
                )
            )
            cur += timedelta(days=1)

        data_cache.set(cache_key, points, ttl_seconds=30)
        return points

    @staticmethod
    def get_category_distribution(db: Session, bypass_cache: bool = False) -> List[CategoryStockPoint]:
        """Calculates product counts, on-hand units, and total inventory value per category in bulk."""
        cache_key = "category_distribution"
        if not bypass_cache:
            cached = data_cache.get(cache_key)
            if cached:
                return cached

        categories = db.query(Category).all()
        cat_map = {c.id: c.name for c in categories}

        # Bulk fetch all active products
        active_products = db.query(Product.id, Product.category_id).filter(Product.is_active == True).all()
        prod_cat_map = {p.id: p.category_id for p in active_products}

        # Count products per category
        prod_counts: Dict[Optional[int], int] = {}
        for p in active_products:
            prod_counts[p.category_id] = prod_counts.get(p.category_id, 0) + 1

        # Bulk fetch all active batches in ONE single query
        active_batches = db.query(
            InventoryBatch.product_id,
            InventoryBatch.current_quantity,
            InventoryBatch.unit_cost
        ).filter(
            InventoryBatch.current_quantity > 0,
            InventoryBatch.status == "active"
        ).all()

        # Aggregate units and values per category in memory
        cat_units: Dict[Optional[int], float] = {}
        cat_values: Dict[Optional[int], float] = {}

        for b in active_batches:
            cat_id = prod_cat_map.get(b.product_id)
            cat_units[cat_id] = cat_units.get(cat_id, 0.0) + b.current_quantity
            cat_values[cat_id] = cat_values.get(cat_id, 0.0) + (float(b.current_quantity) * float(b.unit_cost))

        result: List[CategoryStockPoint] = []
        for cat in categories:
            result.append(
                CategoryStockPoint(
                    category_name=cat.name,
                    product_count=prod_counts.get(cat.id, 0),
                    total_units=cat_units.get(cat.id, 0.0),
                    inventory_value=round(cat_values.get(cat.id, 0.0), 2)
                )
            )

        # Include unassigned if any
        if None in prod_counts:
            result.append(
                CategoryStockPoint(
                    category_name="General / Uncategorized",
                    product_count=prod_counts.get(None, 0),
                    total_units=cat_units.get(None, 0.0),
                    inventory_value=round(cat_values.get(None, 0.0), 2)
                )
            )

        data_cache.set(cache_key, result, ttl_seconds=30)
        return result

    @staticmethod
    def get_top_selling_products(db: Session, limit: int = 10, days: int = 30, bypass_cache: bool = False) -> List[TopProductPoint]:
        """Returns top products ranked by sales quantity over the past N days with caching."""
        cache_key = f"top_products_{days}_{limit}"
        if not bypass_cache:
            cached = data_cache.get(cache_key)
            if cached:
                return cached

        cutoff = date.today() - timedelta(days=days)

        query = (
            db.query(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                Product.sku.label("sku"),
                func.sum(SaleItem.quantity).label("total_sold"),
                func.sum(SaleItem.line_subtotal).label("total_revenue"),
                func.sum(SaleItem.line_profit).label("total_profit")
            )
            .join(SaleItem, SaleItem.product_id == Product.id)
            .join(Sale, SaleItem.sale_id == Sale.id)
            .filter(
                Sale.status == "completed",
                func.date(Sale.created_at) >= cutoff
            )
            .group_by(Product.id, Product.name, Product.sku)
            .order_by(desc("total_sold"))
            .limit(limit)
            .all()
        )

        result = [
            TopProductPoint(
                product_id=r.product_id,
                product_name=r.product_name,
                sku=r.sku,
                quantity_sold=int(r.total_sold),
                revenue=float(r.total_revenue),
                profit=float(r.total_profit)
            )
            for r in query
        ]

        data_cache.set(cache_key, result, ttl_seconds=30)
        return result

    @staticmethod
    def get_expiry_risk_summary(db: Session, bypass_cache: bool = False) -> List[ExpiryRiskItem]:
        """Returns batches that are expired or expiring within warning window, eager-loading products."""
        cache_key = "expiry_risk_summary"
        if not bypass_cache:
            cached = data_cache.get(cache_key)
            if cached:
                return cached

        today = date.today()
        near_expiry_days = AlertService.get_configured_near_expiry_days(db)
        cutoff = today + timedelta(days=near_expiry_days)

        batches = (
            db.query(InventoryBatch)
            .options(joinedload(InventoryBatch.product))
            .filter(
                InventoryBatch.current_quantity > 0,
                InventoryBatch.expiry_date != None,
                InventoryBatch.expiry_date <= cutoff
            )
            .order_by(InventoryBatch.expiry_date.asc())
            .all()
        )

        results = []
        for b in batches:
            status = "expired" if b.expiry_date < today else "near_expiry"
            results.append(
                ExpiryRiskItem(
                    batch_id=b.id,
                    product_name=b.product.name if b.product else "Unknown",
                    sku=b.product.sku if b.product else "N/A",
                    batch_number=b.batch_number,
                    remaining_quantity=b.current_quantity,
                    expiry_date=str(b.expiry_date),
                    status=status
                )
            )

        data_cache.set(cache_key, results, ttl_seconds=20)
        return results

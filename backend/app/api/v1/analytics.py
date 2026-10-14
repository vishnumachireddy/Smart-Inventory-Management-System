import io
import csv
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_owner
from app.models import User, Sale, Product, InventoryBatch
from app.schemas import (
    SalesTrendPoint,
    CategoryStockPoint,
    TopProductPoint,
    ExpiryRiskItem,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/sales", response_model=List[SalesTrendPoint])
def get_sales_analytics(
    days: int = Query(30, ge=7, le=365, description="Historical range in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Returns continuous daily sales, costs, and gross profit trend curves."""
    return AnalyticsService.get_sales_trends(db, days=days)


@router.get("/categories", response_model=List[CategoryStockPoint])
def get_category_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Returns inventory distribution, unit volume, and stock valuation grouped by product category."""
    return AnalyticsService.get_category_distribution(db)


@router.get("/top-products", response_model=List[TopProductPoint])
def get_top_products_analytics(
    days: int = Query(30, ge=7, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Returns top velocity products ranked by sold units and revenue contributions."""
    return AnalyticsService.get_top_selling_products(db, limit=limit, days=days)


@router.get("/expiry-risk", response_model=List[ExpiryRiskItem])
def get_expiry_risk_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Returns batches requiring immediate markdown, sale, or quarantine due to expiry proximity."""
    return AnalyticsService.get_expiry_risk_summary(db)


@router.get("/export/csv")
def export_csv_report(
    report_type: str = Query("sales", description="Export type: sales or inventory"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Exports inventory or sales records as a downloadable CSV report."""
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == "sales":
        writer.writerow(["Sale Number", "Date", "Payment Method", "Subtotal", "Discount", "Total Amount", "Gross Profit", "Status"])
        sales = db.query(Sale).order_by(Sale.created_at.desc()).all()
        for s in sales:
            writer.writerow([
                s.sale_number,
                s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else "",
                s.payment_method,
                s.subtotal,
                s.discount_amount,
                s.total_amount,
                s.gross_profit,
                s.status
            ])
        filename = f"stocksense_sales_{date.today()}.csv"

    else:
        writer.writerow(["Product Name", "SKU", "Category", "Batch Number", "Quantity Available", "Unit Cost", "Expiry Date", "Status"])
        batches = db.query(InventoryBatch).join(Product, InventoryBatch.product_id == Product.id).all()
        for b in batches:
            writer.writerow([
                b.product.name if b.product else "",
                b.product.sku if b.product else "",
                b.product.category.name if b.product and b.product.category else "",
                b.batch_number,
                b.current_quantity,
                b.unit_cost,
                b.expiry_date or "Non-perishable",
                b.status
            ])
        filename = f"stocksense_inventory_{date.today()}.csv"

    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

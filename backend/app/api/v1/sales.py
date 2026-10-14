from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.core.database import get_db
from app.core.deps import require_staff_or_owner, require_shop_owner
from app.models import Sale, SaleItem, User
from app.schemas import (
    SaleCreate,
    SaleResponse,
    SaleCancelRequest,
    SaleItemResponse,
)
from app.services.sales_service import SalesService
from app.services.alert_service import AlertService

router = APIRouter()


def enrich_sale_response(sale: Sale) -> SaleResponse:
    item_responses = []
    for item in sale.items:
        item_responses.append(
            SaleItemResponse(
                id=item.id,
                product_id=item.product_id,
                batch_id=item.batch_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                unit_cost=item.unit_cost,
                line_subtotal=item.line_subtotal,
                line_cost=item.line_cost,
                line_profit=item.line_profit,
                product_name=item.product.name if item.product else None,
                batch_number=item.batch.batch_number if item.batch else None
            )
        )

    return SaleResponse(
        id=sale.id,
        sale_number=sale.sale_number,
        subtotal=sale.subtotal,
        discount_amount=sale.discount_amount,
        total_amount=sale.total_amount,
        total_cost=sale.total_cost,
        gross_profit=sale.gross_profit,
        payment_method=sale.payment_method,
        status=sale.status,
        cancellation_reason=sale.cancellation_reason,
        user_id=sale.user_id,
        created_at=sale.created_at,
        user_name=sale.user.full_name if sale.user else None,
        items=item_responses
    )


@router.get("", response_model=List[SaleResponse])
def list_sales(
    start_date: Optional[date] = Query(None, description="Start date for filtering"),
    end_date: Optional[date] = Query(None, description="End date for filtering"),
    status: Optional[str] = Query(None, description="Filter by status: completed, cancelled"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Lists sales history with optional date range and status filters."""
    query = db.query(Sale)

    if start_date:
        query = query.filter(func.date(Sale.created_at) >= start_date)
    if end_date:
        query = query.filter(func.date(Sale.created_at) <= end_date)
    if status:
        query = query.filter(Sale.status == status)

    sales = query.order_by(desc(Sale.created_at)).offset(skip).limit(limit).all()
    return [enrich_sale_response(s) for s in sales]


@router.post("", response_model=SaleResponse)
def create_sale(
    sale_in: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """
    Creates a new sale and decrements inventory using FEFO logic.
    Rejects the transaction atomically if eligible stock is insufficient or expired.
    """
    try:
        sale = SalesService.create_sale(db=db, sale_in=sale_in, user_id=current_user.id)
        db.commit()
        db.refresh(sale)

        # Trigger alert reconciliation for any low-stock updates
        AlertService.reconcile_all_alerts(db)

        return enrich_sale_response(sale)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Sale fulfillment error: {str(e)}")


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale_detail(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves detailed sale record with line items, allocated batches, and pricing snapshots."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return enrich_sale_response(sale)


@router.post("/{sale_id}/cancel", response_model=SaleResponse)
def cancel_sale(
    sale_id: int,
    cancel_req: SaleCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Cancels a sale and restores stock into original batches via customer return entries."""
    try:
        sale = SalesService.cancel_sale(
            db=db,
            sale_id=sale_id,
            cancel_req=cancel_req,
            user_id=current_user.id
        )
        db.commit()
        db.refresh(sale)

        AlertService.reconcile_all_alerts(db)
        return enrich_sale_response(sale)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

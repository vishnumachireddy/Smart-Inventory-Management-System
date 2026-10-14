import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.core.database import get_db
from app.core.deps import require_staff_or_owner, require_shop_owner
from app.models import PurchaseReceipt, PurchaseReceiptItem, InventoryBatch, StockMovement, Product, User
from app.schemas import (
    PurchaseReceiptCreate,
    PurchaseReceiptResponse,
    PurchaseReceiptItemResponse,
)
from app.services.inventory_service import InventoryService
from app.services.alert_service import AlertService

router = APIRouter()


def enrich_purchase_response(receipt: PurchaseReceipt) -> PurchaseReceiptResponse:
    item_responses = []
    for item in receipt.items:
        item_responses.append(
            PurchaseReceiptItemResponse(
                id=item.id,
                product_id=item.product_id,
                batch_id=item.batch_id,
                batch_number=item.batch_number,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                expiry_date=item.expiry_date,
                product_name=item.product.name if item.product else None
            )
        )

    return PurchaseReceiptResponse(
        id=receipt.id,
        receipt_number=receipt.receipt_number,
        supplier_id=receipt.supplier_id,
        supplier_name=receipt.supplier.name if receipt.supplier else None,
        total_cost=receipt.total_cost,
        notes=receipt.notes,
        received_date=receipt.received_date,
        created_at=receipt.created_at,
        items=item_responses
    )


@router.get("", response_model=List[PurchaseReceiptResponse])
def list_purchases(
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Lists purchase receipt transactions."""
    query = db.query(PurchaseReceipt).options(
        joinedload(PurchaseReceipt.items).joinedload(PurchaseReceiptItem.product),
        joinedload(PurchaseReceipt.supplier)
    )
    if supplier_id:
        query = query.filter(PurchaseReceipt.supplier_id == supplier_id)

    receipts = query.order_by(desc(PurchaseReceipt.created_at)).offset(skip).limit(limit).all()
    return [enrich_purchase_response(r) for r in receipts]


@router.post("", response_model=PurchaseReceiptResponse)
def create_purchase_receipt(
    purchase_in: PurchaseReceiptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """
    Records a purchase receipt from a supplier:
    1. Generates unique receipt number.
    2. Inserts/updates inventory batches.
    3. Writes stock movement records with type 'purchase_receipt'.
    4. Reconciles inventory alerts.
    """
    receipt_number = f"RCPT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    total_cost = Decimal("0.00")
    receipt = PurchaseReceipt(
        receipt_number=receipt_number,
        supplier_id=purchase_in.supplier_id,
        notes=purchase_in.notes,
        received_date=purchase_in.received_date,
        total_cost=Decimal("0.00"),
        created_at=datetime.now(timezone.utc)
    )
    db.add(receipt)
    db.flush()

    for item_req in purchase_in.items:
        product = db.query(Product).filter(Product.id == item_req.product_id).first()
        if not product:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Product {item_req.product_id} not found")

        # Create or update Inventory Batch
        batch = InventoryBatch(
            product_id=product.id,
            supplier_id=purchase_in.supplier_id,
            batch_number=item_req.batch_number,
            quantity_received=item_req.quantity,
            current_quantity=item_req.quantity,
            received_date=purchase_in.received_date,
            expiry_date=item_req.expiry_date,
            unit_cost=item_req.unit_cost,
            status="active",
            created_at=datetime.now(timezone.utc)
        )
        db.add(batch)
        db.flush()

        # Update product purchase cost to latest cost
        product.purchase_cost = item_req.unit_cost

        # Record stock movement
        movement = StockMovement(
            product_id=product.id,
            batch_id=batch.id,
            movement_type="purchase_receipt",
            quantity=item_req.quantity,
            reference_id=receipt_number,
            reason=f"Purchase from supplier: {receipt_number}",
            user_id=current_user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(movement)

        # Record receipt item
        line_total = Decimal(item_req.quantity) * item_req.unit_cost
        total_cost += line_total

        receipt_item = PurchaseReceiptItem(
            receipt_id=receipt.id,
            product_id=product.id,
            batch_id=batch.id,
            batch_number=item_req.batch_number,
            quantity=item_req.quantity,
            unit_cost=item_req.unit_cost,
            expiry_date=item_req.expiry_date
        )
        db.add(receipt_item)

    receipt.total_cost = total_cost
    db.commit()
    db.refresh(receipt)

    AlertService.reconcile_all_alerts(db)
    return enrich_purchase_response(receipt)


@router.get("/{receipt_id}", response_model=PurchaseReceiptResponse)
def get_purchase_detail(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves single purchase receipt details."""
    receipt = db.query(PurchaseReceipt).filter(PurchaseReceipt.id == receipt_id).first()
    if not receipt:
        raise HTTPException(status_code=404, detail="Purchase receipt not found")
    return enrich_purchase_response(receipt)

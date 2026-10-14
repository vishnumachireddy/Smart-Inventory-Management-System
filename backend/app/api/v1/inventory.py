from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.core.database import get_db
from app.core.deps import require_staff_or_owner, require_shop_owner
from app.models import InventoryBatch, Product, StockMovement, User
from app.schemas import (
    BatchCreate,
    BatchResponse,
    BatchAdjustment,
    StockMovementResponse,
    ExpiryRiskItem,
)
from app.services.inventory_service import InventoryService
from app.services.alert_service import AlertService
from app.services.cache_service import data_cache
from app.core.events import broadcast_live_event

router = APIRouter()


@router.get("/batches", response_model=List[BatchResponse])
def list_batches(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    status: Optional[str] = Query(None, description="Filter by status: active, depleted, expired"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Lists batches with remaining days until expiry."""
    query = db.query(InventoryBatch)

    if product_id:
        query = query.filter(InventoryBatch.product_id == product_id)
    if status:
        query = query.filter(InventoryBatch.status == status)

    batches = query.order_by(
        InventoryBatch.expiry_date.asc().nulls_last(),
        InventoryBatch.id.asc()
    ).offset(skip).limit(limit).all()

    today = date.today()
    results = []
    for b in batches:
        days_left = (b.expiry_date - today).days if b.expiry_date else None
        results.append(
            BatchResponse(
                id=b.id,
                product_id=b.product_id,
                supplier_id=b.supplier_id,
                batch_number=b.batch_number,
                quantity_received=b.quantity_received,
                current_quantity=b.current_quantity,
                received_date=b.received_date,
                expiry_date=b.expiry_date,
                unit_cost=b.unit_cost,
                status=b.status,
                created_at=b.created_at,
                days_until_expiry=days_left
            )
        )
    return results


@router.post("/batches", response_model=BatchResponse)
def receive_inventory_batch(
    batch_in: BatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Receives stock into a new batch and logs stock movement ledger entry."""
    try:
        batch = InventoryService.receive_batch(
            db=db,
            batch_in=batch_in,
            user_id=current_user.id
        )
        db.commit()
        db.refresh(batch)

        # Reconcile alerts after receiving inventory
        AlertService.reconcile_all_alerts(db)

        # Broadcast live inventory event
        broadcast_live_event("BATCH_RECEIVED", {
            "batch_id": batch.id,
            "product_id": batch.product_id,
            "batch_number": batch.batch_number,
            "quantity": batch.quantity_received
        })

        today = date.today()
        days_left = (batch.expiry_date - today).days if batch.expiry_date else None
        return BatchResponse(
            id=batch.id,
            product_id=batch.product_id,
            supplier_id=batch.supplier_id,
            batch_number=batch.batch_number,
            quantity_received=batch.quantity_received,
            current_quantity=batch.current_quantity,
            received_date=batch.received_date,
            expiry_date=batch.expiry_date,
            unit_cost=batch.unit_cost,
            status=batch.status,
            created_at=batch.created_at,
            days_until_expiry=days_left
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batches/{batch_id}/adjust", response_model=BatchResponse)
def adjust_batch_quantity(
    batch_id: int,
    adj_in: BatchAdjustment,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Manually adjusts batch quantity (positive/negative) with auditable stock movement reason."""
    try:
        batch = InventoryService.adjust_batch_stock(
            db=db,
            batch_id=batch_id,
            adjustment_quantity=adj_in.adjustment_quantity,
            reason=adj_in.reason,
            user_id=current_user.id
        )
        db.commit()
        db.refresh(batch)

        AlertService.reconcile_all_alerts(db)

        # Broadcast live inventory event
        broadcast_live_event("STOCK_ADJUSTED", {
            "batch_id": batch.id,
            "product_id": batch.product_id,
            "current_quantity": batch.current_quantity
        })

        today = date.today()
        days_left = (batch.expiry_date - today).days if batch.expiry_date else None
        return BatchResponse(
            id=batch.id,
            product_id=batch.product_id,
            supplier_id=batch.supplier_id,
            batch_number=batch.batch_number,
            quantity_received=batch.quantity_received,
            current_quantity=batch.current_quantity,
            received_date=batch.received_date,
            expiry_date=batch.expiry_date,
            unit_cost=batch.unit_cost,
            status=batch.status,
            created_at=batch.created_at,
            days_until_expiry=days_left
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/movements", response_model=List[StockMovementResponse])
def list_stock_movements(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    movement_type: Optional[str] = Query(None, description="Filter by movement type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves immutable stock movement ledger entries with joined relations."""
    query = db.query(StockMovement).options(
        joinedload(StockMovement.product),
        joinedload(StockMovement.batch),
        joinedload(StockMovement.user)
    )

    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)

    movements = query.order_by(desc(StockMovement.created_at)).offset(skip).limit(limit).all()

    results = []
    for m in movements:
        results.append(
            StockMovementResponse(
                id=m.id,
                product_id=m.product_id,
                batch_id=m.batch_id,
                movement_type=m.movement_type,
                quantity=m.quantity,
                reference_id=m.reference_id,
                reason=m.reason,
                user_id=m.user_id,
                created_at=m.created_at,
                product_name=m.product.name if m.product else None,
                batch_number=m.batch.batch_number if m.batch else None,
                user_name=m.user.full_name if m.user else None
            )
        )
    return results


@router.get("/expiry-summary")
def get_expiry_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Returns grouped batches by expiry status with joined products and caching."""
    cache_key = "expiry_summary_grouped"
    cached = data_cache.get(cache_key)
    if cached:
        return cached

    today = date.today()
    near_expiry_days = AlertService.get_configured_near_expiry_days(db)
    near_cutoff = today + timedelta(days=near_expiry_days)

    batches = (
        db.query(InventoryBatch)
        .options(joinedload(InventoryBatch.product))
        .filter(InventoryBatch.current_quantity > 0)
        .all()
    )

    expired = []
    near_expiry = []
    healthy = []
    non_expiring = []

    for b in batches:
        item = {
            "batch_id": b.id,
            "product_id": b.product_id,
            "product_name": b.product.name if b.product else "Unknown",
            "sku": b.product.sku if b.product else "",
            "batch_number": b.batch_number,
            "current_quantity": b.current_quantity,
            "unit": b.product.unit if b.product else "unit",
            "expiry_date": str(b.expiry_date) if b.expiry_date else None,
            "days_left": (b.expiry_date - today).days if b.expiry_date else None,
        }

        if b.expiry_date is None:
            non_expiring.append(item)
        elif b.expiry_date < today:
            expired.append(item)
        elif b.expiry_date <= near_cutoff:
            near_expiry.append(item)
        else:
            healthy.append(item)

    result = {
        "expired": expired,
        "near_expiry": near_expiry,
        "healthy": healthy,
        "non_expiring": non_expiring,
        "counts": {
            "expired": len(expired),
            "near_expiry": len(near_expiry),
            "healthy": len(healthy),
            "non_expiring": len(non_expiring),
            "total_active_batches": len(batches)
        }
    }
    data_cache.set(cache_key, result, ttl_seconds=30)
    return result

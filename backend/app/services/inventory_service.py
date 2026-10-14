from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Product, InventoryBatch, StockMovement, User
from app.schemas import BatchCreate, BatchAdjustment


class InventoryService:

    @staticmethod
    def get_eligible_batches_fefo(db: Session, product_id: int, current_date: Optional[date] = None) -> List[InventoryBatch]:
        """
        Retrieves batches for a product sorted strictly by FEFO:
        1. Expired batches are EXCLUDED.
        2. Earliest expiry date first (ASC). Non-expiring batches (expiry_date IS NULL) sorted last.
        3. Tie-breaker: received_date ASC.
        4. Deterministic resolution: batch.id ASC.
        """
        if current_date is None:
            current_date = date.today()

        query = db.query(InventoryBatch).filter(
            InventoryBatch.product_id == product_id,
            InventoryBatch.current_quantity > 0,
            InventoryBatch.status == "active"
        )

        # Exclude expired batches from eligible sale allocation
        query = query.filter(
            (InventoryBatch.expiry_date == None) | (InventoryBatch.expiry_date >= current_date)
        )

        # FEFO Ordering: Non-null expiry dates ascending, NULL expiry dates last, received_date ASC, id ASC
        batches = query.order_by(
            InventoryBatch.expiry_date.asc().nulls_last(),
            InventoryBatch.received_date.asc(),
            InventoryBatch.id.asc()
        ).all()

        return batches

    @staticmethod
    def allocate_stock_fefo(
        db: Session,
        product_id: int,
        requested_quantity: int,
        reference_id: str,
        user_id: Optional[int] = None,
        reason: str = "Sale fulfillment"
    ) -> List[Tuple[InventoryBatch, int, Decimal]]:
        """
        Allocates requested stock across batches in FEFO order.
        Returns a list of tuples: (batch, allocated_quantity, batch.unit_cost)
        Decrements current_quantity atomically and creates StockMovement records.
        Raises ValueError if total eligible stock is insufficient.
        """
        if requested_quantity <= 0:
            raise ValueError("Requested allocation quantity must be positive")

        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")

        batches = InventoryService.get_eligible_batches_fefo(db, product_id)
        total_available = sum(b.current_quantity for b in batches)

        if total_available < requested_quantity:
            raise ValueError(
                f"Insufficient eligible stock for '{product.name}' (SKU: {product.sku}). "
                f"Requested: {requested_quantity}, Eligible Available: {total_available}"
            )

        allocations = []
        remaining = requested_quantity

        for batch in batches:
            if remaining <= 0:
                break

            deduct = min(batch.current_quantity, remaining)
            batch.current_quantity -= deduct
            remaining -= deduct

            if batch.current_quantity == 0:
                batch.status = "depleted"

            # Create StockMovement ledger entry
            movement = StockMovement(
                product_id=product_id,
                batch_id=batch.id,
                movement_type="sale",
                quantity=-deduct,  # Negative quantity indicates stock reduction
                reference_id=reference_id,
                reason=reason,
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(movement)
            allocations.append((batch, deduct, Decimal(str(batch.unit_cost))))

        return allocations

    @staticmethod
    def receive_batch(
        db: Session,
        batch_in: BatchCreate,
        reference_id: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> InventoryBatch:
        """Receives new inventory into a batch and logs a purchase_receipt movement."""
        product = db.query(Product).filter(Product.id == batch_in.product_id).first()
        if not product:
            raise ValueError(f"Product ID {batch_in.product_id} does not exist")

        batch = InventoryBatch(
            product_id=batch_in.product_id,
            supplier_id=batch_in.supplier_id or product.supplier_id,
            batch_number=batch_in.batch_number,
            quantity_received=batch_in.quantity_received,
            current_quantity=batch_in.quantity_received,
            received_date=batch_in.received_date,
            expiry_date=batch_in.expiry_date,
            unit_cost=batch_in.unit_cost,
            status="active"
        )
        db.add(batch)
        db.flush()

        # Record movement
        movement = StockMovement(
            product_id=batch.product_id,
            batch_id=batch.id,
            movement_type="purchase_receipt",
            quantity=batch.quantity_received,
            reference_id=reference_id or f"RCPT-{batch.batch_number}",
            reason="Inventory stock receipt",
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(movement)
        return batch

    @staticmethod
    def adjust_batch_stock(
        db: Session,
        batch_id: int,
        adjustment_quantity: int,
        reason: str,
        user_id: Optional[int] = None
    ) -> InventoryBatch:
        """Adjusts batch stock positively or negatively with full audit trail."""
        batch = db.query(InventoryBatch).filter(InventoryBatch.id == batch_id).first()
        if not batch:
            raise ValueError(f"Batch with ID {batch_id} not found")

        new_quantity = batch.current_quantity + adjustment_quantity
        if new_quantity < 0:
            raise ValueError(
                f"Adjustment cannot result in negative stock. Current: {batch.current_quantity}, Adjustment: {adjustment_quantity}"
            )

        batch.current_quantity = new_quantity
        if new_quantity == 0 and batch.status == "active":
            batch.status = "depleted"
        elif new_quantity > 0 and batch.status == "depleted":
            batch.status = "active"

        m_type = "manual_adjustment"
        if "damaged" in reason.lower():
            m_type = "damaged_stock"
        elif "expired" in reason.lower():
            m_type = "expired_removal"

        movement = StockMovement(
            product_id=batch.product_id,
            batch_id=batch.id,
            movement_type=m_type,
            quantity=adjustment_quantity,
            reason=reason,
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(movement)
        return batch

    @staticmethod
    def reconcile_expired_batches(db: Session, current_date: Optional[date] = None) -> int:
        """Scans active batches and transitions expired ones to 'expired' status."""
        if current_date is None:
            current_date = date.today()

        expired_batches = db.query(InventoryBatch).filter(
            InventoryBatch.expiry_date != None,
            InventoryBatch.expiry_date < current_date,
            InventoryBatch.status == "active"
        ).all()

        count = len(expired_batches)
        for b in expired_batches:
            b.status = "expired"
        return count

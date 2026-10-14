import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Sale, SaleItem, Product, InventoryBatch, StockMovement
from app.schemas import SaleCreate, SaleCancelRequest
from app.services.inventory_service import InventoryService


class SalesService:

    @staticmethod
    def generate_sale_number() -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_id = uuid.uuid4().hex[:6].upper()
        return f"SAL-{date_str}-{short_id}"

    @staticmethod
    def create_sale(db: Session, sale_in: SaleCreate, user_id: Optional[int] = None) -> Sale:
        """
        Processes a new sale transaction:
        1. Validates requested products.
        2. Allocates stock using FEFO batch sequencing.
        3. Records snapshot pricing, costs, and movement ledger records.
        4. Calculates financial metrics: Revenue, COGS, and Gross Profit.
        5. Atomically commits the entire transaction.
        """
        if not sale_in.items:
            raise ValueError("Sale must contain at least one item")

        sale_number = SalesService.generate_sale_number()

        subtotal = Decimal("0.00")
        total_cost = Decimal("0.00")
        created_items: List[SaleItem] = []

        for item_req in sale_in.items:
            product = db.query(Product).filter(Product.id == item_req.product_id).first()
            if not product:
                raise ValueError(f"Product with ID {item_req.product_id} not found")

            # Determine sale price: use override if specified, otherwise catalog price
            unit_price = item_req.unit_price if item_req.unit_price is not None else Decimal(str(product.selling_price))

            # Perform FEFO allocation across candidate batches
            allocations = InventoryService.allocate_stock_fefo(
                db=db,
                product_id=product.id,
                requested_quantity=item_req.quantity,
                reference_id=sale_number,
                user_id=user_id,
                reason="Customer POS Sale"
            )

            # Record each batch allocation as an auditable SaleItem line
            for batch, qty, batch_unit_cost in allocations:
                line_subtotal = Decimal(qty) * unit_price
                line_cost = Decimal(qty) * batch_unit_cost
                line_profit = line_subtotal - line_cost

                subtotal += line_subtotal
                total_cost += line_cost

                sale_item = SaleItem(
                    product_id=product.id,
                    batch_id=batch.id,
                    quantity=qty,
                    unit_price=unit_price,
                    unit_cost=batch_unit_cost,
                    line_subtotal=line_subtotal,
                    line_cost=line_cost,
                    line_profit=line_profit
                )
                created_items.append(sale_item)

        discount = sale_in.discount_amount or Decimal("0.00")
        total_amount = max(Decimal("0.00"), subtotal - discount)
        gross_profit = total_amount - total_cost

        sale = Sale(
            sale_number=sale_number,
            subtotal=subtotal,
            discount_amount=discount,
            total_amount=total_amount,
            total_cost=total_cost,
            gross_profit=gross_profit,
            payment_method=sale_in.payment_method,
            status="completed",
            user_id=user_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(sale)
        db.flush()

        for item in created_items:
            item.sale_id = sale.id
            db.add(item)

        db.flush()
        return sale

    @staticmethod
    def cancel_sale(
        db: Session,
        sale_id: int,
        cancel_req: SaleCancelRequest,
        user_id: Optional[int] = None
    ) -> Sale:
        """
        Reverses a completed sale through an auditable return workflow:
        1. Validates status is 'completed'.
        2. Restores returned quantities back into their original batches.
        3. Creates reverse StockMovement ledger entries with type 'customer_return'.
        4. Updates sale status to 'cancelled'.
        """
        sale = db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise ValueError(f"Sale with ID {sale_id} not found")
        if sale.status == "cancelled":
            raise ValueError(f"Sale {sale.sale_number} is already cancelled")

        # Reverse each sale item line
        for item in sale.items:
            batch = db.query(InventoryBatch).filter(InventoryBatch.id == item.batch_id).first()
            if batch:
                batch.current_quantity += item.quantity
                if batch.status == "depleted" and batch.current_quantity > 0:
                    batch.status = "active"

            # Create reversal movement
            reversal_movement = StockMovement(
                product_id=item.product_id,
                batch_id=item.batch_id,
                movement_type="customer_return",
                quantity=item.quantity,  # Positive quantity restores stock
                reference_id=sale.sale_number,
                reason=f"Sale Cancellation: {cancel_req.cancellation_reason}",
                user_id=user_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(reversal_movement)

        sale.status = "cancelled"
        sale.cancellation_reason = cancel_req.cancellation_reason
        return sale

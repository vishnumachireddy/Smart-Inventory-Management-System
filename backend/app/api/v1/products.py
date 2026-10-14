from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from app.core.database import get_db
from app.core.deps import require_staff_or_owner, require_shop_owner
from app.models import Product, InventoryBatch, Category, Supplier, User
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductDetailResponse,
    BatchResponse,
)
from app.services.inventory_service import InventoryService
from app.services.alert_service import AlertService

router = APIRouter()


def enrich_product_response(product: Product, db: Session, today: date) -> ProductResponse:
    eligible_batches = db.query(InventoryBatch).filter(
        InventoryBatch.product_id == product.id,
        InventoryBatch.current_quantity > 0,
        InventoryBatch.status == "active",
        (InventoryBatch.expiry_date == None) | (InventoryBatch.expiry_date >= today)
    ).all()

    total_stock = sum(b.current_quantity for b in eligible_batches)

    if total_stock == 0:
        stock_status = "out_of_stock"
    elif total_stock <= product.reorder_threshold:
        stock_status = "low_stock"
    else:
        stock_status = "in_stock"

    return ProductResponse(
        id=product.id,
        name=product.name,
        sku=product.sku,
        barcode=product.barcode,
        category_id=product.category_id,
        supplier_id=product.supplier_id,
        description=product.description,
        unit=product.unit,
        purchase_cost=product.purchase_cost,
        selling_price=product.selling_price,
        reorder_threshold=product.reorder_threshold,
        is_active=product.is_active,
        created_at=product.created_at,
        updated_at=product.updated_at,
        total_stock=total_stock,
        category_name=product.category.name if product.category else None,
        supplier_name=product.supplier.name if product.supplier else None,
        stock_status=stock_status
    )


@router.get("", response_model=List[ProductResponse])
def list_products(
    search: Optional[str] = Query(None, description="Search by name, SKU, or barcode"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    stock_status: Optional[str] = Query(None, description="Filter by status: in_stock, low_stock, out_of_stock"),
    sort_by: str = Query("name", description="Field to sort by: name, sku, price, stock"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Lists products with calculated dynamic stock levels and multi-criteria filters."""
    query = db.query(Product).filter(Product.is_active == True)

    if search:
        search_filter = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(search_filter),
                Product.sku.ilike(search_filter),
                Product.barcode.ilike(search_filter)
            )
        )

    if category_id:
        query = query.filter(Product.category_id == category_id)

    today = date.today()
    products = query.all()

    # Enrich stock records
    enriched = [enrich_product_response(p, db, today) for p in products]

    # Filter by dynamic stock status if requested
    if stock_status:
        enriched = [p for p in enriched if p.stock_status == stock_status]

    # Sort
    reverse = (sort_order.lower() == "desc")
    if sort_by == "stock":
        enriched.sort(key=lambda x: x.total_stock, reverse=reverse)
    elif sort_by == "price":
        enriched.sort(key=lambda x: x.selling_price, reverse=reverse)
    elif sort_by == "sku":
        enriched.sort(key=lambda x: x.sku.lower(), reverse=reverse)
    else:
        enriched.sort(key=lambda x: x.name.lower(), reverse=reverse)

    return enriched[skip: skip + limit]


@router.post("", response_model=ProductResponse)
def create_product(
    prod_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Creates a new product with duplicate SKU validation."""
    existing_sku = db.query(Product).filter(Product.sku == prod_in.sku.strip()).first()
    if existing_sku:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{prod_in.sku}' already exists"
        )

    product = Product(**prod_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)

    # Reconcile alerts for newly created product
    AlertService.reconcile_all_alerts(db)

    return enrich_product_response(product, db, date.today())


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves product details along with its individual inventory batches."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    today = date.today()
    base_response = enrich_product_response(product, db, today)

    # Fetch all batches for this product
    batches = db.query(InventoryBatch).filter(
        InventoryBatch.product_id == product.id
    ).order_by(
        InventoryBatch.expiry_date.asc().nulls_last(),
        InventoryBatch.id.asc()
    ).all()

    batch_responses = []
    for b in batches:
        days_left = (b.expiry_date - today).days if b.expiry_date else None
        batch_responses.append(
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

    return ProductDetailResponse(
        **base_response.model_dump(),
        batches=batch_responses
    )


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    prod_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Updates product information."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if prod_in.sku is not None and prod_in.sku != product.sku:
        existing = db.query(Product).filter(Product.sku == prod_in.sku, Product.id != product_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU code is already used by another product")

    for field, val in prod_in.model_dump(exclude_unset=True).items():
        setattr(product, field, val)

    db.commit()
    db.refresh(product)

    AlertService.reconcile_all_alerts(db)
    return enrich_product_response(product, db, date.today())


@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Soft deletes or deactivates product to protect historical financial and stock auditability."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_active = False
    db.commit()
    return {"message": f"Product '{product.name}' deactivated successfully"}

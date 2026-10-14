from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc, asc, func

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
from app.services.cache_service import data_cache

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
    """Lists products with single-pass bulk batch stock aggregation and high-speed in-memory caching."""
    cache_key = "products_all_enriched"
    enriched: Optional[List[ProductResponse]] = data_cache.get(cache_key)

    if enriched is None:
        today = date.today()
        # 1. Fetch all products with category and supplier joined in 1 single query
        products = (
            db.query(Product)
            .options(
                joinedload(Product.category),
                joinedload(Product.supplier)
            )
            .filter(Product.is_active == True)
            .all()
        )

        # 2. Bulk aggregate eligible stock per product in 1 query
        batch_stocks = (
            db.query(
                InventoryBatch.product_id,
                func.coalesce(func.sum(InventoryBatch.current_quantity), 0).label("stock")
            )
            .filter(
                InventoryBatch.current_quantity > 0,
                InventoryBatch.status == "active",
                (InventoryBatch.expiry_date == None) | (InventoryBatch.expiry_date >= today)
            )
            .group_by(InventoryBatch.product_id)
            .all()
        )
        stock_map = {row.product_id: float(row.stock) for row in batch_stocks}

        # 3. Construct responses in-memory
        enriched = []
        for p in products:
            total_stock = stock_map.get(p.id, 0.0)
            if total_stock == 0:
                p_status = "out_of_stock"
            elif total_stock <= p.reorder_threshold:
                p_status = "low_stock"
            else:
                p_status = "in_stock"

            enriched.append(
                ProductResponse(
                    id=p.id,
                    name=p.name,
                    sku=p.sku,
                    barcode=p.barcode,
                    category_id=p.category_id,
                    supplier_id=p.supplier_id,
                    description=p.description,
                    unit=p.unit,
                    purchase_cost=p.purchase_cost,
                    selling_price=p.selling_price,
                    reorder_threshold=p.reorder_threshold,
                    is_active=p.is_active,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                    total_stock=total_stock,
                    category_name=p.category.name if p.category else None,
                    supplier_name=p.supplier.name if p.supplier else None,
                    stock_status=p_status
                )
            )
        data_cache.set(cache_key, enriched, ttl_seconds=30)

    # In-memory filtering & sorting
    results = list(enriched)

    if search:
        s = search.strip().lower()
        results = [
            p for p in results
            if s in p.name.lower() or s in p.sku.lower() or (p.barcode and s in p.barcode.lower())
        ]

    if category_id:
        results = [p for p in results if p.category_id == category_id]

    if stock_status:
        results = [p for p in results if p.stock_status == stock_status]

    reverse = (sort_order.lower() == "desc")
    if sort_by == "stock":
        results.sort(key=lambda x: x.total_stock, reverse=reverse)
    elif sort_by == "price":
        results.sort(key=lambda x: x.selling_price, reverse=reverse)
    elif sort_by == "sku":
        results.sort(key=lambda x: x.sku.lower(), reverse=reverse)
    else:
        results.sort(key=lambda x: x.name.lower(), reverse=reverse)

    return results[skip: skip + limit]


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
    data_cache.invalidate("products_all_enriched")

    return enrich_product_response(product, db, date.today())


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves product details along with its individual inventory batches."""
    product = db.query(Product).options(
        joinedload(Product.category),
        joinedload(Product.supplier)
    ).filter(Product.id == product_id).first()
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
    data_cache.invalidate("products_all_enriched")
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
    data_cache.invalidate("products_all_enriched")
    return {"message": f"Product '{product.name}' deactivated successfully"}

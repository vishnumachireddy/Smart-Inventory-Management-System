from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.deps import require_staff_or_owner, require_shop_owner
from app.models import Category, Product, User
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter()


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves all product categories with product counts."""
    categories = db.query(Category).order_by(Category.name.asc()).all()
    results = []
    for cat in categories:
        prod_count = db.query(Product).filter(Product.category_id == cat.id, Product.is_active == True).count()
        results.append(
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                description=cat.description,
                created_at=cat.created_at,
                product_count=prod_count
            )
        )
    return results


@router.post("", response_model=CategoryResponse)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Creates a new category (Shop Owner only)."""
    existing = db.query(Category).filter(Category.name.ilike(cat_in.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    cat = Category(name=cat_in.name, description=cat_in.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        created_at=cat.created_at,
        product_count=0
    )


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    cat_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Updates an existing category (Shop Owner only)."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")

    if cat_in.name is not None:
        duplicate = db.query(Category).filter(Category.name.ilike(cat_in.name), Category.id != category_id).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="Category name already in use")
        cat.name = cat_in.name
    if cat_in.description is not None:
        cat.description = cat_in.description

    db.commit()
    db.refresh(cat)
    prod_count = db.query(Product).filter(Product.category_id == cat.id, Product.is_active == True).count()
    return CategoryResponse(
        id=cat.id,
        name=cat.name,
        description=cat.description,
        created_at=cat.created_at,
        product_count=prod_count
    )


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Deletes a category, setting associated products' category to null."""
    cat = db.query(Category).filter(Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return {"message": f"Category '{cat.name}' deleted successfully"}

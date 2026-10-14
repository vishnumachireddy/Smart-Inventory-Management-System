from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_staff_or_owner, require_shop_owner
from app.models import Supplier, User
from app.schemas import SupplierCreate, SupplierUpdate, SupplierResponse

router = APIRouter()


@router.get("", response_model=List[SupplierResponse])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves all registered suppliers."""
    return db.query(Supplier).order_by(Supplier.name.asc()).all()


@router.post("", response_model=SupplierResponse)
def create_supplier(
    supp_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Creates a new supplier (Shop Owner only)."""
    supp = Supplier(**supp_in.model_dump())
    db.add(supp)
    db.commit()
    db.refresh(supp)
    return supp


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_owner)
):
    """Retrieves single supplier details."""
    supp = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supp:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supp


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supp_in: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Updates supplier information (Shop Owner only)."""
    supp = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supp:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for field, value in supp_in.model_dump(exclude_unset=True).items():
        setattr(supp, field, value)

    db.commit()
    db.refresh(supp)
    return supp


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner)
):
    """Deletes a supplier (Shop Owner only)."""
    supp = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supp:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(supp)
    db.commit()
    return {"message": f"Supplier '{supp.name}' deleted successfully"}

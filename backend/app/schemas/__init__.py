from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from decimal import Decimal


# --- Base Response Config ---
class SchemaBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    full_name: str
    email: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    role: str = Field(default="staff")  # "shop_owner" or "staff"


class UserResponse(SchemaBase):
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


# --- Category Schemas ---
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryResponse(CategoryBase, SchemaBase):
    id: int
    created_at: datetime
    product_count: Optional[int] = 0


# --- Supplier Schemas ---
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: int = Field(default=7, ge=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lead_time_days: Optional[int] = Field(None, ge=1)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SupplierResponse(SupplierBase, SchemaBase):
    id: int
    created_at: datetime


# --- Batch Schemas ---
class BatchBase(BaseModel):
    batch_number: str = Field(..., min_length=1)
    quantity_received: int = Field(..., ge=1)
    received_date: date
    expiry_date: Optional[date] = None
    unit_cost: Decimal = Field(..., ge=0)
    supplier_id: Optional[int] = None


class BatchCreate(BatchBase):
    product_id: int


class BatchAdjustment(BaseModel):
    adjustment_quantity: int  # can be positive or negative
    reason: str


class BatchResponse(SchemaBase):
    id: int
    product_id: int
    supplier_id: Optional[int] = None
    batch_number: str
    quantity_received: int
    current_quantity: int
    received_date: date
    expiry_date: Optional[date] = None
    unit_cost: Decimal
    status: str
    created_at: datetime
    days_until_expiry: Optional[int] = None


# --- Product Schemas ---
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    description: Optional[str] = None
    unit: str = Field(default="unit")
    purchase_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    selling_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    reorder_threshold: int = Field(default=10, ge=0)
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    purchase_cost: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)
    reorder_threshold: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase, SchemaBase):
    id: int
    created_at: datetime
    updated_at: datetime
    total_stock: int = 0
    category_name: Optional[str] = None
    supplier_name: Optional[str] = None
    stock_status: str = "in_stock"  # in_stock, low_stock, out_of_stock


class ProductDetailResponse(ProductResponse):
    batches: List[BatchResponse] = []


# --- Stock Movement Schemas ---
class StockMovementCreate(BaseModel):
    product_id: int
    batch_id: Optional[int] = None
    movement_type: str  # adjustment, damaged_stock, expired_removal, etc.
    quantity: int
    reason: Optional[str] = None
    reference_id: Optional[str] = None


class StockMovementResponse(SchemaBase):
    id: int
    product_id: int
    batch_id: Optional[int] = None
    movement_type: str
    quantity: int
    reference_id: Optional[str] = None
    reason: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    product_name: Optional[str] = None
    batch_number: Optional[str] = None
    user_name: Optional[str] = None


# --- Sales Schemas ---
class SaleItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class SaleCreate(BaseModel):
    items: List[SaleItemRequest] = Field(..., min_length=1)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    payment_method: str = Field(default="cash")


class SaleItemResponse(SchemaBase):
    id: int
    product_id: int
    batch_id: int
    quantity: int
    unit_price: Decimal
    unit_cost: Decimal
    line_subtotal: Decimal
    line_cost: Decimal
    line_profit: Decimal
    product_name: Optional[str] = None
    batch_number: Optional[str] = None


class SaleResponse(SchemaBase):
    id: int
    sale_number: str
    subtotal: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    total_cost: Decimal
    gross_profit: Decimal
    payment_method: str
    status: str
    cancellation_reason: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    user_name: Optional[str] = None
    items: List[SaleItemResponse] = []


class SaleCancelRequest(BaseModel):
    cancellation_reason: str = Field(..., min_length=3)


# --- Purchase Schemas ---
class PurchaseItemRequest(BaseModel):
    product_id: int
    batch_number: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_cost: Decimal = Field(..., ge=0)
    expiry_date: Optional[date] = None


class PurchaseReceiptCreate(BaseModel):
    supplier_id: int
    received_date: date
    notes: Optional[str] = None
    items: List[PurchaseItemRequest] = Field(..., min_length=1)


class PurchaseReceiptItemResponse(SchemaBase):
    id: int
    product_id: int
    batch_id: Optional[int] = None
    batch_number: str
    quantity: int
    unit_cost: Decimal
    expiry_date: Optional[date] = None
    product_name: Optional[str] = None


class PurchaseReceiptResponse(SchemaBase):
    id: int
    receipt_number: str
    supplier_id: int
    supplier_name: Optional[str] = None
    total_cost: Decimal
    notes: Optional[str] = None
    received_date: date
    created_at: datetime
    items: List[PurchaseReceiptItemResponse] = []


# --- Alert Schemas ---
class AlertResponse(SchemaBase):
    id: int
    product_id: int
    batch_id: Optional[int] = None
    alert_type: str
    severity: str
    message: str
    is_read: bool
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None
    product_name: Optional[str] = None
    sku: Optional[str] = None
    batch_number: Optional[str] = None
    current_stock: Optional[int] = None
    expiry_date: Optional[date] = None


# --- Demand Forecasting Schemas ---
class ForecastDataPoint(BaseModel):
    date: str
    predicted_demand: float
    is_forecast: bool = True
    actual_demand: Optional[float] = None


class ForecastResponse(BaseModel):
    product_id: int
    product_name: str
    sku: str
    model_type: str
    horizon_days: int
    historical_periods: int
    daily_average_demand: float
    mae: Optional[float] = None
    rmse: Optional[float] = None
    forecast: List[ForecastDataPoint] = []
    insights: str


class ModelEvaluationResponse(BaseModel):
    baseline_moving_average: Dict[str, Any]
    advanced_random_forest: Optional[Dict[str, Any]] = None
    comparison_summary: str


# --- Reorder Recommendation Schemas ---
class ReorderRecommendation(BaseModel):
    product_id: int
    product_name: str
    sku: str
    current_stock: int
    daily_demand_estimate: float
    lead_time_days: int
    safety_stock: int
    reorder_point: int
    suggested_order_quantity: int
    reason: str
    urgency: str  # critical, moderate, healthy
    supplier_name: Optional[str] = None


# --- Dashboard & Analytics Schemas ---
class DashboardKPISummary(BaseModel):
    total_active_products: int
    total_eligible_units: int
    low_stock_products_count: int
    near_expiry_batches_count: int
    expired_batches_count: int
    today_revenue: Decimal
    today_sales_count: int
    period_gross_profit: Decimal
    inventory_valuation: Decimal
    currency_symbol: str = "₹"


class SalesTrendPoint(BaseModel):
    date: str
    revenue: float
    cost: float
    gross_profit: float
    orders_count: int


class CategoryStockPoint(BaseModel):
    category_name: str
    product_count: int
    total_units: int
    inventory_value: float


class TopProductPoint(BaseModel):
    product_id: int
    product_name: str
    sku: str
    quantity_sold: int
    revenue: float
    profit: float


class ExpiryRiskItem(BaseModel):
    batch_id: int
    product_name: str
    sku: str
    batch_number: str
    remaining_quantity: int
    expiry_date: str
    status: str  # expired, near_expiry


# --- App Settings Schemas ---
class AppSettingResponse(SchemaBase):
    id: int
    key: str
    value: str
    description: Optional[str] = None
    updated_at: datetime


class AppSettingUpdate(BaseModel):
    value: str
    description: Optional[str] = None

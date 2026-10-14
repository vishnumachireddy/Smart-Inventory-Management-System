from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Numeric, Text, Float, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="staff", nullable=False)  # "shop_owner" or "staff"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sales = relationship("Sale", back_populates="user")
    movements = relationship("StockMovement", back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    products = relationship("Product", back_populates="category")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    contact_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    lead_time_days = Column(Integer, default=7, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    products = relationship("Product", back_populates="supplier")
    batches = relationship("InventoryBatch", back_populates="supplier")
    purchases = relationship("PurchaseReceipt", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    barcode = Column(String(100), index=True, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    unit = Column(String(50), default="unit", nullable=False)  # pcs, kg, litre, pack, bottle, etc.
    purchase_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    selling_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    reorder_threshold = Column(Integer, default=10, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")
    batches = relationship("InventoryBatch", back_populates="product", cascade="all, delete-orphan")
    movements = relationship("StockMovement", back_populates="product")
    sale_items = relationship("SaleItem", back_populates="product")
    purchase_items = relationship("PurchaseReceiptItem", back_populates="product")
    alerts = relationship("Alert", back_populates="product", cascade="all, delete-orphan")
    forecasts = relationship("ForecastRecord", back_populates="product", cascade="all, delete-orphan")


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    batch_number = Column(String(100), index=True, nullable=False)
    quantity_received = Column(Integer, nullable=False)
    current_quantity = Column(Integer, default=0, nullable=False, index=True)
    received_date = Column(Date, nullable=False)
    expiry_date = Column(Date, nullable=True, index=True)  # Nullable for non-perishable goods
    unit_cost = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), default="active", nullable=False, index=True)  # active, depleted, expired, quarantined
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    product = relationship("Product", back_populates="batches")
    supplier = relationship("Supplier", back_populates="batches")
    movements = relationship("StockMovement", back_populates="batch")
    sale_items = relationship("SaleItem", back_populates="batch")
    alerts = relationship("Alert", back_populates="batch")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    movement_type = Column(String(50), index=True, nullable=False)  
    # purchase_receipt, sale, customer_return, supplier_return, damaged_stock, expired_removal, manual_adjustment
    quantity = Column(Integer, nullable=False)  # Positive for addition, negative for reduction
    reference_id = Column(String(100), nullable=True, index=True)  # e.g. sale_number or receipt_number
    reason = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    product = relationship("Product", back_populates="movements")
    batch = relationship("InventoryBatch", back_populates="movements")
    user = relationship("User", back_populates="movements")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_number = Column(String(100), unique=True, index=True, nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    gross_profit = Column(Numeric(12, 2), default=0.00, nullable=False)
    payment_method = Column(String(50), default="cash", nullable=False)  # cash, card, upi, credit
    status = Column(String(50), default="completed", nullable=False, index=True)  # completed, cancelled
    cancellation_reason = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    user = relationship("User", back_populates="sales")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id", ondelete="RESTRICT"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    line_subtotal = Column(Numeric(12, 2), nullable=False)
    line_cost = Column(Numeric(12, 2), nullable=False)
    line_profit = Column(Numeric(12, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")
    batch = relationship("InventoryBatch", back_populates="sale_items")


class PurchaseReceipt(Base):
    __tablename__ = "purchase_receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String(100), unique=True, index=True, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False, index=True)
    total_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    notes = Column(Text, nullable=True)
    received_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    supplier = relationship("Supplier", back_populates="purchases")
    items = relationship("PurchaseReceiptItem", back_populates="receipt", cascade="all, delete-orphan")


class PurchaseReceiptItem(Base):
    __tablename__ = "purchase_receipt_items"

    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("purchase_receipts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id", ondelete="SET NULL"), nullable=True, index=True)
    batch_number = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    expiry_date = Column(Date, nullable=True)

    receipt = relationship("PurchaseReceipt", back_populates="items")
    product = relationship("Product", back_populates="purchase_items")
    batch = relationship("InventoryBatch")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("inventory_batches.id", ondelete="CASCADE"), nullable=True, index=True)
    alert_type = Column(String(50), index=True, nullable=False)  # low_stock, out_of_stock, near_expiry, expired
    severity = Column(String(50), default="warning", nullable=False)  # info, warning, critical
    message = Column(Text, nullable=False)
    relevant_stock_quantity = Column(Float, nullable=True)
    relevant_expiry_date = Column(Date, nullable=True)
    status = Column(String(50), default="active", nullable=False, index=True)  # active, acknowledged, resolved, dismissed
    is_read = Column(Boolean, default=False, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    first_detected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_checked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    deduplication_key = Column(String(255), unique=True, index=True, nullable=True)

    product = relationship("Product", back_populates="alerts")
    batch = relationship("InventoryBatch", back_populates="alerts")


InventoryAlert = Alert


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    shop_id = Column(String(100), default="default_shop", nullable=False, index=True)
    recipient_emails = Column(Text, default="", nullable=False)
    enabled = Column(Boolean, default=False, nullable=False)
    report_frequency = Column(String(50), default="daily", nullable=False)  # daily, weekly, both
    scheduled_time = Column(String(20), default="08:00", nullable=False)
    timezone = Column(String(100), default="Asia/Kolkata", nullable=False)
    categories = Column(String(255), default="near_expiry,low_stock,out_of_stock,sales_summary", nullable=False)
    include_empty_reports = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")


class ScheduledJobRun(Base):
    __tablename__ = "scheduled_job_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(100), index=True, nullable=False, default="daily_inventory_check")
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="running", nullable=False, index=True)  # running, success, failed, skipped
    summary_counts = Column(Text, nullable=True)  # JSON-encoded summary counts
    error_details = Column(Text, nullable=True)

    email_logs = relationship("EmailDeliveryLog", back_populates="scheduled_run")


class EmailDeliveryLog(Base):
    __tablename__ = "email_delivery_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(100), index=True, nullable=False)  # daily_inventory, weekly_summary, test_email
    recipient = Column(String(255), nullable=False, index=True)
    scheduled_run_id = Column(Integer, ForeignKey("scheduled_job_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    idempotency_key = Column(String(255), unique=True, index=True, nullable=False)
    attempt_count = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="queued", nullable=False, index=True)  # queued, attempted, accepted, failed, disabled
    provider_message_id = Column(String(255), nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    scheduled_run = relationship("ScheduledJobRun", back_populates="email_logs")


class DailyInventorySnapshot(Base):
    __tablename__ = "daily_inventory_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    reporting_date = Column(Date, unique=True, index=True, nullable=False)
    near_expiry_count = Column(Integer, default=0, nullable=False)
    low_stock_count = Column(Integer, default=0, nullable=False)
    out_of_stock_count = Column(Integer, default=0, nullable=False)
    total_stock_value = Column(Numeric(12, 2), default=0.00, nullable=False)
    sales_count = Column(Integer, default=0, nullable=False)
    revenue = Column(Numeric(12, 2), default=0.00, nullable=False)
    gross_profit = Column(Numeric(12, 2), default=0.00, nullable=False)
    summary_text = Column(Text, nullable=True)
    generation_timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ForecastRecord(Base):
    __tablename__ = "forecast_records"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False, index=True)
    horizon_days = Column(Integer, default=7, nullable=False)
    predicted_demand = Column(Float, nullable=False)
    model_type = Column(String(50), default="moving_average", nullable=False)  # moving_average, random_forest
    mae = Column(Float, nullable=True)
    rmse = Column(Float, nullable=True)
    historical_periods = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    product = relationship("Product", back_populates="forecasts")


class AppSetting(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

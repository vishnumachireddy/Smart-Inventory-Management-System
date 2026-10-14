export interface User {
  id: number;
  email: string;
  full_name: string;
  role: 'shop_owner' | 'staff';
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  role: 'shop_owner' | 'staff';
  user_id: number;
  full_name: string;
  email: string;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  product_count?: number;
}

export interface Supplier {
  id: number;
  name: string;
  contact_name?: string;
  email?: string;
  phone?: string;
  address?: string;
  lead_time_days: number;
  latitude?: number;
  longitude?: number;
  created_at: string;
}

export interface Batch {
  id: number;
  product_id: number;
  supplier_id?: number;
  batch_number: string;
  quantity_received: number;
  current_quantity: number;
  received_date: string;
  expiry_date?: string;
  unit_cost: number;
  status: 'active' | 'depleted' | 'expired' | 'quarantined';
  created_at: string;
  days_until_expiry?: number;
}

export interface Product {
  id: number;
  name: string;
  sku: string;
  barcode?: string;
  category_id?: number;
  supplier_id?: number;
  description?: string;
  unit: string;
  purchase_cost: number;
  selling_price: number;
  reorder_threshold: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  total_stock: number;
  category_name?: string;
  supplier_name?: string;
  stock_status: 'in_stock' | 'low_stock' | 'out_of_stock';
  batches?: Batch[];
}

export interface StockMovement {
  id: number;
  product_id: number;
  batch_id?: number;
  movement_type: string;
  quantity: number;
  reference_id?: string;
  reason?: string;
  user_id?: number;
  created_at: string;
  product_name?: string;
  batch_number?: string;
  user_name?: string;
}

export interface SaleItem {
  id: number;
  product_id: number;
  batch_id: number;
  quantity: number;
  unit_price: number;
  unit_cost: number;
  line_subtotal: number;
  line_cost: number;
  line_profit: number;
  product_name?: string;
  batch_number?: string;
}

export interface Sale {
  id: number;
  sale_number: string;
  subtotal: number;
  discount_amount: number;
  total_amount: number;
  total_cost: number;
  gross_profit: number;
  payment_method: string;
  status: 'completed' | 'cancelled';
  cancellation_reason?: string;
  user_id?: number;
  created_at: string;
  user_name?: string;
  items: SaleItem[];
}

export interface PurchaseItem {
  id: number;
  product_id: number;
  batch_id?: number;
  batch_number: string;
  quantity: number;
  unit_cost: number;
  expiry_date?: string;
  product_name?: string;
}

export interface PurchaseReceipt {
  id: number;
  receipt_number: string;
  supplier_id: number;
  supplier_name?: string;
  total_cost: number;
  notes?: string;
  received_date: string;
  created_at: string;
  items: PurchaseItem[];
}

export interface Alert {
  id: number;
  product_id: number;
  batch_id?: number;
  alert_type: 'low_stock' | 'near_expiry' | 'expired';
  severity: 'info' | 'warning' | 'critical';
  message: string;
  is_read: boolean;
  is_resolved: boolean;
  created_at: string;
  resolved_at?: string;
  product_name?: string;
  sku?: string;
  batch_number?: string;
  current_stock?: number;
  expiry_date?: string;
}

export interface ForecastPoint {
  date: string;
  predicted_demand: number;
  is_forecast: boolean;
  actual_demand?: number;
}

export interface ForecastResult {
  product_id: number;
  product_name: string;
  sku: string;
  model_type: string;
  horizon_days: number;
  historical_periods: number;
  daily_average_demand: number;
  mae?: number;
  rmse?: number;
  forecast: ForecastPoint[];
  insights: string;
}

export interface ReorderRecommendation {
  product_id: number;
  product_name: string;
  sku: string;
  current_stock: number;
  daily_demand_estimate: number;
  lead_time_days: number;
  safety_stock: number;
  reorder_point: number;
  suggested_order_quantity: number;
  reason: string;
  urgency: 'critical' | 'moderate' | 'healthy';
  supplier_name?: string;
}

export interface DashboardKPIs {
  total_active_products: number;
  total_eligible_units: number;
  low_stock_products_count: number;
  near_expiry_batches_count: number;
  expired_batches_count: number;
  today_revenue: number;
  today_sales_count: number;
  period_gross_profit: number;
  inventory_valuation: number;
  currency_symbol: string;
}

export interface SalesTrendPoint {
  date: string;
  revenue: number;
  cost: number;
  gross_profit: number;
  orders_count: number;
}

export interface CategoryStockPoint {
  category_name: string;
  product_count: number;
  total_units: number;
  inventory_value: number;
}

export interface TopProductPoint {
  product_id: number;
  product_name: string;
  sku: string;
  quantity_sold: number;
  revenue: number;
  profit: number;
}

export interface AppSetting {
  id: number;
  key: string;
  value: string;
  description?: string;
  updated_at: string;
}

export interface ExpiryRiskItem {
  batch_id: number;
  product_name: string;
  sku: string;
  batch_number: string;
  remaining_quantity: number;
  expiry_date: string;
  status: 'expired' | 'near_expiry';
}

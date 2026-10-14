import axios from 'axios';
import {
  AuthResponse,
  Category,
  Supplier,
  Product,
  Batch,
  StockMovement,
  Sale,
  PurchaseReceipt,
  Alert,
  ForecastResult,
  ReorderRecommendation,
  DashboardKPIs,
  SalesTrendPoint,
  CategoryStockPoint,
  TopProductPoint,
  AppSetting,
  User,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('stocksense_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && window.location.pathname !== '/login') {
      localStorage.removeItem('stocksense_token');
      localStorage.removeItem('stocksense_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// Typed API Client helpers
export const apiClient = {
  // Auth
  login: (data: { email: string; password: string }) =>
    api.post<AuthResponse>('/auth/login', data),
  register: (data: any) =>
    api.post<User>('/auth/register', data),
  getMe: () =>
    api.get<User>('/auth/me'),

  // Users
  getUsers: () =>
    api.get<User[]>('/users'),
  createUser: (data: any) =>
    api.post<User>('/users', data),
  updateUser: (id: number, data: any) =>
    api.put<User>(`/users/${id}`, data),

  // Categories
  getCategories: () =>
    api.get<Category[]>('/categories'),
  createCategory: (data: { name: string; description?: string }) =>
    api.post<Category>('/categories', data),
  updateCategory: (id: number, data: { name?: string; description?: string }) =>
    api.put<Category>(`/categories/${id}`, data),
  deleteCategory: (id: number) =>
    api.delete(`/categories/${id}`),

  // Suppliers
  getSuppliers: () =>
    api.get<Supplier[]>('/suppliers'),
  getSupplier: (id: number) =>
    api.get<Supplier>(`/suppliers/${id}`),
  createSupplier: (data: any) =>
    api.post<Supplier>('/suppliers', data),
  updateSupplier: (id: number, data: any) =>
    api.put<Supplier>(`/suppliers/${id}`, data),
  deleteSupplier: (id: number) =>
    api.delete(`/suppliers/${id}`),

  // Products
  getProducts: (params?: any) =>
    api.get<Product[]>('/products', { params }),
  getProduct: (id: number) =>
    api.get<Product>(`/products/${id}`),
  createProduct: (data: any) =>
    api.post<Product>('/products', data),
  updateProduct: (id: number, data: any) =>
    api.put<Product>(`/products/${id}`, data),
  deleteProduct: (id: number) =>
    api.delete(`/products/${id}`),

  // Inventory & Batches
  getBatches: (params?: any) =>
    api.get<Batch[]>('/inventory/batches', { params }),
  receiveBatch: (data: any) =>
    api.post<Batch>('/inventory/batches', data),
  adjustBatch: (id: number, data: { adjustment_quantity: number; reason: string }) =>
    api.post<Batch>(`/inventory/batches/${id}/adjust`, data),
  getMovements: (params?: any) =>
    api.get<StockMovement[]>('/inventory/movements', { params }),
  getExpirySummary: () =>
    api.get<any>('/inventory/expiry-summary'),

  // Sales
  getSales: (params?: any) =>
    api.get<Sale[]>('/sales', { params }),
  getSale: (id: number) =>
    api.get<Sale>(`/sales/${id}`),
  createSale: (data: { items: { product_id: number; quantity: number; unit_price?: number }[]; discount_amount?: number; payment_method?: string }) =>
    api.post<Sale>('/sales', data),
  cancelSale: (id: number, data: { cancellation_reason: string }) =>
    api.post<Sale>(`/sales/${id}/cancel`, data),

  // Purchases
  getPurchases: (params?: any) =>
    api.get<PurchaseReceipt[]>('/purchases', { params }),
  getPurchase: (id: number) =>
    api.get<PurchaseReceipt>(`/purchases/${id}`),
  createPurchase: (data: any) =>
    api.post<PurchaseReceipt>('/purchases', data),

  // Forecasting
  getForecast: (productId: number, params?: any) =>
    api.get<ForecastResult>(`/forecasts/${productId}`, { params }),
  getAllForecasts: (params?: any) =>
    api.get<ForecastResult[]>('/forecasts', { params }),
  getModelEvaluation: (params?: any) =>
    api.get<any>('/forecasts/evaluation', { params }),

  // Recommendations
  getReorderRecommendations: (params?: any) =>
    api.get<ReorderRecommendation[]>('/recommendations/reorder', { params }),

  // Alerts
  getAlerts: (params?: any) =>
    api.get<Alert[]>('/alerts', { params }),
  reconcileAlerts: () =>
    api.post('/alerts/reconcile'),
  markAlertRead: (id: number) =>
    api.patch<Alert>(`/alerts/${id}/read`),
  markAlertResolved: (id: number) =>
    api.patch<Alert>(`/alerts/${id}/resolve`),

  // Dashboard & Analytics
  getDashboardSummary: () =>
    api.get<DashboardKPIs>('/dashboard/summary'),
  getSalesAnalytics: (days?: number) =>
    api.get<SalesTrendPoint[]>('/analytics/sales', { params: { days } }),
  getCategoryAnalytics: () =>
    api.get<CategoryStockPoint[]>('/analytics/categories'),
  getTopProductsAnalytics: (days?: number, limit?: number) =>
    api.get<TopProductPoint[]>('/analytics/top-products', { params: { days, limit } }),
  getExpiryRiskAnalytics: () =>
    api.get<any[]>('/analytics/expiry-risk'),
  exportCsv: (reportType: string) =>
    api.get(`/analytics/export/csv?report_type=${reportType}`, { responseType: 'blob' }),

  // Settings
  getSettings: () =>
    api.get<AppSetting[]>('/settings'),
  updateSetting: (key: string, data: { value: string; description?: string }) =>
    api.put<AppSetting>(`/settings/${key}`, data),
};

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Package,
  Layers,
  AlertTriangle,
  ClockAlert,
  Skull,
  IndianRupee,
  TrendingUp,
  CircleDollarSign,
  ArrowUpRight,
  Download,
  RefreshCw,
  Bell,
} from 'lucide-react';
import { LoginAlertModal } from '../components/alerts/LoginAlertModal';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { apiClient } from '../api/client';
import { useWebSocket } from '../context/WebSocketContext';
import {
  DashboardKPIs,
  SalesTrendPoint,
  CategoryStockPoint,
  TopProductPoint,
  ExpiryRiskItem,
} from '../types';
import { StatCard, Badge, LoadingSpinner } from '../components/common';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4', '#64748b'];

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isConnected, liveKpis, requestKpis, lastEvent } = useWebSocket();
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<DashboardKPIs | null>(liveKpis);
  const [trends, setTrends] = useState<SalesTrendPoint[]>([]);
  const [categories, setCategories] = useState<CategoryStockPoint[]>([]);
  const [topProducts, setTopProducts] = useState<TopProductPoint[]>([]);
  const [expiryRisk, setExpiryRisk] = useState<ExpiryRiskItem[]>([]);
  const [trendDays, setTrendDays] = useState<number>(30);
  const [isAlertModalOpen, setIsAlertModalOpen] = useState<boolean>(false);
  const [liveNotice, setLiveNotice] = useState<string | null>(null);

  // Instantly adopt live KPIs as soon as WebSocket receives them
  useEffect(() => {
    if (liveKpis) {
      setKpis(liveKpis);
      setLoading(false);
    }
  }, [liveKpis]);

  useEffect(() => {
    // Automatically trigger on first authenticated dashboard entry per session
    const seenInSession = sessionStorage.getItem('stocksense_login_alert_modal_seen');
    if (!seenInSession) {
      setIsAlertModalOpen(true);
      sessionStorage.setItem('stocksense_login_alert_modal_seen', 'true');
    }
  }, []);

  const fetchDashboardData = async (silent = false) => {
    if (!silent && !kpis) setLoading(true);
    try {
      const bundleRes = await apiClient.getDashboardBundle(trendDays);
      const data = bundleRes.data;

      setKpis(data.kpis);
      setTrends(data.trends);
      setCategories(data.categories);
      setTopProducts(data.top_products);
      setExpiryRisk(data.expiry_risk);
    } catch (err) {
      console.error('Failed to load dashboard metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [trendDays]);

  // React to live real-time WebSocket events from other clients or POS
  useEffect(() => {
    if (!lastEvent) return;
    if (
      lastEvent.type === 'SALE_COMPLETED' ||
      lastEvent.type === 'BATCH_RECEIVED' ||
      lastEvent.type === 'STOCK_ADJUSTED' ||
      lastEvent.type === 'SALE_CANCELLED'
    ) {
      setLiveNotice(`Live event: ${lastEvent.type.replace('_', ' ')}`);
      fetchDashboardData(true); // Silent background refresh
      const t = setTimeout(() => setLiveNotice(null), 4000);
      return () => clearTimeout(t);
    }
  }, [lastEvent]);

  const handleExportCsv = async (type: string) => {
    try {
      const res = await apiClient.exportCsv(type);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `stocksense_${type}_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  if (loading && !kpis) {
    return <LoadingSpinner label="Loading live store metrics..." />;
  }

  const sym = kpis?.currency_symbol || '₹';

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Executive Dashboard</h1>
            <div
              title={isConnected ? 'Connected to live WebSocket feed' : 'Connecting WebSocket...'}
              className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border transition-all ${
                isConnected
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
                }`}
              ></span>
              <span>{isConnected ? 'Live WebSocket Feed' : 'Connecting WS...'}</span>
            </div>
            {liveNotice && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-100 text-indigo-800 animate-bounce">
                ⚡ {liveNotice}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time batch inventory, FEFO movement metrics, and instant WebSocket demand synchronization
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsAlertModalOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-lg text-xs font-semibold shadow-sm transition-colors"
          >
            <Bell className="w-3.5 h-3.5 text-amber-600 animate-pulse" />
            <span>Review Alerts</span>
          </button>
          <button
            onClick={() => {
              requestKpis();
              fetchDashboardData();
            }}
            title="Instant WebSocket & DB Sync"
            className="flex items-center space-x-1.5 px-3 py-2 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg text-xs font-medium shadow-sm transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5 text-indigo-600" />
            <span>Live Sync</span>
          </button>
          <button
            onClick={() => handleExportCsv('sales')}
            className="flex items-center space-x-1.5 px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Sales CSV</span>
          </button>
        </div>
      </div>

      {/* 8 Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Catalog"
          value={kpis?.total_active_products || 0}
          subtitle="Registered products"
          icon={Package}
          variant="default"
          onClick={() => navigate('/products')}
        />
        <StatCard
          title="Eligible Stock"
          value={kpis?.total_eligible_units || 0}
          subtitle="Sellable units on hand"
          icon={Layers}
          variant="info"
          onClick={() => navigate('/batches')}
        />
        <StatCard
          title="Low Stock Items"
          value={kpis?.low_stock_products_count || 0}
          subtitle="At or below reorder threshold"
          icon={AlertTriangle}
          variant="warning"
          onClick={() => navigate('/products?stock_status=low_stock')}
        />
        <StatCard
          title="Near Expiry Batches"
          value={kpis?.near_expiry_batches_count || 0}
          subtitle="Expiring within 30 days"
          icon={ClockAlert}
          variant="danger"
          onClick={() => navigate('/expiry')}
        />
        <StatCard
          title="Expired Batches"
          value={kpis?.expired_batches_count || 0}
          subtitle="Unsold stock to quarantine"
          icon={Skull}
          variant="danger"
          onClick={() => navigate('/expiry')}
        />
        <StatCard
          title="Today's Revenue"
          value={`${sym}${Number(kpis?.today_revenue || 0).toLocaleString()}`}
          subtitle={`${kpis?.today_sales_count || 0} orders completed`}
          icon={IndianRupee}
          variant="success"
          onClick={() => navigate('/sales')}
        />
        <StatCard
          title="Period Gross Profit"
          value={`${sym}${Number(kpis?.period_gross_profit || 0).toLocaleString()}`}
          subtitle="Revenue minus COGS"
          icon={TrendingUp}
          variant="success"
          onClick={() => navigate('/analytics')}
        />
        <StatCard
          title="Inventory Valuation"
          value={`${sym}${Number(kpis?.inventory_valuation || 0).toLocaleString()}`}
          subtitle="Calculated at unit costs"
          icon={CircleDollarSign}
          variant="info"
          onClick={() => navigate('/batches')}
        />
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sales & Revenue Trend (2 cols) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-100 gap-2">
            <div>
              <h3 className="text-base font-bold text-slate-900">Revenue & Gross Profit Performance</h3>
              <p className="text-xs text-slate-500">Historical continuous trend over time</p>
            </div>
            <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg">
              {[7, 14, 30, 60].map((d) => (
                <button
                  key={d}
                  onClick={() => setTrendDays(d)}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-md transition-colors ${
                    trendDays === d ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {d}D
                </button>
              ))}
            </div>
          </div>

          <div className="h-72 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorProfit" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickFormatter={(v) => v.slice(5)} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip
                  formatter={(val: any) => [`${sym}${Number(val).toFixed(2)}`, '']}
                  labelFormatter={(lbl) => `Date: ${lbl}`}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
                <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorRev)" />
                <Area type="monotone" dataKey="gross_profit" name="Gross Profit" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorProfit)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category Stock Distribution (1 col) */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Inventory by Category</h3>
            <p className="text-xs text-slate-500">Stock distribution across store aisles</p>
          </div>

          <div className="h-64 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categories}
                  dataKey="total_units"
                  nameKey="category_name"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={3}
                >
                  {categories.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(val: any, name: any) => [`${val} units`, name]}
                  contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-1.5 mt-2 max-h-32 overflow-y-auto pr-1">
            {categories.map((c, i) => (
              <div key={c.category_name} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2 truncate">
                  <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: COLORS[i % COLORS.length] }}></span>
                  <span className="text-slate-600 truncate">{c.category_name}</span>
                </div>
                <span className="font-semibold text-slate-800">{c.total_units} units</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row: Top Selling Products and Expiry Risk */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Velocity Products */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Top Velocity Products</h3>
              <p className="text-xs text-slate-500">Highest volume items sold in the last 30 days</p>
            </div>
            <button
              onClick={() => navigate('/analytics')}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
            >
              <span>View all</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 mt-2">
            {topProducts.map((p, idx) => (
              <div key={p.product_id} className="py-3 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3">
                  <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-600 font-bold flex items-center justify-center text-[10px]">
                    {idx + 1}
                  </span>
                  <div>
                    <h5 className="font-semibold text-slate-900">{p.product_name}</h5>
                    <p className="text-[11px] text-slate-400">SKU: {p.sku}</p>
                  </div>
                </div>
                <div className="text-right">
                  <span className="font-bold text-slate-800">{p.quantity_sold} sold</span>
                  <p className="text-[11px] text-emerald-600 font-medium">+{sym}{p.profit.toFixed(0)} profit</p>
                </div>
              </div>
            ))}
            {topProducts.length === 0 && (
              <p className="text-xs text-slate-400 py-6 text-center">No sales recorded yet.</p>
            )}
          </div>
        </div>

        {/* Expiry Risk Radar */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-base font-bold text-slate-900">Expiry Risk Radar</h3>
              <p className="text-xs text-slate-500">Batches requiring markdown or disposal</p>
            </div>
            <button
              onClick={() => navigate('/expiry')}
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 flex items-center space-x-1"
            >
              <span>Manage expiry</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 mt-2">
            {expiryRisk.slice(0, 5).map((b) => (
              <div key={b.batch_id} className="py-3 flex items-center justify-between text-xs">
                <div>
                  <h5 className="font-semibold text-slate-900">{b.product_name}</h5>
                  <p className="text-[11px] text-slate-400">Batch: {b.batch_number} • Expiry: {b.expiry_date}</p>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-slate-700">{b.remaining_quantity} units</span>
                  <Badge variant={b.status === 'expired' ? 'danger' : 'warning'}>
                    {b.status === 'expired' ? 'Expired' : 'Near Expiry'}
                  </Badge>
                </div>
              </div>
            ))}
            {expiryRisk.length === 0 && (
              <p className="text-xs text-slate-400 py-6 text-center">No critical expiry risks detected.</p>
            )}
          </div>
        </div>
      </div>

      {/* Login Alert Modal Dialog */}
      <LoginAlertModal
        isOpen={isAlertModalOpen}
        onClose={() => setIsAlertModalOpen(false)}
        onRemindLater={() => {
          setIsAlertModalOpen(false);
          sessionStorage.removeItem('stocksense_login_alert_modal_seen');
        }}
      />
    </div>
  );
};

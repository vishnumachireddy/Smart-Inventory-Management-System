import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  Download,
  IndianRupee,
  Layers,
  Calendar,
  BarChart2,
  PieChart as PieIcon,
  RefreshCw,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area,
} from 'recharts';
import { apiClient } from '../api/client';
import { SalesTrendPoint, CategoryStockPoint, TopProductPoint } from '../types';
import { LoadingSpinner } from '../components/common';

export const AnalyticsReports: React.FC = () => {
  const [trends, setTrends] = useState<SalesTrendPoint[]>([]);
  const [categories, setCategories] = useState<CategoryStockPoint[]>([]);
  const [topProducts, setTopProducts] = useState<TopProductPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [rangeDays, setRangeDays] = useState(30);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [trendRes, catRes, topRes] = await Promise.all([
        apiClient.getSalesAnalytics(rangeDays),
        apiClient.getCategoryAnalytics(),
        apiClient.getTopProductsAnalytics(rangeDays, 10),
      ]);
      setTrends(trendRes.data);
      setCategories(catRes.data);
      setTopProducts(topRes.data);
    } catch (err) {
      console.error('Analytics load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, [rangeDays]);

  const handleExport = async (type: 'sales' | 'inventory') => {
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

  // Financial aggregates
  const totalRevenue = trends.reduce((acc, t) => acc + t.revenue, 0);
  const totalCost = trends.reduce((acc, t) => acc + t.cost, 0);
  const totalGrossProfit = trends.reduce((acc, t) => acc + t.gross_profit, 0);
  const overallMargin = totalRevenue > 0 ? ((totalGrossProfit / totalRevenue) * 100).toFixed(1) : '0';

  if (loading && trends.length === 0) {
    return <LoadingSpinner label="Compiling financial analytics..." />;
  }

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Analytics & Business Reports</h1>
          <p className="text-xs text-slate-500 mt-1">
            Analyze profit margins, sales velocity, category valuation, and download CSV audit sheets
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => handleExport('sales')}
            className="flex items-center space-x-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-indigo-600" />
            <span>Export Sales CSV</span>
          </button>
          <button
            onClick={() => handleExport('inventory')}
            className="flex items-center space-x-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Inventory Valuation</span>
          </button>
        </div>
      </div>

      {/* Aggregate Financial Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            {rangeDays}-Day Gross Revenue
          </span>
          <span className="text-2xl font-extrabold text-slate-900 mt-1 block font-mono">
            ₹{totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Cost of Goods Sold (COGS)
          </span>
          <span className="text-2xl font-extrabold text-slate-700 mt-1 block font-mono">
            ₹{totalCost.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Gross Profit Generated
          </span>
          <span className="text-2xl font-extrabold text-emerald-600 mt-1 block font-mono">
            ₹{totalGrossProfit.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block">
            Store Gross Margin
          </span>
          <span className="text-2xl font-extrabold text-indigo-600 mt-1 block font-mono">
            {overallMargin}%
          </span>
        </div>
      </div>

      {/* Chart: Revenue vs Cost vs Profit */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-100 gap-2">
          <div>
            <h3 className="text-base font-bold text-slate-900">Revenue, COGS & Profit Curves</h3>
            <p className="text-xs text-slate-500">Breakdown of gross takings and historical batch acquisition costs</p>
          </div>
          <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-lg">
            {[7, 14, 30, 60].map((d) => (
              <button
                key={d}
                onClick={() => setRangeDays(d)}
                className={`px-3 py-1 text-xs font-bold rounded-md transition-colors ${
                  rangeDays === d ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600'
                }`}
              >
                {d} Days
              </button>
            ))}
          </div>
        </div>

        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="areaRev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="areaCost" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="areaProfit" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="date" stroke="#94a3b8" fontSize={11} tickFormatter={(v) => v.slice(5)} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                formatter={(val: any) => [`₹${Number(val).toFixed(2)}`, '']}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderRadius: '8px',
                  border: '1px solid #e2e8f0',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
              <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#6366f1" strokeWidth={2} fill="url(#areaRev)" />
              <Area type="monotone" dataKey="cost" name="COGS (Cost)" stroke="#94a3b8" strokeWidth={1.5} fill="url(#areaCost)" />
              <Area type="monotone" dataKey="gross_profit" name="Gross Profit" stroke="#10b981" strokeWidth={2} fill="url(#areaProfit)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Category Valuation Bar Chart */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="pb-3 border-b border-slate-100">
          <h3 className="text-base font-bold text-slate-900">Category Inventory Capital Allocation</h3>
          <p className="text-xs text-slate-500">Total monetary valuation of current stock held by category</p>
        </div>

        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={categories} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="category_name" stroke="#94a3b8" fontSize={10} interval={0} angle={-15} textAnchor="end" />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, 'Valuation']}
                contentStyle={{ backgroundColor: '#ffffff', borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
              />
              <Bar dataKey="inventory_value" name="Inventory Value (₹)" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

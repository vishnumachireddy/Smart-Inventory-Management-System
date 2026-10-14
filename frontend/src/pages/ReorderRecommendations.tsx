import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  AlertTriangle,
  Clock,
  ShieldCheck,
  RefreshCw,
  Info,
  CheckCircle2,
  HelpCircle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { ReorderRecommendation } from '../types';
import { Badge, LoadingSpinner, EmptyState } from '../components/common';

export const ReorderRecommendations: React.FC = () => {
  const [recommendations, setRecommendations] = useState<ReorderRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [urgencyFilter, setUrgencyFilter] = useState<string>('');
  const [horizon, setHorizon] = useState<number>(14);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getReorderRecommendations({ horizon_days: horizon });
      setRecommendations(res.data);
    } catch (err) {
      console.error('Failed to load replenishment suggestions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecommendations();
  }, [horizon]);

  const filtered = recommendations.filter((r) => {
    if (!urgencyFilter) return true;
    return r.urgency === urgencyFilter;
  });

  const criticalCount = recommendations.filter((r) => r.urgency === 'critical').length;
  const moderateCount = recommendations.filter((r) => r.urgency === 'moderate').length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Smart Reorder Recommendations</h1>
          <p className="text-xs text-slate-500 mt-1">
            Data-backed inventory replenishment engine based on lead-time demand, forecast velocity, and safety buffers
          </p>
        </div>
        <button
          onClick={fetchRecommendations}
          className="flex items-center space-x-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Recalculate Reorder Points</span>
        </button>
      </div>

      {/* Formula Documentation Card */}
      <div className="p-4 rounded-2xl bg-indigo-50/50 border border-indigo-200 text-xs text-slate-700 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start space-x-3">
          <Info className="w-5 h-5 text-indigo-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-slate-900">Documented Replenishment Formulas:</h4>
            <p className="text-[11px] text-slate-600 mt-0.5">
              • <strong>Reorder Point</strong> = (Expected Daily Demand × Supplier Lead Time) + Safety Stock Buffer
              <br />• <strong>Suggested Order</strong> = max(0, Target Stock Level - Current Available Stock)
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2 shrink-0">
          <span className="text-[11px] font-semibold text-slate-500">Order Horizon:</span>
          <select
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
            className="px-2.5 py-1 text-xs rounded-lg border border-slate-300 bg-white font-semibold"
          >
            <option value={7}>7 Days (Fast Turn)</option>
            <option value={14}>14 Days (Standard)</option>
            <option value={30}>30 Days (Monthly)</option>
          </select>
        </div>
      </div>

      {/* Quick Filter Buttons */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setUrgencyFilter('')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
            urgencyFilter === '' ? 'bg-slate-900 text-white' : 'bg-white border border-slate-200 text-slate-700'
          }`}
        >
          All Items ({recommendations.length})
        </button>
        <button
          onClick={() => setUrgencyFilter('critical')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
            urgencyFilter === 'critical'
              ? 'bg-rose-600 text-white'
              : 'bg-white border border-rose-200 text-rose-700 hover:bg-rose-50'
          }`}
        >
          Critical Attention ({criticalCount})
        </button>
        <button
          onClick={() => setUrgencyFilter('moderate')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
            urgencyFilter === 'moderate'
              ? 'bg-amber-600 text-white'
              : 'bg-white border border-amber-200 text-amber-700 hover:bg-amber-50'
          }`}
        >
          Moderate Reorder ({moderateCount})
        </button>
        <button
          onClick={() => setUrgencyFilter('healthy')}
          className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-colors ${
            urgencyFilter === 'healthy'
              ? 'bg-emerald-600 text-white'
              : 'bg-white border border-emerald-200 text-emerald-700 hover:bg-emerald-50'
          }`}
        >
          Healthy Stock
        </button>
      </div>

      {/* Recommendations Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingSpinner label="Running reorder optimization algorithms..." />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="No Items Require Reordering"
            description="All eligible inventory levels are currently above their calculated reorder points."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Product & SKU</th>
                  <th className="px-6 py-3.5">Current Stock</th>
                  <th className="px-6 py-3.5">Daily Demand</th>
                  <th className="px-6 py-3.5">Lead Time</th>
                  <th className="px-6 py-3.5">Reorder Point</th>
                  <th className="px-6 py-3.5">Suggested Order</th>
                  <th className="px-6 py-3.5">Urgency</th>
                  <th className="px-6 py-3.5">Underlying Rationale</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filtered.map((r) => (
                  <tr key={r.product_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900">{r.product_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        SKU: {r.sku} • {r.supplier_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-sm">
                      <span className={r.current_stock === 0 ? 'text-rose-600' : 'text-slate-900'}>
                        {r.current_stock}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono font-medium">
                      {r.daily_demand_estimate} <span className="text-[10px] text-slate-400">/day</span>
                    </td>
                    <td className="px-6 py-4 font-mono">{r.lead_time_days} days</td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-800">
                      {r.reorder_point}{' '}
                      <span className="text-[10px] font-normal text-slate-400">
                        (safety: {r.safety_stock})
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono font-extrabold text-sm">
                      <span
                        className={
                          r.suggested_order_quantity > 0 ? 'text-indigo-600' : 'text-slate-400'
                        }
                      >
                        {r.suggested_order_quantity > 0 ? `+${r.suggested_order_quantity}` : '0'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <Badge
                        variant={
                          r.urgency === 'critical'
                            ? 'danger'
                            : r.urgency === 'moderate'
                            ? 'warning'
                            : 'success'
                        }
                      >
                        {r.urgency}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-slate-500 max-w-xs text-[11px] leading-relaxed">
                      {r.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

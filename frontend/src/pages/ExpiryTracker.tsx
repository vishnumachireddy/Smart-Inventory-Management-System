import React, { useState, useEffect } from 'react';
import {
  ClockAlert,
  Skull,
  ShieldCheck,
  Package,
  AlertTriangle,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Badge, LoadingSpinner, EmptyState } from '../components/common';
import { useAuth } from '../context/AuthContext';

export const ExpiryTracker: React.FC = () => {
  const { isOwner } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'expired' | 'near_expiry' | 'healthy' | 'non_expiring'>(
    'near_expiry'
  );

  const fetchExpiryData = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getExpirySummary();
      setData(res.data);
      // Auto-switch to expired if expired items exist
      if (res.data.counts.expired > 0) {
        setActiveTab('expired');
      }
    } catch (err) {
      console.error('Failed to load expiry summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpiryData();
  }, []);

  const handleQuarantineExpired = async (batchId: number, qty: number, name: string) => {
    if (!window.confirm(`Quarantine and remove all ${qty} expired units of ${name}?`)) return;
    try {
      await apiClient.adjustBatch(batchId, {
        adjustment_quantity: -qty,
        reason: 'Expired stock removal & quarantine',
      });
      fetchExpiryData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove expired stock');
    }
  };

  if (loading && !data) {
    return <LoadingSpinner label="Auditing batch expiry dates..." />;
  }

  const counts = data?.counts || { expired: 0, near_expiry: 0, healthy: 0, non_expiring: 0 };
  const currentItems = data ? data[activeTab] || [] : [];

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Expiry Date Tracker</h1>
          <p className="text-xs text-slate-500 mt-1">
            Enforce FEFO safety, detect near-expiry windows, and safely quarantine expired stock
          </p>
        </div>
        <button
          onClick={fetchExpiryData}
          className="flex items-center space-x-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Expiry Audit</span>
        </button>
      </div>

      {/* Tabs / Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <button
          onClick={() => setActiveTab('expired')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeTab === 'expired'
              ? 'bg-rose-50 border-rose-300 ring-2 ring-rose-500/20'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-rose-600">
              Expired Stock
            </span>
            <Skull className="w-4 h-4 text-rose-500" />
          </div>
          <span className="text-2xl font-extrabold text-slate-900 mt-1 block">{counts.expired}</span>
          <p className="text-[11px] text-rose-600 mt-0.5 font-medium">Must be quarantined</p>
        </button>

        <button
          onClick={() => setActiveTab('near_expiry')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeTab === 'near_expiry'
              ? 'bg-amber-50 border-amber-300 ring-2 ring-amber-500/20'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-amber-600">
              Near Expiry
            </span>
            <ClockAlert className="w-4 h-4 text-amber-500" />
          </div>
          <span className="text-2xl font-extrabold text-slate-900 mt-1 block">{counts.near_expiry}</span>
          <p className="text-[11px] text-amber-600 mt-0.5 font-medium">Within 30 days window</p>
        </button>

        <button
          onClick={() => setActiveTab('healthy')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeTab === 'healthy'
              ? 'bg-emerald-50 border-emerald-300 ring-2 ring-emerald-500/20'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-600">
              Healthy Stock
            </span>
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <span className="text-2xl font-extrabold text-slate-900 mt-1 block">{counts.healthy}</span>
          <p className="text-[11px] text-emerald-600 mt-0.5 font-medium">&gt; 30 days remaining</p>
        </button>

        <button
          onClick={() => setActiveTab('non_expiring')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeTab === 'non_expiring'
              ? 'bg-indigo-50 border-indigo-300 ring-2 ring-indigo-500/20'
              : 'bg-white border-slate-200 hover:border-slate-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600">
              Non-Perishable
            </span>
            <Package className="w-4 h-4 text-indigo-500" />
          </div>
          <span className="text-2xl font-extrabold text-slate-900 mt-1 block">{counts.non_expiring}</span>
          <p className="text-[11px] text-indigo-600 mt-0.5 font-medium">No expiry threshold</p>
        </button>
      </div>

      {/* Grouped Batches Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 capitalize">
              {activeTab.replace('_', ' ')} Inventory Batches
            </h3>
            <p className="text-xs text-slate-500">
              {activeTab === 'expired'
                ? 'These batches are automatically barred from POS sales to prevent customer shrinkage.'
                : activeTab === 'near_expiry'
                ? 'Prioritized first in sales under the First Expired, First Out (FEFO) business rule.'
                : 'Batches with safe longevity horizons.'}
            </p>
          </div>
          <Badge
            variant={
              activeTab === 'expired'
                ? 'danger'
                : activeTab === 'near_expiry'
                ? 'warning'
                : activeTab === 'healthy'
                ? 'success'
                : 'neutral'
            }
          >
            {currentItems.length} Batches
          </Badge>
        </div>

        {currentItems.length === 0 ? (
          <EmptyState
            title="No Batches in this Category"
            description="There are currently zero inventory batches in this expiry status category."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Product & SKU</th>
                  <th className="px-6 py-3.5">Batch / Lot Code</th>
                  <th className="px-6 py-3.5">Remaining Stock</th>
                  <th className="px-6 py-3.5">Expiry Date</th>
                  <th className="px-6 py-3.5">Days Left</th>
                  {activeTab === 'expired' && isOwner && (
                    <th className="px-6 py-3.5 text-right">Quarantine Action</th>
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {currentItems.map((b: any) => (
                  <tr key={b.batch_id} className="hover:bg-slate-50/80">
                    <td className="px-6 py-4">
                      <div className="font-bold text-slate-900">{b.product_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">SKU: {b.sku}</div>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-800">{b.batch_number}</td>
                    <td className="px-6 py-4">
                      <span className="font-bold text-slate-900 text-sm">{b.current_quantity}</span>{' '}
                      <span className="text-slate-400 text-[11px]">{b.unit}</span>
                    </td>
                    <td className="px-6 py-4 font-semibold text-slate-800">
                      {b.expiry_date || <span className="text-slate-400 font-normal">Non-expiring</span>}
                    </td>
                    <td className="px-6 py-4">
                      {typeof b.days_left === 'number' ? (
                        <span
                          className={`font-semibold ${
                            b.days_left < 0
                              ? 'text-rose-600'
                              : b.days_left <= 7
                              ? 'text-rose-500 font-bold'
                              : b.days_left <= 30
                              ? 'text-amber-600'
                              : 'text-emerald-600'
                          }`}
                        >
                          {b.days_left < 0
                            ? `Expired ${Math.abs(b.days_left)} days ago`
                            : `${b.days_left} days left`}
                        </span>
                      ) : (
                        <span className="text-slate-400">—</span>
                      )}
                    </td>
                    {activeTab === 'expired' && isOwner && (
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() =>
                            handleQuarantineExpired(b.batch_id, b.current_quantity, b.product_name)
                          }
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg font-semibold transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Quarantine Stock</span>
                        </button>
                      </td>
                    )}
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

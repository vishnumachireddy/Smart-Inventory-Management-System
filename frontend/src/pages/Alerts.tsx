import React, { useState, useEffect } from 'react';
import {
  Bell,
  AlertTriangle,
  ClockAlert,
  Skull,
  CheckCircle,
  Eye,
  RefreshCw,
  Filter,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Alert } from '../types';
import { Badge, LoadingSpinner, EmptyState } from '../components/common';

export const Alerts: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [isResolvedFilter, setIsResolvedFilter] = useState<string>('false');
  const [reconciling, setReconciling] = useState(false);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (typeFilter) params.alert_type = typeFilter;
      if (severityFilter) params.severity = severityFilter;
      if (isResolvedFilter !== '') params.is_resolved = isResolvedFilter === 'true';

      const res = await apiClient.getAlerts(params);
      setAlerts(res.data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [typeFilter, severityFilter, isResolvedFilter]);

  const handleReconcile = async () => {
    setReconciling(true);
    try {
      await apiClient.reconcileAlerts();
      fetchAlerts();
    } catch (err) {
      console.error('Alert reconciliation error:', err);
    } finally {
      setReconciling(false);
    }
  };

  const handleMarkRead = async (id: number) => {
    try {
      await apiClient.markAlertRead(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_read: true } : a)));
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  const handleMarkResolved = async (id: number) => {
    try {
      await apiClient.markAlertResolved(id);
      setAlerts((prev) => prev.map((a) => (a.id === id ? { ...a, is_resolved: true } : a)));
    } catch (err) {
      console.error('Failed to mark resolved:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Active Alerts & Warnings</h1>
          <p className="text-xs text-slate-500 mt-1">
            Reconciled notification center for low-stock thresholds, impending expirations, and expired lots
          </p>
        </div>
        <button
          onClick={handleReconcile}
          disabled={reconciling}
          className="flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${reconciling ? 'animate-spin' : ''}`} />
          <span>{reconciling ? 'Reconciling State...' : 'Reconcile Active Alerts'}</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap gap-3">
        <select
          value={isResolvedFilter}
          onChange={(e) => setIsResolvedFilter(e.target.value)}
          className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 font-semibold focus:ring-2 focus:ring-indigo-500"
        >
          <option value="false">Active / Unresolved Alerts</option>
          <option value="true">Resolved History</option>
          <option value="">All Alerts</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Alert Types</option>
          <option value="low_stock">Low Stock Alerts</option>
          <option value="near_expiry">Near-Expiry Alerts</option>
          <option value="expired">Expired Stock Alerts</option>
        </select>

        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="warning">Warning</option>
          <option value="info">Info</option>
        </select>
      </div>

      {/* Alerts List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingSpinner label="Auditing store alerts..." />
        ) : alerts.length === 0 ? (
          <EmptyState
            title="All Clear — Zero Active Alerts"
            description="Your inventory levels are healthy and there are no batches expiring in the warning window."
          />
        ) : (
          <div className="divide-y divide-slate-100">
            {alerts.map((a) => {
              const isCrit = a.severity === 'critical';
              return (
                <div
                  key={a.id}
                  className={`p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 transition-colors ${
                    !a.is_read ? 'bg-indigo-50/20' : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-start space-x-3">
                    <div
                      className={`p-2.5 rounded-xl shrink-0 mt-0.5 ${
                        isCrit ? 'bg-rose-100 text-rose-600' : 'bg-amber-100 text-amber-600'
                      }`}
                    >
                      {a.alert_type === 'expired' ? (
                        <Skull className="w-5 h-5" />
                      ) : a.alert_type === 'near_expiry' ? (
                        <ClockAlert className="w-5 h-5" />
                      ) : (
                        <AlertTriangle className="w-5 h-5" />
                      )}
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-sm text-slate-900">{a.product_name}</span>
                        <Badge variant={isCrit ? 'danger' : 'warning'}>{a.severity}</Badge>
                        <Badge variant="neutral">{a.alert_type.replace('_', ' ')}</Badge>
                        {!a.is_read && (
                          <span className="w-2 h-2 rounded-full bg-indigo-600"></span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 mt-1 max-w-2xl">{a.message}</p>
                      <p className="text-[11px] text-slate-400 mt-1 font-mono">
                        Logged: {new Date(a.created_at).toLocaleString()}
                        {a.is_resolved && a.resolved_at && (
                          <span> • Resolved: {new Date(a.resolved_at).toLocaleString()}</span>
                        )}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 shrink-0">
                    {!a.is_read && (
                      <button
                        onClick={() => handleMarkRead(a.id)}
                        className="px-2.5 py-1 text-xs text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 rounded-lg font-medium"
                      >
                        Mark Read
                      </button>
                    )}
                    {!a.is_resolved && (
                      <button
                        onClick={() => handleMarkResolved(a.id)}
                        className="flex items-center space-x-1 px-3 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-200 rounded-lg text-xs font-semibold"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Resolve</span>
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import {
  Bell,
  AlertTriangle,
  Clock,
  Skull,
  CheckCircle,
  Eye,
  RefreshCw,
  Filter,
  CheckCheck,
  Calendar,
  Layers,
  Sparkles,
  ArrowRight,
  TrendingDown,
  PackageX,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Alert, DailySnapshot } from '../types';
import { Badge, LoadingSpinner, EmptyState } from '../components/common';
import { LoginAlertModal } from '../components/alerts/LoginAlertModal';
import { useAuth } from '../context/AuthContext';

export const Alerts: React.FC = () => {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [snapshots, setSnapshots] = useState<DailySnapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [isResolvedFilter, setIsResolvedFilter] = useState<string>('false');
  const [reconciling, setReconciling] = useState(false);
  const [runningJob, setRunningJob] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeView, setActiveView] = useState<'alerts' | 'snapshots'>('alerts');

  const isOwner = user?.role === 'shop_owner';

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

  const fetchSnapshots = async () => {
    try {
      const res = await apiClient.getDailySnapshots(20);
      setSnapshots(res.data);
    } catch (err) {
      console.error('Failed to load daily snapshots:', err);
    }
  };

  useEffect(() => {
    fetchAlerts();
    if (activeView === 'snapshots') {
      fetchSnapshots();
    }
  }, [typeFilter, severityFilter, isResolvedFilter, activeView]);

  const handleReconcile = async () => {
    setReconciling(true);
    try {
      await apiClient.reconcileAlerts();
      await fetchAlerts();
      if (activeView === 'snapshots') fetchSnapshots();
    } catch (err) {
      console.error('Alert reconciliation error:', err);
    } finally {
      setReconciling(false);
    }
  };

  const handleRunDailyCheck = async () => {
    setRunningJob(true);
    try {
      await apiClient.runDailyCheck(true);
      await fetchAlerts();
      await fetchSnapshots();
    } catch (err) {
      console.error('Daily check trigger failed:', err);
    } finally {
      setRunningJob(false);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await apiClient.markAllAlertsRead();
      setAlerts((prev) => prev.map((a) => ({ ...a, is_read: true })));
    } catch (err) {
      console.error('Failed to mark all read:', err);
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
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
            <Bell className="w-6 h-6 text-indigo-600" />
            Inventory Alerts & Daily Audits
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Real-time reconciliation of out-of-stock shortages, low stock thresholds, and impending shelf-life expirations
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-2 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span>Open Session Alert Dialog</span>
          </button>

          {isOwner && (
            <button
              onClick={handleRunDailyCheck}
              disabled={runningJob}
              title="Execute scheduled daily inventory audit & email delivery"
              className="flex items-center space-x-1.5 px-3 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
            >
              <Calendar className={`w-3.5 h-3.5 ${runningJob ? 'animate-spin' : ''}`} />
              <span>{runningJob ? 'Running Audit...' : 'Run Daily Audit Job'}</span>
            </button>
          )}

          <button
            onClick={handleReconcile}
            disabled={reconciling}
            className="flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-semibold shadow-sm transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reconciling ? 'animate-spin' : ''}`} />
            <span>{reconciling ? 'Reconciling...' : 'Reconcile Alerts'}</span>
          </button>
        </div>
      </div>

      {/* View Switcher Tabs */}
      <div className="flex border-b border-slate-200 gap-4">
        <button
          onClick={() => setActiveView('alerts')}
          className={`pb-3 text-xs font-bold transition-colors border-b-2 ${
            activeView === 'alerts'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Active & Historical Alerts
        </button>
        <button
          onClick={() => setActiveView('snapshots')}
          className={`pb-3 text-xs font-bold transition-colors border-b-2 ${
            activeView === 'snapshots'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          Daily Inventory Snapshots
        </button>
      </div>

      {activeView === 'alerts' ? (
        <>
          {/* Filter Toolbar */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2.5">
              <select
                value={isResolvedFilter}
                onChange={(e) => setIsResolvedFilter(e.target.value)}
                className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 font-semibold focus:ring-2 focus:ring-indigo-500"
              >
                <option value="false">Active / Unresolved Alerts</option>
                <option value="true">Resolved History</option>
                <option value="">All Alert Records</option>
              </select>

              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">All Alert Types</option>
                <option value="out_of_stock">Out of Stock</option>
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

            <button
              onClick={handleMarkAllRead}
              className="flex items-center space-x-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-semibold transition-colors"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              <span>Mark All as Read</span>
            </button>
          </div>

          {/* Alerts List */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
            {loading ? (
              <LoadingSpinner label="Auditing store alert ledgers..." />
            ) : alerts.length === 0 ? (
              <EmptyState
                title="All Clear — Zero Matching Alerts"
                description="Your inventory levels are healthy and there are no active alert warnings matching the selected filters."
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
                            a.alert_type === 'out_of_stock'
                              ? 'bg-rose-100 text-rose-700'
                              : a.alert_type === 'expired'
                              ? 'bg-red-100 text-red-700'
                              : a.alert_type === 'near_expiry'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-blue-100 text-blue-700'
                          }`}
                        >
                          {a.alert_type === 'out_of_stock' ? (
                            <PackageX className="w-5 h-5" />
                          ) : a.alert_type === 'expired' ? (
                            <Skull className="w-5 h-5" />
                          ) : a.alert_type === 'near_expiry' ? (
                            <Clock className="w-5 h-5" />
                          ) : (
                            <TrendingDown className="w-5 h-5" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-sm text-slate-900">{a.product_name}</span>
                            <Badge variant={isCrit ? 'danger' : 'warning'}>{a.severity}</Badge>
                            <Badge variant="neutral">{a.alert_type.replace('_', ' ')}</Badge>
                            {!a.is_read && (
                              <span className="w-2 h-2 rounded-full bg-indigo-600" title="Unread"></span>
                            )}
                          </div>
                          <p className="text-xs text-slate-600 mt-1 max-w-2xl">{a.message}</p>
                          <p className="text-[11px] text-slate-400 mt-1 font-mono">
                            Logged: {new Date(a.created_at).toLocaleString()}
                            {a.is_resolved && a.resolved_at && (
                              <span> &middot; Resolved: {new Date(a.resolved_at).toLocaleString()}</span>
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
        </>
      ) : (
        /* Snapshots History Table */
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 bg-slate-50 border-b border-slate-200">
            <h3 className="text-sm font-bold text-slate-800">Dated Daily Inventory Snapshots (Neon PostgreSQL)</h3>
            <p className="text-xs text-slate-500">Historical records generated by daily automated audit checks</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/50 text-slate-600 border-b border-slate-200 font-semibold">
                  <th className="py-3 px-4">Reporting Date</th>
                  <th className="py-3 px-4 text-center">Near Expiry</th>
                  <th className="py-3 px-4 text-center">Low Stock</th>
                  <th className="py-3 px-4 text-center">Out of Stock</th>
                  <th className="py-3 px-4 text-right">Stock Valuation</th>
                  <th className="py-3 px-4 text-center">Sales Count</th>
                  <th className="py-3 px-4 text-right">Revenue</th>
                  <th className="py-3 px-4">Summary</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {snapshots.map((snap) => (
                  <tr key={snap.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-900">{snap.reporting_date}</td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-2 py-0.5 rounded-full font-bold bg-amber-100 text-amber-800">
                        {snap.near_expiry_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-2 py-0.5 rounded-full font-bold bg-blue-100 text-blue-800">
                        {snap.low_stock_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="px-2 py-0.5 rounded-full font-bold bg-red-100 text-red-800">
                        {snap.out_of_stock_count}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono font-medium text-slate-800">
                      ₹{Number(snap.total_stock_value).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-center font-medium text-slate-700">{snap.sales_count}</td>
                    <td className="py-3 px-4 text-right font-mono font-medium text-emerald-700">
                      ₹{Number(snap.revenue).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 text-slate-500 max-w-xs truncate">{snap.summary_text}</td>
                  </tr>
                ))}
                {snapshots.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-400">
                      No snapshots generated yet. Run a daily audit job to generate initial snapshot.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Login Alert Modal Dialog */}
      <LoginAlertModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onRemindLater={() => setIsModalOpen(false)}
      />
    </div>
  );
};

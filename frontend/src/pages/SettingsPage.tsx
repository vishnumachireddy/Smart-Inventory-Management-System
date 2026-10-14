import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Save,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Mail,
  Send,
  Clock,
  Calendar,
  History,
  ShieldAlert,
  Check,
  AlertTriangle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { AppSetting, NotificationSettings, EmailDeliveryLog, ScheduledJobRun } from '../types';
import { LoadingSpinner, Badge } from '../components/common';
import { useAuth } from '../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { isOwner } = useAuth();
  const [activeTab, setActiveTab] = useState<'general' | 'notifications' | 'logs'>('general');

  // General Settings
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [savingGeneral, setSavingGeneral] = useState(false);
  const [generalSuccess, setGeneralSuccess] = useState('');
  const [generalError, setGeneralError] = useState('');

  // Notification Settings
  const [notif, setNotif] = useState<NotificationSettings | null>(null);
  const [savingNotif, setSavingNotif] = useState(false);
  const [notifSuccess, setNotifSuccess] = useState('');
  const [notifError, setNotifError] = useState('');

  // Test Email
  const [testEmailRecipient, setTestEmailRecipient] = useState('');
  const [sendingTestEmail, setSendingTestEmail] = useState(false);
  const [testEmailResult, setTestEmailResult] = useState<{ success: boolean; message: string } | null>(null);

  // Delivery Logs & Job Runs
  const [deliveryLogs, setDeliveryLogs] = useState<EmailDeliveryLog[]>([]);
  const [jobRuns, setJobRuns] = useState<ScheduledJobRun[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);

  const fetchSettingsAndNotif = async () => {
    setLoading(true);
    try {
      const [appRes, notifRes] = await Promise.all([
        apiClient.getSettings(),
        apiClient.getNotificationSettings(),
      ]);

      const map: Record<string, string> = {};
      appRes.data.forEach((s) => {
        map[s.key] = s.value;
      });
      setSettings(map);
      setNotif(notifRes.data);
      setTestEmailRecipient(notifRes.data.recipient_emails.split(',')[0]?.trim() || '');
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogsAndJobRuns = async () => {
    setLoadingLogs(true);
    try {
      const [logsRes, runsRes] = await Promise.all([
        apiClient.getDeliveryLogs(30),
        apiClient.getJobRuns(20),
      ]);
      setDeliveryLogs(logsRes.data);
      setJobRuns(runsRes.data);
    } catch (err) {
      console.error('Failed to load logs:', err);
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    fetchSettingsAndNotif();
  }, []);

  useEffect(() => {
    if (activeTab === 'logs') {
      fetchLogsAndJobRuns();
    }
  }, [activeTab]);

  const handleGeneralChange = (key: string, val: string) => {
    setSettings((prev) => ({ ...prev, [key]: val }));
  };

  const handleSaveGeneral = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingGeneral(true);
    setGeneralSuccess('');
    setGeneralError('');

    try {
      for (const [key, val] of Object.entries(settings)) {
        await apiClient.updateSetting(key, { value: val });
      }
      setGeneralSuccess('General store settings saved and synchronized!');
    } catch (err: any) {
      setGeneralError(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSavingGeneral(false);
    }
  };

  const handleSaveNotifications = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notif) return;
    setSavingNotif(true);
    setNotifSuccess('');
    setNotifError('');

    try {
      const res = await apiClient.updateNotificationSettings({
        recipient_emails: notif.recipient_emails,
        enabled: notif.enabled,
        report_frequency: notif.report_frequency,
        scheduled_time: notif.scheduled_time,
        timezone: notif.timezone,
        categories: notif.categories,
        include_empty_reports: notif.include_empty_reports,
      });
      setNotif(res.data);
      setNotifSuccess('Email notification schedule & recipient settings saved to Neon PostgreSQL!');
    } catch (err: any) {
      setNotifError(err.response?.data?.detail || 'Failed to save notification settings');
    } finally {
      setSavingNotif(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (!testEmailRecipient.trim()) return;
    setSendingTestEmail(true);
    setTestEmailResult(null);
    try {
      const res = await apiClient.sendTestEmail(testEmailRecipient.trim());
      setTestEmailResult(res.data);
      if (activeTab === 'logs') fetchLogsAndJobRuns();
    } catch (err: any) {
      setTestEmailResult({
        success: false,
        message: err.response?.data?.detail || 'Test email request failed.',
      });
    } finally {
      setSendingTestEmail(false);
    }
  };

  const toggleCategory = (category: string) => {
    if (!notif) return;
    const cats = notif.categories.split(',').map((c) => c.trim()).filter(Boolean);
    const newCats = cats.includes(category) ? cats.filter((c) => c !== category) : [...cats, category];
    setNotif({ ...notif, categories: newCats.join(',') });
  };

  if (loading) {
    return <LoadingSpinner label="Loading application settings..." />;
  }

  const enabledCats = notif?.categories.split(',').map((c) => c.trim()) || [];

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Top Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2.5">
          <SettingsIcon className="w-6 h-6 text-indigo-600" />
          Settings & Email Configuration
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure business rules, automated daily inventory checks, scheduled email delivery, and audit ledgers
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-6">
        <button
          onClick={() => setActiveTab('general')}
          className={`pb-3 text-xs font-bold transition-colors border-b-2 ${
            activeTab === 'general'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          General & Inventory Rules
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`pb-3 text-xs font-bold transition-colors border-b-2 flex items-center gap-1.5 ${
            activeTab === 'notifications'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <Mail className="w-3.5 h-3.5" />
          <span>Email & Daily Schedule</span>
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={`pb-3 text-xs font-bold transition-colors border-b-2 flex items-center gap-1.5 ${
            activeTab === 'logs'
              ? 'border-indigo-600 text-indigo-600'
              : 'border-transparent text-slate-500 hover:text-slate-700'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          <span>Delivery & Job Logs</span>
        </button>
      </div>

      {/* TAB 1: GENERAL SETTINGS */}
      {activeTab === 'general' && (
        <div className="space-y-6">
          {generalSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{generalSuccess}</span>
            </div>
          )}

          {generalError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{generalError}</span>
            </div>
          )}

          <form onSubmit={handleSaveGeneral} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6 text-xs">
            {/* Store Profile */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">Store Profile</h3>
              <div className="mt-4 space-y-4">
                <div>
                  <label className="block font-semibold text-slate-700 uppercase mb-1">Retail Store Name</label>
                  <input
                    type="text"
                    disabled={!isOwner}
                    value={settings.shop_name || 'StockSense Store'}
                    onChange={(e) => handleGeneralChange('shop_name', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 disabled:bg-slate-50 disabled:text-slate-500"
                  />
                </div>
              </div>
            </div>

            {/* Expiry & Inventory Business Rules */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
                Inventory & Expiry Thresholds
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block font-semibold text-slate-700 uppercase mb-1">
                    Near-Expiry Warning Window (Days) *
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={365}
                    required
                    disabled={!isOwner}
                    value={settings.near_expiry_days || '7'}
                    onChange={(e) => handleGeneralChange('near_expiry_days', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono disabled:bg-slate-50"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Batches expiring within this number of days will trigger warnings and FEFO prioritization.
                  </p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 uppercase mb-1">
                    Default Supplier Lead Time (Days) *
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={90}
                    required
                    disabled={!isOwner}
                    value={settings.default_lead_time_days || '7'}
                    onChange={(e) => handleGeneralChange('default_lead_time_days', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono disabled:bg-slate-50"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Fallback lead time applied when a supplier does not have custom dispatch terms.
                  </p>
                </div>
              </div>
            </div>

            {/* Currency & Financial Localization */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">
                Currency & Localization
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
                <div>
                  <label className="block font-semibold text-slate-700 uppercase mb-1">Currency Symbol</label>
                  <input
                    type="text"
                    disabled={!isOwner}
                    value={settings.currency_symbol || '₹'}
                    onChange={(e) => handleGeneralChange('currency_symbol', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 font-bold disabled:bg-slate-50"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 uppercase mb-1">Currency Code (ISO)</label>
                  <input
                    type="text"
                    disabled={!isOwner}
                    value={settings.currency_code || 'INR'}
                    onChange={(e) => handleGeneralChange('currency_code', e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-slate-300 uppercase font-mono disabled:bg-slate-50"
                  />
                </div>
              </div>
            </div>

            {isOwner && (
              <div className="pt-4 border-t border-slate-100 flex justify-end">
                <button
                  type="submit"
                  disabled={savingGeneral}
                  className="flex items-center space-x-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  <span>{savingGeneral ? 'Updating Settings...' : 'Save General Settings'}</span>
                </button>
              </div>
            )}
          </form>
        </div>
      )}

      {/* TAB 2: EMAIL & SCHEDULED AUDITS */}
      {activeTab === 'notifications' && notif && (
        <div className="space-y-6">
          {notifSuccess && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{notifSuccess}</span>
            </div>
          )}

          {notifError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{notifError}</span>
            </div>
          )}

          <form onSubmit={handleSaveNotifications} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6 text-xs">
            {/* Master Toggle */}
            <div className="flex items-center justify-between p-4 bg-indigo-50/40 rounded-xl border border-indigo-100">
              <div>
                <h4 className="font-bold text-sm text-slate-900">Enable Automated Scheduled Inventory Audits</h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  When enabled, the server executes daily FEFO reconciliation at the configured time and emails summary reports.
                </p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  disabled={!isOwner}
                  checked={notif.enabled}
                  onChange={(e) => setNotif({ ...notif, enabled: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
              </label>
            </div>

            {/* Recipients */}
            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">
                Recipient Email Addresses (Comma-Separated) *
              </label>
              <input
                type="text"
                disabled={!isOwner}
                required={notif.enabled}
                placeholder="owner@stocksense.com, manager@stocksense.com"
                value={notif.recipient_emails}
                onChange={(e) => setNotif({ ...notif, recipient_emails: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono disabled:bg-slate-50"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Daily and weekly digest reports will be automatically dispatched to all addresses listed here.
              </p>
            </div>

            {/* Schedule & Timing */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">Report Frequency</label>
                <select
                  disabled={!isOwner}
                  value={notif.report_frequency}
                  onChange={(e) => setNotif({ ...notif, report_frequency: e.target.value as any })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
                >
                  <option value="daily">Daily Inventory Audit</option>
                  <option value="weekly">Weekly Summary Only</option>
                  <option value="both">Daily Alerts + Weekly Summary</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">Scheduled Time (HH:MM)</label>
                <input
                  type="time"
                  disabled={!isOwner}
                  value={notif.scheduled_time}
                  onChange={(e) => setNotif({ ...notif, scheduled_time: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono"
                >
                </input>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 uppercase mb-1">Business Timezone</label>
                <input
                  type="text"
                  disabled
                  value={notif.timezone}
                  className="w-full px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 font-mono text-slate-500"
                />
              </div>
            </div>

            {/* Category Inclusions */}
            <div>
              <h4 className="font-semibold text-slate-700 uppercase mb-2">Sections Included in Email Digest</h4>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { key: 'near_expiry', label: 'Products Nearing Expiry' },
                  { key: 'low_stock', label: 'Very Low-Stock Items' },
                  { key: 'out_of_stock', label: 'Out-of-Stock Items' },
                  { key: 'sales_summary', label: 'Sales & Gross Margin' },
                ].map((item) => (
                  <label
                    key={item.key}
                    className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer transition-all ${
                      enabledCats.includes(item.key)
                        ? 'bg-indigo-50/50 border-indigo-300 text-indigo-900 font-semibold'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    <input
                      type="checkbox"
                      disabled={!isOwner}
                      checked={enabledCats.includes(item.key)}
                      onChange={() => toggleCategory(item.key)}
                      className="rounded text-indigo-600 focus:ring-indigo-500"
                    />
                    <span className="text-[11px]">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Empty Reports Policy */}
            <div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  disabled={!isOwner}
                  checked={notif.include_empty_reports}
                  onChange={(e) => setNotif({ ...notif, include_empty_reports: e.target.checked })}
                  className="rounded text-indigo-600 focus:ring-indigo-500"
                />
                <span className="text-slate-700 font-medium">Send email even when zero inventory alerts are detected</span>
              </label>
            </div>

            {isOwner && (
              <div className="pt-4 border-t border-slate-100 flex justify-end">
                <button
                  type="submit"
                  disabled={savingNotif}
                  className="flex items-center space-x-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all disabled:opacity-50"
                >
                  <Save className="w-4 h-4" />
                  <span>{savingNotif ? 'Saving Schedule...' : 'Save Notification Schedule'}</span>
                </button>
              </div>
            )}
          </form>

          {/* Test Email Card */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4 text-xs">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Send Test Verification Email</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Verifies SMTP connectivity, port handshake, and template rendering without waiting for the scheduled time.
              </p>
            </div>

            {testEmailResult && (
              <div
                className={`p-3 rounded-xl border flex items-center gap-2 ${
                  testEmailResult.success
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-amber-50 border-amber-200 text-amber-800'
                }`}
              >
                {testEmailResult.success ? (
                  <Check className="w-4 h-4 text-emerald-600 shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                )}
                <span>{testEmailResult.message}</span>
              </div>
            )}

            <div className="flex gap-2">
              <input
                type="email"
                placeholder="recipient@example.com"
                value={testEmailRecipient}
                onChange={(e) => setTestEmailRecipient(e.target.value)}
                className="flex-1 px-3 py-2 rounded-lg border border-slate-300 font-mono text-xs"
              />
              <button
                type="button"
                onClick={handleSendTestEmail}
                disabled={sendingTestEmail || !testEmailRecipient.trim()}
                className="flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
              >
                <Send className={`w-3.5 h-3.5 ${sendingTestEmail ? 'animate-spin' : ''}`} />
                <span>{sendingTestEmail ? 'Dispatching...' : 'Send Test'}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: DELIVERY LOGS & SCHEDULED JOBS */}
      {activeTab === 'logs' && (
        <div className="space-y-6">
          {/* Scheduled Job Runs */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden text-xs">
            <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-slate-900">Scheduled Job Execution History</h3>
                <p className="text-[11px] text-slate-500">Audit trail of automated daily inventory checks</p>
              </div>
              <button
                onClick={fetchLogsAndJobRuns}
                disabled={loadingLogs}
                className="p-1.5 hover:bg-slate-200 rounded-lg text-slate-600"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingLogs ? 'animate-spin' : ''}`} />
              </button>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/50 text-slate-600 border-b border-slate-200 font-semibold">
                    <th className="py-2.5 px-4">Run ID</th>
                    <th className="py-2.5 px-4">Job Name</th>
                    <th className="py-2.5 px-4">Started At</th>
                    <th className="py-2.5 px-4">Finished At</th>
                    <th className="py-2.5 px-4 text-center">Status</th>
                    <th className="py-2.5 px-4">Summary / Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {jobRuns.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-4 font-mono font-bold text-slate-700">#{r.id}</td>
                      <td className="py-2.5 px-4 font-mono text-slate-600">{r.job_name}</td>
                      <td className="py-2.5 px-4 text-slate-600">{new Date(r.started_at).toLocaleString()}</td>
                      <td className="py-2.5 px-4 text-slate-600">
                        {r.finished_at ? new Date(r.finished_at).toLocaleString() : 'Running...'}
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <Badge variant={r.status === 'success' ? 'success' : r.status === 'skipped' ? 'info' : 'danger'}>
                          {r.status}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-4 text-slate-600 font-mono text-[11px]">
                        {r.summary_counts || r.error_details || '—'}
                      </td>
                    </tr>
                  ))}
                  {jobRuns.length === 0 && (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-slate-400">
                        No scheduled jobs recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Email Delivery Logs */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden text-xs">
            <div className="p-4 bg-slate-50 border-b border-slate-200">
              <h3 className="font-bold text-sm text-slate-900">Email Delivery Logs</h3>
              <p className="text-[11px] text-slate-500">Persistent delivery statuses for scheduled audits and test messages</p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/50 text-slate-600 border-b border-slate-200 font-semibold">
                    <th className="py-2.5 px-4">Log ID</th>
                    <th className="py-2.5 px-4">Recipient</th>
                    <th className="py-2.5 px-4">Report Type</th>
                    <th className="py-2.5 px-4 text-center">Status</th>
                    <th className="py-2.5 px-4 text-center">Attempts</th>
                    <th className="py-2.5 px-4">Dispatched At</th>
                    <th className="py-2.5 px-4">Message ID / Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {deliveryLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-slate-50">
                      <td className="py-2.5 px-4 font-mono font-bold text-slate-700">#{log.id}</td>
                      <td className="py-2.5 px-4 font-medium text-slate-900">{log.recipient}</td>
                      <td className="py-2.5 px-4 font-mono text-slate-600">{log.report_type}</td>
                      <td className="py-2.5 px-4 text-center">
                        <Badge
                          variant={
                            log.status === 'accepted'
                              ? 'success'
                              : log.status === 'disabled'
                              ? 'neutral'
                              : 'danger'
                          }
                        >
                          {log.status}
                        </Badge>
                      </td>
                      <td className="py-2.5 px-4 text-center font-bold text-slate-700">{log.attempt_count}</td>
                      <td className="py-2.5 px-4 text-slate-600">
                        {new Date(log.last_attempt_at).toLocaleString()}
                      </td>
                      <td className="py-2.5 px-4 font-mono text-[11px] text-slate-500 max-w-xs truncate">
                        {log.provider_message_id || log.failure_reason || '—'}
                      </td>
                    </tr>
                  ))}
                  {deliveryLogs.length === 0 && (
                    <tr>
                      <td colSpan={7} className="py-6 text-center text-slate-400">
                        No email delivery attempts logged yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

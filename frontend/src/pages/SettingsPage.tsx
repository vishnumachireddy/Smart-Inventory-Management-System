import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';
import { apiClient } from '../api/client';
import { AppSetting } from '../types';
import { LoadingSpinner } from '../components/common';
import { useAuth } from '../context/AuthContext';

export const SettingsPage: React.FC = () => {
  const { isOwner } = useAuth();
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getSettings();
      const map: Record<string, string> = {};
      res.data.forEach((s) => {
        map[s.key] = s.value;
      });
      setSettings(map);
    } catch (err) {
      console.error('Failed to load settings:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleChange = (key: string, val: string) => {
    setSettings((prev) => ({ ...prev, [key]: val }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      for (const [key, val] of Object.entries(settings)) {
        await apiClient.updateSetting(key, { value: val });
      }
      setSuccessMsg('Settings saved successfully and inventory alert thresholds updated!');
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading application settings..." />;
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Top Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Application Settings</h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure business rules, alert lead-time windows, and regional currency representations
        </p>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 shrink-0 text-emerald-600" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6 text-xs">
        {/* Store Profile */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 pb-2 border-b border-slate-100">Store Profile</h3>
          <div className="mt-4 space-y-4">
            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">Retail Store / Branch Name</label>
              <input
                type="text"
                disabled={!isOwner}
                value={settings.shop_name || 'StockSense Store'}
                onChange={(e) => handleChange('shop_name', e.target.value)}
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
                value={settings.near_expiry_days || '30'}
                onChange={(e) => handleChange('near_expiry_days', e.target.value)}
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
                onChange={(e) => handleChange('default_lead_time_days', e.target.value)}
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
                onChange={(e) => handleChange('currency_symbol', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 font-bold disabled:bg-slate-50"
              />
            </div>

            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">Currency Code (ISO)</label>
              <input
                type="text"
                disabled={!isOwner}
                value={settings.currency_code || 'INR'}
                onChange={(e) => handleChange('currency_code', e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 uppercase font-mono disabled:bg-slate-50"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        {isOwner && (
          <div className="pt-4 border-t border-slate-100 flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="flex items-center space-x-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? 'Updating Settings...' : 'Save Application Settings'}</span>
            </button>
          </div>
        )}
      </form>
    </div>
  );
};

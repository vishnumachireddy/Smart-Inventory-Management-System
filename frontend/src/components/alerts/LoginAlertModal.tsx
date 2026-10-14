import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Clock,
  TrendingDown,
  PackageX,
  RefreshCw,
  X,
  ExternalLink,
  Bell,
  ArrowRight,
  CheckCircle2,
  Calendar,
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { InventorySummaryResponse } from '../../types';

interface LoginAlertModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRemindLater: () => void;
}

export const LoginAlertModal: React.FC<LoginAlertModalProps> = ({
  isOpen,
  onClose,
  onRemindLater,
}) => {
  const navigate = useNavigate();
  const [data, setData] = useState<InventorySummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'near_expiry' | 'low_stock' | 'out_of_stock'>('near_expiry');
  const [warningDays, setWarningDays] = useState<number>(7);

  const fetchAlertSummary = async (days?: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getInventorySummary(days || warningDays);
      setData(res.data);
      // Auto-select first tab with items
      if (res.data.summary.near_expiry_count > 0) {
        setActiveTab('near_expiry');
      } else if (res.data.summary.low_stock_count > 0) {
        setActiveTab('low_stock');
      } else if (res.data.summary.out_of_stock_count > 0) {
        setActiveTab('out_of_stock');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load inventory alert summary.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchAlertSummary();
    }
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const summary = data?.summary || { near_expiry_count: 0, low_stock_count: 0, out_of_stock_count: 0 };
  const totalAlerts = summary.near_expiry_count + summary.low_stock_count + summary.out_of_stock_count;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-4xl max-h-[90vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden border border-slate-200"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-amber-500/20 text-amber-400 rounded-xl border border-amber-500/30">
              <Bell className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h2 id="modal-title" className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
                Inventory Attention Required
                {totalAlerts > 0 && (
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-red-500/30 text-red-300 font-semibold border border-red-500/40">
                    {totalAlerts} Actionable {totalAlerts === 1 ? 'Item' : 'Items'}
                  </span>
                )}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Session Check: Current stock state evaluated via FEFO logic &middot; Timezone: {data?.timezone || 'Asia/Kolkata'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => fetchAlertSummary()}
              disabled={loading}
              title="Refresh inventory state"
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              title="Close modal"
              className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Category Summary Metric Cards */}
        <div className="grid grid-cols-3 gap-3 p-4 bg-slate-50 border-b border-slate-200">
          {/* Near Expiry Tab Pill */}
          <button
            onClick={() => setActiveTab('near_expiry')}
            className={`flex items-center justify-between p-3.5 rounded-xl border transition-all text-left ${
              activeTab === 'near_expiry'
                ? 'bg-amber-50 border-amber-400 shadow-sm ring-2 ring-amber-400/20'
                : 'bg-white border-slate-200 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-100 text-amber-700">
                <Clock className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-500">Nearing Expiry</div>
                <div className="text-xs text-slate-400 mt-0.5">Within {warningDays} days</div>
              </div>
            </div>
            <span className="text-2xl font-black text-amber-600">{summary.near_expiry_count}</span>
          </button>

          {/* Low Stock Tab Pill */}
          <button
            onClick={() => setActiveTab('low_stock')}
            className={`flex items-center justify-between p-3.5 rounded-xl border transition-all text-left ${
              activeTab === 'low_stock'
                ? 'bg-blue-50 border-blue-400 shadow-sm ring-2 ring-blue-400/20'
                : 'bg-white border-slate-200 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100 text-blue-700">
                <TrendingDown className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-500">Very Low Stock</div>
                <div className="text-xs text-slate-400 mt-0.5">&le; Reorder Point</div>
              </div>
            </div>
            <span className="text-2xl font-black text-blue-600">{summary.low_stock_count}</span>
          </button>

          {/* Out of Stock Tab Pill */}
          <button
            onClick={() => setActiveTab('out_of_stock')}
            className={`flex items-center justify-between p-3.5 rounded-xl border transition-all text-left ${
              activeTab === 'out_of_stock'
                ? 'bg-red-50 border-red-400 shadow-sm ring-2 ring-red-400/20'
                : 'bg-white border-slate-200 hover:border-slate-300'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-100 text-red-700">
                <PackageX className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-500">Out of Stock</div>
                <div className="text-xs text-slate-400 mt-0.5">0 Available Units</div>
              </div>
            </div>
            <span className="text-2xl font-black text-red-600">{summary.out_of_stock_count}</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 min-h-[280px]">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-600 mb-3" />
              <p className="text-sm font-medium">Reconciling batch shelf-life & stock ledgers...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          ) : (
            <>
              {/* TAB 1: PRODUCTS NEARING EXPIRY */}
              {activeTab === 'near_expiry' && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <Clock className="w-4 h-4 text-amber-600" />
                      Eligible Lots Nearing Expiration (Strict FEFO Segregation)
                    </h3>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span>Warning Threshold:</span>
                      <select
                        value={warningDays}
                        onChange={(e) => {
                          const val = Number(e.target.value);
                          setWarningDays(val);
                          fetchAlertSummary(val);
                        }}
                        className="px-2 py-1 rounded border border-slate-200 bg-white text-xs font-medium text-slate-700 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      >
                        <option value={3}>3 Days</option>
                        <option value={7}>7 Days (Default)</option>
                        <option value={14}>14 Days</option>
                        <option value={30}>30 Days</option>
                      </select>
                    </div>
                  </div>

                  {(!data?.near_expiry || data.near_expiry.length === 0) ? (
                    <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                      <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                      <p className="text-sm font-semibold text-slate-700">No Batches Expiring in the Next {warningDays} Days</p>
                      <p className="text-xs text-slate-500 mt-1">All eligible inventory lots have adequate shelf life.</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
                            <th className="py-2.5 px-3">Product Name & SKU</th>
                            <th className="py-2.5 px-3">Batch #</th>
                            <th className="py-2.5 px-3 text-center">Remaining Qty</th>
                            <th className="py-2.5 px-3 text-center">Expiry Date</th>
                            <th className="py-2.5 px-3 text-center">Days Left</th>
                            <th className="py-2.5 px-3">Recommended Action</th>
                            <th className="py-2.5 px-3 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {data.near_expiry.map((item) => (
                            <tr key={item.id} className="hover:bg-amber-50/40 transition-colors">
                              <td className="py-2.5 px-3">
                                <div className="font-semibold text-slate-900">{item.product_name}</div>
                                <div className="text-[11px] text-slate-500 font-mono">SKU: {item.sku}</div>
                              </td>
                              <td className="py-2.5 px-3 font-mono font-medium text-slate-700">{item.batch_number}</td>
                              <td className="py-2.5 px-3 text-center font-bold text-slate-800">{item.remaining_quantity}</td>
                              <td className="py-2.5 px-3 text-center text-slate-600">{item.expiry_date}</td>
                              <td className="py-2.5 px-3 text-center">
                                <span
                                  className={`inline-block px-2 py-0.5 rounded-full text-[11px] font-bold ${
                                    item.severity === 'critical'
                                      ? 'bg-red-100 text-red-700'
                                      : 'bg-amber-100 text-amber-800'
                                  }`}
                                >
                                  {item.days_until_expiry}d
                                </span>
                              </td>
                              <td className="py-2.5 px-3 text-slate-600 max-w-xs">{item.recommended_action}</td>
                              <td className="py-2.5 px-3 text-right">
                                <button
                                  onClick={() => {
                                    onClose();
                                    navigate(`/products/${item.product_id}`);
                                  }}
                                  className="text-indigo-600 hover:text-indigo-800 font-medium inline-flex items-center gap-1 hover:underline"
                                >
                                  Manage <ExternalLink className="w-3 h-3" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 2: VERY LOW-STOCK PRODUCTS */}
              {activeTab === 'low_stock' && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <TrendingDown className="w-4 h-4 text-blue-600" />
                      Products Below Configured Reorder Threshold
                    </h3>
                    <span className="text-xs text-slate-500">
                      Calculated from real sellable batch balances
                    </span>
                  </div>

                  {(!data?.low_stock || data.low_stock.length === 0) ? (
                    <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                      <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                      <p className="text-sm font-semibold text-slate-700">All Products Above Safety Reorder Thresholds</p>
                      <p className="text-xs text-slate-500 mt-1">No impending inventory stockouts detected.</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
                            <th className="py-2.5 px-3">Product Name & SKU</th>
                            <th className="py-2.5 px-3 text-center">Eligible Stock</th>
                            <th className="py-2.5 px-3 text-center">Reorder Threshold</th>
                            <th className="py-2.5 px-3 text-center">Est. Daily Sales</th>
                            <th className="py-2.5 px-3 text-center">Suggested Order</th>
                            <th className="py-2.5 px-3">Recommended Action</th>
                            <th className="py-2.5 px-3 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {data.low_stock.map((item) => (
                            <tr key={item.id} className="hover:bg-blue-50/40 transition-colors">
                              <td className="py-2.5 px-3">
                                <div className="font-semibold text-slate-900">{item.product_name}</div>
                                <div className="text-[11px] text-slate-500 font-mono">SKU: {item.sku}</div>
                              </td>
                              <td className="py-2.5 px-3 text-center font-bold text-amber-600">{item.current_stock}</td>
                              <td className="py-2.5 px-3 text-center font-medium text-slate-600">{item.reorder_threshold}</td>
                              <td className="py-2.5 px-3 text-center text-slate-600">{item.avg_daily_demand}/day</td>
                              <td className="py-2.5 px-3 text-center font-bold text-emerald-600">+{item.suggested_reorder_qty}</td>
                              <td className="py-2.5 px-3 text-slate-600 max-w-xs">{item.recommended_action}</td>
                              <td className="py-2.5 px-3 text-right">
                                <button
                                  onClick={() => {
                                    onClose();
                                    navigate('/purchases');
                                  }}
                                  className="text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1 hover:underline"
                                >
                                  Restock <ArrowRight className="w-3 h-3" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* TAB 3: OUT-OF-STOCK PRODUCTS */}
              {activeTab === 'out_of_stock' && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                      <PackageX className="w-4 h-4 text-red-600" />
                      Completely Out-of-Stock Products (0 Available Units)
                    </h3>
                    <span className="text-xs text-slate-500">
                      Excluded from POS sales fulfillment
                    </span>
                  </div>

                  {(!data?.out_of_stock || data.out_of_stock.length === 0) ? (
                    <div className="text-center py-12 bg-slate-50 rounded-xl border border-dashed border-slate-200">
                      <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                      <p className="text-sm font-semibold text-slate-700">Zero Stockouts Across Active Catalog</p>
                      <p className="text-xs text-slate-500 mt-1">Every active product has sellable stock on hand.</p>
                    </div>
                  ) : (
                    <div className="overflow-x-auto rounded-xl border border-slate-200">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
                            <th className="py-2.5 px-3">Product Name & SKU</th>
                            <th className="py-2.5 px-3 text-center">Status</th>
                            <th className="py-2.5 px-3">Last Known Stock Movement</th>
                            <th className="py-2.5 px-3">Replenishment Action</th>
                            <th className="py-2.5 px-3 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {data.out_of_stock.map((item) => (
                            <tr key={item.id} className="hover:bg-red-50/40 transition-colors">
                              <td className="py-2.5 px-3">
                                <div className="font-semibold text-slate-900">{item.product_name}</div>
                                <div className="text-[11px] text-slate-500 font-mono">SKU: {item.sku}</div>
                              </td>
                              <td className="py-2.5 px-3 text-center">
                                <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-100 text-red-700 border border-red-200">
                                  OUT OF STOCK
                                </span>
                              </td>
                              <td className="py-2.5 px-3 text-slate-600 font-mono text-[11px]">{item.last_stock_movement}</td>
                              <td className="py-2.5 px-3 text-red-700 font-medium">{item.recommended_action}</td>
                              <td className="py-2.5 px-3 text-right">
                                <button
                                  onClick={() => {
                                    onClose();
                                    navigate('/purchases');
                                  }}
                                  className="text-red-600 hover:text-red-800 font-medium inline-flex items-center gap-1 hover:underline"
                                >
                                  Inward <ArrowRight className="w-3 h-3" />
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-50 border-t border-slate-200">
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Calendar className="w-3.5 h-3.5" />
            <span>
              Last Checked:{' '}
              {data?.generated_at
                ? new Date(data.generated_at).toLocaleTimeString('en-IN', {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })
                : 'Just now'}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onRemindLater}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Remind Me Later
            </button>
            <button
              onClick={() => {
                onClose();
                navigate('/alerts');
              }}
              className="px-4 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
            >
              Go to Alerts Hub <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

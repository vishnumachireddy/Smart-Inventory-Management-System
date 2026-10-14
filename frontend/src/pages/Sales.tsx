import React, { useState, useEffect } from 'react';
import {
  ReceiptText,
  Search,
  Filter,
  Eye,
  RotateCcw,
  Printer,
  Calendar,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Sale } from '../types';
import { Badge, Modal, LoadingSpinner, EmptyState } from '../components/common';
import { useAuth } from '../context/AuthContext';

export const Sales: React.FC = () => {
  const { isOwner } = useAuth();
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // Selected Sale for Viewing
  const [viewingSale, setViewingSale] = useState<Sale | null>(null);
  const [isViewOpen, setIsViewOpen] = useState(false);

  // Cancellation Modal
  const [cancellingSale, setCancellingSale] = useState<Sale | null>(null);
  const [cancelReason, setCancelReason] = useState('Customer Return & Refund');
  const [cancelError, setCancelError] = useState('');
  const [submittingCancel, setSubmittingCancel] = useState(false);

  const fetchSales = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (statusFilter) params.status = statusFilter;
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const res = await apiClient.getSales(params);
      setSales(res.data);
    } catch (err) {
      console.error('Failed to fetch sales history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSales();
  }, [statusFilter, startDate, endDate]);

  const handleOpenCancel = (sale: Sale) => {
    setCancellingSale(sale);
    setCancelReason('Customer Return / Transaction Void');
    setCancelError('');
  };

  const handleConfirmCancel = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancellingSale) return;
    setCancelError('');
    setSubmittingCancel(true);

    try {
      await apiClient.cancelSale(cancellingSale.id, {
        cancellation_reason: cancelReason,
      });
      setCancellingSale(null);
      fetchSales();
    } catch (err: any) {
      setCancelError(err.response?.data?.detail || 'Failed to cancel sale transaction');
    } finally {
      setSubmittingCancel(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Sales History & Receipts</h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse past transactions, inspect batch cost snapshots, and issue controlled cancellations
          </p>
        </div>
        <button
          onClick={fetchSales}
          className="flex items-center space-x-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Sales</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled / Voided</option>
        </select>

        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400">From:</span>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="px-2.5 py-1.5 rounded-xl border border-slate-200 text-xs"
          />
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400">To:</span>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="px-2.5 py-1.5 rounded-xl border border-slate-200 text-xs"
          />
        </div>

        {(statusFilter || startDate || endDate) && (
          <button
            onClick={() => {
              setStatusFilter('');
              setStartDate('');
              setEndDate('');
            }}
            className="px-3 py-2 text-xs text-rose-600 hover:bg-rose-50 rounded-xl font-medium transition-colors"
          >
            Reset
          </button>
        )}
      </div>

      {/* Sales Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingSpinner label="Fetching sales history..." />
        ) : sales.length === 0 ? (
          <EmptyState
            title="No Sales Recorded"
            description="No sales matched your date or status selection."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Sale Receipt #</th>
                  <th className="px-6 py-3.5">Timestamp</th>
                  <th className="px-6 py-3.5">Items Sold</th>
                  <th className="px-6 py-3.5">Gross Revenue</th>
                  <th className="px-6 py-3.5">Cost of Goods</th>
                  <th className="px-6 py-3.5">Gross Profit</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {sales.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-slate-900">{s.sale_number}</td>
                    <td className="px-6 py-4 text-slate-500 font-mono text-[11px]">
                      {new Date(s.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-slate-800">
                        {s.items?.reduce((acc, it) => acc + it.quantity, 0) || 0} units
                      </span>{' '}
                      <span className="text-slate-400 text-[11px]">({s.items?.length || 0} lines)</span>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-900">
                      ₹{Number(s.total_amount).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 font-mono text-slate-500">
                      ₹{Number(s.total_cost).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-emerald-600">
                      ₹{Number(s.gross_profit).toFixed(2)}
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant={s.status === 'completed' ? 'success' : 'danger'}>
                        {s.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-1">
                        <button
                          onClick={() => {
                            setViewingSale(s);
                            setIsViewOpen(true);
                          }}
                          title="View Receipt Details"
                          className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {isOwner && s.status === 'completed' && (
                          <button
                            onClick={() => handleOpenCancel(s)}
                            title="Cancel & Revert Stock"
                            className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          >
                            <RotateCcw className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Sale Details / Receipt Modal */}
      <Modal
        isOpen={isViewOpen}
        onClose={() => setIsViewOpen(false)}
        title={`Receipt Details: ${viewingSale?.sale_number}`}
        maxWidth="max-w-md"
      >
        {viewingSale && (
          <div className="space-y-4 text-xs font-sans">
            <div className="p-4 border border-slate-200 rounded-xl bg-slate-50/50 space-y-3">
              <div className="text-center pb-3 border-b border-slate-200">
                <h4 className="font-extrabold text-base text-slate-900">StockSense Store</h4>
                <p className="text-[11px] text-slate-500">Official Sales Receipt</p>
                <p className="text-[11px] font-mono text-slate-500 mt-1">{viewingSale.sale_number}</p>
                <p className="text-[10px] text-slate-400">
                  {new Date(viewingSale.created_at).toLocaleString()} • Logged by: {viewingSale.user_name || 'Staff'}
                </p>
                {viewingSale.status === 'cancelled' && (
                  <div className="mt-2 p-1.5 bg-rose-100 text-rose-800 font-bold rounded-lg text-xs">
                    VOIDED: {viewingSale.cancellation_reason}
                  </div>
                )}
              </div>

              {/* Items Breakdown */}
              <div className="space-y-1.5 py-1">
                <div className="flex justify-between font-bold text-[11px] text-slate-700 border-b border-slate-200 pb-1">
                  <span>Item (Batch)</span>
                  <span>Qty × Price</span>
                  <span>Total</span>
                </div>
                {viewingSale.items.map((it) => (
                  <div key={it.id} className="flex justify-between text-[11px] text-slate-600">
                    <div className="truncate max-w-[150px]">
                      <span className="font-medium text-slate-900 block truncate">{it.product_name}</span>
                      <span className="text-[10px] font-mono text-slate-400">Lot: {it.batch_number}</span>
                    </div>
                    <span className="font-mono">
                      {it.quantity} × ₹{Number(it.unit_price).toFixed(2)}
                    </span>
                    <span className="font-mono font-bold text-slate-900">
                      ₹{Number(it.line_subtotal).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>

              {/* Financial Totals */}
              <div className="pt-2 border-t border-slate-200 space-y-1 font-mono text-[11px]">
                <div className="flex justify-between text-slate-500">
                  <span>Subtotal:</span>
                  <span>₹{Number(viewingSale.subtotal).toFixed(2)}</span>
                </div>
                {Number(viewingSale.discount_amount) > 0 && (
                  <div className="flex justify-between text-emerald-600">
                    <span>Discount:</span>
                    <span>-₹{Number(viewingSale.discount_amount).toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm font-extrabold text-slate-900 pt-1 border-t border-slate-200">
                  <span>Total Paid:</span>
                  <span>₹{Number(viewingSale.total_amount).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-slate-500 text-[10px] pt-1 border-t border-slate-100">
                  <span>Calculated COGS:</span>
                  <span>₹{Number(viewingSale.total_cost).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-emerald-600 font-bold text-[10px]">
                  <span>Estimated Gross Profit:</span>
                  <span>₹{Number(viewingSale.gross_profit).toFixed(2)}</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setIsViewOpen(false)}
                className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg font-semibold"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => window.print()}
                className="flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print</span>
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Sale Cancellation Confirmation Modal */}
      <Modal
        isOpen={Boolean(cancellingSale)}
        onClose={() => setCancellingSale(null)}
        title={`Cancel Sale: ${cancellingSale?.sale_number}`}
      >
        <form onSubmit={handleConfirmCancel} className="space-y-4 text-xs">
          {cancelError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{cancelError}</span>
            </div>
          )}

          <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl space-y-1">
            <p className="font-bold">Auditable Reversal Warning:</p>
            <p className="text-[11px]">
              Cancelling this sale will automatically restore all batch inventory quantities via
              customer return ledger entries and mark the transaction as void.
            </p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 uppercase mb-1">
              Cancellation / Return Reason *
            </label>
            <textarea
              required
              rows={3}
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Provide reason for audit records..."
              className="w-full px-3 py-2 rounded-lg border border-slate-300"
            />
          </div>

          <div className="flex justify-end space-x-2 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setCancellingSale(null)}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingCancel}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg font-semibold disabled:opacity-50"
            >
              {submittingCancel ? 'Reversing...' : 'Confirm Reversal & Restore Stock'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

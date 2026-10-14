import React, { useState, useEffect } from 'react';
import {
  Layers,
  Search,
  Filter,
  SlidersHorizontal,
  AlertCircle,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Batch, Product } from '../types';
import { Badge, Modal, LoadingSpinner, EmptyState } from '../components/common';
import { useAuth } from '../context/AuthContext';

export const Batches: React.FC = () => {
  const { isOwner } = useAuth();
  const [batches, setBatches] = useState<Batch[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedProduct, setSelectedProduct] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [search, setSearch] = useState<string>('');

  // Adjustment Modal
  const [isAdjustModalOpen, setIsAdjustModalOpen] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<Batch | null>(null);
  const [adjQty, setAdjQty] = useState('');
  const [adjReason, setAdjReason] = useState('Recount / Stock Audit Correction');
  const [adjError, setAdjError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedProduct) params.product_id = selectedProduct;
      if (selectedStatus) params.status = selectedStatus;

      const [batchRes, prodRes] = await Promise.all([
        apiClient.getBatches(params),
        apiClient.getProducts(),
      ]);
      setBatches(batchRes.data);
      setProducts(prodRes.data);
    } catch (err) {
      console.error('Error fetching batch data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedProduct, selectedStatus]);

  const prodMap = React.useMemo(() => {
    const map = new Map<number, Product>();
    products.forEach((p) => map.set(p.id, p));
    return map;
  }, [products]);

  const filteredBatches = batches.filter((b) => {
    if (!search) return true;
    const p = prodMap.get(b.product_id);
    const searchLower = search.toLowerCase();
    return (
      b.batch_number.toLowerCase().includes(searchLower) ||
      (p && p.name.toLowerCase().includes(searchLower)) ||
      (p && p.sku.toLowerCase().includes(searchLower))
    );
  });

  const handleOpenAdjust = (batch: Batch) => {
    setSelectedBatch(batch);
    setAdjQty('0');
    setAdjReason('Physical Stock Audit Recount');
    setAdjError('');
    setIsAdjustModalOpen(true);
  };

  const handleAdjustSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatch) return;
    setAdjError('');
    setSubmitting(true);

    try {
      await apiClient.adjustBatch(selectedBatch.id, {
        adjustment_quantity: Number(adjQty),
        reason: adjReason,
      });
      setIsAdjustModalOpen(false);
      fetchData();
    } catch (err: any) {
      setAdjError(err.response?.data?.detail || 'Adjustment failed');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Batch Inventory Tracker</h1>
          <p className="text-xs text-slate-500 mt-1">
            Track individual stock receipts, lot codes, expiration horizons, and perform auditable adjustments
          </p>
        </div>
        <button
          onClick={() => fetchData()}
          className="flex items-center space-x-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Batches</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by lot/batch number, product name, or SKU..."
            className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          <select
            value={selectedProduct}
            onChange={(e) => setSelectedProduct(e.target.value)}
            className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 max-w-xs"
          >
            <option value="">All Products</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.sku})
              </option>
            ))}
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Batch Statuses</option>
            <option value="active">Active (On Hand)</option>
            <option value="depleted">Depleted (0 Stock)</option>
            <option value="expired">Expired</option>
          </select>
        </div>
      </div>

      {/* Batches Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingSpinner label="Loading batches..." />
        ) : filteredBatches.length === 0 ? (
          <EmptyState
            title="No Batches Found"
            description="No inventory batches match your active search or filter selection."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Batch / Lot</th>
                  <th className="px-6 py-3.5">Product & SKU</th>
                  <th className="px-6 py-3.5">Available / Received</th>
                  <th className="px-6 py-3.5">Expiry Horizon</th>
                  <th className="px-6 py-3.5">Unit Cost</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredBatches.map((b) => {
                  const prod = prodMap.get(b.product_id);
                  return (
                    <tr key={b.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4 font-mono font-bold text-slate-900">{b.batch_number}</td>
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-900">{prod?.name || `Product #${b.product_id}`}</div>
                        <div className="text-[11px] text-slate-400 font-mono">SKU: {prod?.sku}</div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-bold text-slate-900 text-sm">{b.current_quantity}</span>
                        <span className="text-slate-400 text-[11px]">
                          {' '}
                          / {b.quantity_received} {prod?.unit || 'units'}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {b.expiry_date ? (
                          <div>
                            <span className="font-semibold text-slate-900">{b.expiry_date}</span>
                            {typeof b.days_until_expiry === 'number' && (
                              <div
                                className={`text-[10px] font-medium mt-0.5 ${
                                  b.days_until_expiry < 0
                                    ? 'text-rose-600 font-bold'
                                    : b.days_until_expiry <= 30
                                    ? 'text-amber-600 font-semibold'
                                    : 'text-slate-400'
                                }`}
                              >
                                {b.days_until_expiry < 0
                                  ? `Expired ${Math.abs(b.days_until_expiry)}d ago`
                                  : `${b.days_until_expiry}d left`}
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400">Non-expiring</span>
                        )}
                      </td>
                      <td className="px-6 py-4 font-mono font-medium">₹{Number(b.unit_cost).toFixed(2)}</td>
                      <td className="px-6 py-4">
                        <Badge
                          variant={
                            b.status === 'active'
                              ? 'success'
                              : b.status === 'expired'
                              ? 'danger'
                              : 'neutral'
                          }
                        >
                          {b.status}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 text-right">
                        {isOwner && (
                          <button
                            onClick={() => handleOpenAdjust(b)}
                            title="Adjust Stock Quantity"
                            className="inline-flex items-center space-x-1 px-2.5 py-1.5 text-xs text-indigo-700 bg-indigo-50 hover:bg-indigo-100 rounded-lg font-medium transition-colors"
                          >
                            <SlidersHorizontal className="w-3.5 h-3.5" />
                            <span>Adjust</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Stock Adjustment Modal */}
      <Modal
        isOpen={isAdjustModalOpen}
        onClose={() => setIsAdjustModalOpen(false)}
        title={`Adjust Stock: Batch ${selectedBatch?.batch_number}`}
      >
        <form onSubmit={handleAdjustSubmit} className="space-y-4 text-xs">
          {adjError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{adjError}</span>
            </div>
          )}

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-slate-700">
            <p>
              Current Available Quantity:{' '}
              <span className="font-bold font-mono text-slate-900">{selectedBatch?.current_quantity}</span>
            </p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 uppercase mb-1">
              Quantity Adjustment (+ to add, - to deduct) *
            </label>
            <input
              type="number"
              required
              value={adjQty}
              onChange={(e) => setAdjQty(e.target.value)}
              placeholder="e.g. -2 for damaged, +5 for recount"
              className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono text-sm"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Resulting Stock will be:{' '}
              <span className="font-semibold text-slate-800">
                {(selectedBatch?.current_quantity || 0) + Number(adjQty || 0)}
              </span>
            </p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 uppercase mb-1">Auditable Reason *</label>
            <select
              value={adjReason}
              onChange={(e) => setAdjReason(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
            >
              <option value="Physical Stock Audit Recount">Physical Stock Audit Recount</option>
              <option value="Damaged Stock Removal">Damaged / Broken Stock Removal</option>
              <option value="Expired Stock Removal">Expired Stock Disposal</option>
              <option value="Supplier Replacement Intake">Supplier Replacement Intake</option>
              <option value="Packaging Leakage">Packaging Leakage / Spoilage</option>
            </select>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsAdjustModalOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold disabled:opacity-50"
            >
              {submitting ? 'Updating...' : 'Confirm Stock Adjustment'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

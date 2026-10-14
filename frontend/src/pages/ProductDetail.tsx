import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Package,
  Layers,
  Calendar,
  ClockAlert,
  ArrowLeftRight,
  Plus,
  AlertTriangle,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Product, Batch, StockMovement } from '../types';
import { Badge, Modal, LoadingSpinner, EmptyState } from '../components/common';
import { useAuth } from '../context/AuthContext';

export const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isOwner } = useAuth();

  const [product, setProduct] = useState<Product | null>(null);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [loading, setLoading] = useState(true);

  // New Batch Modal
  const [isBatchModalOpen, setIsBatchModalOpen] = useState(false);
  const [batchNumber, setBatchNumber] = useState('');
  const [qty, setQty] = useState('');
  const [receivedDate, setReceivedDate] = useState(new Date().toISOString().split('T')[0]);
  const [expiryDate, setExpiryDate] = useState('');
  const [unitCost, setUnitCost] = useState('');
  const [batchError, setBatchError] = useState('');
  const [submittingBatch, setSubmittingBatch] = useState(false);

  const fetchDetail = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const [prodRes, movRes] = await Promise.all([
        apiClient.getProduct(Number(id)),
        apiClient.getMovements({ product_id: Number(id) }),
      ]);
      setProduct(prodRes.data);
      setMovements(movRes.data);
    } catch (err) {
      console.error('Failed to load product detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  const handleOpenBatchModal = () => {
    if (!product) return;
    setBatchNumber(`B-${product.sku}-${Math.floor(100 + Math.random() * 900)}`);
    setQty('20');
    setReceivedDate(new Date().toISOString().split('T')[0]);
    setExpiryDate('');
    setUnitCost(String(product.purchase_cost));
    setBatchError('');
    setIsBatchModalOpen(true);
  };

  const handleReceiveBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!product) return;
    setBatchError('');
    setSubmittingBatch(true);
    try {
      await apiClient.receiveBatch({
        product_id: product.id,
        batch_number: batchNumber.trim(),
        quantity_received: Number(qty),
        received_date: receivedDate,
        expiry_date: expiryDate ? expiryDate : undefined,
        unit_cost: Number(unitCost),
        supplier_id: product.supplier_id,
      });
      setIsBatchModalOpen(false);
      fetchDetail();
    } catch (err: any) {
      setBatchError(err.response?.data?.detail || 'Failed to receive batch stock');
    } finally {
      setSubmittingBatch(false);
    }
  };

  if (loading) {
    return <LoadingSpinner label="Loading product & batch history..." />;
  }

  if (!product) {
    return (
      <EmptyState
        title="Product Not Found"
        description="The requested product record does not exist or has been removed."
        actionText="Back to Products"
        onAction={() => navigate('/products')}
      />
    );
  }

  const margin =
    product.selling_price > 0
      ? (((product.selling_price - product.purchase_cost) / product.selling_price) * 100).toFixed(1)
      : '0';

  return (
    <div className="space-y-6">
      {/* Navigation and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/products')}
            className="p-2 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl text-slate-600 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{product.name}</h1>
              <Badge
                variant={
                  product.stock_status === 'in_stock'
                    ? 'success'
                    : product.stock_status === 'low_stock'
                    ? 'warning'
                    : 'danger'
                }
              >
                {product.stock_status === 'in_stock'
                  ? 'In Stock'
                  : product.stock_status === 'low_stock'
                  ? 'Low Stock'
                  : 'Out of Stock'}
              </Badge>
            </div>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              SKU: {product.sku} {product.barcode ? `• Barcode: ${product.barcode}` : ''}
            </p>
          </div>
        </div>

        {isOwner && (
          <button
            onClick={handleOpenBatchModal}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Receive New Batch Stock</span>
          </button>
        )}
      </div>

      {/* Product Summary Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Available Stock
          </span>
          <span className="text-xl font-bold text-slate-900 mt-1 block">
            {product.total_stock}{' '}
            <span className="text-xs font-normal text-slate-500">{product.unit}</span>
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Selling Price
          </span>
          <span className="text-xl font-bold text-slate-900 mt-1 block font-mono">
            ₹{Number(product.selling_price).toFixed(2)}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Purchase Cost
          </span>
          <span className="text-xl font-bold text-slate-700 mt-1 block font-mono">
            ₹{Number(product.purchase_cost).toFixed(2)}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Gross Margin
          </span>
          <span className="text-xl font-bold text-emerald-600 mt-1 block font-mono">
            {margin}%
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Category
          </span>
          <span className="text-sm font-semibold text-slate-800 mt-1 block truncate">
            {product.category_name || 'Unassigned'}
          </span>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Supplier
          </span>
          <span className="text-sm font-semibold text-slate-800 mt-1 block truncate">
            {product.supplier_name || 'Default Supplier'}
          </span>
        </div>
      </div>

      {/* Batches Breakdown Table (FEFO Sequencing) */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Inventory Batches (FEFO Prioritized)</h3>
            <p className="text-xs text-slate-500">
              Batches with earliest expiry dates are prioritized during sales fulfillment
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-600 rounded-lg">
            {product.batches?.length || 0} Batches Recorded
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="px-6 py-3.5">Batch Number</th>
                <th className="px-6 py-3.5">Available Quantity</th>
                <th className="px-6 py-3.5">Received Date</th>
                <th className="px-6 py-3.5">Expiry Date</th>
                <th className="px-6 py-3.5">Unit Cost</th>
                <th className="px-6 py-3.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {product.batches?.map((b) => (
                <tr key={b.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-slate-900">{b.batch_number}</td>
                  <td className="px-6 py-4">
                    <span className="font-bold text-slate-900 text-sm">{b.current_quantity}</span>
                    <span className="text-slate-400 text-[11px]"> / {b.quantity_received} {product.unit}</span>
                  </td>
                  <td className="px-6 py-4 text-slate-500">{b.received_date}</td>
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
                              ? `Expired ${Math.abs(b.days_until_expiry)} days ago`
                              : `${b.days_until_expiry} days remaining`}
                          </div>
                        )}
                      </div>
                    ) : (
                      <span className="text-slate-400">Non-expiring</span>
                    )}
                  </td>
                  <td className="px-6 py-4 font-mono">₹{Number(b.unit_cost).toFixed(2)}</td>
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
                </tr>
              ))}
              {(!product.batches || product.batches.length === 0) && (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                    No active or historical inventory batches found for this product.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stock Movements Ledger for this Product */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100">
          <h3 className="text-base font-bold text-slate-900">Audit Movement Ledger</h3>
          <p className="text-xs text-slate-500">Every stock receipt, POS sale, and adjustment logged for this item</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
              <tr>
                <th className="px-6 py-3">Timestamp</th>
                <th className="px-6 py-3">Movement Type</th>
                <th className="px-6 py-3">Quantity Delta</th>
                <th className="px-6 py-3">Batch Number</th>
                <th className="px-6 py-3">Reference / Reason</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {movements.slice(0, 10).map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/80">
                  <td className="px-6 py-3.5 text-slate-500">
                    {new Date(m.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-3.5">
                    <Badge
                      variant={
                        m.movement_type === 'purchase_receipt' || m.movement_type === 'customer_return'
                          ? 'success'
                          : m.movement_type === 'sale'
                          ? 'info'
                          : 'warning'
                      }
                    >
                      {m.movement_type}
                    </Badge>
                  </td>
                  <td className="px-6 py-3.5 font-bold font-mono">
                    <span className={m.quantity > 0 ? 'text-emerald-600' : 'text-slate-900'}>
                      {m.quantity > 0 ? `+${m.quantity}` : m.quantity}
                    </span>
                  </td>
                  <td className="px-6 py-3.5 font-mono text-slate-600">{m.batch_number || '—'}</td>
                  <td className="px-6 py-3.5 text-slate-500">
                    {m.reference_id ? <span className="font-mono text-slate-700 mr-1.5">{m.reference_id}:</span> : ''}
                    {m.reason || '—'}
                  </td>
                </tr>
              ))}
              {movements.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                    No movement records recorded yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Receive Batch Modal */}
      <Modal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
        title={`Receive Stock for ${product.name}`}
      >
        <form onSubmit={handleReceiveBatch} className="space-y-4 text-xs">
          {batchError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{batchError}</span>
            </div>
          )}

          <div>
            <label className="block font-semibold text-slate-700 uppercase mb-1">Batch Number *</label>
            <input
              type="text"
              required
              value={batchNumber}
              onChange={(e) => setBatchNumber(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">Quantity Received *</label>
              <input
                type="number"
                required
                min={1}
                value={qty}
                onChange={(e) => setQty(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">Unit Cost (₹) *</label>
              <input
                type="number"
                step="0.01"
                required
                min={0}
                value={unitCost}
                onChange={(e) => setUnitCost(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">Received Date *</label>
              <input
                type="date"
                required
                value={receivedDate}
                onChange={(e) => setReceivedDate(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300"
              />
            </div>
            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">Expiry Date (Optional)</label>
              <input
                type="date"
                value={expiryDate}
                onChange={(e) => setExpiryDate(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300"
              />
            </div>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsBatchModalOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingBatch}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold disabled:opacity-50"
            >
              {submittingBatch ? 'Receiving...' : 'Confirm Receipt'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

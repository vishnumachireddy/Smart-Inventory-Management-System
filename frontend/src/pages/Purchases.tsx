import React, { useState, useEffect } from 'react';
import {
  PackagePlus,
  Plus,
  Search,
  Filter,
  Eye,
  Trash2,
  Calendar,
  Truck,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { PurchaseReceipt, Supplier, Product } from '../types';
import { Badge, Modal, LoadingSpinner, EmptyState } from '../components/common';
import { useAuth } from '../context/AuthContext';

export const Purchases: React.FC = () => {
  const { isOwner } = useAuth();
  const [purchases, setPurchases] = useState<PurchaseReceipt[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // New Purchase Receipt Modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedSupplier, setSelectedSupplier] = useState('');
  const [receivedDate, setReceivedDate] = useState(new Date().toISOString().split('T')[0]);
  const [notes, setNotes] = useState('');
  const [receiptItems, setReceiptItems] = useState<
    { product_id: string; batch_number: string; quantity: string; unit_cost: string; expiry_date: string }[]
  >([]);
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // View Receipt Modal
  const [viewingReceipt, setViewingReceipt] = useState<PurchaseReceipt | null>(null);

  const fetchPurchases = async () => {
    setLoading(true);
    try {
      const [pRes, sRes, prodRes] = await Promise.all([
        apiClient.getPurchases(),
        apiClient.getSuppliers(),
        apiClient.getProducts(),
      ]);
      setPurchases(pRes.data);
      setSuppliers(sRes.data);
      setProducts(prodRes.data);
    } catch (err) {
      console.error('Failed to load purchases:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchases();
  }, []);

  const handleOpenNew = () => {
    setSelectedSupplier(suppliers[0] ? String(suppliers[0].id) : '');
    setReceivedDate(new Date().toISOString().split('T')[0]);
    setNotes('');
    setFormError('');
    setReceiptItems([
      {
        product_id: products[0] ? String(products[0].id) : '',
        batch_number: `BATCH-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
        quantity: '50',
        unit_cost: products[0] ? String(products[0].purchase_cost) : '10.00',
        expiry_date: '',
      },
    ]);
    setIsModalOpen(true);
  };

  const handleAddItemLine = () => {
    setReceiptItems((prev) => [
      ...prev,
      {
        product_id: products[0] ? String(products[0].id) : '',
        batch_number: `BATCH-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`,
        quantity: '20',
        unit_cost: products[0] ? String(products[0].purchase_cost) : '10.00',
        expiry_date: '',
      },
    ]);
  };

  const handleRemoveItemLine = (index: number) => {
    setReceiptItems((prev) => prev.filter((_, i) => i !== index));
  };

  const handleItemChange = (index: number, field: string, val: string) => {
    setReceiptItems((prev) =>
      prev.map((item, i) => {
        if (i !== index) return item;
        const updated = { ...item, [field]: val };
        if (field === 'product_id') {
          const p = products.find((prod) => String(prod.id) === val);
          if (p) {
            updated.unit_cost = String(p.purchase_cost);
          }
        }
        return updated;
      })
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (receiptItems.length === 0) {
      setFormError('Please add at least one item line');
      return;
    }
    setFormError('');
    setSubmitting(true);

    try {
      const payload = {
        supplier_id: Number(selectedSupplier),
        received_date: receivedDate,
        notes: notes.trim() || undefined,
        items: receiptItems.map((it) => ({
          product_id: Number(it.product_id),
          batch_number: it.batch_number.trim(),
          quantity: Number(it.quantity),
          unit_cost: Number(it.unit_cost),
          expiry_date: it.expiry_date ? it.expiry_date : undefined,
        })),
      };

      await apiClient.createPurchase(payload);
      setIsModalOpen(false);
      fetchPurchases();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to record purchase receipt');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Purchase Receipts</h1>
          <p className="text-xs text-slate-500 mt-1">
            Receive vendor shipments into new inventory batches with supplier cost logs
          </p>
        </div>
        {isOwner && (
          <button
            onClick={handleOpenNew}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-xs font-semibold shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Receive Purchase Shipment</span>
          </button>
        )}
      </div>

      {/* Receipts Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingSpinner label="Fetching purchase orders..." />
        ) : purchases.length === 0 ? (
          <EmptyState
            title="No Purchase Receipts"
            description="No supplier purchase shipments recorded yet."
            actionText={isOwner ? 'Record First Shipment' : undefined}
            onAction={isOwner ? handleOpenNew : undefined}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Receipt Number</th>
                  <th className="px-6 py-3.5">Supplier</th>
                  <th className="px-6 py-3.5">Received Date</th>
                  <th className="px-6 py-3.5">Total Lots Received</th>
                  <th className="px-6 py-3.5">Total Invoice Cost</th>
                  <th className="px-6 py-3.5">Notes</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {purchases.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-slate-900">{r.receipt_number}</td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{r.supplier_name}</td>
                    <td className="px-6 py-4 text-slate-500 font-mono text-[11px]">{r.received_date}</td>
                    <td className="px-6 py-4">
                      <span className="font-semibold text-slate-900">
                        {r.items.reduce((acc, it) => acc + it.quantity, 0)} units
                      </span>{' '}
                      <span className="text-slate-400 text-[11px]">({r.items.length} lots)</span>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-900">
                      ₹{Number(r.total_cost).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-slate-500 truncate max-w-xs">{r.notes || '—'}</td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => setViewingReceipt(r)}
                        className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Record Purchase Shipment Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Record Supplier Purchase Shipment"
        maxWidth="max-w-3xl"
      >
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {formError && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{formError}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div>
              <label className="block font-semibold text-slate-700 uppercase mb-1">Supplier *</label>
              <select
                required
                value={selectedSupplier}
                onChange={(e) => setSelectedSupplier(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-300 bg-white"
              >
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

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
              <label className="block font-semibold text-slate-700 uppercase mb-1">Delivery Notes</label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Invoice or challan #..."
                className="w-full px-3 py-2 rounded-lg border border-slate-300"
              />
            </div>
          </div>

          {/* Line Items Table */}
          <div className="pt-2">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <span className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">
                Shipment Batch Items
              </span>
              <button
                type="button"
                onClick={handleAddItemLine}
                className="flex items-center space-x-1 text-xs text-indigo-600 font-semibold hover:text-indigo-800"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Item Line</span>
              </button>
            </div>

            <div className="space-y-3 mt-3 max-h-60 overflow-y-auto pr-1">
              {receiptItems.map((item, idx) => (
                <div
                  key={idx}
                  className="grid grid-cols-12 gap-2 p-2.5 rounded-lg border border-slate-200 bg-slate-50 items-center"
                >
                  <div className="col-span-4">
                    <label className="block text-[10px] text-slate-500 font-medium mb-0.5">Product</label>
                    <select
                      value={item.product_id}
                      onChange={(e) => handleItemChange(idx, 'product_id', e.target.value)}
                      className="w-full px-2 py-1.5 text-xs rounded border border-slate-300 bg-white"
                    >
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="col-span-3">
                    <label className="block text-[10px] text-slate-500 font-medium mb-0.5">Batch / Lot #</label>
                    <input
                      type="text"
                      required
                      value={item.batch_number}
                      onChange={(e) => handleItemChange(idx, 'batch_number', e.target.value)}
                      className="w-full px-2 py-1.5 text-xs rounded border border-slate-300 font-mono"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-[10px] text-slate-500 font-medium mb-0.5">Quantity</label>
                    <input
                      type="number"
                      required
                      min={1}
                      value={item.quantity}
                      onChange={(e) => handleItemChange(idx, 'quantity', e.target.value)}
                      className="w-full px-2 py-1.5 text-xs rounded border border-slate-300 font-mono"
                    />
                  </div>

                  <div className="col-span-2">
                    <label className="block text-[10px] text-slate-500 font-medium mb-0.5">Unit Cost (₹)</label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      min={0}
                      value={item.unit_cost}
                      onChange={(e) => handleItemChange(idx, 'unit_cost', e.target.value)}
                      className="w-full px-2 py-1.5 text-xs rounded border border-slate-300 font-mono"
                    />
                  </div>

                  <div className="col-span-1 text-right pt-4">
                    {receiptItems.length > 1 && (
                      <button
                        type="button"
                        onClick={() => handleRemoveItemLine(idx)}
                        className="text-slate-400 hover:text-rose-600 p-1"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-end space-x-2 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg font-semibold"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold disabled:opacity-50"
            >
              {submitting ? 'Recording Shipment...' : 'Save & Update Stock'}
            </button>
          </div>
        </form>
      </Modal>

      {/* View Purchase Receipt Modal */}
      <Modal
        isOpen={Boolean(viewingReceipt)}
        onClose={() => setViewingReceipt(null)}
        title={`Purchase Receipt: ${viewingReceipt?.receipt_number}`}
      >
        {viewingReceipt && (
          <div className="space-y-4 text-xs">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1">
              <p>
                <span className="font-semibold text-slate-500">Supplier:</span>{' '}
                <span className="font-bold text-slate-900">{viewingReceipt.supplier_name}</span>
              </p>
              <p>
                <span className="font-semibold text-slate-500">Received Date:</span>{' '}
                <span className="font-mono text-slate-800">{viewingReceipt.received_date}</span>
              </p>
              {viewingReceipt.notes && (
                <p>
                  <span className="font-semibold text-slate-500">Notes:</span>{' '}
                  <span className="text-slate-700">{viewingReceipt.notes}</span>
                </p>
              )}
            </div>

            <div className="divide-y divide-slate-100 border border-slate-200 rounded-lg overflow-hidden">
              <div className="p-2.5 bg-slate-100 font-bold text-slate-700 flex justify-between">
                <span>Product (Batch)</span>
                <span>Qty × Cost</span>
                <span>Total</span>
              </div>
              {viewingReceipt.items.map((it) => (
                <div key={it.id} className="p-2.5 flex justify-between text-slate-800 bg-white">
                  <div>
                    <span className="font-semibold block">{it.product_name}</span>
                    <span className="text-[10px] font-mono text-slate-400">Lot: {it.batch_number}</span>
                  </div>
                  <span className="font-mono">
                    {it.quantity} × ₹{Number(it.unit_cost).toFixed(2)}
                  </span>
                  <span className="font-mono font-bold text-slate-900">
                    ₹{(it.quantity * Number(it.unit_cost)).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>

            <div className="flex justify-between items-center text-sm font-bold border-t border-slate-200 pt-3">
              <span>Total Shipment Cost:</span>
              <span className="font-mono text-indigo-600 text-base">
                ₹{Number(viewingReceipt.total_cost).toFixed(2)}
              </span>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

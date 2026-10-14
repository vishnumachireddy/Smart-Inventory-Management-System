import React, { useState, useEffect } from 'react';
import { ArrowLeftRight, Search, Filter, RefreshCw, Calendar } from 'lucide-react';
import { apiClient } from '../api/client';
import { StockMovement, Product } from '../types';
import { Badge, LoadingSpinner, EmptyState } from '../components/common';

export const Movements: React.FC = () => {
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [selectedProduct, setSelectedProduct] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');

  const fetchMovements = async () => {
    setLoading(true);
    try {
      const params: any = {};
      if (selectedProduct) params.product_id = selectedProduct;
      if (selectedType) params.movement_type = selectedType;

      const [movRes, prodRes] = await Promise.all([
        apiClient.getMovements(params),
        apiClient.getProducts(),
      ]);
      setMovements(movRes.data);
      setProducts(prodRes.data);
    } catch (err) {
      console.error('Failed to fetch stock movements:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMovements();
  }, [selectedProduct, selectedType]);

  const movementTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      purchase_receipt: 'Purchase Receipt',
      sale: 'POS Customer Sale',
      customer_return: 'Customer Return',
      supplier_return: 'Supplier Return',
      damaged_stock: 'Damaged Stock',
      expired_removal: 'Expired Stock Disposal',
      manual_adjustment: 'Manual Audit Adjustment',
    };
    return labels[type] || type;
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Stock Movement Ledger</h1>
          <p className="text-xs text-slate-500 mt-1">
            Immutable transaction log of every stock intake, sale deduction, return, and inventory adjustment
          </p>
        </div>
        <button
          onClick={fetchMovements}
          className="flex items-center space-x-1.5 px-3 py-2 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Ledger</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-wrap gap-3">
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
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Movement Types</option>
          <option value="sale">POS Sale (Reduction)</option>
          <option value="purchase_receipt">Purchase Receipt (Intake)</option>
          <option value="customer_return">Customer Return (Restoration)</option>
          <option value="damaged_stock">Damaged Stock</option>
          <option value="expired_removal">Expired Stock Disposal</option>
          <option value="manual_adjustment">Manual Audit Adjustment</option>
        </select>

        {(selectedProduct || selectedType) && (
          <button
            onClick={() => {
              setSelectedProduct('');
              setSelectedType('');
            }}
            className="px-3 py-2 text-xs text-rose-600 hover:bg-rose-50 rounded-xl font-medium transition-colors"
          >
            Reset Filters
          </button>
        )}
      </div>

      {/* Ledger Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <LoadingSpinner label="Auditing ledger transactions..." />
        ) : movements.length === 0 ? (
          <EmptyState
            title="No Movement Records"
            description="No inventory movement records match your criteria."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider border-b border-slate-100">
                <tr>
                  <th className="px-6 py-3.5">Timestamp</th>
                  <th className="px-6 py-3.5">Movement Type</th>
                  <th className="px-6 py-3.5">Product & SKU</th>
                  <th className="px-6 py-3.5">Batch / Lot</th>
                  <th className="px-6 py-3.5">Quantity Change</th>
                  <th className="px-6 py-3.5">Reference Transaction</th>
                  <th className="px-6 py-3.5">Reason / Logged By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {movements.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-6 py-4 text-slate-500 font-mono text-[11px]">
                      {new Date(m.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      <Badge
                        variant={
                          m.movement_type === 'purchase_receipt' || m.movement_type === 'customer_return'
                            ? 'success'
                            : m.movement_type === 'sale'
                            ? 'info'
                            : 'warning'
                        }
                      >
                        {movementTypeLabel(m.movement_type)}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900">{m.product_name || `Product #${m.product_id}`}</div>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-700">
                      {m.batch_number || '—'}
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-sm">
                      <span className={m.quantity > 0 ? 'text-emerald-600' : 'text-slate-900'}>
                        {m.quantity > 0 ? `+${m.quantity}` : m.quantity}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-slate-600">
                      {m.reference_id || '—'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-slate-800">{m.reason || '—'}</div>
                      {m.user_name && (
                        <div className="text-[10px] text-slate-400 mt-0.5">By: {m.user_name}</div>
                      )}
                    </td>
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

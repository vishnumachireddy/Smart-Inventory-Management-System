import React, { useState, useEffect } from 'react';
import {
  ShoppingCart,
  Search,
  Plus,
  Minus,
  Trash2,
  Printer,
  CheckCircle,
  AlertCircle,
  CreditCard,
  IndianRupee,
  QrCode,
  Tag,
  Store,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { Product, Sale } from '../types';
import { Badge, Modal, LoadingSpinner } from '../components/common';

interface CartItem {
  product: Product;
  quantity: number;
}

export const PosSale: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [categories, setCategories] = useState<any[]>([]);

  // Cart State
  const [cart, setCart] = useState<CartItem[]>([]);
  const [discount, setDiscount] = useState('0');
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'upi' | 'card'>('cash');
  const [submitting, setSubmitting] = useState(false);
  const [saleError, setSaleError] = useState('');

  // Receipt Modal State
  const [completedSale, setCompletedSale] = useState<Sale | null>(null);
  const [isReceiptOpen, setIsReceiptOpen] = useState(false);

  const fetchCatalog = async () => {
    setLoading(true);
    try {
      const [prodRes, catRes] = await Promise.all([
        apiClient.getProducts({ stock_status: 'in_stock' }),
        apiClient.getCategories(),
      ]);
      setProducts(prodRes.data);
      setCategories(catRes.data);
    } catch (err) {
      console.error('Failed to load catalog for POS:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalog();
  }, []);

  const addToCart = (product: Product) => {
    setSaleError('');
    setCart((prev) => {
      const existing = prev.find((item) => item.product.id === product.id);
      if (existing) {
        if (existing.quantity >= product.total_stock) {
          setSaleError(`Cannot add more than available stock (${product.total_stock} ${product.unit})`);
          return prev;
        }
        return prev.map((item) =>
          item.product.id === product.id ? { ...item, quantity: item.quantity + 1 } : item
        );
      } else {
        return [...prev, { product, quantity: 1 }];
      }
    });
  };

  const updateQuantity = (productId: number, delta: number) => {
    setSaleError('');
    setCart((prev) =>
      prev
        .map((item) => {
          if (item.product.id === productId) {
            const newQty = item.quantity + delta;
            if (newQty > item.product.total_stock) {
              setSaleError(`Cannot exceed available stock (${item.product.total_stock})`);
              return item;
            }
            return newQty > 0 ? { ...item, quantity: newQty } : null;
          }
          return item;
        })
        .filter(Boolean) as CartItem[]
    );
  };

  const removeFromCart = (productId: number) => {
    setCart((prev) => prev.filter((item) => item.product.id !== productId));
  };

  const clearCart = () => {
    setCart([]);
    setDiscount('0');
    setSaleError('');
  };

  // Calculations
  const subtotal = cart.reduce(
    (acc, item) => acc + item.quantity * Number(item.product.selling_price),
    0
  );
  const discountVal = Math.min(subtotal, Math.max(0, Number(discount) || 0));
  const totalAmount = Math.max(0, subtotal - discountVal);

  const handleCheckout = async () => {
    if (cart.length === 0) return;
    setSaleError('');
    setSubmitting(true);

    try {
      const payload = {
        items: cart.map((item) => ({
          product_id: item.product.id,
          quantity: item.quantity,
          unit_price: Number(item.product.selling_price),
        })),
        discount_amount: discountVal,
        payment_method: paymentMethod,
      };

      const res = await apiClient.createSale(payload);
      setCompletedSale(res.data);
      setIsReceiptOpen(true);
      clearCart();
      fetchCatalog(); // Refresh available stocks
    } catch (err: any) {
      setSaleError(err.response?.data?.detail || 'Failed to complete sale transaction');
    } finally {
      setSubmitting(false);
    }
  };

  const filteredProducts = products.filter((p) => {
    const matchesSearch =
      !search ||
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase()) ||
      (p.barcode && p.barcode.includes(search));

    const matchesCategory =
      !selectedCategory || (p.category_id && String(p.category_id) === selectedCategory);

    return matchesSearch && matchesCategory;
  });

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col lg:flex-row gap-6">
      {/* Left: Product Catalog Selection */}
      <div className="flex-1 flex flex-col bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Search & Filter Bar */}
        <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search or scan barcode (name, SKU, barcode)..."
              className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Product Cards Grid */}
        <div className="flex-1 p-4 overflow-y-auto">
          {loading ? (
            <LoadingSpinner label="Loading active store catalog..." />
          ) : filteredProducts.length === 0 ? (
            <p className="text-center text-xs text-slate-400 py-12">No eligible sellable products found.</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-3">
              {filteredProducts.map((p) => (
                <div
                  key={p.id}
                  onClick={() => addToCart(p)}
                  className="p-3.5 rounded-xl border border-slate-200 hover:border-indigo-500 hover:shadow-md cursor-pointer transition-all flex flex-col justify-between bg-white group active:scale-[0.98]"
                >
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider truncate">
                        {p.sku}
                      </span>
                      <span className="text-[10px] font-semibold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">
                        {p.total_stock} {p.unit}
                      </span>
                    </div>
                    <h4 className="text-xs font-bold text-slate-900 line-clamp-2 group-hover:text-indigo-600 transition-colors">
                      {p.name}
                    </h4>
                  </div>
                  <div className="mt-3 flex items-center justify-between pt-2 border-t border-slate-50">
                    <span className="text-sm font-extrabold text-slate-900 font-mono">
                      ₹{Number(p.selling_price).toFixed(2)}
                    </span>
                    <div className="w-6 h-6 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center group-hover:bg-indigo-600 group-hover:text-white transition-colors">
                      <Plus className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right: Cart & Checkout Pane */}
      <div className="w-full lg:w-96 bg-white rounded-2xl border border-slate-200 shadow-sm flex flex-col overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center space-x-2">
            <ShoppingCart className="w-5 h-5 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900">Current Order</h3>
          </div>
          {cart.length > 0 && (
            <button
              onClick={clearCart}
              className="text-xs text-rose-600 hover:text-rose-800 font-semibold"
            >
              Clear Cart
            </button>
          )}
        </div>

        {/* Error Alert */}
        {saleError && (
          <div className="m-3 p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl flex items-start space-x-2 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span>{saleError}</span>
          </div>
        )}

        {/* Cart Items List */}
        <div className="flex-1 p-4 overflow-y-auto divide-y divide-slate-100">
          {cart.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <ShoppingCart className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <p className="text-xs font-medium">Cart is empty</p>
              <p className="text-[11px] text-slate-400 mt-0.5">Click catalog products to add to order</p>
            </div>
          ) : (
            cart.map((item) => (
              <div key={item.product.id} className="py-3 flex items-center justify-between text-xs">
                <div className="flex-1 min-w-0 pr-2">
                  <h5 className="font-bold text-slate-900 truncate">{item.product.name}</h5>
                  <p className="text-[11px] text-slate-400 font-mono">
                    ₹{Number(item.product.selling_price).toFixed(2)} each
                  </p>
                </div>

                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1 bg-slate-100 rounded-lg p-0.5">
                    <button
                      onClick={() => updateQuantity(item.product.id, -1)}
                      className="p-1 hover:bg-white rounded text-slate-600 transition-colors"
                    >
                      <Minus className="w-3 h-3" />
                    </button>
                    <span className="w-6 text-center font-bold text-slate-900 text-xs">
                      {item.quantity}
                    </span>
                    <button
                      onClick={() => updateQuantity(item.product.id, 1)}
                      className="p-1 hover:bg-white rounded text-slate-600 transition-colors"
                    >
                      <Plus className="w-3 h-3" />
                    </button>
                  </div>
                  <span className="font-bold text-slate-900 font-mono w-16 text-right">
                    ₹{(item.quantity * Number(item.product.selling_price)).toFixed(2)}
                  </span>
                  <button
                    onClick={() => removeFromCart(item.product.id)}
                    className="text-slate-300 hover:text-rose-600 p-1"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Checkout Controls */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50 space-y-3 text-xs">
          {/* Discount Input */}
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-600">Discount (₹)</span>
            <input
              type="number"
              min={0}
              step="1"
              value={discount}
              onChange={(e) => setDiscount(e.target.value)}
              className="w-24 px-2 py-1 text-right text-xs rounded-lg border border-slate-300 font-mono font-bold"
            />
          </div>

          {/* Payment Method Tabs */}
          <div>
            <span className="font-semibold text-slate-600 block mb-1.5">Payment Method</span>
            <div className="grid grid-cols-3 gap-1.5">
              {(['cash', 'upi', 'card'] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setPaymentMethod(m)}
                  className={`py-1.5 rounded-lg text-xs font-semibold capitalize transition-colors ${
                    paymentMethod === m
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>

          {/* Totals */}
          <div className="space-y-1 pt-2 border-t border-slate-200">
            <div className="flex justify-between text-slate-500">
              <span>Subtotal</span>
              <span className="font-mono">₹{subtotal.toFixed(2)}</span>
            </div>
            {discountVal > 0 && (
              <div className="flex justify-between text-emerald-600">
                <span>Discount</span>
                <span className="font-mono">-₹{discountVal.toFixed(2)}</span>
              </div>
            )}
            <div className="flex justify-between text-sm font-extrabold text-slate-900 pt-1 border-t border-slate-200">
              <span>Total Due</span>
              <span className="font-mono text-indigo-600">₹{totalAmount.toFixed(2)}</span>
            </div>
          </div>

          {/* Submit Button */}
          <button
            onClick={handleCheckout}
            disabled={cart.length === 0 || submitting}
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl text-sm shadow-sm transition-all disabled:opacity-50 flex items-center justify-center space-x-2 active:scale-[0.98]"
          >
            <span>{submitting ? 'Allocating FEFO Stock...' : 'Complete & Generate Receipt'}</span>
          </button>
        </div>
      </div>

      {/* Printable Receipt Modal */}
      <Modal
        isOpen={isReceiptOpen}
        onClose={() => setIsReceiptOpen(false)}
        title="Sale Receipt"
        maxWidth="max-w-md"
      >
        {completedSale && (
          <div className="space-y-4 text-xs font-sans">
            {/* Printable Area */}
            <div id="printable-receipt" className="p-4 border border-slate-200 rounded-xl bg-slate-50/50 space-y-3">
              <div className="text-center pb-3 border-b border-slate-200">
                <h4 className="font-extrabold text-base text-slate-900 tracking-tight">StockSense Retail</h4>
                <p className="text-[11px] text-slate-500">Smart Retail & Fresh Inventory</p>
                <p className="text-[11px] font-mono text-slate-500 mt-1">Receipt: {completedSale.sale_number}</p>
                <p className="text-[10px] text-slate-400">
                  Date: {new Date(completedSale.created_at).toLocaleString()}
                </p>
              </div>

              {/* Items Breakdown */}
              <div className="space-y-1.5 py-1">
                <div className="flex justify-between font-bold text-[11px] text-slate-700 border-b border-slate-200 pb-1">
                  <span>Item (Batch)</span>
                  <span>Qty × Price</span>
                  <span>Total</span>
                </div>
                {completedSale.items.map((it) => (
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
                  <span>₹{Number(completedSale.subtotal).toFixed(2)}</span>
                </div>
                {Number(completedSale.discount_amount) > 0 && (
                  <div className="flex justify-between text-emerald-600">
                    <span>Discount:</span>
                    <span>-₹{Number(completedSale.discount_amount).toFixed(2)}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm font-extrabold text-slate-900 pt-1 border-t border-slate-200">
                  <span>Total Paid:</span>
                  <span>₹{Number(completedSale.total_amount).toFixed(2)}</span>
                </div>
                <div className="flex justify-between text-[10px] text-slate-400 pt-1">
                  <span>Payment Method:</span>
                  <span className="uppercase font-semibold">{completedSale.payment_method}</span>
                </div>
              </div>

              <div className="text-center pt-2 text-[10px] text-slate-400 border-t border-slate-200">
                Thank you for shopping with us!
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-between pt-2">
              <button
                type="button"
                onClick={() => setIsReceiptOpen(false)}
                className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-xs font-semibold"
              >
                Close
              </button>
              <button
                type="button"
                onClick={handlePrint}
                className="flex items-center space-x-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print Receipt</span>
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

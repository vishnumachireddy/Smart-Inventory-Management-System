import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Boxes,
  Clock,
  Sparkles,
  TrendingUp,
  ShieldCheck,
  Mail,
  ArrowRight,
  Database,
  CheckCircle,
  Receipt,
  AlertTriangle,
  Server,
  Layers,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const HomePage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-500 flex items-center justify-center shadow-lg shadow-indigo-500/25">
              <Boxes className="w-6 h-6 text-white" />
            </div>
            <div>
              <span className="text-xl font-black tracking-tight text-white">StockSense</span>
              <span className="hidden sm:inline-block ml-2 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                v1.0 &middot; Neon Serverless
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400 hidden sm:inline">
                  Signed in as <strong className="text-slate-200">{user?.full_name}</strong> ({user?.role})
                </span>
                <Link
                  to="/"
                  className="px-4 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-md shadow-indigo-600/30 transition-all flex items-center gap-1.5"
                >
                  Enter Dashboard <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-4 py-2 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-900 rounded-lg transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-xs font-semibold bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white rounded-lg shadow-md shadow-indigo-600/20 transition-all"
                >
                  Register Store
                </Link>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-24 sm:pt-28 sm:pb-32">
        {/* Glow Effects */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-indigo-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute top-1/3 left-1/3 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[250px] bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          {/* Live Status Pill */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300 mb-8 animate-fade-in shadow-inner">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-semibold text-slate-200">Neon Serverless PostgreSQL</span>
            <span className="text-slate-500">&middot;</span>
            <span className="text-indigo-400 font-mono">Asia/Kolkata</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white max-w-4xl mx-auto leading-tight sm:leading-none">
            Smart Inventory & Expiry Tracker for{' '}
            <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">
              Small Retailers
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Eliminate product expiration write-offs and prevent costly stockouts. StockSense combines strict{' '}
            <strong className="text-slate-200">First Expired, First Out (FEFO)</strong> allocation, machine-learning demand forecasting, and automated daily email audits.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to={isAuthenticated ? '/' : '/login'}
              className="w-full sm:w-auto px-8 py-3.5 bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-600 hover:from-indigo-500 hover:to-blue-500 text-white font-bold rounded-xl shadow-xl shadow-indigo-500/25 transition-all text-sm flex items-center justify-center gap-2 group"
            >
              <span>{isAuthenticated ? 'Open Control Dashboard' : 'Sign In to Demo Store'}</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              to="/register"
              className="w-full sm:w-auto px-7 py-3.5 bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white font-semibold rounded-xl border border-slate-800 transition-colors text-sm"
            >
              Create Owner Account
            </Link>
          </div>

          {/* Quick Credential Hint for Demo */}
          <div className="mt-6 text-xs text-slate-500">
            Demo Credentials &middot; Owner: <span className="text-slate-400 font-mono">owner@stocksense.com / Owner@123</span> &middot; Staff: <span className="text-slate-400 font-mono">staff@stocksense.com / Staff@123</span>
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="py-20 bg-slate-900/50 border-t border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-xs font-bold tracking-wider text-indigo-400 uppercase">Core Capabilities</h2>
            <p className="text-2xl sm:text-3xl font-black text-white mt-2">Engineered for Real Grocery & Pharmacy Operations</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Feature 1 */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all hover:-translate-y-1 group">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center mb-5 border border-amber-500/20 group-hover:scale-110 transition-transform">
                <Clock className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Strict FEFO Batch Allocation</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Prioritizes lots with the nearest expiration date on every POS transaction. Expired batches are automatically blocked from sellable inventory.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all hover:-translate-y-1 group">
              <div className="w-12 h-12 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center mb-5 border border-blue-500/20 group-hover:scale-110 transition-transform">
                <TrendingUp className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Demand Forecasting & Reorder</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Moving average and Random Forest regression models calculate dynamic safety stock and replenishment quantities based on supplier lead times.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all hover:-translate-y-1 group">
              <div className="w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-5 border border-emerald-500/20 group-hover:scale-110 transition-transform">
                <Mail className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Daily Automated Email Audits</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Scheduled background worker audits inventory at 08:00 Asia/Kolkata, generates daily snapshots, and emails structured reports with idempotency protection.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all hover:-translate-y-1 group">
              <div className="w-12 h-12 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center mb-5 border border-purple-500/20 group-hover:scale-110 transition-transform">
                <Receipt className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Fast POS Terminal & Receipts</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Barcode scan support, live cart calculations, tax/discount toggles, and instant printable invoices with auditable customer return reversals.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all hover:-translate-y-1 group">
              <div className="w-12 h-12 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center mb-5 border border-rose-500/20 group-hover:scale-110 transition-transform">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Smart Login Alert Dialog</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Pops up upon user login with 3 segregated tabs for Near Expiry (&le;7d), Low Stock, and Out of Stock with instant one-click resolution actions.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all hover:-translate-y-1 group">
              <div className="w-12 h-12 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-5 border border-indigo-500/20 group-hover:scale-110 transition-transform">
                <Database className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Neon Serverless Persistence</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                Backed by cloud PostgreSQL with resilient connection pooling (pool_pre_ping=True, pool_recycle=300), Alembic migrations, and strict ACID transactions.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto py-8 bg-slate-950 border-t border-slate-900 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-400">StockSense</span> &middot; Smart Inventory & Expiry Tracker
          </div>
          <div>
            Powered by FastAPI &middot; React 19 &middot; Neon Serverless PostgreSQL &middot; scikit-learn
          </div>
        </div>
      </footer>
    </div>
  );
};

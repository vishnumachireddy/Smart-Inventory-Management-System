import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Layers,
  ClockAlert,
  ArrowLeftRight,
  ShoppingCart,
  ReceiptText,
  Truck,
  TrendingUp,
  PackagePlus,
  Bell,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  Store,
  FileSpreadsheet,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useWebSocket } from '../../context/WebSocketContext';
import { apiClient } from '../../api/client';

export const AppLayout: React.FC = () => {
  const { user, logout, isOwner } = useAuth();
  const { isConnected, liveAlertsSummary } = useWebSocket();
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [unreadAlertsCount, setUnreadAlertsCount] = useState<number>(0);

  // Sync unread alerts count instantly from WebSocket feed
  useEffect(() => {
    if (liveAlertsSummary) {
      const activeAlerts = (liveAlertsSummary.near_expiry_count || 0) + 
                           (liveAlertsSummary.low_stock_count || 0) + 
                           (liveAlertsSummary.out_of_stock_count || 0);
      setUnreadAlertsCount(activeAlerts);
    }
  }, [liveAlertsSummary]);

  // Initial fallback load only if socket did not deliver summary within 2s
  useEffect(() => {
    if (liveAlertsSummary) return;
    const t = setTimeout(async () => {
      try {
        const res = await apiClient.getInventorySummary();
        const activeAlerts = (res.data.summary.near_expiry_count || 0) + 
                             (res.data.summary.low_stock_count || 0) + 
                             (res.data.summary.out_of_stock_count || 0);
        setUnreadAlertsCount(activeAlerts);
      } catch {
        // Silently ignore if not authorized yet
      }
    }, 2000);
    return () => clearTimeout(t);
  }, [liveAlertsSummary]);

  const navigation = [
    {
      group: 'Core Inventory',
      items: [
        { name: 'Dashboard', path: '/', icon: LayoutDashboard },
        { name: 'Products Catalog', path: '/products', icon: Package },
        { name: 'Batch Inventory', path: '/batches', icon: Layers },
        { name: 'Expiry Tracker', path: '/expiry', icon: ClockAlert },
        { name: 'Stock Movements', path: '/movements', icon: ArrowLeftRight },
      ],
    },
    {
      group: 'Sales & Purchases',
      items: [
        { name: 'New POS Sale', path: '/pos', icon: ShoppingCart },
        { name: 'Sales Ledger', path: '/sales', icon: ReceiptText },
        { name: 'Purchase Receipts', path: '/purchases', icon: PackagePlus },
        { name: 'Suppliers Directory', path: '/suppliers', icon: Truck },
      ],
    },
    {
      group: 'Demand & Analytics',
      items: [
        { name: 'Demand Forecasting', path: '/forecasting', icon: TrendingUp },
        { name: 'Reorder Suggestions', path: '/recommendations', icon: FileSpreadsheet },
        { name: 'Analytics & Reports', path: '/analytics', icon: TrendingUp },
      ],
    },
    {
      group: 'Management',
      items: [
        { name: 'Alerts Center', path: '/alerts', icon: Bell, badge: unreadAlertsCount },
        ...(isOwner ? [{ name: 'Staff Accounts', path: '/users', icon: Users }] : []),
        { name: 'Store Settings', path: '/settings', icon: Settings },
        { name: 'Public Showcase', path: '/home', icon: Sparkles },
      ],
    },
  ];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Mobile Top Header */}
      <header className="md:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
            <Store className="w-5 h-5" />
          </div>
          <span className="font-bold text-slate-900 tracking-tight text-lg">StockSense</span>
        </div>
        <div className="flex items-center space-x-2">
          <div
            title={isConnected ? 'Live WebSocket Connected' : 'Connecting WebSocket...'}
            className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${
              isConnected
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
              }`}
            ></span>
            <span>{isConnected ? 'LIVE' : 'SYNC'}</span>
          </div>
          <Link
            to="/alerts"
            className="relative p-2 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100"
          >
            <Bell className="w-5 h-5" />
            {unreadAlertsCount > 0 && (
              <span className="absolute top-1 right-1 w-2.5 h-2.5 bg-rose-500 rounded-full"></span>
            )}
          </Link>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </header>

      {/* Sidebar Navigation */}
      <aside
        className={`fixed md:sticky top-0 left-0 z-30 h-screen w-64 bg-white border-r border-slate-200 flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="px-6 py-5 border-b border-slate-100 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-200">
              <Store className="w-5 h-5" />
            </div>
            <div>
              <span className="font-extrabold text-slate-900 tracking-tight text-lg leading-none block">
                StockSense
              </span>
              <span className="text-[11px] font-medium text-slate-400 tracking-wider uppercase block mt-0.5">
                Smart Retail Tracker
              </span>
            </div>
          </Link>
          <div
            title={isConnected ? 'Live WebSocket Connected' : 'Connecting to real-time feed...'}
            className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold border transition-colors ${
              isConnected
                ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                : 'bg-amber-50 text-amber-700 border-amber-200'
            }`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                isConnected ? 'bg-emerald-500 animate-pulse' : 'bg-amber-400'
              }`}
            ></span>
            <span>{isConnected ? 'LIVE' : 'SYNC'}</span>
          </div>
        </div>

        {/* Quick Action POS Button */}
        <div className="p-4 border-b border-slate-100">
          <Link
            to="/pos"
            onClick={() => setMobileMenuOpen(false)}
            className="w-full flex items-center justify-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2.5 rounded-xl font-medium text-sm shadow-sm shadow-indigo-100 transition-all active:scale-[0.98]"
          >
            <ShoppingCart className="w-4 h-4" />
            <span>Open POS Terminal</span>
          </Link>
        </div>

        {/* Nav Links */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {navigation.map((section) => (
            <div key={section.group}>
              <h4 className="px-3 text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
                {section.group}
              </h4>
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-indigo-50 text-indigo-700 font-semibold'
                          : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <Icon
                          className={`w-4 h-4 ${
                            isActive ? 'text-indigo-600' : 'text-slate-400'
                          }`}
                        />
                        <span>{item.name}</span>
                      </div>
                      {typeof item.badge === 'number' && item.badge > 0 && (
                        <span className="px-2 py-0.5 text-xs font-bold bg-rose-500 text-white rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User Profile Footer */}
        <div className="p-3 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center justify-between p-2 rounded-lg hover:bg-white transition-colors">
            <div className="flex items-center space-x-3 min-w-0">
              <div className="w-8 h-8 rounded-full bg-slate-200 text-slate-700 font-semibold flex items-center justify-center text-xs shrink-0">
                {user?.full_name?.charAt(0) || 'U'}
              </div>
              <div className="truncate">
                <p className="text-sm font-semibold text-slate-800 truncate">{user?.full_name}</p>
                <span className="inline-block px-1.5 py-0.2 text-[10px] font-bold uppercase rounded bg-indigo-100 text-indigo-700">
                  {user?.role === 'shop_owner' ? 'Shop Owner' : 'Staff'}
                </span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign Out"
              className="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Pane */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <div className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

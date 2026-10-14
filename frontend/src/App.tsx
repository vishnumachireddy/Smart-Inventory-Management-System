import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { AppLayout } from './components/layout/AppLayout';
import { HomePage } from './pages/HomePage';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Products } from './pages/Products';
import { ProductDetail } from './pages/ProductDetail';
import { Batches } from './pages/Batches';
import { ExpiryTracker } from './pages/ExpiryTracker';
import { Movements } from './pages/Movements';
import { PosSale } from './pages/PosSale';
import { Sales } from './pages/Sales';
import { Purchases } from './pages/Purchases';
import { Suppliers } from './pages/Suppliers';
import { Forecasting } from './pages/Forecasting';
import { ReorderRecommendations } from './pages/ReorderRecommendations';
import { Alerts } from './pages/Alerts';
import { AnalyticsReports } from './pages/AnalyticsReports';
import { UsersManagement } from './pages/UsersManagement';
import { SettingsPage } from './pages/SettingsPage';
import { LoadingSpinner } from './components/common';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <LoadingSpinner label="Authenticating session..." />
      </div>
    );
  }

  return user ? <>{children}</> : <Navigate to="/login" replace />;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Showcase & Auth Routes */}
            <Route path="/home" element={<HomePage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Application Routes */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <AppLayout />
                </PrivateRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="products" element={<Products />} />
              <Route path="products/:id" element={<ProductDetail />} />
              <Route path="batches" element={<Batches />} />
              <Route path="expiry" element={<ExpiryTracker />} />
              <Route path="movements" element={<Movements />} />
              <Route path="pos" element={<PosSale />} />
              <Route path="sales" element={<Sales />} />
              <Route path="purchases" element={<Purchases />} />
              <Route path="suppliers" element={<Suppliers />} />
              <Route path="forecasting" element={<Forecasting />} />
              <Route path="recommendations" element={<ReorderRecommendations />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="analytics" element={<AnalyticsReports />} />
              <Route path="users" element={<UsersManagement />} />
              <Route path="settings" element={<SettingsPage />} />
            </Route>

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </WebSocketProvider>
    </AuthProvider>
  );
};

export default App;

import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { apiClient } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isOwner: boolean;
  isStaff: boolean;
  isAuthenticated: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('stocksense_token'));
  const [loading, setLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    try {
      const res = await apiClient.getMe();
      setUser(res.data);
      localStorage.setItem('stocksense_user', JSON.stringify(res.data));
    } catch {
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const savedToken = localStorage.getItem('stocksense_token');
    const savedUser = localStorage.getItem('stocksense_user');

    if (savedToken) {
      setToken(savedToken);
      if (savedUser) {
        try {
          setUser(JSON.parse(savedUser));
          setLoading(false);
        } catch {
          refreshUser();
        }
      } else {
        refreshUser();
      }
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const res = await apiClient.login({ email, password });
    const { access_token, user_id, role, full_name } = res.data;

    localStorage.setItem('stocksense_token', access_token);
    setToken(access_token);

    const currentUser: User = {
      id: user_id,
      email,
      full_name,
      role,
      is_active: true,
      created_at: new Date().toISOString(),
    };

    localStorage.setItem('stocksense_user', JSON.stringify(currentUser));
    setUser(currentUser);
  };

  const logout = () => {
    localStorage.removeItem('stocksense_token');
    localStorage.removeItem('stocksense_user');
    setToken(null);
    setUser(null);
  };

  const isOwner = user?.role === 'shop_owner';
  const isStaff = user?.role === 'staff' || isOwner;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isOwner,
        isStaff,
        isAuthenticated: !!user,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

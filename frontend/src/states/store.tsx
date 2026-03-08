/**
 * Global State Management using Context API
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from '../api/endpoint';
import { authEndpoints } from '../api/endpoint';
import { apiClient } from '../api/client';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  refreshToken: () => Promise<void>;
}

interface StockContextType {
  selectedStock: number | null;
  setSelectedStock: (id: number | null) => void;
  watchlist: number[];
  addToWatchlist: (stockId: number) => void;
  removeFromWatchlist: (stockId: number) => void;
  isInWatchlist: (stockId: number) => boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);
const StockContext = createContext<StockContextType | null>(null);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        apiClient.setToken(token);
        try {
          const { data } = await authEndpoints.getCurrentUser();
          if (data) {
            setUser(data);
          } else {
            apiClient.clearToken();
          }
        } catch (error) {
          apiClient.clearToken();
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = (userData: User, accessToken: string, refreshToken: string) => {
    console.log('👤 [AuthProvider] login() called with user:', userData.email);
    console.log('🔐 [AuthProvider] Token lengths:', {
      accessToken: accessToken.length,
      refreshToken: refreshToken.length,
    });
    
    setUser(userData);
    console.log('👤 [AuthProvider] User state set');
    
    apiClient.setToken(accessToken);
    console.log('🔑 [AuthProvider] apiClient token set, calling setToken()');
    
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    console.log('💾 [AuthProvider] Tokens stored in localStorage');
  };

  const logout = () => {
    setUser(null);
    apiClient.clearToken();
    localStorage.removeItem('refresh_token');
  };

  const refreshTokenFn = async () => {
    try {
      const refreshTokenValue = localStorage.getItem('refresh_token');
      if (!refreshTokenValue) {
        throw new Error('No refresh token');
      }
      const { data, error } = await authEndpoints.refresh(refreshTokenValue);
      if (error || !data) {
        throw new Error(error || 'Token refresh failed');
      }
      apiClient.setToken(data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
    } catch (error) {
      logout();
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshToken: refreshTokenFn,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const StockProvider: React.FC<{ children: ReactNode }> = ({ children }: { children: ReactNode }) => {
  const [selectedStock, setSelectedStock] = useState<number | null>(null);
  const [watchlist, setWatchlist] = useState<number[]>(() => {
    const saved = localStorage.getItem('watchlist');
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem('watchlist', JSON.stringify(watchlist));
  }, [watchlist]);

  const addToWatchlist = (stockId: number) => {
    setWatchlist((prev: number[]) => (prev.includes(stockId) ? prev : [...prev, stockId]));
  };

  const removeFromWatchlist = (stockId: number) => {
    setWatchlist((prev: number[]) => prev.filter((id: number) => id !== stockId));
  };

  const isInWatchlist = (stockId: number) => {
    return watchlist.includes(stockId);
  };

  const value: StockContextType = {
    selectedStock,
    setSelectedStock,
    watchlist,
    addToWatchlist,
    removeFromWatchlist,
    isInWatchlist,
  };

  return <StockContext.Provider value={value}>{children}</StockContext.Provider>;
};

// =====================
// Custom Hooks
// =====================

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const useStock = (): StockContextType => {
  const context = useContext(StockContext);
  if (!context) {
    throw new Error('useStock must be used within StockProvider');
  }
  return context;
};

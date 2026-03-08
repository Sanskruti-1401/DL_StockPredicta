/**
 * Protected Route Component
 * Wraps routes that require authentication
 */

import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../states/store';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }: ProtectedRouteProps) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const [isReady, setIsReady] = useState(false);
  
  useEffect(() => {
    // Wait for auth state to finish loading  
    if (!isLoading) {
      setIsReady(true);
    }
  }, [isLoading]);

  // Still loading, show loading screen
  if (!isReady) {
    return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#0f172a', color: '#fff', fontSize: '18px' }}>Initializing...</div>;
  }

  // Not authenticated, redirect to login
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />;
  }

  // Authenticated, allow access
  return <>{children}</>;
};

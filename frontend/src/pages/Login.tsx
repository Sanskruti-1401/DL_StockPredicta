/**
 * Login Page Component
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../states/store';
import { authEndpoints } from '../api/endpoint';
import '../styles/auth.css';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect to dashboard when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      console.log('✨ [Login] Authenticated, redirecting to dashboard');
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('=== FORM SUBMITTED ===');
    setError(null);

    if (!email || !password) {
      console.log('Missing fields:', { email, password });
      setError('Please fill in all fields');
      return;
    }

    try {
      setLoading(true);
      console.log('🔵 [Login] Starting login with:', { email });
      
      const { data, error: err } = await authEndpoints.login({
        email,
        password,
      });

      console.log('🟢 [Login] Response received:', { data, err });

      if (err) {
        console.error('❌ [Login] Error from API:', err);
        setError(err);
      } else if (data) {
        console.log('✅ [Login] Data received:', {
          user: data.user?.email,
          access_token: data.access_token ? 'present' : 'missing',
          refresh_token: data.refresh_token ? 'present' : 'missing',
        });
        
        console.log('🔄 [Login] Calling login() function...');
        login(data.user, data.access_token, data.refresh_token);
        // Navigation will be handled by useEffect watching isAuthenticated
      }
    } catch (err) {
      console.error('💥 [Login] Caught exception:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Stock Predictor</h1>
          <p>Sign In to Your Account</p>
        </div>

        {error && <div className="auth-error">{error}</div>}

        <form onSubmit={handleLogin} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e: any) => setEmail(e.target.value)}
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e: any) => setPassword(e.target.value)}
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        <div className="auth-divider">or</div>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <button
              type="button"
              className="auth-link"
              onClick={() => navigate('/register')}
              disabled={loading}
            >
              Sign Up
            </button>
          </p>

          <p className="demo-hint">
            Demo credentials: demo@example.com / password
          </p>
        </div>
      </div>

      <div className="auth-background">
        <div className="bg-gradient"></div>
        <div className="bg-pattern"></div>
      </div>
    </div>
  );
};

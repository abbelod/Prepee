import { useState } from 'react';
import { useNavigate } from 'react-router';
import './Auth.css';
import api from '../services/api'
import { useAuth } from './AuthProvider';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState<{ email?: string; password?: string; general?: string }>({});
  const [isLoading, setIsLoading] = useState(false);
  const { setUser } = useAuth();

  const validateForm = () => {
    const newErrors: { email?: string; password?: string } = {};

    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Login function using the configured axios instance (api)
  async function loginUser(email: string, password: string) {
    try {
      const response = await api.post('/auth/login/', { email, password });
      const { access, refresh, user } = response.data;
      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);

      setUser(user);

      if (user) {
        localStorage.setItem('user', JSON.stringify(user));
      }
      // Set the default Authorization header for future requests
      api.defaults.headers.common['Authorization'] = 'Bearer ' + access;
      return { success: true };
    } catch (error: any) {
      console.error("Login failed", error);
      // Return the error response data for further handling
      return { success: false, error: error.response?.data };
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({}); // Clear any previous errors

    try {
      const result = await loginUser(email, password);

      if (result.success) {
        navigate('/');
      } else {
        // Handle error response from the API
        const errorData = result.error;
        if (errorData?.email) {
          setErrors({ email: errorData.email[0] });
        } else if (errorData?.password) {
          setErrors({ password: errorData.password[0] });
        } else if (errorData?.detail) {
          setErrors({ general: errorData.detail });
        } else if (errorData?.non_field_errors) {
          setErrors({ general: errorData.non_field_errors[0] });
        } else {
          setErrors({ general: 'Login failed. Please check your credentials.' });
        }
      }
    } catch (error) {
      // This catch should rarely happen because loginUser catches errors,
      // but kept for safety
      console.error('Login error:', error);
      setErrors({
        general: 'Unable to connect to the server. Please try again later.'
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1 className="auth-title">Welcome Back!</h1>
          <p className="auth-subtitle">Sign in to start challenging opponents</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {errors.general && (
            <div className="error-message general-error" style={{ marginBottom: '1rem' }}>
              {errors.general}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="login-email" className="form-label">
              Email Address
            </label>
            <input
              id="login-email"
              type="email"
              className={`form-input ${errors.email ? 'form-input-error' : ''}`}
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
            />
            {errors.email && <span className="error-message">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="login-password" className="form-label">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              className={`form-input ${errors.password ? 'form-input-error' : ''}`}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
            {errors.password && <span className="error-message">{errors.password}</span>}
          </div>

          <div className="form-options">
            <label className="checkbox-label">
              <input type="checkbox" />
              <span>Remember me</span>
            </label>
            <a href="#" className="forgot-password-link">Forgot password?</a>
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Don't have an account?{' '}
            <button
              type="button"
              onClick={() => navigate('/signup')}
              className="auth-link-button"
            >
              Sign Up
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
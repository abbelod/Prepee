import { useState } from 'react';
import { useNavigate } from 'react-router';
import './Auth.css';

export default function Signup() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [city, setCity] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<{
    name?: string;
    username?: string;
    city?: string;
    email?: string;
    password?: string;
    confirmPassword?: string;
    general?: string;
  }>({});
  const [isLoading, setIsLoading] = useState(false);

  const validateForm = () => {
    const newErrors: {
      name?: string;
      username?: string;
      city?: string;
      email?: string;
      password?: string;
      confirmPassword?: string;
    } = {};

    if (!name.trim()) {
      newErrors.name = 'Name is required';
    } else if (name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    }

    if (!username.trim()) {
      newErrors.username = 'Username is required';
    } else if (username.trim().length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
    }

    if (!city.trim()) {
      newErrors.city = 'City is required';
    } else if (city.trim().length < 2) {
      newErrors.city = 'City must be at least 2 characters';
    }

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

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({}); // Clear any previous errors

    try {
      const response = await fetch('http://prepee.onrender.com/api/auth/signup/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
          email: email,
          city,
          password: password,
          password2: confirmPassword,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        // if(data.access) {
        //   localStorage.setItem('accessToken', data.access)
        // }
        // if(data.refresh) {
        //   localStorage.setItem('refreshToken', data.refresh)
        // }

        // // Store user data if needed
        // if (data.user) {
        //   localStorage.setItem('user', JSON.stringify(data.user));
        // }

        // Navigate to login page or home page based on your flow
        // If API returns token, go to home:
        if (data.token) {
          navigate('/');
        } else {
          // Otherwise, go to login:
          navigate('/login');
        }
      } else {
        // Handle error responses from Django REST Framework
        const newErrors: {
          name?: string;
          username?: string;
          email?: string;
          city?: string;
          password?: string;
          confirmPassword?: string;
          general?: string;
        } = {};

        if (data.username) {
          newErrors.username = Array.isArray(data.username) ? data.username[0] : data.username;
        }
        if (data.email) {
          newErrors.email = Array.isArray(data.email) ? data.email[0] : data.email;
        }
        if (data.city) {
          newErrors.city = Array.isArray(data.city) ? data.city[0] : data.city;
        }
        if (data.password) {
          newErrors.password = Array.isArray(data.password) ? data.password[0] : data.password;
        }
        if (data.password2) {
          newErrors.confirmPassword = Array.isArray(data.password2) ? data.password2[0] : data.password2;
        }
        if (data.detail) {
          newErrors.general = data.detail;
        }
        if (data.non_field_errors) {
          newErrors.general = Array.isArray(data.non_field_errors) 
            ? data.non_field_errors[0] 
            : data.non_field_errors;
        }

        // If no specific errors, show generic message
        if (Object.keys(newErrors).length === 0) {
          newErrors.general = 'Signup failed. Please try again.';
        }

        setErrors(newErrors);
      }
    } catch (error) {
      console.error('Signup error:', error);
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
          <h1 className="auth-title">Join Prepee!</h1>
          <p className="auth-subtitle">Create your account and start competing</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          {errors.general && (
            <div className="error-message general-error" style={{ marginBottom: '1rem' }}>
              {errors.general}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="signup-name" className="form-label">
              Full Name
            </label>
            <input
              id="signup-name"
              type="text"
              className={`form-input ${errors.name ? 'form-input-error' : ''}`}
              placeholder="Enter your full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={isLoading}
            />
            {errors.name && <span className="error-message">{errors.name}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="signup-username" className="form-label">
              Username
            </label>
            <input
              id="signup-username"
              type="text"
              className={`form-input ${errors.username ? 'form-input-error' : ''}`}
              placeholder="Choose a username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
            />
            {errors.username && <span className="error-message">{errors.username}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="signup-email" className="form-label">
              Email Address
            </label>
            <input
              id="signup-email"
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
            <label htmlFor="signup-city" className="form-label">
              City
            </label>
            <input
              id="signup-city"
              type="text"
              className={`form-input ${errors.city ? 'form-input-error' : ''}`}
              placeholder="Enter your city"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              disabled={isLoading}
            />
            {errors.city && <span className="error-message">{errors.city}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="signup-password" className="form-label">
              Password
            </label>
            <input
              id="signup-password"
              type="password"
              className={`form-input ${errors.password ? 'form-input-error' : ''}`}
              placeholder="Create a password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
            />
            {errors.password && <span className="error-message">{errors.password}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="signup-confirm-password" className="form-label">
              Confirm Password
            </label>
            <input
              id="signup-confirm-password"
              type="password"
              className={`form-input ${errors.confirmPassword ? 'form-input-error' : ''}`}
              placeholder="Confirm your password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
            />
            {errors.confirmPassword && (
              <span className="error-message">{errors.confirmPassword}</span>
            )}
          </div>

          <div className="form-options">
            <label className="checkbox-label">
              <input type="checkbox" required />
              <span>I agree to the Terms and Conditions</span>
            </label>
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={isLoading}
          >
            {isLoading ? 'Creating Account...' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Already have an account?{' '}
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="auth-link-button"
            >
              Sign In
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
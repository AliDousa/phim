import React, { createContext, useContext, useState, useEffect } from 'react';
import ApiService from '@/lib/api';
import { toast } from 'sonner';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Check if user is authenticated on app load
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token && token !== 'dummy-dev-token' && token.trim() !== '') {
      // Verify token by getting user profile
      ApiService.getProfile()
        .then((response) => {
          if (response && response.user) {
            setUser(response.user);
            setIsAuthenticated(true);
          } else {
            // Invalid response, clear auth
            localStorage.removeItem('authToken');
            setUser(null);
            setIsAuthenticated(false);
          }
        })
        .catch((error) => {
          console.error('Token verification failed:', error);
          // Token is invalid, remove it
          localStorage.removeItem('authToken');
          setUser(null);
          setIsAuthenticated(false);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (credentials) => {
    try {
      setLoading(true);
      const response = await ApiService.login(credentials);
      
      if (response && response.token && response.user) {
        localStorage.setItem('authToken', response.token);
        setUser(response.user);
        setIsAuthenticated(true);
        toast.success('Login successful!');
        return response;
      } else {
        throw new Error('Invalid login response from server');
      }
    } catch (error) {
      console.error('Login error:', error);
      // Clear any invalid tokens
      localStorage.removeItem('authToken');
      setUser(null);
      setIsAuthenticated(false);
      toast.error(error.message || 'Login failed');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const register = async (userData) => {
    try {
      setLoading(true);
      const response = await ApiService.register(userData);
      
      localStorage.setItem('authToken', response.token);
      setUser(response.user);
      setIsAuthenticated(true);
      
      toast.success('Registration successful!');
      return response;
    } catch (error) {
      toast.error(error.message || 'Registration failed');
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await ApiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('authToken');
      setUser(null);
      setIsAuthenticated(false);
      toast.success('Logged out successfully');
    }
  };

  const updateProfile = async (data) => {
    try {
      const response = await ApiService.updateProfile(data);
      setUser(response.user);
      toast.success('Profile updated successfully');
      return response;
    } catch (error) {
      toast.error(error.message || 'Profile update failed');
      throw error;
    }
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
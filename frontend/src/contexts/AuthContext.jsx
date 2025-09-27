import React, { createContext, useContext, useState, useEffect } from 'react';
import { vendorEcosystemAPI } from '../services/ecosystemAPI';

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
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const savedToken = localStorage.getItem('vendor_ecosystem_token');
    const savedUser = localStorage.getItem('vendor_ecosystem_user');
    
    if (savedToken && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(userData);
        setIsAuthenticated(true);
        vendorEcosystemAPI.setAuthToken(savedToken);
      } catch (error) {
        console.error('Error parsing saved user data:', error);
        logout();
      }
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      const response = await vendorEcosystemAPI.login(email, password);
      const { user: userData, token: userToken } = response;
      
      if (!userData || !userToken) {
        return { 
          success: false, 
          error: 'Invalid response from server' 
        };
      }
      
      setUser(userData);
      setToken(userToken);
      setIsAuthenticated(true);
      
      localStorage.setItem('vendor_ecosystem_token', userToken);
      localStorage.setItem('vendor_ecosystem_user', JSON.stringify(userData));
      
      vendorEcosystemAPI.setAuthToken(userToken);
      
      return { success: true, user: userData };
    } catch (error) {
      console.error('Login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.message || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await vendorEcosystemAPI.register(userData);
      const { user: newUser, token: userToken } = response;
      
      setUser(newUser);
      setToken(userToken);
      setIsAuthenticated(true);
      
      localStorage.setItem('vendor_ecosystem_token', userToken);
      localStorage.setItem('vendor_ecosystem_user', JSON.stringify(newUser));
      
      vendorEcosystemAPI.setAuthToken(userToken);
      
      return { success: true, user: newUser };
    } catch (error) {
      console.error('Registration error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);
    
    localStorage.removeItem('vendor_ecosystem_token');
    localStorage.removeItem('vendor_ecosystem_user');
    
    vendorEcosystemAPI.setAuthToken(null);
  };

  const updateUser = (userData) => {
    setUser(userData);
    localStorage.setItem('vendor_ecosystem_user', JSON.stringify(userData));
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    updateUser,
    hasRole: (role) => user?.role === role || user?.role === 'system_admin',
    isVendor: () => user?.role === 'vendor',
    isAdmin: () => ['verification_officer', 'regional_admin', 'system_admin'].includes(user?.role),
    isSystemAdmin: () => user?.role === 'system_admin'
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
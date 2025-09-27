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
    console.log('AuthContext: useEffect running, checking localStorage...');
    const savedToken = localStorage.getItem('vendor_ecosystem_token');
    const savedUser = localStorage.getItem('vendor_ecosystem_user');
    
    console.log('AuthContext: savedToken:', savedToken ? savedToken.substring(0, 20) + '...' : 'null');
    console.log('AuthContext: savedUser:', savedUser ? 'found' : 'null');
    
    if (savedToken && savedUser) {
      try {
        const userData = JSON.parse(savedUser);
        console.log('AuthContext: Parsed user data:', userData);
        setToken(savedToken);
        setUser(userData);
        setIsAuthenticated(true);
        vendorEcosystemAPI.setAuthToken(savedToken);
        console.log('AuthContext: Authentication state set to true');
      } catch (error) {
        console.error('AuthContext: Error parsing saved user data:', error);
        logout();
      }
    } else {
      console.log('AuthContext: No saved credentials found');
    }
    setLoading(false);
    console.log('AuthContext: Loading set to false');
  }, []);

  const login = async (email, password) => {
    try {
      console.log('AuthContext: Starting login for:', email);
      const response = await vendorEcosystemAPI.login(email, password);
      console.log('AuthContext: API response:', response);
      
      const { user: userData, token: userToken } = response;
      console.log('AuthContext: Extracted user:', userData);
      console.log('AuthContext: Extracted token:', userToken ? userToken.substring(0, 20) + '...' : 'null');
      
      if (!userData || !userToken) {
        console.error('AuthContext: Missing user or token in response');
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
      
      console.log('AuthContext: Login successful, state updated');
      return { success: true, user: userData };
    } catch (error) {
      console.error('AuthContext: Login error:', error);
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
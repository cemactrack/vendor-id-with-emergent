import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { Toaster } from "./components/ui/toaster";

// Import components
import LoginForm from "./components/auth/LoginForm";
import RegisterForm from "./components/auth/RegisterForm";
import EmailVerification from "./components/auth/EmailVerification";
import ForgotPassword from "./components/auth/ForgotPassword";
import ResetPassword from "./components/auth/ResetPassword";
import TwoFactorSetup from "./components/auth/TwoFactorSetup";
import ResponsiveVendorDashboard from "./components/ResponsiveVendorDashboard";
import VendorEcosystemDashboard from "./components/ecosystem/VendorEcosystemDashboard";
import PublicVendorSearch from "./components/public/PublicVendorSearch";
import PublicVendorVerification from "./components/public/PublicVendorVerification";
import AdminDashboard from "./components/admin/AdminDashboard";
import VendorOnboarding from "./components/vendor/VendorOnboarding";

// Protected Route Component
const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole && user?.role !== 'system_admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Public Route Component (redirect if authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Main App Component
const AppContent = () => {
  const { user } = useAuth();

  const getDashboardComponent = () => {
    if (!user) return <Navigate to="/login" replace />;

    switch (user.role) {
      case 'vendor':
        return <VendorEcosystemDashboard />;
      case 'verification_officer':
      case 'regional_admin':
      case 'system_admin':
        return <AdminDashboard />;
      case 'customer':
      default:
        return <PublicVendorSearch />;
    }
  };

  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<PublicVendorSearch />} />
        <Route path="/search" element={<PublicVendorSearch />} />
        <Route path="/verify/:vendorId" element={<PublicVendorVerification />} />
        
        {/* Authentication Routes */}
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <LoginForm onSuccess={() => window.location.href = '/dashboard'} />
            </PublicRoute>
          } 
        />
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <RegisterForm onSuccess={() => window.location.href = '/onboarding'} />
            </PublicRoute>
          } 
        />
        
        {/* Protected Routes */}
        <Route 
          path="/dashboard" 
          element={
            <ProtectedRoute>
              {getDashboardComponent()}
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/onboarding" 
          element={
            <ProtectedRoute requiredRole="vendor">
              <VendorOnboarding />
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin" 
          element={
            <ProtectedRoute requiredRole="verification_officer">
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* Legacy Routes for Backward Compatibility */}
        <Route 
          path="/legacy" 
          element={
            <ProtectedRoute>
              <ResponsiveVendorDashboard />
            </ProtectedRoute>
          } 
        />
        
        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  );
};

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </div>
  );
}

export default App;
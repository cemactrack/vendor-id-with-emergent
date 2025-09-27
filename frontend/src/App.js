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
import SecuritySettings from "./components/auth/SecuritySettings";
import LandingPage from "./components/LandingPage";
import Layout from "./components/layout/Layout";
import ResponsiveVendorDashboard from "./components/ResponsiveVendorDashboard";
import VendorEcosystemDashboard from "./components/ecosystem/VendorEcosystemDashboard";
import PublicVendorSearch from "./components/public/PublicVendorSearch";
import PublicVendorVerification from "./components/public/PublicVendorVerification";
import AdminDashboard from "./components/admin/AdminDashboard";
import VendorOnboarding from "./components/vendor/VendorOnboarding";
import DocumentUpload from "./components/vendor/DocumentUpload";
import VendorIDCard from "./components/vendor/VendorIDCard";
import OCRProcessing from "./components/vendor/OCRProcessing";
import DocumentReview from "./components/admin/DocumentReview";
import VerificationQueue from "./components/admin/VerificationQueue";
import EscrowDashboard from "./components/escrow/EscrowDashboard";
import OrderCreation from "./components/escrow/OrderCreation";
import ProfileValidation from "./components/trust/ProfileValidation";
import ProfileEditor from "./components/profile/ProfileEditor";

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
        <Route path="/" element={<LandingPage />} />
        <Route path="/search" element={<Layout><PublicVendorSearch /></Layout>} />
        <Route path="/verify/:vendorId" element={<Layout><PublicVendorVerification /></Layout>} />
        
        {/* Authentication Routes */}
        <Route 
          path="/login" 
          element={
            <PublicRoute>
              <div className="min-h-screen">
                <LoginForm />
              </div>
            </PublicRoute>
          } 
        />
        <Route 
          path="/register" 
          element={
            <PublicRoute>
              <div className="min-h-screen">
                <RegisterForm onSuccess={() => window.location.href = '/onboarding'} />
              </div>
            </PublicRoute>
          } 
        />
        <Route 
          path="/verify-email" 
          element={
            <div className="min-h-screen">
              <EmailVerification />
            </div>
          } 
        />
        <Route 
          path="/forgot-password" 
          element={
            <PublicRoute>
              <div className="min-h-screen">
                <ForgotPassword />
              </div>
            </PublicRoute>
          } 
        />
        <Route 
          path="/reset-password" 
          element={
            <PublicRoute>
              <div className="min-h-screen">
                <ResetPassword />
              </div>
            </PublicRoute>
          } 
        />
        <Route 
          path="/2fa-setup" 
          element={
            <ProtectedRoute>
              <div className="min-h-screen">
                <TwoFactorSetup />
              </div>
            </ProtectedRoute>
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
              <div className="min-h-screen">
                <VendorOnboarding />
              </div>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/security-settings" 
          element={
            <ProtectedRoute>
              <Layout>
                <SecuritySettings />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/documents" 
          element={
            <ProtectedRoute requiredRole="vendor">
              <Layout>
                <DocumentUpload />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/vendor-id" 
          element={
            <ProtectedRoute requiredRole="vendor">
              <Layout>
                <VendorIDCard />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/ocr-processing" 
          element={
            <ProtectedRoute requiredRole="vendor">
              <Layout>
                <OCRProcessing />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/escrow" 
          element={
            <ProtectedRoute>
              <Layout>
                <EscrowDashboard />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/escrow/create-order/:vendorId" 
          element={
            <ProtectedRoute>
              <Layout>
                <OrderCreation />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/profile/validation" 
          element={
            <ProtectedRoute>
              <Layout>
                <ProfileValidation />
              </Layout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile/edit" 
          element={
            <ProtectedRoute>
              <Layout>
                <ProfileEditor />
              </Layout>
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
        
        <Route 
          path="/admin/verification-queue" 
          element={
            <ProtectedRoute requiredRole="verification_officer">
              <Layout>
                <VerificationQueue />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/document-review/:documentId" 
          element={
            <ProtectedRoute requiredRole="verification_officer">
              <Layout>
                <DocumentReview />
              </Layout>
            </ProtectedRoute>
          } 
        />
        
        <Route 
          path="/admin/document-review" 
          element={
            <ProtectedRoute requiredRole="verification_officer">
              <Layout>
                <DocumentReview />
              </Layout>
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
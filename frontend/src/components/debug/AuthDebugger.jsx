import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';

const AuthDebugger = () => {
  const { user, token, isAuthenticated, loading, login } = useAuth();
  const [debugInfo, setDebugInfo] = useState({});
  const [testLoginStatus, setTestLoginStatus] = useState('');

  useEffect(() => {
    const savedToken = localStorage.getItem('vendor_ecosystem_token');
    const savedUser = localStorage.getItem('vendor_ecosystem_user');
    const regularToken = localStorage.getItem('token');
    
    setDebugInfo({
      savedToken: savedToken ? savedToken.substring(0, 20) + '...' : 'null',
      savedUser: savedUser ? JSON.parse(savedUser) : null,
      regularToken: regularToken ? regularToken.substring(0, 20) + '...' : 'null',
      contextUser: user,
      contextToken: token ? token.substring(0, 20) + '...' : 'null',
      isAuthenticated,
      loading
    });
  }, [user, token, isAuthenticated, loading]);

  const testLogin = async () => {
    setTestLoginStatus('Testing...');
    try {
      const result = await login('testvendor@example.com', 'testpassword123');
      setTestLoginStatus(`Login result: ${JSON.stringify(result)}`);
    } catch (error) {
      setTestLoginStatus(`Login error: ${error.message}`);
    }
  };

  const testDirectAPI = async () => {
    try {
      const response = await vendorEcosystemAPI.login('testvendor@example.com', 'testpassword123');
      setTestLoginStatus(`Direct API result: ${JSON.stringify(response)}`);
    } catch (error) {
      setTestLoginStatus(`Direct API error: ${error.message}`);
    }
  };

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Authentication Debugger</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Auth Context State</h2>
            <pre className="text-sm bg-gray-50 p-3 rounded">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
          
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-lg font-semibold mb-4">Test Login</h2>
            <div className="space-y-3">
              <button 
                onClick={testLogin}
                className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
              >
                Test Auth Context Login
              </button>
              <button 
                onClick={testDirectAPI}
                className="w-full bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
              >
                Test Direct API Login
              </button>
              {testLoginStatus && (
                <div className="bg-gray-50 p-3 rounded text-sm">
                  {testLoginStatus}
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="mt-6 bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-4">Current localStorage Content</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <strong>vendor_ecosystem_token:</strong>
              <div className="bg-gray-50 p-2 rounded mt-1 break-all">
                {localStorage.getItem('vendor_ecosystem_token') || 'null'}
              </div>
            </div>
            <div>
              <strong>vendor_ecosystem_user:</strong>
              <div className="bg-gray-50 p-2 rounded mt-1">
                {localStorage.getItem('vendor_ecosystem_user') || 'null'}
              </div>
            </div>
            <div>
              <strong>token:</strong>
              <div className="bg-gray-50 p-2 rounded mt-1 break-all">
                {localStorage.getItem('token') || 'null'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthDebugger;
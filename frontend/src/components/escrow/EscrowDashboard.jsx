import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  ShoppingCart,
  Clock,
  CheckCircle,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Package,
  MessageSquare,
  Eye,
  Download
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useAuth } from '../../contexts/AuthContext';
import OrderCreation from './OrderCreation';

const EscrowDashboard = () => {
  const [orders, setOrders] = useState([]);
  const [stats, setStats] = useState({
    totalOrders: 0,
    pendingPayment: 0,
    inProgress: 0,
    completed: 0,
    disputed: 0,
    totalValue: 0
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [showOrderCreation, setShowOrderCreation] = useState(false);
  
  const { user } = useAuth();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load user orders (as customer)
      const customerOrders = await vendorEcosystemAPI.getUserOrders('customer');
      
      // Load vendor orders if user is also a vendor
      let vendorOrders = [];
      if (user.vendor_id) {
        vendorOrders = await vendorEcosystemAPI.getUserOrders('vendor');
      }
      
      const allOrders = [...customerOrders.orders, ...vendorOrders.orders];
      setOrders(allOrders);
      
      // Calculate statistics
      const statistics = calculateStats(allOrders);
      setStats(statistics);
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (ordersData) => {
    return {
      totalOrders: ordersData.length,
      pendingPayment: ordersData.filter(o => o.status === 'pending_payment').length,
      inProgress: ordersData.filter(o => ['payment_confirmed', 'in_progress', 'delivered'].includes(o.status)).length,
      completed: ordersData.filter(o => o.status === 'completed').length,
      disputed: ordersData.filter(o => o.status === 'disputed').length,
      totalValue: ordersData.reduce((sum, o) => sum + (o.total_amount || 0), 0)
    };
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending_payment: { label: 'Pending Payment', variant: 'default', color: 'bg-yellow-100 text-yellow-800' },
      payment_submitted: { label: 'Payment Submitted', variant: 'secondary', color: 'bg-blue-100 text-blue-800' },
      payment_confirmed: { label: 'Payment Confirmed', variant: 'secondary', color: 'bg-green-100 text-green-800' },
      in_progress: { label: 'In Progress', variant: 'default', color: 'bg-blue-100 text-blue-800' },
      delivered: { label: 'Delivered', variant: 'secondary', color: 'bg-purple-100 text-purple-800' },
      completed: { label: 'Completed', variant: 'default', color: 'bg-green-100 text-green-800' },
      disputed: { label: 'Disputed', variant: 'destructive', color: 'bg-red-100 text-red-800' },
      cancelled: { label: 'Cancelled', variant: 'secondary', color: 'bg-gray-100 text-gray-800' }
    };

    const config = statusConfig[status] || statusConfig.pending_payment;
    return (
      <Badge className={config.color}>
        {config.label}
      </Badge>
    );
  };

  const formatCurrency = (amount, currency) => {
    const symbols = {
      USD: '$', NGN: '₦', GHS: '₵', KES: 'KSh', 
      ZAR: 'R', GBP: '£', EUR: '€', CAD: 'C$'
    };
    return `${symbols[currency] || currency} ${amount?.toFixed(2) || '0.00'}`;
  };

  const handleOrderCreated = (orderData) => {
    setShowOrderCreation(false);
    setSelectedVendor(null);
    loadDashboardData(); // Refresh data
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading escrow dashboard...</p>
        </div>
      </div>
    );
  }

  if (showOrderCreation && selectedVendor) {
    return (
      <OrderCreation
        vendorId={selectedVendor}
        onOrderCreated={handleOrderCreated}
        onCancel={() => {
          setShowOrderCreation(false);
          setSelectedVendor(null);
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Escrow Dashboard</h1>
              <p className="text-gray-600">Manage your orders and payments securely</p>
            </div>
            <Button 
              onClick={() => setActiveTab('create')}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <ShoppingCart className="w-4 h-4 mr-2" />
              Create Order
            </Button>
          </div>
        </div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Orders</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalOrders}</p>
                </div>
                <ShoppingCart className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">In Progress</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.inProgress}</p>
                </div>
                <Clock className="w-8 h-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.completed}</p>
                </div>
                <CheckCircle className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Value</p>
                  <p className="text-2xl font-bold text-gray-900">${stats.totalValue.toFixed(0)}</p>
                </div>
                <DollarSign className="w-8 h-8 text-emerald-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="orders">My Orders</TabsTrigger>
            <TabsTrigger value="payments">Payments</TabsTrigger>
            <TabsTrigger value="disputes">Disputes</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Recent Orders */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Orders</CardTitle>
                </CardHeader>
                <CardContent>
                  {orders.slice(0, 5).length > 0 ? (
                    <div className="space-y-4">
                      {orders.slice(0, 5).map((order) => (
                        <div key={order.order_id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div>
                            <p className="font-medium text-sm">{order.order_id}</p>
                            <p className="text-xs text-gray-600">
                              {formatCurrency(order.total_amount, order.currency)}
                            </p>
                          </div>
                          {getStatusBadge(order.status)}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <ShoppingCart className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No orders yet</h3>
                      <p className="text-gray-600 mb-4">Start by creating your first order</p>
                      <Button 
                        onClick={() => setActiveTab('create')}
                        size="sm"
                        className="bg-emerald-600 hover:bg-emerald-700"
                      >
                        Create Order
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('create')}
                    >
                      <ShoppingCart className="w-4 h-4 mr-2" />
                      Create New Order
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('payments')}
                    >
                      <DollarSign className="w-4 h-4 mr-2" />
                      View Payments
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => setActiveTab('disputes')}
                    >
                      <MessageSquare className="w-4 h-4 mr-2" />
                      Manage Disputes
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Orders Tab */}
          <TabsContent value="orders" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>All Orders</CardTitle>
              </CardHeader>
              <CardContent>
                {orders.length > 0 ? (
                  <div className="space-y-4">
                    {orders.map((order) => (
                      <div key={order.order_id} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <h3 className="font-medium">{order.order_id}</h3>
                            <p className="text-sm text-gray-600">
                              {new Date(order.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <div className="text-right">
                            {getStatusBadge(order.status)}
                            <p className="text-sm font-medium mt-1">
                              {formatCurrency(order.total_amount, order.currency)}
                            </p>
                          </div>
                        </div>
                        
                        <div className="text-sm text-gray-600 mb-3">
                          <p><strong>Items:</strong> {order.items?.length || 0} item(s)</p>
                          <p><strong>Delivery:</strong> {order.delivery_address}</p>
                        </div>
                        
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="w-4 h-4 mr-1" />
                            View Details
                          </Button>
                          {order.status === 'delivered' && (
                            <Button variant="outline" size="sm" className="text-emerald-600">
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Confirm Receipt
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Package className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No orders found</h3>
                    <p className="text-gray-600">Your orders will appear here</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Payments Tab */}
          <TabsContent value="payments" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Payment History</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <DollarSign className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Payment Management</h3>
                  <p className="text-gray-600">View and manage your payment history</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Disputes Tab */}
          <TabsContent value="disputes" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Disputes</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Disputes</h3>
                  <p className="text-gray-600">Dispute resolution will appear here when needed</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default EscrowDashboard;
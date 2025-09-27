import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { Badge } from '../ui/badge';
import { 
  ShoppingCart,
  Plus,
  Trash2,
  MapPin,
  CreditCard,
  Shield,
  Calculator,
  AlertTriangle
} from 'lucide-react';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useAuth } from '../../contexts/AuthContext';

const SUPPORTED_CURRENCIES = [
  { code: 'USD', name: 'US Dollar', symbol: '$' },
  { code: 'NGN', name: 'Nigerian Naira', symbol: '₦' },
  { code: 'GHS', name: 'Ghanaian Cedi', symbol: '₵' },
  { code: 'KES', name: 'Kenyan Shilling', symbol: 'KSh' },
  { code: 'ZAR', name: 'South African Rand', symbol: 'R' },
  { code: 'GBP', name: 'British Pound', symbol: '£' },
  { code: 'EUR', name: 'Euro', symbol: '€' },
  { code: 'CAD', name: 'Canadian Dollar', symbol: 'C$' }
];

const OrderCreation = ({ vendorId, onOrderCreated, onCancel }) => {
  const [orderData, setOrderData] = useState({
    vendor_id: vendorId,
    items: [{ 
      product_name: '', 
      description: '', 
      quantity: 1, 
      unit_price: 0, 
      currency: 'USD' 
    }],
    delivery_address: '',
    special_instructions: '',
    expected_delivery_date: ''
  });
  
  const [vendor, setVendor] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [calculations, setCalculations] = useState({
    subtotal: 0,
    platformFee: 0,
    total: 0,
    currency: 'USD'
  });
  
  const { user } = useAuth();

  useEffect(() => {
    loadVendorInfo();
  }, [vendorId]);

  useEffect(() => {
    calculateTotals();
  }, [orderData.items]);

  const loadVendorInfo = async () => {
    try {
      const vendorData = await vendorEcosystemAPI.getVendorProfile(vendorId);
      setVendor(vendorData);
    } catch (error) {
      console.error('Failed to load vendor info:', error);
    }
  };

  const calculateTotals = () => {
    let subtotal = 0;
    let currency = 'USD';
    
    orderData.items.forEach(item => {
      if (item.unit_price && item.quantity) {
        subtotal += parseFloat(item.unit_price) * parseInt(item.quantity);
        currency = item.currency;
      }
    });
    
    const platformFee = subtotal * 0.025; // 2.5%
    const total = subtotal + platformFee;
    
    setCalculations({
      subtotal: subtotal.toFixed(2),
      platformFee: platformFee.toFixed(2),
      total: total.toFixed(2),
      currency
    });
  };

  const addItem = () => {
    setOrderData(prev => ({
      ...prev,
      items: [...prev.items, { 
        product_name: '', 
        description: '', 
        quantity: 1, 
        unit_price: 0, 
        currency: prev.items[0]?.currency || 'USD' 
      }]
    }));
  };

  const removeItem = (index) => {
    if (orderData.items.length > 1) {
      setOrderData(prev => ({
        ...prev,
        items: prev.items.filter((_, i) => i !== index)
      }));
    }
  };

  const updateItem = (index, field, value) => {
    setOrderData(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Validate order data
      if (!orderData.delivery_address.trim()) {
        throw new Error('Delivery address is required');
      }

      if (orderData.items.some(item => !item.product_name.trim() || !item.unit_price || !item.quantity)) {
        throw new Error('All items must have name, price, and quantity');
      }

      // Create order
      const result = await vendorEcosystemAPI.createEscrowOrder(orderData);
      
      if (onOrderCreated) {
        onOrderCreated(result);
      }
      
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create order';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getCurrencySymbol = (code) => {
    return SUPPORTED_CURRENCIES.find(c => c.code === code)?.symbol || code;
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <ShoppingCart className="w-5 h-5 mr-2" />
            Create New Order
            {vendor && (
              <Badge variant="outline" className="ml-auto">
                {vendor.business_name}
              </Badge>
            )}
          </CardTitle>
        </CardHeader>
      </Card>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {/* Order Items */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Order Items
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addItem}
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Item
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {orderData.items.map((item, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Item {index + 1}</h4>
                  {orderData.items.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeItem(index)}
                      className="text-red-600 hover:text-red-800"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor={`product_name_${index}`}>Product Name *</Label>
                    <Input
                      id={`product_name_${index}`}
                      value={item.product_name}
                      onChange={(e) => updateItem(index, 'product_name', e.target.value)}
                      placeholder="Enter product name"
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor={`currency_${index}`}>Currency</Label>
                    <Select
                      value={item.currency}
                      onValueChange={(value) => updateItem(index, 'currency', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SUPPORTED_CURRENCIES.map(currency => (
                          <SelectItem key={currency.code} value={currency.code}>
                            {currency.symbol} {currency.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor={`quantity_${index}`}>Quantity *</Label>
                    <Input
                      id={`quantity_${index}`}
                      type="number"
                      min="1"
                      value={item.quantity}
                      onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 0)}
                      required
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor={`unit_price_${index}`}>Unit Price *</Label>
                    <div className="relative">
                      <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">
                        {getCurrencySymbol(item.currency)}
                      </span>
                      <Input
                        id={`unit_price_${index}`}
                        type="number"
                        step="0.01"
                        min="0"
                        value={item.unit_price}
                        onChange={(e) => updateItem(index, 'unit_price', parseFloat(e.target.value) || 0)}
                        className="pl-8"
                        placeholder="0.00"
                        required
                      />
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor={`description_${index}`}>Description</Label>
                  <Textarea
                    id={`description_${index}`}
                    value={item.description}
                    onChange={(e) => updateItem(index, 'description', e.target.value)}
                    placeholder="Optional item description"
                    rows={2}
                  />
                </div>
                
                <div className="flex justify-end">
                  <Badge variant="secondary">
                    Total: {getCurrencySymbol(item.currency)} {(item.unit_price * item.quantity || 0).toFixed(2)}
                  </Badge>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Delivery Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <MapPin className="w-5 h-5 mr-2" />
              Delivery Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="delivery_address">Delivery Address *</Label>
              <Textarea
                id="delivery_address"
                value={orderData.delivery_address}
                onChange={(e) => setOrderData(prev => ({...prev, delivery_address: e.target.value}))}
                placeholder="Enter complete delivery address"
                rows={3}
                required
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="expected_delivery_date">Expected Delivery Date</Label>
              <Input
                id="expected_delivery_date"
                type="date"
                value={orderData.expected_delivery_date}
                onChange={(e) => setOrderData(prev => ({...prev, expected_delivery_date: e.target.value}))}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="special_instructions">Special Instructions</Label>
              <Textarea
                id="special_instructions"
                value={orderData.special_instructions}
                onChange={(e) => setOrderData(prev => ({...prev, special_instructions: e.target.value}))}
                placeholder="Any special delivery instructions"
                rows={2}
              />
            </div>
          </CardContent>
        </Card>

        {/* Order Summary */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calculator className="w-5 h-5 mr-2" />
              Order Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal:</span>
                <span>{getCurrencySymbol(calculations.currency)} {calculations.subtotal}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Platform Fee (2.5%):</span>
                <span>{getCurrencySymbol(calculations.currency)} {calculations.platformFee}</span>
              </div>
              <div className="border-t pt-3">
                <div className="flex justify-between text-lg font-semibold">
                  <span>Total:</span>
                  <span>{getCurrencySymbol(calculations.currency)} {calculations.total}</span>
                </div>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-start">
                <Shield className="w-5 h-5 text-blue-600 mt-0.5 mr-3" />
                <div className="text-sm text-blue-800">
                  <p className="font-medium mb-2">Escrow Protection</p>
                  <ul className="space-y-1 text-xs">
                    <li>• Funds held securely until order completion</li>
                    <li>• 7-day auto-release after delivery confirmation</li>
                    <li>• Dispute resolution available if needed</li>
                    <li>• Manual bank payment verification required</li>
                  </ul>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-between">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </Button>
          
          <Button
            type="submit"
            disabled={loading || calculations.total === '0.00'}
            className="bg-emerald-600 hover:bg-emerald-700"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Creating Order...
              </>
            ) : (
              <>
                <CreditCard className="w-4 h-4 mr-2" />
                Create Order & Pay {getCurrencySymbol(calculations.currency)} {calculations.total}
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default OrderCreation;
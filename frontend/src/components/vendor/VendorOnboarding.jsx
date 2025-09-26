import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { 
  Building2, 
  MapPin, 
  Globe, 
  FileText, 
  Calendar,
  Users,
  CheckCircle,
  ArrowRight,
  ArrowLeft,
  Shield,
  Upload,
  Award,
  Clock
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { vendorEcosystemAPI } from '../../services/ecosystemAPI';
import { useNavigate } from 'react-router-dom';
import DocumentUpload from './DocumentUpload';

const VendorOnboarding = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    business_name: '',
    business_description: '',
    category: '',
    website: '',
    business_address: '',
    registration_number: '',
    tax_id: '',
    established_year: '',
    employee_count: '',
    logo_url: ''
  });
  const [documentsUploaded, setDocumentsUploaded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const { user } = useAuth();
  const navigate = useNavigate();

  const businessCategories = [
    { value: 'technology', label: 'Technology' },
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'agriculture', label: 'Agriculture' },
    { value: 'healthcare', label: 'Healthcare' },
    { value: 'education', label: 'Education' },
    { value: 'finance', label: 'Finance' },
    { value: 'retail', label: 'Retail' },
    { value: 'services', label: 'Services' },
    { value: 'construction', label: 'Construction' },
    { value: 'logistics', label: 'Logistics' },
    { value: 'food_beverage', label: 'Food & Beverage' },
    { value: 'automotive', label: 'Automotive' },
    { value: 'textile', label: 'Textile' },
    { value: 'energy', label: 'Energy' },
    { value: 'real_estate', label: 'Real Estate' },
    { value: 'other', label: 'Other' }
  ];

  const employeeRanges = [
    { value: '1', label: '1 employee (Solo business)' },
    { value: '5', label: '2-5 employees' },
    { value: '15', label: '6-15 employees' },
    { value: '50', label: '16-50 employees' },
    { value: '200', label: '51-200 employees' },
    { value: '1000', label: '201-1000 employees' },
    { value: '5000', label: '1000+ employees' }
  ];

  const steps = [
    { number: 1, title: 'Business Information', description: 'Tell us about your business' },
    { number: 2, title: 'Business Details', description: 'Additional business information' },
    { number: 3, title: 'Document Upload', description: 'Upload verification documents' },
    { number: 4, title: 'Review & Submit', description: 'Verify your information' },
    { number: 5, title: 'Verification Process', description: 'Awaiting approval' }
  ];

  const getProgress = () => (currentStep / steps.length) * 100;

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleSelectChange = (name, value) => {
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const validateStep = (step) => {
    setError('');
    
    if (step === 1) {
      if (!formData.business_name.trim()) {
        setError('Business name is required');
        return false;
      }
      if (!formData.category) {
        setError('Business category is required');
        return false;
      }
      if (!formData.business_address.trim()) {
        setError('Business address is required');
        return false;
      }
    }
    
    return true;
  };

  const nextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => Math.min(prev + 1, steps.length));
    }
  };

  const prevStep = () => {
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async () => {
    if (!validateStep(currentStep)) return;

    setLoading(true);
    setError('');

    try {
      // Convert employee count to number
      const profileData = {
        ...formData,
        established_year: formData.established_year ? parseInt(formData.established_year) : null,
        employee_count: formData.employee_count ? parseInt(formData.employee_count) : null
      };

      await vendorEcosystemAPI.createVendorProfile(profileData);
      
      // Move to verification process step
      setCurrentStep(5);
      setSuccess('Vendor profile submitted successfully! Your documents are now under review.');
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to create vendor profile');
    } finally {
      setLoading(false);
    }
  };

  // Render step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            {/* Business Name */}
            <div className="space-y-2">
              <Label htmlFor="business_name" className="text-sm font-medium text-gray-700">
                Business Name *
              </Label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  id="business_name"
                  name="business_name"
                  value={formData.business_name}
                  onChange={handleInputChange}
                  placeholder="Enter your business name"
                  className="pl-10 h-12"
                  required
                />
              </div>
            </div>

            {/* Business Category */}
            <div className="space-y-2">
              <Label htmlFor="category" className="text-sm font-medium text-gray-700">
                Business Category *
              </Label>
              <Select value={formData.category} onValueChange={(value) => handleSelectChange('category', value)}>
                <SelectTrigger className="h-12">
                  <SelectValue placeholder="Select your business category" />
                </SelectTrigger>
                <SelectContent>
                  {businessCategories.map((category) => (
                    <SelectItem key={category.value} value={category.value}>
                      {category.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Business Description */}
            <div className="space-y-2">
              <Label htmlFor="business_description" className="text-sm font-medium text-gray-700">
                Business Description
              </Label>
              <Textarea
                id="business_description"
                name="business_description"
                value={formData.business_description}
                onChange={handleInputChange}
                placeholder="Describe what your business does..."
                rows={4}
                className="resize-none"
              />
            </div>

            {/* Business Address */}
            <div className="space-y-2">
              <Label htmlFor="business_address" className="text-sm font-medium text-gray-700">
                Business Address *
              </Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 text-gray-400 w-5 h-5" />
                <Textarea
                  id="business_address"
                  name="business_address"
                  value={formData.business_address}
                  onChange={handleInputChange}
                  placeholder="Enter your complete business address"
                  rows={3}
                  className="pl-10 resize-none"
                  required
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            {/* Website */}
            <div className="space-y-2">
              <Label htmlFor="website" className="text-sm font-medium text-gray-700">
                Website
              </Label>
              <div className="relative">
                <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  id="website"
                  name="website"
                  type="url"
                  value={formData.website}
                  onChange={handleInputChange}
                  placeholder="https://www.yourwebsite.com"
                  className="pl-10 h-12"
                />
              </div>
            </div>

            {/* Registration Number */}
            <div className="space-y-2">
              <Label htmlFor="registration_number" className="text-sm font-medium text-gray-700">
                Business Registration Number
              </Label>
              <div className="relative">
                <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  id="registration_number"
                  name="registration_number"
                  value={formData.registration_number}
                  onChange={handleInputChange}
                  placeholder="Enter business registration number"
                  className="pl-10 h-12"
                />
              </div>
            </div>

            {/* Tax ID */}
            <div className="space-y-2">
              <Label htmlFor="tax_id" className="text-sm font-medium text-gray-700">
                Tax ID / VAT Number
              </Label>
              <div className="relative">
                <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  id="tax_id"
                  name="tax_id"
                  value={formData.tax_id}
                  onChange={handleInputChange}
                  placeholder="Enter tax ID or VAT number"
                  className="pl-10 h-12"
                />
              </div>
            </div>

            {/* Established Year */}
            <div className="space-y-2">
              <Label htmlFor="established_year" className="text-sm font-medium text-gray-700">
                Year Established
              </Label>
              <div className="relative">
                <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <Input
                  id="established_year"
                  name="established_year"
                  type="number"
                  min="1800"
                  max={new Date().getFullYear()}
                  value={formData.established_year}
                  onChange={handleInputChange}
                  placeholder="e.g., 2020"
                  className="pl-10 h-12"
                />
              </div>
            </div>

            {/* Employee Count */}
            <div className="space-y-2">
              <Label htmlFor="employee_count" className="text-sm font-medium text-gray-700">
                Number of Employees
              </Label>
              <Select value={formData.employee_count} onValueChange={(value) => handleSelectChange('employee_count', value)}>
                <SelectTrigger className="h-12">
                  <Users className="w-5 h-5 text-gray-400 mr-2" />
                  <SelectValue placeholder="Select number of employees" />
                </SelectTrigger>
                <SelectContent>
                  {employeeRanges.map((range) => (
                    <SelectItem key={range.value} value={range.value}>
                      {range.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <CheckCircle className="w-6 h-6 text-green-600 mr-2" />
                <h3 className="text-lg font-semibold text-green-800">Review Your Information</h3>
              </div>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Business Name</p>
                    <p className="font-medium">{formData.business_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Category</p>
                    <p className="font-medium">
                      {businessCategories.find(cat => cat.value === formData.category)?.label || formData.category}
                    </p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-sm text-gray-600">Business Address</p>
                    <p className="font-medium">{formData.business_address}</p>
                  </div>
                  {formData.business_description && (
                    <div className="md:col-span-2">
                      <p className="text-sm text-gray-600">Description</p>
                      <p className="font-medium">{formData.business_description}</p>
                    </div>
                  )}
                  {formData.website && (
                    <div>
                      <p className="text-sm text-gray-600">Website</p>
                      <p className="font-medium">{formData.website}</p>
                    </div>
                  )}
                  {formData.registration_number && (
                    <div>
                      <p className="text-sm text-gray-600">Registration Number</p>
                      <p className="font-medium">{formData.registration_number}</p>
                    </div>
                  )}
                  {formData.tax_id && (
                    <div>
                      <p className="text-sm text-gray-600">Tax ID</p>
                      <p className="font-medium">{formData.tax_id}</p>
                    </div>
                  )}
                  {formData.established_year && (
                    <div>
                      <p className="text-sm text-gray-600">Year Established</p>
                      <p className="font-medium">{formData.established_year}</p>
                    </div>
                  )}
                  {formData.employee_count && (
                    <div>
                      <p className="text-sm text-gray-600">Employees</p>
                      <p className="font-medium">
                        {employeeRanges.find(range => range.value === formData.employee_count)?.label || formData.employee_count}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <Alert className="border-blue-200 bg-blue-50">
              <Shield className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-blue-800">
                After creating your profile, you'll need to upload verification documents to complete the verification process.
                This includes business registration certificates, tax documents, and owner identification.
              </AlertDescription>
            </Alert>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Building2 className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Vendor Onboarding</h1>
          <p className="text-gray-600">Set up your vendor profile to start your verification journey</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            {steps.map((step) => (
              <div key={step.number} className="flex flex-col items-center flex-1">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold ${
                  currentStep >= step.number 
                    ? 'bg-emerald-600 text-white' 
                    : 'bg-gray-200 text-gray-600'
                }`}>
                  {currentStep > step.number ? <CheckCircle className="w-6 h-6" /> : step.number}
                </div>
                <div className="mt-2 text-center">
                  <p className="text-sm font-medium text-gray-900">{step.title}</p>
                  <p className="text-xs text-gray-600">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
          <Progress value={getProgress()} className="h-2" />
        </div>

        {/* Main Form Card */}
        <Card className="shadow-2xl border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="pb-6">
            <CardTitle className="text-2xl font-bold text-center text-gray-900">
              {steps[currentStep - 1]?.title}
            </CardTitle>
          </CardHeader>
          
          <CardContent>
            {error && (
              <Alert className="border-red-200 bg-red-50 mb-6">
                <AlertDescription className="text-red-800">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="border-green-200 bg-green-50 mb-6">
                <AlertDescription className="text-green-800">
                  {success}
                </AlertDescription>
              </Alert>
            )}

            {renderStepContent()}

            {/* Navigation Buttons */}
            <div className="flex justify-between mt-8">
              <Button
                type="button"
                variant="outline"
                onClick={prevStep}
                disabled={currentStep === 1}
                className="flex items-center"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Previous
              </Button>

              {currentStep < steps.length ? (
                <Button
                  type="button"
                  onClick={nextStep}
                  className="flex items-center bg-emerald-600 hover:bg-emerald-700"
                >
                  Next
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              ) : (
                <Button
                  type="button"
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex items-center bg-emerald-600 hover:bg-emerald-700"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Creating Profile...
                    </>
                  ) : (
                    <>
                      Create Profile
                      <CheckCircle className="w-4 h-4 ml-2" />
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* User Info */}
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-600">
            Welcome, <span className="font-medium">{user?.full_name}</span> • {user?.email}
          </p>
        </div>
      </div>
    </div>
  );
};

export default VendorOnboarding;
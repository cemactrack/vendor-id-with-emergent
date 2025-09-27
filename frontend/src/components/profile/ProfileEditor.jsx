import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Progress } from '../ui/progress';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import { Badge } from '../ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { 
  Building, 
  MapPin, 
  Phone, 
  Mail, 
  Globe, 
  Clock, 
  Users, 
  Camera,
  Plus,
  Trash2,
  Save,
  CheckCircle,
  AlertCircle,
  Loader2,
  Edit
} from 'lucide-react';

const ProfileEditor = () => {
  const [profile, setProfile] = useState({
    business_name: '',
    business_description: '',
    tagline: '',
    website: '',
    business_address: '',
    city: '',
    state: '',
    country: 'Nigeria',
    postal_code: '',
    established_year: '',
    employee_count: '',
    annual_revenue: '',
    logo_url: '',
    cover_image_url: '',
    business_hours: [],
    business_contacts: [],
    social_media: [],
    business_images: []
  });

  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [activeTab, setActiveTab] = useState('basic');
  const [completionScore, setCompletionScore] = useState(0);

  useEffect(() => {
    loadProfileData();
    loadServices();
  }, []);

  const loadProfileData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/vendors/dashboard`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('vendor_ecosystem_token')}` }
      });

      const data = await response.json();
      if (data.success && data.profile) {
        setProfile(prevProfile => ({
          ...prevProfile,
          ...data.profile,
          business_hours: data.profile.business_hours || [],
          business_contacts: data.profile.business_contacts || [],
          social_media: data.profile.social_media || [],
          business_images: data.profile.business_images || []
        }));
        setCompletionScore(data.profile.profile_completion_score || 0);
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
      setError('Failed to load profile data');
    } finally {
      setLoading(false);
    }
  };

  const loadServices = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/profile/services`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('vendor_ecosystem_token')}` }
      });

      const data = await response.json();
      if (data.success) {
        setServices(data.services);
      }
    } catch (err) {
      console.error('Failed to load services:', err);
    }
  };

  const saveProfile = async () => {
    try {
      setSaving(true);
      setError('');
      setSuccess('');

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/profile/update`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('vendor_ecosystem_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(profile)
      });

      const data = await response.json();
      
      if (data.success) {
        setSuccess(`Profile updated successfully! ${data.updated_fields.length} fields updated.`);
        setCompletionScore(data.new_completion_score);
        
        if (data.badges_earned.length > 0) {
          setSuccess(prev => prev + ` New badges earned: ${data.badges_earned.join(', ')}`);
        }
      } else {
        setError(data.validation_errors?.join(', ') || 'Failed to update profile');
      }
    } catch (err) {
      console.error('Profile update error:', err);
      setError('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const addBusinessHour = () => {
    const newHour = {
      day_of_week: 1,
      day_name: 'Monday',
      is_open: true,
      open_time: '09:00',
      close_time: '17:00',
      is_24_hours: false
    };
    setProfile(prev => ({
      ...prev,
      business_hours: [...prev.business_hours, newHour]
    }));
  };

  const updateBusinessHour = (index, field, value) => {
    const updatedHours = [...profile.business_hours];
    updatedHours[index] = { ...updatedHours[index], [field]: value };
    setProfile(prev => ({ ...prev, business_hours: updatedHours }));
  };

  const removeBusinessHour = (index) => {
    const updatedHours = profile.business_hours.filter((_, i) => i !== index);
    setProfile(prev => ({ ...prev, business_hours: updatedHours }));
  };

  const addContact = () => {
    const newContact = {
      contact_type: 'primary',
      contact_person: '',
      job_title: '',
      phone: '',
      email: '',
      is_primary: profile.business_contacts.length === 0,
      is_public: true
    };
    setProfile(prev => ({
      ...prev,
      business_contacts: [...prev.business_contacts, newContact]
    }));
  };

  const updateContact = (index, field, value) => {
    const updatedContacts = [...profile.business_contacts];
    updatedContacts[index] = { ...updatedContacts[index], [field]: value };
    setProfile(prev => ({ ...prev, business_contacts: updatedContacts }));
  };

  const removeContact = (index) => {
    const updatedContacts = profile.business_contacts.filter((_, i) => i !== index);
    setProfile(prev => ({ ...prev, business_contacts: updatedContacts }));
  };

  const renderBasicInfo = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building className="w-5 h-5" />
            Business Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="business_name">Business Name *</Label>
              <Input
                id="business_name"
                value={profile.business_name}
                onChange={(e) => setProfile(prev => ({ ...prev, business_name: e.target.value }))}
                placeholder="Your Business Name"
              />
            </div>
            <div>
              <Label htmlFor="tagline">Business Tagline</Label>
              <Input
                id="tagline"
                value={profile.tagline}
                onChange={(e) => setProfile(prev => ({ ...prev, tagline: e.target.value }))}
                placeholder="Your business in one line"
              />
            </div>
          </div>
          
          <div>
            <Label htmlFor="business_description">Business Description *</Label>
            <Textarea
              id="business_description"
              value={profile.business_description}
              onChange={(e) => setProfile(prev => ({ ...prev, business_description: e.target.value }))}
              placeholder="Describe your business, services, and what makes you unique..."
              rows={4}
            />
            <p className="text-sm text-gray-500 mt-1">
              {profile.business_description.length}/500 characters (minimum 50 required)
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="website">Website</Label>
              <Input
                id="website"
                value={profile.website}
                onChange={(e) => setProfile(prev => ({ ...prev, website: e.target.value }))}
                placeholder="https://yourwebsite.com"
              />
            </div>
            <div>
              <Label htmlFor="established_year">Established Year</Label>
              <Input
                id="established_year"
                type="number"
                min="1800"
                max={new Date().getFullYear()}
                value={profile.established_year}
                onChange={(e) => setProfile(prev => ({ ...prev, established_year: parseInt(e.target.value) }))}
                placeholder="2020"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="employee_count">Number of Employees</Label>
              <Select
                value={profile.employee_count?.toString()}
                onValueChange={(value) => setProfile(prev => ({ ...prev, employee_count: parseInt(value) }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select employee count" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1</SelectItem>
                  <SelectItem value="2">2-5</SelectItem>
                  <SelectItem value="6">6-10</SelectItem>
                  <SelectItem value="11">11-25</SelectItem>
                  <SelectItem value="26">26-50</SelectItem>
                  <SelectItem value="51">51-100</SelectItem>
                  <SelectItem value="101">100+</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="annual_revenue">Annual Revenue</Label>
              <Select
                value={profile.annual_revenue}
                onValueChange={(value) => setProfile(prev => ({ ...prev, annual_revenue: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select revenue range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="< ₦1M">< ₦1M</SelectItem>
                  <SelectItem value="₦1M - ₦5M">₦1M - ₦5M</SelectItem>
                  <SelectItem value="₦5M - ₦10M">₦5M - ₦10M</SelectItem>
                  <SelectItem value="₦10M - ₦50M">₦10M - ₦50M</SelectItem>
                  <SelectItem value="₦50M+">₦50M+</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-5 h-5" />
            Location Information
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="business_address">Business Address *</Label>
            <Input
              id="business_address"
              value={profile.business_address}
              onChange={(e) => setProfile(prev => ({ ...prev, business_address: e.target.value }))}
              placeholder="123 Business Street"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="city">City *</Label>
              <Input
                id="city"
                value={profile.city}
                onChange={(e) => setProfile(prev => ({ ...prev, city: e.target.value }))}
                placeholder="Lagos"
              />
            </div>
            <div>
              <Label htmlFor="state">State *</Label>
              <Input
                id="state"
                value={profile.state}
                onChange={(e) => setProfile(prev => ({ ...prev, state: e.target.value }))}
                placeholder="Lagos State"
              />
            </div>
            <div>
              <Label htmlFor="postal_code">Postal Code</Label>
              <Input
                id="postal_code"
                value={profile.postal_code}
                onChange={(e) => setProfile(prev => ({ ...prev, postal_code: e.target.value }))}
                placeholder="100001"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  const renderContactInfo = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="w-5 h-5" />
            Business Contacts
          </CardTitle>
          <CardDescription>
            Add multiple contact persons for different purposes (sales, support, etc.)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {profile.business_contacts.map((contact, index) => (
            <div key={index} className="p-4 border rounded-lg space-y-4">
              <div className="flex justify-between items-center">
                <h4 className="font-medium">Contact {index + 1}</h4>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => removeContact(index)}
                  className="text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Contact Type</Label>
                  <Select
                    value={contact.contact_type}
                    onValueChange={(value) => updateContact(index, 'contact_type', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="primary">Primary</SelectItem>
                      <SelectItem value="sales">Sales</SelectItem>
                      <SelectItem value="support">Support</SelectItem>
                      <SelectItem value="technical">Technical</SelectItem>
                      <SelectItem value="billing">Billing</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Contact Person</Label>
                  <Input
                    value={contact.contact_person}
                    onChange={(e) => updateContact(index, 'contact_person', e.target.value)}
                    placeholder="John Doe"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Job Title</Label>
                  <Input
                    value={contact.job_title}
                    onChange={(e) => updateContact(index, 'job_title', e.target.value)}
                    placeholder="Sales Manager"
                  />
                </div>
                <div>
                  <Label>Phone</Label>
                  <Input
                    value={contact.phone}
                    onChange={(e) => updateContact(index, 'phone', e.target.value)}
                    placeholder="+234 xxx xxx xxxx"
                  />
                </div>
              </div>
              
              <div>
                <Label>Email</Label>
                <Input
                  type="email"
                  value={contact.email}
                  onChange={(e) => updateContact(index, 'email', e.target.value)}
                  placeholder="contact@company.com"
                />
              </div>
              
              <div className="flex items-center space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={contact.is_primary}
                    onChange={(e) => updateContact(index, 'is_primary', e.target.checked)}
                  />
                  <span className="text-sm">Primary Contact</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={contact.is_public}
                    onChange={(e) => updateContact(index, 'is_public', e.target.checked)}
                  />
                  <span className="text-sm">Show on Public Profile</span>
                </label>
              </div>
            </div>
          ))}
          
          <Button onClick={addContact} variant="outline" className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            Add Contact
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Business Hours
          </CardTitle>
          <CardDescription>
            Set your operational hours for customer reference
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {profile.business_hours.map((hour, index) => (
            <div key={index} className="p-4 border rounded-lg space-y-4">
              <div className="flex justify-between items-center">
                <h4 className="font-medium">{hour.day_name}</h4>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => removeBusinessHour(index)}
                  className="text-red-600"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <Label>Day</Label>
                  <Select
                    value={hour.day_name}
                    onValueChange={(value) => {
                      const dayMap = { Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4, Friday: 5, Saturday: 6, Sunday: 0 };
                      updateBusinessHour(index, 'day_name', value);
                      updateBusinessHour(index, 'day_of_week', dayMap[value]);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Monday">Monday</SelectItem>
                      <SelectItem value="Tuesday">Tuesday</SelectItem>
                      <SelectItem value="Wednesday">Wednesday</SelectItem>
                      <SelectItem value="Thursday">Thursday</SelectItem>
                      <SelectItem value="Friday">Friday</SelectItem>
                      <SelectItem value="Saturday">Saturday</SelectItem>
                      <SelectItem value="Sunday">Sunday</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Open Time</Label>
                  <Input
                    type="time"
                    value={hour.open_time}
                    onChange={(e) => updateBusinessHour(index, 'open_time', e.target.value)}
                    disabled={!hour.is_open || hour.is_24_hours}
                  />
                </div>
                <div>
                  <Label>Close Time</Label>
                  <Input
                    type="time"
                    value={hour.close_time}
                    onChange={(e) => updateBusinessHour(index, 'close_time', e.target.value)}
                    disabled={!hour.is_open || hour.is_24_hours}
                  />
                </div>
                <div className="flex flex-col space-y-2">
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={hour.is_open}
                      onChange={(e) => updateBusinessHour(index, 'is_open', e.target.checked)}
                    />
                    <span className="text-sm">Open</span>
                  </label>
                  <label className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      checked={hour.is_24_hours}
                      onChange={(e) => updateBusinessHour(index, 'is_24_hours', e.target.checked)}
                      disabled={!hour.is_open}
                    />
                    <span className="text-sm">24 Hours</span>
                  </label>
                </div>
              </div>
            </div>
          ))}
          
          <Button onClick={addBusinessHour} variant="outline" className="w-full">
            <Plus className="w-4 h-4 mr-2" />
            Add Business Hours
          </Button>
        </CardContent>
      </Card>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-8 w-8 animate-spin mr-2" />
        <span>Loading profile...</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Edit Profile</h1>
        <p className="text-gray-600">Update your business information and settings</p>
        
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Profile Completion</span>
            <span className="text-sm text-gray-600">{completionScore.toFixed(1)}%</span>
          </div>
          <Progress value={completionScore} className="w-full" />
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert className="mb-6">
          <CheckCircle className="h-4 w-4" />
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="basic">
            <Building className="w-4 h-4 mr-2" />
            Basic Info
          </TabsTrigger>
          <TabsTrigger value="contact">
            <Phone className="w-4 h-4 mr-2" />
            Contact & Hours
          </TabsTrigger>
        </TabsList>

        <TabsContent value="basic">
          {renderBasicInfo()}
        </TabsContent>

        <TabsContent value="contact">
          {renderContactInfo()}
        </TabsContent>
      </Tabs>

      <div className="mt-8 flex justify-end space-x-4">
        <Button variant="outline" onClick={loadProfileData}>
          <Edit className="w-4 h-4 mr-2" />
          Reset Changes
        </Button>
        <Button onClick={saveProfile} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Profile
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

export default ProfileEditor;
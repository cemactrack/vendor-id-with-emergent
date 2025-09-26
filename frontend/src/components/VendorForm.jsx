import React, { useState, useRef } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Upload, X, User, Calendar, Hash } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { vendorAPI } from '../services/api';

const VendorForm = ({ vendor = null, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    name: vendor?.name || '',
    photo: vendor?.photo || '',
    issueDate: vendor?.issueDate || new Date().toISOString().split('T')[0]
  });
  
  const [photoPreview, setPhotoPreview] = useState(vendor?.photo || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef(null);
  const { toast } = useToast();

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast({
          title: "File too large",
          description: "Please select an image smaller than 5MB",
          variant: "destructive"
        });
        return;
      }

      try {
        setIsSubmitting(true);
        toast({
          title: "Uploading...",
          description: "Processing your image"
        });

        const photoUrl = await vendorAPI.uploadPhoto(file);
        setPhotoPreview(photoUrl);
        setFormData(prev => ({
          ...prev,
          photo: photoUrl
        }));

        toast({
          title: "Success",
          description: "Photo uploaded successfully"
        });
      } catch (error) {
        toast({
          title: "Upload failed",
          description: error.response?.data?.detail || "Failed to upload photo",
          variant: "destructive"
        });
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  const removePhoto = () => {
    setPhotoPreview('');
    setFormData(prev => ({
      ...prev,
      photo: ''
    }));
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast({
        title: "Validation Error",
        description: "Vendor name is required",
        variant: "destructive"
      });
      return;
    }

    setIsSubmitting(true);
    
    try {
      let result;
      if (vendor) {
        result = await vendorAPI.updateVendor(vendor.id, formData);
        toast({
          title: "Success",
          description: "Vendor updated successfully"
        });
      } else {
        result = await vendorAPI.createVendor(formData);
        toast({
          title: "Success",
          description: "Vendor created successfully"
        });
      }
      
      onSave(result);
    } catch (error) {
      toast({
        title: "Error",
        description: error.message || "Something went wrong",
        variant: "destructive"
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <User className="w-5 h-5" />
          <span>{vendor ? 'Edit Vendor' : 'Create New Vendor'}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Photo Upload */}
          <div className="space-y-2">
            <Label htmlFor="photo">Vendor Photo</Label>
            <div className="flex items-center space-x-4">
              {photoPreview ? (
                <div className="relative">
                  <img 
                    src={photoPreview} 
                    alt="Preview" 
                    className="w-20 h-20 rounded-full object-cover border-2 border-gray-300"
                  />
                  <button
                    type="button"
                    onClick={removePhoto}
                    className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ) : (
                <div className="w-20 h-20 rounded-full border-2 border-dashed border-gray-300 flex items-center justify-center bg-gray-50">
                  <User className="w-8 h-8 text-gray-400" />
                </div>
              )}
              
              <div className="flex-1">
                <input
                  ref={fileInputRef}
                  type="file"
                  id="photo"
                  accept="image/*"
                  onChange={handlePhotoUpload}
                  className="hidden"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Photo
                </Button>
                <p className="text-sm text-gray-500 mt-1">
                  JPG, PNG or GIF (max 5MB)
                </p>
              </div>
            </div>
          </div>

          {/* Vendor Name */}
          <div className="space-y-2">
            <Label htmlFor="name">Vendor Name *</Label>
            <Input
              id="name"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="Enter full name in UPPERCASE"
              className="font-semibold"
              required
            />
          </div>

          {/* Issue Date */}
          <div className="space-y-2">
            <Label htmlFor="issueDate">Issue Date</Label>
            <div className="relative">
              <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                id="issueDate"
                name="issueDate"
                type="date"
                value={formData.issueDate}
                onChange={handleInputChange}
                className="pl-10"
              />
            </div>
          </div>

          {/* Vendor ID (Read-only for existing vendors) */}
          {vendor && (
            <div className="space-y-2">
              <Label htmlFor="vendorId">Vendor ID</Label>
              <div className="relative">
                <Hash className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                <Input
                  id="vendorId"
                  value={vendor.id}
                  className="pl-10 bg-gray-50"
                  readOnly
                />
              </div>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex space-x-3 pt-4">
            <Button 
              type="submit" 
              disabled={isSubmitting}
              className="flex-1"
            >
              {isSubmitting ? 'Saving...' : vendor ? 'Update Vendor' : 'Create Vendor'}
            </Button>
            <Button 
              type="button" 
              variant="outline" 
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default VendorForm;
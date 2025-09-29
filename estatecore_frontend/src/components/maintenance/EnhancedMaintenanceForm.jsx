import React, { useState, useEffect, useRef } from 'react';
import { Camera, Upload, X, AlertCircle, CheckCircle, Clock, MapPin } from 'lucide-react';

const MAINTENANCE_CATEGORIES = [
  { id: 'plumbing', name: 'Plumbing', icon: '🔧', color: '#2563eb', requiresPhotos: true },
  { id: 'electrical', name: 'Electrical', icon: '⚡', color: '#dc2626', requiresPhotos: true },
  { id: 'hvac', name: 'HVAC', icon: '🌡️', color: '#059669', requiresPhotos: false },
  { id: 'appliances', name: 'Appliances', icon: '🏠', color: '#7c3aed', requiresPhotos: true },
  { id: 'flooring', name: 'Flooring', icon: '🔨', color: '#92400e', requiresPhotos: true },
  { id: 'painting', name: 'Painting', icon: '🎨', color: '#db2777', requiresPhotos: true },
  { id: 'doors_windows', name: 'Doors & Windows', icon: '🚪', color: '#0891b2', requiresPhotos: true },
  { id: 'pest_control', name: 'Pest Control', icon: '🐛', color: '#ea580c', requiresPhotos: false },
  { id: 'security', name: 'Security', icon: '🔒', color: '#dc2626', requiresPhotos: true },
  { id: 'landscaping', name: 'Landscaping', icon: '🌱', color: '#059669', requiresPhotos: false },
  { id: 'cleaning', name: 'Cleaning', icon: '🧽', color: '#0891b2', requiresPhotos: false },
  { id: 'other', name: 'Other', icon: '🔧', color: '#6b7280', requiresPhotos: true }
];

const PRIORITY_LEVELS = [
  { 
    id: 'low', 
    name: 'Low Priority', 
    description: 'Non-urgent, can wait 7+ days',
    color: '#6b7280',
    examples: ['Cosmetic issues', 'Minor repairs', 'Routine maintenance']
  },
  { 
    id: 'medium', 
    name: 'Medium Priority', 
    description: 'Should be addressed within 3 days',
    color: '#f59e0b',
    examples: ['Appliance issues', 'Minor leaks', 'Door/window problems']
  },
  { 
    id: 'high', 
    name: 'High Priority', 
    description: 'Needs attention within 24 hours',
    color: '#ef4444',
    examples: ['Major leaks', 'Electrical issues', 'Security problems']
  },
  { 
    id: 'emergency', 
    name: 'Emergency', 
    description: 'Immediate attention required',
    color: '#dc2626',
    examples: ['No heat/AC', 'Power outage', 'Gas leaks', 'Major flooding']
  }
];

const CONTACT_METHODS = [
  { id: 'email', name: 'Email', icon: '📧' },
  { id: 'phone', name: 'Phone Call', icon: '📞' },
  { id: 'sms', name: 'Text Message', icon: '💬' }
];

const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16MB
const MAX_FILES = 10;
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];

export default function EnhancedMaintenanceForm({ onSubmit, onCancel, userInfo, properties = [] }) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '',
    priority: 'medium',
    property_id: '',
    unit_number: '',
    location_details: '',
    preferred_contact_method: 'email',
    access_instructions: ''
  });

  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  const [showCamera, setShowCamera] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const selectedCategory = MAINTENANCE_CATEGORIES.find(cat => cat.id === formData.category);
  const selectedPriority = PRIORITY_LEVELS.find(pri => pri.id === formData.priority);

  // Auto-fill user property if only one available
  useEffect(() => {
    if (properties.length === 1 && !formData.property_id) {
      setFormData(prev => ({ ...prev, property_id: properties[0].id }));
    }
  }, [properties, formData.property_id]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Description is required';
    }

    if (!formData.category) {
      newErrors.category = 'Please select a category';
    }

    if (!formData.property_id) {
      newErrors.property_id = 'Please select a property';
    }

    // Check if photos are required for this category
    if (selectedCategory?.requiresPhotos && selectedFiles.length === 0) {
      newErrors.photos = 'Photos are required for this type of request';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };

  const handleFileSelect = (files) => {
    const validFiles = Array.from(files).filter(file => {
      if (!ALLOWED_TYPES.includes(file.type)) {
        alert(`File "${file.name}" is not a supported image format`);
        return false;
      }
      if (file.size > MAX_FILE_SIZE) {
        alert(`File "${file.name}" is too large. Maximum size is 16MB`);
        return false;
      }
      return true;
    });

    if (selectedFiles.length + validFiles.length > MAX_FILES) {
      alert(`Maximum ${MAX_FILES} files allowed`);
      return;
    }

    const newFiles = [...selectedFiles, ...validFiles];
    setSelectedFiles(newFiles);

    // Generate previews
    validFiles.forEach(file => {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviews(prev => [...prev, {
          file,
          url: e.target.result,
          id: Date.now() + Math.random()
        }]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeFile = (index) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    const newPreviews = previews.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    setPreviews(newPreviews);
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files) {
      handleFileSelect(e.dataTransfer.files);
    }
  };

  const handleCameraCapture = (e) => {
    if (e.target.files) {
      handleFileSelect(e.target.files);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const formDataToSubmit = new FormData();
      
      // Append form fields
      Object.keys(formData).forEach(key => {
        formDataToSubmit.append(key, formData[key]);
      });

      // Append user info
      if (userInfo?.id) {
        formDataToSubmit.append('user_id', userInfo.id);
        formDataToSubmit.append('tenant_id', userInfo.id);
      }

      // Append photos
      selectedFiles.forEach(file => {
        formDataToSubmit.append('photos', file);
      });

      await onSubmit(formDataToSubmit);
      
      // Reset form on success
      setFormData({
        title: '',
        description: '',
        category: '',
        priority: 'medium',
        property_id: '',
        unit_number: '',
        location_details: '',
        preferred_contact_method: 'email',
        access_instructions: ''
      });
      setSelectedFiles([]);
      setPreviews([]);
      setCurrentStep(1);
      
    } catch (error) {
      console.error('Error submitting maintenance request:', error);
      alert('Failed to submit request. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStepIndicator = () => (
    <div className="flex justify-center mb-8">
      <div className="flex items-center space-x-4">
        {[1, 2, 3].map(step => (
          <div key={step} className="flex items-center">
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold
              ${currentStep >= step 
                ? 'bg-blue-600 text-white' 
                : 'bg-gray-200 text-gray-500'
              }
            `}>
              {step}
            </div>
            {step < 3 && (
              <div className={`
                w-12 h-1 mx-2
                ${currentStep > step ? 'bg-blue-600' : 'bg-gray-200'}
              `} />
            )}
          </div>
        ))}
      </div>
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
        
        {/* Title */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Request Title *
          </label>
          <input
            type="text"
            value={formData.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            placeholder="Brief description of the issue"
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.title ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.title && (
            <p className="mt-1 text-sm text-red-600 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" />
              {errors.title}
            </p>
          )}
        </div>

        {/* Description */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Detailed Description *
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            placeholder="Please provide as much detail as possible about the issue..."
            rows={4}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.description ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.description && (
            <p className="mt-1 text-sm text-red-600 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" />
              {errors.description}
            </p>
          )}
        </div>

        {/* Category Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category *
          </label>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {MAINTENANCE_CATEGORIES.map(category => (
              <button
                key={category.id}
                type="button"
                onClick={() => handleInputChange('category', category.id)}
                className={`
                  p-3 rounded-lg border-2 text-left transition-all
                  ${formData.category === category.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{category.icon}</span>
                  <span className="font-medium text-sm">{category.name}</span>
                </div>
                {category.requiresPhotos && (
                  <div className="mt-1 text-xs text-gray-500 flex items-center">
                    <Camera className="w-3 h-3 mr-1" />
                    Photos required
                  </div>
                )}
              </button>
            ))}
          </div>
          {errors.category && (
            <p className="mt-1 text-sm text-red-600 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" />
              {errors.category}
            </p>
          )}
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Priority & Location</h3>
        
        {/* Priority Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Priority Level *
          </label>
          <div className="space-y-3">
            {PRIORITY_LEVELS.map(priority => (
              <button
                key={priority.id}
                type="button"
                onClick={() => handleInputChange('priority', priority.id)}
                className={`
                  w-full p-4 rounded-lg border-2 text-left transition-all
                  ${formData.priority === priority.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div 
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: priority.color }}
                      />
                      <span className="font-semibold">{priority.name}</span>
                      {priority.id === 'emergency' && (
                        <span className="text-red-600 animate-pulse">🚨</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{priority.description}</p>
                    <div className="mt-2">
                      <span className="text-xs text-gray-500">Examples: </span>
                      <span className="text-xs text-gray-600">
                        {priority.examples.join(', ')}
                      </span>
                    </div>
                  </div>
                  {formData.priority === priority.id && (
                    <CheckCircle className="w-5 h-5 text-blue-600" />
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Property Selection */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Property *
          </label>
          <select
            value={formData.property_id}
            onChange={(e) => handleInputChange('property_id', e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.property_id ? 'border-red-500' : 'border-gray-300'
            }`}
          >
            <option value="">Select a property...</option>
            {properties.map(property => (
              <option key={property.id} value={property.id}>
                {property.name} - {property.address}
              </option>
            ))}
          </select>
          {errors.property_id && (
            <p className="mt-1 text-sm text-red-600 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" />
              {errors.property_id}
            </p>
          )}
        </div>

        {/* Unit Number */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Unit Number
          </label>
          <input
            type="text"
            value={formData.unit_number}
            onChange={(e) => handleInputChange('unit_number', e.target.value)}
            placeholder="e.g., 2B, 101, etc."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Location Details */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <MapPin className="w-4 h-4 inline mr-1" />
            Specific Location
          </label>
          <input
            type="text"
            value={formData.location_details}
            onChange={(e) => handleInputChange('location_details', e.target.value)}
            placeholder="e.g., Master bathroom, Kitchen sink, Living room wall, etc."
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Photos & Additional Information</h3>
        
        {/* Photo Upload */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Photos {selectedCategory?.requiresPhotos && '*'}
            {selectedCategory?.requiresPhotos && (
              <span className="text-sm text-gray-500 ml-1">(Required for this category)</span>
            )}
          </label>
          
          {/* Drag & Drop Area */}
          <div
            className={`
              relative border-2 border-dashed rounded-lg p-6 text-center transition-colors
              ${dragActive 
                ? 'border-blue-500 bg-blue-50' 
                : 'border-gray-300 hover:border-gray-400'
              }
              ${errors.photos ? 'border-red-500' : ''}
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="space-y-3">
              <div className="flex justify-center">
                <Upload className="w-12 h-12 text-gray-400" />
              </div>
              <div>
                <p className="text-lg font-medium text-gray-900">
                  Drop photos here or click to select
                </p>
                <p className="text-sm text-gray-500">
                  Up to {MAX_FILES} files, max 16MB each
                </p>
                <p className="text-xs text-gray-400">
                  Supported: JPG, PNG, GIF, BMP, WebP
                </p>
              </div>
              
              <div className="flex justify-center space-x-4">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <Upload className="w-4 h-4 mr-2" />
                  Choose Files
                </button>
                
                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <Camera className="w-4 h-4 mr-2" />
                  Take Photo
                </button>
              </div>
            </div>
            
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*"
              onChange={(e) => handleFileSelect(e.target.files)}
              className="hidden"
            />
            
            <input
              ref={cameraInputRef}
              type="file"
              accept="image/*"
              capture="environment"
              onChange={handleCameraCapture}
              className="hidden"
            />
          </div>
          
          {errors.photos && (
            <p className="mt-1 text-sm text-red-600 flex items-center">
              <AlertCircle className="w-4 h-4 mr-1" />
              {errors.photos}
            </p>
          )}
          
          {/* Photo Previews */}
          {previews.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Selected Photos ({previews.length})
              </p>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {previews.map((preview, index) => (
                  <div key={preview.id} className="relative group">
                    <img
                      src={preview.url}
                      alt={`Preview ${index + 1}`}
                      className="w-full h-24 object-cover rounded-lg border"
                    />
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="w-4 h-4" />
                    </button>
                    <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-50 text-white text-xs p-1 rounded-b-lg truncate">
                      {preview.file.name}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Contact Preferences */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Preferred Contact Method
          </label>
          <div className="grid grid-cols-3 gap-3">
            {CONTACT_METHODS.map(method => (
              <button
                key={method.id}
                type="button"
                onClick={() => handleInputChange('preferred_contact_method', method.id)}
                className={`
                  p-3 rounded-lg border-2 text-center transition-all
                  ${formData.preferred_contact_method === method.id
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >
                <div className="text-lg mb-1">{method.icon}</div>
                <div className="text-sm font-medium">{method.name}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Access Instructions */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Access Instructions
          </label>
          <textarea
            value={formData.access_instructions}
            onChange={(e) => handleInputChange('access_instructions', e.target.value)}
            placeholder="Any special instructions for accessing the property or specific area..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-lg shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Submit Maintenance Request
        </h2>
        <p className="text-gray-600">
          Please provide detailed information about your maintenance issue
        </p>
      </div>

      {renderStepIndicator()}

      <form onSubmit={handleSubmit}>
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}

        {/* Navigation Buttons */}
        <div className="flex justify-between pt-6 border-t">
          <div>
            {currentStep > 1 && (
              <button
                type="button"
                onClick={() => setCurrentStep(prev => prev - 1)}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Previous
              </button>
            )}
          </div>
          
          <div className="flex space-x-3">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            )}
            
            {currentStep < 3 ? (
              <button
                type="button"
                onClick={() => setCurrentStep(prev => prev + 1)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Next
              </button>
            ) : (
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                {isSubmitting ? (
                  <>
                    <Clock className="w-4 h-4 mr-2 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit Request'
                )}
              </button>
            )}
          </div>
        </div>
      </form>

      {/* Priority Emergency Notice */}
      {formData.priority === 'emergency' && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 mr-3" />
            <div>
              <h4 className="font-semibold text-red-800">Emergency Request Notice</h4>
              <p className="text-sm text-red-700 mt-1">
                For true emergencies requiring immediate response (gas leaks, electrical hazards, flooding), 
                please also call our emergency hotline at <strong>(555) 123-4567</strong>.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
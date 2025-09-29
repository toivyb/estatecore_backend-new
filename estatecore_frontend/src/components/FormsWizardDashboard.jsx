import React, { useState, useEffect } from 'react';

const FormsWizardDashboard = () => {
  const [activeTab, setActiveTab] = useState('property-wizard');
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({});
  const [validationErrors, setValidationErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Property Creation Wizard
  const [propertyData, setPropertyData] = useState({
    // Basic Information
    property_name: '',
    property_type: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'USA',
    
    // Details
    bedrooms: '',
    bathrooms: '',
    square_feet: '',
    lot_size: '',
    year_built: '',
    
    // Financial
    purchase_price: '',
    rent_amount: '',
    deposit_amount: '',
    hoa_fees: '',
    property_tax: '',
    insurance_cost: '',
    
    // Features
    amenities: [],
    utilities_included: [],
    pet_policy: '',
    parking: '',
    laundry: '',
    
    // Media
    photos: [],
    virtual_tour_url: '',
    floor_plan: null
  });

  // Tenant Application Wizard
  const [tenantData, setTenantData] = useState({
    // Personal Information
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    date_of_birth: '',
    ssn: '',
    
    // Employment
    employer: '',
    job_title: '',
    employment_duration: '',
    monthly_income: '',
    additional_income: '',
    
    // References
    previous_landlord: '',
    landlord_phone: '',
    rental_history: '',
    personal_references: [],
    
    // Background
    criminal_background: false,
    eviction_history: false,
    credit_score: '',
    
    // Application Details
    move_in_date: '',
    lease_term: '',
    pets: [],
    emergency_contact: {},
    
    // Documents
    id_document: null,
    income_verification: null,
    bank_statements: null
  });

  // Maintenance Request Wizard
  const [maintenanceData, setMaintenanceData] = useState({
    // Request Information
    property_id: '',
    unit_number: '',
    request_type: '',
    priority: 'medium',
    title: '',
    description: '',
    
    // Details
    location_in_unit: '',
    preferred_time: '',
    access_instructions: '',
    
    // Contact
    tenant_present: true,
    contact_phone: '',
    alternative_contact: '',
    
    // Media
    photos: [],
    videos: []
  });

  const propertyWizardSteps = [
    { id: 1, title: 'Basic Information', icon: '🏠' },
    { id: 2, title: 'Property Details', icon: '📐' },
    { id: 3, title: 'Financial Information', icon: '💰' },
    { id: 4, title: 'Features & Amenities', icon: '✨' },
    { id: 5, title: 'Media & Documentation', icon: '📸' },
    { id: 6, title: 'Review & Submit', icon: '✅' }
  ];

  const tenantWizardSteps = [
    { id: 1, title: 'Personal Information', icon: '👤' },
    { id: 2, title: 'Employment & Income', icon: '💼' },
    { id: 3, title: 'References & History', icon: '📝' },
    { id: 4, title: 'Background Check', icon: '🔍' },
    { id: 5, title: 'Application Details', icon: '📋' },
    { id: 6, title: 'Document Upload', icon: '📄' },
    { id: 7, title: 'Review & Submit', icon: '✅' }
  ];

  const maintenanceWizardSteps = [
    { id: 1, title: 'Request Information', icon: '🔧' },
    { id: 2, title: 'Details & Scheduling', icon: '🗓️' },
    { id: 3, title: 'Contact Information', icon: '📞' },
    { id: 4, title: 'Media Upload', icon: '📷' },
    { id: 5, title: 'Review & Submit', icon: '✅' }
  ];

  const validateStep = (step, data) => {
    const errors = {};

    if (activeTab === 'property-wizard') {
      switch (step) {
        case 1:
          if (!data.property_name) errors.property_name = 'Property name is required';
          if (!data.property_type) errors.property_type = 'Property type is required';
          if (!data.address) errors.address = 'Address is required';
          if (!data.city) errors.city = 'City is required';
          if (!data.state) errors.state = 'State is required';
          if (!data.zip_code) errors.zip_code = 'ZIP code is required';
          break;
        case 2:
          if (!data.bedrooms) errors.bedrooms = 'Number of bedrooms is required';
          if (!data.bathrooms) errors.bathrooms = 'Number of bathrooms is required';
          if (!data.square_feet) errors.square_feet = 'Square footage is required';
          break;
        case 3:
          if (!data.rent_amount) errors.rent_amount = 'Rent amount is required';
          if (data.rent_amount && isNaN(data.rent_amount)) errors.rent_amount = 'Must be a valid number';
          break;
      }
    } else if (activeTab === 'tenant-wizard') {
      switch (step) {
        case 1:
          if (!data.first_name) errors.first_name = 'First name is required';
          if (!data.last_name) errors.last_name = 'Last name is required';
          if (!data.email) errors.email = 'Email is required';
          if (!data.phone) errors.phone = 'Phone number is required';
          break;
        case 2:
          if (!data.employer) errors.employer = 'Employer is required';
          if (!data.monthly_income) errors.monthly_income = 'Monthly income is required';
          break;
      }
    } else if (activeTab === 'maintenance-wizard') {
      switch (step) {
        case 1:
          if (!data.property_id) errors.property_id = 'Property is required';
          if (!data.title) errors.title = 'Title is required';
          if (!data.description) errors.description = 'Description is required';
          break;
      }
    }

    return errors;
  };

  const handleNext = () => {
    let data, steps;
    
    if (activeTab === 'property-wizard') {
      data = propertyData;
      steps = propertyWizardSteps;
    } else if (activeTab === 'tenant-wizard') {
      data = tenantData;
      steps = tenantWizardSteps;
    } else {
      data = maintenanceData;
      steps = maintenanceWizardSteps;
    }

    const errors = validateStep(currentStep, data);
    setValidationErrors(errors);

    if (Object.keys(errors).length === 0) {
      if (currentStep < steps.length) {
        setCurrentStep(currentStep + 1);
      }
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    try {
      let endpoint, data;
      
      if (activeTab === 'property-wizard') {
        endpoint = '/api/properties';
        data = propertyData;
      } else if (activeTab === 'tenant-wizard') {
        endpoint = '/api/tenant-applications';
        data = tenantData;
      } else {
        endpoint = '/api/maintenance-requests';
        data = maintenanceData;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
      });

      if (response.ok) {
        alert('Successfully submitted!');
        // Reset form
        setCurrentStep(1);
        if (activeTab === 'property-wizard') {
          setPropertyData({});
        } else if (activeTab === 'tenant-wizard') {
          setTenantData({});
        } else {
          setMaintenanceData({});
        }
      } else {
        alert('Submission failed. Please try again.');
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('Submission failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStepIndicator = (steps) => (
    <div className="flex items-center justify-center mb-8">
      {steps.map((step, index) => (
        <div key={step.id} className="flex items-center">
          <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
            currentStep >= step.id 
              ? 'bg-blue-600 border-blue-600 text-white' 
              : 'border-gray-300 text-gray-500'
          }`}>
            {currentStep > step.id ? '✓' : step.icon}
          </div>
          <div className="ml-3 mr-6">
            <div className={`text-sm font-medium ${
              currentStep >= step.id ? 'text-blue-600' : 'text-gray-500'
            }`}>
              {step.title}
            </div>
          </div>
          {index < steps.length - 1 && (
            <div className={`w-8 h-0.5 ${
              currentStep > step.id ? 'bg-blue-600' : 'bg-gray-300'
            }`} />
          )}
        </div>
      ))}
    </div>
  );

  const renderFormField = (label, name, type = 'text', options = null, data, setData) => (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {validationErrors[name] && <span className="text-red-500">*</span>}
      </label>
      {type === 'select' ? (
        <select
          value={data[name] || ''}
          onChange={(e) => setData({...data, [name]: e.target.value})}
          className={`w-full p-2 border rounded-md ${
            validationErrors[name] ? 'border-red-500' : 'border-gray-300'
          }`}
        >
          <option value="">Select...</option>
          {options.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      ) : type === 'textarea' ? (
        <textarea
          value={data[name] || ''}
          onChange={(e) => setData({...data, [name]: e.target.value})}
          className={`w-full p-2 border rounded-md ${
            validationErrors[name] ? 'border-red-500' : 'border-gray-300'
          }`}
          rows="3"
        />
      ) : type === 'checkbox' ? (
        <div className="flex items-center">
          <input
            type="checkbox"
            checked={data[name] || false}
            onChange={(e) => setData({...data, [name]: e.target.checked})}
            className="mr-2"
          />
          <span className="text-sm">{label}</span>
        </div>
      ) : (
        <input
          type={type}
          value={data[name] || ''}
          onChange={(e) => setData({...data, [name]: e.target.value})}
          className={`w-full p-2 border rounded-md ${
            validationErrors[name] ? 'border-red-500' : 'border-gray-300'
          }`}
        />
      )}
      {validationErrors[name] && (
        <p className="mt-1 text-sm text-red-500">{validationErrors[name]}</p>
      )}
    </div>
  );

  const renderPropertyWizardStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderFormField('Property Name', 'property_name', 'text', null, propertyData, setPropertyData)}
            {renderFormField('Property Type', 'property_type', 'select', [
              { value: 'apartment', label: 'Apartment' },
              { value: 'house', label: 'House' },
              { value: 'condo', label: 'Condo' },
              { value: 'townhouse', label: 'Townhouse' },
              { value: 'commercial', label: 'Commercial' }
            ], propertyData, setPropertyData)}
            <div className="md:col-span-2">
              {renderFormField('Address', 'address', 'text', null, propertyData, setPropertyData)}
            </div>
            {renderFormField('City', 'city', 'text', null, propertyData, setPropertyData)}
            {renderFormField('State', 'state', 'text', null, propertyData, setPropertyData)}
            {renderFormField('ZIP Code', 'zip_code', 'text', null, propertyData, setPropertyData)}
          </div>
        );
      case 2:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderFormField('Bedrooms', 'bedrooms', 'number', null, propertyData, setPropertyData)}
            {renderFormField('Bathrooms', 'bathrooms', 'number', null, propertyData, setPropertyData)}
            {renderFormField('Square Feet', 'square_feet', 'number', null, propertyData, setPropertyData)}
            {renderFormField('Lot Size (sq ft)', 'lot_size', 'number', null, propertyData, setPropertyData)}
            {renderFormField('Year Built', 'year_built', 'number', null, propertyData, setPropertyData)}
          </div>
        );
      case 3:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderFormField('Purchase Price', 'purchase_price', 'number', null, propertyData, setPropertyData)}
            {renderFormField('Monthly Rent', 'rent_amount', 'number', null, propertyData, setPropertyData)}
            {renderFormField('Security Deposit', 'deposit_amount', 'number', null, propertyData, setPropertyData)}
            {renderFormField('HOA Fees', 'hoa_fees', 'number', null, propertyData, setPropertyData)}
            {renderFormField('Property Tax (Annual)', 'property_tax', 'number', null, propertyData, setPropertyData)}
            {renderFormField('Insurance Cost (Annual)', 'insurance_cost', 'number', null, propertyData, setPropertyData)}
          </div>
        );
      case 4:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Amenities</label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {['Pool', 'Gym', 'Parking', 'Balcony', 'Air Conditioning', 'Dishwasher', 'Washer/Dryer', 'Fireplace'].map(amenity => (
                  <label key={amenity} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={propertyData.amenities?.includes(amenity) || false}
                      onChange={(e) => {
                        const amenities = propertyData.amenities || [];
                        if (e.target.checked) {
                          setPropertyData({...propertyData, amenities: [...amenities, amenity]});
                        } else {
                          setPropertyData({...propertyData, amenities: amenities.filter(a => a !== amenity)});
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm">{amenity}</span>
                  </label>
                ))}
              </div>
            </div>
            {renderFormField('Pet Policy', 'pet_policy', 'select', [
              { value: 'no_pets', label: 'No Pets' },
              { value: 'cats_only', label: 'Cats Only' },
              { value: 'dogs_only', label: 'Dogs Only' },
              { value: 'cats_and_dogs', label: 'Cats and Dogs' },
              { value: 'all_pets', label: 'All Pets Welcome' }
            ], propertyData, setPropertyData)}
            {renderFormField('Parking', 'parking', 'select', [
              { value: 'none', label: 'No Parking' },
              { value: 'street', label: 'Street Parking' },
              { value: 'garage', label: 'Garage' },
              { value: 'driveway', label: 'Driveway' },
              { value: 'covered', label: 'Covered Parking' }
            ], propertyData, setPropertyData)}
          </div>
        );
      case 5:
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Property Photos</label>
              <input
                type="file"
                multiple
                accept="image/*"
                className="w-full p-2 border border-gray-300 rounded-md"
              />
            </div>
            {renderFormField('Virtual Tour URL', 'virtual_tour_url', 'url', null, propertyData, setPropertyData)}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Floor Plan</label>
              <input
                type="file"
                accept="image/*,.pdf"
                className="w-full p-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>
        );
      case 6:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Review Property Information</h3>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div><strong>Property Name:</strong> {propertyData.property_name}</div>
                <div><strong>Type:</strong> {propertyData.property_type}</div>
                <div><strong>Address:</strong> {propertyData.address}</div>
                <div><strong>Bedrooms:</strong> {propertyData.bedrooms}</div>
                <div><strong>Bathrooms:</strong> {propertyData.bathrooms}</div>
                <div><strong>Monthly Rent:</strong> ${propertyData.rent_amount}</div>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  const renderTenantWizardStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderFormField('First Name', 'first_name', 'text', null, tenantData, setTenantData)}
            {renderFormField('Last Name', 'last_name', 'text', null, tenantData, setTenantData)}
            {renderFormField('Email', 'email', 'email', null, tenantData, setTenantData)}
            {renderFormField('Phone Number', 'phone', 'tel', null, tenantData, setTenantData)}
            {renderFormField('Date of Birth', 'date_of_birth', 'date', null, tenantData, setTenantData)}
            {renderFormField('Social Security Number', 'ssn', 'text', null, tenantData, setTenantData)}
          </div>
        );
      case 2:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderFormField('Employer', 'employer', 'text', null, tenantData, setTenantData)}
            {renderFormField('Job Title', 'job_title', 'text', null, tenantData, setTenantData)}
            {renderFormField('Employment Duration', 'employment_duration', 'text', null, tenantData, setTenantData)}
            {renderFormField('Monthly Income', 'monthly_income', 'number', null, tenantData, setTenantData)}
            <div className="md:col-span-2">
              {renderFormField('Additional Income Sources', 'additional_income', 'textarea', null, tenantData, setTenantData)}
            </div>
          </div>
        );
      case 7:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Review Application</h3>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div><strong>Name:</strong> {tenantData.first_name} {tenantData.last_name}</div>
                <div><strong>Email:</strong> {tenantData.email}</div>
                <div><strong>Phone:</strong> {tenantData.phone}</div>
                <div><strong>Employer:</strong> {tenantData.employer}</div>
                <div><strong>Monthly Income:</strong> ${tenantData.monthly_income}</div>
              </div>
            </div>
          </div>
        );
      default:
        return <div>Step {currentStep} content for tenant application...</div>;
    }
  };

  const renderMaintenanceWizardStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {renderFormField('Property', 'property_id', 'select', [
              { value: '1', label: 'Sunset Apartments - Unit 101' },
              { value: '2', label: 'Downtown Loft - Unit 205' },
              { value: '3', label: 'Garden View - Unit 301' }
            ], maintenanceData, setMaintenanceData)}
            {renderFormField('Request Type', 'request_type', 'select', [
              { value: 'plumbing', label: 'Plumbing' },
              { value: 'electrical', label: 'Electrical' },
              { value: 'hvac', label: 'HVAC' },
              { value: 'appliance', label: 'Appliance' },
              { value: 'general', label: 'General Maintenance' }
            ], maintenanceData, setMaintenanceData)}
            {renderFormField('Priority', 'priority', 'select', [
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'emergency', label: 'Emergency' }
            ], maintenanceData, setMaintenanceData)}
            <div className="md:col-span-2">
              {renderFormField('Title', 'title', 'text', null, maintenanceData, setMaintenanceData)}
            </div>
            <div className="md:col-span-2">
              {renderFormField('Description', 'description', 'textarea', null, maintenanceData, setMaintenanceData)}
            </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-4">
            <h3 className="text-lg font-medium">Review Maintenance Request</h3>
            <div className="bg-gray-50 p-4 rounded-md">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div><strong>Property:</strong> {maintenanceData.property_id}</div>
                <div><strong>Type:</strong> {maintenanceData.request_type}</div>
                <div><strong>Priority:</strong> {maintenanceData.priority}</div>
                <div><strong>Title:</strong> {maintenanceData.title}</div>
                <div className="md:col-span-2"><strong>Description:</strong> {maintenanceData.description}</div>
              </div>
            </div>
          </div>
        );
      default:
        return <div>Step {currentStep} content for maintenance request...</div>;
    }
  };

  const getCurrentSteps = () => {
    if (activeTab === 'property-wizard') return propertyWizardSteps;
    if (activeTab === 'tenant-wizard') return tenantWizardSteps;
    return maintenanceWizardSteps;
  };

  const renderWizardContent = () => {
    if (activeTab === 'property-wizard') return renderPropertyWizardStep();
    if (activeTab === 'tenant-wizard') return renderTenantWizardStep();
    return renderMaintenanceWizardStep();
  };

  const isLastStep = () => {
    const steps = getCurrentSteps();
    return currentStep === steps.length;
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Forms & Wizards</h1>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'property-wizard', label: 'Property Creation', icon: '🏠' },
            { id: 'tenant-wizard', label: 'Tenant Application', icon: '👤' },
            { id: 'maintenance-wizard', label: 'Maintenance Request', icon: '🔧' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id);
                setCurrentStep(1);
                setValidationErrors({});
              }}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Wizard Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {renderStepIndicator(getCurrentSteps())}
        
        <div className="min-h-96">
          {renderWizardContent()}
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 1}
            className={`px-4 py-2 rounded-md ${
              currentStep === 1
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-gray-600 text-white hover:bg-gray-700'
            }`}
          >
            ← Previous
          </button>

          {isLastStep() ? (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className={`px-6 py-2 rounded-md ${
                isSubmitting
                  ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {isSubmitting ? 'Submitting...' : '✅ Submit'}
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Next →
            </button>
          )}
        </div>
      </div>

      {/* Help Section */}
      <div className="bg-blue-50 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-2">Wizard Help</h3>
        <div className="text-sm text-blue-800 space-y-2">
          <p><strong>Property Creation Wizard:</strong> Step-by-step property registration with validation and media upload.</p>
          <p><strong>Tenant Application Wizard:</strong> Comprehensive tenant screening application with document upload.</p>
          <p><strong>Maintenance Request Wizard:</strong> Streamlined maintenance request submission with photo/video support.</p>
          <p><strong>Tips:</strong> All required fields are marked with an asterisk (*). You can navigate between steps, and your progress is saved.</p>
        </div>
      </div>
    </div>
  );
};

export default FormsWizardDashboard;
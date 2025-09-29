/**
 * Mobile Property Inspection Workflow
 * Complete inspection process optimized for mobile devices
 */

import React, { useState, useEffect, useRef } from 'react';
import useNativeFeatures from '../hooks/useNativeFeatures';
import offlineStorage from '../services/OfflineStorageService';

const MobileInspectionWorkflow = ({ propertyId, onComplete, onCancel }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [inspection, setInspection] = useState({
    id: `inspection_${Date.now()}`,
    propertyId,
    date: new Date().toISOString(),
    inspector: 'current_user',
    type: 'routine',
    status: 'in_progress',
    sections: [],
    photos: [],
    notes: '',
    checklist: [],
    geolocation: null,
    weather: null,
    duration: 0
  });
  
  const [activeSection, setActiveSection] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [startTime] = useState(Date.now());
  const audioRef = useRef(null);
  
  const {
    capturePhoto,
    getCurrentLocation,
    requestLocationPermission,
    requestCameraPermission,
    vibrate,
    showNotification
  } = useNativeFeatures();

  // Inspection sections and checklist
  const inspectionSections = [
    {
      id: 'exterior',
      title: 'Exterior Inspection',
      icon: '🏠',
      items: [
        { id: 'roof', label: 'Roof Condition', type: 'rating', required: true },
        { id: 'siding', label: 'Siding/Exterior Walls', type: 'rating', required: true },
        { id: 'windows', label: 'Windows & Doors', type: 'rating', required: true },
        { id: 'gutters', label: 'Gutters & Downspouts', type: 'rating', required: false },
        { id: 'landscaping', label: 'Landscaping', type: 'rating', required: false },
        { id: 'driveway', label: 'Driveway/Walkways', type: 'rating', required: false },
        { id: 'exterior_lighting', label: 'Exterior Lighting', type: 'check', required: false }
      ]
    },
    {
      id: 'interior',
      title: 'Interior Inspection',
      icon: '🏡',
      items: [
        { id: 'flooring', label: 'Flooring Condition', type: 'rating', required: true },
        { id: 'walls_ceiling', label: 'Walls & Ceilings', type: 'rating', required: true },
        { id: 'lighting', label: 'Interior Lighting', type: 'check', required: true },
        { id: 'outlets', label: 'Electrical Outlets', type: 'check', required: true },
        { id: 'doors_trim', label: 'Doors & Trim', type: 'rating', required: false },
        { id: 'stairs', label: 'Stairs & Railings', type: 'rating', required: false }
      ]
    },
    {
      id: 'kitchen',
      title: 'Kitchen',
      icon: '🍳',
      items: [
        { id: 'appliances', label: 'Appliances', type: 'rating', required: true },
        { id: 'cabinets', label: 'Cabinets & Countertops', type: 'rating', required: true },
        { id: 'plumbing', label: 'Plumbing Fixtures', type: 'rating', required: true },
        { id: 'ventilation', label: 'Ventilation', type: 'check', required: false }
      ]
    },
    {
      id: 'bathrooms',
      title: 'Bathrooms',
      icon: '🛁',
      items: [
        { id: 'fixtures', label: 'Plumbing Fixtures', type: 'rating', required: true },
        { id: 'tiles', label: 'Tiles & Grout', type: 'rating', required: true },
        { id: 'ventilation', label: 'Ventilation Fan', type: 'check', required: true },
        { id: 'water_pressure', label: 'Water Pressure', type: 'rating', required: false }
      ]
    },
    {
      id: 'systems',
      title: 'Mechanical Systems',
      icon: '⚙️',
      items: [
        { id: 'hvac', label: 'HVAC System', type: 'rating', required: true },
        { id: 'electrical', label: 'Electrical Panel', type: 'rating', required: true },
        { id: 'water_heater', label: 'Water Heater', type: 'rating', required: true },
        { id: 'smoke_detectors', label: 'Smoke Detectors', type: 'check', required: true },
        { id: 'carbon_monoxide', label: 'CO Detectors', type: 'check', required: true }
      ]
    },
    {
      id: 'safety',
      title: 'Safety & Security',
      icon: '🔒',
      items: [
        { id: 'locks', label: 'Door Locks', type: 'check', required: true },
        { id: 'security_system', label: 'Security System', type: 'check', required: false },
        { id: 'emergency_exits', label: 'Emergency Exits', type: 'check', required: true },
        { id: 'fire_extinguisher', label: 'Fire Extinguisher', type: 'check', required: false }
      ]
    }
  ];

  useEffect(() => {
    initializeInspection();
  }, []);

  const initializeInspection = async () => {
    try {
      // Request permissions
      await requestLocationPermission();
      await requestCameraPermission();
      
      // Get current location
      try {
        const location = await getCurrentLocation();
        setInspection(prev => ({
          ...prev,
          geolocation: location
        }));
      } catch (error) {
        console.warn('Could not get location:', error);
      }
      
      // Initialize checklist
      const checklist = inspectionSections.flatMap(section =>
        section.items.map(item => ({
          sectionId: section.id,
          itemId: item.id,
          label: item.label,
          type: item.type,
          required: item.required,
          completed: false,
          value: null,
          notes: '',
          photos: []
        }))
      );
      
      setInspection(prev => ({
        ...prev,
        checklist
      }));
      
    } catch (error) {
      console.error('Initialization error:', error);
    }
  };

  const updateChecklistItem = (sectionId, itemId, updates) => {
    setInspection(prev => ({
      ...prev,
      checklist: prev.checklist.map(item =>
        item.sectionId === sectionId && item.itemId === itemId
          ? { ...item, ...updates, completed: updates.value !== null }
          : item
      )
    }));
    
    vibrate(25); // Subtle feedback
  };

  const takePhoto = async (sectionId, itemId = null) => {
    try {
      const photo = await capturePhoto({
        quality: 0.8,
        width: 1920,
        height: 1080
      });
      
      const photoData = {
        id: `photo_${Date.now()}`,
        sectionId,
        itemId,
        file: photo.file,
        dataUrl: photo.dataUrl,
        timestamp: new Date().toISOString(),
        location: inspection.geolocation
      };
      
      // Save photo to offline storage
      await offlineStorage.saveAttachment({
        id: photoData.id,
        entityType: 'inspection',
        entityId: inspection.id,
        file: photo.file,
        metadata: {
          sectionId,
          itemId,
          timestamp: photoData.timestamp
        }
      });
      
      // Add to inspection
      setInspection(prev => ({
        ...prev,
        photos: [...prev.photos, photoData]
      }));
      
      // Update checklist item if associated
      if (itemId) {
        updateChecklistItem(sectionId, itemId, {
          photos: [...(getChecklistItem(sectionId, itemId)?.photos || []), photoData.id]
        });
      }
      
      vibrate([50, 25, 50]); // Camera feedback
      showNotification('Photo captured', { 
        body: 'Photo added to inspection',
        tag: 'inspection-photo'
      });
      
    } catch (error) {
      console.error('Photo capture error:', error);
      alert('Failed to capture photo. Please try again.');
    }
  };

  const getChecklistItem = (sectionId, itemId) => {
    return inspection.checklist.find(item => 
      item.sectionId === sectionId && item.itemId === itemId
    );
  };

  const getSectionProgress = (sectionId) => {
    const sectionItems = inspection.checklist.filter(item => item.sectionId === sectionId);
    const completedItems = sectionItems.filter(item => item.completed);
    return sectionItems.length > 0 ? (completedItems.length / sectionItems.length) * 100 : 0;
  };

  const getOverallProgress = () => {
    const totalItems = inspection.checklist.length;
    const completedItems = inspection.checklist.filter(item => item.completed).length;
    return totalItems > 0 ? (completedItems / totalItems) * 100 : 0;
  };

  const canCompleteInspection = () => {
    const requiredItems = inspection.checklist.filter(item => item.required);
    return requiredItems.every(item => item.completed);
  };

  const saveInspection = async () => {
    try {
      const duration = Math.round((Date.now() - startTime) / 1000 / 60); // minutes
      
      const finalInspection = {
        ...inspection,
        duration,
        completedAt: new Date().toISOString(),
        status: 'completed'
      };
      
      // Save to offline storage
      await offlineStorage.saveInspection(finalInspection);
      
      showNotification('Inspection saved', {
        body: 'Inspection completed and saved locally',
        tag: 'inspection-complete'
      });
      
      onComplete(finalInspection);
    } catch (error) {
      console.error('Save error:', error);
      alert('Failed to save inspection. Please try again.');
    }
  };

  const renderRatingInput = (sectionId, itemId, currentValue) => {
    const ratings = [
      { value: 5, label: 'Excellent', color: 'text-green-600' },
      { value: 4, label: 'Good', color: 'text-blue-600' },
      { value: 3, label: 'Fair', color: 'text-yellow-600' },
      { value: 2, label: 'Poor', color: 'text-orange-600' },
      { value: 1, label: 'Critical', color: 'text-red-600' }
    ];
    
    return (
      <div className="grid grid-cols-5 gap-2 mt-2">
        {ratings.map(rating => (
          <button
            key={rating.value}
            onClick={() => updateChecklistItem(sectionId, itemId, { value: rating.value })}
            className={`p-3 rounded-lg border-2 transition-all ${
              currentValue === rating.value
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className={`text-2xl ${rating.color}`}>
              {'★'.repeat(rating.value)}
            </div>
            <div className="text-xs text-gray-600 mt-1">{rating.label}</div>
          </button>
        ))}
      </div>
    );
  };

  const renderCheckInput = (sectionId, itemId, currentValue) => {
    const options = [
      { value: true, label: 'Pass', icon: '✓', color: 'text-green-600 bg-green-50 border-green-200' },
      { value: false, label: 'Fail', icon: '✗', color: 'text-red-600 bg-red-50 border-red-200' }
    ];
    
    return (
      <div className="grid grid-cols-2 gap-3 mt-2">
        {options.map(option => (
          <button
            key={option.value.toString()}
            onClick={() => updateChecklistItem(sectionId, itemId, { value: option.value })}
            className={`p-4 rounded-lg border-2 transition-all ${
              currentValue === option.value
                ? option.color
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="text-2xl">{option.icon}</div>
            <div className="text-sm font-medium mt-1">{option.label}</div>
          </button>
        ))}
      </div>
    );
  };

  const renderSectionOverview = () => (
    <div className="space-y-4">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Property Inspection</h2>
        <div className="bg-gray-200 rounded-full h-3 mb-2">
          <div 
            className="bg-blue-600 h-3 rounded-full transition-all duration-300"
            style={{ width: `${getOverallProgress()}%` }}
          />
        </div>
        <p className="text-sm text-gray-600">
          {Math.round(getOverallProgress())}% Complete
        </p>
      </div>

      {inspectionSections.map((section, index) => (
        <button
          key={section.id}
          onClick={() => {
            setActiveSection(section.id);
            setCurrentStep(1);
          }}
          className="w-full p-4 bg-white rounded-lg shadow-sm border border-gray-200 hover:border-blue-300 transition-colors"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-2xl mr-3">{section.icon}</span>
              <div className="text-left">
                <h3 className="font-medium text-gray-900">{section.title}</h3>
                <p className="text-sm text-gray-500">
                  {getSectionProgress(section.id).toFixed(0)}% complete
                </p>
              </div>
            </div>
            <div className="flex items-center">
              <div className="w-8 h-8 bg-gray-200 rounded-full mr-2">
                <div 
                  className="bg-blue-600 rounded-full h-full transition-all duration-300"
                  style={{ width: `${getSectionProgress(section.id)}%` }}
                />
              </div>
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </button>
      ))}

      <div className="flex space-x-3 mt-6">
        <button
          onClick={onCancel}
          className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          onClick={() => setCurrentStep(2)}
          disabled={!canCompleteInspection()}
          className={`flex-1 py-3 px-4 rounded-lg font-medium ${
            canCompleteInspection()
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Review & Complete
        </button>
      </div>
    </div>
  );

  const renderSectionDetail = () => {
    const section = inspectionSections.find(s => s.id === activeSection);
    if (!section) return null;

    return (
      <div className="space-y-6">
        <div className="flex items-center mb-6">
          <button
            onClick={() => {
              setActiveSection(null);
              setCurrentStep(0);
            }}
            className="mr-3 p-2 text-gray-600 hover:text-gray-800"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h2 className="text-xl font-bold text-gray-900">{section.title}</h2>
            <p className="text-sm text-gray-600">
              {getSectionProgress(section.id).toFixed(0)}% complete
            </p>
          </div>
        </div>

        <div className="mb-4">
          <button
            onClick={() => takePhoto(section.id)}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89L8.5 4.5A2 2 0 0110.164 3.5h3.672A2 2 0 0115.5 4.5l.906 1.61A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Take Section Photo
          </button>
        </div>

        {section.items.map(item => {
          const checklistItem = getChecklistItem(section.id, item.id);
          
          return (
            <div key={item.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  <h3 className="font-medium text-gray-900">{item.label}</h3>
                  {item.required && (
                    <span className="ml-2 text-xs text-red-600">Required</span>
                  )}
                </div>
                <button
                  onClick={() => takePhoto(section.id, item.id)}
                  className="p-2 text-gray-400 hover:text-blue-600"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89L8.5 4.5A2 2 0 0110.164 3.5h3.672A2 2 0 0115.5 4.5l.906 1.61A2 2 0 0118.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
              </div>

              {item.type === 'rating' && renderRatingInput(section.id, item.id, checklistItem?.value)}
              {item.type === 'check' && renderCheckInput(section.id, item.id, checklistItem?.value)}

              <textarea
                placeholder="Add notes..."
                value={checklistItem?.notes || ''}
                onChange={(e) => updateChecklistItem(section.id, item.id, { notes: e.target.value })}
                className="w-full mt-3 p-2 border border-gray-200 rounded text-sm resize-none"
                rows={2}
              />

              {checklistItem?.photos?.length > 0 && (
                <div className="mt-2 text-xs text-gray-500">
                  📸 {checklistItem.photos.length} photo(s) attached
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderReviewSummary = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Inspection Complete</h2>
        <p className="text-gray-600">Review your inspection before saving</p>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <div className="flex items-center">
          <svg className="w-6 h-6 text-green-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 className="font-medium text-green-900">
              {Math.round(getOverallProgress())}% Complete
            </h3>
            <p className="text-sm text-green-700">
              {inspection.checklist.filter(item => item.completed).length} of {inspection.checklist.length} items checked
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <h3 className="font-medium text-gray-900">Inspection Summary</h3>
        {inspectionSections.map(section => (
          <div key={section.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
            <span className="font-medium">{section.title}</span>
            <span className="text-sm text-gray-600">
              {getSectionProgress(section.id).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Overall Notes
        </label>
        <textarea
          value={inspection.notes}
          onChange={(e) => setInspection(prev => ({ ...prev, notes: e.target.value }))}
          placeholder="Add overall inspection notes..."
          className="w-full p-3 border border-gray-300 rounded-lg resize-none"
          rows={4}
        />
      </div>

      <div className="flex space-x-3">
        <button
          onClick={() => setCurrentStep(0)}
          className="flex-1 py-3 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Back to Overview
        </button>
        <button
          onClick={saveInspection}
          className="flex-1 py-3 px-4 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium"
        >
          Save Inspection
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="px-4 py-3">
          <div className="flex items-center justify-between">
            <h1 className="text-lg font-semibold text-gray-900">
              Property Inspection
            </h1>
            <button
              onClick={onCancel}
              className="text-gray-600 hover:text-gray-800"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div className="p-4">
        {currentStep === 0 && renderSectionOverview()}
        {currentStep === 1 && renderSectionDetail()}
        {currentStep === 2 && renderReviewSummary()}
      </div>
    </div>
  );
};

export default MobileInspectionWorkflow;
/**
 * Mobile-Optimized Property Card Component
 * Touch-friendly interface with swipe gestures and quick actions
 */

import React, { useState, useRef } from 'react';
import { useSwipeable } from 'react-swipeable';
import useNativeFeatures from '../hooks/useNativeFeatures';
import offlineStorage from '../services/OfflineStorageService';

const MobilePropertyCard = ({ 
  property, 
  onEdit, 
  onDelete, 
  onInspect, 
  onViewDetails,
  onQuickAction 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [swipeOffset, setSwipeOffset] = useState(0);
  const [showActions, setShowActions] = useState(false);
  const cardRef = useRef(null);
  
  const { shareContent, vibrate, getCurrentLocation } = useNativeFeatures();

  // Swipe handlers
  const swipeHandlers = useSwipeable({
    onSwipedLeft: () => {
      setShowActions(true);
      vibrate(50);
    },
    onSwipedRight: () => {
      setShowActions(false);
    },
    onSwiping: (eventData) => {
      if (eventData.dir === 'Left') {
        setSwipeOffset(Math.min(-eventData.deltaX, 100));
      } else if (eventData.dir === 'Right' && showActions) {
        setSwipeOffset(Math.max(-100 + eventData.deltaX, 0));
      }
    },
    onSwiped: () => {
      setSwipeOffset(0);
    },
    trackMouse: false,
    trackTouch: true
  });

  const handleQuickShare = async () => {
    try {
      await shareContent({
        title: property.title,
        text: `Check out this property: ${property.address}`,
        url: `${window.location.origin}/properties/${property.id}`
      });
    } catch (error) {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(`${property.title} - ${property.address}`);
    }
  };

  const handleQuickCall = () => {
    if (property.contact?.phone) {
      window.location.href = `tel:${property.contact.phone}`;
    }
  };

  const handleQuickNavigate = async () => {
    try {
      const location = await getCurrentLocation();
      const destination = `${property.address}, ${property.city}, ${property.state}`;
      
      // Open in default maps app
      if (navigator.platform.indexOf('iPhone') !== -1) {
        window.open(`maps://maps.apple.com/?daddr=${encodeURIComponent(destination)}`);
      } else {
        window.open(`https://maps.google.com/?daddr=${encodeURIComponent(destination)}`);
      }
    } catch (error) {
      // Fallback: open in web maps
      const destination = `${property.address}, ${property.city}, ${property.state}`;
      window.open(`https://maps.google.com/?daddr=${encodeURIComponent(destination)}`);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      available: 'bg-green-100 text-green-800',
      occupied: 'bg-blue-100 text-blue-800',
      maintenance: 'bg-yellow-100 text-yellow-800',
      vacant: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'text-red-600',
      medium: 'text-yellow-600',
      low: 'text-green-600'
    };
    return colors[priority] || 'text-gray-600';
  };

  return (
    <div 
      ref={cardRef}
      className="relative bg-white rounded-lg shadow-md overflow-hidden transform transition-transform duration-200 active:scale-98"
      style={{ transform: `translateX(${swipeOffset}px)` }}
      {...swipeHandlers}
    >
      {/* Main Card Content */}
      <div className="relative">
        {/* Property Image */}
        <div className="relative h-48 bg-gray-200 overflow-hidden">
          {property.images && property.images.length > 0 ? (
            <img
              src={property.images[0]}
              alt={property.title}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100">
              <svg className="w-12 h-12 text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 7h10M7 10h10M7 13h10" />
              </svg>
            </div>
          )}
          
          {/* Status Badge */}
          <div className="absolute top-3 right-3">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(property.status)}`}>
              {property.status?.charAt(0).toUpperCase() + property.status?.slice(1)}
            </span>
          </div>

          {/* Priority Indicator */}
          {property.priority && (
            <div className="absolute top-3 left-3">
              <div className={`w-3 h-3 rounded-full ${getPriorityColor(property.priority)}`}>
                <div className="w-full h-full rounded-full animate-pulse"></div>
              </div>
            </div>
          )}

          {/* Offline Indicator */}
          {property.needsSync && (
            <div className="absolute bottom-3 right-3">
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-800">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Sync
              </span>
            </div>
          )}
        </div>

        {/* Card Content */}
        <div className="p-4">
          {/* Title and Address */}
          <div className="mb-3">
            <h3 
              className="text-lg font-semibold text-gray-900 line-clamp-1 cursor-pointer"
              onClick={() => setIsExpanded(!isExpanded)}
            >
              {property.title || `${property.address}`}
            </h3>
            <p className="text-sm text-gray-600 line-clamp-1 mt-1">
              {property.address}, {property.city}, {property.state}
            </p>
          </div>

          {/* Quick Stats */}
          <div className="flex items-center space-x-4 mb-3">
            {property.bedrooms && (
              <div className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
                </svg>
                {property.bedrooms} bed
              </div>
            )}
            {property.bathrooms && (
              <div className="flex items-center text-sm text-gray-600">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 14v3m4-3v3m4-3v3M3 21h18M3 10h18M3 7l9-4 9 4M4 10h16v11H4V10z" />
                </svg>
                {property.bathrooms} bath
              </div>
            )}
            {property.rent && (
              <div className="flex items-center text-sm font-medium text-green-600">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
                ${property.rent}/mo
              </div>
            )}
          </div>

          {/* Expandable Details */}
          {isExpanded && (
            <div className="mt-4 space-y-3 border-t pt-3">
              {property.description && (
                <p className="text-sm text-gray-700">{property.description}</p>
              )}
              
              {property.amenities && property.amenities.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Amenities</h4>
                  <div className="flex flex-wrap gap-1">
                    {property.amenities.slice(0, 3).map((amenity, index) => (
                      <span
                        key={index}
                        className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                      >
                        {amenity}
                      </span>
                    ))}
                    {property.amenities.length > 3 && (
                      <span className="px-2 py-1 bg-gray-50 text-gray-700 text-xs rounded-full">
                        +{property.amenities.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              )}

              {property.lastInspection && (
                <div className="text-xs text-gray-500">
                  Last inspected: {new Date(property.lastInspection).toLocaleDateString()}
                </div>
              )}
            </div>
          )}

          {/* Quick Action Buttons */}
          <div className="flex items-center justify-between mt-4">
            <div className="flex space-x-2">
              <button
                onClick={() => onViewDetails(property)}
                className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 active:bg-blue-800 transition-colors"
              >
                Details
              </button>
              
              <button
                onClick={() => onInspect(property)}
                className="flex-1 px-3 py-2 bg-green-600 text-white text-sm rounded-md hover:bg-green-700 active:bg-green-800 transition-colors"
              >
                Inspect
              </button>
            </div>

            {/* More Actions Button */}
            <button
              onClick={() => setShowActions(!showActions)}
              className="ml-2 p-2 text-gray-400 hover:text-gray-600 active:text-gray-800 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Swipe Actions Overlay */}
      {showActions && (
        <div className="absolute inset-y-0 right-0 w-24 bg-gray-100 flex flex-col justify-center">
          <button
            onClick={handleQuickShare}
            className="flex-1 flex flex-col items-center justify-center text-blue-600 hover:bg-blue-50 active:bg-blue-100 transition-colors"
          >
            <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.367 2.684 3 3 0 00-5.367-2.684z" />
            </svg>
            <span className="text-xs">Share</span>
          </button>

          <button
            onClick={handleQuickCall}
            className="flex-1 flex flex-col items-center justify-center text-green-600 hover:bg-green-50 active:bg-green-100 transition-colors"
          >
            <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
            <span className="text-xs">Call</span>
          </button>

          <button
            onClick={handleQuickNavigate}
            className="flex-1 flex flex-col items-center justify-center text-purple-600 hover:bg-purple-50 active:bg-purple-100 transition-colors"
          >
            <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-xs">Navigate</span>
          </button>

          <button
            onClick={() => onEdit(property)}
            className="flex-1 flex flex-col items-center justify-center text-orange-600 hover:bg-orange-50 active:bg-orange-100 transition-colors"
          >
            <svg className="w-6 h-6 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            <span className="text-xs">Edit</span>
          </button>
        </div>
      )}

      {/* Touch Ripple Effect */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="relative w-full h-full overflow-hidden rounded-lg">
          {/* Ripple animation would go here */}
        </div>
      </div>
    </div>
  );
};

export default MobilePropertyCard;
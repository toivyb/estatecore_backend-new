/**
 * Custom React Hook for Native Device Integration
 * Camera, GPS, Push Notifications, and Device Capabilities
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export const useNativeFeatures = () => {
  const [permissions, setPermissions] = useState({
    camera: 'prompt',
    geolocation: 'prompt',
    notifications: 'default'
  });
  
  const [capabilities, setCapabilities] = useState({
    camera: false,
    geolocation: false,
    notifications: false,
    installPrompt: false,
    share: false,
    vibration: false
  });
  
  const [deviceInfo, setDeviceInfo] = useState({
    isOnline: navigator.onLine,
    isStandalone: false,
    isMobile: false,
    platform: 'unknown'
  });
  
  const deferredPromptRef = useRef(null);

  // Initialize capabilities and permissions
  useEffect(() => {
    checkCapabilities();
    checkPermissions();
    detectDeviceInfo();
    
    // Listen for install prompt
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      deferredPromptRef.current = e;
      setCapabilities(prev => ({ ...prev, installPrompt: true }));
    };
    
    // Listen for online/offline events
    const handleOnline = () => setDeviceInfo(prev => ({ ...prev, isOnline: true }));
    const handleOffline = () => setDeviceInfo(prev => ({ ...prev, isOnline: false }));
    
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const checkCapabilities = () => {
    setCapabilities({
      camera: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      geolocation: !!navigator.geolocation,
      notifications: 'Notification' in window,
      installPrompt: true, // Will be updated when event fires
      share: !!(navigator.share),
      vibration: !!navigator.vibrate,
      fileSystem: 'showOpenFilePicker' in window,
      webRTC: !!(window.RTCPeerConnection || window.webkitRTCPeerConnection),
      deviceMotion: 'DeviceMotionEvent' in window,
      deviceOrientation: 'DeviceOrientationEvent' in window,
      battery: 'getBattery' in navigator,
      wakelock: 'wakeLock' in navigator
    });
  };

  const checkPermissions = async () => {
    try {
      if ('permissions' in navigator) {
        const cameraResult = await navigator.permissions.query({ name: 'camera' });
        const geoResult = await navigator.permissions.query({ name: 'geolocation' });
        
        setPermissions({
          camera: cameraResult.state,
          geolocation: geoResult.state,
          notifications: Notification.permission
        });
      }
    } catch (error) {
      console.warn('Permission API not fully supported:', error);
    }
  };

  const detectDeviceInfo = () => {
    const userAgent = navigator.userAgent.toLowerCase();
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                        window.navigator.standalone ||
                        document.referrer.includes('android-app://');
    
    setDeviceInfo({
      isOnline: navigator.onLine,
      isStandalone,
      isMobile: /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent),
      platform: getPlatform(userAgent),
      touchScreen: 'ontouchstart' in window,
      screenSize: {
        width: window.screen.width,
        height: window.screen.height
      }
    });
  };

  const getPlatform = (userAgent) => {
    if (userAgent.includes('android')) return 'android';
    if (userAgent.includes('iphone') || userAgent.includes('ipad')) return 'ios';
    if (userAgent.includes('windows')) return 'windows';
    if (userAgent.includes('mac')) return 'mac';
    if (userAgent.includes('linux')) return 'linux';
    return 'unknown';
  };

  // Camera Functions
  const requestCameraPermission = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } 
      });
      stream.getTracks().forEach(track => track.stop()); // Stop immediately
      setPermissions(prev => ({ ...prev, camera: 'granted' }));
      return true;
    } catch (error) {
      console.error('Camera permission denied:', error);
      setPermissions(prev => ({ ...prev, camera: 'denied' }));
      return false;
    }
  }, []);

  const capturePhoto = useCallback(async (options = {}) => {
    const {
      width = 1920,
      height = 1080,
      facingMode = 'environment', // 'user' for front camera
      quality = 0.8
    } = options;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          width: { ideal: width },
          height: { ideal: height },
          facingMode 
        }
      });

      const video = document.createElement('video');
      video.srcObject = stream;
      video.play();

      return new Promise((resolve, reject) => {
        video.onloadedmetadata = () => {
          const canvas = document.createElement('canvas');
          const context = canvas.getContext('2d');
          
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          
          context.drawImage(video, 0, 0);
          
          canvas.toBlob((blob) => {
            stream.getTracks().forEach(track => track.stop());
            
            if (blob) {
              const file = new File([blob], `photo_${Date.now()}.jpg`, { 
                type: 'image/jpeg' 
              });
              resolve({
                file,
                blob,
                dataUrl: canvas.toDataURL('image/jpeg', quality),
                width: canvas.width,
                height: canvas.height
              });
            } else {
              reject(new Error('Failed to capture photo'));
            }
          }, 'image/jpeg', quality);
        };
      });
    } catch (error) {
      console.error('Error capturing photo:', error);
      throw error;
    }
  }, []);

  // Geolocation Functions
  const requestLocationPermission = useCallback(async () => {
    try {
      await new Promise((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });
      setPermissions(prev => ({ ...prev, geolocation: 'granted' }));
      return true;
    } catch (error) {
      console.error('Location permission denied:', error);
      setPermissions(prev => ({ ...prev, geolocation: 'denied' }));
      return false;
    }
  }, []);

  const getCurrentLocation = useCallback(async (options = {}) => {
    const {
      enableHighAccuracy = true,
      timeout = 10000,
      maximumAge = 300000 // 5 minutes
    } = options;

    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('Geolocation not supported'));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude,
            altitudeAccuracy: position.coords.altitudeAccuracy,
            heading: position.coords.heading,
            speed: position.coords.speed,
            timestamp: position.timestamp
          });
        },
        (error) => {
          reject(new Error(`Geolocation error: ${error.message}`));
        },
        { enableHighAccuracy, timeout, maximumAge }
      );
    });
  }, []);

  const watchLocation = useCallback((callback, options = {}) => {
    if (!navigator.geolocation) {
      throw new Error('Geolocation not supported');
    }

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        callback({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          timestamp: position.timestamp
        });
      },
      (error) => {
        callback({ error: error.message });
      },
      options
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  // Push Notifications
  const requestNotificationPermission = useCallback(async () => {
    try {
      if (!('Notification' in window)) {
        throw new Error('Notifications not supported');
      }

      const permission = await Notification.requestPermission();
      setPermissions(prev => ({ ...prev, notifications: permission }));
      
      return permission === 'granted';
    } catch (error) {
      console.error('Notification permission error:', error);
      return false;
    }
  }, []);

  const showNotification = useCallback(async (title, options = {}) => {
    try {
      if (Notification.permission !== 'granted') {
        throw new Error('Notification permission not granted');
      }

      const notification = new Notification(title, {
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        ...options
      });

      return notification;
    } catch (error) {
      console.error('Error showing notification:', error);
      throw error;
    }
  }, []);

  const subscribeToPushNotifications = useCallback(async () => {
    try {
      if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        throw new Error('Push notifications not supported');
      }

      const registration = await navigator.serviceWorker.ready;
      
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: process.env.REACT_APP_VAPID_PUBLIC_KEY
      });

      // Send subscription to server
      const response = await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subscription)
      });

      if (!response.ok) {
        throw new Error('Failed to register push subscription');
      }

      return subscription;
    } catch (error) {
      console.error('Push subscription error:', error);
      throw error;
    }
  }, []);

  // Device Features
  const vibrate = useCallback((pattern = 200) => {
    if (navigator.vibrate) {
      navigator.vibrate(pattern);
      return true;
    }
    return false;
  }, []);

  const shareContent = useCallback(async (data) => {
    try {
      if (navigator.share) {
        await navigator.share(data);
        return true;
      } else {
        // Fallback to Web Share Target API or custom sharing
        throw new Error('Web Share API not supported');
      }
    } catch (error) {
      console.error('Share error:', error);
      return false;
    }
  }, []);

  const installPWA = useCallback(async () => {
    try {
      if (!deferredPromptRef.current) {
        throw new Error('Install prompt not available');
      }

      const choiceResult = await deferredPromptRef.current.prompt();
      console.log('User choice:', choiceResult.outcome);
      
      deferredPromptRef.current = null;
      setCapabilities(prev => ({ ...prev, installPrompt: false }));
      
      return choiceResult.outcome === 'accepted';
    } catch (error) {
      console.error('Install error:', error);
      return false;
    }
  }, []);

  const getBatteryInfo = useCallback(async () => {
    try {
      if ('getBattery' in navigator) {
        const battery = await navigator.getBattery();
        return {
          level: Math.round(battery.level * 100),
          charging: battery.charging,
          chargingTime: battery.chargingTime,
          dischargingTime: battery.dischargingTime
        };
      }
      throw new Error('Battery API not supported');
    } catch (error) {
      console.error('Battery info error:', error);
      return null;
    }
  }, []);

  const requestWakeLock = useCallback(async () => {
    try {
      if ('wakeLock' in navigator) {
        const wakeLock = await navigator.wakeLock.request('screen');
        return wakeLock;
      }
      throw new Error('Wake Lock API not supported');
    } catch (error) {
      console.error('Wake lock error:', error);
      return null;
    }
  }, []);

  // File System Access
  const openFilePicker = useCallback(async (options = {}) => {
    try {
      if ('showOpenFilePicker' in window) {
        const fileHandles = await window.showOpenFilePicker({
          multiple: options.multiple || false,
          accept: options.accept || {
            'image/*': ['.png', '.jpg', '.jpeg', '.gif'],
            'application/pdf': ['.pdf']
          }
        });
        
        const files = await Promise.all(
          fileHandles.map(async (handle) => {
            const file = await handle.getFile();
            return { file, handle };
          })
        );
        
        return files;
      } else {
        // Fallback to input file
        return new Promise((resolve) => {
          const input = document.createElement('input');
          input.type = 'file';
          input.multiple = options.multiple || false;
          input.accept = Object.values(options.accept || {}).flat().join(',');
          
          input.onchange = (e) => {
            const files = Array.from(e.target.files).map(file => ({ file }));
            resolve(files);
          };
          
          input.click();
        });
      }
    } catch (error) {
      console.error('File picker error:', error);
      return [];
    }
  }, []);

  return {
    // State
    permissions,
    capabilities,
    deviceInfo,
    
    // Permission requests
    requestCameraPermission,
    requestLocationPermission,
    requestNotificationPermission,
    
    // Camera
    capturePhoto,
    
    // Location
    getCurrentLocation,
    watchLocation,
    
    // Notifications
    showNotification,
    subscribeToPushNotifications,
    
    // Device features
    vibrate,
    shareContent,
    installPWA,
    getBatteryInfo,
    requestWakeLock,
    openFilePicker,
    
    // Utilities
    checkPermissions,
    checkCapabilities
  };
};

export default useNativeFeatures;
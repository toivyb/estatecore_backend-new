// API Base URL Configuration
const BASE = import.meta.env.VITE_API_BASE_URL || 
  'https://estatecore-backend-sujs.onrender.com'  // Use production backend with all endpoints

export const authHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Enhanced API client with automatic authentication
class ApiClient {
  constructor() {
    this.BASE = BASE;
  }

  // Get complete headers with authentication and content type
  getHeaders(isUpload = false) {
    const headers = {
      ...authHeader(),
      ...(isUpload ? {} : { 'Content-Type': 'application/json' })
    };
    return headers;
  }

  // Generic request method with automatic error handling
  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.BASE}${endpoint}`;
    
    const config = {
      headers: this.getHeaders(options.isUpload),
      ...options,
    };

    // Override headers if explicitly provided
    if (options.headers) {
      config.headers = { ...config.headers, ...options.headers };
    }

    try {
      const response = await fetch(url, config);
      
      // Handle authentication errors
      if (response.status === 401) {
        console.warn('Authentication failed - redirecting to login');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.dispatchEvent(new Event('loginStateChange'));
        
        // Only redirect if not already on login page
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        throw new Error('Authentication failed');
      }

      // Return response for further processing
      return response;
      
    } catch (error) {
      console.error(`API Error for ${endpoint}:`, error);
      throw error;
    }
  }

  // GET request
  async get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    const response = await this.request(url, { method: 'GET' });
    
    if (!response.ok) {
      const errorData = await response.json();
      return errorData;
    }
    
    return response.json();
  }

  // POST request
  async post(endpoint, data = null, options = {}) {
    const response = await this.request(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : null,
      ...options,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      return errorData;
    }
    
    return response.json();
  }

  // PUT request
  async put(endpoint, data = null) {
    const response = await this.request(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : null,
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      return errorData;
    }
    
    return response.json();
  }

  // DELETE request
  async delete(endpoint) {
    const response = await this.request(endpoint, { method: 'DELETE' });
    
    // Handle both success and error responses
    if (!response.ok) {
      const errorData = await response.json();
      return errorData; // Return error data instead of throwing
    }
    
    return response.json();
  }

  // File upload
  async upload(endpoint, formData) {
    const response = await this.request(endpoint, {
      method: 'POST',
      body: formData,
      isUpload: true,
    });
    return response.json();
  }
}

// Create singleton instance
const apiClient = new ApiClient();

// API object with base functionality (backward compatibility)
export const api = {
  BASE,
  authHeader,
  // Enhanced methods
  get: apiClient.get.bind(apiClient),
  post: apiClient.post.bind(apiClient),
  put: apiClient.put.bind(apiClient),
  delete: apiClient.delete.bind(apiClient),
  upload: apiClient.upload.bind(apiClient),
  request: apiClient.request.bind(apiClient)
};

export default api;

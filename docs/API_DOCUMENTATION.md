# EstateCore API Documentation

## Overview
EstateCore provides a RESTful API for property management operations with AI-powered features.

## Base URL
```
Development: http://localhost:5000/api
Production: https://your-domain.com/api
```

## Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Core Endpoints

### Authentication
```
POST /api/auth/login
POST /api/auth/logout  
POST /api/auth/refresh
```

### Users
```
GET    /api/users              # List all users
POST   /api/users              # Create new user
GET    /api/users/{id}         # Get user by ID
PUT    /api/users/{id}         # Update user
DELETE /api/users/{id}         # Delete user
```

### Properties
```
GET    /api/properties         # List properties
POST   /api/properties         # Create property
GET    /api/properties/{id}    # Get property details
PUT    /api/properties/{id}    # Update property
DELETE /api/properties/{id}    # Delete property
```

### Tenants
```
GET    /api/tenants            # List tenants
POST   /api/tenants            # Create tenant
GET    /api/tenants/{id}       # Get tenant details
PUT    /api/tenants/{id}       # Update tenant
DELETE /api/tenants/{id}       # Delete tenant
```

### License Plate Recognition (LPR)
```
GET    /api/lpr-events         # List LPR events
POST   /api/lpr-events         # Create LPR event
GET    /api/lpr-events/csv     # Export events as CSV
GET    /api/lpr-events/{id}    # Get specific event
```

### Maintenance
```
GET    /api/maintenance        # List maintenance requests
POST   /api/maintenance        # Create maintenance request
GET    /api/maintenance/{id}   # Get maintenance details
PUT    /api/maintenance/{id}   # Update maintenance request
```

### AI Features
```
POST   /api/ai/lease-score     # Calculate lease scoring
POST   /api/ai/maintenance-forecast  # Predict maintenance needs
POST   /api/ai/revenue-analysis      # Analyze revenue leakage
POST   /api/ai/asset-health          # Asset health scoring
```

## Request/Response Examples

### Create User
```http
POST /api/users
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "tenant",
  "password": "secure_password"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "id": 123,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "tenant",
    "created_at": "2024-01-01T12:00:00Z"
  }
}
```

### Create LPR Event
```http
POST /api/lpr-events
Content-Type: application/json

{
  "timestamp": "2024-01-01 12:00:00",
  "plate": "ABC123",
  "camera": "Main Gate",
  "confidence": 0.95,
  "image_url": "https://example.com/image.jpg",
  "notes": "Vehicle entry"
}
```

Response:
```json
{
  "success": true,
  "id": 456
}
```

## Error Handling
All endpoints return consistent error responses:

```json
{
  "error": true,
  "message": "Error description",
  "code": "ERROR_CODE",
  "details": {}
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting
API requests are limited to:
- **Authentication**: 10 requests per minute
- **General endpoints**: 100 requests per minute
- **AI endpoints**: 20 requests per minute

## Pagination
List endpoints support pagination:
```
GET /api/users?page=2&limit=10&sort=created_at&order=desc
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 10,
    "total": 150,
    "pages": 15
  }
}
```

## Filtering and Search
Many endpoints support filtering:
```
GET /api/properties?status=active&type=apartment&city=Portland
GET /api/tenants?search=john&role=tenant
```

## Webhooks
EstateCore supports webhooks for real-time notifications:

### Supported Events
- `user.created`
- `property.updated` 
- `maintenance.created`
- `lpr.event`

### Webhook Configuration
```http
POST /api/webhooks
{
  "url": "https://your-app.com/webhook",
  "events": ["user.created", "lpr.event"],
  "secret": "your-webhook-secret"
}
```

## SDKs and Libraries
- **Python**: `pip install estatecore-sdk`
- **JavaScript**: `npm install estatecore-js`
- **PHP**: `composer require estatecore/php-sdk`

## Testing
Use the included Postman collection for API testing:
```
Import: docs/EstateCore-API-Collection.postman.json
```

## Support
- **Documentation**: [https://docs.estatecore.com](https://docs.estatecore.com)
- **Support**: support@estatecore.com
- **Issues**: [GitHub Issues](https://github.com/estatecore/estatecore/issues)
# Tenant Portal API Documentation

This document describes the tenant-specific endpoints created for the EstateCore tenant portal application.

## Base URL
All tenant portal endpoints are prefixed with `/api/tenant-portal`

## Authentication
All endpoints require tenant authentication and verify that the user has the 'tenant' role.

## Endpoints

### 1. Tenant Authentication Validation
**POST** `/api/tenant-portal/auth/validate`

Validates tenant login credentials and returns user/tenant information.

**Request Body:**
```json
{
  "email": "tenant@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "message": "Authentication successful",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "tenant@example.com",
    "role": "tenant"
  },
  "tenant": {
    "id": 1,
    "property_id": 1,
    "unit_id": 101,
    "status": "active"
  }
}
```

### 2. Tenant Profile Data
**GET** `/api/tenant-portal/profile/{user_id}`

Retrieves complete tenant profile information including user, tenant, and property details.

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "tenant@example.com",
    "created_at": "2025-01-01T00:00:00"
  },
  "tenant": {
    "id": 1,
    "lease_start": "2025-01-01",
    "lease_end": "2025-12-31",
    "rent_amount": 1500.00,
    "deposit": 1500.00,
    "status": "active",
    "unit_id": 101
  },
  "property": {
    "id": 1,
    "name": "Sunset Apartments",
    "address": "123 Main St, City, State",
    "type": "apartment"
  }
}
```

### 3. Payment History
**GET** `/api/tenant-portal/payments/{user_id}`

Retrieves tenant payment history with pagination support.

**Query Parameters:**
- `limit` (optional): Number of payments to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by payment status (pending, completed, failed)

**Response (200):**
```json
{
  "payments": [
    {
      "id": 1,
      "amount": 1500.00,
      "status": "completed",
      "payment_date": "2025-09-01T10:00:00",
      "stripe_payment_id": "pi_1234567890",
      "property_id": 1
    }
  ],
  "total_count": 12,
  "limit": 50,
  "offset": 0
}
```

### 4. Maintenance Requests
**GET** `/api/tenant-portal/maintenance/{user_id}`

Retrieves tenant maintenance requests with pagination support.

**Query Parameters:**
- `limit` (optional): Number of requests to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `status` (optional): Filter by status (submitted, in_progress, completed, cancelled)

**Response (200):**
```json
{
  "maintenance_requests": [
    {
      "id": 1,
      "title": "Leaky faucet in kitchen",
      "description": "The kitchen faucet has been dripping for several days",
      "category": "plumbing",
      "priority": "medium",
      "status": "in_progress",
      "notes": "Scheduled for repair on Friday",
      "created_at": "2025-09-15T09:00:00",
      "updated_at": "2025-09-16T14:30:00",
      "completed_at": null,
      "assigned_to": "maintenance_user"
    }
  ],
  "total_count": 5,
  "limit": 50,
  "offset": 0
}
```

**POST** `/api/tenant-portal/maintenance/{user_id}`

Creates a new maintenance request.

**Request Body:**
```json
{
  "title": "Broken air conditioning",
  "description": "AC unit not cooling properly, very hot in apartment",
  "category": "hvac",
  "priority": "high"
}
```

**Response (201):**
```json
{
  "message": "Maintenance request created successfully",
  "id": 2
}
```

### 5. Notifications
**GET** `/api/tenant-portal/notifications/{user_id}`

Retrieves tenant notifications with filtering options.

**Query Parameters:**
- `limit` (optional): Number of notifications to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)
- `unread_only` (optional): Show only unread notifications (true/false, default: false)
- `type` (optional): Filter by notification type (general, payment, maintenance, lease, system)

**Response (200):**
```json
{
  "notifications": [
    {
      "id": 1,
      "title": "Rent Due Reminder",
      "message": "Your rent payment of $1500 is due on October 1st",
      "type": "payment",
      "priority": "normal",
      "is_read": false,
      "action_required": true,
      "action_url": "/payments",
      "created_at": "2025-09-25T09:00:00",
      "read_at": null,
      "expires_at": "2025-10-02T00:00:00"
    }
  ],
  "unread_count": 3,
  "limit": 50,
  "offset": 0
}
```

**PUT** `/api/tenant-portal/notifications/{notification_id}/read`

Marks a notification as read.

**Response (200):**
```json
{
  "message": "Notification marked as read"
}
```

### 6. Lease Information
**GET** `/api/tenant-portal/lease/{user_id}`

Retrieves comprehensive lease information for the tenant.

**Response (200):**
```json
{
  "tenant_id": 1,
  "lease_start": "2025-01-01",
  "lease_end": "2025-12-31",
  "rent_amount": 1500.00,
  "deposit": 1500.00,
  "status": "active",
  "lease_status": "active",
  "days_until_expiry": 102,
  "lease_document_name": "lease_agreement_2025.pdf",
  "property": {
    "id": 1,
    "name": "Sunset Apartments",
    "address": "123 Main St, City, State",
    "type": "apartment"
  },
  "unit_id": 101
}
```

### 7. Dashboard Summary
**GET** `/api/tenant-portal/dashboard/{user_id}`

Retrieves a comprehensive dashboard summary with key metrics and recent activity.

**Response (200):**
```json
{
  "tenant_info": {
    "name": "john_doe",
    "email": "tenant@example.com",
    "property_name": "Sunset Apartments",
    "unit_id": 101,
    "rent_amount": 1500.00
  },
  "lease_info": {
    "status": "active",
    "days_until_expiry": 102,
    "lease_end": "2025-12-31"
  },
  "counts": {
    "unread_notifications": 3,
    "unread_messages": 1,
    "pending_maintenance": 2
  },
  "recent_payments": [
    {
      "id": 1,
      "amount": 1500.00,
      "status": "completed",
      "payment_date": "2025-09-01T10:00:00"
    }
  ]
}
```

## Error Responses

All endpoints return consistent error responses:

**400 Bad Request:**
```json
{
  "error": "Email and password are required"
}
```

**401 Unauthorized:**
```json
{
  "error": "Invalid credentials"
}
```

**403 Forbidden:**
```json
{
  "error": "Access denied - tenant access only"
}
```

**404 Not Found:**
```json
{
  "error": "Tenant profile not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error message"
}
```

## Data Models

### MaintenanceRequest
- **id**: Unique identifier
- **tenant_id**: Foreign key to users table
- **property_id**: Foreign key to properties table
- **unit_id**: Unit identifier (optional)
- **title**: Short description of the issue
- **description**: Detailed description
- **category**: Type of maintenance (plumbing, electrical, hvac, appliance, other)
- **priority**: Priority level (low, medium, high, urgent)
- **status**: Current status (submitted, in_progress, completed, cancelled)
- **assigned_to_id**: Foreign key to users table (maintenance staff)
- **estimated_cost**: Estimated repair cost
- **actual_cost**: Actual repair cost
- **notes**: Additional notes
- **created_at**: Creation timestamp
- **updated_at**: Last update timestamp
- **completed_at**: Completion timestamp

### Notification
- **id**: Unique identifier
- **user_id**: Foreign key to users table
- **title**: Notification title
- **message**: Notification content
- **type**: Notification type (general, payment, maintenance, lease, system)
- **priority**: Priority level (low, normal, high, urgent)
- **is_read**: Read status
- **action_required**: Whether action is required
- **action_url**: URL for action (optional)
- **expires_at**: Expiration timestamp (optional)
- **created_at**: Creation timestamp
- **read_at**: Read timestamp

## Usage Notes

1. All endpoints require the user to have the 'tenant' role
2. User authentication should be handled before calling these endpoints
3. The system automatically creates notifications for relevant events (new maintenance requests, etc.)
4. Pagination is supported on list endpoints using `limit` and `offset` parameters
5. Date/time fields are returned in ISO format
6. All monetary amounts are returned as floats
7. Expired notifications are automatically filtered out from results
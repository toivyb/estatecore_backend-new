# Appwrite Database Collections Setup

## Database Configuration

**Database ID:** `estatecore_main`

Create the following collections in your Appwrite database with the specified attributes:

## 1. Users Collection
**Collection ID:** `users`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| name | string | 255 | Yes | No | - |
| email | string | 320 | Yes | No | - |
| role | string | 50 | Yes | No | "user" |
| is_active | boolean | - | Yes | No | true |
| created_at | datetime | - | No | No | - |
| updated_at | datetime | - | No | No | - |

**Indexes:**
- email (unique)

## 2. Tenants Collection
**Collection ID:** `tenants`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| name | string | 255 | Yes | No | - |
| email | string | 320 | Yes | No | - |
| phone | string | 20 | No | No | - |
| emergency_contact_name | string | 255 | No | No | - |
| emergency_contact_phone | string | 20 | No | No | - |
| lease_status | string | 20 | Yes | No | "inactive" |
| move_in_date | datetime | - | No | No | - |
| move_out_date | datetime | - | No | No | - |
| notes | string | 2000 | No | No | - |
| access_permissions | string | 1000 | No | Yes | - |
| created_at | datetime | - | No | No | - |
| updated_at | datetime | - | No | No | - |

**Indexes:**
- email (unique)
- lease_status

## 3. Properties Collection  
**Collection ID:** `properties`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| name | string | 255 | Yes | No | - |
| address | string | 500 | Yes | No | - |
| city | string | 100 | Yes | No | - |
| state | string | 50 | Yes | No | - |
| zip_code | string | 10 | Yes | No | - |
| property_type | string | 50 | Yes | No | "apartment" |
| total_units | integer | - | Yes | No | 1 |
| description | string | 2000 | No | No | - |
| amenities | string | 1000 | No | Yes | - |
| monthly_rent | float | - | No | No | 0 |
| deposit_amount | float | - | No | No | 0 |
| is_active | boolean | - | Yes | No | true |
| created_at | datetime | - | No | No | - |
| updated_at | datetime | - | No | No | - |

**Indexes:**
- city
- property_type
- is_active

## 4. Leases Collection
**Collection ID:** `leases`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| tenant_id | string | 36 | Yes | No | - |
| property_id | string | 36 | Yes | No | - |
| unit_number | string | 10 | No | No | - |
| start_date | datetime | - | Yes | No | - |
| end_date | datetime | - | Yes | No | - |
| monthly_rent | float | - | Yes | No | - |
| deposit_amount | float | - | Yes | No | - |
| status | string | 20 | Yes | No | "draft" |
| lease_terms | string | 5000 | No | No | - |
| notes | string | 2000 | No | No | - |
| created_at | datetime | - | No | No | - |
| updated_at | datetime | - | No | No | - |

**Indexes:**
- tenant_id
- property_id  
- status
- start_date
- end_date

## 5. Work Orders Collection
**Collection ID:** `workorders`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| title | string | 255 | Yes | No | - |
| description | string | 2000 | Yes | No | - |
| property_id | string | 36 | Yes | No | - |
| tenant_id | string | 36 | No | No | - |
| assigned_to | string | 255 | No | No | - |
| priority | string | 20 | Yes | No | "medium" |
| status | string | 20 | Yes | No | "open" |
| category | string | 50 | Yes | No | "general" |
| estimated_cost | float | - | No | No | 0 |
| actual_cost | float | - | No | No | 0 |
| due_date | datetime | - | No | No | - |
| completed_date | datetime | - | No | No | - |
| photos | string | 500 | No | Yes | - |
| notes | string | 2000 | No | No | - |
| created_at | datetime | - | No | No | - |
| updated_at | datetime | - | No | No | - |

**Indexes:**
- property_id
- tenant_id
- status
- priority
- due_date

## 6. Payments Collection
**Collection ID:** `payments`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| tenant_id | string | 36 | Yes | No | - |
| lease_id | string | 36 | Yes | No | - |
| amount | float | - | Yes | No | - |
| payment_type | string | 50 | Yes | No | "rent" |
| payment_method | string | 50 | Yes | No | "online" |
| payment_date | datetime | - | Yes | No | - |
| due_date | datetime | - | No | No | - |
| status | string | 20 | Yes | No | "pending" |
| transaction_id | string | 255 | No | No | - |
| notes | string | 1000 | No | No | - |
| created_at | datetime | - | No | No | - |
| updated_at | datetime | - | No | No | - |

**Indexes:**
- tenant_id
- lease_id
- payment_date
- due_date
- status

## 7. Cameras Collection (VMS)
**Collection ID:** `cameras`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| name | string | 255 | Yes | No | - |
| location | string | 255 | Yes | No | - |
| property_id | string | 36 | Yes | No | - |
| ip_address | string | 45 | Yes | No | - |
| port | integer | - | No | No | 554 |
| username | string | 100 | No | No | - |
| password | string | 100 | No | No | - |
| stream_url | string | 500 | No | No | - |
| status | string | 20 | Yes | No | "offline" |
| recording_enabled | boolean | - | Yes | No | false |
| motion_detection | boolean | - | Yes | No | false |
| resolution | string | 20 | No | No | "1080p" |
| fps | integer | - | No | No | 30 |
| created_at | datetime | - | No | No | - |
| updated_at | datetime | - | No | No | - |

**Indexes:**
- property_id
- status
- ip_address

## 8. Recordings Collection (VMS)
**Collection ID:** `recordings`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| camera_id | string | 36 | Yes | No | - |
| filename | string | 255 | Yes | No | - |
| file_path | string | 500 | Yes | No | - |
| file_size | integer | - | No | No | 0 |
| duration | integer | - | No | No | 0 |
| start_time | datetime | - | Yes | No | - |
| end_time | datetime | - | Yes | No | - |
| recording_type | string | 50 | Yes | No | "scheduled" |
| status | string | 20 | Yes | No | "active" |
| thumbnail_path | string | 500 | No | No | - |
| created_at | datetime | - | No | No | - |

**Indexes:**
- camera_id
- start_time
- recording_type

## 9. Motion Events Collection (VMS)
**Collection ID:** `motion_events`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| camera_id | string | 36 | Yes | No | - |
| detected_at | datetime | - | Yes | No | - |
| confidence | float | - | No | No | 0 |
| bounding_box | string | 200 | No | No | - |
| snapshot_path | string | 500 | No | No | - |
| recording_id | string | 36 | No | No | - |
| processed | boolean | - | Yes | No | false |
| created_at | datetime | - | No | No | - |

**Indexes:**
- camera_id
- detected_at
- processed

## 10. Access Doors Collection
**Collection ID:** `access_doors`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| name | string | 255 | Yes | No | - |
| location | string | 255 | Yes | No | - |
| property_id | string | 36 | Yes | No | - |
| door_type | string | 50 | Yes | No | "entry" |
| access_method | string | 50 | Yes | No | "keycard" |
| status | string | 20 | Yes | No | "locked" |
| is_active | boolean | - | Yes | No | true |
| controller_ip | string | 45 | No | No | - |
| controller_port | integer | - | No | No | 4370 |
| created_at | datetime | - | No | No | - |
| updated_at | datetime | - | No | No | - |

**Indexes:**
- property_id
- status
- door_type

## 11. Access Events Collection
**Collection ID:** `access_events`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| door_id | string | 36 | Yes | No | - |
| tenant_id | string | 36 | No | No | - |
| event_type | string | 50 | Yes | No | "access_attempt" |
| access_method | string | 50 | No | No | - |
| card_id | string | 100 | No | No | - |
| result | string | 20 | Yes | No | "denied" |
| timestamp | datetime | - | Yes | No | - |
| notes | string | 500 | No | No | - |
| created_at | datetime | - | No | No | - |

**Indexes:**
- door_id
- tenant_id
- timestamp
- result

## 12. Audit Logs Collection
**Collection ID:** `audit_logs`

| Attribute | Type | Size | Required | Array | Default |
|-----------|------|------|----------|-------|---------|
| user_id | string | 36 | No | No | - |
| action | string | 100 | Yes | No | - |
| resource_type | string | 50 | Yes | No | - |
| resource_id | string | 36 | No | No | - |
| details | string | 2000 | No | No | - |
| ip_address | string | 45 | No | No | - |
| user_agent | string | 500 | No | No | - |
| timestamp | datetime | - | Yes | No | - |
| created_at | datetime | - | No | No | - |

**Indexes:**
- user_id
- action
- timestamp
- resource_type

## Permissions Setup

For each collection, set the following permissions:

### Read Permissions:
- `users` (authenticated users can read)
- `role:admin` (admin role can read all)

### Write Permissions:
- `users` (authenticated users can write their own data)
- `role:admin` (admin role can write all)

### Create Permissions:
- `users` (authenticated users can create)
- `role:admin` (admin role can create)

### Update Permissions:
- `users` (authenticated users can update their own data)  
- `role:admin` (admin role can update all)

### Delete Permissions:
- `role:admin` (only admin role can delete)

## Setup Steps in Appwrite Console

1. **Go to your Appwrite project:** https://cloud.appwrite.io
2. **Navigate to Databases**
3. **Create database:** `estatecore_main`
4. **Create each collection** with the Collection ID specified
5. **Add all attributes** for each collection as listed above
6. **Create indexes** as specified
7. **Set permissions** for each collection
8. **Test the setup** by creating sample documents

## Important Notes

- All datetime fields should use ISO 8601 format
- String arrays are used for multi-value fields (amenities, access_permissions, photos)
- Foreign key relationships are managed through document IDs (tenant_id, property_id, etc.)
- Ensure proper validation rules are set for required fields
- Consider setting up database functions/triggers for automated timestamps
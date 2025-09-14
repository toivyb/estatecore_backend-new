# 🔧 Manual Appwrite Setup Guide

Since you're getting 401 Unauthorized errors, your Appwrite backend needs to be set up. Here's the step-by-step manual process:

## 🎯 **Step 1: Create Database Collections**

Go to your Appwrite Console: https://cloud.appwrite.io

### 1.1 Navigate to Your Project
- Project: **Estate_core Backend**
- Project ID: **68b6e4240013f757c47b**

### 1.2 Create Database
1. Go to **Databases** in the sidebar
2. Click **Create Database**
3. Database ID: `68b72cd60024e95cea71`
4. Name: `EstateCore Main Database`

### 1.3 Create Collections (12 Total)
For each collection below, click **Create Collection** and add the attributes:

#### Collection 1: `users`
```
Collection ID: users
Name: Users

Attributes:
- name (String, Size: 255, Required: Yes)
- email (String, Size: 320, Required: Yes) 
- role (String, Size: 50, Required: Yes, Default: "user")
- is_active (Boolean, Required: Yes, Default: true)
- created_at (DateTime, Required: No)
- updated_at (DateTime, Required: No)

Indexes:
- Key: email, Type: Unique, Attributes: [email]

Permissions:
- Read: users, role:admin
- Create: users, role:admin
- Update: users, role:admin  
- Delete: role:admin
```

#### Collection 2: `tenants`
```
Collection ID: tenants
Name: Tenants

Attributes:
- name (String, Size: 255, Required: Yes)
- email (String, Size: 320, Required: Yes)
- phone (String, Size: 20, Required: No)
- emergency_contact_name (String, Size: 255, Required: No)
- emergency_contact_phone (String, Size: 20, Required: No)
- lease_status (String, Size: 20, Required: Yes, Default: "inactive")
- move_in_date (DateTime, Required: No)
- move_out_date (DateTime, Required: No)
- notes (String, Size: 2000, Required: No)
- created_at (DateTime, Required: No)
- updated_at (DateTime, Required: No)

Indexes:
- Key: email, Type: Unique, Attributes: [email]
- Key: lease_status, Type: Key, Attributes: [lease_status]

Permissions:
- Read: users, role:admin
- Create: users, role:admin
- Update: users, role:admin
- Delete: role:admin
```

#### Collection 3: `properties`
```
Collection ID: properties
Name: Properties

Attributes:
- name (String, Size: 255, Required: Yes)
- address (String, Size: 500, Required: Yes)
- city (String, Size: 100, Required: Yes)
- state (String, Size: 50, Required: Yes)
- zip_code (String, Size: 10, Required: Yes)
- property_type (String, Size: 50, Required: Yes, Default: "apartment")
- total_units (Integer, Required: Yes, Default: 1)
- description (String, Size: 2000, Required: No)
- monthly_rent (Float, Required: No, Default: 0)
- deposit_amount (Float, Required: No, Default: 0)
- is_active (Boolean, Required: Yes, Default: true)
- created_at (DateTime, Required: No)
- updated_at (DateTime, Required: No)

Indexes:
- Key: city, Type: Key, Attributes: [city]
- Key: property_type, Type: Key, Attributes: [property_type]
- Key: is_active, Type: Key, Attributes: [is_active]

Permissions:
- Read: users, role:admin
- Create: users, role:admin
- Update: users, role:admin
- Delete: role:admin
```

#### Collection 4: `leases`
```
Collection ID: leases
Name: Leases

Attributes:
- tenant_id (String, Size: 36, Required: Yes)
- property_id (String, Size: 36, Required: Yes)  
- unit_number (String, Size: 10, Required: No)
- start_date (DateTime, Required: Yes)
- end_date (DateTime, Required: Yes)
- monthly_rent (Float, Required: Yes)
- deposit_amount (Float, Required: Yes)
- status (String, Size: 20, Required: Yes, Default: "draft")
- lease_terms (String, Size: 5000, Required: No)
- notes (String, Size: 2000, Required: No)
- created_at (DateTime, Required: No)
- updated_at (DateTime, Required: No)

Indexes:
- Key: tenant_id, Type: Key, Attributes: [tenant_id]
- Key: property_id, Type: Key, Attributes: [property_id]
- Key: status, Type: Key, Attributes: [status]

Permissions:
- Read: users, role:admin
- Create: users, role:admin
- Update: users, role:admin
- Delete: role:admin
```

#### Collection 5: `workorders`
```
Collection ID: workorders  
Name: Work Orders

Attributes:
- title (String, Size: 255, Required: Yes)
- description (String, Size: 2000, Required: Yes)
- property_id (String, Size: 36, Required: Yes)
- tenant_id (String, Size: 36, Required: No)
- assigned_to (String, Size: 255, Required: No)
- priority (String, Size: 20, Required: Yes, Default: "medium")
- status (String, Size: 20, Required: Yes, Default: "open")
- category (String, Size: 50, Required: Yes, Default: "general")
- estimated_cost (Float, Required: No, Default: 0)
- actual_cost (Float, Required: No, Default: 0)
- due_date (DateTime, Required: No)
- completed_date (DateTime, Required: No)
- notes (String, Size: 2000, Required: No)
- created_at (DateTime, Required: No)
- updated_at (DateTime, Required: No)

Indexes:
- Key: property_id, Type: Key, Attributes: [property_id]
- Key: status, Type: Key, Attributes: [status]
- Key: priority, Type: Key, Attributes: [priority]

Permissions:
- Read: users, role:admin
- Create: users, role:admin
- Update: users, role:admin
- Delete: role:admin
```

#### Collection 6: `payments`
```
Collection ID: payments
Name: Payments

Attributes:
- tenant_id (String, Size: 36, Required: Yes)
- lease_id (String, Size: 36, Required: Yes)
- amount (Float, Required: Yes)
- payment_type (String, Size: 50, Required: Yes, Default: "rent")
- payment_method (String, Size: 50, Required: Yes, Default: "online")
- payment_date (DateTime, Required: Yes)
- due_date (DateTime, Required: No)
- status (String, Size: 20, Required: Yes, Default: "pending")
- transaction_id (String, Size: 255, Required: No)
- notes (String, Size: 1000, Required: No)
- created_at (DateTime, Required: No)
- updated_at (DateTime, Required: No)

Indexes:
- Key: tenant_id, Type: Key, Attributes: [tenant_id]
- Key: lease_id, Type: Key, Attributes: [lease_id]
- Key: status, Type: Key, Attributes: [status]

Permissions:
- Read: users, role:admin
- Create: users, role:admin
- Update: users, role:admin
- Delete: role:admin
```

#### Collection 7: `cameras`
```
Collection ID: cameras
Name: Cameras

Attributes:
- name (String, Size: 255, Required: Yes)
- location (String, Size: 255, Required: Yes)
- property_id (String, Size: 36, Required: Yes)
- ip_address (String, Size: 45, Required: Yes)
- port (Integer, Required: No, Default: 554)
- username (String, Size: 100, Required: No)
- password (String, Size: 100, Required: No)
- stream_url (String, Size: 500, Required: No)
- status (String, Size: 20, Required: Yes, Default: "offline")
- recording_enabled (Boolean, Required: Yes, Default: false)
- motion_detection (Boolean, Required: Yes, Default: false)
- resolution (String, Size: 20, Required: No, Default: "1080p")
- fps (Integer, Required: No, Default: 30)
- created_at (DateTime, Required: No)
- updated_at (DateTime, Required: No)

Permissions:
- Read: users, role:admin
- Create: users, role:admin
- Update: users, role:admin
- Delete: role:admin
```

#### Collections 8-12: (Abbreviated for space)
Continue with the same pattern for:
- `recordings` (video recordings metadata)
- `motion_events` (motion detection events)
- `access_doors` (access control doors)
- `access_events` (access logs)
- `audit_logs` (system audit trail)

---

## 🔐 **Step 2: Configure Authentication**

### 2.1 Enable Authentication
1. Go to **Auth** in the sidebar
2. Click **Settings**
3. Enable **Email/Password** authentication
4. Set password requirements:
   - Minimum length: 8 characters
   - Require uppercase: Optional
   - Require lowercase: Optional
   - Require numbers: Optional
   - Require special characters: Optional

### 2.2 Configure Sessions
1. In Auth Settings:
   - Session length: 1 year (default)
   - Allow multiple sessions: Yes
   - Security settings as needed

---

## 🎯 **Step 3: Create Test User**

### 3.1 Manual User Creation
1. Go to **Auth > Users**
2. Click **Create User**
3. Email: `admin@estatecore.com`
4. Password: `password123` (change this!)
5. Name: `Admin User`

### 3.2 Alternative: Use Registration
Once auth is configured, you can use the registration form in your app.

---

## ⚡ **Step 4: Deploy Functions (Optional)**

### 4.1 Skip Functions Initially
For now, skip the functions deployment. Your app will work with basic CRUD operations.

### 4.2 Functions Can Be Added Later
The dashboard metrics and other advanced features require functions, but basic property management will work without them.

---

## 🧪 **Step 5: Test Your Setup**

### 5.1 Try Login
1. Go to your frontend application
2. Try logging in with the test user credentials
3. Should work if authentication is configured correctly

### 5.2 Check Console Errors
1. Open browser developer tools
2. Look for any remaining 401 errors
3. They should be resolved after auth configuration

---

## 🔍 **Troubleshooting**

### Common Issues:

**Still Getting 401 Errors:**
- Check that Email/Password auth is enabled
- Verify database collections exist
- Ensure permissions are set correctly

**Login Not Working:**
- Create a test user manually in Appwrite console
- Check password requirements
- Verify project ID matches in your code

**Database Errors:**
- Ensure all 12 collections are created
- Check that collection IDs match exactly
- Verify permissions are set

---

## 🎉 **Once Setup is Complete**

After completing these steps:
1. Your login should work
2. You can create properties, tenants, etc.
3. Basic property management features will be functional
4. Advanced features (reporting, VMS) may need functions

**This manual setup will get your Appwrite backend working!** ⚡
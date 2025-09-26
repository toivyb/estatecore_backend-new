# EstateCore White-Label Multi-Tenant Architecture

## Overview

This documentation covers the comprehensive white-label multi-tenant architecture implementation for EstateCore, enabling enterprise customers and partners to deploy branded versions of the platform with complete customization and isolation.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Components](#core-components)
3. [Database Schema](#database-schema)
4. [API Documentation](#api-documentation)
5. [Deployment Guide](#deployment-guide)
6. [Partner Integration](#partner-integration)
7. [Tenant Management](#tenant-management)
8. [Branding & Customization](#branding--customization)
9. [SSO Integration](#sso-integration)
10. [Monitoring & Analytics](#monitoring--analytics)
11. [Security Considerations](#security-considerations)
12. [Troubleshooting](#troubleshooting)

## Architecture Overview

### Multi-Tenant Strategy
- **Shared Database, Isolated by Organization**: Each tenant gets a unique organization context with data isolation
- **Tenant Resolution**: Automatic tenant identification via subdomain, custom domain, or API headers
- **Resource Quotas**: Configurable limits per tenant based on their plan
- **Feature Flags**: Granular feature control per tenant

### Key Features
- Complete UI/UX white-labeling with custom themes
- Subdomain provisioning (client.estatecore.com)
- Custom domain support with SSL (client.com)
- Partner portal for managing multiple tenants
- SSO integration (SAML 2.0, OAuth 2.0, OpenID Connect)
- Real-time usage monitoring and analytics
- API-first architecture with tenant-aware endpoints

## Core Components

### 1. Tenant Context System
**File**: `services/tenant_context.py`

Manages tenant context throughout the request lifecycle:
```python
from services.tenant_context import get_current_tenant_context

context = get_current_tenant_context()
tenant_id = context.tenant_id
brand_setting = context.get_brand_setting('logo_url')
```

### 2. Tenant Middleware
**File**: `middleware/tenant_middleware.py`

Automatic tenant resolution and context injection:
```python
from middleware.tenant_middleware import setup_tenant_middleware

# In your app initialization
setup_tenant_middleware(app, {
    'require_tenant_for_api': True,
    'allowed_no_tenant_paths': ['/health', '/admin']
})
```

### 3. White-Label Models
**File**: `models/white_label_tenant.py`

Core data models for multi-tenancy:
- `WhiteLabelTenant`: Main tenant configuration
- `Partner`: Partner organizations managing tenants
- `TenantDomain`: Custom domain management
- `TenantUsageLog`: Usage tracking and billing

### 4. Branding Service
**File**: `services/branding_service.py`

Complete branding and theme management:
```python
from services.branding_service import get_branding_service

service = get_branding_service()
brand_config = service.get_tenant_brand_config(tenant_id)
css_content = service.generate_theme_css(tenant_id)
```

### 5. Feature Flags System
**File**: `services/feature_flags.py`

Tenant-specific feature management:
```python
from services.feature_flags import feature_enabled, get_feature_value

if feature_enabled('ai_analytics', tenant_id):
    # Enable AI features
    pass

max_properties = get_feature_value('max_properties', tenant_id, default=50)
```

## Database Schema

### Core Tables

#### white_label_tenants
```sql
CREATE TABLE white_label_tenants (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER UNIQUE NOT NULL,
    tenant_key VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    subdomain VARCHAR(63) UNIQUE NOT NULL,
    custom_domain VARCHAR(255) UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'provisioning',
    brand_config JSON,
    feature_flags JSON,
    resource_quotas JSON,
    usage_metrics JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### partners
```sql
CREATE TABLE partners (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    contact_email VARCHAR(120) NOT NULL,
    api_key VARCHAR(100) UNIQUE NOT NULL,
    default_revenue_share DECIMAL(5,2) DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### tenant_domains
```sql
CREATE TABLE tenant_domains (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    verification_token VARCHAR(100),
    ssl_certificate_arn VARCHAR(500),
    verified_at TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES white_label_tenants(id)
);
```

## API Documentation

### Authentication
All partner API calls require authentication via API key:
```bash
curl -H "X-API-Key: your-partner-api-key" \
     -H "Content-Type: application/json" \
     https://api.estatecore.com/api/white-label/tenants
```

### Core Endpoints

#### Create Tenant
```bash
POST /api/white-label/tenants
Content-Type: application/json
X-API-Key: your-partner-api-key

{
    "name": "Acme Property Management",
    "subdomain": "acme",
    "contact_email": "admin@acme.com",
    "plan": "premium",
    "feature_flags": {
        "ai_analytics": true,
        "custom_domains": true
    },
    "brand_config": {
        "name": "Acme Properties",
        "colors": {
            "primary": "#ff6b35",
            "secondary": "#004e89"
        }
    }
}
```

#### Update Tenant Branding
```bash
PUT /api/white-label/tenants/{tenant_id}/branding
Content-Type: application/json
X-API-Key: your-partner-api-key

{
    "colors": {
        "primary": "#ff6b35",
        "secondary": "#004e89"
    },
    "logo": {
        "primary": "https://cdn.acme.com/logo.png"
    },
    "typography": {
        "font_family_primary": "'Roboto', sans-serif"
    }
}
```

#### Setup Custom Domain
```bash
POST /api/white-label/tenants/{tenant_id}/domains
Content-Type: application/json
X-API-Key: your-partner-api-key

{
    "domain": "properties.acme.com"
}
```

### Tenant Context API
For tenant-specific API access using tenant context:
```bash
GET /api/white-label/current/info
X-Tenant-Key: acme

# or via subdomain
GET https://acme.estatecore.com/api/white-label/current/info
```

## Deployment Guide

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis (for caching)
- AWS Account (for S3, CloudFront, Route53)

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/estatecore

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
BRANDING_BUCKET=estatecore-branding

# Security
SECRET_KEY=your-secret-key
ADMIN_TOKEN=your-admin-token

# SSO Configuration
SSO_PRIVATE_KEY=path/to/private/key.pem
SSO_PUBLIC_KEY=path/to/public/key.pem
```

### Database Setup
```bash
# Run migrations
flask db upgrade

# Create initial partner
python scripts/create_partner.py \
    --name "Initial Partner" \
    --email "partner@example.com"
```

### Application Integration
```python
# In your main app.py
from middleware.tenant_middleware import setup_tenant_middleware
from routes.white_label_api import white_label_bp

# Setup middleware
setup_tenant_middleware(app)

# Register blueprint
app.register_blueprint(white_label_bp)
```

### DNS Configuration
For custom domains, configure DNS records:
```
CNAME properties.acme.com -> acme.estatecore.com
```

### SSL Certificate Management
Automatic SSL certificate provisioning via AWS Certificate Manager.

## Partner Integration

### Partner Registration
1. Contact EstateCore to register as a partner
2. Receive API credentials and documentation
3. Integrate with partner portal or API directly

### Partner Portal Access
Access the partner portal at: `https://partners.estatecore.com`

Features:
- Tenant management dashboard
- Real-time analytics and monitoring
- Billing and revenue tracking
- Support ticket management

### API Integration Example
```python
import requests

class EstateCorePartnerAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.estatecore.com/api/white-label"
    
    def create_tenant(self, tenant_data):
        response = requests.post(
            f"{self.base_url}/tenants",
            headers={"X-API-Key": self.api_key},
            json=tenant_data
        )
        return response.json()
    
    def get_tenant_analytics(self, tenant_id):
        response = requests.get(
            f"{self.base_url}/tenants/{tenant_id}/analytics",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()

# Usage
api = EstateCorePartnerAPI("your-api-key")
tenant = api.create_tenant({
    "name": "New Client",
    "subdomain": "newclient",
    "contact_email": "admin@newclient.com"
})
```

## Tenant Management

### Tenant Lifecycle
1. **Provisioning**: Initial tenant creation and setup
2. **Active**: Fully operational tenant
3. **Suspended**: Temporarily disabled
4. **Maintenance**: Under maintenance
5. **Deactivated**: Permanently disabled

### Resource Management
```python
# Check resource usage
from services.tenant_monitoring import get_tenant_monitoring_service

monitoring = get_tenant_monitoring_service()
usage = monitoring.get_usage_analytics(tenant_id, period_days=30)

# Update quotas
tenant.set_resource_quota('api_calls_monthly', 100000)
tenant.set_resource_quota('storage_gb', 100)
```

### Configuration Management
```python
# Feature management
from services.feature_flags import get_feature_flag_service

features = get_feature_flag_service()
features.set_tenant_feature(tenant_id, 'ai_analytics', True)
features.set_tenant_feature(tenant_id, 'max_properties', 200)
```

## Branding & Customization

### Theme Configuration
```json
{
    "colors": {
        "primary": "#007bff",
        "secondary": "#6c757d",
        "success": "#28a745",
        "danger": "#dc3545"
    },
    "typography": {
        "font_family_primary": "'Inter', sans-serif",
        "font_size_base": "1rem"
    },
    "layout": {
        "border_radius": "0.5rem",
        "container_max_width": "1200px"
    }
}
```

### Asset Management
Upload branded assets via API:
```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -F "file=@logo.png" \
  -F "asset_type=logo" \
  https://api.estatecore.com/api/white-label/tenants/{tenant_id}/branding/upload
```

### Custom CSS
```css
/* Auto-generated from tenant configuration */
:root {
    --color-primary: #007bff;
    --font-family-primary: 'Inter', sans-serif;
}

.btn-primary {
    background-color: var(--color-primary);
}
```

### Email Templates
Customize email templates with tenant branding:
```python
from services.branding_service import get_email_branding_service

email_service = get_email_branding_service()
rendered_email = email_service.render_branded_email(
    'welcome_email',
    tenant_id=tenant_id,
    user_name='John Doe'
)
```

## SSO Integration

### Supported Providers
- SAML 2.0
- OAuth 2.0
- OpenID Connect
- Azure AD
- Google Workspace
- Okta
- OneLogin

### Configuration Example
```python
from services.sso_service import get_sso_service, SSOProvider

sso_service = get_sso_service()

# Configure Azure AD SSO
config = {
    'tenant_id': 'your-azure-tenant-id',
    'client_id': 'your-app-client-id',
    'client_secret': 'your-app-client-secret',
    'name': 'Azure AD Login'
}

success, message = sso_service.configure_tenant_sso(
    tenant_id, 
    SSOProvider.AZURE_AD, 
    config
)
```

### SSO Flow
1. User accesses tenant login page
2. Clicks SSO provider button
3. Redirected to provider for authentication
4. Provider redirects back with authentication result
5. User is logged into tenant system

### Custom Authentication
Implement custom authentication providers:
```python
class CustomSSOProvider(BaseSSOProvider):
    def validate_config(self, config):
        # Validate custom provider config
        return True, "Valid"
    
    def get_authorization_url(self, config, state):
        # Generate authorization URL
        return "https://custom-provider.com/auth"
    
    def process_callback(self, config, callback_data):
        # Process authentication callback
        return True, "Success", user_info
```

## Monitoring & Analytics

### Usage Tracking
```python
from services.tenant_monitoring import log_tenant_api_request

# Automatically logged by middleware
log_tenant_api_request(
    endpoint='/api/properties',
    method='GET',
    response_status=200,
    response_time=150.5
)
```

### Health Monitoring
```python
from services.tenant_monitoring import get_tenant_monitoring_service

monitoring = get_tenant_monitoring_service()
health_score = monitoring.get_tenant_health_score(tenant_id)

# Returns:
{
    "health_score": 95.2,
    "status": "excellent",
    "components": {
        "api_health": 98.5,
        "usage_health": 92.0,
        "error_health": 97.0,
        "activity_health": 93.5
    }
}
```

### Analytics Dashboard
Access detailed analytics:
- API usage patterns
- Resource consumption
- User activity metrics
- Error rates and performance
- Revenue and billing data

### Alerts and Notifications
```python
# Create usage alert
monitoring.create_alert(
    tenant_id=tenant_id,
    alert_name="High API Usage",
    condition="api_calls_hourly > threshold",
    threshold=1000,
    level=AlertLevel.WARNING
)
```

## Security Considerations

### Data Isolation
- Organization-level data filtering
- Tenant context validation on all operations
- No cross-tenant data leakage

### Authentication & Authorization
- Partner API key authentication
- Tenant-specific SSO configurations
- Role-based access control per tenant

### SSL/TLS
- Automatic SSL certificate provisioning
- Enforced HTTPS for custom domains
- Certificate renewal automation

### Rate Limiting
```python
from middleware.tenant_middleware import tenant_resource_limit

@tenant_resource_limit('api_calls', cost=1)
def api_endpoint():
    # Automatically enforces tenant API limits
    pass
```

### Audit Logging
All tenant operations are logged for compliance:
```python
from services.tenant_monitoring import log_tenant_activity

log_tenant_activity(
    user_id=user_id,
    activity_type='property_created',
    details={'property_id': 123}
)
```

## Troubleshooting

### Common Issues

#### Tenant Not Resolving
```bash
# Check tenant configuration
curl -H "X-Admin-Token: your-token" \
     https://api.estatecore.com/api/white-label/tenants?status=active

# Verify DNS configuration
dig acme.estatecore.com
```

#### SSO Configuration Issues
```python
# Test SSO configuration
from services.sso_service import get_sso_service

sso_service = get_sso_service()
result = sso_service.initiate_sso_login(tenant_id, provider_type)
print(f"SSO Status: {result}")
```

#### Performance Issues
```python
# Check tenant health
from services.tenant_monitoring import get_tenant_monitoring_service

monitoring = get_tenant_monitoring_service()
health = monitoring.get_tenant_health_score(tenant_id)
analytics = monitoring.get_usage_analytics(tenant_id)
```

### Debug Mode
Enable debug logging:
```python
import logging
logging.getLogger('white_label').setLevel(logging.DEBUG)
```

### Support Channels
- Technical Documentation: [docs.estatecore.com](https://docs.estatecore.com)
- Partner Support: partner-support@estatecore.com
- API Status: [status.estatecore.com](https://status.estatecore.com)

## Advanced Features

### Multi-Region Deployment
Configure tenants across multiple regions for global scalability.

### Webhook Integration
Receive real-time notifications for tenant events:
```json
{
    "event": "tenant.created",
    "tenant_id": 123,
    "timestamp": "2024-01-01T00:00:00Z",
    "data": {
        "tenant_key": "acme",
        "status": "active"
    }
}
```

### Custom Integrations
Build custom integrations using the extensible architecture:
```python
from services.tenant_context import require_tenant_context

@require_tenant_context
def custom_integration_endpoint():
    context = get_current_tenant_context()
    # Custom logic here
```

### Backup and Recovery
Tenant-specific backup and recovery procedures with point-in-time restoration.

## Conclusion

The EstateCore white-label multi-tenant architecture provides a comprehensive solution for partners and enterprises requiring branded property management platforms. With robust APIs, extensive customization options, and enterprise-grade security, it enables scalable deployment of tailored solutions while maintaining operational efficiency.

For additional support or custom requirements, contact the EstateCore development team.
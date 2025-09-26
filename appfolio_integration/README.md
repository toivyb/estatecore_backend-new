# AppFolio Integration for EstateCore

Comprehensive integration package for AppFolio Property Manager, Investment Manager, and related property management systems. This integration supports 7M+ units with enterprise-grade features designed for the small to mid-size property management market.

## Features

### Core Integration Capabilities
- **Property Manager Integration**: Complete property management core functionality
- **Investment Manager**: Real estate investment tracking and reporting
- **APM (AppFolio Property Manager)**: Advanced leasing and operations
- **Maintenance Management**: Work order and vendor management
- **Financial Integration**: Automated rent collection and expense tracking
- **Tenant Portal**: Resident communication and self-service
- **Vendor Management**: Contractor coordination and payments

### Data Synchronization
- **Bidirectional Sync**: Real-time data synchronization between EstateCore and AppFolio
- **Incremental Updates**: Efficient sync of only changed data
- **Conflict Resolution**: Intelligent handling of data conflicts
- **Batch Processing**: Large-scale data operations
- **Custom Field Mapping**: Flexible data transformation

### Enterprise Features
- **Multi-Property Portfolios**: Portfolio-level management and reporting
- **Role-Based Access Control (RBAC)**: Granular permission management
- **White-Label Configuration**: Customizable branding and interface
- **Custom Reporting**: Advanced reporting and analytics
- **Bulk Operations**: Mass data import/export and updates
- **Integration Health Monitoring**: Real-time health and performance tracking

### Real-Time Features
- **Webhook Notifications**: Instant event processing
- **Live Data Updates**: Real-time synchronization
- **Event-Driven Workflows**: Automated responses to AppFolio events
- **Performance Monitoring**: Comprehensive system monitoring

## Architecture

### Service Components

```
appfolio_integration/
├── __init__.py                      # Package initialization
├── appfolio_auth_service.py         # OAuth 2.0 authentication
├── appfolio_api_client.py          # API client and rate limiting
├── appfolio_mapping_service.py     # Data transformation and mapping
├── appfolio_sync_service.py        # Bidirectional synchronization
├── appfolio_webhook_service.py     # Real-time webhook processing
├── appfolio_enterprise_service.py  # Enterprise features (RBAC, portfolios)
├── appfolio_monitoring_service.py  # Health monitoring and alerts
├── appfolio_integration_service.py # Main coordination service
├── appfolio_routes.py              # Flask API routes
├── models.py                       # Data models
└── README.md                       # Documentation
```

### Key Services

1. **AppFolioAuthService**: Handles OAuth 2.0 authentication and token management
2. **AppFolioAPIClient**: Manages API requests with rate limiting and error handling
3. **AppFolioMappingService**: Transforms data between EstateCore and AppFolio formats
4. **AppFolioSyncService**: Orchestrates bidirectional data synchronization
5. **AppFolioWebhookService**: Processes real-time webhook events
6. **AppFolioEnterpriseService**: Provides advanced enterprise features
7. **AppFolioMonitoringService**: Monitors health and performance
8. **AppFolioIntegrationService**: Main service coordinating all components

## Installation

### Prerequisites
- Python 3.8+
- Flask
- Required dependencies (see requirements.txt)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export APPFOLIO_CLIENT_ID="your_client_id"
export APPFOLIO_CLIENT_SECRET="your_client_secret"
export APPFOLIO_REDIRECT_URI="https://your-domain.com/oauth/callback"
export APPFOLIO_ENVIRONMENT="sandbox"  # or "production"
export APPFOLIO_WEBHOOK_SECRET="your_webhook_secret"
export APPFOLIO_ENCRYPTION_KEY="your_encryption_key"
```

### Integration Setup
```python
from appfolio_integration import get_appfolio_integration_service
from appfolio_integration.appfolio_integration_service import IntegrationConfiguration
from appfolio_integration.appfolio_auth_service import AppFolioProductType

# Initialize service
service = get_appfolio_integration_service()

# Create integration configuration
config = IntegrationConfiguration(
    organization_id="org_123",
    integration_name="MyCompany AppFolio Integration",
    appfolio_products=[
        AppFolioProductType.PROPERTY_MANAGER,
        AppFolioProductType.INVESTMENT_MANAGER
    ],
    sync_enabled=True,
    real_time_sync=True,
    enterprise_features=True,
    webhook_enabled=True
)

# Create integration
result = service.create_integration("org_123", config)
```

## API Usage

### Authentication Flow

#### 1. Start OAuth Flow
```http
POST /api/v1/integrations/appfolio/connect
Content-Type: application/json

{
    "organization_id": "org_123",
    "product_types": ["property_manager", "investment_manager"],
    "custom_scopes": []
}
```

#### 2. Handle OAuth Callback
```http
POST /api/v1/integrations/appfolio/oauth/callback
Content-Type: application/json

{
    "code": "oauth_authorization_code",
    "state": "oauth_state_token"
}
```

### Data Synchronization

#### Full Synchronization
```http
POST /api/v1/integrations/appfolio/sync/full
Content-Type: application/json

{
    "organization_id": "org_123",
    "sync_direction": "both",
    "entity_types": ["properties", "units", "tenants", "leases"]
}
```

#### Incremental Synchronization
```http
POST /api/v1/integrations/appfolio/sync/incremental
Content-Type: application/json

{
    "organization_id": "org_123",
    "entity_types": ["payments", "work_orders"],
    "since_timestamp": "2024-01-01T00:00:00Z"
}
```

#### Check Sync Status
```http
GET /api/v1/integrations/appfolio/sync/status/org_123
GET /api/v1/integrations/appfolio/sync/status/org_123/job_123
```

### Health Monitoring

#### Integration Health
```http
GET /api/v1/integrations/appfolio/health/org_123?force_refresh=true
```

#### Integration Summary
```http
GET /api/v1/integrations/appfolio/summary/org_123
```

### Enterprise Features

#### Create Portfolio
```http
POST /api/v1/integrations/appfolio/enterprise/portfolios
Content-Type: application/json

{
    "organization_id": "org_123",
    "name": "Downtown Portfolio",
    "property_ids": ["prop_1", "prop_2", "prop_3"],
    "description": "Downtown commercial properties"
}
```

#### Generate Custom Report
```http
POST /api/v1/integrations/appfolio/enterprise/reports
Content-Type: application/json

{
    "organization_id": "org_123",
    "name": "Monthly Financial Summary",
    "type": "financial_summary",
    "data_sources": ["properties", "payments", "expenses"],
    "filters": {
        "date_range": {
            "start": "2024-01-01",
            "end": "2024-01-31"
        }
    }
}
```

## Data Models

### Core Entities

#### Property
```python
@dataclass
class AppFolioProperty:
    id: str
    name: str
    address: Dict[str, str]
    property_type: PropertyType
    unit_count: int
    portfolio_id: Optional[str] = None
    monthly_income: Optional[float] = None
    # ... additional fields
```

#### Unit
```python
@dataclass
class AppFolioUnit:
    id: str
    property_id: str
    unit_number: str
    unit_type: UnitType
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    rent_amount: Optional[float] = None
    # ... additional fields
```

#### Tenant
```python
@dataclass
class AppFolioTenant:
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    move_in_date: Optional[date] = None
    # ... additional fields
```

### Financial Entities

#### Payment
```python
@dataclass
class AppFolioPayment:
    id: str
    tenant_id: str
    amount: float
    payment_date: date
    payment_method: str
    status: PaymentStatus
    # ... additional fields
```

#### Work Order
```python
@dataclass
class AppFolioWorkOrder:
    id: str
    property_id: str
    title: str
    description: str
    status: WorkOrderStatus
    priority: WorkOrderPriority
    # ... additional fields
```

## Configuration

### Environment Variables
```bash
# Required
APPFOLIO_CLIENT_ID=your_client_id
APPFOLIO_CLIENT_SECRET=your_client_secret
APPFOLIO_REDIRECT_URI=https://your-domain.com/oauth/callback

# Optional
APPFOLIO_ENVIRONMENT=sandbox
APPFOLIO_WEBHOOK_SECRET=your_webhook_secret
APPFOLIO_ENCRYPTION_KEY=your_encryption_key
```

### Integration Configuration
```python
config = IntegrationConfiguration(
    organization_id="org_123",
    integration_name="My Integration",
    appfolio_products=[AppFolioProductType.PROPERTY_MANAGER],
    sync_enabled=True,
    real_time_sync=True,
    batch_sync_schedule="0 2 * * *",  # Daily at 2 AM
    auto_conflict_resolution=True,
    data_quality_checks=True,
    enterprise_features=True,
    webhook_enabled=True,
    sync_entities=["properties", "units", "tenants", "leases"],
    excluded_entities=["documents"],
    incremental_sync=True,
    max_retry_attempts=3,
    timeout_seconds=300,
    rate_limit_requests_per_minute=100
)
```

## Webhooks

### Setup Webhooks
```python
# Setup webhook subscriptions
result = webhook_service.setup_organization_webhooks(
    organization_id="org_123",
    event_types=[
        WebhookEventType.PROPERTY_UPDATED,
        WebhookEventType.TENANT_CREATED,
        WebhookEventType.PAYMENT_PROCESSED,
        WebhookEventType.WORK_ORDER_COMPLETED
    ]
)
```

### Webhook Events
The integration supports various webhook events:
- Property events: `property.created`, `property.updated`, `property.deleted`
- Unit events: `unit.created`, `unit.updated`, `unit.deleted`
- Tenant events: `tenant.created`, `tenant.updated`, `tenant.deleted`
- Lease events: `lease.created`, `lease.updated`, `lease.expired`
- Payment events: `payment.created`, `payment.processed`, `payment.failed`
- Work order events: `work_order.created`, `work_order.updated`, `work_order.completed`

### Webhook Endpoint
```
POST /webhooks/appfolio/{organization_id}
```

## Error Handling

### Common Error Codes
- `400`: Bad Request - Invalid input parameters
- `401`: Unauthorized - Invalid or expired authentication
- `403`: Forbidden - Insufficient permissions
- `404`: Not Found - Resource not found
- `429`: Too Many Requests - Rate limit exceeded
- `500`: Internal Server Error - Server-side error
- `502`: Bad Gateway - Upstream service error
- `503`: Service Unavailable - Service temporarily unavailable

### Error Response Format
```json
{
    "error": "Error message",
    "error_code": "ERROR_CODE",
    "details": {
        "field": "Additional error details"
    },
    "request_id": "req_123456789"
}
```

## Performance and Monitoring

### Metrics Tracked
- API response times
- Request success/failure rates
- Sync job completion rates
- Data quality scores
- System resource usage
- Webhook delivery success rates

### Health Checks
- AppFolio API connectivity
- Database connectivity
- Webhook endpoint availability
- System resource usage
- Sync service health

### Alerts
- High error rates
- Slow response times
- Sync failures
- System resource exhaustion
- Webhook delivery failures

## Security

### Authentication
- OAuth 2.0 with PKCE support
- Secure token storage with encryption
- Automatic token refresh
- Token revocation support

### Data Protection
- End-to-end encryption for sensitive data
- Secure webhook signature verification
- Rate limiting and DDoS protection
- Audit logging for all operations

### Access Control
- Role-based access control (RBAC)
- Fine-grained permissions
- Organization-level isolation
- User session management

## Troubleshooting

### Common Issues

#### Connection Issues
```python
# Test connection
result = service.get_connection_status("org_123")
if not result["connected"]:
    # Check credentials and re-authenticate
    auth_result = service.connect_to_appfolio("org_123", [AppFolioProductType.PROPERTY_MANAGER])
```

#### Sync Issues
```python
# Check sync status
sync_status = service.get_sync_status("org_123")
if sync_status["active_jobs"]:
    # Monitor active jobs
    for job in sync_status["active_jobs"]:
        progress = service.get_sync_progress(job["job_id"])
```

#### Data Quality Issues
```python
# Check data quality
health = service.get_integration_health("org_123")
if health.data_quality_score < 90:
    # Review conflicts and errors
    conflicts = sync_service.get_conflict_records("org_123", resolved=False)
```

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('appfolio_integration')
```

### Debug Mode
```python
# Enable detailed logging
service.api_client.debug_mode = True
service.sync_service.debug_mode = True
```

## Support

### Documentation
- API Reference: `/api/v1/integrations/appfolio/docs`
- Webhook Documentation: See webhook service documentation
- Error Codes: See error handling section

### Contact
- Technical Support: EstateCore Development Team
- Integration Issues: Submit GitHub issue
- Feature Requests: Submit GitHub feature request

## License
This integration is part of the EstateCore platform and follows the same licensing terms.

## Changelog

### Version 1.0.0
- Initial release
- Complete AppFolio Property Manager integration
- Investment Manager support
- Enterprise features (portfolios, RBAC, custom reports)
- Real-time webhooks
- Comprehensive monitoring and health checks
- Bidirectional data synchronization
- White-label configuration support
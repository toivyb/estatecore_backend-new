# RealPage Integration for EstateCore

## Overview

The RealPage Integration module provides comprehensive connectivity with RealPage's suite of property management products, enabling seamless data synchronization, revenue management, and operational workflow automation for enterprise property management portfolios.

## Supported Products

### Core Platforms
- **OneSite** - Property management platform
- **LeasingDesk** - Leasing and marketing
- **YieldStar** - Revenue management and pricing
- **Velocity** - Resident screening and leasing
- **ActiveBuilding** - Operations management
- **CrossFire** - Maintenance and service requests
- **RealPage Analytics** - Business intelligence

## Key Features

### 1. Multi-Product Authentication
- OAuth 2.0 authentication with RealPage
- Secure credential management and token refresh
- Multi-tenant support for enterprise portfolios
- Role-based access control

### 2. Comprehensive Data Synchronization
- **Property Portfolio Management**
  - Property and building information
  - Unit inventory and availability
  - Floor plans and amenities
  - Market positioning data

- **Resident and Leasing Data**
  - Tenant/resident profiles and applications
  - Lease agreements and renewals
  - Screening results and credit reports
  - Move-in/move-out workflows

- **Financial Operations**
  - Rent rolls and payment processing
  - Revenue forecasting and budgeting
  - Concession management
  - Late fee processing and collections

- **Maintenance and Operations**
  - Work order management
  - Vendor coordination
  - Asset tracking and preventive maintenance
  - Service request automation

### 3. Revenue Management Integration
- **YieldStar Pricing Intelligence**
  - Market rent analysis and recommendations
  - Competitive pricing data
  - Lease pricing optimization algorithms
  - Renewal pricing strategies

- **Performance Analytics**
  - Occupancy forecasting
  - Revenue optimization reporting
  - Market benchmarking
  - Lease conversion analytics

### 4. Real-Time Capabilities
- Webhook notifications for instant updates
- Real-time pricing adjustments
- Immediate lead and application processing
- Live availability updates

### 5. Enterprise Features
- Multi-property portfolio support
- Custom field mapping and transformations
- Advanced conflict resolution
- Data quality monitoring and validation
- Comprehensive audit trails

## Architecture

### Service Components

1. **RealPageIntegrationService** - Main orchestration service
2. **RealPageAuthService** - Authentication and connection management
3. **RealPageAPIClient** - API communication layer
4. **RealPageSyncService** - Data synchronization engine
5. **RealPageMappingService** - Data transformation and mapping
6. **RealPageRevenueService** - Revenue management integration
7. **RealPageWebhookService** - Real-time notification handling
8. **RealPageSchedulerService** - Automated workflow scheduling
9. **RealPageMonitoringService** - Health monitoring and analytics

### Integration Patterns

- **Circuit Breaker** - Resilient API communication
- **Rate Limiting** - API quota management
- **Retry Logic** - Automatic error recovery
- **Conflict Resolution** - Data synchronization conflict handling
- **Event-Driven Architecture** - Real-time data processing

## Configuration

### Environment Variables
```bash
# RealPage API Configuration
REALPAGE_CLIENT_ID=your_client_id
REALPAGE_CLIENT_SECRET=your_client_secret
REALPAGE_REDIRECT_URI=https://your-domain.com/auth/realpage/callback
REALPAGE_ENVIRONMENT=production  # or sandbox

# Product-Specific Endpoints
REALPAGE_ONESITE_API_URL=https://api.realpage.com/onesite/v1
REALPAGE_YIELDSTAR_API_URL=https://api.realpage.com/yieldstar/v1
REALPAGE_VELOCITY_API_URL=https://api.realpage.com/velocity/v1

# Integration Settings
REALPAGE_SYNC_INTERVAL=300  # 5 minutes
REALPAGE_WEBHOOK_SECRET=your_webhook_secret
REALPAGE_RATE_LIMIT=1000  # requests per hour
```

### Database Configuration
The integration requires database tables for storing connection credentials, sync jobs, mappings, and audit logs. Run the migration scripts in the `/migrations` folder.

## Usage Examples

### Basic Setup
```python
from realpage_integration import get_realpage_integration_service

# Get integration service
service = get_realpage_integration_service()

# Create integration for organization
config = IntegrationConfiguration(
    organization_id="org123",
    integration_name="Main Portfolio",
    realpage_products=[
        RealPageProductType.ONESITE,
        RealPageProductType.YIELDSTAR,
        RealPageProductType.VELOCITY
    ],
    sync_enabled=True,
    real_time_sync=True
)

result = service.create_integration("org123", config)
```

### Connect to RealPage
```python
# Start OAuth flow
auth_result = service.start_oauth_flow("org123")
# Redirect user to auth_result['authorization_url']

# Complete OAuth after callback
connection_result = service.complete_oauth_flow(
    code="auth_code",
    state="oauth_state",
    organization_id="org123"
)
```

### Data Synchronization
```python
# Full portfolio sync
sync_result = await service.sync_full_portfolio("org123")

# Incremental sync
incremental_result = await service.sync_incremental_data(
    "org123", 
    entity_types=["properties", "units", "leases"]
)

# Real-time pricing sync
pricing_result = await service.sync_yieldstar_pricing("org123")
```

### Revenue Management
```python
# Get pricing recommendations
pricing_recs = service.get_pricing_recommendations(
    "org123",
    property_id="prop123",
    unit_type="1br1ba"
)

# Apply pricing optimization
optimization_result = service.apply_pricing_optimization(
    "org123",
    recommendations=pricing_recs
)
```

## API Gateway Integration

The RealPage integration is fully integrated with EstateCore's API Gateway, providing:

- Centralized authentication and authorization
- Rate limiting and quota management
- Request/response transformation
- Comprehensive monitoring and analytics
- Webhook delivery management

## Monitoring and Health Checks

### Health Status Monitoring
```python
# Get integration health
health = service.get_integration_health("org123")
print(f"Status: {health.status}")
print(f"Data Quality Score: {health.data_quality_score}")
print(f"Uptime: {health.uptime_percentage}%")
```

### Performance Metrics
- API response times
- Sync job success rates
- Data quality scores
- Error rates and patterns
- Resource utilization

## Error Handling and Recovery

### Automatic Recovery
- Connection retry with exponential backoff
- Token refresh automation
- Circuit breaker protection
- Graceful degradation

### Manual Intervention
- Conflict resolution workflows
- Data validation and correction
- Manual sync triggers
- Emergency disconnect procedures

## Security

### Data Protection
- End-to-end encryption in transit
- Secure credential storage
- Access logging and auditing
- GDPR and compliance support

### Access Control
- Role-based permissions
- API key management
- Organization-level isolation
- Audit trail maintenance

## Testing

### Unit Tests
Run the test suite with:
```bash
python -m pytest realpage_integration/tests/
```

### Integration Tests
Test against RealPage sandbox:
```bash
python -m pytest realpage_integration/tests/integration/
```

### Load Testing
Performance testing:
```bash
python -m pytest realpage_integration/tests/load/
```

## Deployment

### Production Deployment
1. Configure environment variables
2. Run database migrations
3. Deploy integration services
4. Configure API Gateway routes
5. Setup monitoring dashboards

### Scaling Considerations
- Horizontal scaling for sync services
- Database connection pooling
- Redis for caching and rate limiting
- Load balancer configuration

## Support

For technical support and questions:
- Email: dev@estatecore.com
- Documentation: https://docs.estatecore.com/integrations/realpage
- Issues: Create tickets in the EstateCore support system

## License

This integration is part of the EstateCore platform and is subject to the EstateCore Enterprise License Agreement.
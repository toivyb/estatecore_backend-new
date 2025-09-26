# EstateCore Yardi Integration

A comprehensive, enterprise-grade integration solution for connecting EstateCore with Yardi property management systems including Yardi Voyager, Yardi Breeze, Genesis2, and other Yardi products.

## Overview

This integration provides seamless bidirectional data synchronization between EstateCore and Yardi systems, enabling enterprise customers to maintain their existing Yardi workflows while leveraging EstateCore's advanced features like AI analytics, IoT monitoring, and modern tenant portals.

## Features

### Core Integration Capabilities
- **Multiple Yardi Product Support**: Voyager, Breeze, Genesis2, RentCafe, MaintenanceCafe
- **Bidirectional Synchronization**: Real-time and batch data sync between systems
- **Advanced Authentication**: OAuth2, API keys, certificate-based authentication
- **Conflict Resolution**: Intelligent conflict detection and resolution strategies
- **Data Transformation**: Flexible field mapping and data transformation engine

### Enterprise Features
- **Multi-Property Portfolio Management**: Centralized management of property portfolios
- **Role-Based Access Control**: Granular permissions and access management
- **Custom Reporting**: Advanced reporting and analytics capabilities
- **White-Label Configuration**: Enterprise client customization options
- **Audit Trails**: Comprehensive logging and compliance tracking

### Data Synchronization
- **Property and Building Information**: Complete property data sync
- **Unit Details and Availability**: Real-time unit status and availability
- **Tenant/Resident Management**: Comprehensive tenant data synchronization
- **Lease Agreements**: Lease terms, renewals, and documentation
- **Payment Processing**: Rent rolls, payment history, and financial data
- **Maintenance Operations**: Work orders, vendor management, and scheduling
- **Financial Data**: Chart of accounts, general ledger, and reporting

### Advanced Capabilities
- **Real-Time Webhooks**: Instant notifications from Yardi systems
- **Scheduled Synchronization**: Automated sync jobs with flexible scheduling
- **Data Quality Monitoring**: Validation, quality checks, and integrity scoring
- **Performance Analytics**: Comprehensive monitoring and alerting
- **Error Handling**: Robust retry mechanisms and error recovery
- **Incremental Sync**: Efficient delta synchronization for performance

## Installation

### Prerequisites
- Python 3.8+
- EstateCore system installed and configured
- Access to Yardi system with appropriate API credentials
- Database access for storing integration configuration

### Quick Installation

1. **Install the integration module**:
   ```bash
   cd /path/to/estatecore_project
   python yardi_integration/setup.py
   ```

2. **Configure your Yardi connection**:
   ```bash
   # Edit the configuration file
   vim yardi_config.json
   ```

3. **Test the integration**:
   ```bash
   python -m yardi_integration.test_connection
   ```

### Manual Installation

1. **Install dependencies**:
   ```bash
   pip install -r yardi_integration/requirements.txt
   ```

2. **Setup database tables**:
   ```sql
   -- Execute the SQL statements from setup.py output
   ```

3. **Configure encryption**:
   ```bash
   python -c "from yardi_integration.setup import YardiIntegrationSetup; YardiIntegrationSetup().setup_encryption()"
   ```

## Configuration

### Basic Configuration

Create a `yardi_config.json` file with your Yardi system details:

```json
{
  "yardi_products": {
    "voyager": {
      "enabled": true,
      "base_url": "https://your-yardi-instance.com",
      "api_version": "1.0",
      "auth_method": "api_key",
      "credentials": {
        "api_key": "your-api-key",
        "client_id": "your-client-id"
      }
    }
  },
  "sync_configuration": {
    "default_batch_size": 100,
    "enable_real_time": true,
    "entity_types": ["properties", "units", "tenants", "leases", "payments"]
  }
}
```

### Enterprise Configuration

For enterprise deployments with multiple properties:

```json
{
  "enterprise": {
    "multi_property_enabled": true,
    "portfolios": [
      {
        "portfolio_name": "Downtown Properties",
        "properties": ["prop_001", "prop_002", "prop_003"],
        "consolidated_reporting": true
      }
    ],
    "role_based_access": true,
    "custom_branding": {
      "company_name": "Your Company",
      "logo_url": "https://yourcompany.com/logo.png"
    }
  }
}
```

## API Usage

### Creating an Integration

```python
from yardi_integration import get_yardi_integration_service, IntegrationConfiguration
from yardi_integration.models import YardiProductType, YardiConnectionType

# Initialize the service
yardi_service = get_yardi_integration_service()

# Create integration configuration
config = IntegrationConfiguration(
    organization_id="your_org_id",
    integration_name="Main Yardi Integration",
    yardi_product=YardiProductType.VOYAGER,
    connection_type=YardiConnectionType.API,
    sync_enabled=True,
    real_time_sync=True,
    webhook_enabled=True
)

# Create the integration
result = yardi_service.create_integration("your_org_id", config)
```

### Connecting to Yardi

```python
# Connection parameters
connection_params = {
    'base_url': 'https://your-yardi-instance.com',
    'credentials': {
        'api_key': 'your-api-key',
        'client_id': 'your-client-id'
    },
    'connection_name': 'Yardi Production',
    'is_sandbox': False
}

# Establish connection
result = yardi_service.connect_to_yardi("your_org_id", connection_params)
```

### Starting Synchronization

```python
# Full synchronization
result = await yardi_service.start_full_sync(
    organization_id="your_org_id",
    sync_direction="both",  # 'to_yardi', 'from_yardi', or 'both'
    entity_types=["properties", "units", "tenants", "leases"]
)

# Incremental synchronization
result = await yardi_service.start_incremental_sync(
    organization_id="your_org_id",
    entity_types=["payments", "maintenance"],
    since_timestamp=datetime.utcnow() - timedelta(hours=24)
)
```

## REST API Endpoints

### Connection Management

```bash
# Create integration
POST /api/yardi/integrations
{
  "integration_name": "Main Yardi Integration",
  "yardi_product": "voyager",
  "connection_type": "api"
}

# Connect to Yardi
POST /api/yardi/integrations/{org_id}/connect
{
  "base_url": "https://your-yardi-instance.com",
  "credentials": {"api_key": "your-key"}
}

# Get connection status
GET /api/yardi/integrations/{org_id}/status

# Disconnect
POST /api/yardi/integrations/{org_id}/disconnect
```

### Synchronization

```bash
# Start full sync
POST /api/yardi/sync/{org_id}/full
{
  "sync_direction": "both",
  "entity_types": ["properties", "units", "tenants"]
}

# Start incremental sync
POST /api/yardi/sync/{org_id}/incremental
{
  "entity_types": ["payments"],
  "since_timestamp": "2023-10-01T00:00:00Z"
}

# Get sync status
GET /api/yardi/sync/{org_id}/status?job_id={job_id}

# Cancel sync job
POST /api/yardi/sync/jobs/{job_id}/cancel
```

### Monitoring and Health

```bash
# Get integration health
GET /api/yardi/integrations/{org_id}/health

# Get performance metrics
GET /api/yardi/integrations/{org_id}/metrics?time_range=24h

# Get integration summary
GET /api/yardi/integrations/{org_id}/summary
```

## Data Mapping

### Field Mapping Configuration

Configure how data fields map between EstateCore and Yardi:

```python
from yardi_integration.yardi_mapping_service import YardiMappingService
from yardi_integration.models import YardiEntityType, YardiProductType

mapping_service = YardiMappingService()

# Create property mapping
property_mappings = [
    {
        'source_field': 'name',
        'target_field': 'PropertyName',
        'transformation_type': 'direct_map',
        'data_type': 'string',
        'required': True
    },
    {
        'source_field': 'rent_amount',
        'target_field': 'MarketRent',
        'transformation_type': 'currency_to_cents',
        'data_type': 'float'
    }
]

mapping_service.create_entity_mapping(
    organization_id="your_org_id",
    entity_type=YardiEntityType.PROPERTIES,
    yardi_product=YardiProductType.VOYAGER,
    field_mappings=property_mappings
)
```

### Custom Transformations

```python
# Register custom transformation function
def custom_phone_formatter(value, config):
    # Custom phone number formatting logic
    return formatted_phone

mapping_service.register_custom_transformer(
    'custom_phone_format', 
    custom_phone_formatter
)
```

## Scheduling and Automation

### Creating Scheduled Jobs

```python
from yardi_integration.yardi_scheduler_service import YardiSchedulerService

scheduler = YardiSchedulerService(sync_service)

# Create daily sync schedule
schedule_config = {
    'job_name': 'Daily Full Sync',
    'schedule_type': 'cron',
    'cron_expression': '0 2 * * *',  # 2 AM daily
    'sync_direction': 'both',
    'entity_types': ['properties', 'units', 'tenants'],
    'notify_on_failure': True,
    'notification_emails': ['admin@yourcompany.com']
}

result = scheduler.create_schedule("your_org_id", schedule_config)
```

### REST API for Scheduling

```bash
# Create schedule
POST /api/yardi/schedules/{org_id}
{
  "job_name": "Hourly Payment Sync",
  "schedule_type": "interval",
  "interval_minutes": 60,
  "sync_direction": "from_yardi",
  "entity_types": ["payments"]
}

# List schedules
GET /api/yardi/schedules/{org_id}

# Update schedule
PUT /api/yardi/schedules/{schedule_id}

# Pause/Resume schedule
POST /api/yardi/schedules/{schedule_id}/pause
POST /api/yardi/schedules/{schedule_id}/resume
```

## Enterprise Features

### Multi-Property Portfolio Management

```python
from yardi_integration.yardi_enterprise_service import YardiEnterpriseService

enterprise_service = YardiEnterpriseService(api_client, sync_service, mapping_service)

# Create property portfolio
portfolio = enterprise_service.create_property_portfolio(
    organization_id="your_org_id",
    portfolio_name="Downtown Properties",
    properties=["prop_001", "prop_002", "prop_003"],
    consolidated_reporting=True
)

# Setup accounting structure for portfolio
setup_result = enterprise_service.setup_portfolio_accounting(
    portfolio.portfolio_id, 
    connection_id
)
```

### Custom Reporting

```python
from yardi_integration.yardi_enterprise_service import ReportType

# Create custom financial report
report = enterprise_service.create_custom_report(
    organization_id="your_org_id",
    report_name="Monthly Financial Summary",
    report_type=ReportType.FINANCIAL_SUMMARY,
    data_sources=["rent_rolls", "expenses", "payments"],
    filters={"property_portfolio": portfolio.portfolio_id}
)

# Generate report
result = enterprise_service.generate_custom_report(
    report_id=report.report_id,
    date_range={"start_date": "2023-10-01", "end_date": "2023-10-31"}
)
```

## Webhook Configuration

### Setting Up Webhooks

```python
from yardi_integration.yardi_webhook_service import YardiWebhookService, WebhookEventType

webhook_service = YardiWebhookService(sync_service)

# Setup webhooks for organization
result = webhook_service.setup_organization_webhooks(
    organization_id="your_org_id",
    yardi_product=YardiProductType.VOYAGER
)

# Register custom event handler
async def handle_payment_received(event):
    # Custom logic for payment events
    print(f"Payment received: {event.event_data}")

webhook_service.register_handler(
    WebhookEventType.PAYMENT_RECEIVED, 
    handle_payment_received
)
```

### Webhook Endpoint

Yardi systems will send webhooks to:
```
POST /api/yardi/webhooks/{organization_id}
```

## Monitoring and Alerting

### Health Monitoring

```python
from yardi_integration.yardi_monitoring_service import YardiMonitoringService

monitoring_service = YardiMonitoringService()

# Get integration health
health = yardi_service.get_integration_health("your_org_id")

print(f"Status: {health.status}")
print(f"Data Quality Score: {health.data_quality_score}")
print(f"Uptime: {health.uptime_percentage}%")
```

### Performance Metrics

```bash
# Get performance metrics via API
GET /api/yardi/integrations/{org_id}/metrics?time_range=7d

# Response includes:
{
  "api_response_time": {"avg": 120.5, "p95": 250.0},
  "error_rate": 1.2,
  "sync_performance": {"avg_duration": 45.2},
  "uptime_percentage": 99.8
}
```

### Custom Alerts

```python
# Create custom alert rule
alert_config = {
    'rule_name': 'High Sync Failure Rate',
    'condition': 'sync_failure_rate > 10%',
    'severity': 'error',
    'notification_channels': ['email', 'slack'],
    'cooldown_minutes': 30
}

monitoring_service.create_alert_rule("your_org_id", alert_config)
```

## Troubleshooting

### Common Issues

1. **Connection Failures**
   ```bash
   # Test connection
   GET /api/yardi/integrations/{org_id}/status
   
   # Check logs
   tail -f /var/log/estatecore/yardi_integration.log
   ```

2. **Sync Failures**
   ```bash
   # Get sync job details
   GET /api/yardi/sync/{org_id}/status?job_id={job_id}
   
   # Review error details
   GET /api/yardi/integrations/{org_id}/health
   ```

3. **Performance Issues**
   ```bash
   # Check performance metrics
   GET /api/yardi/integrations/{org_id}/metrics
   
   # Review system health
   GET /api/yardi/system/health
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('yardi_integration').setLevel(logging.DEBUG)
```

### Data Quality Issues

```python
# Check data quality score
health = yardi_service.get_integration_health("your_org_id")
if health.data_quality_score < 90:
    print("Data quality issues detected:")
    for issue in health.issues:
        print(f"  - {issue}")
```

## Security Considerations

### Credential Management
- All credentials are encrypted at rest using Fernet encryption
- Support for certificate-based authentication
- OAuth2 token refresh and management
- API key rotation capabilities

### Network Security
- HTTPS/TLS required for all API communications
- Webhook signature validation
- IP whitelisting support
- Rate limiting and DDoS protection

### Access Control
- Role-based permissions system
- Organization-level data isolation
- Audit logging for all operations
- Session management and timeout

## Performance Optimization

### Sync Performance
- Batch processing for large datasets
- Parallel worker configuration
- Incremental sync for efficiency
- Connection pooling and reuse

### Monitoring
- Real-time performance metrics
- Automatic performance tuning
- Resource usage monitoring
- Capacity planning alerts

### Caching
- Response caching for read operations
- Connection state caching
- Field mapping cache
- Metadata caching

## Support and Maintenance

### Logging
All integration activities are logged with different levels:
- `INFO`: Normal operations and status updates
- `WARNING`: Non-critical issues and recoverable errors
- `ERROR`: Sync failures and connection issues
- `CRITICAL`: System failures requiring immediate attention

### Updates
- Automatic schema migration support
- Backward compatibility maintenance
- Version management
- Update notifications

### Backup and Recovery
- Configuration backup and restore
- Data mapping export/import
- Connection state recovery
- Disaster recovery procedures

## Contributing

### Development Setup
1. Clone the repository
2. Install development dependencies: `pip install -r requirements-dev.txt`
3. Run tests: `pytest yardi_integration/tests/`
4. Follow coding standards and submit pull requests

### Testing
- Unit tests for all components
- Integration tests with mock Yardi responses
- Performance testing with load simulation
- End-to-end testing scenarios

## License

This Yardi integration is part of the EstateCore system and is subject to the EstateCore licensing terms.

## Contact

For support, questions, or enterprise licensing:
- Email: support@estatecore.com
- Documentation: https://docs.estatecore.com/yardi-integration
- Issues: https://github.com/estatecore/yardi-integration/issues
# QuickBooks Online Integration for EstateCore

A comprehensive enterprise-grade QuickBooks Online integration for automated accounting and financial management in property management workflows.

## 🚀 Features

### Core Integration
- **OAuth 2.0 Authentication**: Secure QuickBooks Online connection with token management
- **Complete API Coverage**: Full CRUD operations for all QuickBooks entities
- **Bidirectional Sync**: Real-time data synchronization between EstateCore and QuickBooks
- **Automated Workflows**: Intelligent automation for rent invoices, payments, and expenses

### Financial Data Management
- **Rent Payment Automation**: Automatic invoice generation and payment tracking
- **Expense Management**: Categorized expense sync with property-based allocation
- **Security Deposits**: Proper handling of deposits and refunds
- **Late Fee Processing**: Automated late fee assessment and tracking
- **Multi-Property Support**: Separate accounting for different properties

### Enterprise Features
- **Portfolio Management**: Multi-property portfolio support with consolidated reporting
- **Role-Based Access**: Granular permissions for different user roles
- **White-Label Support**: Custom branding for enterprise clients
- **Custom Reports**: Configurable financial reports and analytics
- **Audit Trail**: Comprehensive logging of all operations
- **Data Quality**: Advanced reconciliation and error detection

### Integration & Monitoring
- **API Gateway Integration**: Enterprise-grade API management
- **Rate Limiting**: Intelligent request throttling and quota management
- **Error Handling**: Robust error recovery and retry mechanisms
- **Health Monitoring**: Real-time integration health monitoring
- **Webhooks**: Event-driven notifications for critical events

## 📋 Prerequisites

- Python 3.8+
- QuickBooks Online Developer Account
- Valid SSL certificate for OAuth callbacks
- PostgreSQL or SQLite database
- Redis (optional, for caching)

## 🛠️ Installation

### 1. Install Dependencies

```bash
pip install requests cryptography flask
pip install -r requirements.txt
```

### 2. QuickBooks Developer Setup

1. Create a QuickBooks Developer account at [developer.intuit.com](https://developer.intuit.com)
2. Create a new app and obtain your Client ID and Client Secret
3. Configure OAuth redirect URIs
4. Note your sandbox/production base URLs

### 3. Environment Configuration

Create a `.env` file with your QuickBooks credentials:

```bash
# QuickBooks OAuth Configuration
QUICKBOOKS_CLIENT_ID=your_client_id
QUICKBOOKS_CLIENT_SECRET=your_client_secret
QUICKBOOKS_REDIRECT_URI=https://yourdomain.com/api/quickbooks/oauth/callback
QUICKBOOKS_BASE_URL=https://sandbox-quickbooks.api.intuit.com
QUICKBOOKS_DISCOVERY_URL=https://appcenter.intuit.com/api/v1/OpenID_sandbox

# Encryption for token storage
QUICKBOOKS_ENCRYPTION_KEY=your_encryption_key_base64

# Database
DATABASE_URL=postgresql://user:pass@localhost/estatecore

# API Gateway (optional)
API_GATEWAY_ENABLED=true
```

### 4. Database Setup

The integration uses the existing EstateCore database with additional tables for QuickBooks data:

```bash
# Run database migrations
python -c "from quickbooks_integration import setup_database; setup_database()"
```

## 🔧 Configuration

### Basic Setup

```python
from quickbooks_integration import QuickBooksIntegrationService

# Initialize the service
qb_service = QuickBooksIntegrationService()

# Start OAuth flow
auth_result = qb_service.start_oauth_flow("organization_id")
print(f"Redirect user to: {auth_result['authorization_url']}")
```

### Flask Integration

```python
from flask import Flask
from quickbooks_integration.quickbooks_routes import register_quickbooks_routes
from quickbooks_integration.api_gateway_integration import setup_quickbooks_api_gateway_integration

app = Flask(__name__)

# Register QuickBooks routes
register_quickbooks_routes(app)

# Setup API Gateway integration (optional)
setup_quickbooks_api_gateway_integration(app)
```

## 🔑 Authentication Flow

### 1. Initiate Connection

```python
# Start OAuth flow
result = qb_service.start_oauth_flow("org_123")

if result['success']:
    # Redirect user to QuickBooks
    redirect_url = result['authorization_url']
```

### 2. Handle OAuth Callback

```python
# In your OAuth callback handler
result = qb_service.complete_oauth_flow(
    code="authorization_code",
    state="oauth_state", 
    realm_id="company_id"
)

if result['success']:
    print(f"Connected to {result['company_name']}")
```

### 3. Check Connection Status

```python
status = qb_service.get_connection_status("org_123")
print(f"Connected: {status['connected']}")
print(f"Company: {status['company_name']}")
```

## 📊 Data Synchronization

### Automatic Sync

```python
# Enable automated workflows
result = qb_service.enable_automation("org_123", [
    "rent_invoice_generation",
    "payment_sync", 
    "late_fee_processing"
])
```

### Manual Sync

```python
# Sync all data
import asyncio

result = asyncio.run(qb_service.sync_all_data("org_123", direction="both"))
print(f"Synced {result['results']['successful_records']} records")

# Sync specific entities
result = qb_service.sync_entity_manual("org_123", "tenants", tenant_data)
```

### Sync Configuration

```python
# Configure sync settings
qb_service.sync_service.update_sync_configuration("org_123", {
    "auto_sync_enabled": True,
    "sync_interval_minutes": 15,
    "conflict_resolution": "timestamp_based",
    "batch_size": 50
})
```

## 🏢 Enterprise Features

### Multi-Property Portfolio

```python
# Create property portfolio
result = qb_service.setup_multi_property(
    organization_id="org_123",
    portfolio_name="Downtown Properties",
    properties=["prop_1", "prop_2", "prop_3"]
)
```

### Custom Reports

```python
# Create custom financial report
result = qb_service.create_custom_report(
    organization_id="org_123",
    report_name="Monthly P&L by Property",
    report_type="profit_loss",
    parameters={"grouping": "property", "period": "monthly"}
)

# Generate report
report_data = qb_service.generate_report(
    report_id=result['report_id'],
    date_range={"start": "2024-01-01", "end": "2024-01-31"}
)
```

### Role-Based Access

```python
# Configure user access
qb_service.enterprise_service.create_user_access(
    user_id="user_123",
    organization_id="org_123", 
    access_level="advanced",
    allowed_properties=["prop_1", "prop_2"],
    allowed_features=["sync", "reports", "automation"]
)
```

## 📈 Monitoring & Analytics

### Health Monitoring

```python
# Get integration health
health = qb_service.get_integration_health("org_123")
print(f"Status: {health.status}")
print(f"Data Quality: {health.data_quality['integrity_score']}%")
print(f"Issues: {health.issues}")
```

### Data Quality

```python
# Run reconciliation
result = qb_service.perform_reconciliation("org_123", period_days=30)
print(f"Found {result['reconciliation_report']['discrepancies_found']} discrepancies")

# Get data quality score
quality = qb_service.get_data_quality_score("org_123")
print(f"Integrity Score: {quality['data_quality']['integrity_score']}%")
```

### Audit Trail

```python
# Get audit logs
audit_logs = qb_service.get_audit_trail("org_123", limit=100)
for log in audit_logs['audit_logs']:
    print(f"{log['timestamp']}: {log['operation_type']} {log['entity_type']}")
```

## 🔧 Account Mapping

### Property Account Setup

```python
# Map property to QuickBooks accounts
from quickbooks_integration.quickbooks_routes import create_property_mapping

mapping = create_property_mapping(
    property_id="prop_123",
    property_name="Downtown Apartments",
    revenue_account_id="4000",  # Rental Income
    expense_account_id="6000",  # Property Expenses
    deposit_account_id="1200",  # Security Deposits
    ar_account_id="1300"        # Accounts Receivable
)
```

### Custom Field Mapping

```python
# Customize data mapping
from quickbooks_integration.data_mapping_service import get_data_mapping_service

mapping_service = get_data_mapping_service()

# Add custom transformation
def custom_tenant_name(data):
    return f"{data['first_name']} {data['last_name']} - {data['property_name']}"

mapping_service.add_custom_transformation("custom_tenant_name", custom_tenant_name)
```

## 🔒 Security & Compliance

### Token Security

- All tokens are encrypted using AES-256 encryption
- Automatic token refresh before expiration
- Secure token storage with configurable encryption keys

### Access Control

- Role-based permissions for QuickBooks features
- IP address whitelisting support
- API key scoping and rate limiting

### Audit Compliance

- Complete audit trail of all operations
- Immutable transaction logs
- Data integrity verification

## 🧪 Testing

### Run Tests

```bash
# Run all tests
python -m pytest quickbooks_integration/tests/ -v

# Run specific test categories
python -m pytest quickbooks_integration/tests/test_quickbooks_integration.py::TestQuickBooksOAuthService -v

# Run with coverage
python -m pytest quickbooks_integration/tests/ --cov=quickbooks_integration --cov-report=html
```

### Test with Sandbox

```python
# Use QuickBooks Sandbox for testing
from quickbooks_integration.quickbooks_oauth_service import OAuthConfig

config = OAuthConfig(
    client_id="sandbox_client_id",
    client_secret="sandbox_client_secret", 
    redirect_uri="http://localhost:5000/test/callback",
    scope=["com.intuit.quickbooks.accounting"],
    base_url="https://sandbox-quickbooks.api.intuit.com"
)
```

## 🚀 Deployment

### Production Configuration

```python
# Production settings
QUICKBOOKS_BASE_URL=https://quickbooks.api.intuit.com
QUICKBOOKS_DISCOVERY_URL=https://appcenter.intuit.com/api/v1/OpenID

# Enable all security features
API_GATEWAY_ENABLED=true
RATE_LIMITING_ENABLED=true
AUDIT_LOGGING_ENABLED=true
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY quickbooks_integration/ /app/quickbooks_integration/
WORKDIR /app

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
```

### Environment Variables

```bash
# Required
QUICKBOOKS_CLIENT_ID=your_production_client_id
QUICKBOOKS_CLIENT_SECRET=your_production_client_secret
QUICKBOOKS_ENCRYPTION_KEY=your_secure_encryption_key

# Optional
QUICKBOOKS_WEBHOOK_SECRET=your_webhook_secret
REDIS_URL=redis://localhost:6379
SENTRY_DSN=your_sentry_dsn
```

## 📚 API Reference

### REST Endpoints

All endpoints are available under `/api/quickbooks/` or `/api/v1/quickbooks/` when using the API Gateway.

#### Connection Management

- `POST /api/quickbooks/connect` - Start OAuth flow
- `GET /api/quickbooks/status` - Get connection status  
- `POST /api/quickbooks/disconnect` - Disconnect QuickBooks

#### Data Synchronization

- `POST /api/quickbooks/sync` - Sync all data
- `POST /api/quickbooks/sync/entity` - Sync specific entities
- `GET /api/quickbooks/sync/history` - Get sync history

#### Automation

- `POST /api/quickbooks/automation/enable` - Enable automation
- `POST /api/quickbooks/automation/execute` - Execute workflow
- `GET /api/quickbooks/automation/status` - Get automation status

#### Data Quality

- `POST /api/quickbooks/reconcile` - Run reconciliation
- `GET /api/quickbooks/data-quality` - Get quality metrics
- `GET /api/quickbooks/audit-trail` - Get audit logs

#### Enterprise Features

- `POST /api/quickbooks/enterprise/portfolios` - Create portfolio
- `GET /api/quickbooks/enterprise/portfolios` - List portfolios
- `POST /api/quickbooks/enterprise/reports` - Create custom report
- `POST /api/quickbooks/enterprise/reports/{id}/generate` - Generate report

#### Monitoring

- `GET /api/quickbooks/health` - Get integration health
- `GET /api/quickbooks/summary` - Get integration summary

### Python API

```python
from quickbooks_integration import QuickBooksIntegrationService

qb = QuickBooksIntegrationService()

# All methods return standardized response format:
{
    "success": true,
    "data": {...},
    "error": null,
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🎯 Best Practices

### Data Mapping

1. **Property Separation**: Use QuickBooks Classes to separate properties
2. **Account Structure**: Maintain consistent chart of accounts
3. **Custom Fields**: Use QuickBooks custom fields for EstateCore IDs
4. **Validation**: Always validate data before sync

### Error Handling

1. **Retry Logic**: Implement exponential backoff for transient errors
2. **Circuit Breakers**: Fail fast when QuickBooks is unavailable
3. **Data Integrity**: Use reconciliation to catch and fix discrepancies
4. **Monitoring**: Set up alerts for critical failures

### Performance

1. **Batch Operations**: Use batch APIs for bulk data operations
2. **Caching**: Cache frequently accessed data like accounts
3. **Pagination**: Handle large datasets with proper pagination
4. **Rate Limiting**: Respect QuickBooks API rate limits

### Security

1. **Token Management**: Regularly rotate and refresh tokens
2. **Encryption**: Always encrypt sensitive data at rest
3. **Access Control**: Use principle of least privilege
4. **Audit Logging**: Log all access and changes

## 🐛 Troubleshooting

### Common Issues

#### Connection Problems

```python
# Check connection status
status = qb_service.get_connection_status("org_123")
if not status['connected']:
    # Reconnect to QuickBooks
    result = qb_service.start_oauth_flow("org_123")
```

#### Sync Failures

```python
# Check sync errors
sync_history = qb_service.sync_service.get_sync_history("org_123", limit=10)
for sync in sync_history:
    if sync['status'] == 'failed':
        print(f"Sync failed: {sync['error_message']}")
```

#### Data Quality Issues

```python
# Run reconciliation
result = qb_service.perform_reconciliation("org_123")
discrepancies = result['reconciliation_report']['discrepancies']

for discrepancy in discrepancies:
    print(f"Issue: {discrepancy['description']}")
    print(f"Resolution: {discrepancy['auto_resolvable']}")
```

### Error Codes

- `QB001`: OAuth authentication failed
- `QB002`: Token refresh failed  
- `QB003`: API rate limit exceeded
- `QB004`: Data validation error
- `QB005`: Sync conflict detected
- `QB006`: Account mapping not found
- `QB007`: Reconciliation discrepancy
- `QB008`: Automation workflow failed

### Support

For technical support:
- Check the logs in `instance/logs/quickbooks.log`
- Review the audit trail for operation history
- Use the health check endpoint for system status
- Contact EstateCore support with error details

## 📄 License

This QuickBooks integration is part of the EstateCore platform and is subject to the EstateCore license agreement.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 🗺️ Roadmap

### Upcoming Features

- [ ] Advanced financial reporting
- [ ] Multi-currency support
- [ ] QuickBooks Desktop integration
- [ ] Advanced workflow automation
- [ ] Real-time notifications
- [ ] Mobile app integration

### Version History

- **v1.0.0**: Initial release with core features
- **v1.1.0**: Added enterprise features and multi-property support
- **v1.2.0**: Enhanced error handling and reconciliation
- **v1.3.0**: API Gateway integration and monitoring
- **v1.4.0**: Advanced automation and workflows

---

**Built with ❤️ for the EstateCore Platform**
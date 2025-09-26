# RentManager Integration for EstateCore

A comprehensive enterprise-grade integration between RentManager and EstateCore, supporting multi-family residential, commercial properties, affordable housing compliance, student housing, HOA management, and advanced property management features.

## Overview

RentManager is a leading property management platform serving 3M+ units, particularly strong in multi-family and commercial property management. This integration provides seamless data synchronization, compliance monitoring, and specialized features for various property types.

## Supported RentManager Products

- **Property Management Core** - Complete property and tenant management
- **Asset Management** - Investment tracking and portfolio management  
- **Compliance Management** - Affordable housing and regulatory compliance
- **Student Housing** - Academic calendars, roommate matching, parent guarantors
- **Commercial Management** - CAM charges, percentage rent, commercial leases
- **HOA Management** - Community associations, assessments, violations
- **Maintenance Management** - Work orders, vendor coordination, scheduling

## Supported Property Types

- Multi-family Residential
- Commercial (Office, Retail, Industrial, Warehouse)
- Affordable Housing (LIHTC, Section 8, HUD, etc.)
- Student Housing
- Senior Housing
- Mixed Use
- HOA Communities and Condominiums
- Single Family Rentals

## Compliance Programs Supported

- **LIHTC** (Low-Income Housing Tax Credit)
- **Section 8** Housing Choice Voucher Program
- **HUD** Programs (HOME, CDBG, etc.)
- **USDA Rural Development** Programs
- **Tax-Exempt Bond** Financing
- **State and Local** Affordable Housing Programs

## Key Features

### Core Integration Features
- ✅ Real-time bidirectional synchronization
- ✅ Comprehensive data mapping and transformation
- ✅ Conflict resolution and data quality checks
- ✅ Enterprise security with OAuth 2.0 and API key support
- ✅ Bulk operations and batch processing
- ✅ Webhook support for real-time updates
- ✅ Performance monitoring and analytics
- ✅ Audit trails and compliance tracking

### Property Management Features
- ✅ Property portfolio and building management
- ✅ Unit inventory and availability tracking
- ✅ Tenant/resident management and screening
- ✅ Lease agreements and compliance tracking
- ✅ Rent collection and payment processing
- ✅ Maintenance requests and work orders
- ✅ Vendor management and service coordination
- ✅ Financial reporting and accounting

### Compliance Features
- ✅ Income certifications and recertifications
- ✅ AMI (Area Median Income) tracking
- ✅ Rent and income limit monitoring
- ✅ Compliance violation tracking
- ✅ Automated compliance reporting
- ✅ Audit trail maintenance
- ✅ Government reporting capabilities

### Specialized Features
- ✅ **Student Housing**: Roommate matching, academic calendars, parent guarantors
- ✅ **Commercial**: CAM charges, percentage rent, tenant improvements
- ✅ **HOA Management**: Assessments, violations, board management
- ✅ **Asset Management**: Performance tracking, investment analysis

## Installation and Setup

### Prerequisites

- Python 3.8+
- EstateCore platform installed
- RentManager account with API access
- Valid SSL certificates for production

### Installation

1. **Install the integration module:**
```bash
cd estatecore_project
pip install -r rentmanager_integration/requirements.txt
```

2. **Register the integration with EstateCore:**
```python
from rentmanager_integration import rentmanager_routes
app.register_blueprint(rentmanager_routes.rentmanager_bp)
```

3. **Configure environment variables:**
```bash
export RENTMANAGER_CLIENT_ID="your_client_id"
export RENTMANAGER_CLIENT_SECRET="your_client_secret"  
export RENTMANAGER_BASE_URL="https://api.rentmanager.com"
export RENTMANAGER_ENVIRONMENT="production"  # or "sandbox"
```

### Configuration

#### Basic Integration Setup

```python
from rentmanager_integration import get_rentmanager_integration_service, IntegrationConfiguration
from rentmanager_integration import RentManagerProductType, PropertyType, ComplianceType

# Get integration service
integration_service = get_rentmanager_integration_service()

# Create integration configuration
config = IntegrationConfiguration(
    organization_id="your_org_id",
    integration_name="Main RentManager Integration",
    product_types=[
        RentManagerProductType.PROPERTY_MANAGEMENT,
        RentManagerProductType.COMPLIANCE_MANAGEMENT
    ],
    property_types=[
        PropertyType.MULTI_FAMILY,
        PropertyType.AFFORDABLE_HOUSING
    ],
    compliance_programs=[
        ComplianceType.LIHTC,
        ComplianceType.SECTION_8
    ],
    sync_enabled=True,
    real_time_sync=True,
    compliance_validation=True
)

# Create integration
result = integration_service.create_integration("your_org_id", config)
```

#### Authentication Setup

**OAuth 2.0 (Recommended):**
```python
# Start OAuth flow
connection_params = {
    "auth_type": "oauth2",
    "redirect_uri": "https://your-domain.com/oauth/callback",
    "custom_scopes": ["compliance:read", "compliance:write"]
}

result = integration_service.connect_to_rentmanager("your_org_id", connection_params)
# Redirect user to result["authorization_url"]

# Complete OAuth flow (in callback handler)
result = integration_service.complete_oauth_flow(code, state)
```

**API Key Authentication:**
```python
connection_params = {
    "auth_type": "api_key",
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "base_url": "https://api.rentmanager.com"
}

result = integration_service.connect_to_rentmanager("your_org_id", connection_params)
```

## Usage Examples

### Data Synchronization

#### Full Synchronization
```python
import asyncio

# Start full sync
sync_options = {
    "sync_direction": "bidirectional",
    "entity_types": ["properties", "units", "residents", "leases"],
    "compliance_validation": True
}

result = await integration_service.start_full_sync("your_org_id", sync_options)
print(f"Sync job started: {result['job_id']}")
```

#### Incremental Synchronization
```python
from datetime import datetime, timedelta

# Sync changes from last 24 hours
since_timestamp = datetime.utcnow() - timedelta(hours=24)
result = await integration_service.start_incremental_sync("your_org_id", since_timestamp)
```

#### Monitor Sync Progress
```python
sync_service = integration_service.sync_service
progress = sync_service.get_sync_progress(job_id)

print(f"Progress: {progress['progress_percentage']}%")
print(f"Processed: {progress['processed_entities']}/{progress['total_entities']}")
```

### Compliance Management

#### Check Compliance Status
```python
compliance_status = integration_service.get_compliance_status("your_org_id")

print(f"Overall Compliance: {compliance_status['overall_compliance']}")
for program, status in compliance_status['compliance_programs'].items():
    print(f"{program}: {'✓' if status['compliant'] else '✗'}")
```

#### Generate Compliance Report
```python
from rentmanager_integration import ComplianceType

report = integration_service.generate_compliance_report(
    "your_org_id",
    ComplianceType.LIHTC,
    "monthly"
)

print(f"Report ID: {report['report_id']}")
print(f"Generated: {report['generated_at']}")
```

### Property-Specific Operations

#### Student Housing Applications
```python
api_client = integration_service.api_client

applications = await api_client.get_student_applications("your_org_id", "property_id")
for app in applications.data:
    print(f"Student: {app['student_id']}, University: {app['university']}")
```

#### Commercial CAM Charges
```python
cam_charges = await api_client.get_cam_charges("your_org_id", "property_id", 2024)
print(f"Total CAM: ${cam_charges.data['total_cam_charges']}")
```

#### HOA Assessments
```python
assessments = await api_client.get_hoa_assessments("your_org_id", "property_id")
for assessment in assessments.data:
    print(f"Assessment: ${assessment['amount']}, Due: {assessment['due_date']}")
```

### Data Mapping Customization

```python
mapping_service = integration_service.mapping_service

# Setup custom mapping for student housing
custom_mapping = {
    "field_mappings": {
        "student_id": {
            "source_field": "student_identifier",
            "target_field": "external_student_id",
            "required": True
        },
        "university": {
            "source_field": "educational_institution",
            "target_field": "school_name",
            "transform": "normalize_university_name"
        }
    }
}

mapping_service.setup_custom_mapping("your_org_id", "student_housing", custom_mapping)
```

## API Endpoints

### Integration Management
- `POST /api/integrations/rentmanager/integrations` - Create integration
- `GET /api/integrations/rentmanager/integrations/{org_id}` - Get integration
- `DELETE /api/integrations/rentmanager/integrations/{org_id}` - Delete integration

### Connection Management  
- `POST /api/integrations/rentmanager/connections` - Create connection
- `POST /api/integrations/rentmanager/connections/{org_id}/oauth/callback` - OAuth callback
- `GET /api/integrations/rentmanager/connections/{org_id}/status` - Connection status
- `DELETE /api/integrations/rentmanager/connections/{org_id}` - Disconnect

### Synchronization
- `POST /api/integrations/rentmanager/sync/full` - Start full sync
- `POST /api/integrations/rentmanager/sync/incremental` - Start incremental sync
- `GET /api/integrations/rentmanager/sync/jobs/{job_id}` - Get sync status
- `DELETE /api/integrations/rentmanager/sync/jobs/{job_id}` - Cancel sync
- `GET /api/integrations/rentmanager/sync/history/{org_id}` - Sync history

### Compliance
- `GET /api/integrations/rentmanager/compliance/status/{org_id}` - Compliance status
- `POST /api/integrations/rentmanager/compliance/reports` - Generate report

### Monitoring
- `GET /api/integrations/rentmanager/health/{org_id}` - Integration health

### Property-Specific
- `GET /api/integrations/rentmanager/student-housing/{org_id}/applications` - Student applications
- `GET /api/integrations/rentmanager/commercial/{org_id}/cam-charges` - CAM charges
- `GET /api/integrations/rentmanager/hoa/{org_id}/assessments` - HOA assessments

## Error Handling

The integration includes comprehensive error handling and retry mechanisms:

```python
try:
    result = await integration_service.start_full_sync("your_org_id")
    if not result['success']:
        print(f"Sync failed: {result['error']}")
except Exception as e:
    print(f"Integration error: {e}")
```

## Monitoring and Alerts

### Health Monitoring
```python
health = integration_service.get_integration_health("your_org_id")

print(f"Status: {health.status.value}")
print(f"Data Quality Score: {health.data_quality_score}")
print(f"Uptime: {health.uptime_percentage}%")

if health.issues:
    print("Issues found:")
    for issue in health.issues:
        print(f"  - {issue}")

if health.recommendations:
    print("Recommendations:")
    for rec in health.recommendations:
        print(f"  - {rec}")
```

### Performance Metrics
```python
summary = integration_service.get_integration_summary("your_org_id")

print(f"Properties: {summary['connection']['property_count']}")
print(f"Units: {summary['connection']['unit_count']}")
print(f"Residents: {summary['connection']['resident_count']}")
print(f"Active Jobs: {summary['synchronization']['active_jobs']}")
```

## Security

### Authentication
- OAuth 2.0 with PKCE support
- API key authentication with secret rotation
- JWT token validation
- SAML SSO integration support

### Data Protection
- End-to-end encryption in transit and at rest
- Field-level encryption for sensitive data
- Audit trails for all operations
- Compliance with SOC 2, HIPAA, and PCI standards

### Access Control
- Role-based access control (RBAC)
- Granular permission management
- Organization-level data isolation
- API rate limiting and throttling

## Troubleshooting

### Common Issues

**Connection Issues:**
```python
# Check connection status
status = integration_service.auth_service.validate_connection("your_org_id")
if not status['valid']:
    print(f"Connection issue: {status['error']}")
    # Try refreshing token
    integration_service.auth_service.refresh_access_token("your_org_id")
```

**Sync Failures:**
```python
# Check sync job details
job = sync_service.get_sync_job(job_id)
if job.status == SyncStatus.FAILED:
    print("Sync errors:")
    for error in job.errors:
        print(f"  - {error['error']} at {error['timestamp']}")
```

**Compliance Violations:**
```python
compliance_status = integration_service.get_compliance_status("your_org_id")
if compliance_status['violations']:
    print("Compliance violations found:")
    for violation in compliance_status['violations']:
        print(f"  - {violation}")
```

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('rentmanager_integration').setLevel(logging.DEBUG)
```

## Performance Optimization

### Batch Processing
```python
# Configure larger batch sizes for better performance
config.batch_size = 500
config.max_workers = 10
```

### Selective Sync
```python
# Sync only specific entities
config.sync_entities = ["properties", "units", "leases"]
config.excluded_entities = ["documents", "messages"]
```

### Property Filtering
```python
# Sync only specific property types
config.property_filters = {
    "property_type": ["multi_family", "affordable_housing"],
    "active": True
}
```

## Support and Documentation

### Additional Resources
- [RentManager API Documentation](https://api.rentmanager.com/docs)
- [EstateCore Integration Guide](../docs/INTEGRATION_GUIDE.md)
- [Compliance Management Documentation](../docs/COMPLIANCE.md)

### Support Channels
- Technical Support: support@estatecore.com
- Integration Issues: integrations@estatecore.com
- Compliance Questions: compliance@estatecore.com

## License

This integration is part of the EstateCore platform and is subject to EstateCore's licensing terms.

## Changelog

### Version 1.0.0
- Initial release with comprehensive RentManager integration
- Support for all major property types and compliance programs
- Real-time synchronization and monitoring
- Enterprise security and audit features
- Specialized student housing, commercial, and HOA features

---

**Note**: This integration requires an active RentManager subscription and API access. Contact RentManager support to enable API access for your account.
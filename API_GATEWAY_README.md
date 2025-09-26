# EstateCore Enterprise API Gateway

A comprehensive enterprise-grade API Gateway implementation for EstateCore property management platform, providing advanced authentication, authorization, monitoring, and multi-tenant capabilities.

## 🚀 Features

### Core API Gateway
- **Centralized API Routing**: Intelligent request routing with path-based and header-based routing
- **Request/Response Transformation**: Powerful data transformation engine for API compatibility
- **API Versioning**: Support for multiple API versions (v1, v2, beta, alpha)
- **Circuit Breaker Pattern**: Automatic failure detection and recovery
- **Caching**: Intelligent response caching with configurable TTL
- **Load Balancing**: Multiple upstream service support

### Authentication & Authorization
- **API Key Management**: Secure API key generation, rotation, and revocation
- **OAuth 2.0 Support**: Complete OAuth 2.0 implementation with PKCE
- **JWT Tokens**: Secure JSON Web Token authentication
- **Role-Based Access Control (RBAC)**: Fine-grained permission system
- **Scoped Permissions**: Endpoint and method-specific access control
- **Multi-Factor Authentication**: Support for MFA integration

### Monitoring & Analytics
- **Real-time Metrics**: Live API usage statistics and performance metrics
- **SLA Monitoring**: Automated SLA compliance checking and alerting
- **Performance Analytics**: Response time, throughput, and error rate analysis
- **Custom Dashboards**: Configurable monitoring dashboards
- **Alert Management**: Smart alerting with configurable thresholds
- **Audit Logging**: Comprehensive request and response logging

### Developer Experience
- **Auto-generated Documentation**: OpenAPI 3.0 specification generation
- **Interactive API Explorer**: Swagger UI-based API testing interface
- **SDK Generation**: Automatic SDK generation for multiple languages
- **Code Examples**: Language-specific code samples
- **Sandbox Environment**: Safe testing environment with mock data
- **Postman Collections**: Ready-to-use API collections

### Enterprise Features
- **Multi-tenant Support**: Complete tenant isolation and customization
- **White-label Capabilities**: Custom branding and domain support
- **Webhook Management**: Reliable webhook delivery with retry logic
- **Custom Endpoints**: Tenant-specific API endpoint creation
- **Backup & Recovery**: Automated backup with encryption and compression
- **Disaster Recovery**: Multi-region failover capabilities

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+ (or SQLite for development)
- Redis 6+ (optional, for advanced caching)
- Node.js 16+ (for frontend components)

## 🛠️ Installation

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/estatecore/api-gateway.git
   cd estatecore_project
   ```

2. **Run the automated setup**:
   ```bash
   python setup_api_gateway.py
   ```

3. **Start the API Gateway**:
   ```bash
   python start_api_gateway.py
   ```

### Manual Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install pyyaml jinja2 aiohttp cryptography psutil
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Initialize the database**:
   ```bash
   python -c "from setup_api_gateway import APIGatewaySetup; APIGatewaySetup().initialize_database()"
   ```

4. **Start the server**:
   ```bash
   python start_api_gateway.py
   ```

### Docker Deployment

1. **Using Docker Compose**:
   ```bash
   docker-compose -f docker-compose.apigateway.yml up -d
   ```

2. **Build custom image**:
   ```bash
   docker build -f Dockerfile.apigateway -t estatecore-api-gateway .
   docker run -p 5000:5000 estatecore-api-gateway
   ```

## 🔧 Configuration

### Basic Configuration

The API Gateway uses YAML configuration files. The main configuration file is `api_gateway_config.yaml`:

```yaml
# Basic server configuration
servers:
  - url: "https://api.estatecore.com"
    description: "Production server"

# Security schemes
security_schemes:
  - name: "ApiKeyAuth"
    type: "api_key"
    api_key_name: "X-API-Key"
    api_key_location: "header"

# Rate limiting
rate_limiting:
  default_limits:
    requests_per_minute: 100
    requests_per_hour: 1000
```

### Environment Variables

Key environment variables:

```bash
# Core Configuration
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/estatecore
JWT_SECRET_KEY=your-jwt-secret

# API Gateway Specific
API_BASE_URL=https://api.estatecore.com
API_GATEWAY_CONFIG=api_gateway_config.yaml
API_KEY_MASTER_KEY=your-encryption-key

# Optional Features
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=https://app.estatecore.com,https://dashboard.estatecore.com
```

## 🔑 Authentication

### API Key Authentication

1. **Create an API Key**:
   ```bash
   curl -X POST http://localhost:5000/api/gateway/keys \
     -H "Content-Type: application/json" \
     -d '{
       "client_id": "your-client-id",
       "organization_id": "your-org-id",
       "name": "My API Key",
       "key_type": "full_access",
       "endpoints": ["/api/v1/*"],
       "methods": ["GET", "POST", "PUT", "DELETE"]
     }'
   ```

2. **Use the API Key**:
   ```bash
   curl -H "X-API-Key: your-api-key" \
     http://localhost:5000/api/v1/properties
   ```

### OAuth 2.0 Authentication

1. **Register OAuth Client**:
   ```python
   from oauth_authentication_service import get_oauth_service, ClientType
   
   oauth_service = get_oauth_service()
   client = oauth_service.register_client(
       client_name="My App",
       organization_id="org-123",
       client_type=ClientType.CONFIDENTIAL,
       redirect_uris=["https://myapp.com/callback"],
       allowed_scopes=["read", "write"]
   )
   ```

2. **Authorization Code Flow**:
   ```bash
   # Step 1: Get authorization code
   curl "http://localhost:5000/api/gateway/oauth/authorize?client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&scope=read&state=STATE"
   
   # Step 2: Exchange code for token
   curl -X POST http://localhost:5000/api/gateway/oauth/token \
     -H "Content-Type: application/json" \
     -d '{
       "grant_type": "authorization_code",
       "code": "AUTH_CODE",
       "client_id": "CLIENT_ID",
       "client_secret": "CLIENT_SECRET",
       "redirect_uri": "REDIRECT_URI"
     }'
   ```

## 📊 Monitoring & Analytics

### Real-time Metrics

Access real-time metrics via the monitoring endpoint:

```bash
curl http://localhost:5000/api/gateway/metrics?time_window=3600
```

Response:
```json
{
  "metrics": {
    "total_requests": 1250,
    "successful_requests": 1200,
    "failed_requests": 50,
    "average_response_time": 0.45,
    "p95_response_time": 1.2,
    "error_rate": 4.0,
    "requests_per_second": 12.5
  },
  "time_window": 3600,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Analytics Dashboard

Access the comprehensive analytics dashboard:

```bash
curl http://localhost:5000/api/gateway/analytics/dashboard
```

### Custom Alerts

Configure custom alert thresholds:

```yaml
monitoring:
  alert_thresholds:
    error_rate_percentage: 5.0
    response_time_ms: 2000
    availability_percentage: 99.9
```

## 🏢 Enterprise Features

### Multi-tenant Setup

1. **Create a Tenant**:
   ```bash
   curl -X POST http://localhost:5000/api/gateway/tenants \
     -H "Content-Type: application/json" \
     -d '{
       "organization_id": "acme-corp",
       "tenant_name": "Acme Corporation",
       "tier": "enterprise",
       "custom_domain": "api.acme.com"
     }'
   ```

2. **Configure Tenant Limits**:
   ```yaml
   enterprise:
     tier_limits:
       enterprise:
         requests_per_minute: 2000
         webhook_endpoints: 50
         custom_endpoints: 100
   ```

### Webhook Management

1. **Create Webhook Endpoint**:
   ```bash
   curl -X POST http://localhost:5000/api/gateway/tenants/TENANT_ID/webhooks \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Payment Notifications",
       "url": "https://myapp.com/webhooks/payments",
       "events": ["payment.processed", "payment.failed"],
       "secret": "webhook-secret-key"
     }'
   ```

2. **Webhook Payload Example**:
   ```json
   {
     "id": "webhook-delivery-123",
     "event": "payment.processed",
     "timestamp": "2024-01-15T10:30:00Z",
     "data": {
       "payment_id": "pay_123",
       "amount": 1500.00,
       "status": "completed"
     }
   }
   ```

### Custom Endpoints

Create tenant-specific API endpoints:

```python
from enterprise_features_service import CustomEndpointConfig

config = CustomEndpointConfig(
    endpoint_id="custom-endpoint-1",
    tenant_id="tenant-123",
    path="/api/v1/custom/reports",
    method="GET",
    upstream_url="https://reports.tenant.com/api/data",
    custom_logic="# Python code for custom processing",
    rate_limit=50
)
```

## 📚 API Documentation

### Interactive API Explorer

Access the interactive API documentation at:
```
http://localhost:5000/api/gateway/docs
```

### OpenAPI Specification

Get the complete OpenAPI 3.0 specification:
```bash
curl http://localhost:5000/api/gateway/docs/openapi.json
```

### SDK Generation

Generate SDKs for your preferred language:

```bash
# Python SDK
curl http://localhost:5000/api/gateway/docs/sdk/python

# JavaScript SDK
curl http://localhost:5000/api/gateway/docs/sdk/javascript

# Java SDK
curl http://localhost:5000/api/gateway/docs/sdk/java
```

## 🧪 Testing

### Run the Test Suite

```bash
# Run all tests
python test_api_gateway.py

# Run specific test categories
python test_api_gateway.py TestAPIGatewayCore
python test_api_gateway.py TestAPIKeyManagement
python test_api_gateway.py TestOAuthAuthentication

# Run integration tests (requires running server)
RUN_INTEGRATION_TESTS=1 python test_api_gateway.py
```

### Load Testing

Use the built-in load testing capabilities:

```python
from test_api_gateway import TestAPIGatewayPerformance
import unittest

# Run performance tests
suite = unittest.TestLoader().loadTestsFromTestCase(TestAPIGatewayPerformance)
unittest.TextTestRunner(verbosity=2).run(suite)
```

## 🚀 Performance Optimization

### Caching Configuration

Enable and configure response caching:

```yaml
caching:
  enabled: true
  default_ttl: 300
  endpoint_specific:
    - endpoint: "/api/v1/properties"
      ttl: 600
    - endpoint: "/api/v1/analytics/dashboard"
      ttl: 900
```

### Rate Limiting

Configure intelligent rate limiting:

```yaml
rate_limiting:
  algorithms:
    - endpoint: "/api/v1/payments"
      algorithm: "token_bucket"
      requests_per_minute: 25
      scope: "per_user"
```

### Circuit Breakers

Configure circuit breakers for resilience:

```yaml
circuit_breakers:
  specific_endpoints:
    - endpoint: "/api/v1/payments"
      failure_threshold: 3
      timeout: 120
```

## 🔒 Security

### Security Best Practices

1. **API Key Security**:
   - Use strong, randomly generated API keys
   - Implement key rotation policies
   - Monitor key usage patterns

2. **Rate Limiting**:
   - Implement per-client rate limits
   - Use different limits for different endpoints
   - Monitor for abuse patterns

3. **Input Validation**:
   - Validate all input parameters
   - Sanitize data before processing
   - Implement request size limits

4. **Encryption**:
   - Use HTTPS for all communications
   - Encrypt sensitive data at rest
   - Use secure key management

### Security Monitoring

Monitor security events:

```python
from api_monitoring_service import get_monitoring_service

monitoring = get_monitoring_service()
alerts = monitoring.alert_manager.get_active_alerts()

# Check for security-related alerts
security_alerts = [alert for alert in alerts if 'security' in alert.labels]
```

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**:
   ```bash
   # Check if server is running
   curl http://localhost:5000/api/gateway/health
   ```

2. **Authentication Errors**:
   ```bash
   # Verify API key
   python -c "from api_key_management_service import get_api_key_service; print(get_api_key_service().verify_api_key('your-key'))"
   ```

3. **Rate Limiting Issues**:
   ```bash
   # Check rate limit status
   curl -I http://localhost:5000/api/v1/properties \
     -H "X-API-Key: your-key"
   ```

### Debug Mode

Enable debug mode for detailed logging:

```bash
DEBUG=true python start_api_gateway.py
```

### Log Analysis

Monitor logs for issues:

```bash
# View recent logs
tail -f instance/logs/api_gateway.log

# Search for errors
grep "ERROR" instance/logs/api_gateway.log
```

## 📈 Scaling

### Horizontal Scaling

Deploy multiple instances with load balancing:

```yaml
# docker-compose.yml
services:
  api-gateway-1:
    build: .
    ports:
      - "5001:5000"
  
  api-gateway-2:
    build: .
    ports:
      - "5002:5000"
  
  nginx:
    image: nginx
    depends_on:
      - api-gateway-1
      - api-gateway-2
```

### Database Scaling

Use read replicas for better performance:

```yaml
databases:
  primary:
    url: "postgresql://user:pass@primary-db:5432/estatecore"
    
  replicas:
    - url: "postgresql://user:pass@replica-1:5432/estatecore"
    - url: "postgresql://user:pass@replica-2:5432/estatecore"
```

### Caching Scaling

Use Redis cluster for distributed caching:

```yaml
redis:
  cluster:
    nodes:
      - "redis-1:6379"
      - "redis-2:6379"
      - "redis-3:6379"
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style

We use Python Black for code formatting:

```bash
pip install black
black api_gateway_service.py
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [https://docs.estatecore.com/api-gateway](https://docs.estatecore.com/api-gateway)
- **Issues**: [GitHub Issues](https://github.com/estatecore/api-gateway/issues)
- **Discussions**: [GitHub Discussions](https://github.com/estatecore/api-gateway/discussions)
- **Email**: support@estatecore.com

## 🗺️ Roadmap

### Upcoming Features

- [ ] GraphQL API Gateway support
- [ ] gRPC protocol support
- [ ] Advanced ML-based anomaly detection
- [ ] Multi-cloud deployment templates
- [ ] Enhanced security scanning
- [ ] Real-time collaboration features

### Version History

- **v1.0.0**: Initial release with core features
- **v1.1.0**: Added multi-tenant support
- **v1.2.0**: Enhanced monitoring and analytics
- **v1.3.0**: OAuth 2.0 and JWT support
- **v1.4.0**: Enterprise features and webhooks

---

**Built with ❤️ by the EstateCore Team**
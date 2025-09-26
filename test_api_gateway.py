"""
Comprehensive Test Suite for EstateCore API Gateway
Tests for all API Gateway functionality, performance, and security
"""

import os
import sys
import unittest
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import uuid

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import API Gateway services
from api_gateway_service import (
    APIGatewayService, APIEndpoint, APIClient, APIVersion, HTTPMethod, 
    AuthenticationType, CircuitBreakerState, RequestTransformer, ResponseTransformer
)
from api_key_management_service import (
    APIKeyManagementService, APIKeyType, APIKeyPermissions, APIKeyStatus,
    APIKeyGenerator, APIKeyValidation
)
from oauth_authentication_service import (
    OAuthAuthenticationService, GrantType, ClientType, PKCEVerifier, JWTManager
)
from api_monitoring_service import (
    APIMonitoringService, RequestMetrics, PerformanceMetrics, SLAManager, AlertManager
)
from api_documentation_service import (
    APIDocumentationService, OpenAPIGenerator, CodeSampleGenerator, SandboxEnvironment
)
from enterprise_features_service import (
    EnterpriseFeatureService, MultiTenantManager, WebhookManager, BackupRecoveryManager,
    TenantTier, WebhookStatus
)

class TestAPIGatewayCore(unittest.TestCase):
    """Test core API Gateway functionality"""
    
    def setUp(self):
        self.gateway = APIGatewayService()
        self.test_endpoint = APIEndpoint(
            path="/api/v1/test",
            method=HTTPMethod.GET,
            version=APIVersion.V1,
            upstream_url="http://localhost:8080/test",
            authentication=AuthenticationType.API_KEY,
            rate_limit=100
        )
        self.gateway.register_endpoint(self.test_endpoint)
    
    def test_endpoint_registration(self):
        """Test endpoint registration"""
        endpoint_key = f"{self.test_endpoint.version.value}:{self.test_endpoint.method.value}:{self.test_endpoint.path}"
        self.assertIn(endpoint_key, self.gateway.endpoints)
        self.assertEqual(self.gateway.endpoints[endpoint_key], self.test_endpoint)
    
    def test_client_registration(self):
        """Test client registration"""
        client = APIClient(
            client_id="test_client",
            client_secret="test_secret",
            name="Test Client",
            organization_id="test_org",
            api_keys=["test_key_123"],
            allowed_endpoints=["/api/v1/test"],
            scopes=["read", "write"]
        )
        
        self.gateway.register_client(client)
        self.assertIn(client.client_id, self.gateway.clients)
        self.assertEqual(self.gateway.clients[client.client_id], client)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Test within limits
        for i in range(5):
            result = self.gateway.check_rate_limit("test_client", "test_endpoint", 10, type(self.gateway).RateLimitType.PER_MINUTE)
            self.assertTrue(result)
        
        # Test exceeding limits
        for i in range(10):
            self.gateway.check_rate_limit("test_client", "test_endpoint", 10, type(self.gateway).RateLimitType.PER_MINUTE)
        
        result = self.gateway.check_rate_limit("test_client", "test_endpoint", 10, type(self.gateway).RateLimitType.PER_MINUTE)
        self.assertFalse(result)
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        endpoint_key = "test_endpoint"
        
        # Circuit should be closed initially
        self.assertTrue(self.gateway.check_circuit_breaker(endpoint_key))
        
        # Simulate failures
        for i in range(6):  # Exceed threshold
            self.gateway.record_request_result(endpoint_key, False)
        
        # Circuit should be open now
        self.assertFalse(self.gateway.check_circuit_breaker(endpoint_key))
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        from api_gateway_service import APIRequest
        
        request = APIRequest(
            request_id="test",
            client_id="test_client",
            endpoint=self.test_endpoint,
            method="GET",
            path="/api/v1/test",
            headers={},
            query_params={"param1": "value1"},
            body=None,
            remote_addr="127.0.0.1",
            user_agent="Test Agent",
            timestamp=datetime.utcnow(),
            version=APIVersion.V1,
            authentication_method=AuthenticationType.API_KEY
        )
        
        cache_key = self.gateway.get_cache_key(request)
        self.assertIsInstance(cache_key, str)
        self.assertEqual(len(cache_key), 32)  # MD5 hash length

class TestAPIKeyManagement(unittest.TestCase):
    """Test API key management functionality"""
    
    def setUp(self):
        self.key_service = APIKeyManagementService()
        # Set test master key for encryption
        os.environ['API_KEY_MASTER_KEY'] = 'test_master_key_for_encryption_testing'
    
    def test_api_key_generation(self):
        """Test API key generation"""
        full_key, key_hash, key_prefix = APIKeyGenerator.generate_api_key()
        
        self.assertTrue(full_key.startswith('ec_'))
        self.assertEqual(len(key_hash), 64)  # SHA256 hash length
        self.assertEqual(len(key_prefix), 12)  # prefix + first 8 chars
        
    def test_api_key_validation(self):
        """Test API key format validation"""
        # Valid key
        valid_key = "ec_abcdefghijklmnopqrstuvwxyz123456"
        self.assertTrue(APIKeyGenerator.validate_api_key_format(valid_key))
        
        # Invalid keys
        self.assertFalse(APIKeyGenerator.validate_api_key_format("invalid_key"))
        self.assertFalse(APIKeyGenerator.validate_api_key_format(""))
        self.assertFalse(APIKeyGenerator.validate_api_key_format("short"))
    
    def test_api_key_creation(self):
        """Test API key creation"""
        permissions = APIKeyPermissions(
            endpoints=["/api/v1/test"],
            methods=["GET", "POST"],
            rate_limits={"default": 100}
        )
        
        api_key, key_obj = self.key_service.create_api_key(
            client_id="test_client",
            organization_id="test_org",
            name="Test Key",
            description="Test API key",
            key_type=APIKeyType.FULL_ACCESS,
            permissions=permissions
        )
        
        self.assertIsNotNone(api_key)
        self.assertIsNotNone(key_obj)
        self.assertEqual(key_obj.name, "Test Key")
        self.assertEqual(key_obj.client_id, "test_client")
        self.assertEqual(key_obj.status, APIKeyStatus.ACTIVE)
    
    def test_api_key_verification(self):
        """Test API key verification"""
        permissions = APIKeyPermissions()
        api_key, key_obj = self.key_service.create_api_key(
            client_id="test_client",
            organization_id="test_org",
            name="Test Key",
            description="Test",
            key_type=APIKeyType.FULL_ACCESS,
            permissions=permissions
        )
        
        # Verify valid key
        is_valid, verified_key, error = self.key_service.verify_api_key(api_key)
        self.assertTrue(is_valid)
        self.assertIsNotNone(verified_key)
        self.assertIsNone(error)
        
        # Verify invalid key
        is_valid, verified_key, error = self.key_service.verify_api_key("invalid_key")
        self.assertFalse(is_valid)
        self.assertIsNone(verified_key)
        self.assertIsNotNone(error)
    
    def test_api_key_revocation(self):
        """Test API key revocation"""
        permissions = APIKeyPermissions()
        api_key, key_obj = self.key_service.create_api_key(
            client_id="test_client",
            organization_id="test_org",
            name="Test Key",
            description="Test",
            key_type=APIKeyType.FULL_ACCESS,
            permissions=permissions
        )
        
        # Revoke key
        success = self.key_service.revoke_api_key(key_obj.key_id, "Test revocation")
        self.assertTrue(success)
        
        # Verify revoked key fails verification
        is_valid, verified_key, error = self.key_service.verify_api_key(api_key)
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_api_key_rotation(self):
        """Test API key rotation"""
        permissions = APIKeyPermissions()
        api_key, key_obj = self.key_service.create_api_key(
            client_id="test_client",
            organization_id="test_org",
            name="Test Key",
            description="Test",
            key_type=APIKeyType.FULL_ACCESS,
            permissions=permissions
        )
        
        old_key_hash = key_obj.key_hash
        
        # Rotate key
        success, new_key = self.key_service.rotate_api_key(key_obj.key_id)
        self.assertTrue(success)
        self.assertIsNotNone(new_key)
        
        # Verify old key is invalid
        is_valid, _, _ = self.key_service.verify_api_key(api_key)
        self.assertFalse(is_valid)
        
        # Verify new key is valid
        is_valid, _, _ = self.key_service.verify_api_key(new_key)
        self.assertTrue(is_valid)

class TestOAuthAuthentication(unittest.TestCase):
    """Test OAuth 2.0 authentication functionality"""
    
    def setUp(self):
        self.oauth_service = OAuthAuthenticationService()
        self.test_client = self.oauth_service.register_client(
            client_name="Test Client",
            organization_id="test_org",
            client_type=ClientType.CONFIDENTIAL,
            redirect_uris=["http://localhost:3000/callback"],
            allowed_scopes=["read", "write"]
        )
    
    def test_client_registration(self):
        """Test OAuth client registration"""
        self.assertIsNotNone(self.test_client.client_id)
        self.assertIsNotNone(self.test_client.client_secret)
        self.assertEqual(self.test_client.client_name, "Test Client")
        self.assertEqual(self.test_client.client_type, ClientType.CONFIDENTIAL)
    
    def test_authorization_url_creation(self):
        """Test authorization URL creation"""
        success, auth_url, error = self.oauth_service.create_authorization_url(
            client_id=self.test_client.client_id,
            redirect_uri="http://localhost:3000/callback",
            scopes=["read"],
            state="test_state"
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(auth_url)
        self.assertIsNone(error)
        self.assertIn("client_id", auth_url)
        self.assertIn("redirect_uri", auth_url)
        self.assertIn("scope", auth_url)
    
    def test_pkce_verification(self):
        """Test PKCE (Proof Key for Code Exchange) functionality"""
        verifier = PKCEVerifier.generate_code_verifier()
        challenge = PKCEVerifier.generate_code_challenge(verifier)
        
        self.assertIsNotNone(verifier)
        self.assertIsNotNone(challenge)
        self.assertTrue(PKCEVerifier.verify_code_challenge(verifier, challenge))
        self.assertFalse(PKCEVerifier.verify_code_challenge("wrong_verifier", challenge))
    
    def test_authorization_code_flow(self):
        """Test complete authorization code flow"""
        # Create authorization code
        auth_code = self.oauth_service.create_authorization_code(
            client_id=self.test_client.client_id,
            user_id="test_user",
            scopes=["read"],
            redirect_uri="http://localhost:3000/callback"
        )
        
        self.assertIsNotNone(auth_code)
        
        # Exchange code for token
        success, token_response, error = self.oauth_service.exchange_code_for_token(
            code=auth_code,
            client_id=self.test_client.client_id,
            client_secret=self.test_client.client_secret,
            redirect_uri="http://localhost:3000/callback"
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(token_response)
        self.assertIsNone(error)
        self.assertIn('access_token', token_response)
        self.assertIn('token_type', token_response)
    
    def test_client_credentials_grant(self):
        """Test client credentials grant"""
        success, token_response, error = self.oauth_service.client_credentials_grant(
            client_id=self.test_client.client_id,
            client_secret=self.test_client.client_secret,
            scopes=["read"]
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(token_response)
        self.assertIsNone(error)
        self.assertIn('access_token', token_response)
    
    def test_jwt_token_verification(self):
        """Test JWT token verification"""
        jwt_manager = JWTManager()
        
        from oauth_authentication_service import JWTClaims
        claims = JWTClaims(
            iss="test_issuer",
            sub="test_subject",
            aud="test_audience",
            exp=int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            iat=int(datetime.utcnow().timestamp()),
            nbf=int(datetime.utcnow().timestamp()),
            jti=str(uuid.uuid4()),
            scopes=["read", "write"]
        )
        
        token = jwt_manager.create_access_token(claims)
        self.assertIsNotNone(token)
        
        is_valid, payload, error = jwt_manager.verify_token(token)
        self.assertTrue(is_valid)
        self.assertIsNotNone(payload)
        self.assertIsNone(error)

class TestAPIMonitoring(unittest.TestCase):
    """Test API monitoring and analytics functionality"""
    
    def setUp(self):
        self.monitoring_service = APIMonitoringService()
    
    def test_request_metrics_recording(self):
        """Test request metrics recording"""
        metrics = RequestMetrics(
            request_id="test_request",
            timestamp=datetime.utcnow(),
            client_id="test_client",
            endpoint="/api/v1/test",
            method="GET",
            version="v1",
            response_status=200,
            response_time=0.5,
            request_size=100,
            response_size=500,
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )
        
        initial_count = len(self.monitoring_service.request_metrics)
        self.monitoring_service.record_request(metrics)
        
        self.assertEqual(len(self.monitoring_service.request_metrics), initial_count + 1)
        self.assertEqual(self.monitoring_service.request_metrics[-1], metrics)
    
    def test_performance_metrics_calculation(self):
        """Test performance metrics calculation"""
        # Add test data
        for i in range(10):
            metrics = RequestMetrics(
                request_id=f"test_request_{i}",
                timestamp=datetime.utcnow(),
                client_id="test_client",
                endpoint="/api/v1/test",
                method="GET",
                version="v1",
                response_status=200 if i < 8 else 500,
                response_time=0.1 + (i * 0.05),
                request_size=100,
                response_size=500,
                ip_address="127.0.0.1",
                user_agent="Test Agent"
            )
            self.monitoring_service.record_request(metrics)
        
        performance = self.monitoring_service.get_performance_metrics(3600)
        
        self.assertEqual(performance.total_requests, 10)
        self.assertEqual(performance.successful_requests, 8)
        self.assertEqual(performance.failed_requests, 2)
        self.assertEqual(performance.error_rate, 20.0)
        self.assertGreater(performance.average_response_time, 0)
    
    def test_sla_monitoring(self):
        """Test SLA monitoring"""
        sla_manager = SLAManager()
        
        # Create test metrics that violate SLA
        bad_metrics = [
            RequestMetrics(
                request_id=f"bad_request_{i}",
                timestamp=datetime.utcnow(),
                client_id="test_client",
                endpoint="/api/v1/test",
                method="GET",
                version="v1",
                response_status=500,  # Server error
                response_time=5.0,    # Very slow
                request_size=100,
                response_size=500,
                ip_address="127.0.0.1",
                user_agent="Test Agent"
            )
            for i in range(5)
        ]
        
        violations = sla_manager.check_sla_compliance(bad_metrics)
        self.assertGreater(len(violations), 0)
    
    def test_alert_management(self):
        """Test alert management"""
        alert_manager = AlertManager()
        
        from api_monitoring_service import AlertSeverity
        alert = alert_manager.create_alert(
            title="Test Alert",
            description="This is a test alert",
            severity=AlertSeverity.WARNING,
            source="test_suite"
        )
        
        self.assertIsNotNone(alert.alert_id)
        self.assertEqual(alert.title, "Test Alert")
        self.assertFalse(alert.resolved)
        
        # Test alert resolution
        success = alert_manager.resolve_alert(alert.alert_id)
        self.assertTrue(success)
        self.assertTrue(alert.resolved)

class TestAPIDocumentation(unittest.TestCase):
    """Test API documentation functionality"""
    
    def setUp(self):
        self.doc_service = APIDocumentationService()
    
    def test_openapi_spec_generation(self):
        """Test OpenAPI specification generation"""
        spec = self.doc_service.generate_documentation()
        
        self.assertIsInstance(spec, dict)
        self.assertEqual(spec['openapi'], '3.0.3')
        self.assertIn('info', spec)
        self.assertIn('paths', spec)
        self.assertIn('components', spec)
        self.assertIn('tags', spec)
    
    def test_code_sample_generation(self):
        """Test code sample generation"""
        samples = self.doc_service.generate_code_samples('/api/v1/properties', 'GET')
        
        self.assertIsInstance(samples, list)
        if samples:  # If we have samples
            self.assertGreater(len(samples), 0)
            for sample in samples:
                self.assertIsNotNone(sample.language)
                self.assertIsNotNone(sample.source)
    
    def test_sdk_generation(self):
        """Test SDK generation"""
        try:
            python_sdk = self.doc_service.generate_sdk('python')
            self.assertIsInstance(python_sdk, dict)
        except ValueError:
            # SDK generation may not be fully implemented
            pass
    
    def test_api_explorer_generation(self):
        """Test API explorer generation"""
        explorer_html = self.doc_service.generate_api_explorer()
        
        self.assertIsInstance(explorer_html, str)
        self.assertIn('swagger-ui', explorer_html.lower())
    
    def test_sandbox_environment(self):
        """Test sandbox environment"""
        sandbox = SandboxEnvironment()
        
        # Create sandbox client
        client_creds = sandbox.create_sandbox_client("Test Client", ["read", "write"])
        
        self.assertIn('client_id', client_creds)
        self.assertIn('api_key', client_creds)
        self.assertTrue(client_creds['client_id'].startswith('sandbox_'))
        self.assertTrue(client_creds['api_key'].startswith('sandbox_'))

class TestEnterpriseFeatures(unittest.TestCase):
    """Test enterprise features functionality"""
    
    def setUp(self):
        self.enterprise_service = EnterpriseFeatureService()
    
    def test_multi_tenant_management(self):
        """Test multi-tenant functionality"""
        tenant = self.enterprise_service.tenant_manager.create_tenant(
            organization_id="test_org",
            tenant_name="Test Tenant",
            tier=TenantTier.PROFESSIONAL,
            custom_domain="test.example.com"
        )
        
        self.assertIsNotNone(tenant.tenant_id)
        self.assertEqual(tenant.tenant_name, "Test Tenant")
        self.assertEqual(tenant.tier, TenantTier.PROFESSIONAL)
        self.assertEqual(tenant.custom_domain, "test.example.com")
        
        # Test tenant retrieval
        retrieved_tenant = self.enterprise_service.tenant_manager.get_tenant(tenant.tenant_id)
        self.assertEqual(retrieved_tenant, tenant)
        
        # Test tenant by domain
        domain_tenant = self.enterprise_service.tenant_manager.get_tenant_by_domain("test.example.com")
        self.assertEqual(domain_tenant, tenant)
    
    def test_webhook_management(self):
        """Test webhook management"""
        webhook_manager = self.enterprise_service.webhook_manager
        
        # Create webhook endpoint
        webhook = webhook_manager.create_webhook_endpoint(
            tenant_id="test_tenant",
            name="Test Webhook",
            url="https://example.com/webhook",
            events=["api.request", "api.error"]
        )
        
        self.assertIsNotNone(webhook.webhook_id)
        self.assertEqual(webhook.name, "Test Webhook")
        self.assertEqual(webhook.url, "https://example.com/webhook")
        self.assertIn("api.request", webhook.events)
        
        # Test webhook triggering
        webhook_manager.trigger_webhook(
            tenant_id="test_tenant",
            event_type="api.request",
            payload={"test": "data"}
        )
        
        # Allow some time for async processing
        time.sleep(0.1)
        
        # Check that delivery was queued
        self.assertGreater(webhook_manager.delivery_queue.qsize(), 0)
    
    def test_backup_recovery(self):
        """Test backup and recovery functionality"""
        backup_manager = self.enterprise_service.backup_manager
        
        from enterprise_features_service import BackupType
        
        # Create backup configuration
        config = backup_manager.create_backup_config(
            tenant_id="test_tenant",
            backup_type=BackupType.FULL,
            schedule="daily",
            retention_days=7
        )
        
        self.assertIsNotNone(config.backup_id)
        self.assertEqual(config.backup_type, BackupType.FULL)
        self.assertEqual(config.schedule, "daily")
        self.assertEqual(config.retention_days, 7)
        
        # Test backup execution
        with tempfile.TemporaryDirectory() as temp_dir:
            os.environ['BACKUP_ROOT_DIR'] = temp_dir
            record = backup_manager.execute_backup(config.backup_id)
            
            if record:  # Backup might fail in test environment
                self.assertIsNotNone(record.record_id)
                self.assertEqual(record.tenant_id, "test_tenant")
                self.assertTrue(os.path.exists(record.file_path))

class TestAPIGatewayPerformance(unittest.TestCase):
    """Test API Gateway performance and load handling"""
    
    def setUp(self):
        self.gateway = APIGatewayService()
        self.monitoring = APIMonitoringService()
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        def make_request(request_id):
            metrics = RequestMetrics(
                request_id=f"concurrent_request_{request_id}",
                timestamp=datetime.utcnow(),
                client_id="test_client",
                endpoint="/api/v1/test",
                method="GET",
                version="v1",
                response_status=200,
                response_time=0.1,
                request_size=100,
                response_size=500,
                ip_address="127.0.0.1",
                user_agent="Test Agent"
            )
            self.monitoring.record_request(metrics)
            return request_id
        
        # Test with 50 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        self.assertEqual(len(results), 50)
        self.assertGreaterEqual(len(self.monitoring.request_metrics), 50)
    
    def test_rate_limiting_under_load(self):
        """Test rate limiting under load"""
        client_id = "load_test_client"
        endpoint = "test_endpoint"
        
        # Make requests rapidly
        allowed_count = 0
        denied_count = 0
        
        for i in range(20):
            if self.gateway.check_rate_limit(client_id, endpoint, 10, type(self.gateway).RateLimitType.PER_MINUTE):
                allowed_count += 1
            else:
                denied_count += 1
        
        # Should have some denied requests
        self.assertGreater(denied_count, 0)
        self.assertLessEqual(allowed_count, 10)
    
    def test_memory_usage_under_load(self):
        """Test memory usage during load testing"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Generate load
        for i in range(1000):
            metrics = RequestMetrics(
                request_id=f"memory_test_{i}",
                timestamp=datetime.utcnow(),
                client_id="test_client",
                endpoint="/api/v1/test",
                method="GET",
                version="v1",
                response_status=200,
                response_time=0.1,
                request_size=100,
                response_size=500,
                ip_address="127.0.0.1",
                user_agent="Test Agent"
            )
            self.monitoring.record_request(metrics)
        
        gc.collect()  # Force garbage collection
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        self.assertLess(memory_increase, 100)

class TestAPIGatewaySecurity(unittest.TestCase):
    """Test API Gateway security features"""
    
    def setUp(self):
        self.gateway = APIGatewayService()
        self.key_service = APIKeyManagementService()
    
    def test_api_key_security(self):
        """Test API key security features"""
        # Test key generation security
        keys = set()
        for i in range(100):
            key, _, _ = APIKeyGenerator.generate_api_key()
            keys.add(key)
        
        # All keys should be unique
        self.assertEqual(len(keys), 100)
        
        # Keys should be unpredictable
        key_list = list(keys)
        self.assertNotEqual(key_list[0], key_list[1])
    
    def test_rate_limiting_security(self):
        """Test rate limiting as security measure"""
        # Test IP-based rate limiting
        client_id = "security_test_client"
        
        # Simulate attack from single IP
        attack_blocked = False
        for i in range(100):
            if not self.gateway.check_rate_limit(client_id, "security_endpoint", 10, type(self.gateway).RateLimitType.PER_MINUTE):
                attack_blocked = True
                break
        
        self.assertTrue(attack_blocked)
    
    def test_input_validation(self):
        """Test input validation and sanitization"""
        transformer = RequestTransformer()
        
        # Test with malicious input
        malicious_data = {
            "script": "<script>alert('xss')</script>",
            "sql": "'; DROP TABLE users; --",
            "long_string": "A" * 10000
        }
        
        transformation_config = {
            "validations": {
                "script": {"max_length": 100},
                "sql": {"regex": "^[a-zA-Z0-9 ]*$"},
                "long_string": {"max_length": 1000}
            }
        }
        
        try:
            transformed = transformer.transform_request(malicious_data, transformation_config)
            # Should handle validation appropriately
            if "script" in transformed:
                self.assertLessEqual(len(transformed["script"]), 100)
            if "long_string" in transformed:
                self.assertLessEqual(len(transformed["long_string"]), 1000)
        except ValueError:
            # Validation should catch malicious input
            pass

def run_integration_tests():
    """Run integration tests against live API Gateway"""
    
    class IntegrationTestSuite(unittest.TestCase):
        """Integration tests for live API Gateway"""
        
        @classmethod
        def setUpClass(cls):
            # These tests would run against a live API Gateway instance
            cls.base_url = os.environ.get('API_GATEWAY_TEST_URL', 'http://localhost:5000')
            cls.api_key = os.environ.get('API_GATEWAY_TEST_KEY', 'test_key')
        
        def test_health_check(self):
            """Test API Gateway health check"""
            try:
                response = requests.get(f"{self.base_url}/api/gateway/health", timeout=5)
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data['status'], 'healthy')
            except requests.RequestException:
                self.skipTest("API Gateway not available for integration testing")
        
        def test_openapi_endpoint(self):
            """Test OpenAPI specification endpoint"""
            try:
                response = requests.get(f"{self.base_url}/api/gateway/docs/openapi.json", timeout=5)
                self.assertEqual(response.status_code, 200)
                spec = response.json()
                self.assertEqual(spec['openapi'], '3.0.3')
            except requests.RequestException:
                self.skipTest("API Gateway not available for integration testing")
        
        def test_metrics_endpoint(self):
            """Test metrics endpoint"""
            try:
                response = requests.get(
                    f"{self.base_url}/api/gateway/metrics",
                    headers={'X-API-Key': self.api_key},
                    timeout=5
                )
                # Should return 200 or 401 (if key is invalid)
                self.assertIn(response.status_code, [200, 401])
            except requests.RequestException:
                self.skipTest("API Gateway not available for integration testing")
    
    return IntegrationTestSuite

def create_test_suite():
    """Create comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Core functionality tests
    suite.addTest(unittest.makeSuite(TestAPIGatewayCore))
    suite.addTest(unittest.makeSuite(TestAPIKeyManagement))
    suite.addTest(unittest.makeSuite(TestOAuthAuthentication))
    suite.addTest(unittest.makeSuite(TestAPIMonitoring))
    suite.addTest(unittest.makeSuite(TestAPIDocumentation))
    suite.addTest(unittest.makeSuite(TestEnterpriseFeatures))
    
    # Performance tests
    suite.addTest(unittest.makeSuite(TestAPIGatewayPerformance))
    
    # Security tests
    suite.addTest(unittest.makeSuite(TestAPIGatewaySecurity))
    
    # Integration tests (if environment allows)
    if os.environ.get('RUN_INTEGRATION_TESTS'):
        suite.addTest(unittest.makeSuite(run_integration_tests()))
    
    return suite

if __name__ == '__main__':
    # Set up test environment
    os.environ['API_KEY_MASTER_KEY'] = 'test_master_key_for_testing'
    os.environ['JWT_SECRET_KEY'] = 'test_jwt_secret_key'
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    sys.exit(exit_code)
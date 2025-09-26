"""
Comprehensive test suite for QuickBooks Online integration

Tests all components of the QuickBooks integration including OAuth,
API client, synchronization, automation, and enterprise features.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the services to test
from ..quickbooks_oauth_service import QuickBooksOAuthService, QuickBooksConnection, OAuthConfig
from ..quickbooks_api_client import QuickBooksAPIClient, QBOEntityType, QBOOperationType, QBORequest
from ..data_mapping_service import DataMappingService, EstateCoreTenant, QuickBooksEntity
from ..financial_sync_service import FinancialSyncService, SyncDirection, SyncStatus
from ..automation_engine import QuickBooksAutomationEngine, WorkflowType, WorkflowStatus
from ..reconciliation_service import ReconciliationService, DiscrepancyType, ErrorSeverity
from ..enterprise_features import EnterpriseQuickBooksService, AccessLevel, ReportType
from ..quickbooks_integration_service import QuickBooksIntegrationService

@pytest.fixture
def oauth_config():
    """OAuth configuration for testing"""
    return OAuthConfig(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:5000/test/callback",
        scope=["com.intuit.quickbooks.accounting"],
        base_url="https://sandbox-quickbooks.api.intuit.com"
    )

@pytest.fixture
def mock_connection():
    """Mock QuickBooks connection"""
    return QuickBooksConnection(
        connection_id="test_connection_id",
        organization_id="test_org_id",
        company_id="test_company_id",
        access_token="test_access_token",
        refresh_token="test_refresh_token",
        token_expires_at=datetime.now() + timedelta(hours=1),
        scope=["com.intuit.quickbooks.accounting"],
        base_url="https://sandbox-quickbooks.api.intuit.com",
        company_info={"Name": "Test Company"},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for testing"""
    return {
        "tenant_id": "tenant_123",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "555-1234",
        "unit_address": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "12345",
        "unit_number": "A1",
        "lease_start_date": "2024-01-01",
        "lease_end_date": "2024-12-31"
    }

@pytest.fixture
def sample_payment_data():
    """Sample payment data for testing"""
    return {
        "rent_payment_id": "payment_123",
        "tenant_id": "tenant_123",
        "property_id": "property_123",
        "amount": 1500.00,
        "payment_date": "2024-01-01",
        "due_date": "2024-01-01",
        "status": "paid",
        "payment_method": "credit_card",
        "period_start": "2024-01-01",
        "period_end": "2024-01-31",
        "unit_number": "A1"
    }

@pytest.fixture
def sample_expense_data():
    """Sample expense data for testing"""
    return {
        "expense_id": "expense_123",
        "vendor_name": "Test Vendor",
        "property_id": "property_123",
        "amount": 500.00,
        "expense_date": "2024-01-15",
        "due_date": "2024-02-15",
        "category": "maintenance",
        "description": "Plumbing repair",
        "invoice_number": "INV-001"
    }

class TestQuickBooksOAuthService:
    """Test OAuth authentication service"""
    
    def test_oauth_service_initialization(self, oauth_config):
        """Test OAuth service initialization"""
        service = QuickBooksOAuthService(oauth_config)
        
        assert service.config.client_id == "test_client_id"
        assert service.config.redirect_uri == "http://localhost:5000/test/callback"
        assert len(service.connections) == 0
    
    def test_generate_authorization_url(self, oauth_config):
        """Test authorization URL generation"""
        service = QuickBooksOAuthService(oauth_config)
        
        auth_url, state = service.generate_authorization_url("test_org")
        
        assert "client_id=test_client_id" in auth_url
        assert "redirect_uri=" in auth_url
        assert "scope=com.intuit.quickbooks.accounting" in auth_url
        assert len(state) > 20  # Should be a long random string
    
    @patch('requests.post')
    def test_exchange_code_for_tokens(self, mock_post, oauth_config):
        """Test token exchange"""
        # Mock successful token response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "scope": "com.intuit.quickbooks.accounting"
        }
        mock_post.return_value = mock_response
        
        service = QuickBooksOAuthService(oauth_config)
        
        # Mock state validation
        with patch.object(service, '_validate_oauth_state', return_value="test_org"):
            with patch.object(service, '_get_company_info', return_value={"Name": "Test Company"}):
                connection = service.exchange_code_for_tokens("test_code", "test_state", "test_realm")
                
                assert connection.access_token == "new_access_token"
                assert connection.refresh_token == "new_refresh_token"
                assert connection.company_id == "test_realm"
                assert connection.organization_id == "test_org"
    
    @patch('requests.post')
    def test_refresh_access_token(self, mock_post, oauth_config, mock_connection):
        """Test token refresh"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "access_token": "refreshed_access_token",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response
        
        service = QuickBooksOAuthService(oauth_config)
        service.connections[mock_connection.connection_id] = mock_connection
        
        success = service.refresh_access_token(mock_connection.connection_id)
        
        assert success
        assert mock_connection.access_token == "refreshed_access_token"
    
    def test_token_expiration_check(self, mock_connection):
        """Test token expiration checking"""
        # Test non-expired token
        assert not mock_connection.is_token_expired()
        
        # Test expired token
        mock_connection.token_expires_at = datetime.now() - timedelta(hours=1)
        assert mock_connection.is_token_expired()

class TestQuickBooksAPIClient:
    """Test QuickBooks API client"""
    
    def test_api_client_initialization(self):
        """Test API client initialization"""
        client = QuickBooksAPIClient()
        
        assert client.api_version == "v3"
        assert client.max_retries == 3
        assert client.timeout == 30
    
    @patch('requests.get')
    def test_make_request_success(self, mock_get, mock_connection):
        """Test successful API request"""
        mock_oauth_service = Mock()
        mock_oauth_service.ensure_valid_token.return_value = "valid_token"
        
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.json.return_value = {"QueryResponse": {"Customer": []}}
        mock_get.return_value = mock_response
        
        client = QuickBooksAPIClient(mock_oauth_service)
        response = client._make_request(mock_connection, 'GET', 'customers')
        
        assert response.status_code == 200
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_make_request_rate_limit(self, mock_get, mock_connection):
        """Test rate limiting handling"""
        mock_oauth_service = Mock()
        mock_oauth_service.ensure_valid_token.return_value = "valid_token"
        
        # First response: rate limited
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.headers = {'Retry-After': '1'}
        
        # Second response: success
        success_response = Mock()
        success_response.ok = True
        success_response.status_code = 200
        success_response.json.return_value = {"QueryResponse": {"Customer": []}}
        
        mock_get.side_effect = [rate_limit_response, success_response]
        
        client = QuickBooksAPIClient(mock_oauth_service)
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            response = client._make_request(mock_connection, 'GET', 'customers')
        
        assert response.status_code == 200
        assert mock_get.call_count == 2
    
    def test_parse_response_success(self):
        """Test successful response parsing"""
        client = QuickBooksAPIClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "QueryResponse": {"Customer": [{"Id": "1", "Name": "Test Customer"}]}
        }
        
        parsed = client._parse_response(mock_response)
        
        assert parsed.success
        assert parsed.query_response["Customer"][0]["Name"] == "Test Customer"
    
    def test_parse_response_error(self):
        """Test error response parsing"""
        client = QuickBooksAPIClient()
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Fault": {
                "Error": [{"Detail": "Invalid request"}]
            }
        }
        
        parsed = client._parse_response(mock_response)
        
        assert not parsed.success
        assert parsed.error == "Invalid request"
    
    def test_create_customer_request(self):
        """Test customer creation request"""
        client = QuickBooksAPIClient()
        
        customer_data = {
            "Name": "Test Customer",
            "PrimaryEmailAddr": {"Address": "test@example.com"}
        }
        
        request = QBORequest(
            entity_type=QBOEntityType.CUSTOMER,
            operation=QBOOperationType.CREATE,
            data={"Customer": customer_data}
        )
        
        assert request.entity_type == QBOEntityType.CUSTOMER
        assert request.operation == QBOOperationType.CREATE
        assert request.data["Customer"]["Name"] == "Test Customer"

class TestDataMappingService:
    """Test data mapping service"""
    
    def test_mapping_service_initialization(self):
        """Test mapping service initialization"""
        service = DataMappingService()
        
        assert "tenant_to_customer" in service.mappings
        assert "rent_to_invoice" in service.mappings
        assert len(service.transformation_functions) > 0
    
    def test_tenant_to_customer_mapping(self, sample_tenant_data):
        """Test tenant to customer mapping"""
        service = DataMappingService()
        
        mapped_data = service.map_entity(sample_tenant_data, "tenant_to_customer")
        
        assert mapped_data["GivenName"] == "John"
        assert mapped_data["FamilyName"] == "Doe"
        assert mapped_data["PrimaryEmailAddr.Address"] == "john.doe@example.com"
        assert mapped_data["DisplayName"] == "John Doe - Unit A1"
    
    def test_payment_to_invoice_mapping(self, sample_payment_data):
        """Test payment to invoice mapping"""
        service = DataMappingService()
        
        mapped_data = service.map_entity(sample_payment_data, "rent_to_invoice")
        
        assert mapped_data["Line.0.Amount"] == 1500.00
        assert mapped_data["DocNumber"] == "EC-payment_123"
        assert "Line" in mapped_data  # Should have line items
    
    def test_transformation_functions(self):
        """Test transformation functions"""
        service = DataMappingService()
        
        # Test date formatting
        date_func = service.transformation_functions["format_date"]
        assert date_func("2024-01-01") == "2024-01-01"
        assert date_func(datetime(2024, 1, 1)) == "2024-01-01"
        
        # Test currency formatting
        currency_func = service.transformation_functions["format_currency"]
        assert currency_func(1500) == 1500.0
        assert currency_func("$1,500.00") == 1500.0
    
    def test_validation(self, sample_tenant_data):
        """Test data validation"""
        service = DataMappingService()
        
        mapped_data = service.map_entity(sample_tenant_data, "tenant_to_customer")
        errors = service.validate_mapped_data(mapped_data, QuickBooksEntity.CUSTOMER)
        
        # Should have no validation errors
        assert len(errors) == 0
    
    def test_property_mapping_creation(self):
        """Test property account mapping creation"""
        service = DataMappingService()
        
        mapping = service.create_property_mapping(
            property_id="prop_123",
            property_name="Test Property",
            revenue_account_id="4000",
            expense_account_id="6000",
            deposit_account_id="1200",
            ar_account_id="1300"
        )
        
        assert mapping.property_id == "prop_123"
        assert mapping.property_name == "Test Property"
        assert mapping.revenue_account_id == "4000"

class TestFinancialSyncService:
    """Test financial synchronization service"""
    
    def test_sync_service_initialization(self):
        """Test sync service initialization"""
        service = FinancialSyncService()
        
        assert service.api_client is not None
        assert service.mapping_service is not None
        assert service.oauth_service is not None
    
    @pytest.mark.asyncio
    async def test_sync_tenants_to_customers(self, sample_tenant_data):
        """Test tenant synchronization"""
        # Mock dependencies
        mock_api_client = Mock()
        mock_mapping_service = Mock()
        mock_oauth_service = Mock()
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.connection_id = "test_connection"
        mock_oauth_service.get_organization_connection.return_value = mock_connection
        
        # Mock mapping
        mock_mapping_service.map_entity.return_value = {
            "Name": "John Doe - Unit A1",
            "GivenName": "John",
            "FamilyName": "Doe"
        }
        mock_mapping_service.validate_mapped_data.return_value = []
        
        # Mock API response
        mock_response = Mock()
        mock_response.success = True
        mock_response.data = {"Customer": {"Id": "123"}}
        mock_api_client.execute_request.return_value = mock_response
        
        service = FinancialSyncService(mock_api_client, mock_mapping_service, mock_oauth_service)
        
        result = await service.sync_tenants_to_customers("test_org", [sample_tenant_data])
        
        assert result.status == SyncStatus.COMPLETED
        assert result.successful_records == 1
        assert result.failed_records == 0
    
    @pytest.mark.asyncio
    async def test_sync_payments_to_quickbooks(self, sample_payment_data):
        """Test payment synchronization"""
        # Mock dependencies
        mock_api_client = Mock()
        mock_mapping_service = Mock()
        mock_oauth_service = Mock()
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.connection_id = "test_connection"
        mock_oauth_service.get_organization_connection.return_value = mock_connection
        
        service = FinancialSyncService(mock_api_client, mock_mapping_service, mock_oauth_service)
        
        # Mock the private methods
        service._create_rent_invoice = Mock(return_value={"success": True, "invoice_id": "inv_123"})
        service._create_payment_received = Mock(return_value={"success": True})
        
        result = await service.sync_payments_to_quickbooks("test_org", [sample_payment_data])
        
        assert result.status == SyncStatus.COMPLETED
        assert result.successful_records == 1
    
    def test_sync_configuration_creation(self):
        """Test sync configuration creation"""
        service = FinancialSyncService()
        
        config = service.create_sync_configuration(
            organization_id="test_org",
            auto_sync_enabled=True,
            sync_interval_minutes=30
        )
        
        assert config.organization_id == "test_org"
        assert config.auto_sync_enabled
        assert config.sync_interval_minutes == 30

class TestAutomationEngine:
    """Test automation engine"""
    
    def test_automation_engine_initialization(self):
        """Test automation engine initialization"""
        engine = QuickBooksAutomationEngine()
        
        assert engine.sync_service is not None
        assert engine.api_client is not None
        assert len(engine.workflows) > 0  # Should have default workflows
    
    def test_workflow_schedule_creation(self):
        """Test workflow schedule creation"""
        engine = QuickBooksAutomationEngine()
        
        workflow = engine.create_workflow_schedule(
            workflow_type=WorkflowType.RENT_INVOICE_GENERATION,
            frequency="daily",
            time_of_day="09:00",
            enabled=True
        )
        
        assert workflow.workflow_type == WorkflowType.RENT_INVOICE_GENERATION
        assert workflow.frequency == "daily"
        assert workflow.enabled
    
    def test_manual_workflow_execution(self):
        """Test manual workflow execution"""
        engine = QuickBooksAutomationEngine()
        
        execution_id = engine.execute_workflow_manually(
            workflow_type=WorkflowType.PAYMENT_SYNC,
            organization_id="test_org",
            parameters={"batch_size": 50}
        )
        
        assert execution_id is not None
        assert execution_id in engine.executions
        
        execution = engine.executions[execution_id]
        assert execution.workflow_type == WorkflowType.PAYMENT_SYNC
        assert execution.organization_id == "test_org"
    
    def test_workflow_status_retrieval(self):
        """Test workflow execution status retrieval"""
        engine = QuickBooksAutomationEngine()
        
        execution_id = engine.execute_workflow_manually(
            workflow_type=WorkflowType.LATE_FEE_PROCESSING,
            organization_id="test_org"
        )
        
        status = engine.get_workflow_execution_status(execution_id)
        
        assert status is not None
        assert status["execution_id"] == execution_id
        assert status["workflow_type"] == WorkflowType.LATE_FEE_PROCESSING.value

class TestReconciliationService:
    """Test reconciliation service"""
    
    def test_reconciliation_service_initialization(self):
        """Test reconciliation service initialization"""
        service = ReconciliationService()
        
        assert service.api_client is not None
        assert service.oauth_service is not None
        assert service.amount_tolerance == 0.01
    
    def test_audit_log_creation(self):
        """Test audit log creation"""
        service = ReconciliationService()
        
        service.log_operation(
            organization_id="test_org",
            connection_id="test_conn",
            operation_type="sync",
            entity_type="customer",
            entity_id="customer_123",
            success=True
        )
        
        assert len(service.audit_logs) == 1
        
        log = service.audit_logs[0]
        assert log.organization_id == "test_org"
        assert log.operation_type == "sync"
        assert log.success
    
    def test_reconciliation_execution(self):
        """Test reconciliation execution"""
        service = ReconciliationService()
        
        # Mock connection
        mock_connection = Mock()
        mock_connection.connection_id = "test_conn"
        service.oauth_service.get_organization_connection = Mock(return_value=mock_connection)
        
        # Mock data methods
        service._get_estatecore_tenants = Mock(return_value=[])
        service._get_estatecore_rent_payments = Mock(return_value=[])
        service._get_estatecore_expenses = Mock(return_value=[])
        service.api_client.get_customers = Mock(return_value=[])
        service.api_client.get_invoices = Mock(return_value=[])
        service.api_client.get_payments = Mock(return_value=[])
        
        report = service.reconcile_data("test_org")
        
        assert report.organization_id == "test_org"
        assert report.status in [status for status in report.status.__class__]
    
    def test_data_quality_score(self):
        """Test data quality score calculation"""
        service = ReconciliationService()
        
        score_data = service.get_data_integrity_score("test_org")
        
        assert "integrity_score" in score_data
        assert "total_discrepancies" in score_data
        assert score_data["integrity_score"] >= 0
        assert score_data["integrity_score"] <= 100

class TestEnterpriseFeatures:
    """Test enterprise features"""
    
    def test_enterprise_service_initialization(self):
        """Test enterprise service initialization"""
        service = EnterpriseQuickBooksService()
        
        assert service.api_client is not None
        assert service.sync_service is not None
        assert len(service.portfolios) >= 0
    
    def test_property_portfolio_creation(self):
        """Test property portfolio creation"""
        service = EnterpriseQuickBooksService()
        
        portfolio = service.create_property_portfolio(
            organization_id="test_org",
            portfolio_name="Test Portfolio",
            properties=["prop1", "prop2", "prop3"],
            consolidated_reporting=True
        )
        
        assert portfolio.organization_id == "test_org"
        assert portfolio.portfolio_name == "Test Portfolio"
        assert len(portfolio.properties) == 3
        assert portfolio.consolidated_reporting
    
    def test_user_access_creation(self):
        """Test user access configuration"""
        service = EnterpriseQuickBooksService()
        
        user_access = service.create_user_access(
            user_id="user_123",
            organization_id="test_org",
            access_level=AccessLevel.ADVANCED,
            allowed_properties={"prop1", "prop2"},
            allowed_features={"sync", "automation"},
            allowed_reports={ReportType.PROFIT_LOSS, ReportType.CASH_FLOW}
        )
        
        assert user_access.user_id == "user_123"
        assert user_access.access_level == AccessLevel.ADVANCED
        assert "prop1" in user_access.allowed_properties
        assert "sync" in user_access.allowed_features
    
    def test_permission_checking(self):
        """Test user permission checking"""
        service = EnterpriseQuickBooksService()
        
        # Create user access
        service.create_user_access(
            user_id="user_123",
            organization_id="test_org",
            access_level=AccessLevel.BASIC,
            allowed_properties={"prop1"},
            allowed_features={"read", "sync"}
        )
        
        # Test valid permissions
        assert service.check_user_permission("user_123", "read")
        assert service.check_user_permission("user_123", "sync", "prop1")
        
        # Test invalid permissions
        assert not service.check_user_permission("user_123", "admin")
        assert not service.check_user_permission("user_123", "sync", "prop2")
    
    def test_custom_report_creation(self):
        """Test custom report creation"""
        service = EnterpriseQuickBooksService()
        
        report = service.create_custom_report(
            organization_id="test_org",
            report_name="Monthly P&L",
            report_type=ReportType.PROFIT_LOSS,
            parameters={"period": "monthly"},
            filters={"property_id": "prop1"}
        )
        
        assert report.organization_id == "test_org"
        assert report.report_name == "Monthly P&L"
        assert report.report_type == ReportType.PROFIT_LOSS
    
    def test_white_label_configuration(self):
        """Test white-label configuration"""
        service = EnterpriseQuickBooksService()
        
        config = service.create_whitelabel_config(
            organization_id="test_org",
            company_name="Acme Property Management",
            primary_color="#ff0000",
            logo_url="https://example.com/logo.png"
        )
        
        assert config.organization_id == "test_org"
        assert config.company_name == "Acme Property Management"
        assert config.primary_color == "#ff0000"
    
    def test_branding_application(self):
        """Test branding application"""
        service = EnterpriseQuickBooksService()
        
        # Create white-label config
        service.create_whitelabel_config(
            organization_id="test_org",
            company_name="Acme Property Management",
            primary_color="#ff0000"
        )
        
        # Test content branding
        content = "<h1>EstateCore Dashboard</h1><p style='color: #007bff'>Welcome</p>"
        branded_content = service.apply_branding("test_org", content, "html")
        
        assert "Acme Property Management" in branded_content
        assert "#ff0000" in branded_content

class TestQuickBooksIntegrationService:
    """Test main integration service"""
    
    def test_integration_service_initialization(self):
        """Test integration service initialization"""
        service = QuickBooksIntegrationService()
        
        assert service.oauth_service is not None
        assert service.api_client is not None
        assert service.sync_service is not None
        assert service.automation_engine is not None
        assert service.reconciliation_service is not None
        assert service.enterprise_service is not None
    
    def test_oauth_flow_initiation(self):
        """Test OAuth flow initiation"""
        service = QuickBooksIntegrationService()
        
        with patch.object(service.oauth_service, 'generate_authorization_url', 
                         return_value=("https://oauth.url", "state123")):
            result = service.start_oauth_flow("test_org")
            
            assert result["success"]
            assert "authorization_url" in result
            assert "state" in result
    
    def test_connection_status_retrieval(self):
        """Test connection status retrieval"""
        service = QuickBooksIntegrationService()
        
        # Test no connection
        with patch.object(service.oauth_service, 'get_organization_connection', return_value=None):
            status = service.get_connection_status("test_org")
            
            assert not status["connected"]
            assert status["status"] == "not_connected"
    
    @pytest.mark.asyncio
    async def test_full_data_sync(self):
        """Test full data synchronization"""
        service = QuickBooksIntegrationService()
        
        # Mock dependencies
        mock_connection = Mock()
        mock_connection.connection_id = "test_conn"
        
        with patch.object(service.oauth_service, 'get_organization_connection', return_value=mock_connection):
            with patch.object(service, '_get_organization_tenants', return_value=[]):
                with patch.object(service, '_get_organization_payments', return_value=[]):
                    with patch.object(service, '_get_organization_expenses', return_value=[]):
                        result = await service.sync_all_data("test_org", "both")
                        
                        assert result["success"]
                        assert "results" in result
    
    def test_integration_health_assessment(self):
        """Test integration health assessment"""
        service = QuickBooksIntegrationService()
        
        # Mock all the health check methods
        with patch.object(service, 'get_connection_status', return_value={"connected": True, "status": "connected"}):
            with patch.object(service.sync_service, 'get_sync_configuration', return_value=None):
                with patch.object(service.sync_service, 'get_sync_history', return_value=[]):
                    with patch.object(service, 'get_automation_status', return_value={"automation_enabled": True}):
                        with patch.object(service, 'get_data_quality_score', return_value={"success": True, "data_quality": {"integrity_score": 95}}):
                            health = service.get_integration_health("test_org", force_refresh=True)
                            
                            assert health.status is not None
                            assert health.connection_health is not None
                            assert health.last_check is not None

# Integration Tests
class TestIntegrationFlow:
    """Test end-to-end integration flows"""
    
    @pytest.mark.asyncio
    async def test_complete_sync_flow(self, sample_tenant_data, sample_payment_data):
        """Test complete synchronization flow"""
        # This would test the full flow from EstateCore data to QuickBooks
        # In a real test environment, this would use test QuickBooks sandbox
        
        service = QuickBooksIntegrationService()
        
        # Mock OAuth connection
        mock_connection = Mock()
        mock_connection.connection_id = "test_conn"
        mock_connection.organization_id = "test_org"
        
        with patch.object(service.oauth_service, 'get_organization_connection', return_value=mock_connection):
            # Mock data retrieval
            with patch.object(service, '_get_organization_tenants', return_value=[sample_tenant_data]):
                with patch.object(service, '_get_organization_payments', return_value=[sample_payment_data]):
                    with patch.object(service, '_get_organization_expenses', return_value=[]):
                        # Mock API responses
                        mock_sync_result = Mock()
                        mock_sync_result.status = SyncStatus.COMPLETED
                        mock_sync_result.successful_records = 1
                        mock_sync_result.failed_records = 0
                        
                        with patch.object(service.sync_service, 'sync_tenants_to_customers', return_value=mock_sync_result):
                            with patch.object(service.sync_service, 'sync_payments_to_quickbooks', return_value=mock_sync_result):
                                result = await service.sync_all_data("test_org", "to_qb")
                                
                                assert result["success"]
                                assert "tenants_to_customers" in result["results"]
                                assert "payments" in result["results"]

# Performance Tests
class TestPerformance:
    """Test performance characteristics"""
    
    def test_large_dataset_mapping(self):
        """Test mapping performance with large datasets"""
        service = DataMappingService()
        
        # Create large dataset
        large_dataset = []
        for i in range(1000):
            tenant = {
                "tenant_id": f"tenant_{i}",
                "first_name": f"First{i}",
                "last_name": f"Last{i}",
                "email": f"tenant{i}@example.com",
                "unit_number": f"Unit{i}"
            }
            large_dataset.append(tenant)
        
        # Time the mapping operation
        start_time = datetime.now()
        mapped_data = []
        
        for tenant in large_dataset:
            mapped = service.map_entity(tenant, "tenant_to_customer")
            mapped_data.append(mapped)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (adjust based on requirements)
        assert duration < 10.0  # 10 seconds for 1000 records
        assert len(mapped_data) == 1000
    
    @pytest.mark.asyncio
    async def test_batch_sync_performance(self):
        """Test batch synchronization performance"""
        service = FinancialSyncService()
        
        # Mock large dataset
        large_tenant_dataset = []
        for i in range(100):
            tenant = {
                "tenant_id": f"tenant_{i}",
                "first_name": f"First{i}",
                "last_name": f"Last{i}",
                "email": f"tenant{i}@example.com"
            }
            large_tenant_dataset.append(tenant)
        
        # Mock dependencies for performance test
        mock_connection = Mock()
        mock_connection.connection_id = "test_conn"
        
        with patch.object(service.oauth_service, 'get_organization_connection', return_value=mock_connection):
            with patch.object(service.mapping_service, 'map_entity', return_value={"Name": "Test"}):
                with patch.object(service.mapping_service, 'validate_mapped_data', return_value=[]):
                    mock_response = Mock()
                    mock_response.success = True
                    mock_response.data = {"Customer": {"Id": "123"}}
                    
                    with patch.object(service.api_client, 'execute_request', return_value=mock_response):
                        start_time = datetime.now()
                        
                        result = await service.sync_tenants_to_customers("test_org", large_tenant_dataset)
                        
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds()
                        
                        # Should complete within reasonable time
                        assert duration < 30.0  # 30 seconds for 100 records
                        assert result.successful_records == 100

# Error Handling Tests
class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_oauth_failure_handling(self):
        """Test OAuth failure scenarios"""
        service = QuickBooksOAuthService()
        
        # Test invalid state
        with patch.object(service, '_validate_oauth_state', return_value=None):
            with pytest.raises(ValueError, match="Invalid or expired OAuth state"):
                service.exchange_code_for_tokens("code", "invalid_state", "realm_id")
    
    @patch('requests.post')
    def test_api_client_error_handling(self, mock_post, mock_connection):
        """Test API client error handling"""
        mock_oauth_service = Mock()
        mock_oauth_service.ensure_valid_token.return_value = "valid_token"
        
        # Mock network error
        mock_post.side_effect = Exception("Network error")
        
        client = QuickBooksAPIClient(mock_oauth_service)
        
        with pytest.raises(Exception):
            client._make_request(mock_connection, 'POST', 'customers', data={"test": "data"})
    
    @pytest.mark.asyncio
    async def test_sync_partial_failure(self, sample_tenant_data):
        """Test sync partial failure handling"""
        service = FinancialSyncService()
        
        # Mock connection
        mock_connection = Mock()
        service.oauth_service.get_organization_connection = Mock(return_value=mock_connection)
        
        # Mock mapping - one success, one failure
        def mock_map_entity(data, mapping_type):
            if data.get("tenant_id") == "tenant_fail":
                raise Exception("Mapping failed")
            return {"Name": "Test Customer"}
        
        service.mapping_service.map_entity = mock_map_entity
        service.mapping_service.validate_mapped_data = Mock(return_value=[])
        
        # Mock API response
        mock_response = Mock()
        mock_response.success = True
        service.api_client.execute_request = Mock(return_value=mock_response)
        
        # Test data with one failing tenant
        test_data = [
            sample_tenant_data,
            {**sample_tenant_data, "tenant_id": "tenant_fail"}
        ]
        
        result = await service.sync_tenants_to_customers("test_org", test_data)
        
        assert result.status == SyncStatus.PARTIAL
        assert result.successful_records == 1
        assert result.failed_records == 1
        assert len(result.errors) == 1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
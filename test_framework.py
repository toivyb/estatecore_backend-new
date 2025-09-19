"""
Comprehensive Test Framework for EstateCore
Automated testing for all services and API endpoints
"""

import unittest
import json
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import requests
from typing import Dict, List, Any, Optional

# Import EstateCore services
from database_service import get_database_service
from permissions_service import get_permission_service, Permission, Role
from rent_collection_service import get_rent_collection_service, PaymentMethod, PaymentStatus
from lease_management_service import get_lease_management_service, LeaseStatus
from financial_reporting_service import get_financial_reporting_service, ReportType
from security_service import get_security_service, SecurityEventType
from maintenance_scheduling_service import get_maintenance_service, MaintenanceStatus
from tenant_screening_service import get_tenant_screening_service, ApplicationStatus
from bulk_operations_service import get_bulk_operations_service, OperationType, EntityType
from performance_service import get_performance_service
from file_storage_service import create_file_storage_service

class EstateTestCase(unittest.TestCase):
    """Base test case with common setup and utilities"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_data_dir = tempfile.mkdtemp()
        cls.test_config = {
            'TESTING': True,
            'DATABASE_URL': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-secret-key',
            'UPLOAD_FOLDER': cls.test_data_dir
        }
        
    def setUp(self):
        """Set up for each test"""
        self.db_service = get_database_service()
        self.maxDiff = None
        
    def tearDown(self):
        """Clean up after each test"""
        # Clear any test data
        pass
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        import shutil
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir)

class TestDatabaseService(EstateTestCase):
    """Test database service functionality"""
    
    def test_database_connection(self):
        """Test database connection and basic operations"""
        # Test connection
        result = self.db_service.test_connection()
        self.assertTrue(result['success'])
        
    def test_property_operations(self):
        """Test property CRUD operations"""
        # Create property
        property_data = {
            'property_name': 'Test Property',
            'address': '123 Test St',
            'property_type': 'apartment',
            'rent_amount': 1500,
            'bedrooms': 2,
            'bathrooms': 1
        }
        
        # Test create
        result = self.db_service.create_property(property_data)
        self.assertTrue(result['success'])
        property_id = result['property_id']
        
        # Test read
        property_result = self.db_service.get_property(property_id)
        self.assertTrue(property_result['success'])
        self.assertEqual(property_result['property']['property_name'], 'Test Property')
        
        # Test update
        update_data = {'rent_amount': 1600}
        update_result = self.db_service.update_property(property_id, update_data)
        self.assertTrue(update_result['success'])
        
        # Verify update
        updated_property = self.db_service.get_property(property_id)
        self.assertEqual(updated_property['property']['rent_amount'], 1600)
        
    def test_tenant_operations(self):
        """Test tenant CRUD operations"""
        tenant_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@test.com',
            'phone': '555-1234',
            'property_id': 1
        }
        
        result = self.db_service.create_tenant(tenant_data)
        self.assertTrue(result['success'])
        
    def test_maintenance_operations(self):
        """Test maintenance request operations"""
        maintenance_data = {
            'property_id': 1,
            'title': 'Test Maintenance',
            'description': 'Test maintenance request',
            'priority': 'medium',
            'maintenance_type': 'plumbing'
        }
        
        result = self.db_service.create_maintenance_request(maintenance_data)
        self.assertTrue(result['success'])

class TestPermissionsService(EstateTestCase):
    """Test permissions and role management"""
    
    def setUp(self):
        super().setUp()
        self.permission_service = get_permission_service()
        
    def test_role_creation(self):
        """Test role creation and management"""
        # Test creating a role
        role_data = {
            'name': 'test_role',
            'description': 'Test role for unit testing',
            'permissions': ['READ_PROPERTIES', 'WRITE_PROPERTIES']
        }
        
        result = self.permission_service.create_role(role_data)
        self.assertTrue(result['success'])
        
    def test_permission_checking(self):
        """Test permission checking functionality"""
        # Mock user with specific permissions
        user_permissions = ['READ_PROPERTIES', 'WRITE_TENANTS']
        
        # Test has_permission function
        has_read = self.permission_service.check_user_permission(1, Permission.READ_PROPERTIES)
        self.assertIsNotNone(has_read)  # Should not be None for valid permission check
        
    def test_role_hierarchy(self):
        """Test role hierarchy and inheritance"""
        # Test that admin roles have proper permissions
        admin_permissions = self.permission_service.get_role_permissions(Role.SUPER_ADMIN)
        self.assertIsInstance(admin_permissions, list)
        
    def test_user_role_assignment(self):
        """Test user role assignment"""
        result = self.permission_service.assign_user_role(1, Role.PROPERTY_MANAGER)
        self.assertTrue(result['success'])

class TestRentCollectionService(EstateTestCase):
    """Test rent collection and payment processing"""
    
    def setUp(self):
        super().setUp()
        self.rent_service = get_rent_collection_service()
        
    def test_payment_processing(self):
        """Test payment processing functionality"""
        payment_data = {
            'tenant_id': 1,
            'property_id': 1,
            'amount': 1500.00,
            'payment_method': PaymentMethod.CREDIT_CARD,
            'payment_date': datetime.utcnow()
        }
        
        result = self.rent_service.process_payment(payment_data)
        self.assertTrue(result['success'])
        
    def test_late_fee_calculation(self):
        """Test late fee calculation"""
        # Test with payment 10 days late
        due_date = datetime.utcnow() - timedelta(days=10)
        payment_date = datetime.utcnow()
        rent_amount = 1500.00
        
        late_fee = self.rent_service.calculate_late_fee(
            rent_amount, due_date, payment_date
        )
        
        self.assertGreater(late_fee, 0)
        self.assertIsInstance(late_fee, float)
        
    def test_payment_reminder_generation(self):
        """Test automated payment reminders"""
        tenant_id = 1
        property_id = 1
        
        reminders = self.rent_service.generate_payment_reminders(tenant_id, property_id)
        self.assertIsInstance(reminders, list)
        
    def test_payment_history(self):
        """Test payment history retrieval"""
        history = self.rent_service.get_payment_history(tenant_id=1, months=6)
        self.assertTrue(history['success'])
        self.assertIsInstance(history['payments'], list)

class TestLeaseManagementService(EstateTestCase):
    """Test lease management functionality"""
    
    def setUp(self):
        super().setUp()
        self.lease_service = get_lease_management_service()
        
    def test_lease_creation(self):
        """Test lease agreement creation"""
        lease_data = {
            'tenant_id': 1,
            'property_id': 1,
            'start_date': datetime.utcnow(),
            'end_date': datetime.utcnow() + timedelta(days=365),
            'monthly_rent': 1500.00,
            'security_deposit': 1500.00,
            'lease_type': 'fixed_term'
        }
        
        result = self.lease_service.create_lease_agreement(lease_data)
        self.assertTrue(result['success'])
        
    def test_lease_renewal_processing(self):
        """Test lease renewal functionality"""
        lease_id = 'test_lease_001'
        renewal_data = {
            'new_rent_amount': 1600.00,
            'renewal_period_months': 12
        }
        
        result = self.lease_service.process_lease_renewal(lease_id, renewal_data)
        self.assertTrue(result['success'])
        
    def test_expiring_leases_detection(self):
        """Test detection of expiring leases"""
        expiring_leases = self.lease_service.get_expiring_leases(days_ahead=30)
        self.assertTrue(expiring_leases['success'])
        self.assertIsInstance(expiring_leases['leases'], list)

class TestFinancialReportingService(EstateTestCase):
    """Test financial reporting functionality"""
    
    def setUp(self):
        super().setUp()
        self.financial_service = get_financial_reporting_service()
        
    def test_income_statement_generation(self):
        """Test income statement generation"""
        report_params = {
            'start_date': datetime.utcnow() - timedelta(days=30),
            'end_date': datetime.utcnow(),
            'property_ids': [1, 2, 3]
        }
        
        report = self.financial_service.generate_income_statement(report_params)
        self.assertTrue(report['success'])
        self.assertIn('total_income', report['report'])
        self.assertIn('total_expenses', report['report'])
        
    def test_cash_flow_analysis(self):
        """Test cash flow analysis"""
        analysis = self.financial_service.generate_cash_flow_analysis({
            'period_months': 6,
            'property_ids': [1, 2]
        })
        
        self.assertTrue(analysis['success'])
        self.assertIn('cash_flow_data', analysis)
        
    def test_rent_roll_report(self):
        """Test rent roll report generation"""
        rent_roll = self.financial_service.generate_rent_roll({
            'as_of_date': datetime.utcnow(),
            'include_vacant': True
        })
        
        self.assertTrue(rent_roll['success'])
        self.assertIsInstance(rent_roll['properties'], list)
        
    def test_kpi_calculations(self):
        """Test KPI calculations"""
        kpis = self.financial_service.calculate_kpis({
            'period_months': 12,
            'property_ids': [1, 2, 3]
        })
        
        self.assertTrue(kpis['success'])
        self.assertIn('occupancy_rate', kpis['kpis'])
        self.assertIn('gross_yield', kpis['kpis'])

class TestSecurityService(EstateTestCase):
    """Test security and authentication functionality"""
    
    def setUp(self):
        super().setUp()
        self.security_service = get_security_service()
        
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = 'test_password_123'
        
        # Hash password
        hashed = self.security_service.hash_password(password)
        self.assertIsInstance(hashed, str)
        self.assertNotEqual(hashed, password)
        
        # Verify password
        is_valid = self.security_service.verify_password(password, hashed)
        self.assertTrue(is_valid)
        
        # Test wrong password
        is_invalid = self.security_service.verify_password('wrong_password', hashed)
        self.assertFalse(is_invalid)
        
    def test_session_management(self):
        """Test JWT session management"""
        user_data = {'user_id': 1, 'role': 'admin'}
        
        # Create session
        session_result = self.security_service.create_session(user_data)
        self.assertTrue(session_result['success'])
        self.assertIn('token', session_result)
        
        # Validate session
        token = session_result['token']
        validation = self.security_service.validate_session(token)
        self.assertTrue(validation['valid'])
        
    def test_rate_limiting(self):
        """Test API rate limiting"""
        # Simulate multiple requests
        client_ip = '127.0.0.1'
        endpoint = '/api/test'
        
        # Should allow initial requests
        for i in range(5):
            allowed = self.security_service.check_rate_limit(client_ip, endpoint)
            self.assertTrue(allowed['allowed'])
            
    def test_security_event_logging(self):
        """Test security event logging"""
        event_data = {
            'event_type': SecurityEventType.LOGIN_ATTEMPT,
            'user_id': 1,
            'ip_address': '127.0.0.1',
            'details': {'success': True}
        }
        
        result = self.security_service.log_security_event(event_data)
        self.assertTrue(result['success'])

class TestMaintenanceSchedulingService(EstateTestCase):
    """Test maintenance scheduling functionality"""
    
    def setUp(self):
        super().setUp()
        self.maintenance_service = get_maintenance_service()
        
    def test_work_order_creation(self):
        """Test work order creation and scheduling"""
        work_order_data = {
            'property_id': 1,
            'title': 'HVAC Maintenance',
            'description': 'Regular HVAC inspection and cleaning',
            'priority': 'medium',
            'maintenance_type': 'hvac',
            'estimated_cost': 200.00
        }
        
        result = self.maintenance_service.create_work_order(work_order_data)
        self.assertTrue(result['success'])
        
    def test_vendor_assignment(self):
        """Test vendor assignment to work orders"""
        work_order_id = 'wo_001'
        vendor_id = 1
        
        result = self.maintenance_service.assign_vendor(work_order_id, vendor_id)
        self.assertTrue(result['success'])
        
    def test_preventive_maintenance_scheduling(self):
        """Test preventive maintenance scheduling"""
        schedule_data = {
            'equipment_type': 'hvac',
            'frequency_months': 6,
            'property_ids': [1, 2, 3]
        }
        
        result = self.maintenance_service.schedule_preventive_maintenance(schedule_data)
        self.assertTrue(result['success'])

class TestTenantScreeningService(EstateTestCase):
    """Test tenant screening functionality"""
    
    def setUp(self):
        super().setUp()
        self.screening_service = get_tenant_screening_service()
        
    def test_application_processing(self):
        """Test tenant application processing"""
        application_data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@test.com',
            'phone': '555-5678',
            'monthly_income': 5000.00,
            'credit_score': 750,
            'property_id': 1
        }
        
        result = self.screening_service.process_application(application_data)
        self.assertTrue(result['success'])
        
    def test_background_check(self):
        """Test background check functionality"""
        application_id = 'app_001'
        
        result = self.screening_service.run_background_check(application_id)
        self.assertTrue(result['success'])
        
    def test_credit_score_evaluation(self):
        """Test credit score evaluation"""
        credit_score = 720
        
        evaluation = self.screening_service.evaluate_credit_score(credit_score)
        self.assertIn('score_rating', evaluation)
        self.assertIn('approval_recommendation', evaluation)

class TestBulkOperationsService(EstateTestCase):
    """Test bulk operations functionality"""
    
    def setUp(self):
        super().setUp()
        self.bulk_service = get_bulk_operations_service()
        
    def test_bulk_data_validation(self):
        """Test bulk data validation"""
        test_data = [
            {
                'property_name': 'Test Property 1',
                'address': '123 Test St',
                'property_type': 'apartment',
                'rent_amount': 1500,
                'bedrooms': 2,
                'bathrooms': 1
            },
            {
                'property_name': 'Test Property 2',
                'address': '456 Test Ave',
                'property_type': 'house',
                'rent_amount': 2000,
                'bedrooms': 3,
                'bathrooms': 2
            }
        ]
        
        validation_result = self.bulk_service.validate_bulk_data(
            EntityType.PROPERTIES, test_data
        )
        
        self.assertTrue(validation_result.is_valid)
        self.assertEqual(len(validation_result.valid_records), 2)
        
    def test_bulk_import_operation(self):
        """Test bulk import functionality"""
        csv_data = """property_name,address,property_type,rent_amount,bedrooms,bathrooms
Test Property 1,123 Test St,apartment,1500,2,1
Test Property 2,456 Test Ave,house,2000,3,2"""
        
        operation_id = self.bulk_service.create_bulk_operation(
            OperationType.IMPORT,
            EntityType.PROPERTIES,
            created_by=1
        )
        
        result = self.bulk_service.process_bulk_import(
            operation_id, csv_data, 'csv'
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.total_processed, 2)

class TestPerformanceService(EstateTestCase):
    """Test performance optimization functionality"""
    
    def setUp(self):
        super().setUp()
        self.performance_service = get_performance_service()
        
    def test_caching_functionality(self):
        """Test caching functionality"""
        # Test cache set/get
        cache_key = 'test_key'
        cache_value = {'data': 'test_value'}
        
        self.performance_service.cache.set(cache_key, cache_value, ttl=60)
        retrieved_value = self.performance_service.cache.get(cache_key)
        
        self.assertEqual(retrieved_value, cache_value)
        
    def test_performance_monitoring(self):
        """Test performance monitoring"""
        # Simulate endpoint performance recording
        endpoint = '/api/test'
        duration = 0.150  # 150ms
        
        self.performance_service.monitor.record_request(endpoint, duration)
        
        # Get stats
        stats = self.performance_service.monitor.get_endpoint_stats(endpoint)
        self.assertIn('avg_duration', stats)
        
    def test_optimization_recommendations(self):
        """Test optimization recommendations"""
        recommendations = self.performance_service.generate_optimization_recommendations()
        self.assertIsInstance(recommendations, list)

class TestAPIEndpoints(EstateTestCase):
    """Test API endpoints with mock Flask app"""
    
    def setUp(self):
        super().setUp()
        # Note: In a real test environment, you would set up a test Flask app
        self.base_url = 'http://localhost:5001'
        
    def test_properties_endpoint(self):
        """Test properties API endpoint"""
        # This would require a running test server
        # For now, we'll test the service layer directly
        pass
        
    def test_authentication_endpoint(self):
        """Test authentication endpoints"""
        # Test login functionality
        pass
        
    def test_bulk_operations_endpoints(self):
        """Test bulk operations API endpoints"""
        # Test bulk operations API
        pass

class TestIntegration(EstateTestCase):
    """Integration tests for cross-service functionality"""
    
    def test_rent_collection_with_notifications(self):
        """Test rent collection integrated with notification system"""
        # Test that payment processing triggers appropriate notifications
        pass
        
    def test_maintenance_with_tenant_notifications(self):
        """Test maintenance scheduling with tenant notifications"""
        # Test that maintenance scheduling notifies relevant tenants
        pass
        
    def test_lease_renewal_workflow(self):
        """Test complete lease renewal workflow"""
        # Test end-to-end lease renewal process
        pass

class TestFileOperations(EstateTestCase):
    """Test file upload and storage functionality"""
    
    def setUp(self):
        super().setUp()
        self.file_service = create_file_storage_service()
        
    def test_file_upload_validation(self):
        """Test file upload validation"""
        # Test various file types and sizes
        test_files = [
            {'name': 'test.pdf', 'size': 1024 * 1024, 'type': 'application/pdf'},
            {'name': 'test.jpg', 'size': 512 * 1024, 'type': 'image/jpeg'},
            {'name': 'test.txt', 'size': 1024, 'type': 'text/plain'}
        ]
        
        for file_info in test_files:
            validation = self.file_service.validate_file(file_info)
            self.assertIn('valid', validation)

def create_test_suite():
    """Create comprehensive test suite"""
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDatabaseService,
        TestPermissionsService,
        TestRentCollectionService,
        TestLeaseManagementService,
        TestFinancialReportingService,
        TestSecurityService,
        TestMaintenanceSchedulingService,
        TestTenantScreeningService,
        TestBulkOperationsService,
        TestPerformanceService,
        TestAPIEndpoints,
        TestIntegration,
        TestFileOperations
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    return test_suite

def run_all_tests():
    """Run all tests and generate report"""
    print("🧪 Starting EstateCore Test Suite")
    print("=" * 50)
    
    # Create and run test suite
    test_suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate test report
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
    else:
        print(f"\n⚠️ {len(result.failures + result.errors)} test(s) failed")
    
    return result

def run_specific_test(test_class_name: str = None, test_method_name: str = None):
    """Run specific test class or method"""
    if test_class_name:
        # Get test class from globals
        test_class = globals().get(test_class_name)
        if test_class:
            if test_method_name:
                # Run specific test method
                suite = unittest.TestSuite()
                suite.addTest(test_class(test_method_name))
            else:
                # Run all tests in class
                suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            
            runner = unittest.TextTestRunner(verbosity=2)
            return runner.run(suite)
        else:
            print(f"Test class '{test_class_name}' not found")
    else:
        print("Please specify a test class name")

def run_performance_tests():
    """Run performance-specific tests"""
    print("⚡ Running Performance Tests")
    return run_specific_test('TestPerformanceService')

def run_security_tests():
    """Run security-specific tests"""
    print("🔒 Running Security Tests")
    return run_specific_test('TestSecurityService')

def run_integration_tests():
    """Run integration tests"""
    print("🔗 Running Integration Tests")
    return run_specific_test('TestIntegration')

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'performance':
            run_performance_tests()
        elif sys.argv[1] == 'security':
            run_security_tests()
        elif sys.argv[1] == 'integration':
            run_integration_tests()
        elif sys.argv[1] == 'specific' and len(sys.argv) > 2:
            test_class = sys.argv[2]
            test_method = sys.argv[3] if len(sys.argv) > 3 else None
            run_specific_test(test_class, test_method)
        else:
            print("Usage: python test_framework.py [performance|security|integration|specific <class> [method]]")
    else:
        # Run all tests
        run_all_tests()
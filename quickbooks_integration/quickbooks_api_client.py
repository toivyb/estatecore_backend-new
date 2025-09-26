"""
QuickBooks Online API Client

Comprehensive API client for QuickBooks Online with full CRUD operations,
data synchronization, error handling, and enterprise features.
"""

import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import time
from urllib.parse import urlencode

from .quickbooks_oauth_service import QuickBooksOAuthService, QuickBooksConnection

logger = logging.getLogger(__name__)

class QBOEntityType(Enum):
    """QuickBooks Online entity types"""
    ACCOUNT = "Account"
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    ITEM = "Item"
    INVOICE = "Invoice"
    BILL = "Bill"
    PAYMENT = "Payment"
    BILL_PAYMENT = "BillPayment"
    EXPENSE = "Purchase"
    JOURNAL_ENTRY = "JournalEntry"
    TAX_CODE = "TaxCode"
    TAX_RATE = "TaxRate"
    COMPANY_INFO = "CompanyInfo"
    PREFERENCES = "Preferences"
    DEPOSIT = "Deposit"
    TRANSFER = "Transfer"

class QBOOperationType(Enum):
    """QuickBooks operation types"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    QUERY = "query"

@dataclass
class QBORequest:
    """Represents a QuickBooks API request"""
    entity_type: QBOEntityType
    operation: QBOOperationType
    data: Optional[Dict[str, Any]] = None
    entity_id: Optional[str] = None
    query: Optional[str] = None
    company_id: Optional[str] = None

@dataclass
class QBOResponse:
    """Represents a QuickBooks API response"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    fault: Optional[Dict[str, Any]] = None
    warnings: Optional[List[Dict[str, Any]]] = None
    query_response: Optional[Dict[str, Any]] = None
    batch_item_response: Optional[List[Dict[str, Any]]] = None

@dataclass
class QBOSyncResult:
    """Results from synchronization operations"""
    entity_type: QBOEntityType
    operation: str
    total_records: int
    successful_records: int
    failed_records: int
    errors: List[Dict[str, Any]]
    sync_time: datetime
    duration_seconds: float

class QuickBooksAPIError(Exception):
    """Custom exception for QuickBooks API errors"""
    def __init__(self, message: str, fault_code: Optional[str] = None, fault_detail: Optional[str] = None):
        super().__init__(message)
        self.fault_code = fault_code
        self.fault_detail = fault_detail

class QuickBooksAPIClient:
    """
    Comprehensive QuickBooks Online API client with enterprise features
    """
    
    def __init__(self, oauth_service: Optional[QuickBooksOAuthService] = None):
        self.oauth_service = oauth_service or QuickBooksOAuthService()
        
        # API configuration
        self.api_version = "v3"
        self.max_retries = 3
        self.retry_delay = 1.0
        self.timeout = 30
        
        # Rate limiting
        self.rate_limit_delay = 0.1  # Delay between requests
        self.last_request_time = 0
        
        # Batch operation settings
        self.max_batch_size = 30  # QuickBooks limit
        
        # Cache for frequently accessed data
        self._account_cache: Dict[str, Dict[str, Any]] = {}
        self._customer_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_expiry = timedelta(minutes=15)
        self._cache_timestamps: Dict[str, datetime] = {}
    
    def _wait_for_rate_limit(self):
        """Implement rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, connection: QuickBooksConnection, method: str, 
                     endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> requests.Response:
        """
        Make authenticated request to QuickBooks API with retry logic
        """
        self._wait_for_rate_limit()
        
        # Ensure valid token
        access_token = self.oauth_service.ensure_valid_token(connection.connection_id)
        if not access_token:
            raise QuickBooksAPIError("Failed to obtain valid access token")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        if method in ['POST', 'PUT']:
            headers['Content-Type'] = 'application/json'
        
        url = f"{connection.base_url}/{self.api_version}/company/{connection.company_id}/{endpoint}"
        
        for attempt in range(self.max_retries + 1):
            try:
                if method == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=data, params=params, timeout=self.timeout)
                elif method == 'PUT':
                    response = requests.put(url, headers=headers, json=data, params=params, timeout=self.timeout)
                elif method == 'DELETE':
                    response = requests.delete(url, headers=headers, params=params, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 60))
                    logger.warning(f"Rate limited, waiting {retry_after} seconds")
                    time.sleep(retry_after)
                    continue
                
                return response
                
            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Request timeout, retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    raise QuickBooksAPIError("Request timeout after retries")
            
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Connection error, retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                else:
                    raise QuickBooksAPIError("Connection error after retries")
        
        raise QuickBooksAPIError("Maximum retries exceeded")
    
    def _parse_response(self, response: requests.Response) -> QBOResponse:
        """Parse QuickBooks API response"""
        try:
            if response.status_code == 200:
                data = response.json()
                
                # Check for fault in response
                if 'Fault' in data:
                    fault = data['Fault']
                    error_msg = fault.get('Error', [{}])[0].get('Detail', 'Unknown error')
                    return QBOResponse(
                        success=False,
                        error=error_msg,
                        fault=fault
                    )
                
                # Handle warnings
                warnings = data.get('Warnings')
                
                # Extract actual data
                query_response = data.get('QueryResponse')
                batch_response = data.get('BatchItemResponse')
                
                return QBOResponse(
                    success=True,
                    data=data,
                    warnings=warnings,
                    query_response=query_response,
                    batch_item_response=batch_response
                )
            
            else:
                # Try to parse error response
                try:
                    error_data = response.json()
                    fault = error_data.get('Fault', {})
                    error_msg = fault.get('Error', [{}])[0].get('Detail', f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                
                return QBOResponse(
                    success=False,
                    error=error_msg
                )
                
        except json.JSONDecodeError:
            return QBOResponse(
                success=False,
                error=f"Invalid JSON response: {response.text}"
            )
    
    def execute_request(self, connection_id: str, request: QBORequest) -> QBOResponse:
        """Execute a QuickBooks API request"""
        connection = self.oauth_service.get_connection(connection_id)
        if not connection:
            return QBOResponse(success=False, error="Connection not found")
        
        try:
            if request.operation == QBOOperationType.CREATE:
                return self._create_entity(connection, request)
            elif request.operation == QBOOperationType.READ:
                return self._read_entity(connection, request)
            elif request.operation == QBOOperationType.UPDATE:
                return self._update_entity(connection, request)
            elif request.operation == QBOOperationType.DELETE:
                return self._delete_entity(connection, request)
            elif request.operation == QBOOperationType.QUERY:
                return self._query_entities(connection, request)
            else:
                return QBOResponse(success=False, error=f"Unsupported operation: {request.operation}")
        
        except Exception as e:
            logger.error(f"Request execution failed: {e}")
            return QBOResponse(success=False, error=str(e))
    
    def _create_entity(self, connection: QuickBooksConnection, request: QBORequest) -> QBOResponse:
        """Create a new entity"""
        endpoint = request.entity_type.value.lower()
        response = self._make_request(connection, 'POST', endpoint, data=request.data)
        return self._parse_response(response)
    
    def _read_entity(self, connection: QuickBooksConnection, request: QBORequest) -> QBOResponse:
        """Read an entity by ID"""
        endpoint = f"{request.entity_type.value.lower()}/{request.entity_id}"
        response = self._make_request(connection, 'GET', endpoint)
        return self._parse_response(response)
    
    def _update_entity(self, connection: QuickBooksConnection, request: QBORequest) -> QBOResponse:
        """Update an entity"""
        endpoint = request.entity_type.value.lower()
        response = self._make_request(connection, 'POST', endpoint, data=request.data)
        return self._parse_response(response)
    
    def _delete_entity(self, connection: QuickBooksConnection, request: QBORequest) -> QBOResponse:
        """Delete an entity (soft delete)"""
        endpoint = f"{request.entity_type.value.lower()}?operation=delete"
        response = self._make_request(connection, 'POST', endpoint, data=request.data)
        return self._parse_response(response)
    
    def _query_entities(self, connection: QuickBooksConnection, request: QBORequest) -> QBOResponse:
        """Query entities using SQL-like syntax"""
        params = {'query': request.query}
        response = self._make_request(connection, 'GET', 'query', params=params)
        return self._parse_response(response)
    
    # High-level entity operations
    
    def get_accounts(self, connection_id: str, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get chart of accounts with caching"""
        cache_key = f"accounts_{connection_id}"
        
        # Check cache
        if not force_refresh and cache_key in self._account_cache:
            cache_time = self._cache_timestamps.get(cache_key)
            if cache_time and datetime.now() - cache_time < self._cache_expiry:
                return self._account_cache[cache_key]
        
        # Fetch from API
        request = QBORequest(
            entity_type=QBOEntityType.ACCOUNT,
            operation=QBOOperationType.QUERY,
            query="SELECT * FROM Account"
        )
        
        response = self.execute_request(connection_id, request)
        if response.success and response.query_response:
            accounts = response.query_response.get('Account', [])
            
            # Cache results
            self._account_cache[cache_key] = accounts
            self._cache_timestamps[cache_key] = datetime.now()
            
            return accounts
        
        return []
    
    def create_customer(self, connection_id: str, customer_data: Dict[str, Any]) -> QBOResponse:
        """Create a new customer"""
        request = QBORequest(
            entity_type=QBOEntityType.CUSTOMER,
            operation=QBOOperationType.CREATE,
            data=customer_data
        )
        return self.execute_request(connection_id, request)
    
    def create_invoice(self, connection_id: str, invoice_data: Dict[str, Any]) -> QBOResponse:
        """Create a new invoice"""
        request = QBORequest(
            entity_type=QBOEntityType.INVOICE,
            operation=QBOOperationType.CREATE,
            data=invoice_data
        )
        return self.execute_request(connection_id, request)
    
    def create_payment(self, connection_id: str, payment_data: Dict[str, Any]) -> QBOResponse:
        """Create a payment received"""
        request = QBORequest(
            entity_type=QBOEntityType.PAYMENT,
            operation=QBOOperationType.CREATE,
            data=payment_data
        )
        return self.execute_request(connection_id, request)
    
    def create_expense(self, connection_id: str, expense_data: Dict[str, Any]) -> QBOResponse:
        """Create an expense/purchase"""
        request = QBORequest(
            entity_type=QBOEntityType.EXPENSE,
            operation=QBOOperationType.CREATE,
            data=expense_data
        )
        return self.execute_request(connection_id, request)
    
    def create_journal_entry(self, connection_id: str, journal_data: Dict[str, Any]) -> QBOResponse:
        """Create a journal entry"""
        request = QBORequest(
            entity_type=QBOEntityType.JOURNAL_ENTRY,
            operation=QBOOperationType.CREATE,
            data=journal_data
        )
        return self.execute_request(connection_id, request)
    
    def get_customers(self, connection_id: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all customers"""
        query = "SELECT * FROM Customer"
        if active_only:
            query += " WHERE Active = true"
        
        request = QBORequest(
            entity_type=QBOEntityType.CUSTOMER,
            operation=QBOOperationType.QUERY,
            query=query
        )
        
        response = self.execute_request(connection_id, request)
        if response.success and response.query_response:
            return response.query_response.get('Customer', [])
        return []
    
    def get_invoices(self, connection_id: str, start_date: Optional[datetime] = None, 
                    end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get invoices with optional date filtering"""
        query = "SELECT * FROM Invoice"
        
        conditions = []
        if start_date:
            conditions.append(f"TxnDate >= '{start_date.strftime('%Y-%m-%d')}'")
        if end_date:
            conditions.append(f"TxnDate <= '{end_date.strftime('%Y-%m-%d')}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        request = QBORequest(
            entity_type=QBOEntityType.INVOICE,
            operation=QBOOperationType.QUERY,
            query=query
        )
        
        response = self.execute_request(connection_id, request)
        if response.success and response.query_response:
            return response.query_response.get('Invoice', [])
        return []
    
    def get_payments(self, connection_id: str, start_date: Optional[datetime] = None,
                    end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get payments with optional date filtering"""
        query = "SELECT * FROM Payment"
        
        conditions = []
        if start_date:
            conditions.append(f"TxnDate >= '{start_date.strftime('%Y-%m-%d')}'")
        if end_date:
            conditions.append(f"TxnDate <= '{end_date.strftime('%Y-%m-%d')}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        request = QBORequest(
            entity_type=QBOEntityType.PAYMENT,
            operation=QBOOperationType.QUERY,
            query=query
        )
        
        response = self.execute_request(connection_id, request)
        if response.success and response.query_response:
            return response.query_response.get('Payment', [])
        return []
    
    # Batch operations
    
    def execute_batch_request(self, connection_id: str, requests: List[QBORequest]) -> List[QBOResponse]:
        """Execute multiple requests in a batch"""
        connection = self.oauth_service.get_connection(connection_id)
        if not connection:
            return [QBOResponse(success=False, error="Connection not found")] * len(requests)
        
        # Split into batches if necessary
        batch_size = min(self.max_batch_size, len(requests))
        results = []
        
        for i in range(0, len(requests), batch_size):
            batch = requests[i:i + batch_size]
            batch_result = self._execute_single_batch(connection, batch)
            results.extend(batch_result)
        
        return results
    
    def _execute_single_batch(self, connection: QuickBooksConnection, 
                            requests: List[QBORequest]) -> List[QBOResponse]:
        """Execute a single batch of requests"""
        batch_data = {
            "BatchItemRequest": []
        }
        
        for i, req in enumerate(requests):
            batch_item = {
                "bId": str(i),
                req.entity_type.value: req.data
            }
            batch_data["BatchItemRequest"].append(batch_item)
        
        try:
            response = self._make_request(connection, 'POST', 'batch', data=batch_data)
            parsed_response = self._parse_response(response)
            
            if parsed_response.success and parsed_response.batch_item_response:
                results = []
                for item in parsed_response.batch_item_response:
                    if 'Fault' in item:
                        results.append(QBOResponse(
                            success=False,
                            error=item['Fault'].get('Error', [{}])[0].get('Detail', 'Batch item failed')
                        ))
                    else:
                        results.append(QBOResponse(success=True, data=item))
                return results
            else:
                return [QBOResponse(success=False, error="Batch request failed")] * len(requests)
        
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            return [QBOResponse(success=False, error=str(e))] * len(requests)
    
    # Advanced synchronization
    
    def sync_entity_type(self, connection_id: str, entity_type: QBOEntityType, 
                        data_list: List[Dict[str, Any]], operation: QBOOperationType) -> QBOSyncResult:
        """Synchronize a list of entities of the same type"""
        start_time = datetime.now()
        
        # Create requests
        requests = []
        for data in data_list:
            request = QBORequest(
                entity_type=entity_type,
                operation=operation,
                data=data
            )
            requests.append(request)
        
        # Execute batch
        responses = self.execute_batch_request(connection_id, requests)
        
        # Analyze results
        successful = sum(1 for r in responses if r.success)
        failed = len(responses) - successful
        errors = [{'error': r.error, 'data': req.data} for r, req in zip(responses, requests) if not r.success]
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        return QBOSyncResult(
            entity_type=entity_type,
            operation=operation.value,
            total_records=len(data_list),
            successful_records=successful,
            failed_records=failed,
            errors=errors,
            sync_time=start_time,
            duration_seconds=duration
        )
    
    def get_company_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get company information"""
        connection = self.oauth_service.get_connection(connection_id)
        if not connection:
            return None
        
        request = QBORequest(
            entity_type=QBOEntityType.COMPANY_INFO,
            operation=QBOOperationType.READ,
            entity_id=connection.company_id
        )
        
        response = self.execute_request(connection_id, request)
        if response.success and response.query_response:
            company_info_list = response.query_response.get('CompanyInfo', [])
            return company_info_list[0] if company_info_list else None
        
        return None
    
    def test_connection(self, connection_id: str) -> Dict[str, Any]:
        """Test QuickBooks connection"""
        try:
            company_info = self.get_company_info(connection_id)
            if company_info:
                return {
                    'status': 'connected',
                    'company_name': company_info.get('Name', 'Unknown'),
                    'company_id': company_info.get('Id'),
                    'test_time': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'failed',
                    'error': 'Unable to retrieve company information'
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def clear_cache(self):
        """Clear all cached data"""
        self._account_cache.clear()
        self._customer_cache.clear()
        self._cache_timestamps.clear()

# Service instance
_api_client = None

def get_quickbooks_api_client() -> QuickBooksAPIClient:
    """Get singleton API client instance"""
    global _api_client
    if _api_client is None:
        _api_client = QuickBooksAPIClient()
    return _api_client
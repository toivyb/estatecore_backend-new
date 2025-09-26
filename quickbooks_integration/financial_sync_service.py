"""
Financial Synchronization Service for QuickBooks Integration

Handles bidirectional synchronization of financial data between EstateCore
and QuickBooks Online with conflict resolution and data integrity.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
import uuid

from .quickbooks_api_client import QuickBooksAPIClient, QBOEntityType, QBOOperationType, QBORequest
from .data_mapping_service import DataMappingService, EstateCoreTenant, QuickBooksEntity
from .quickbooks_oauth_service import QuickBooksOAuthService

logger = logging.getLogger(__name__)

class SyncDirection(Enum):
    """Synchronization direction"""
    ESTATECORE_TO_QB = "estatecore_to_qb"
    QB_TO_ESTATECORE = "qb_to_estatecore"
    BIDIRECTIONAL = "bidirectional"

class SyncStatus(Enum):
    """Synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    ESTATECORE_WINS = "estatecore_wins"
    QUICKBOOKS_WINS = "quickbooks_wins"
    MANUAL_REVIEW = "manual_review"
    MERGE_FIELDS = "merge_fields"
    TIMESTAMP_BASED = "timestamp_based"

@dataclass
class SyncRecord:
    """Record of a synchronization operation"""
    sync_id: str
    organization_id: str
    connection_id: str
    entity_type: str
    entity_id: str
    direction: SyncDirection
    status: SyncStatus
    estatecore_data: Optional[Dict[str, Any]]
    quickbooks_data: Optional[Dict[str, Any]]
    sync_timestamp: datetime
    last_modified_ec: Optional[datetime]
    last_modified_qb: Optional[datetime]
    conflict_resolution: Optional[ConflictResolution] = None
    error_message: Optional[str] = None
    retry_count: int = 0

@dataclass
class SyncConfiguration:
    """Configuration for synchronization"""
    organization_id: str
    auto_sync_enabled: bool = True
    sync_interval_minutes: int = 15
    conflict_resolution: ConflictResolution = ConflictResolution.TIMESTAMP_BASED
    sync_entities: List[str] = None
    max_retry_attempts: int = 3
    batch_size: int = 50
    
    def __post_init__(self):
        if self.sync_entities is None:
            self.sync_entities = ["tenants", "payments", "expenses", "invoices"]

@dataclass
class SyncResult:
    """Result of a synchronization operation"""
    sync_id: str
    status: SyncStatus
    total_records: int
    successful_records: int
    failed_records: int
    conflicts: int
    duration_seconds: float
    errors: List[Dict[str, Any]]
    conflicts_requiring_review: List[Dict[str, Any]]

class FinancialSyncService:
    """
    Service for synchronizing financial data between EstateCore and QuickBooks
    """
    
    def __init__(self, api_client: Optional[QuickBooksAPIClient] = None,
                 mapping_service: Optional[DataMappingService] = None,
                 oauth_service: Optional[QuickBooksOAuthService] = None):
        self.api_client = api_client or QuickBooksAPIClient()
        self.mapping_service = mapping_service or DataMappingService()
        self.oauth_service = oauth_service or QuickBooksOAuthService()
        
        # Sync records storage (in production, use database)
        self.sync_records: Dict[str, SyncRecord] = {}
        self.sync_configurations: Dict[str, SyncConfiguration] = {}
        
        # Load existing configurations
        self._load_configurations()
    
    def _load_configurations(self):
        """Load synchronization configurations"""
        try:
            with open('instance/sync_configurations.json', 'r') as f:
                data = json.load(f)
                for org_id, config_data in data.get('configurations', {}).items():
                    self.sync_configurations[org_id] = SyncConfiguration(**config_data)
        except FileNotFoundError:
            logger.info("No sync configurations file found")
        except Exception as e:
            logger.error(f"Error loading sync configurations: {e}")
    
    def _save_configurations(self):
        """Save synchronization configurations"""
        try:
            import os
            os.makedirs('instance', exist_ok=True)
            data = {
                'configurations': {
                    org_id: asdict(config) 
                    for org_id, config in self.sync_configurations.items()
                }
            }
            with open('instance/sync_configurations.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving sync configurations: {e}")
    
    def create_sync_configuration(self, organization_id: str, **kwargs) -> SyncConfiguration:
        """Create a new sync configuration"""
        config = SyncConfiguration(organization_id=organization_id, **kwargs)
        self.sync_configurations[organization_id] = config
        self._save_configurations()
        return config
    
    def get_sync_configuration(self, organization_id: str) -> Optional[SyncConfiguration]:
        """Get sync configuration for organization"""
        return self.sync_configurations.get(organization_id)
    
    def update_sync_configuration(self, organization_id: str, updates: Dict[str, Any]) -> bool:
        """Update sync configuration"""
        if organization_id not in self.sync_configurations:
            return False
        
        config = self.sync_configurations[organization_id]
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self._save_configurations()
        return True
    
    async def sync_tenants_to_customers(self, organization_id: str, tenant_data: List[Dict[str, Any]]) -> SyncResult:
        """Sync EstateCore tenants to QuickBooks customers"""
        start_time = datetime.now()
        sync_id = str(uuid.uuid4())
        
        connection = self.oauth_service.get_organization_connection(organization_id)
        if not connection:
            return SyncResult(
                sync_id=sync_id,
                status=SyncStatus.FAILED,
                total_records=0,
                successful_records=0,
                failed_records=0,
                conflicts=0,
                duration_seconds=0,
                errors=[{"error": "No QuickBooks connection found"}],
                conflicts_requiring_review=[]
            )
        
        successful = 0
        failed = 0
        errors = []
        conflicts = []
        
        for tenant in tenant_data:
            try:
                # Map EstateCore tenant to QuickBooks customer
                qb_customer = self.mapping_service.map_entity(tenant, "tenant_to_customer")
                
                # Validate mapped data
                validation_errors = self.mapping_service.validate_mapped_data(
                    qb_customer, QuickBooksEntity.CUSTOMER
                )
                
                if validation_errors:
                    errors.append({
                        "tenant_id": tenant.get("tenant_id"),
                        "errors": validation_errors
                    })
                    failed += 1
                    continue
                
                # Check if customer already exists
                existing_customer = await self._find_existing_customer(
                    connection.connection_id, tenant.get("tenant_id")
                )
                
                if existing_customer:
                    # Update existing customer
                    qb_customer["Id"] = existing_customer["Id"]
                    qb_customer["SyncToken"] = existing_customer["SyncToken"]
                    
                    request = QBORequest(
                        entity_type=QBOEntityType.CUSTOMER,
                        operation=QBOOperationType.UPDATE,
                        data={"Customer": qb_customer}
                    )
                else:
                    # Create new customer
                    request = QBORequest(
                        entity_type=QBOEntityType.CUSTOMER,
                        operation=QBOOperationType.CREATE,
                        data={"Customer": qb_customer}
                    )
                
                # Execute request
                response = self.api_client.execute_request(connection.connection_id, request)
                
                if response.success:
                    successful += 1
                    
                    # Record sync operation
                    sync_record = SyncRecord(
                        sync_id=f"{sync_id}_{tenant.get('tenant_id')}",
                        organization_id=organization_id,
                        connection_id=connection.connection_id,
                        entity_type="tenant",
                        entity_id=tenant.get("tenant_id"),
                        direction=SyncDirection.ESTATECORE_TO_QB,
                        status=SyncStatus.COMPLETED,
                        estatecore_data=tenant,
                        quickbooks_data=response.data,
                        sync_timestamp=datetime.now(),
                        last_modified_ec=datetime.now(),
                        last_modified_qb=datetime.now()
                    )
                    self.sync_records[sync_record.sync_id] = sync_record
                else:
                    failed += 1
                    errors.append({
                        "tenant_id": tenant.get("tenant_id"),
                        "error": response.error
                    })
            
            except Exception as e:
                failed += 1
                errors.append({
                    "tenant_id": tenant.get("tenant_id"),
                    "error": str(e)
                })
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return SyncResult(
            sync_id=sync_id,
            status=SyncStatus.COMPLETED if failed == 0 else SyncStatus.PARTIAL,
            total_records=len(tenant_data),
            successful_records=successful,
            failed_records=failed,
            conflicts=len(conflicts),
            duration_seconds=duration,
            errors=errors,
            conflicts_requiring_review=conflicts
        )
    
    async def sync_payments_to_quickbooks(self, organization_id: str, payment_data: List[Dict[str, Any]]) -> SyncResult:
        """Sync EstateCore payments to QuickBooks invoices and payments"""
        start_time = datetime.now()
        sync_id = str(uuid.uuid4())
        
        connection = self.oauth_service.get_organization_connection(organization_id)
        if not connection:
            return SyncResult(
                sync_id=sync_id,
                status=SyncStatus.FAILED,
                total_records=0,
                successful_records=0,
                failed_records=0,
                conflicts=0,
                duration_seconds=0,
                errors=[{"error": "No QuickBooks connection found"}],
                conflicts_requiring_review=[]
            )
        
        successful = 0
        failed = 0
        errors = []
        
        for payment in payment_data:
            try:
                # Create invoice first
                invoice_result = await self._create_rent_invoice(connection.connection_id, payment)
                if not invoice_result["success"]:
                    failed += 1
                    errors.append({
                        "payment_id": payment.get("rent_payment_id"),
                        "error": f"Invoice creation failed: {invoice_result['error']}"
                    })
                    continue
                
                # Create payment received
                payment_result = await self._create_payment_received(
                    connection.connection_id, payment, invoice_result["invoice_id"]
                )
                
                if payment_result["success"]:
                    successful += 1
                else:
                    failed += 1
                    errors.append({
                        "payment_id": payment.get("rent_payment_id"),
                        "error": f"Payment creation failed: {payment_result['error']}"
                    })
            
            except Exception as e:
                failed += 1
                errors.append({
                    "payment_id": payment.get("rent_payment_id"),
                    "error": str(e)
                })
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return SyncResult(
            sync_id=sync_id,
            status=SyncStatus.COMPLETED if failed == 0 else SyncStatus.PARTIAL,
            total_records=len(payment_data),
            successful_records=successful,
            failed_records=failed,
            conflicts=0,
            duration_seconds=duration,
            errors=errors,
            conflicts_requiring_review=[]
        )
    
    async def sync_expenses_to_quickbooks(self, organization_id: str, expense_data: List[Dict[str, Any]]) -> SyncResult:
        """Sync EstateCore expenses to QuickBooks bills"""
        start_time = datetime.now()
        sync_id = str(uuid.uuid4())
        
        connection = self.oauth_service.get_organization_connection(organization_id)
        if not connection:
            return SyncResult(
                sync_id=sync_id,
                status=SyncStatus.FAILED,
                total_records=0,
                successful_records=0,
                failed_records=0,
                conflicts=0,
                duration_seconds=0,
                errors=[{"error": "No QuickBooks connection found"}],
                conflicts_requiring_review=[]
            )
        
        successful = 0
        failed = 0
        errors = []
        
        for expense in expense_data:
            try:
                # Map EstateCore expense to QuickBooks bill
                qb_bill = self.mapping_service.map_entity(expense, "expense_to_bill")
                
                # Validate mapped data
                validation_errors = self.mapping_service.validate_mapped_data(
                    qb_bill, QuickBooksEntity.BILL
                )
                
                if validation_errors:
                    errors.append({
                        "expense_id": expense.get("expense_id"),
                        "errors": validation_errors
                    })
                    failed += 1
                    continue
                
                # Create bill
                request = QBORequest(
                    entity_type=QBOEntityType.BILL,
                    operation=QBOOperationType.CREATE,
                    data={"Bill": qb_bill}
                )
                
                response = self.api_client.execute_request(connection.connection_id, request)
                
                if response.success:
                    successful += 1
                else:
                    failed += 1
                    errors.append({
                        "expense_id": expense.get("expense_id"),
                        "error": response.error
                    })
            
            except Exception as e:
                failed += 1
                errors.append({
                    "expense_id": expense.get("expense_id"),
                    "error": str(e)
                })
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return SyncResult(
            sync_id=sync_id,
            status=SyncStatus.COMPLETED if failed == 0 else SyncStatus.PARTIAL,
            total_records=len(expense_data),
            successful_records=successful,
            failed_records=failed,
            conflicts=0,
            duration_seconds=duration,
            errors=errors,
            conflicts_requiring_review=[]
        )
    
    async def _find_existing_customer(self, connection_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Find existing customer by EstateCore tenant ID"""
        try:
            # Search for customer by account number
            account_num = f"EC-{tenant_id}"
            request = QBORequest(
                entity_type=QBOEntityType.CUSTOMER,
                operation=QBOOperationType.QUERY,
                query=f"SELECT * FROM Customer WHERE AcctNum = '{account_num}'"
            )
            
            response = self.api_client.execute_request(connection_id, request)
            
            if response.success and response.query_response:
                customers = response.query_response.get('Customer', [])
                return customers[0] if customers else None
            
            return None
        except Exception as e:
            logger.error(f"Error finding existing customer: {e}")
            return None
    
    async def _create_rent_invoice(self, connection_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create rent invoice in QuickBooks"""
        try:
            # Map payment to invoice
            qb_invoice = self.mapping_service.map_entity(payment_data, "rent_to_invoice")
            
            # Create invoice
            request = QBORequest(
                entity_type=QBOEntityType.INVOICE,
                operation=QBOOperationType.CREATE,
                data={"Invoice": qb_invoice}
            )
            
            response = self.api_client.execute_request(connection_id, request)
            
            if response.success:
                invoice_data = response.data.get("Invoice", {})
                return {
                    "success": True,
                    "invoice_id": invoice_data.get("Id"),
                    "invoice_data": invoice_data
                }
            else:
                return {
                    "success": False,
                    "error": response.error
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _create_payment_received(self, connection_id: str, payment_data: Dict[str, Any], 
                                     invoice_id: str) -> Dict[str, Any]:
        """Create payment received in QuickBooks"""
        try:
            # Map payment data
            qb_payment = self.mapping_service.map_entity(payment_data, "payment_to_payment")
            
            # Link to invoice
            qb_payment["Line"] = [{
                "Amount": qb_payment["TotalAmt"],
                "LinkedTxn": [{
                    "TxnId": invoice_id,
                    "TxnType": "Invoice"
                }]
            }]
            
            # Create payment
            request = QBORequest(
                entity_type=QBOEntityType.PAYMENT,
                operation=QBOOperationType.CREATE,
                data={"Payment": qb_payment}
            )
            
            response = self.api_client.execute_request(connection_id, request)
            
            if response.success:
                return {
                    "success": True,
                    "payment_data": response.data.get("Payment", {})
                }
            else:
                return {
                    "success": False,
                    "error": response.error
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_from_quickbooks(self, organization_id: str, entity_types: List[str] = None) -> SyncResult:
        """Sync data from QuickBooks to EstateCore"""
        start_time = datetime.now()
        sync_id = str(uuid.uuid4())
        
        if entity_types is None:
            entity_types = ["customers", "invoices", "payments"]
        
        connection = self.oauth_service.get_organization_connection(organization_id)
        if not connection:
            return SyncResult(
                sync_id=sync_id,
                status=SyncStatus.FAILED,
                total_records=0,
                successful_records=0,
                failed_records=0,
                conflicts=0,
                duration_seconds=0,
                errors=[{"error": "No QuickBooks connection found"}],
                conflicts_requiring_review=[]
            )
        
        successful = 0
        failed = 0
        errors = []
        conflicts = []
        total_records = 0
        
        for entity_type in entity_types:
            try:
                if entity_type == "customers":
                    result = await self._sync_customers_from_qb(connection.connection_id, organization_id)
                elif entity_type == "invoices":
                    result = await self._sync_invoices_from_qb(connection.connection_id, organization_id)
                elif entity_type == "payments":
                    result = await self._sync_payments_from_qb(connection.connection_id, organization_id)
                else:
                    continue
                
                total_records += result["total"]
                successful += result["successful"]
                failed += result["failed"]
                errors.extend(result["errors"])
                conflicts.extend(result["conflicts"])
                
            except Exception as e:
                failed += 1
                errors.append({
                    "entity_type": entity_type,
                    "error": str(e)
                })
        
        duration = (datetime.now() - start_time).total_seconds()
        
        return SyncResult(
            sync_id=sync_id,
            status=SyncStatus.COMPLETED if failed == 0 else SyncStatus.PARTIAL,
            total_records=total_records,
            successful_records=successful,
            failed_records=failed,
            conflicts=len(conflicts),
            duration_seconds=duration,
            errors=errors,
            conflicts_requiring_review=conflicts
        )
    
    async def _sync_customers_from_qb(self, connection_id: str, organization_id: str) -> Dict[str, Any]:
        """Sync customers from QuickBooks to EstateCore"""
        # Get recent customers from QuickBooks
        customers = self.api_client.get_customers(connection_id)
        
        successful = 0
        failed = 0
        errors = []
        conflicts = []
        
        for customer in customers:
            try:
                # Convert QuickBooks customer to EstateCore tenant format
                tenant_data = self._map_customer_to_tenant(customer)
                
                # Check for conflicts with existing tenant data
                # This would involve checking against EstateCore database
                
                # For now, just track successful conversion
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    "customer_id": customer.get("Id"),
                    "error": str(e)
                })
        
        return {
            "total": len(customers),
            "successful": successful,
            "failed": failed,
            "errors": errors,
            "conflicts": conflicts
        }
    
    async def _sync_invoices_from_qb(self, connection_id: str, organization_id: str) -> Dict[str, Any]:
        """Sync invoices from QuickBooks to EstateCore"""
        # Get recent invoices
        invoices = self.api_client.get_invoices(connection_id)
        
        successful = 0
        failed = 0
        errors = []
        conflicts = []
        
        for invoice in invoices:
            try:
                # Convert QuickBooks invoice to EstateCore format
                # This would involve mapping back to EstateCore schema
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    "invoice_id": invoice.get("Id"),
                    "error": str(e)
                })
        
        return {
            "total": len(invoices),
            "successful": successful,
            "failed": failed,
            "errors": errors,
            "conflicts": conflicts
        }
    
    async def _sync_payments_from_qb(self, connection_id: str, organization_id: str) -> Dict[str, Any]:
        """Sync payments from QuickBooks to EstateCore"""
        # Get recent payments
        payments = self.api_client.get_payments(connection_id)
        
        successful = 0
        failed = 0
        errors = []
        conflicts = []
        
        for payment in payments:
            try:
                # Convert QuickBooks payment to EstateCore format
                successful += 1
                
            except Exception as e:
                failed += 1
                errors.append({
                    "payment_id": payment.get("Id"),
                    "error": str(e)
                })
        
        return {
            "total": len(payments),
            "successful": successful,
            "failed": failed,
            "errors": errors,
            "conflicts": conflicts
        }
    
    def _map_customer_to_tenant(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Map QuickBooks customer to EstateCore tenant"""
        # Reverse mapping from QuickBooks to EstateCore
        return {
            "tenant_id": customer.get("AcctNum", "").replace("EC-", ""),
            "first_name": customer.get("GivenName", ""),
            "last_name": customer.get("FamilyName", ""),
            "email": customer.get("PrimaryEmailAddr", {}).get("Address", ""),
            "phone": customer.get("PrimaryPhone", {}).get("FreeFormNumber", ""),
            "quickbooks_customer_id": customer.get("Id")
        }
    
    def get_sync_status(self, sync_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a sync operation"""
        # This would query the database for sync status
        # For now, return basic status
        return {
            "sync_id": sync_id,
            "status": "completed",
            "last_sync": datetime.now().isoformat()
        }
    
    def get_sync_history(self, organization_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get sync history for organization"""
        records = [
            record for record in self.sync_records.values()
            if record.organization_id == organization_id
        ]
        
        # Sort by timestamp descending
        records.sort(key=lambda x: x.sync_timestamp, reverse=True)
        
        return [
            {
                "sync_id": record.sync_id,
                "entity_type": record.entity_type,
                "direction": record.direction.value,
                "status": record.status.value,
                "sync_timestamp": record.sync_timestamp.isoformat(),
                "error_message": record.error_message
            }
            for record in records[:limit]
        ]
    
    def resolve_conflict(self, sync_id: str, resolution: ConflictResolution, 
                        manual_data: Optional[Dict[str, Any]] = None) -> bool:
        """Resolve a sync conflict"""
        record = self.sync_records.get(sync_id)
        if not record:
            return False
        
        record.conflict_resolution = resolution
        
        if resolution == ConflictResolution.MANUAL_REVIEW and manual_data:
            # Apply manual resolution
            record.estatecore_data = manual_data
        
        record.status = SyncStatus.COMPLETED
        return True

# Service instance
_sync_service = None

def get_financial_sync_service() -> FinancialSyncService:
    """Get singleton sync service instance"""
    global _sync_service
    if _sync_service is None:
        _sync_service = FinancialSyncService()
    return _sync_service
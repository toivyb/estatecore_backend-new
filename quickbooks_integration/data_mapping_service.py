"""
Data Mapping Service for QuickBooks Integration

Handles mapping between EstateCore data structures and QuickBooks Online
entities with configurable mapping rules, validation, and transformation.
"""

import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import re
from decimal import Decimal

logger = logging.getLogger(__name__)

class EstateCoreTenant(Enum):
    """EstateCore entity types"""
    TENANT = "tenant"
    PROPERTY = "property"
    UNIT = "unit"
    RENT_PAYMENT = "rent_payment"
    EXPENSE = "expense"
    INVOICE = "invoice"
    VENDOR = "vendor"
    LEASE = "lease"
    MAINTENANCE_REQUEST = "maintenance_request"

class QuickBooksEntity(Enum):
    """QuickBooks entity types"""
    CUSTOMER = "Customer"
    ITEM = "Item"
    ACCOUNT = "Account"
    INVOICE = "Invoice"
    PAYMENT = "Payment"
    VENDOR = "Vendor"
    BILL = "Bill"
    EXPENSE = "Purchase"
    JOURNAL_ENTRY = "JournalEntry"

@dataclass
class MappingRule:
    """Defines how to map a field from EstateCore to QuickBooks"""
    source_field: str
    target_field: str
    transform_function: Optional[str] = None
    default_value: Optional[Any] = None
    required: bool = True
    validation_pattern: Optional[str] = None

@dataclass
class EntityMapping:
    """Complete mapping configuration for an entity type"""
    source_entity: EstateCoreTenant
    target_entity: QuickBooksEntity
    field_mappings: List[MappingRule]
    custom_mappings: Dict[str, Any] = None
    validation_rules: Dict[str, Any] = None

@dataclass
class PropertyAccountMapping:
    """Maps properties to specific QuickBooks accounts"""
    property_id: str
    property_name: str
    revenue_account_id: str
    expense_account_id: str
    deposit_account_id: str
    ar_account_id: str  # Accounts Receivable
    custom_class_id: Optional[str] = None
    location_id: Optional[str] = None

class DataMappingService:
    """
    Service for mapping EstateCore data to QuickBooks Online format
    """
    
    def __init__(self):
        self.mappings: Dict[str, EntityMapping] = {}
        self.property_mappings: Dict[str, PropertyAccountMapping] = {}
        self.transformation_functions: Dict[str, Callable] = {}
        
        # Initialize default mappings
        self._initialize_default_mappings()
        self._initialize_transformation_functions()
        
        # Load custom mappings if they exist
        self._load_custom_mappings()
    
    def _initialize_default_mappings(self):
        """Initialize default mapping configurations"""
        
        # Tenant to Customer mapping
        tenant_to_customer = EntityMapping(
            source_entity=EstateCoreTenant.TENANT,
            target_entity=QuickBooksEntity.CUSTOMER,
            field_mappings=[
                MappingRule("first_name", "GivenName", required=True),
                MappingRule("last_name", "FamilyName", required=True),
                MappingRule("email", "PrimaryEmailAddr.Address"),
                MappingRule("phone", "PrimaryPhone.FreeFormNumber"),
                MappingRule("unit_address", "BillAddr.Line1"),
                MappingRule("city", "BillAddr.City"),
                MappingRule("state", "BillAddr.CountrySubDivisionCode"),
                MappingRule("zip_code", "BillAddr.PostalCode"),
                MappingRule("unit_number", "DisplayName", transform_function="format_tenant_display_name"),
                MappingRule("lease_start_date", "Notes", transform_function="format_tenant_notes"),
                MappingRule("tenant_id", "AcctNum", transform_function="format_account_number")
            ],
            custom_mappings={
                "Active": True,
                "Taxable": False,
                "CustomerTypeRef": {"value": "1", "name": "Tenant"}
            }
        )
        self.mappings["tenant_to_customer"] = tenant_to_customer
        
        # Rent Payment to Invoice mapping
        rent_to_invoice = EntityMapping(
            source_entity=EstateCoreTenant.RENT_PAYMENT,
            target_entity=QuickBooksEntity.INVOICE,
            field_mappings=[
                MappingRule("tenant_id", "CustomerRef.value", transform_function="get_qb_customer_id"),
                MappingRule("due_date", "DueDate", transform_function="format_date"),
                MappingRule("period_start", "TxnDate", transform_function="format_date"),
                MappingRule("amount", "Line.0.Amount", transform_function="format_currency"),
                MappingRule("property_id", "Line.0.DetailType", default_value="SalesItemLineDetail"),
                MappingRule("unit_number", "Memo", transform_function="format_invoice_memo"),
                MappingRule("rent_payment_id", "DocNumber", transform_function="format_doc_number")
            ],
            custom_mappings={
                "Line": [{
                    "DetailType": "SalesItemLineDetail",
                    "SalesItemLineDetail": {
                        "ItemRef": {"value": "1", "name": "Rent"},
                        "UnitPrice": 0,
                        "Qty": 1,
                        "TaxCodeRef": {"value": "NON"}
                    }
                }]
            }
        )
        self.mappings["rent_to_invoice"] = rent_to_invoice
        
        # Payment to Payment mapping
        payment_to_payment = EntityMapping(
            source_entity=EstateCoreTenant.RENT_PAYMENT,
            target_entity=QuickBooksEntity.PAYMENT,
            field_mappings=[
                MappingRule("tenant_id", "CustomerRef.value", transform_function="get_qb_customer_id"),
                MappingRule("payment_date", "TxnDate", transform_function="format_date"),
                MappingRule("amount", "TotalAmt", transform_function="format_currency"),
                MappingRule("payment_method", "PaymentMethodRef.value", transform_function="map_payment_method"),
                MappingRule("property_id", "DepositToAccountRef.value", transform_function="get_property_deposit_account"),
                MappingRule("rent_payment_id", "PaymentRefNum", transform_function="format_payment_ref")
            ]
        )
        self.mappings["payment_to_payment"] = payment_to_payment
        
        # Expense to Bill mapping
        expense_to_bill = EntityMapping(
            source_entity=EstateCoreTenant.EXPENSE,
            target_entity=QuickBooksEntity.BILL,
            field_mappings=[
                MappingRule("vendor_name", "VendorRef.value", transform_function="get_qb_vendor_id"),
                MappingRule("expense_date", "TxnDate", transform_function="format_date"),
                MappingRule("due_date", "DueDate", transform_function="format_date"),
                MappingRule("amount", "Line.0.Amount", transform_function="format_currency"),
                MappingRule("category", "Line.0.AccountBasedExpenseLineDetail.AccountRef.value", 
                           transform_function="map_expense_account"),
                MappingRule("description", "Line.0.Description"),
                MappingRule("property_id", "Line.0.AccountBasedExpenseLineDetail.ClassRef.value",
                           transform_function="get_property_class"),
                MappingRule("expense_id", "DocNumber", transform_function="format_doc_number")
            ]
        )
        self.mappings["expense_to_bill"] = expense_to_bill
        
        # Vendor mapping
        vendor_to_vendor = EntityMapping(
            source_entity=EstateCoreTenant.VENDOR,
            target_entity=QuickBooksEntity.VENDOR,
            field_mappings=[
                MappingRule("vendor_name", "Name", required=True),
                MappingRule("email", "PrimaryEmailAddr.Address"),
                MappingRule("phone", "PrimaryPhone.FreeFormNumber"),
                MappingRule("address", "BillAddr.Line1"),
                MappingRule("city", "BillAddr.City"),
                MappingRule("state", "BillAddr.CountrySubDivisionCode"),
                MappingRule("zip_code", "BillAddr.PostalCode"),
                MappingRule("tax_id", "TaxIdentifier"),
                MappingRule("vendor_id", "AcctNum", transform_function="format_account_number")
            ],
            custom_mappings={
                "Active": True,
                "Vendor1099": False
            }
        )
        self.mappings["vendor_to_vendor"] = vendor_to_vendor
    
    def _initialize_transformation_functions(self):
        """Initialize transformation functions"""
        
        def format_date(value: Any) -> str:
            """Format date for QuickBooks"""
            if isinstance(value, str):
                try:
                    parsed_date = datetime.strptime(value, "%Y-%m-%d")
                    return parsed_date.strftime("%Y-%m-%d")
                except ValueError:
                    return value
            elif isinstance(value, (datetime, date)):
                return value.strftime("%Y-%m-%d")
            return str(value)
        
        def format_currency(value: Any) -> float:
            """Format currency for QuickBooks"""
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, Decimal):
                return float(value)
            elif isinstance(value, str):
                # Remove currency symbols and parse
                cleaned = re.sub(r'[^\d.-]', '', value)
                try:
                    return float(cleaned)
                except ValueError:
                    return 0.0
            return 0.0
        
        def format_tenant_display_name(data: Dict[str, Any]) -> str:
            """Format tenant display name"""
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            unit_number = data.get('unit_number', '')
            return f"{first_name} {last_name} - Unit {unit_number}".strip()
        
        def format_tenant_notes(data: Dict[str, Any]) -> str:
            """Format tenant notes"""
            lease_start = data.get('lease_start_date', '')
            lease_end = data.get('lease_end_date', '')
            notes = f"Lease: {lease_start}"
            if lease_end:
                notes += f" to {lease_end}"
            return notes
        
        def format_account_number(value: Any) -> str:
            """Format account number"""
            return f"EC-{str(value)}"
        
        def format_doc_number(value: Any) -> str:
            """Format document number"""
            return f"EC-{str(value)}"
        
        def format_payment_ref(value: Any) -> str:
            """Format payment reference"""
            return f"RENT-{str(value)}"
        
        def format_invoice_memo(data: Dict[str, Any]) -> str:
            """Format invoice memo"""
            unit = data.get('unit_number', '')
            period_start = data.get('period_start', '')
            period_end = data.get('period_end', '')
            return f"Rent for Unit {unit} - {period_start} to {period_end}"
        
        def get_qb_customer_id(tenant_id: str) -> str:
            """Get QuickBooks customer ID for tenant"""
            # This would lookup in a mapping table
            return f"qb_customer_{tenant_id}"
        
        def get_qb_vendor_id(vendor_name: str) -> str:
            """Get QuickBooks vendor ID"""
            return f"qb_vendor_{vendor_name.replace(' ', '_').lower()}"
        
        def map_payment_method(payment_method: str) -> str:
            """Map payment method to QuickBooks"""
            method_mapping = {
                'credit_card': '1',
                'bank_transfer': '2',
                'check': '3',
                'cash': '4',
                'online': '5'
            }
            return method_mapping.get(payment_method.lower(), '1')
        
        def get_property_deposit_account(property_id: str) -> str:
            """Get deposit account for property"""
            mapping = self.property_mappings.get(property_id)
            return mapping.deposit_account_id if mapping else "1"  # Default account
        
        def map_expense_account(category: str) -> str:
            """Map expense category to QuickBooks account"""
            account_mapping = {
                'maintenance': '61',  # Maintenance expense
                'utilities': '62',    # Utilities
                'insurance': '63',    # Insurance
                'marketing': '64',    # Marketing
                'management': '65',   # Management fees
                'legal': '66',        # Legal fees
                'supplies': '67',     # Supplies
                'other': '68'         # Other expenses
            }
            return account_mapping.get(category.lower(), '68')
        
        def get_property_class(property_id: str) -> str:
            """Get QuickBooks class for property"""
            mapping = self.property_mappings.get(property_id)
            return mapping.custom_class_id if mapping and mapping.custom_class_id else None
        
        # Register all functions
        self.transformation_functions.update({
            'format_date': format_date,
            'format_currency': format_currency,
            'format_tenant_display_name': format_tenant_display_name,
            'format_tenant_notes': format_tenant_notes,
            'format_account_number': format_account_number,
            'format_doc_number': format_doc_number,
            'format_payment_ref': format_payment_ref,
            'format_invoice_memo': format_invoice_memo,
            'get_qb_customer_id': get_qb_customer_id,
            'get_qb_vendor_id': get_qb_vendor_id,
            'map_payment_method': map_payment_method,
            'get_property_deposit_account': get_property_deposit_account,
            'map_expense_account': map_expense_account,
            'get_property_class': get_property_class
        })
    
    def _load_custom_mappings(self):
        """Load custom mappings from configuration"""
        try:
            with open('instance/quickbooks_mappings.json', 'r') as f:
                config = json.load(f)
                
                # Load property mappings
                for prop_data in config.get('property_mappings', []):
                    mapping = PropertyAccountMapping(**prop_data)
                    self.property_mappings[mapping.property_id] = mapping
                
                # Load custom entity mappings if any
                # ... (implementation for custom mappings)
                
        except FileNotFoundError:
            logger.info("No custom mappings file found, using defaults")
        except Exception as e:
            logger.error(f"Error loading custom mappings: {e}")
    
    def map_entity(self, source_data: Dict[str, Any], mapping_key: str) -> Dict[str, Any]:
        """
        Map EstateCore entity to QuickBooks format
        
        Args:
            source_data: The EstateCore entity data
            mapping_key: Key identifying the mapping to use
            
        Returns:
            Dict containing QuickBooks formatted data
        """
        if mapping_key not in self.mappings:
            raise ValueError(f"Unknown mapping key: {mapping_key}")
        
        mapping = self.mappings[mapping_key]
        result = {}
        
        # Apply custom mappings first
        if mapping.custom_mappings:
            result.update(mapping.custom_mappings)
        
        # Apply field mappings
        for rule in mapping.field_mappings:
            try:
                value = self._extract_value(source_data, rule.source_field)
                
                if value is None and rule.default_value is not None:
                    value = rule.default_value
                
                if value is not None:
                    # Apply transformation if specified
                    if rule.transform_function:
                        func = self.transformation_functions.get(rule.transform_function)
                        if func:
                            if rule.transform_function in ['format_tenant_display_name', 
                                                         'format_tenant_notes', 
                                                         'format_invoice_memo']:
                                # Functions that need the entire data object
                                value = func(source_data)
                            else:
                                value = func(value)
                    
                    # Validate value if pattern specified
                    if rule.validation_pattern and isinstance(value, str):
                        if not re.match(rule.validation_pattern, value):
                            logger.warning(f"Value '{value}' doesn't match pattern {rule.validation_pattern}")
                    
                    # Set the value in the result
                    self._set_nested_value(result, rule.target_field, value)
                
                elif rule.required:
                    logger.warning(f"Required field {rule.source_field} is missing")
            
            except Exception as e:
                logger.error(f"Error mapping field {rule.source_field}: {e}")
        
        return result
    
    def _extract_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Extract value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = field_path.split('.')
        current = data
        
        # Navigate to the parent of the target field
        for key in keys[:-1]:
            # Handle array notation like "Line.0.Amount"
            if key.isdigit():
                key = int(key)
                if not isinstance(current, list):
                    current = []
                # Extend list if necessary
                while len(current) <= key:
                    current.append({})
                current = current[key]
            else:
                if key not in current:
                    current[key] = {}
                current = current[key]
        
        # Set the final value
        final_key = keys[-1]
        if final_key.isdigit():
            final_key = int(final_key)
            if not isinstance(current, list):
                current = []
            while len(current) <= final_key:
                current.append({})
        
        current[final_key] = value
    
    def validate_mapped_data(self, data: Dict[str, Any], entity_type: QuickBooksEntity) -> List[str]:
        """
        Validate mapped data for QuickBooks requirements
        
        Returns:
            List of validation errors
        """
        errors = []
        
        # Entity-specific validation
        if entity_type == QuickBooksEntity.CUSTOMER:
            if not data.get('Name'):
                errors.append("Customer Name is required")
        
        elif entity_type == QuickBooksEntity.INVOICE:
            if not data.get('CustomerRef', {}).get('value'):
                errors.append("Invoice CustomerRef is required")
            if not data.get('Line'):
                errors.append("Invoice must have at least one line item")
        
        elif entity_type == QuickBooksEntity.PAYMENT:
            if not data.get('CustomerRef', {}).get('value'):
                errors.append("Payment CustomerRef is required")
            if not data.get('TotalAmt'):
                errors.append("Payment TotalAmt is required")
        
        elif entity_type == QuickBooksEntity.BILL:
            if not data.get('VendorRef', {}).get('value'):
                errors.append("Bill VendorRef is required")
            if not data.get('Line'):
                errors.append("Bill must have at least one line item")
        
        elif entity_type == QuickBooksEntity.VENDOR:
            if not data.get('Name'):
                errors.append("Vendor Name is required")
        
        return errors
    
    def create_property_mapping(self, property_id: str, property_name: str,
                              revenue_account_id: str, expense_account_id: str,
                              deposit_account_id: str, ar_account_id: str,
                              custom_class_id: Optional[str] = None,
                              location_id: Optional[str] = None) -> PropertyAccountMapping:
        """Create a new property mapping"""
        mapping = PropertyAccountMapping(
            property_id=property_id,
            property_name=property_name,
            revenue_account_id=revenue_account_id,
            expense_account_id=expense_account_id,
            deposit_account_id=deposit_account_id,
            ar_account_id=ar_account_id,
            custom_class_id=custom_class_id,
            location_id=location_id
        )
        
        self.property_mappings[property_id] = mapping
        self._save_mappings()
        return mapping
    
    def get_property_mapping(self, property_id: str) -> Optional[PropertyAccountMapping]:
        """Get property mapping by ID"""
        return self.property_mappings.get(property_id)
    
    def list_property_mappings(self) -> List[PropertyAccountMapping]:
        """List all property mappings"""
        return list(self.property_mappings.values())
    
    def update_property_mapping(self, property_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing property mapping"""
        if property_id not in self.property_mappings:
            return False
        
        mapping = self.property_mappings[property_id]
        for key, value in updates.items():
            if hasattr(mapping, key):
                setattr(mapping, key, value)
        
        self._save_mappings()
        return True
    
    def _save_mappings(self):
        """Save mappings to configuration file"""
        config = {
            'property_mappings': [
                asdict(mapping) for mapping in self.property_mappings.values()
            ]
        }
        
        try:
            import os
            os.makedirs('instance', exist_ok=True)
            with open('instance/quickbooks_mappings.json', 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving mappings: {e}")
    
    def add_custom_transformation(self, name: str, func: Callable) -> None:
        """Add a custom transformation function"""
        self.transformation_functions[name] = func
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """Get summary of all configured mappings"""
        return {
            'entity_mappings': {
                key: {
                    'source': mapping.source_entity.value,
                    'target': mapping.target_entity.value,
                    'field_count': len(mapping.field_mappings)
                }
                for key, mapping in self.mappings.items()
            },
            'property_mappings_count': len(self.property_mappings),
            'transformation_functions': list(self.transformation_functions.keys())
        }

# Service instance
_mapping_service = None

def get_data_mapping_service() -> DataMappingService:
    """Get singleton mapping service instance"""
    global _mapping_service
    if _mapping_service is None:
        _mapping_service = DataMappingService()
    return _mapping_service
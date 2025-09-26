"""
AppFolio Data Mapping Service

Handles data transformation and mapping between EstateCore and AppFolio
data formats, field mappings, and business logic transformations.
"""

import logging
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import re

from .models import (
    AppFolioProperty, AppFolioUnit, AppFolioTenant, AppFolioLease,
    AppFolioPayment, AppFolioWorkOrder, AppFolioVendor, AppFolioAccount,
    AppFolioTransaction, AppFolioDocument, AppFolioPortfolio,
    AppFolioApplication, AppFolioMessage,
    PropertyType, UnitType, LeaseStatus, PaymentStatus, 
    WorkOrderStatus, WorkOrderPriority
)

logger = logging.getLogger(__name__)

class MappingDirection(Enum):
    """Data mapping direction"""
    TO_APPFOLIO = "to_appfolio"
    FROM_APPFOLIO = "from_appfolio"
    BIDIRECTIONAL = "bidirectional"

class FieldMappingType(Enum):
    """Field mapping types"""
    DIRECT = "direct"           # 1:1 mapping
    TRANSFORM = "transform"     # Apply transformation function
    CALCULATED = "calculated"   # Calculate from multiple fields
    CONDITIONAL = "conditional" # Conditional mapping
    LOOKUP = "lookup"          # Lookup table mapping
    CUSTOM = "custom"          # Custom mapping function

@dataclass
class FieldMapping:
    """Field mapping configuration"""
    source_field: str
    target_field: str
    mapping_type: FieldMappingType = FieldMappingType.DIRECT
    transformation_function: Optional[str] = None
    default_value: Any = None
    required: bool = False
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None

@dataclass
class EntityMapping:
    """Entity mapping configuration"""
    entity_type: str
    source_entity: str
    target_entity: str
    field_mappings: List[FieldMapping] = field(default_factory=list)
    custom_mappings: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    post_processing: Optional[str] = None

class AppFolioMappingService:
    """
    AppFolio Data Mapping Service
    
    Handles all data transformation and mapping operations between
    EstateCore and AppFolio data formats.
    """
    
    def __init__(self):
        self.entity_mappings: Dict[str, EntityMapping] = {}
        self.transformation_functions: Dict[str, Callable] = {}
        self.lookup_tables: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default mappings
        self._setup_default_mappings()
        self._setup_transformation_functions()
        self._setup_lookup_tables()
        
        logger.info("AppFolio Mapping Service initialized")
    
    def _setup_default_mappings(self):
        """Setup default entity and field mappings"""
        
        # Property mappings
        property_mappings = [
            FieldMapping("id", "id", FieldMappingType.DIRECT),
            FieldMapping("name", "name", FieldMappingType.DIRECT, required=True),
            FieldMapping("address", "address", FieldMappingType.TRANSFORM, "format_address"),
            FieldMapping("property_type", "property_type", FieldMappingType.LOOKUP, "property_type_lookup"),
            FieldMapping("unit_count", "unit_count", FieldMappingType.DIRECT, default_value=0),
            FieldMapping("description", "description", FieldMappingType.DIRECT),
            FieldMapping("year_built", "year_built", FieldMappingType.DIRECT),
            FieldMapping("square_footage", "square_footage", FieldMappingType.DIRECT),
            FieldMapping("amenities", "amenities", FieldMappingType.TRANSFORM, "format_amenities_list"),
            FieldMapping("monthly_income", "monthly_rent", FieldMappingType.DIRECT),
            FieldMapping("monthly_expenses", "monthly_expenses", FieldMappingType.DIRECT),
        ]
        
        self.entity_mappings["properties"] = EntityMapping(
            entity_type="properties",
            source_entity="EstateCore_Property",
            target_entity="AppFolio_Property",
            field_mappings=property_mappings
        )
        
        # Unit mappings
        unit_mappings = [
            FieldMapping("id", "id", FieldMappingType.DIRECT),
            FieldMapping("property_id", "property_id", FieldMappingType.DIRECT, required=True),
            FieldMapping("unit_number", "unit_number", FieldMappingType.DIRECT, required=True),
            FieldMapping("unit_type", "unit_type", FieldMappingType.LOOKUP, "unit_type_lookup"),
            FieldMapping("bedrooms", "bedrooms", FieldMappingType.DIRECT),
            FieldMapping("bathrooms", "bathrooms", FieldMappingType.DIRECT),
            FieldMapping("square_footage", "square_footage", FieldMappingType.DIRECT),
            FieldMapping("rent_amount", "rent_amount", FieldMappingType.DIRECT),
            FieldMapping("security_deposit", "security_deposit", FieldMappingType.DIRECT),
            FieldMapping("available_date", "available_date", FieldMappingType.TRANSFORM, "format_date"),
            FieldMapping("amenities", "amenities", FieldMappingType.TRANSFORM, "format_amenities_list"),
        ]
        
        self.entity_mappings["units"] = EntityMapping(
            entity_type="units",
            source_entity="EstateCore_Unit",
            target_entity="AppFolio_Unit",
            field_mappings=unit_mappings
        )
        
        # Tenant mappings
        tenant_mappings = [
            FieldMapping("id", "id", FieldMappingType.DIRECT),
            FieldMapping("first_name", "first_name", FieldMappingType.DIRECT, required=True),
            FieldMapping("last_name", "last_name", FieldMappingType.DIRECT, required=True),
            FieldMapping("email", "email", FieldMappingType.TRANSFORM, "format_email"),
            FieldMapping("phone", "phone", FieldMappingType.TRANSFORM, "format_phone"),
            FieldMapping("mobile_phone", "mobile_phone", FieldMappingType.TRANSFORM, "format_phone"),
            FieldMapping("emergency_contact", "emergency_contact", FieldMappingType.TRANSFORM, "format_contact"),
            FieldMapping("move_in_date", "move_in_date", FieldMappingType.TRANSFORM, "format_date"),
            FieldMapping("move_out_date", "move_out_date", FieldMappingType.TRANSFORM, "format_date"),
            FieldMapping("monthly_income", "monthly_income", FieldMappingType.DIRECT),
            FieldMapping("credit_score", "credit_score", FieldMappingType.DIRECT),
        ]
        
        self.entity_mappings["tenants"] = EntityMapping(
            entity_type="tenants",
            source_entity="EstateCore_Tenant",
            target_entity="AppFolio_Tenant",
            field_mappings=tenant_mappings
        )
        
        # Lease mappings
        lease_mappings = [
            FieldMapping("id", "id", FieldMappingType.DIRECT),
            FieldMapping("property_id", "property_id", FieldMappingType.DIRECT, required=True),
            FieldMapping("unit_id", "unit_id", FieldMappingType.DIRECT, required=True),
            FieldMapping("tenant_id", "tenant_id", FieldMappingType.DIRECT, required=True),
            FieldMapping("start_date", "start_date", FieldMappingType.TRANSFORM, "format_date", required=True),
            FieldMapping("end_date", "end_date", FieldMappingType.TRANSFORM, "format_date", required=True),
            FieldMapping("status", "status", FieldMappingType.LOOKUP, "lease_status_lookup"),
            FieldMapping("rent_amount", "rent_amount", FieldMappingType.DIRECT, required=True),
            FieldMapping("security_deposit", "security_deposit", FieldMappingType.DIRECT),
            FieldMapping("pet_deposit", "pet_deposit", FieldMappingType.DIRECT),
            FieldMapping("rent_due_day", "rent_due_day", FieldMappingType.DIRECT, default_value=1),
            FieldMapping("late_fee_amount", "late_fee_amount", FieldMappingType.DIRECT),
            FieldMapping("auto_renew", "auto_renew", FieldMappingType.DIRECT, default_value=False),
        ]
        
        self.entity_mappings["leases"] = EntityMapping(
            entity_type="leases",
            source_entity="EstateCore_Lease",
            target_entity="AppFolio_Lease",
            field_mappings=lease_mappings
        )
        
        # Payment mappings
        payment_mappings = [
            FieldMapping("id", "id", FieldMappingType.DIRECT),
            FieldMapping("tenant_id", "tenant_id", FieldMappingType.DIRECT, required=True),
            FieldMapping("lease_id", "lease_id", FieldMappingType.DIRECT),
            FieldMapping("property_id", "property_id", FieldMappingType.DIRECT),
            FieldMapping("unit_id", "unit_id", FieldMappingType.DIRECT),
            FieldMapping("amount", "amount", FieldMappingType.DIRECT, required=True),
            FieldMapping("payment_date", "payment_date", FieldMappingType.TRANSFORM, "format_date", required=True),
            FieldMapping("payment_method", "payment_method", FieldMappingType.LOOKUP, "payment_method_lookup"),
            FieldMapping("status", "status", FieldMappingType.LOOKUP, "payment_status_lookup"),
            FieldMapping("reference_number", "reference_number", FieldMappingType.DIRECT),
            FieldMapping("description", "description", FieldMappingType.DIRECT),
        ]
        
        self.entity_mappings["payments"] = EntityMapping(
            entity_type="payments",
            source_entity="EstateCore_Payment",
            target_entity="AppFolio_Payment",
            field_mappings=payment_mappings
        )
        
        # Work Order mappings
        work_order_mappings = [
            FieldMapping("id", "id", FieldMappingType.DIRECT),
            FieldMapping("property_id", "property_id", FieldMappingType.DIRECT, required=True),
            FieldMapping("unit_id", "unit_id", FieldMappingType.DIRECT),
            FieldMapping("tenant_id", "tenant_id", FieldMappingType.DIRECT),
            FieldMapping("vendor_id", "vendor_id", FieldMappingType.DIRECT),
            FieldMapping("title", "title", FieldMappingType.DIRECT, required=True),
            FieldMapping("description", "description", FieldMappingType.DIRECT, required=True),
            FieldMapping("status", "status", FieldMappingType.LOOKUP, "work_order_status_lookup"),
            FieldMapping("priority", "priority", FieldMappingType.LOOKUP, "work_order_priority_lookup"),
            FieldMapping("category", "category", FieldMappingType.LOOKUP, "work_order_category_lookup"),
            FieldMapping("created_date", "created_date", FieldMappingType.TRANSFORM, "format_date"),
            FieldMapping("scheduled_date", "scheduled_date", FieldMappingType.TRANSFORM, "format_date"),
            FieldMapping("estimated_cost", "estimated_cost", FieldMappingType.DIRECT),
            FieldMapping("actual_cost", "actual_cost", FieldMappingType.DIRECT),
        ]
        
        self.entity_mappings["work_orders"] = EntityMapping(
            entity_type="work_orders",
            source_entity="EstateCore_WorkOrder",
            target_entity="AppFolio_WorkOrder",
            field_mappings=work_order_mappings
        )
        
        # Vendor mappings
        vendor_mappings = [
            FieldMapping("id", "id", FieldMappingType.DIRECT),
            FieldMapping("name", "name", FieldMappingType.DIRECT, required=True),
            FieldMapping("business_type", "business_type", FieldMappingType.LOOKUP, "vendor_type_lookup"),
            FieldMapping("contact_person", "contact_person", FieldMappingType.DIRECT),
            FieldMapping("email", "email", FieldMappingType.TRANSFORM, "format_email"),
            FieldMapping("phone", "phone", FieldMappingType.TRANSFORM, "format_phone"),
            FieldMapping("address", "address", FieldMappingType.TRANSFORM, "format_address"),
            FieldMapping("license_number", "license_number", FieldMappingType.DIRECT),
            FieldMapping("tax_id", "tax_id", FieldMappingType.DIRECT),
            FieldMapping("hourly_rate", "hourly_rate", FieldMappingType.DIRECT),
            FieldMapping("services", "services", FieldMappingType.TRANSFORM, "format_services_list"),
        ]
        
        self.entity_mappings["vendors"] = EntityMapping(
            entity_type="vendors",
            source_entity="EstateCore_Vendor",
            target_entity="AppFolio_Vendor",
            field_mappings=vendor_mappings
        )
    
    def _setup_transformation_functions(self):
        """Setup transformation functions"""
        
        self.transformation_functions.update({
            "format_address": self._format_address,
            "format_date": self._format_date,
            "format_datetime": self._format_datetime,
            "format_phone": self._format_phone,
            "format_email": self._format_email,
            "format_contact": self._format_contact,
            "format_amenities_list": self._format_amenities_list,
            "format_services_list": self._format_services_list,
            "calculate_monthly_rent": self._calculate_monthly_rent,
            "calculate_total_deposit": self._calculate_total_deposit,
            "normalize_unit_number": self._normalize_unit_number,
            "validate_rent_amount": self._validate_rent_amount,
        })
    
    def _setup_lookup_tables(self):
        """Setup lookup tables for data mapping"""
        
        # Property type mappings
        self.lookup_tables["property_type_lookup"] = {
            "apartment": PropertyType.RESIDENTIAL.value,
            "single_family": PropertyType.RESIDENTIAL.value,
            "multi_family": PropertyType.RESIDENTIAL.value,
            "commercial": PropertyType.COMMERCIAL.value,
            "retail": PropertyType.RETAIL.value,
            "office": PropertyType.OFFICE.value,
            "warehouse": PropertyType.INDUSTRIAL.value,
            "mixed_use": PropertyType.MIXED_USE.value,
            "land": PropertyType.LAND.value,
        }
        
        # Unit type mappings
        self.lookup_tables["unit_type_lookup"] = {
            "apartment": UnitType.APARTMENT.value,
            "studio": UnitType.STUDIO.value,
            "house": UnitType.HOUSE.value,
            "condo": UnitType.CONDO.value,
            "townhouse": UnitType.TOWNHOUSE.value,
            "room": UnitType.ROOM.value,
            "commercial": UnitType.COMMERCIAL_SPACE.value,
            "parking": UnitType.PARKING_SPACE.value,
            "storage": UnitType.STORAGE.value,
        }
        
        # Lease status mappings
        self.lookup_tables["lease_status_lookup"] = {
            "current": LeaseStatus.ACTIVE.value,
            "active": LeaseStatus.ACTIVE.value,
            "pending": LeaseStatus.PENDING.value,
            "expired": LeaseStatus.EXPIRED.value,
            "terminated": LeaseStatus.TERMINATED.value,
            "cancelled": LeaseStatus.CANCELLED.value,
            "renewed": LeaseStatus.RENEWED.value,
        }
        
        # Payment status mappings
        self.lookup_tables["payment_status_lookup"] = {
            "pending": PaymentStatus.PENDING.value,
            "processing": PaymentStatus.PENDING.value,
            "completed": PaymentStatus.PROCESSED.value,
            "processed": PaymentStatus.PROCESSED.value,
            "failed": PaymentStatus.FAILED.value,
            "declined": PaymentStatus.FAILED.value,
            "refunded": PaymentStatus.REFUNDED.value,
            "cancelled": PaymentStatus.CANCELLED.value,
            "partial": PaymentStatus.PARTIAL.value,
        }
        
        # Payment method mappings
        self.lookup_tables["payment_method_lookup"] = {
            "cash": "cash",
            "check": "check",
            "credit_card": "credit_card",
            "debit_card": "debit_card",
            "ach": "bank_transfer",
            "wire": "wire_transfer",
            "money_order": "money_order",
            "online": "online_payment",
        }
        
        # Work order status mappings
        self.lookup_tables["work_order_status_lookup"] = {
            "open": WorkOrderStatus.OPEN.value,
            "new": WorkOrderStatus.OPEN.value,
            "in_progress": WorkOrderStatus.IN_PROGRESS.value,
            "assigned": WorkOrderStatus.IN_PROGRESS.value,
            "completed": WorkOrderStatus.COMPLETED.value,
            "closed": WorkOrderStatus.COMPLETED.value,
            "cancelled": WorkOrderStatus.CANCELLED.value,
            "on_hold": WorkOrderStatus.ON_HOLD.value,
        }
        
        # Work order priority mappings
        self.lookup_tables["work_order_priority_lookup"] = {
            "low": WorkOrderPriority.LOW.value,
            "normal": WorkOrderPriority.NORMAL.value,
            "medium": WorkOrderPriority.NORMAL.value,
            "high": WorkOrderPriority.HIGH.value,
            "urgent": WorkOrderPriority.URGENT.value,
            "emergency": WorkOrderPriority.EMERGENCY.value,
        }
        
        # Work order category mappings
        self.lookup_tables["work_order_category_lookup"] = {
            "plumbing": "plumbing",
            "electrical": "electrical",
            "hvac": "hvac",
            "appliance": "appliance",
            "painting": "painting",
            "flooring": "flooring",
            "cleaning": "cleaning",
            "landscaping": "landscaping",
            "security": "security",
            "general": "general_maintenance",
        }
        
        # Vendor type mappings
        self.lookup_tables["vendor_type_lookup"] = {
            "contractor": "general_contractor",
            "plumber": "plumbing",
            "electrician": "electrical",
            "hvac": "hvac",
            "painter": "painting",
            "cleaner": "cleaning",
            "landscaper": "landscaping",
            "security": "security",
            "appliance": "appliance_repair",
        }
    
    def map_entity(self, entity_type: str, source_data: Dict[str, Any], 
                   direction: MappingDirection = MappingDirection.TO_APPFOLIO) -> Dict[str, Any]:
        """
        Map entity data between EstateCore and AppFolio formats
        
        Args:
            entity_type: Type of entity to map
            source_data: Source data dictionary
            direction: Mapping direction
            
        Returns:
            Mapped data dictionary
        """
        try:
            if entity_type not in self.entity_mappings:
                raise ValueError(f"No mapping configuration found for entity type: {entity_type}")
            
            mapping = self.entity_mappings[entity_type]
            mapped_data = {}
            
            # Apply field mappings
            for field_mapping in mapping.field_mappings:
                try:
                    mapped_value = self._apply_field_mapping(field_mapping, source_data, direction)
                    if mapped_value is not None:
                        mapped_data[field_mapping.target_field] = mapped_value
                except Exception as e:
                    logger.warning(f"Failed to map field {field_mapping.source_field}: {str(e)}")
                    if field_mapping.required:
                        raise
            
            # Apply custom mappings
            if mapping.custom_mappings:
                custom_data = self._apply_custom_mappings(mapping.custom_mappings, source_data, direction)
                mapped_data.update(custom_data)
            
            # Validate mapped data
            if mapping.validation_rules:
                self._validate_mapped_data(mapped_data, mapping.validation_rules)
            
            # Post-processing
            if mapping.post_processing and mapping.post_processing in self.transformation_functions:
                mapped_data = self.transformation_functions[mapping.post_processing](mapped_data)
            
            logger.debug(f"Successfully mapped {entity_type} entity")
            return mapped_data
            
        except Exception as e:
            logger.error(f"Failed to map {entity_type} entity: {str(e)}")
            raise
    
    def _apply_field_mapping(self, field_mapping: FieldMapping, source_data: Dict[str, Any], 
                           direction: MappingDirection) -> Any:
        """Apply individual field mapping"""
        
        source_value = source_data.get(field_mapping.source_field)
        
        # Handle missing required fields
        if source_value is None:
            if field_mapping.required:
                if field_mapping.default_value is not None:
                    source_value = field_mapping.default_value
                else:
                    raise ValueError(f"Required field {field_mapping.source_field} is missing")
            elif field_mapping.default_value is not None:
                source_value = field_mapping.default_value
            else:
                return None
        
        # Apply mapping based on type
        if field_mapping.mapping_type == FieldMappingType.DIRECT:
            return source_value
        
        elif field_mapping.mapping_type == FieldMappingType.TRANSFORM:
            if field_mapping.transformation_function in self.transformation_functions:
                transform_func = self.transformation_functions[field_mapping.transformation_function]
                return transform_func(source_value)
            else:
                logger.warning(f"Transformation function {field_mapping.transformation_function} not found")
                return source_value
        
        elif field_mapping.mapping_type == FieldMappingType.LOOKUP:
            if field_mapping.transformation_function in self.lookup_tables:
                lookup_table = self.lookup_tables[field_mapping.transformation_function]
                return lookup_table.get(str(source_value).lower(), source_value)
            else:
                logger.warning(f"Lookup table {field_mapping.transformation_function} not found")
                return source_value
        
        elif field_mapping.mapping_type == FieldMappingType.CALCULATED:
            # For calculated fields, we would need additional logic here
            return source_value
        
        elif field_mapping.mapping_type == FieldMappingType.CONDITIONAL:
            # For conditional mapping, we would need condition evaluation logic
            return source_value
        
        elif field_mapping.mapping_type == FieldMappingType.CUSTOM:
            if field_mapping.transformation_function in self.transformation_functions:
                transform_func = self.transformation_functions[field_mapping.transformation_function]
                return transform_func(source_value, source_data)
            else:
                logger.warning(f"Custom function {field_mapping.transformation_function} not found")
                return source_value
        
        return source_value
    
    def _apply_custom_mappings(self, custom_mappings: Dict[str, Any], 
                             source_data: Dict[str, Any], direction: MappingDirection) -> Dict[str, Any]:
        """Apply custom mapping logic"""
        custom_data = {}
        
        for field_name, mapping_config in custom_mappings.items():
            try:
                if isinstance(mapping_config, str) and mapping_config in self.transformation_functions:
                    transform_func = self.transformation_functions[mapping_config]
                    custom_data[field_name] = transform_func(source_data)
                elif isinstance(mapping_config, dict):
                    # Handle complex custom mapping configurations
                    if 'function' in mapping_config and mapping_config['function'] in self.transformation_functions:
                        transform_func = self.transformation_functions[mapping_config['function']]
                        custom_data[field_name] = transform_func(source_data, mapping_config)
            except Exception as e:
                logger.warning(f"Failed to apply custom mapping for {field_name}: {str(e)}")
        
        return custom_data
    
    def _validate_mapped_data(self, mapped_data: Dict[str, Any], validation_rules: Dict[str, Any]):
        """Validate mapped data against rules"""
        for field_name, rules in validation_rules.items():
            if field_name in mapped_data:
                value = mapped_data[field_name]
                
                if 'required' in rules and rules['required'] and value is None:
                    raise ValueError(f"Required field {field_name} is missing")
                
                if 'type' in rules and value is not None:
                    expected_type = rules['type']
                    if not isinstance(value, expected_type):
                        raise ValueError(f"Field {field_name} must be of type {expected_type}")
                
                if 'min_length' in rules and isinstance(value, str):
                    if len(value) < rules['min_length']:
                        raise ValueError(f"Field {field_name} must be at least {rules['min_length']} characters")
                
                if 'max_length' in rules and isinstance(value, str):
                    if len(value) > rules['max_length']:
                        raise ValueError(f"Field {field_name} must be at most {rules['max_length']} characters")
                
                if 'pattern' in rules and isinstance(value, str):
                    if not re.match(rules['pattern'], value):
                        raise ValueError(f"Field {field_name} does not match required pattern")
    
    # Transformation functions
    
    def _format_address(self, address_data: Union[str, Dict[str, str]]) -> Dict[str, str]:
        """Format address data"""
        if isinstance(address_data, str):
            # Simple string address
            return {"full_address": address_data}
        elif isinstance(address_data, dict):
            # Structured address
            formatted = {}
            field_mappings = {
                'street': 'street_address',
                'address1': 'street_address',
                'street_address': 'street_address',
                'city': 'city',
                'state': 'state',
                'zip': 'postal_code',
                'zipcode': 'postal_code',
                'postal_code': 'postal_code',
                'country': 'country'
            }
            
            for source_key, target_key in field_mappings.items():
                if source_key in address_data:
                    formatted[target_key] = address_data[source_key]
            
            return formatted
        
        return {}
    
    def _format_date(self, date_value: Union[str, datetime, date]) -> str:
        """Format date value"""
        if isinstance(date_value, str):
            try:
                # Try parsing common date formats
                if 'T' in date_value:
                    parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                    return parsed_date.date().isoformat()
                else:
                    return date_value
            except ValueError:
                return date_value
        elif isinstance(date_value, datetime):
            return date_value.date().isoformat()
        elif isinstance(date_value, date):
            return date_value.isoformat()
        
        return str(date_value)
    
    def _format_datetime(self, datetime_value: Union[str, datetime]) -> str:
        """Format datetime value"""
        if isinstance(datetime_value, str):
            try:
                parsed_datetime = datetime.fromisoformat(datetime_value.replace('Z', '+00:00'))
                return parsed_datetime.isoformat()
            except ValueError:
                return datetime_value
        elif isinstance(datetime_value, datetime):
            return datetime_value.isoformat()
        
        return str(datetime_value)
    
    def _format_phone(self, phone_value: str) -> str:
        """Format phone number"""
        if not phone_value:
            return ""
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_value)
        
        # Format US phone numbers
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return phone_value
    
    def _format_email(self, email_value: str) -> str:
        """Format and validate email"""
        if not email_value:
            return ""
        
        email = email_value.lower().strip()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return email
        
        return email_value
    
    def _format_contact(self, contact_data: Dict[str, Any]) -> Dict[str, str]:
        """Format emergency contact information"""
        if not contact_data:
            return {}
        
        formatted = {}
        if 'name' in contact_data:
            formatted['name'] = contact_data['name']
        if 'phone' in contact_data:
            formatted['phone'] = self._format_phone(contact_data['phone'])
        if 'relationship' in contact_data:
            formatted['relationship'] = contact_data['relationship']
        if 'email' in contact_data:
            formatted['email'] = self._format_email(contact_data['email'])
        
        return formatted
    
    def _format_amenities_list(self, amenities: Union[str, List[str]]) -> List[str]:
        """Format amenities list"""
        if isinstance(amenities, str):
            # Split comma-separated string
            return [amenity.strip() for amenity in amenities.split(',') if amenity.strip()]
        elif isinstance(amenities, list):
            return [str(amenity).strip() for amenity in amenities if amenity]
        
        return []
    
    def _format_services_list(self, services: Union[str, List[str]]) -> List[str]:
        """Format services list"""
        return self._format_amenities_list(services)
    
    def _calculate_monthly_rent(self, source_data: Dict[str, Any]) -> float:
        """Calculate monthly rent from lease data"""
        rent_amount = source_data.get('rent_amount', 0)
        rent_frequency = source_data.get('rent_frequency', 'monthly')
        
        if rent_frequency == 'weekly':
            return rent_amount * 4.33  # Average weeks per month
        elif rent_frequency == 'daily':
            return rent_amount * 30.44  # Average days per month
        elif rent_frequency == 'annually':
            return rent_amount / 12
        
        return rent_amount
    
    def _calculate_total_deposit(self, source_data: Dict[str, Any]) -> float:
        """Calculate total deposit amount"""
        security_deposit = source_data.get('security_deposit', 0) or 0
        pet_deposit = source_data.get('pet_deposit', 0) or 0
        cleaning_deposit = source_data.get('cleaning_deposit', 0) or 0
        
        return security_deposit + pet_deposit + cleaning_deposit
    
    def _normalize_unit_number(self, unit_number: str) -> str:
        """Normalize unit number format"""
        if not unit_number:
            return ""
        
        # Remove leading/trailing spaces and convert to uppercase
        normalized = str(unit_number).strip().upper()
        
        # Add leading zeros if it's a numeric unit
        if normalized.isdigit():
            return normalized.zfill(3)  # Pad to 3 digits
        
        return normalized
    
    def _validate_rent_amount(self, rent_amount: float) -> float:
        """Validate rent amount"""
        if not isinstance(rent_amount, (int, float)):
            raise ValueError("Rent amount must be a number")
        
        if rent_amount < 0:
            raise ValueError("Rent amount cannot be negative")
        
        if rent_amount > 100000:  # Reasonable upper limit
            logger.warning(f"Unusually high rent amount: {rent_amount}")
        
        return round(rent_amount, 2)
    
    def add_custom_mapping(self, entity_type: str, field_mapping: FieldMapping):
        """Add custom field mapping"""
        if entity_type in self.entity_mappings:
            self.entity_mappings[entity_type].field_mappings.append(field_mapping)
        else:
            logger.warning(f"Entity type {entity_type} not found for custom mapping")
    
    def add_transformation_function(self, name: str, function: Callable):
        """Add custom transformation function"""
        self.transformation_functions[name] = function
    
    def add_lookup_table(self, name: str, lookup_data: Dict[str, Any]):
        """Add custom lookup table"""
        self.lookup_tables[name] = lookup_data
    
    def get_mapping_summary(self) -> Dict[str, Any]:
        """Get summary of all mappings"""
        return {
            'entity_mappings': list(self.entity_mappings.keys()),
            'transformation_functions': list(self.transformation_functions.keys()),
            'lookup_tables': list(self.lookup_tables.keys()),
            'total_field_mappings': sum(
                len(mapping.field_mappings) for mapping in self.entity_mappings.values()
            )
        }
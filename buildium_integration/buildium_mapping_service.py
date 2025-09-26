"""
Buildium Mapping Service

Handles data transformation and mapping between EstateCore and Buildium formats
with support for custom field mappings, data validation, and small portfolio optimizations.
"""

import logging
import json
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from decimal import Decimal
import phonenumbers
from email_validator import validate_email, EmailNotValidError

from .models import (
    BuildiumProperty, BuildiumUnit, BuildiumTenant, BuildiumLease,
    BuildiumPayment, BuildiumMaintenanceRequest, BuildiumVendor,
    BuildiumApplication, BuildiumOwner, BuildiumDocument,
    BuildiumFinancialTransaction, PropertyType, UnitType,
    LeaseStatus, PaymentStatus, MaintenanceRequestStatus,
    MaintenancePriority, ApplicationStatus, DocumentType
)

logger = logging.getLogger(__name__)


class TransformationType(Enum):
    """Data transformation types"""
    DIRECT_MAP = "direct_map"
    CALCULATED = "calculated"
    CONCATENATED = "concatenated"
    FORMATTED = "formatted"
    CONDITIONAL = "conditional"
    LOOKUP = "lookup"
    CUSTOM_FUNCTION = "custom_function"
    DATE_FORMAT = "date_format"
    CURRENCY_CONVERSION = "currency_conversion"
    PHONE_FORMAT = "phone_format"
    EMAIL_VALIDATION = "email_validation"


class MappingDirection(Enum):
    """Mapping direction"""
    TO_BUILDIUM = "to_buildium"
    FROM_BUILDIUM = "from_buildium"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class FieldMapping:
    """Field mapping configuration"""
    source_field: str
    target_field: str
    transformation_type: TransformationType
    direction: MappingDirection = MappingDirection.BIDIRECTIONAL
    required: bool = False
    default_value: Optional[Any] = None
    validation_rules: List[str] = field(default_factory=list)
    transformation_config: Dict[str, Any] = field(default_factory=dict)
    custom_function: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class EntityMapping:
    """Complete entity mapping configuration"""
    entity_type: str
    field_mappings: List[FieldMapping]
    validation_rules: List[str] = field(default_factory=list)
    small_portfolio_optimized: bool = False
    custom_transformations: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MappingResult:
    """Result of mapping operation"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_issues: List[str] = field(default_factory=list)
    transformation_notes: List[str] = field(default_factory=list)


class BuildiumMappingService:
    """
    Buildium Mapping Service
    
    Handles bidirectional data transformation between EstateCore and Buildium
    with support for:
    - Custom field mappings
    - Data validation and formatting
    - Small portfolio optimizations
    - Type conversion and validation
    """
    
    def __init__(self):
        self.mappings: Dict[str, EntityMapping] = {}
        self.custom_transformers: Dict[str, Callable] = {}
        self.validation_cache: Dict[str, Dict] = {}
        
        # Initialize default mappings
        self._initialize_default_mappings()
        self._register_default_transformers()
    
    def _initialize_default_mappings(self):
        """Initialize default field mappings for all entity types"""
        
        # Property mappings
        property_mappings = [
            FieldMapping(
                source_field="name",
                target_field="Name",
                transformation_type=TransformationType.DIRECT_MAP,
                required=True
            ),
            FieldMapping(
                source_field="property_type",
                target_field="PropertyType",
                transformation_type=TransformationType.LOOKUP,
                transformation_config={
                    "lookup_table": {
                        "apartment": "Apartment",
                        "single_family": "SingleFamily",
                        "condo": "Condominium",
                        "townhouse": "Townhouse",
                        "duplex": "Duplex",
                        "commercial": "Commercial",
                        "mixed_use": "MixedUse"
                    }
                },
                required=True
            ),
            FieldMapping(
                source_field="address",
                target_field="Address",
                transformation_type=TransformationType.CUSTOM_FUNCTION,
                custom_function="format_address",
                required=True
            ),
            FieldMapping(
                source_field="unit_count",
                target_field="UnitCount",
                transformation_type=TransformationType.DIRECT_MAP,
                validation_rules=["positive_integer"]
            ),
            FieldMapping(
                source_field="year_built",
                target_field="YearBuilt",
                transformation_type=TransformationType.DIRECT_MAP,
                validation_rules=["valid_year"]
            ),
            FieldMapping(
                source_field="monthly_income",
                target_field="MonthlyIncome",
                transformation_type=TransformationType.CURRENCY_CONVERSION
            )
        ]
        
        self.mappings["property"] = EntityMapping(
            entity_type="property",
            field_mappings=property_mappings
        )
        
        # Unit mappings
        unit_mappings = [
            FieldMapping(
                source_field="unit_number",
                target_field="UnitNumber",
                transformation_type=TransformationType.FORMATTED,
                transformation_config={"format": "uppercase"},
                required=True
            ),
            FieldMapping(
                source_field="unit_type",
                target_field="UnitType",
                transformation_type=TransformationType.LOOKUP,
                transformation_config={
                    "lookup_table": {
                        "studio": "Studio",
                        "1_bedroom": "OneBedroom",
                        "2_bedroom": "TwoBedroom",
                        "3_bedroom": "ThreeBedroom",
                        "4_bedroom": "FourBedroom",
                        "5plus_bedroom": "FivePlusBedroom"
                    }
                }
            ),
            FieldMapping(
                source_field="rent_amount",
                target_field="RentAmount",
                transformation_type=TransformationType.CURRENCY_CONVERSION,
                validation_rules=["positive_amount"]
            ),
            FieldMapping(
                source_field="security_deposit",
                target_field="SecurityDeposit",
                transformation_type=TransformationType.CURRENCY_CONVERSION
            ),
            FieldMapping(
                source_field="square_footage",
                target_field="SquareFootage",
                transformation_type=TransformationType.DIRECT_MAP,
                validation_rules=["positive_integer"]
            )
        ]
        
        self.mappings["unit"] = EntityMapping(
            entity_type="unit",
            field_mappings=unit_mappings
        )
        
        # Tenant mappings
        tenant_mappings = [
            FieldMapping(
                source_field="first_name",
                target_field="FirstName",
                transformation_type=TransformationType.FORMATTED,
                transformation_config={"format": "title_case"},
                required=True
            ),
            FieldMapping(
                source_field="last_name",
                target_field="LastName",
                transformation_type=TransformationType.FORMATTED,
                transformation_config={"format": "title_case"},
                required=True
            ),
            FieldMapping(
                source_field="email",
                target_field="Email",
                transformation_type=TransformationType.EMAIL_VALIDATION,
                validation_rules=["valid_email"]
            ),
            FieldMapping(
                source_field="phone",
                target_field="Phone",
                transformation_type=TransformationType.PHONE_FORMAT,
                transformation_config={"format": "US", "default_region": "US"}
            ),
            FieldMapping(
                source_field="date_of_birth",
                target_field="DateOfBirth",
                transformation_type=TransformationType.DATE_FORMAT,
                transformation_config={"input_format": "%Y-%m-%d", "output_format": "ISO"}
            )
        ]
        
        self.mappings["tenant"] = EntityMapping(
            entity_type="tenant",
            field_mappings=tenant_mappings
        )
        
        # Payment mappings
        payment_mappings = [
            FieldMapping(
                source_field="amount",
                target_field="Amount",
                transformation_type=TransformationType.CURRENCY_CONVERSION,
                required=True,
                validation_rules=["positive_amount"]
            ),
            FieldMapping(
                source_field="payment_date",
                target_field="PaymentDate",
                transformation_type=TransformationType.DATE_FORMAT,
                required=True
            ),
            FieldMapping(
                source_field="payment_method",
                target_field="PaymentMethod",
                transformation_type=TransformationType.LOOKUP,
                transformation_config={
                    "lookup_table": {
                        "cash": "Cash",
                        "check": "Check",
                        "ach": "ACH",
                        "credit_card": "CreditCard",
                        "money_order": "MoneyOrder"
                    }
                }
            ),
            FieldMapping(
                source_field="status",
                target_field="Status",
                transformation_type=TransformationType.LOOKUP,
                transformation_config={
                    "lookup_table": {
                        "pending": "Pending",
                        "processed": "Processed",
                        "failed": "Failed",
                        "refunded": "Refunded"
                    }
                }
            )
        ]
        
        self.mappings["payment"] = EntityMapping(
            entity_type="payment",
            field_mappings=payment_mappings
        )
    
    def _register_default_transformers(self):
        """Register default transformation functions"""
        
        def format_address(value: Dict[str, str], config: Dict[str, Any]) -> Dict[str, str]:
            """Format address dictionary for Buildium"""
            if not isinstance(value, dict):
                return {}
            
            return {
                "AddressLine1": value.get("street", ""),
                "AddressLine2": value.get("unit", ""),
                "City": value.get("city", ""),
                "State": value.get("state", ""),
                "PostalCode": value.get("zip_code", ""),
                "Country": value.get("country", "US")
            }
        
        def format_phone(value: str, config: Dict[str, Any]) -> str:
            """Format phone number"""
            if not value:
                return ""
            
            try:
                region = config.get("default_region", "US")
                phone_number = phonenumbers.parse(value, region)
                
                if phonenumbers.is_valid_number(phone_number):
                    format_type = config.get("format", "US")
                    if format_type == "US":
                        return phonenumbers.format_number(
                            phone_number, 
                            phonenumbers.PhoneNumberFormat.NATIONAL
                        )
                    else:
                        return phonenumbers.format_number(
                            phone_number, 
                            phonenumbers.PhoneNumberFormat.E164
                        )
                else:
                    return value
            except Exception as e:
                logger.warning(f"Phone formatting failed: {e}")
                return value
        
        def validate_email(value: str, config: Dict[str, Any]) -> str:
            """Validate and normalize email"""
            if not value:
                return ""
            
            try:
                valid = validate_email(value)
                return valid.email
            except EmailNotValidError:
                logger.warning(f"Invalid email format: {value}")
                return value
        
        def format_currency(value: Union[str, float, Decimal], config: Dict[str, Any]) -> float:
            """Format currency value"""
            if value is None:
                return 0.0
            
            try:
                if isinstance(value, str):
                    # Remove currency symbols and formatting
                    cleaned = re.sub(r'[^\d.-]', '', value)
                    return float(cleaned)
                elif isinstance(value, Decimal):
                    return float(value)
                else:
                    return float(value)
            except (ValueError, TypeError):
                return 0.0
        
        def format_date(value: Union[str, date, datetime], config: Dict[str, Any]) -> str:
            """Format date value"""
            if not value:
                return ""
            
            try:
                if isinstance(value, str):
                    # Parse string date
                    input_format = config.get("input_format", "%Y-%m-%d")
                    dt = datetime.strptime(value, input_format)
                elif isinstance(value, date):
                    dt = datetime.combine(value, datetime.min.time())
                elif isinstance(value, datetime):
                    dt = value
                else:
                    return ""
                
                output_format = config.get("output_format", "ISO")
                if output_format == "ISO":
                    return dt.isoformat()
                else:
                    return dt.strftime(output_format)
                    
            except Exception as e:
                logger.warning(f"Date formatting failed: {e}")
                return str(value)
        
        # Register transformers
        self.custom_transformers.update({
            "format_address": format_address,
            "format_phone": format_phone,
            "validate_email": validate_email,
            "format_currency": format_currency,
            "format_date": format_date
        })
    
    def transform_to_buildium(
        self,
        entity_type: str,
        estatecore_data: Dict[str, Any],
        organization_id: str,
        custom_mappings: Optional[Dict[str, Any]] = None
    ) -> MappingResult:
        """Transform EstateCore data to Buildium format"""
        try:
            mapping = self.mappings.get(entity_type)
            if not mapping:
                return MappingResult(
                    success=False,
                    errors=[f"No mapping found for entity type: {entity_type}"]
                )
            
            buildium_data = {}
            errors = []
            warnings = []
            transformation_notes = []
            
            # Apply custom mappings if provided
            effective_mappings = mapping.field_mappings.copy()
            if custom_mappings:
                effective_mappings.extend(self._parse_custom_mappings(custom_mappings))
            
            for field_mapping in effective_mappings:
                if field_mapping.direction in [MappingDirection.TO_BUILDIUM, MappingDirection.BIDIRECTIONAL]:
                    try:
                        source_value = self._get_nested_value(estatecore_data, field_mapping.source_field)
                        
                        if source_value is None and field_mapping.required:
                            errors.append(f"Required field '{field_mapping.source_field}' is missing")
                            continue
                        
                        if source_value is None and field_mapping.default_value is not None:
                            source_value = field_mapping.default_value
                            transformation_notes.append(f"Used default value for {field_mapping.source_field}")
                        
                        # Apply transformation
                        transformed_value = self._apply_transformation(
                            source_value,
                            field_mapping.transformation_type,
                            field_mapping.transformation_config,
                            field_mapping.custom_function
                        )
                        
                        # Validate transformed value
                        validation_result = self._validate_field(
                            transformed_value,
                            field_mapping.validation_rules
                        )
                        
                        if not validation_result["valid"]:
                            if field_mapping.required:
                                errors.extend(validation_result["errors"])
                            else:
                                warnings.extend(validation_result["errors"])
                        
                        if transformed_value is not None:
                            self._set_nested_value(buildium_data, field_mapping.target_field, transformed_value)
                        
                    except Exception as e:
                        error_msg = f"Transformation failed for field {field_mapping.source_field}: {e}"
                        if field_mapping.required:
                            errors.append(error_msg)
                        else:
                            warnings.append(error_msg)
            
            return MappingResult(
                success=len(errors) == 0,
                data=buildium_data if len(errors) == 0 else None,
                errors=errors,
                warnings=warnings,
                transformation_notes=transformation_notes
            )
            
        except Exception as e:
            logger.error(f"Transformation to Buildium failed: {e}")
            return MappingResult(
                success=False,
                errors=[f"Transformation failed: {e}"]
            )
    
    def transform_from_buildium(
        self,
        entity_type: str,
        buildium_data: Dict[str, Any],
        organization_id: str,
        custom_mappings: Optional[Dict[str, Any]] = None
    ) -> MappingResult:
        """Transform Buildium data to EstateCore format"""
        try:
            mapping = self.mappings.get(entity_type)
            if not mapping:
                return MappingResult(
                    success=False,
                    errors=[f"No mapping found for entity type: {entity_type}"]
                )
            
            estatecore_data = {}
            errors = []
            warnings = []
            transformation_notes = []
            
            # Apply custom mappings if provided
            effective_mappings = mapping.field_mappings.copy()
            if custom_mappings:
                effective_mappings.extend(self._parse_custom_mappings(custom_mappings))
            
            for field_mapping in effective_mappings:
                if field_mapping.direction in [MappingDirection.FROM_BUILDIUM, MappingDirection.BIDIRECTIONAL]:
                    try:
                        # For reverse mapping, source and target are swapped
                        buildium_value = self._get_nested_value(buildium_data, field_mapping.target_field)
                        
                        if buildium_value is None and field_mapping.default_value is not None:
                            buildium_value = field_mapping.default_value
                            transformation_notes.append(f"Used default value for {field_mapping.target_field}")
                        
                        # Apply reverse transformation
                        transformed_value = self._apply_reverse_transformation(
                            buildium_value,
                            field_mapping.transformation_type,
                            field_mapping.transformation_config,
                            field_mapping.custom_function
                        )
                        
                        if transformed_value is not None:
                            self._set_nested_value(estatecore_data, field_mapping.source_field, transformed_value)
                        
                    except Exception as e:
                        warnings.append(f"Reverse transformation failed for field {field_mapping.target_field}: {e}")
            
            # Add metadata
            estatecore_data["buildium_id"] = buildium_data.get("Id")
            estatecore_data["sync_metadata"] = {
                "last_sync": datetime.utcnow().isoformat(),
                "source": "buildium",
                "buildium_updated_at": buildium_data.get("UpdatedDateTime")
            }
            
            return MappingResult(
                success=True,
                data=estatecore_data,
                warnings=warnings,
                transformation_notes=transformation_notes
            )
            
        except Exception as e:
            logger.error(f"Transformation from Buildium failed: {e}")
            return MappingResult(
                success=False,
                errors=[f"Transformation failed: {e}"]
            )
    
    def create_custom_mapping(
        self,
        organization_id: str,
        entity_type: str,
        field_mappings: List[Dict[str, Any]]
    ) -> bool:
        """Create custom mapping configuration"""
        try:
            mapping_objects = []
            for mapping_dict in field_mappings:
                field_mapping = FieldMapping(
                    source_field=mapping_dict["source_field"],
                    target_field=mapping_dict["target_field"],
                    transformation_type=TransformationType(mapping_dict["transformation_type"]),
                    direction=MappingDirection(mapping_dict.get("direction", "bidirectional")),
                    required=mapping_dict.get("required", False),
                    default_value=mapping_dict.get("default_value"),
                    validation_rules=mapping_dict.get("validation_rules", []),
                    transformation_config=mapping_dict.get("transformation_config", {}),
                    custom_function=mapping_dict.get("custom_function")
                )
                mapping_objects.append(field_mapping)
            
            custom_mapping_key = f"{organization_id}_{entity_type}"
            if custom_mapping_key in self.mappings:
                # Extend existing mapping
                self.mappings[custom_mapping_key].field_mappings.extend(mapping_objects)
            else:
                # Create new custom mapping
                self.mappings[custom_mapping_key] = EntityMapping(
                    entity_type=entity_type,
                    field_mappings=mapping_objects
                )
            
            logger.info(f"Created custom mapping for {organization_id} - {entity_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create custom mapping: {e}")
            return False
    
    def register_custom_transformer(self, name: str, function: Callable) -> bool:
        """Register custom transformation function"""
        try:
            self.custom_transformers[name] = function
            logger.info(f"Registered custom transformer: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register custom transformer: {e}")
            return False
    
    # Helper methods
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation"""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _apply_transformation(
        self,
        value: Any,
        transformation_type: TransformationType,
        config: Dict[str, Any],
        custom_function: Optional[str]
    ) -> Any:
        """Apply transformation to value"""
        if value is None:
            return None
        
        try:
            if transformation_type == TransformationType.DIRECT_MAP:
                return value
            
            elif transformation_type == TransformationType.LOOKUP:
                lookup_table = config.get("lookup_table", {})
                return lookup_table.get(str(value), value)
            
            elif transformation_type == TransformationType.FORMATTED:
                format_type = config.get("format", "")
                if format_type == "uppercase":
                    return str(value).upper()
                elif format_type == "lowercase":
                    return str(value).lower()
                elif format_type == "title_case":
                    return str(value).title()
                else:
                    return value
            
            elif transformation_type == TransformationType.CURRENCY_CONVERSION:
                return self.custom_transformers["format_currency"](value, config)
            
            elif transformation_type == TransformationType.DATE_FORMAT:
                return self.custom_transformers["format_date"](value, config)
            
            elif transformation_type == TransformationType.PHONE_FORMAT:
                return self.custom_transformers["format_phone"](value, config)
            
            elif transformation_type == TransformationType.EMAIL_VALIDATION:
                return self.custom_transformers["validate_email"](value, config)
            
            elif transformation_type == TransformationType.CUSTOM_FUNCTION and custom_function:
                if custom_function in self.custom_transformers:
                    return self.custom_transformers[custom_function](value, config)
                else:
                    logger.warning(f"Custom function not found: {custom_function}")
                    return value
            
            else:
                return value
                
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            return value
    
    def _apply_reverse_transformation(
        self,
        value: Any,
        transformation_type: TransformationType,
        config: Dict[str, Any],
        custom_function: Optional[str]
    ) -> Any:
        """Apply reverse transformation for Buildium to EstateCore"""
        if value is None:
            return None
        
        try:
            if transformation_type == TransformationType.LOOKUP:
                # Reverse lookup
                lookup_table = config.get("lookup_table", {})
                reverse_lookup = {v: k for k, v in lookup_table.items()}
                return reverse_lookup.get(str(value), value)
            
            elif transformation_type == TransformationType.FORMATTED:
                format_type = config.get("format", "")
                if format_type in ["uppercase", "lowercase", "title_case"]:
                    return str(value).lower()  # Normalize to lowercase for EstateCore
                else:
                    return value
            
            else:
                # For most transformations, use the same function
                return self._apply_transformation(value, transformation_type, config, custom_function)
                
        except Exception as e:
            logger.error(f"Reverse transformation failed: {e}")
            return value
    
    def _validate_field(self, value: Any, validation_rules: List[str]) -> Dict[str, Any]:
        """Validate field value against rules"""
        errors = []
        
        for rule in validation_rules:
            if rule == "positive_integer" and (not isinstance(value, int) or value < 0):
                errors.append(f"Value must be a positive integer")
            
            elif rule == "positive_amount" and (not isinstance(value, (int, float)) or value < 0):
                errors.append(f"Value must be a positive amount")
            
            elif rule == "valid_email" and value:
                try:
                    validate_email(value)
                except EmailNotValidError:
                    errors.append(f"Invalid email format")
            
            elif rule == "valid_year" and value:
                current_year = datetime.now().year
                if not isinstance(value, int) or value < 1800 or value > current_year + 10:
                    errors.append(f"Invalid year")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _parse_custom_mappings(self, custom_mappings: Dict[str, Any]) -> List[FieldMapping]:
        """Parse custom mappings from dictionary"""
        mappings = []
        
        for mapping_dict in custom_mappings.get("field_mappings", []):
            try:
                field_mapping = FieldMapping(
                    source_field=mapping_dict["source_field"],
                    target_field=mapping_dict["target_field"],
                    transformation_type=TransformationType(mapping_dict["transformation_type"]),
                    direction=MappingDirection(mapping_dict.get("direction", "bidirectional")),
                    required=mapping_dict.get("required", False),
                    default_value=mapping_dict.get("default_value"),
                    validation_rules=mapping_dict.get("validation_rules", []),
                    transformation_config=mapping_dict.get("transformation_config", {}),
                    custom_function=mapping_dict.get("custom_function")
                )
                mappings.append(field_mapping)
            except Exception as e:
                logger.warning(f"Failed to parse custom mapping: {e}")
        
        return mappings
    
    def get_mapping_info(self, entity_type: str, organization_id: Optional[str] = None) -> Optional[EntityMapping]:
        """Get mapping information for entity type"""
        if organization_id:
            custom_key = f"{organization_id}_{entity_type}"
            if custom_key in self.mappings:
                return self.mappings[custom_key]
        
        return self.mappings.get(entity_type)
    
    def validate_mapping_configuration(self, entity_type: str, mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate mapping configuration"""
        errors = []
        warnings = []
        
        required_fields = ["source_field", "target_field", "transformation_type"]
        
        for i, mapping in enumerate(mappings):
            for field in required_fields:
                if field not in mapping:
                    errors.append(f"Mapping {i}: Missing required field '{field}'")
            
            try:
                TransformationType(mapping.get("transformation_type", ""))
            except ValueError:
                errors.append(f"Mapping {i}: Invalid transformation type")
            
            try:
                MappingDirection(mapping.get("direction", "bidirectional"))
            except ValueError:
                warnings.append(f"Mapping {i}: Invalid direction, using bidirectional")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
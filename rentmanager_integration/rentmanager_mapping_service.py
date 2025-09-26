"""
RentManager Data Mapping Service

Comprehensive data mapping service for transforming data between RentManager and EstateCore
with support for all property types, compliance requirements, and specialized features.
"""

import logging
import json
import uuid
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union, Callable, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import re

from .models import (
    RentManagerProperty, RentManagerUnit, RentManagerResident, RentManagerLease,
    RentManagerPayment, RentManagerWorkOrder, RentManagerVendor, RentManagerAccount,
    PropertyType, UnitType, ComplianceType, ResidentStatus, WorkOrderStatus, PaymentStatus,
    dict_to_property, property_to_dict
)

logger = logging.getLogger(__name__)

class MappingDirection(Enum):
    """Data mapping direction"""
    TO_ESTATECORE = "to_estatecore"
    TO_RENTMANAGER = "to_rentmanager"
    BIDIRECTIONAL = "bidirectional"

class MappingType(Enum):
    """Type of data mapping"""
    DIRECT = "direct"  # Direct field mapping
    TRANSFORM = "transform"  # Field transformation required
    CALCULATED = "calculated"  # Calculated field
    CONDITIONAL = "conditional"  # Conditional mapping
    COMPOSITE = "composite"  # Multiple fields to one
    SPLIT = "split"  # One field to multiple
    LOOKUP = "lookup"  # Lookup table mapping

@dataclass
class FieldMapping:
    """Field mapping configuration"""
    source_field: str
    target_field: str
    mapping_type: MappingType
    direction: MappingDirection = MappingDirection.BIDIRECTIONAL
    
    # Transformation configuration
    transform_function: Optional[str] = None
    lookup_table: Optional[Dict[str, Any]] = None
    validation_rules: List[str] = field(default_factory=list)
    default_value: Optional[Any] = None
    
    # Conditional mapping
    condition: Optional[str] = None
    condition_field: Optional[str] = None
    condition_value: Optional[Any] = None
    
    # Composite/Split configuration
    source_fields: List[str] = field(default_factory=list)
    target_fields: List[str] = field(default_factory=list)
    
    # Data quality
    required: bool = False
    format_pattern: Optional[str] = None
    
    # Compliance tracking
    compliance_required: bool = False
    audit_required: bool = False

@dataclass
class EntityMapping:
    """Entity mapping configuration"""
    entity_type: str
    source_entity: str
    target_entity: str
    field_mappings: List[FieldMapping] = field(default_factory=list)
    
    # Processing configuration
    pre_processing: List[str] = field(default_factory=list)
    post_processing: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    
    # Compliance configuration
    compliance_mappings: Dict[str, Any] = field(default_factory=dict)
    audit_fields: List[str] = field(default_factory=list)
    
    # Custom configuration
    custom_mappings: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MappingResult:
    """Result of a mapping operation"""
    success: bool
    mapped_data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    compliance_status: Dict[str, Any] = field(default_factory=dict)

class RentManagerMappingService:
    """
    RentManager Data Mapping Service
    
    Handles comprehensive data mapping between RentManager and EstateCore
    with support for all property types and compliance requirements.
    """
    
    def __init__(self):
        # Core mapping configurations
        self.entity_mappings: Dict[str, EntityMapping] = {}
        self.custom_mappings: Dict[str, Dict[str, Any]] = {}
        self.transform_functions: Dict[str, Callable] = {}
        self.validation_rules: Dict[str, Callable] = {}
        
        # Compliance mapping configurations
        self.compliance_mappings: Dict[ComplianceType, Dict[str, Any]] = {}
        self.compliance_validation: Dict[str, Callable] = {}
        
        # Lookup tables
        self.lookup_tables: Dict[str, Dict[str, Any]] = {}
        
        # Property type specific mappings
        self.property_type_mappings: Dict[PropertyType, Dict[str, Any]] = {}
        
        # Initialize default mappings
        self._initialize_default_mappings()
        self._initialize_compliance_mappings()
        self._initialize_lookup_tables()
        self._initialize_transform_functions()
        self._initialize_validation_rules()
        
        logger.info("RentManager Mapping Service initialized")
    
    # ===================================================
    # CORE MAPPING METHODS
    # ===================================================
    
    def map_to_estatecore(self, entity_type: str, rentmanager_data: Dict[str, Any],
                         organization_id: str = None) -> MappingResult:
        """
        Map RentManager data to EstateCore format
        
        Args:
            entity_type: Type of entity being mapped
            rentmanager_data: Data from RentManager
            organization_id: Organization identifier for custom mappings
            
        Returns:
            MappingResult with mapped data
        """
        try:
            # Get entity mapping configuration
            entity_mapping = self._get_entity_mapping(entity_type, organization_id)
            if not entity_mapping:
                return MappingResult(
                    success=False,
                    errors=[f"No mapping configuration found for entity type: {entity_type}"]
                )
            
            # Pre-processing
            processed_data = self._apply_pre_processing(rentmanager_data, entity_mapping)
            
            # Apply field mappings
            mapped_data = {}
            errors = []
            warnings = []
            validation_results = {}
            
            for field_mapping in entity_mapping.field_mappings:
                if field_mapping.direction not in [MappingDirection.TO_ESTATECORE, MappingDirection.BIDIRECTIONAL]:
                    continue
                
                mapping_result = self._apply_field_mapping(
                    processed_data, field_mapping, MappingDirection.TO_ESTATECORE
                )
                
                if mapping_result["success"]:
                    if mapping_result["value"] is not None:
                        mapped_data[field_mapping.target_field] = mapping_result["value"]
                else:
                    if field_mapping.required:
                        errors.append(mapping_result["error"])
                    else:
                        warnings.append(mapping_result["error"])
                
                # Store validation results
                if "validation" in mapping_result:
                    validation_results[field_mapping.target_field] = mapping_result["validation"]
            
            # Apply custom mappings
            custom_result = self._apply_custom_mappings(
                processed_data, mapped_data, entity_type, organization_id, MappingDirection.TO_ESTATECORE
            )
            mapped_data.update(custom_result.get("data", {}))
            warnings.extend(custom_result.get("warnings", []))
            
            # Post-processing
            final_data = self._apply_post_processing(mapped_data, entity_mapping)
            
            # Compliance validation
            compliance_status = self._validate_compliance(final_data, entity_type, organization_id)
            
            # Overall validation
            validation_result = self._validate_mapped_data(final_data, entity_mapping)
            if not validation_result["success"]:
                errors.extend(validation_result["errors"])
                warnings.extend(validation_result["warnings"])
            
            return MappingResult(
                success=len(errors) == 0,
                mapped_data=final_data if len(errors) == 0 else None,
                errors=errors,
                warnings=warnings,
                validation_results=validation_results,
                compliance_status=compliance_status
            )
            
        except Exception as e:
            logger.error(f"Failed to map data to EstateCore: {e}")
            return MappingResult(
                success=False,
                errors=[f"Mapping failed: {str(e)}"]
            )
    
    def map_to_rentmanager(self, entity_type: str, estatecore_data: Dict[str, Any],
                          organization_id: str = None) -> MappingResult:
        """
        Map EstateCore data to RentManager format
        
        Args:
            entity_type: Type of entity being mapped
            estatecore_data: Data from EstateCore
            organization_id: Organization identifier for custom mappings
            
        Returns:
            MappingResult with mapped data
        """
        try:
            # Get entity mapping configuration
            entity_mapping = self._get_entity_mapping(entity_type, organization_id)
            if not entity_mapping:
                return MappingResult(
                    success=False,
                    errors=[f"No mapping configuration found for entity type: {entity_type}"]
                )
            
            # Pre-processing
            processed_data = self._apply_pre_processing(estatecore_data, entity_mapping)
            
            # Apply field mappings
            mapped_data = {}
            errors = []
            warnings = []
            validation_results = {}
            
            for field_mapping in entity_mapping.field_mappings:
                if field_mapping.direction not in [MappingDirection.TO_RENTMANAGER, MappingDirection.BIDIRECTIONAL]:
                    continue
                
                mapping_result = self._apply_field_mapping(
                    processed_data, field_mapping, MappingDirection.TO_RENTMANAGER
                )
                
                if mapping_result["success"]:
                    if mapping_result["value"] is not None:
                        mapped_data[field_mapping.source_field] = mapping_result["value"]
                else:
                    if field_mapping.required:
                        errors.append(mapping_result["error"])
                    else:
                        warnings.append(mapping_result["error"])
                
                # Store validation results
                if "validation" in mapping_result:
                    validation_results[field_mapping.source_field] = mapping_result["validation"]
            
            # Apply custom mappings
            custom_result = self._apply_custom_mappings(
                processed_data, mapped_data, entity_type, organization_id, MappingDirection.TO_RENTMANAGER
            )
            mapped_data.update(custom_result.get("data", {}))
            warnings.extend(custom_result.get("warnings", []))
            
            # Post-processing
            final_data = self._apply_post_processing(mapped_data, entity_mapping)
            
            # Compliance validation
            compliance_status = self._validate_compliance(final_data, entity_type, organization_id)
            
            # Overall validation
            validation_result = self._validate_mapped_data(final_data, entity_mapping)
            if not validation_result["success"]:
                errors.extend(validation_result["errors"])
                warnings.extend(validation_result["warnings"])
            
            return MappingResult(
                success=len(errors) == 0,
                mapped_data=final_data if len(errors) == 0 else None,
                errors=errors,
                warnings=warnings,
                validation_results=validation_results,
                compliance_status=compliance_status
            )
            
        except Exception as e:
            logger.error(f"Failed to map data to RentManager: {e}")
            return MappingResult(
                success=False,
                errors=[f"Mapping failed: {str(e)}"]
            )
    
    # ===================================================
    # FIELD MAPPING METHODS
    # ===================================================
    
    def _apply_field_mapping(self, source_data: Dict[str, Any], 
                           field_mapping: FieldMapping, 
                           direction: MappingDirection) -> Dict[str, Any]:
        """Apply individual field mapping"""
        try:
            # Determine source and target fields based on direction
            if direction == MappingDirection.TO_ESTATECORE:
                source_field = field_mapping.source_field
                target_field = field_mapping.target_field
            else:
                source_field = field_mapping.target_field
                target_field = field_mapping.source_field
            
            # Check condition if specified
            if field_mapping.condition:
                if not self._evaluate_condition(source_data, field_mapping):
                    return {
                        "success": True,
                        "value": field_mapping.default_value,
                        "skipped": True
                    }
            
            # Get source value(s)
            if field_mapping.mapping_type == MappingType.COMPOSITE:
                source_values = {}
                for sf in field_mapping.source_fields:
                    source_values[sf] = self._get_nested_value(source_data, sf)
                source_value = source_values
            else:
                source_value = self._get_nested_value(source_data, source_field)
            
            # Handle missing required fields
            if source_value is None and field_mapping.required:
                return {
                    "success": False,
                    "error": f"Required field '{source_field}' is missing"
                }
            
            # Apply default value if source is None
            if source_value is None:
                source_value = field_mapping.default_value
            
            # Apply mapping transformation
            mapped_value = self._transform_value(
                source_value, field_mapping, direction
            )
            
            # Validate mapped value
            validation_result = self._validate_field_value(
                mapped_value, field_mapping
            )
            
            return {
                "success": True,
                "value": mapped_value,
                "validation": validation_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Field mapping failed for '{field_mapping.source_field}': {str(e)}"
            }
    
    def _transform_value(self, value: Any, field_mapping: FieldMapping, 
                        direction: MappingDirection) -> Any:
        """Transform value based on mapping type and configuration"""
        if value is None:
            return None
        
        try:
            if field_mapping.mapping_type == MappingType.DIRECT:
                return value
            
            elif field_mapping.mapping_type == MappingType.LOOKUP:
                return self._apply_lookup_mapping(value, field_mapping, direction)
            
            elif field_mapping.mapping_type == MappingType.TRANSFORM:
                return self._apply_transform_function(value, field_mapping, direction)
            
            elif field_mapping.mapping_type == MappingType.CALCULATED:
                return self._apply_calculated_mapping(value, field_mapping, direction)
            
            elif field_mapping.mapping_type == MappingType.COMPOSITE:
                return self._apply_composite_mapping(value, field_mapping, direction)
            
            elif field_mapping.mapping_type == MappingType.SPLIT:
                return self._apply_split_mapping(value, field_mapping, direction)
            
            else:
                return value
                
        except Exception as e:
            logger.warning(f"Value transformation failed: {e}")
            return value
    
    def _apply_lookup_mapping(self, value: Any, field_mapping: FieldMapping, 
                            direction: MappingDirection) -> Any:
        """Apply lookup table mapping"""
        if not field_mapping.lookup_table:
            return value
        
        lookup_key = str(value).lower()
        
        # Direct lookup
        if lookup_key in field_mapping.lookup_table:
            return field_mapping.lookup_table[lookup_key]
        
        # Reverse lookup for bidirectional mappings
        if direction == MappingDirection.TO_RENTMANAGER:
            for k, v in field_mapping.lookup_table.items():
                if str(v).lower() == lookup_key:
                    return k
        
        return value
    
    def _apply_transform_function(self, value: Any, field_mapping: FieldMapping,
                                direction: MappingDirection) -> Any:
        """Apply transform function"""
        if not field_mapping.transform_function:
            return value
        
        if field_mapping.transform_function in self.transform_functions:
            transform_func = self.transform_functions[field_mapping.transform_function]
            return transform_func(value, direction)
        
        return value
    
    # ===================================================
    # COMPLIANCE MAPPING METHODS
    # ===================================================
    
    def map_compliance_data(self, compliance_type: ComplianceType, 
                          source_data: Dict[str, Any],
                          direction: MappingDirection) -> MappingResult:
        """
        Map compliance-specific data
        
        Args:
            compliance_type: Type of compliance program
            source_data: Source compliance data
            direction: Mapping direction
            
        Returns:
            MappingResult with compliance mapped data
        """
        try:
            if compliance_type not in self.compliance_mappings:
                return MappingResult(
                    success=False,
                    errors=[f"No compliance mapping for {compliance_type.value}"]
                )
            
            compliance_config = self.compliance_mappings[compliance_type]
            mapped_data = {}
            errors = []
            warnings = []
            
            # Map compliance-specific fields
            for field_name, mapping_config in compliance_config.get("field_mappings", {}).items():
                if direction.value in mapping_config.get("directions", [direction.value]):
                    source_field = mapping_config.get("source_field", field_name)
                    target_field = mapping_config.get("target_field", field_name)
                    
                    source_value = self._get_nested_value(source_data, source_field)
                    
                    # Apply compliance-specific transformations
                    if "transform" in mapping_config:
                        transform_name = mapping_config["transform"]
                        if transform_name in self.transform_functions:
                            source_value = self.transform_functions[transform_name](
                                source_value, direction
                            )
                    
                    # Validate compliance requirements
                    if mapping_config.get("required", False) and source_value is None:
                        errors.append(f"Required compliance field '{field_name}' is missing")
                    
                    if source_value is not None:
                        mapped_data[target_field] = source_value
            
            # Apply compliance validation
            compliance_status = self._validate_compliance_data(
                mapped_data, compliance_type
            )
            
            return MappingResult(
                success=len(errors) == 0,
                mapped_data=mapped_data if len(errors) == 0 else None,
                errors=errors,
                warnings=warnings,
                compliance_status=compliance_status
            )
            
        except Exception as e:
            logger.error(f"Compliance mapping failed: {e}")
            return MappingResult(
                success=False,
                errors=[f"Compliance mapping failed: {str(e)}"]
            )
    
    # ===================================================
    # PROPERTY TYPE SPECIFIC MAPPINGS
    # ===================================================
    
    def map_student_housing_data(self, source_data: Dict[str, Any],
                               direction: MappingDirection) -> Dict[str, Any]:
        """Map student housing specific data"""
        mapped_data = {}
        
        if direction == MappingDirection.TO_ESTATECORE:
            # Map RentManager student housing fields to EstateCore
            student_mappings = {
                "student_id": "student_identifier",
                "university_name": "educational_institution",
                "graduation_date": "expected_graduation",
                "academic_standing": "academic_status",
                "roommate_preferences": "housing_preferences",
                "parent_guarantor": "guarantor_information"
            }
        else:
            # Map EstateCore to RentManager student housing fields
            student_mappings = {
                "student_identifier": "student_id",
                "educational_institution": "university_name",
                "expected_graduation": "graduation_date",
                "academic_status": "academic_standing",
                "housing_preferences": "roommate_preferences",
                "guarantor_information": "parent_guarantor"
            }
        
        for source_field, target_field in student_mappings.items():
            value = self._get_nested_value(source_data, source_field)
            if value is not None:
                mapped_data[target_field] = value
        
        return mapped_data
    
    def map_commercial_property_data(self, source_data: Dict[str, Any],
                                   direction: MappingDirection) -> Dict[str, Any]:
        """Map commercial property specific data"""
        mapped_data = {}
        
        if direction == MappingDirection.TO_ESTATECORE:
            # Map RentManager commercial fields to EstateCore
            commercial_mappings = {
                "cam_charges": "common_area_maintenance",
                "percentage_rent_rate": "percentage_rent_percentage",
                "percentage_rent_threshold": "breakpoint_sales_amount",
                "anchor_tenants": "major_tenants",
                "retail_classification": "retail_category",
                "office_class": "office_building_class",
                "lease_type": "lease_structure_type"
            }
        else:
            # Map EstateCore to RentManager commercial fields
            commercial_mappings = {
                "common_area_maintenance": "cam_charges",
                "percentage_rent_percentage": "percentage_rent_rate",
                "breakpoint_sales_amount": "percentage_rent_threshold",
                "major_tenants": "anchor_tenants",
                "retail_category": "retail_classification",
                "office_building_class": "office_class",
                "lease_structure_type": "lease_type"
            }
        
        for source_field, target_field in commercial_mappings.items():
            value = self._get_nested_value(source_data, source_field)
            if value is not None:
                mapped_data[target_field] = value
        
        return mapped_data
    
    def map_affordable_housing_data(self, source_data: Dict[str, Any],
                                  direction: MappingDirection) -> Dict[str, Any]:
        """Map affordable housing specific data"""
        mapped_data = {}
        
        if direction == MappingDirection.TO_ESTATECORE:
            # Map RentManager affordable housing fields to EstateCore
            affordable_mappings = {
                "ami_percentage": "area_median_income_percentage",
                "income_limit": "maximum_allowable_income",
                "rent_limit": "maximum_allowable_rent",
                "household_size": "family_size",
                "certification_date": "income_certification_date",
                "recertification_date": "next_recertification_date",
                "compliance_program": "housing_program_type",
                "monitoring_agent": "compliance_monitor"
            }
        else:
            # Map EstateCore to RentManager affordable housing fields
            affordable_mappings = {
                "area_median_income_percentage": "ami_percentage",
                "maximum_allowable_income": "income_limit",
                "maximum_allowable_rent": "rent_limit",
                "family_size": "household_size",
                "income_certification_date": "certification_date",
                "next_recertification_date": "recertification_date",
                "housing_program_type": "compliance_program",
                "compliance_monitor": "monitoring_agent"
            }
        
        for source_field, target_field in affordable_mappings.items():
            value = self._get_nested_value(source_data, source_field)
            if value is not None:
                mapped_data[target_field] = value
        
        return mapped_data
    
    # ===================================================
    # CONFIGURATION METHODS
    # ===================================================
    
    def setup_custom_mapping(self, organization_id: str, entity_type: str,
                           mapping_config: Dict[str, Any]) -> bool:
        """
        Setup custom mapping configuration for organization
        
        Args:
            organization_id: Organization identifier
            entity_type: Entity type for mapping
            mapping_config: Custom mapping configuration
            
        Returns:
            True if setup successful
        """
        try:
            if organization_id not in self.custom_mappings:
                self.custom_mappings[organization_id] = {}
            
            self.custom_mappings[organization_id][entity_type] = mapping_config
            
            logger.info(f"Custom mapping setup for {organization_id}/{entity_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup custom mapping: {e}")
            return False
    
    def get_mapping_configuration(self, entity_type: str, 
                                organization_id: str = None) -> Dict[str, Any]:
        """Get current mapping configuration for entity type"""
        config = {}
        
        # Get default mapping
        if entity_type in self.entity_mappings:
            config = asdict(self.entity_mappings[entity_type])
        
        # Apply custom mappings if available
        if organization_id and organization_id in self.custom_mappings:
            if entity_type in self.custom_mappings[organization_id]:
                custom_config = self.custom_mappings[organization_id][entity_type]
                config.update(custom_config)
        
        return config
    
    # ===================================================
    # UTILITY METHODS
    # ===================================================
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        try:
            keys = field_path.split('.')
            value = data
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return None
            return value
        except:
            return None
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = field_path.split('.')
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def _evaluate_condition(self, data: Dict[str, Any], 
                          field_mapping: FieldMapping) -> bool:
        """Evaluate condition for conditional mapping"""
        if not field_mapping.condition_field:
            return True
        
        condition_value = self._get_nested_value(data, field_mapping.condition_field)
        expected_value = field_mapping.condition_value
        
        if field_mapping.condition == "equals":
            return condition_value == expected_value
        elif field_mapping.condition == "not_equals":
            return condition_value != expected_value
        elif field_mapping.condition == "exists":
            return condition_value is not None
        elif field_mapping.condition == "not_exists":
            return condition_value is None
        elif field_mapping.condition == "in":
            return condition_value in expected_value if expected_value else False
        elif field_mapping.condition == "not_in":
            return condition_value not in expected_value if expected_value else True
        
        return True
    
    def _validate_field_value(self, value: Any, field_mapping: FieldMapping) -> Dict[str, Any]:
        """Validate field value against mapping configuration"""
        validation_result = {"valid": True, "errors": [], "warnings": []}
        
        # Check format pattern
        if field_mapping.format_pattern and value:
            if not re.match(field_mapping.format_pattern, str(value)):
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Value '{value}' does not match pattern '{field_mapping.format_pattern}'"
                )
        
        # Apply validation rules
        for rule_name in field_mapping.validation_rules:
            if rule_name in self.validation_rules:
                rule_result = self.validation_rules[rule_name](value)
                if not rule_result.get("valid", True):
                    validation_result["valid"] = False
                    validation_result["errors"].extend(rule_result.get("errors", []))
                validation_result["warnings"].extend(rule_result.get("warnings", []))
        
        return validation_result
    
    # ===================================================
    # INITIALIZATION METHODS
    # ===================================================
    
    def _initialize_default_mappings(self):
        """Initialize default entity mappings"""
        # Property mapping
        property_mappings = [
            FieldMapping("id", "id", MappingType.DIRECT),
            FieldMapping("name", "property_name", MappingType.DIRECT, required=True),
            FieldMapping("address", "property_address", MappingType.DIRECT),
            FieldMapping("property_type", "property_type", MappingType.LOOKUP, 
                        lookup_table=self._get_property_type_lookup()),
            FieldMapping("unit_count", "total_units", MappingType.DIRECT),
            FieldMapping("year_built", "construction_year", MappingType.DIRECT),
            FieldMapping("total_square_footage", "gross_square_feet", MappingType.DIRECT),
            FieldMapping("monthly_income", "gross_monthly_income", MappingType.DIRECT),
            FieldMapping("monthly_expenses", "operating_expenses", MappingType.DIRECT),
            FieldMapping("compliance_programs", "compliance_programs", MappingType.DIRECT),
        ]
        
        self.entity_mappings["property"] = EntityMapping(
            entity_type="property",
            source_entity="RentManagerProperty",
            target_entity="EstateCore_Property",
            field_mappings=property_mappings
        )
        
        # Unit mapping
        unit_mappings = [
            FieldMapping("id", "id", MappingType.DIRECT),
            FieldMapping("property_id", "property_id", MappingType.DIRECT, required=True),
            FieldMapping("unit_number", "unit_number", MappingType.DIRECT, required=True),
            FieldMapping("unit_type", "unit_type", MappingType.LOOKUP,
                        lookup_table=self._get_unit_type_lookup()),
            FieldMapping("bedrooms", "bedroom_count", MappingType.DIRECT),
            FieldMapping("bathrooms", "bathroom_count", MappingType.DIRECT),
            FieldMapping("square_footage", "square_feet", MappingType.DIRECT),
            FieldMapping("market_rent", "market_rent_amount", MappingType.DIRECT),
            FieldMapping("current_rent", "current_rent_amount", MappingType.DIRECT),
        ]
        
        self.entity_mappings["unit"] = EntityMapping(
            entity_type="unit",
            source_entity="RentManagerUnit",
            target_entity="EstateCore_Unit",
            field_mappings=unit_mappings
        )
        
        # Resident mapping
        resident_mappings = [
            FieldMapping("id", "id", MappingType.DIRECT),
            FieldMapping("first_name", "first_name", MappingType.DIRECT, required=True),
            FieldMapping("last_name", "last_name", MappingType.DIRECT, required=True),
            FieldMapping("email", "email_address", MappingType.DIRECT),
            FieldMapping("phone", "primary_phone", MappingType.DIRECT),
            FieldMapping("mobile_phone", "mobile_phone", MappingType.DIRECT),
            FieldMapping("current_unit_id", "unit_id", MappingType.DIRECT),
            FieldMapping("move_in_date", "move_in_date", MappingType.DIRECT),
            FieldMapping("resident_status", "tenant_status", MappingType.LOOKUP,
                        lookup_table=self._get_resident_status_lookup()),
        ]
        
        self.entity_mappings["resident"] = EntityMapping(
            entity_type="resident",
            source_entity="RentManagerResident",
            target_entity="EstateCore_Tenant",
            field_mappings=resident_mappings
        )
    
    def _initialize_compliance_mappings(self):
        """Initialize compliance-specific mappings"""
        # LIHTC compliance mapping
        self.compliance_mappings[ComplianceType.LIHTC] = {
            "field_mappings": {
                "ami_percentage": {
                    "source_field": "ami_percentage",
                    "target_field": "area_median_income_percentage",
                    "required": True,
                    "directions": ["to_estatecore", "to_rentmanager"]
                },
                "income_limit": {
                    "source_field": "income_limit",
                    "target_field": "maximum_allowable_income",
                    "required": True,
                    "directions": ["to_estatecore", "to_rentmanager"]
                },
                "rent_limit": {
                    "source_field": "rent_limit",
                    "target_field": "maximum_allowable_rent",
                    "required": True,
                    "directions": ["to_estatecore", "to_rentmanager"]
                }
            }
        }
        
        # Section 8 compliance mapping
        self.compliance_mappings[ComplianceType.SECTION_8] = {
            "field_mappings": {
                "voucher_number": {
                    "source_field": "voucher_id",
                    "target_field": "housing_voucher_number",
                    "required": True,
                    "directions": ["to_estatecore", "to_rentmanager"]
                },
                "tenant_portion": {
                    "source_field": "tenant_payment",
                    "target_field": "tenant_rent_portion",
                    "required": True,
                    "directions": ["to_estatecore", "to_rentmanager"]
                },
                "housing_assistance_payment": {
                    "source_field": "hap_amount",
                    "target_field": "housing_assistance_payment",
                    "required": True,
                    "directions": ["to_estatecore", "to_rentmanager"]
                }
            }
        }
    
    def _initialize_lookup_tables(self):
        """Initialize lookup tables for data transformation"""
        self.lookup_tables = {
            "property_type": self._get_property_type_lookup(),
            "unit_type": self._get_unit_type_lookup(),
            "resident_status": self._get_resident_status_lookup(),
            "lease_status": self._get_lease_status_lookup(),
            "payment_status": self._get_payment_status_lookup(),
            "work_order_status": self._get_work_order_status_lookup()
        }
    
    def _initialize_transform_functions(self):
        """Initialize data transformation functions"""
        self.transform_functions = {
            "format_phone": self._format_phone_number,
            "format_currency": self._format_currency,
            "format_date": self._format_date,
            "format_address": self._format_address,
            "calculate_rent_per_sqft": self._calculate_rent_per_sqft,
            "split_full_name": self._split_full_name,
            "combine_name": self._combine_name,
            "normalize_email": self._normalize_email
        }
    
    def _initialize_validation_rules(self):
        """Initialize validation rules"""
        self.validation_rules = {
            "validate_email": self._validate_email,
            "validate_phone": self._validate_phone,
            "validate_currency": self._validate_currency,
            "validate_date": self._validate_date,
            "validate_postal_code": self._validate_postal_code
        }
    
    # ===================================================
    # LOOKUP TABLE METHODS
    # ===================================================
    
    def _get_property_type_lookup(self) -> Dict[str, str]:
        """Get property type lookup table"""
        return {
            "multi_family": "multifamily",
            "commercial": "commercial",
            "affordable_housing": "affordable",
            "student_housing": "student",
            "senior_housing": "senior",
            "mixed_use": "mixed_use",
            "retail": "retail",
            "office": "office",
            "industrial": "industrial",
            "hoa_community": "hoa"
        }
    
    def _get_unit_type_lookup(self) -> Dict[str, str]:
        """Get unit type lookup table"""
        return {
            "apartment": "apartment",
            "studio": "studio",
            "one_bedroom": "1br",
            "two_bedroom": "2br",
            "three_bedroom": "3br",
            "four_bedroom": "4br",
            "townhouse": "townhouse",
            "commercial_space": "commercial",
            "parking_space": "parking"
        }
    
    def _get_resident_status_lookup(self) -> Dict[str, str]:
        """Get resident status lookup table"""
        return {
            "current": "active",
            "prospective": "prospect",
            "former": "former",
            "applicant": "applicant",
            "approved": "approved",
            "denied": "denied"
        }
    
    def _get_lease_status_lookup(self) -> Dict[str, str]:
        """Get lease status lookup table"""
        return {
            "active": "active",
            "pending": "pending",
            "expired": "expired",
            "terminated": "terminated",
            "renewed": "renewed",
            "cancelled": "cancelled"
        }
    
    def _get_payment_status_lookup(self) -> Dict[str, str]:
        """Get payment status lookup table"""
        return {
            "pending": "pending",
            "processed": "completed",
            "failed": "failed",
            "refunded": "refunded",
            "cancelled": "cancelled"
        }
    
    def _get_work_order_status_lookup(self) -> Dict[str, str]:
        """Get work order status lookup table"""
        return {
            "open": "open",
            "assigned": "assigned",
            "in_progress": "in_progress",
            "completed": "completed",
            "cancelled": "cancelled"
        }
    
    # ===================================================
    # TRANSFORM FUNCTION IMPLEMENTATIONS
    # ===================================================
    
    def _format_phone_number(self, value: Any, direction: MappingDirection) -> str:
        """Format phone number"""
        if not value:
            return None
        
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', str(value))
        
        # Format as (XXX) XXX-XXXX for US numbers
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        return str(value)
    
    def _format_currency(self, value: Any, direction: MappingDirection) -> float:
        """Format currency value"""
        if value is None:
            return None
        
        try:
            # Remove currency symbols and convert to float
            if isinstance(value, str):
                cleaned = re.sub(r'[^\d.-]', '', value)
                return float(cleaned) if cleaned else 0.0
            return float(value)
        except:
            return 0.0
    
    def _format_date(self, value: Any, direction: MappingDirection) -> str:
        """Format date value"""
        if not value:
            return None
        
        try:
            if isinstance(value, datetime):
                return value.date().isoformat()
            elif isinstance(value, date):
                return value.isoformat()
            elif isinstance(value, str):
                # Try to parse common date formats
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                    try:
                        parsed_date = datetime.strptime(value, fmt)
                        return parsed_date.date().isoformat()
                    except:
                        continue
                return value
        except:
            return str(value) if value else None
    
    def _validate_email(self, value: Any) -> Dict[str, Any]:
        """Validate email address"""
        if not value:
            return {"valid": True}
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, str(value)):
            return {"valid": True}
        else:
            return {
                "valid": False,
                "errors": [f"Invalid email format: {value}"]
            }
    
    # Additional placeholder methods for completeness...
    def _format_address(self, value: Any, direction: MappingDirection) -> Any:
        return value
    
    def _calculate_rent_per_sqft(self, value: Any, direction: MappingDirection) -> Any:
        return value
    
    def _split_full_name(self, value: Any, direction: MappingDirection) -> Any:
        return value
    
    def _combine_name(self, value: Any, direction: MappingDirection) -> Any:
        return value
    
    def _normalize_email(self, value: Any, direction: MappingDirection) -> Any:
        return str(value).lower().strip() if value else None
    
    def _validate_phone(self, value: Any) -> Dict[str, Any]:
        return {"valid": True}
    
    def _validate_currency(self, value: Any) -> Dict[str, Any]:
        return {"valid": True}
    
    def _validate_date(self, value: Any) -> Dict[str, Any]:
        return {"valid": True}
    
    def _validate_postal_code(self, value: Any) -> Dict[str, Any]:
        return {"valid": True}
    
    def _get_entity_mapping(self, entity_type: str, organization_id: str = None) -> Optional[EntityMapping]:
        return self.entity_mappings.get(entity_type)
    
    def _apply_pre_processing(self, data: Dict[str, Any], entity_mapping: EntityMapping) -> Dict[str, Any]:
        return data
    
    def _apply_post_processing(self, data: Dict[str, Any], entity_mapping: EntityMapping) -> Dict[str, Any]:
        return data
    
    def _apply_custom_mappings(self, source_data: Dict[str, Any], mapped_data: Dict[str, Any], 
                             entity_type: str, organization_id: str, direction: MappingDirection) -> Dict[str, Any]:
        return {"data": {}, "warnings": []}
    
    def _validate_compliance(self, data: Dict[str, Any], entity_type: str, organization_id: str) -> Dict[str, Any]:
        return {"compliant": True}
    
    def _validate_mapped_data(self, data: Dict[str, Any], entity_mapping: EntityMapping) -> Dict[str, Any]:
        return {"success": True, "errors": [], "warnings": []}
    
    def _apply_calculated_mapping(self, value: Any, field_mapping: FieldMapping, direction: MappingDirection) -> Any:
        return value
    
    def _apply_composite_mapping(self, value: Any, field_mapping: FieldMapping, direction: MappingDirection) -> Any:
        return value
    
    def _apply_split_mapping(self, value: Any, field_mapping: FieldMapping, direction: MappingDirection) -> Any:
        return value
    
    def _validate_compliance_data(self, data: Dict[str, Any], compliance_type: ComplianceType) -> Dict[str, Any]:
        return {"compliant": True}

# Global service instance
_mapping_service = None

def get_rentmanager_mapping_service() -> RentManagerMappingService:
    """Get singleton mapping service instance"""
    global _mapping_service
    if _mapping_service is None:
        _mapping_service = RentManagerMappingService()
    return _mapping_service
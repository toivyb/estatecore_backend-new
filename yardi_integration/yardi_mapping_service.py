"""
Yardi Data Mapping Service

Handles field mapping and data transformation between EstateCore and Yardi systems.
Supports complex transformations, business rules, and product-specific mappings.
"""

import os
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

from .models import YardiProductType, YardiEntityType

logger = logging.getLogger(__name__)

class TransformationType(Enum):
    """Data transformation types"""
    DIRECT_MAP = "direct_map"
    CALCULATED = "calculated"
    CONDITIONAL = "conditional"
    LOOKUP = "lookup"
    FORMAT = "format"
    SPLIT = "split"
    COMBINE = "combine"
    CUSTOM = "custom"

class DataType(Enum):
    """Supported data types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    ARRAY = "array"

@dataclass
class FieldMapping:
    """Individual field mapping configuration"""
    mapping_id: str
    source_field: str
    target_field: str
    transformation_type: TransformationType
    data_type: DataType
    required: bool = False
    default_value: Any = None
    transformation_config: Dict[str, Any] = field(default_factory=dict)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    business_rules: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class EntityMapping:
    """Complete entity mapping configuration"""
    entity_type: YardiEntityType
    yardi_product: YardiProductType
    organization_id: str
    field_mappings: List[FieldMapping] = field(default_factory=list)
    entity_rules: Dict[str, Any] = field(default_factory=dict)
    preprocessing_rules: List[Dict[str, Any]] = field(default_factory=list)
    postprocessing_rules: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

class YardiMappingService:
    """
    Yardi Data Mapping Service
    
    Provides comprehensive data mapping and transformation capabilities
    for bidirectional synchronization between EstateCore and Yardi systems.
    """
    
    def __init__(self):
        # Mapping storage
        self.entity_mappings: Dict[str, EntityMapping] = {}
        self.field_mappings: Dict[str, FieldMapping] = {}
        self.custom_transformers: Dict[str, Callable] = {}
        self.lookup_tables: Dict[str, Dict[str, Any]] = {}
        
        # Built-in transformers
        self._register_builtin_transformers()
        
        # Load default mappings
        self._load_default_mappings()
        
        logger.info("Yardi Mapping Service initialized")
    
    def _register_builtin_transformers(self):
        """Register built-in transformation functions"""
        self.custom_transformers.update({
            'format_phone': self._format_phone_number,
            'format_date': self._format_date,
            'normalize_name': self._normalize_name,
            'calculate_rent_period': self._calculate_rent_period,
            'split_address': self._split_address,
            'combine_name': self._combine_name,
            'currency_to_cents': self._currency_to_cents,
            'cents_to_currency': self._cents_to_currency,
            'boolean_to_yesno': self._boolean_to_yesno,
            'yesno_to_boolean': self._yesno_to_boolean
        })
    
    def _load_default_mappings(self):
        """Load default field mappings for different Yardi products"""
        # Load default mappings from configuration files or create programmatically
        pass
    
    # =====================================================
    # MAPPING CONFIGURATION
    # =====================================================
    
    def create_entity_mapping(self, organization_id: str, entity_type: YardiEntityType,
                            yardi_product: YardiProductType, 
                            field_mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create entity mapping configuration"""
        try:
            mapping_key = f"{organization_id}_{entity_type.value}_{yardi_product.value}"
            
            # Create field mapping objects
            field_mapping_objects = []
            for mapping_config in field_mappings:
                field_mapping = FieldMapping(
                    mapping_id=str(uuid.uuid4()),
                    source_field=mapping_config['source_field'],
                    target_field=mapping_config['target_field'],
                    transformation_type=TransformationType(mapping_config.get('transformation_type', 'direct_map')),
                    data_type=DataType(mapping_config.get('data_type', 'string')),
                    required=mapping_config.get('required', False),
                    default_value=mapping_config.get('default_value'),
                    transformation_config=mapping_config.get('transformation_config', {}),
                    validation_rules=mapping_config.get('validation_rules', {}),
                    business_rules=mapping_config.get('business_rules', {})
                )
                field_mapping_objects.append(field_mapping)
                self.field_mappings[field_mapping.mapping_id] = field_mapping
            
            # Create entity mapping
            entity_mapping = EntityMapping(
                entity_type=entity_type,
                yardi_product=yardi_product,
                organization_id=organization_id,
                field_mappings=field_mapping_objects
            )
            
            self.entity_mappings[mapping_key] = entity_mapping
            
            logger.info(f"Created entity mapping for {entity_type.value} in organization {organization_id}")
            
            return {
                "success": True,
                "mapping_key": mapping_key,
                "field_count": len(field_mapping_objects)
            }
            
        except Exception as e:
            logger.error(f"Failed to create entity mapping: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_entity_mapping(self, organization_id: str, entity_type: YardiEntityType,
                         yardi_product: YardiProductType) -> Optional[EntityMapping]:
        """Get entity mapping configuration"""
        mapping_key = f"{organization_id}_{entity_type.value}_{yardi_product.value}"
        return self.entity_mappings.get(mapping_key)
    
    def update_entity_mapping(self, organization_id: str, entity_type: YardiEntityType,
                            yardi_product: YardiProductType, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update entity mapping configuration"""
        try:
            mapping_key = f"{organization_id}_{entity_type.value}_{yardi_product.value}"
            entity_mapping = self.entity_mappings.get(mapping_key)
            
            if not entity_mapping:
                return {
                    "success": False,
                    "error": "Entity mapping not found"
                }
            
            # Update entity-level properties
            if 'entity_rules' in updates:
                entity_mapping.entity_rules.update(updates['entity_rules'])
            
            if 'preprocessing_rules' in updates:
                entity_mapping.preprocessing_rules = updates['preprocessing_rules']
            
            if 'postprocessing_rules' in updates:
                entity_mapping.postprocessing_rules = updates['postprocessing_rules']
            
            # Update field mappings
            if 'field_mappings' in updates:
                for field_update in updates['field_mappings']:
                    field_mapping = next(
                        (fm for fm in entity_mapping.field_mappings 
                         if fm.source_field == field_update.get('source_field')),
                        None
                    )
                    if field_mapping:
                        for key, value in field_update.items():
                            if hasattr(field_mapping, key):
                                setattr(field_mapping, key, value)
            
            entity_mapping.updated_at = datetime.utcnow()
            
            return {
                "success": True,
                "message": "Entity mapping updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to update entity mapping: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # =====================================================
    # DATA TRANSFORMATION
    # =====================================================
    
    def transform_to_yardi(self, organization_id: str, entity_type: YardiEntityType,
                         estatecore_data: Dict[str, Any], 
                         yardi_product: Optional[YardiProductType] = None) -> Dict[str, Any]:
        """Transform EstateCore data to Yardi format"""
        
        if not yardi_product:
            # Try to determine from organization connection
            yardi_product = self._get_organization_yardi_product(organization_id)
        
        # Get entity mapping
        entity_mapping = self.get_entity_mapping(organization_id, entity_type, yardi_product)
        if not entity_mapping:
            # Use default mapping
            entity_mapping = self._get_default_mapping(entity_type, yardi_product, "to_yardi")
        
        return self._transform_data(estatecore_data, entity_mapping, "to_yardi")
    
    def transform_to_estatecore(self, organization_id: str, entity_type: YardiEntityType,
                              yardi_data: Dict[str, Any],
                              yardi_product: Optional[YardiProductType] = None) -> Dict[str, Any]:
        """Transform Yardi data to EstateCore format"""
        
        if not yardi_product:
            yardi_product = self._get_organization_yardi_product(organization_id)
        
        # Get entity mapping
        entity_mapping = self.get_entity_mapping(organization_id, entity_type, yardi_product)
        if not entity_mapping:
            # Use default mapping
            entity_mapping = self._get_default_mapping(entity_type, yardi_product, "to_estatecore")
        
        return self._transform_data(yardi_data, entity_mapping, "to_estatecore")
    
    def _transform_data(self, source_data: Dict[str, Any], entity_mapping: EntityMapping,
                       direction: str) -> Dict[str, Any]:
        """Core data transformation logic"""
        
        try:
            # Apply preprocessing rules
            processed_data = self._apply_preprocessing_rules(source_data, entity_mapping)
            
            # Transform fields
            transformed_data = {}
            
            for field_mapping in entity_mapping.field_mappings:
                try:
                    # Determine source and target fields based on direction
                    if direction == "to_yardi":
                        source_field = field_mapping.source_field
                        target_field = field_mapping.target_field
                    else:
                        source_field = field_mapping.target_field
                        target_field = field_mapping.source_field
                    
                    # Get source value
                    source_value = self._get_nested_value(processed_data, source_field)
                    
                    # Apply transformation
                    transformed_value = self._apply_field_transformation(
                        source_value, field_mapping, direction
                    )
                    
                    # Set target value
                    if transformed_value is not None:
                        self._set_nested_value(transformed_data, target_field, transformed_value)
                    elif field_mapping.required and field_mapping.default_value is not None:
                        self._set_nested_value(transformed_data, target_field, field_mapping.default_value)
                        
                except Exception as e:
                    logger.error(f"Field transformation failed for {field_mapping.source_field}: {e}")
                    continue
            
            # Apply postprocessing rules
            final_data = self._apply_postprocessing_rules(transformed_data, entity_mapping)
            
            # Apply business rules
            validated_data = self._apply_business_rules(final_data, entity_mapping)
            
            return validated_data
            
        except Exception as e:
            logger.error(f"Data transformation failed: {e}")
            return source_data  # Return original data on failure
    
    def _apply_field_transformation(self, value: Any, field_mapping: FieldMapping,
                                  direction: str) -> Any:
        """Apply transformation to a single field"""
        
        if value is None:
            return field_mapping.default_value
        
        try:
            # Apply transformation based on type
            if field_mapping.transformation_type == TransformationType.DIRECT_MAP:
                return self._cast_to_type(value, field_mapping.data_type)
            
            elif field_mapping.transformation_type == TransformationType.CALCULATED:
                return self._apply_calculated_transformation(value, field_mapping)
            
            elif field_mapping.transformation_type == TransformationType.CONDITIONAL:
                return self._apply_conditional_transformation(value, field_mapping)
            
            elif field_mapping.transformation_type == TransformationType.LOOKUP:
                return self._apply_lookup_transformation(value, field_mapping)
            
            elif field_mapping.transformation_type == TransformationType.FORMAT:
                return self._apply_format_transformation(value, field_mapping)
            
            elif field_mapping.transformation_type == TransformationType.CUSTOM:
                return self._apply_custom_transformation(value, field_mapping, direction)
            
            else:
                return value
                
        except Exception as e:
            logger.error(f"Field transformation failed: {e}")
            return value
    
    # =====================================================
    # TRANSFORMATION IMPLEMENTATIONS
    # =====================================================
    
    def _apply_calculated_transformation(self, value: Any, field_mapping: FieldMapping) -> Any:
        """Apply calculated transformation"""
        formula = field_mapping.transformation_config.get('formula')
        if not formula:
            return value
        
        # Simple formula evaluation (would need more sophisticated parser for production)
        try:
            # Replace placeholders with actual values
            evaluated_formula = formula.replace('${value}', str(value))
            
            # Safe evaluation (very limited for security)
            if re.match(r'^[\d\+\-\*\/\.\(\)\s]+$', evaluated_formula):
                return eval(evaluated_formula)
            else:
                return value
        except:
            return value
    
    def _apply_conditional_transformation(self, value: Any, field_mapping: FieldMapping) -> Any:
        """Apply conditional transformation"""
        conditions = field_mapping.transformation_config.get('conditions', [])
        
        for condition in conditions:
            condition_field = condition.get('field')
            condition_operator = condition.get('operator')
            condition_value = condition.get('value')
            result_value = condition.get('result')
            
            # Evaluate condition (simplified)
            if condition_operator == 'equals' and value == condition_value:
                return result_value
            elif condition_operator == 'not_equals' and value != condition_value:
                return result_value
            elif condition_operator == 'contains' and str(condition_value) in str(value):
                return result_value
        
        return field_mapping.transformation_config.get('default', value)
    
    def _apply_lookup_transformation(self, value: Any, field_mapping: FieldMapping) -> Any:
        """Apply lookup transformation"""
        lookup_table_name = field_mapping.transformation_config.get('lookup_table')
        if not lookup_table_name or lookup_table_name not in self.lookup_tables:
            return value
        
        lookup_table = self.lookup_tables[lookup_table_name]
        return lookup_table.get(str(value), value)
    
    def _apply_format_transformation(self, value: Any, field_mapping: FieldMapping) -> Any:
        """Apply format transformation"""
        format_type = field_mapping.transformation_config.get('format_type')
        format_pattern = field_mapping.transformation_config.get('format_pattern')
        
        if format_type == 'date' and format_pattern:
            try:
                if isinstance(value, str):
                    parsed_date = datetime.fromisoformat(value.replace('Z', '+00:00'))
                else:
                    parsed_date = value
                return parsed_date.strftime(format_pattern)
            except:
                return value
        
        elif format_type == 'currency':
            try:
                amount = float(value)
                currency_symbol = field_mapping.transformation_config.get('currency_symbol', '$')
                decimals = field_mapping.transformation_config.get('decimals', 2)
                return f"{currency_symbol}{amount:.{decimals}f}"
            except:
                return value
        
        elif format_type == 'phone':
            return self._format_phone_number(value)
        
        return value
    
    def _apply_custom_transformation(self, value: Any, field_mapping: FieldMapping,
                                   direction: str) -> Any:
        """Apply custom transformation"""
        transformer_name = field_mapping.transformation_config.get('transformer')
        if transformer_name in self.custom_transformers:
            transformer = self.custom_transformers[transformer_name]
            return transformer(value, field_mapping.transformation_config)
        
        return value
    
    # =====================================================
    # BUILT-IN TRANSFORMERS
    # =====================================================
    
    def _format_phone_number(self, value: Any, config: Dict[str, Any] = None) -> str:
        """Format phone number"""
        if not value:
            return ""
        
        # Remove all non-digits
        digits = re.sub(r'[^\d]', '', str(value))
        
        # Format based on length
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return str(value)
    
    def _format_date(self, value: Any, config: Dict[str, Any] = None) -> str:
        """Format date"""
        format_pattern = config.get('format', '%Y-%m-%d') if config else '%Y-%m-%d'
        
        try:
            if isinstance(value, str):
                # Try to parse ISO format
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif isinstance(value, datetime):
                dt = value
            else:
                return str(value)
            
            return dt.strftime(format_pattern)
        except:
            return str(value)
    
    def _normalize_name(self, value: Any, config: Dict[str, Any] = None) -> str:
        """Normalize name (title case, trim, etc.)"""
        if not value:
            return ""
        
        name = str(value).strip()
        return ' '.join(word.capitalize() for word in name.split())
    
    def _calculate_rent_period(self, value: Any, config: Dict[str, Any] = None) -> float:
        """Calculate rent for different periods"""
        if not value:
            return 0.0
        
        try:
            monthly_rent = float(value)
            period = config.get('period', 'monthly') if config else 'monthly'
            
            if period == 'weekly':
                return monthly_rent / 4.33
            elif period == 'daily':
                return monthly_rent / 30.44
            elif period == 'yearly':
                return monthly_rent * 12
            else:
                return monthly_rent
        except:
            return 0.0
    
    def _split_address(self, value: Any, config: Dict[str, Any] = None) -> Dict[str, str]:
        """Split address into components"""
        if not value:
            return {}
        
        address = str(value).strip()
        
        # Simple address parsing (would need more sophisticated logic)
        parts = address.split(',')
        
        result = {}
        if len(parts) >= 1:
            result['street'] = parts[0].strip()
        if len(parts) >= 2:
            result['city'] = parts[1].strip()
        if len(parts) >= 3:
            state_zip = parts[2].strip().split()
            if len(state_zip) >= 1:
                result['state'] = state_zip[0]
            if len(state_zip) >= 2:
                result['zip'] = state_zip[1]
        
        return result
    
    def _combine_name(self, value: Any, config: Dict[str, Any] = None) -> str:
        """Combine name parts"""
        if not isinstance(value, dict):
            return str(value) if value else ""
        
        parts = []
        for field in ['first_name', 'middle_name', 'last_name']:
            if field in value and value[field]:
                parts.append(str(value[field]).strip())
        
        return ' '.join(parts)
    
    def _currency_to_cents(self, value: Any, config: Dict[str, Any] = None) -> int:
        """Convert currency to cents"""
        try:
            amount = float(str(value).replace('$', '').replace(',', ''))
            return int(amount * 100)
        except:
            return 0
    
    def _cents_to_currency(self, value: Any, config: Dict[str, Any] = None) -> float:
        """Convert cents to currency"""
        try:
            return float(value) / 100
        except:
            return 0.0
    
    def _boolean_to_yesno(self, value: Any, config: Dict[str, Any] = None) -> str:
        """Convert boolean to Yes/No"""
        if isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, str):
            return "Yes" if value.lower() in ['true', 'yes', '1'] else "No"
        else:
            return "No"
    
    def _yesno_to_boolean(self, value: Any, config: Dict[str, Any] = None) -> bool:
        """Convert Yes/No to boolean"""
        if isinstance(value, str):
            return value.lower() in ['yes', 'true', '1', 'y']
        elif isinstance(value, bool):
            return value
        else:
            return False
    
    # =====================================================
    # UTILITY METHODS
    # =====================================================
    
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
    
    def _set_nested_value(self, data: Dict[str, Any], field_path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = field_path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _cast_to_type(self, value: Any, data_type: DataType) -> Any:
        """Cast value to specified data type"""
        if value is None:
            return None
        
        try:
            if data_type == DataType.STRING:
                return str(value)
            elif data_type == DataType.INTEGER:
                return int(float(value))
            elif data_type == DataType.FLOAT:
                return float(value)
            elif data_type == DataType.BOOLEAN:
                if isinstance(value, bool):
                    return value
                elif isinstance(value, str):
                    return value.lower() in ['true', 'yes', '1', 'y']
                else:
                    return bool(value)
            elif data_type == DataType.DATE:
                if isinstance(value, datetime):
                    return value.date()
                elif isinstance(value, str):
                    return datetime.fromisoformat(value.replace('Z', '+00:00')).date()
            elif data_type == DataType.DATETIME:
                if isinstance(value, datetime):
                    return value
                elif isinstance(value, str):
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif data_type == DataType.JSON:
                if isinstance(value, str):
                    return json.loads(value)
                else:
                    return value
            elif data_type == DataType.ARRAY:
                if isinstance(value, list):
                    return value
                elif isinstance(value, str):
                    return [item.strip() for item in value.split(',')]
                else:
                    return [value]
            else:
                return value
        except:
            return value
    
    def _apply_preprocessing_rules(self, data: Dict[str, Any], 
                                 entity_mapping: EntityMapping) -> Dict[str, Any]:
        """Apply preprocessing rules to data"""
        processed_data = data.copy()
        
        for rule in entity_mapping.preprocessing_rules:
            rule_type = rule.get('type')
            
            if rule_type == 'trim_whitespace':
                for key, value in processed_data.items():
                    if isinstance(value, str):
                        processed_data[key] = value.strip()
            
            elif rule_type == 'normalize_case':
                case_type = rule.get('case', 'lower')
                fields = rule.get('fields', [])
                
                for field in fields:
                    if field in processed_data and isinstance(processed_data[field], str):
                        if case_type == 'lower':
                            processed_data[field] = processed_data[field].lower()
                        elif case_type == 'upper':
                            processed_data[field] = processed_data[field].upper()
                        elif case_type == 'title':
                            processed_data[field] = processed_data[field].title()
            
            elif rule_type == 'remove_empty':
                processed_data = {k: v for k, v in processed_data.items() 
                                if v is not None and str(v).strip() != ''}
        
        return processed_data
    
    def _apply_postprocessing_rules(self, data: Dict[str, Any],
                                  entity_mapping: EntityMapping) -> Dict[str, Any]:
        """Apply postprocessing rules to data"""
        processed_data = data.copy()
        
        for rule in entity_mapping.postprocessing_rules:
            rule_type = rule.get('type')
            
            if rule_type == 'add_metadata':
                metadata = rule.get('metadata', {})
                processed_data.update(metadata)
            
            elif rule_type == 'calculate_fields':
                calculations = rule.get('calculations', [])
                for calc in calculations:
                    target_field = calc.get('target_field')
                    formula = calc.get('formula')
                    if target_field and formula:
                        # Simple calculation (would need expression parser for production)
                        try:
                            result = eval(formula, {"__builtins__": {}}, processed_data)
                            processed_data[target_field] = result
                        except:
                            pass
        
        return processed_data
    
    def _apply_business_rules(self, data: Dict[str, Any],
                            entity_mapping: EntityMapping) -> Dict[str, Any]:
        """Apply business rules validation and transformation"""
        validated_data = data.copy()
        
        business_rules = entity_mapping.entity_rules.get('business_rules', [])
        
        for rule in business_rules:
            rule_type = rule.get('type')
            
            if rule_type == 'validate_required':
                required_fields = rule.get('fields', [])
                for field in required_fields:
                    if field not in validated_data or not validated_data[field]:
                        logger.warning(f"Required field '{field}' is missing or empty")
            
            elif rule_type == 'set_defaults':
                defaults = rule.get('defaults', {})
                for field, default_value in defaults.items():
                    if field not in validated_data or not validated_data[field]:
                        validated_data[field] = default_value
        
        return validated_data
    
    # =====================================================
    # DEFAULT MAPPINGS
    # =====================================================
    
    def setup_voyager_default_mappings(self, organization_id: str):
        """Setup default mappings for Yardi Voyager"""
        
        # Properties mapping
        property_mappings = [
            {
                'source_field': 'name',
                'target_field': 'PropertyName',
                'transformation_type': 'direct_map',
                'data_type': 'string',
                'required': True
            },
            {
                'source_field': 'address.street',
                'target_field': 'PropertyAddress',
                'transformation_type': 'direct_map',
                'data_type': 'string'
            },
            {
                'source_field': 'property_manager.name',
                'target_field': 'PropertyManager',
                'transformation_type': 'direct_map',
                'data_type': 'string'
            }
        ]
        
        self.create_entity_mapping(
            organization_id=organization_id,
            entity_type=YardiEntityType.PROPERTIES,
            yardi_product=YardiProductType.VOYAGER,
            field_mappings=property_mappings
        )
        
        # Units mapping
        unit_mappings = [
            {
                'source_field': 'unit_number',
                'target_field': 'UnitNumber',
                'transformation_type': 'direct_map',
                'data_type': 'string',
                'required': True
            },
            {
                'source_field': 'rent_amount',
                'target_field': 'MarketRent',
                'transformation_type': 'direct_map',
                'data_type': 'float'
            },
            {
                'source_field': 'status',
                'target_field': 'UnitStatus',
                'transformation_type': 'lookup',
                'data_type': 'string'
            }
        ]
        
        self.create_entity_mapping(
            organization_id=organization_id,
            entity_type=YardiEntityType.UNITS,
            yardi_product=YardiProductType.VOYAGER,
            field_mappings=unit_mappings
        )
        
        logger.info(f"Setup Voyager default mappings for organization {organization_id}")
    
    def setup_breeze_default_mappings(self, organization_id: str):
        """Setup default mappings for Yardi Breeze"""
        
        # Properties mapping for Breeze
        property_mappings = [
            {
                'source_field': 'name',
                'target_field': 'property_name',
                'transformation_type': 'direct_map',
                'data_type': 'string',
                'required': True
            },
            {
                'source_field': 'address',
                'target_field': 'property_address',
                'transformation_type': 'direct_map',
                'data_type': 'string'
            }
        ]
        
        self.create_entity_mapping(
            organization_id=organization_id,
            entity_type=YardiEntityType.PROPERTIES,
            yardi_product=YardiProductType.BREEZE,
            field_mappings=property_mappings
        )
        
        logger.info(f"Setup Breeze default mappings for organization {organization_id}")
    
    def _get_default_mapping(self, entity_type: YardiEntityType, 
                           yardi_product: YardiProductType, direction: str) -> EntityMapping:
        """Get default mapping configuration"""
        
        # Create minimal default mapping
        default_mappings = []
        
        if entity_type == YardiEntityType.PROPERTIES:
            default_mappings = [
                FieldMapping(
                    mapping_id=str(uuid.uuid4()),
                    source_field='name',
                    target_field='PropertyName' if yardi_product == YardiProductType.VOYAGER else 'property_name',
                    transformation_type=TransformationType.DIRECT_MAP,
                    data_type=DataType.STRING
                )
            ]
        elif entity_type == YardiEntityType.TENANTS:
            default_mappings = [
                FieldMapping(
                    mapping_id=str(uuid.uuid4()),
                    source_field='name',
                    target_field='ResidentName' if yardi_product == YardiProductType.VOYAGER else 'resident_name',
                    transformation_type=TransformationType.DIRECT_MAP,
                    data_type=DataType.STRING
                )
            ]
        
        return EntityMapping(
            entity_type=entity_type,
            yardi_product=yardi_product,
            organization_id='default',
            field_mappings=default_mappings
        )
    
    def _get_organization_yardi_product(self, organization_id: str) -> YardiProductType:
        """Get Yardi product type for organization"""
        # This would query the organization's connection configuration
        # For now, default to Voyager
        return YardiProductType.VOYAGER
    
    # Lookup table management
    
    def create_lookup_table(self, table_name: str, mappings: Dict[str, Any]):
        """Create lookup table for value mappings"""
        self.lookup_tables[table_name] = mappings
        logger.info(f"Created lookup table '{table_name}' with {len(mappings)} mappings")
    
    def get_lookup_tables(self) -> List[str]:
        """Get list of available lookup tables"""
        return list(self.lookup_tables.keys())
    
    def register_custom_transformer(self, name: str, transformer_func: Callable):
        """Register custom transformation function"""
        self.custom_transformers[name] = transformer_func
        logger.info(f"Registered custom transformer '{name}'")
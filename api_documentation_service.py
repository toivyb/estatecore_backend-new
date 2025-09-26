"""
API Documentation and Developer Experience Service for EstateCore API Gateway
Auto-generated OpenAPI documentation, interactive API explorer, SDK generation, and sandbox environment
"""

import os
import json
import yaml
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import re
from collections import defaultdict
import jinja2
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParameterType(Enum):
    """Parameter types for API documentation"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"

class ParameterLocation(Enum):
    """Parameter locations"""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    BODY = "body"
    FORM = "formData"

class SecuritySchemeType(Enum):
    """Security scheme types"""
    API_KEY = "apiKey"
    HTTP = "http"
    OAUTH2 = "oauth2"
    OPEN_ID_CONNECT = "openIdConnect"

@dataclass
class APIParameter:
    """API parameter definition"""
    name: str
    param_type: ParameterType
    location: ParameterLocation
    description: str
    required: bool = False
    default_value: Any = None
    enum_values: List[Any] = field(default_factory=list)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    example: Any = None

@dataclass
class APIResponse:
    """API response definition"""
    status_code: int
    description: str
    schema: Dict[str, Any] = field(default_factory=dict)
    examples: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)

@dataclass
class APIEndpointDoc:
    """API endpoint documentation"""
    path: str
    method: str
    summary: str
    description: str
    tags: List[str] = field(default_factory=list)
    parameters: List[APIParameter] = field(default_factory=list)
    responses: List[APIResponse] = field(default_factory=list)
    security: List[Dict[str, List[str]]] = field(default_factory=list)
    deprecated: bool = False
    examples: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Optional[str] = None
    scopes: List[str] = field(default_factory=list)

@dataclass
class APITag:
    """API tag for grouping endpoints"""
    name: str
    description: str
    external_docs: Optional[Dict[str, str]] = None

@dataclass
class SecurityScheme:
    """Security scheme definition"""
    name: str
    scheme_type: SecuritySchemeType
    description: str
    api_key_name: Optional[str] = None
    api_key_location: Optional[str] = None
    bearer_format: Optional[str] = None
    oauth2_flows: Dict[str, Any] = field(default_factory=dict)
    scopes: Dict[str, str] = field(default_factory=dict)

@dataclass
class APIInfo:
    """API information"""
    title: str
    version: str
    description: str
    terms_of_service: Optional[str] = None
    contact: Dict[str, str] = field(default_factory=dict)
    license: Dict[str, str] = field(default_factory=dict)

@dataclass
class CodeExample:
    """Code example for SDK generation"""
    language: str
    label: str
    source: str
    description: Optional[str] = None

class OpenAPIGenerator:
    """OpenAPI 3.0 specification generator"""
    
    def __init__(self, api_info: APIInfo):
        self.api_info = api_info
        self.endpoints: List[APIEndpointDoc] = []
        self.tags: List[APITag] = []
        self.security_schemes: List[SecurityScheme] = []
        self.components = {
            'schemas': {},
            'responses': {},
            'parameters': {},
            'examples': {},
            'requestBodies': {},
            'headers': {},
            'securitySchemes': {},
            'links': {},
            'callbacks': {}
        }
    
    def add_endpoint(self, endpoint: APIEndpointDoc):
        """Add endpoint documentation"""
        self.endpoints.append(endpoint)
    
    def add_tag(self, tag: APITag):
        """Add API tag"""
        self.tags.append(tag)
    
    def add_security_scheme(self, scheme: SecurityScheme):
        """Add security scheme"""
        self.security_schemes.append(scheme)
        
        # Add to components
        if scheme.scheme_type == SecuritySchemeType.API_KEY:
            self.components['securitySchemes'][scheme.name] = {
                'type': 'apiKey',
                'name': scheme.api_key_name,
                'in': scheme.api_key_location,
                'description': scheme.description
            }
        elif scheme.scheme_type == SecuritySchemeType.HTTP:
            self.components['securitySchemes'][scheme.name] = {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': scheme.bearer_format or 'JWT',
                'description': scheme.description
            }
        elif scheme.scheme_type == SecuritySchemeType.OAUTH2:
            self.components['securitySchemes'][scheme.name] = {
                'type': 'oauth2',
                'description': scheme.description,
                'flows': scheme.oauth2_flows
            }
    
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add component schema"""
        self.components['schemas'][name] = schema
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate complete OpenAPI 3.0 specification"""
        spec = {
            'openapi': '3.0.3',
            'info': {
                'title': self.api_info.title,
                'version': self.api_info.version,
                'description': self.api_info.description
            },
            'servers': [
                {
                    'url': os.environ.get('API_BASE_URL', 'https://api.estatecore.com'),
                    'description': 'Production server'
                },
                {
                    'url': os.environ.get('API_SANDBOX_URL', 'https://sandbox-api.estatecore.com'),
                    'description': 'Sandbox server'
                }
            ],
            'paths': {},
            'components': self.components,
            'tags': []
        }
        
        # Add contact and license if provided
        if self.api_info.contact:
            spec['info']['contact'] = self.api_info.contact
        
        if self.api_info.license:
            spec['info']['license'] = self.api_info.license
        
        if self.api_info.terms_of_service:
            spec['info']['termsOfService'] = self.api_info.terms_of_service
        
        # Add tags
        for tag in self.tags:
            tag_spec = {
                'name': tag.name,
                'description': tag.description
            }
            if tag.external_docs:
                tag_spec['externalDocs'] = tag.external_docs
            spec['tags'].append(tag_spec)
        
        # Group endpoints by path
        paths = defaultdict(dict)
        for endpoint in self.endpoints:
            path_spec = self._generate_path_spec(endpoint)
            paths[endpoint.path][endpoint.method.lower()] = path_spec
        
        spec['paths'] = dict(paths)
        
        return spec
    
    def _generate_path_spec(self, endpoint: APIEndpointDoc) -> Dict[str, Any]:
        """Generate path specification for endpoint"""
        path_spec = {
            'summary': endpoint.summary,
            'description': endpoint.description,
            'tags': endpoint.tags,
            'parameters': [],
            'responses': {}
        }
        
        # Add deprecation notice
        if endpoint.deprecated:
            path_spec['deprecated'] = True
        
        # Add parameters
        for param in endpoint.parameters:
            param_spec = {
                'name': param.name,
                'in': param.location.value,
                'description': param.description,
                'required': param.required,
                'schema': {
                    'type': param.param_type.value
                }
            }
            
            # Add constraints
            if param.enum_values:
                param_spec['schema']['enum'] = param.enum_values
            
            if param.min_value is not None:
                param_spec['schema']['minimum'] = param.min_value
            
            if param.max_value is not None:
                param_spec['schema']['maximum'] = param.max_value
            
            if param.min_length is not None:
                param_spec['schema']['minLength'] = param.min_length
            
            if param.max_length is not None:
                param_spec['schema']['maxLength'] = param.max_length
            
            if param.pattern:
                param_spec['schema']['pattern'] = param.pattern
            
            if param.default_value is not None:
                param_spec['schema']['default'] = param.default_value
            
            if param.example is not None:
                param_spec['example'] = param.example
            
            path_spec['parameters'].append(param_spec)
        
        # Add responses
        for response in endpoint.responses:
            response_spec = {
                'description': response.description
            }
            
            if response.schema:
                response_spec['content'] = {
                    'application/json': {
                        'schema': response.schema
                    }
                }
                
                if response.examples:
                    response_spec['content']['application/json']['examples'] = response.examples
            
            if response.headers:
                response_spec['headers'] = response.headers
            
            path_spec['responses'][str(response.status_code)] = response_spec
        
        # Add security
        if endpoint.security:
            path_spec['security'] = endpoint.security
        
        # Add rate limit info
        if endpoint.rate_limit:
            if 'x-rate-limit' not in path_spec:
                path_spec['x-rate-limit'] = endpoint.rate_limit
        
        # Add required scopes
        if endpoint.scopes:
            path_spec['x-required-scopes'] = endpoint.scopes
        
        # Add code examples
        if endpoint.examples:
            path_spec['x-code-examples'] = endpoint.examples
        
        return path_spec

class CodeSampleGenerator:
    """Generate code samples for different programming languages"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates" / "code_samples"
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate_samples(self, endpoint: APIEndpointDoc, base_url: str) -> List[CodeExample]:
        """Generate code samples for an endpoint"""
        samples = []
        
        # Prepare template context
        context = {
            'endpoint': endpoint,
            'base_url': base_url,
            'method': endpoint.method.upper(),
            'path': endpoint.path,
            'has_body': any(p.location == ParameterLocation.BODY for p in endpoint.parameters),
            'query_params': [p for p in endpoint.parameters if p.location == ParameterLocation.QUERY],
            'path_params': [p for p in endpoint.parameters if p.location == ParameterLocation.PATH],
            'header_params': [p for p in endpoint.parameters if p.location == ParameterLocation.HEADER],
            'body_params': [p for p in endpoint.parameters if p.location == ParameterLocation.BODY]
        }
        
        # Language templates
        languages = ['python', 'javascript', 'java', 'csharp', 'php', 'go', 'ruby', 'curl']
        
        for lang in languages:
            try:
                template = self.jinja_env.get_template(f"{lang}.j2")
                code = template.render(**context)
                
                samples.append(CodeExample(
                    language=lang,
                    label=self._get_language_label(lang),
                    source=code,
                    description=f"{self._get_language_label(lang)} example for {endpoint.summary}"
                ))
            except jinja2.TemplateNotFound:
                logger.warning(f"Template not found for language: {lang}")
            except Exception as e:
                logger.error(f"Failed to generate {lang} sample: {str(e)}")
        
        return samples
    
    def _get_language_label(self, lang: str) -> str:
        """Get display label for programming language"""
        labels = {
            'python': 'Python',
            'javascript': 'JavaScript',
            'java': 'Java',
            'csharp': 'C#',
            'php': 'PHP',
            'go': 'Go',
            'ruby': 'Ruby',
            'curl': 'cURL'
        }
        return labels.get(lang, lang.title())

class SDKGenerator:
    """Generate SDK for different programming languages"""
    
    def __init__(self, openapi_spec: Dict[str, Any]):
        self.spec = openapi_spec
        self.templates_dir = Path(__file__).parent / "templates" / "sdks"
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate_python_sdk(self) -> Dict[str, str]:
        """Generate Python SDK"""
        return self._generate_sdk('python', {
            'package_name': 'estatecore_api',
            'class_name': 'EstateCoreAPI',
            'version': self.spec['info']['version']
        })
    
    def generate_javascript_sdk(self) -> Dict[str, str]:
        """Generate JavaScript SDK"""
        return self._generate_sdk('javascript', {
            'package_name': 'estatecore-api',
            'class_name': 'EstateCoreAPI',
            'version': self.spec['info']['version']
        })
    
    def generate_java_sdk(self) -> Dict[str, str]:
        """Generate Java SDK"""
        return self._generate_sdk('java', {
            'package_name': 'com.estatecore.api',
            'class_name': 'EstateCoreAPI',
            'version': self.spec['info']['version']
        })
    
    def _generate_sdk(self, language: str, config: Dict[str, str]) -> Dict[str, str]:
        """Generate SDK for specified language"""
        files = {}
        
        try:
            # Get all template files for the language
            lang_templates_dir = self.templates_dir / language
            if not lang_templates_dir.exists():
                return files
            
            context = {
                'spec': self.spec,
                'config': config,
                'endpoints': self._extract_endpoints(),
                'models': self._extract_models(),
                'security_schemes': self.spec.get('components', {}).get('securitySchemes', {})
            }
            
            for template_file in lang_templates_dir.rglob("*.j2"):
                template_path = str(template_file.relative_to(lang_templates_dir))
                output_path = template_path.replace('.j2', '')
                
                template = self.jinja_env.get_template(f"{language}/{template_path}")
                content = template.render(**context)
                
                files[output_path] = content
            
        except Exception as e:
            logger.error(f"Failed to generate {language} SDK: {str(e)}")
        
        return files
    
    def _extract_endpoints(self) -> List[Dict[str, Any]]:
        """Extract endpoints from OpenAPI spec"""
        endpoints = []
        
        for path, methods in self.spec.get('paths', {}).items():
            for method, spec in methods.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    endpoint = {
                        'path': path,
                        'method': method.upper(),
                        'operation_id': spec.get('operationId', f"{method}_{path.replace('/', '_').replace('{', '').replace('}', '')}"),
                        'summary': spec.get('summary', ''),
                        'description': spec.get('description', ''),
                        'parameters': spec.get('parameters', []),
                        'responses': spec.get('responses', {}),
                        'tags': spec.get('tags', [])
                    }
                    endpoints.append(endpoint)
        
        return endpoints
    
    def _extract_models(self) -> Dict[str, Any]:
        """Extract data models from OpenAPI spec"""
        return self.spec.get('components', {}).get('schemas', {})

class APIExplorerGenerator:
    """Generate interactive API explorer (Swagger UI)"""
    
    def __init__(self):
        self.templates_dir = Path(__file__).parent / "templates" / "explorer"
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate_explorer_html(self, openapi_spec: Dict[str, Any], 
                              custom_config: Optional[Dict[str, Any]] = None) -> str:
        """Generate HTML for API explorer"""
        
        config = {
            'title': openapi_spec['info']['title'],
            'spec_url': '/api/docs/openapi.json',
            'theme': 'light',
            'layout': 'StandaloneLayout',
            'deep_linking': True,
            'show_extensions': True,
            'show_common_extensions': True,
            'swagger_ui_bundle_js': 'https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js',
            'swagger_ui_standalone_preset_js': 'https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js',
            'swagger_ui_css': 'https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css'
        }
        
        if custom_config:
            config.update(custom_config)
        
        try:
            template = self.jinja_env.get_template('swagger_ui.html.j2')
            return template.render(
                config=config,
                spec=openapi_spec,
                spec_json=json.dumps(openapi_spec, indent=2)
            )
        except Exception as e:
            logger.error(f"Failed to generate API explorer: {str(e)}")
            return ""

class SandboxEnvironment:
    """Sandbox environment for API testing"""
    
    def __init__(self):
        self.sandbox_data = {}
        self.sandbox_clients = {}
        self.mock_responses = {}
    
    def create_sandbox_client(self, client_name: str, scopes: List[str]) -> Dict[str, str]:
        """Create sandbox API client"""
        client_id = f"sandbox_{uuid.uuid4().hex[:16]}"
        api_key = f"sandbox_{uuid.uuid4().hex}"
        
        self.sandbox_clients[client_id] = {
            'client_id': client_id,
            'api_key': api_key,
            'name': client_name,
            'scopes': scopes,
            'created_at': datetime.utcnow().isoformat(),
            'is_sandbox': True
        }
        
        return {
            'client_id': client_id,
            'api_key': api_key
        }
    
    def add_mock_response(self, endpoint: str, method: str, 
                         response_data: Dict[str, Any]):
        """Add mock response for sandbox testing"""
        key = f"{method.upper()}:{endpoint}"
        self.mock_responses[key] = response_data
    
    def get_mock_response(self, endpoint: str, method: str) -> Optional[Dict[str, Any]]:
        """Get mock response for endpoint"""
        key = f"{method.upper()}:{endpoint}"
        return self.mock_responses.get(key)
    
    def populate_sample_data(self):
        """Populate sandbox with sample data"""
        # Sample properties
        self.sandbox_data['properties'] = [
            {
                'id': '1',
                'name': 'Sunset Apartments',
                'address': '123 Main St, City, State 12345',
                'units': 50,
                'type': 'apartment',
                'status': 'active'
            },
            {
                'id': '2',
                'name': 'Downtown Condos',
                'address': '456 Oak Ave, City, State 12345',
                'units': 25,
                'type': 'condo',
                'status': 'active'
            }
        ]
        
        # Sample tenants
        self.sandbox_data['tenants'] = [
            {
                'id': '1',
                'name': 'John Doe',
                'email': 'john.doe@example.com',
                'phone': '555-1234',
                'property_id': '1',
                'unit': 'A101',
                'lease_start': '2024-01-01',
                'lease_end': '2024-12-31'
            },
            {
                'id': '2',
                'name': 'Jane Smith',
                'email': 'jane.smith@example.com',
                'phone': '555-5678',
                'property_id': '2',
                'unit': 'B201',
                'lease_start': '2024-02-01',
                'lease_end': '2025-01-31'
            }
        ]
        
        # Add mock responses
        self.add_mock_response('/api/v1/properties', 'GET', {
            'data': self.sandbox_data['properties'],
            'total': len(self.sandbox_data['properties']),
            'page': 1,
            'per_page': 10
        })
        
        self.add_mock_response('/api/v1/tenants', 'GET', {
            'data': self.sandbox_data['tenants'],
            'total': len(self.sandbox_data['tenants']),
            'page': 1,
            'per_page': 10
        })

class APIDocumentationService:
    """Main API documentation service"""
    
    def __init__(self):
        self.openapi_generator = OpenAPIGenerator(
            APIInfo(
                title="EstateCore API",
                version="1.0.0",
                description="Comprehensive property management API",
                contact={
                    'name': 'EstateCore Support',
                    'url': 'https://estatecore.com/support',
                    'email': 'support@estatecore.com'
                },
                license={
                    'name': 'MIT',
                    'url': 'https://opensource.org/licenses/MIT'
                }
            )
        )
        
        self.code_generator = CodeSampleGenerator()
        self.explorer_generator = APIExplorerGenerator()
        self.sandbox = SandboxEnvironment()
        
        # Initialize default documentation
        self._initialize_default_docs()
        
        # Populate sandbox
        self.sandbox.populate_sample_data()
    
    def _initialize_default_docs(self):
        """Initialize default API documentation"""
        
        # Add tags
        tags = [
            APITag("Authentication", "Authentication and authorization endpoints"),
            APITag("Properties", "Property management endpoints"),
            APITag("Tenants", "Tenant management endpoints"),
            APITag("Payments", "Payment processing endpoints"),
            APITag("Maintenance", "Maintenance request endpoints"),
            APITag("Analytics", "Analytics and reporting endpoints")
        ]
        
        for tag in tags:
            self.openapi_generator.add_tag(tag)
        
        # Add security schemes
        security_schemes = [
            SecurityScheme(
                name="ApiKeyAuth",
                scheme_type=SecuritySchemeType.API_KEY,
                description="API key authentication",
                api_key_name="X-API-Key",
                api_key_location="header"
            ),
            SecurityScheme(
                name="BearerAuth",
                scheme_type=SecuritySchemeType.HTTP,
                description="JWT Bearer token authentication",
                bearer_format="JWT"
            ),
            SecurityScheme(
                name="OAuth2",
                scheme_type=SecuritySchemeType.OAUTH2,
                description="OAuth 2.0 authentication",
                oauth2_flows={
                    "authorizationCode": {
                        "authorizationUrl": "https://api.estatecore.com/oauth/authorize",
                        "tokenUrl": "https://api.estatecore.com/oauth/token",
                        "scopes": {
                            "read": "Read access to resources",
                            "write": "Write access to resources",
                            "admin": "Administrative access"
                        }
                    }
                }
            )
        ]
        
        for scheme in security_schemes:
            self.openapi_generator.add_security_scheme(scheme)
        
        # Add common schemas
        schemas = {
            "Error": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer"},
                            "message": {"type": "string"},
                            "request_id": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        },
                        "required": ["code", "message", "request_id", "timestamp"]
                    }
                }
            },
            "PaginationMeta": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "per_page": {"type": "integer"},
                    "total": {"type": "integer"},
                    "total_pages": {"type": "integer"}
                }
            },
            "Property": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "address": {"type": "string"},
                    "units": {"type": "integer"},
                    "type": {"type": "string", "enum": ["apartment", "house", "condo", "commercial"]},
                    "status": {"type": "string", "enum": ["active", "inactive", "maintenance"]}
                },
                "required": ["id", "name", "address", "units", "type", "status"]
            },
            "Tenant": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string"},
                    "property_id": {"type": "string"},
                    "unit": {"type": "string"},
                    "lease_start": {"type": "string", "format": "date"},
                    "lease_end": {"type": "string", "format": "date"}
                },
                "required": ["id", "name", "email", "property_id", "unit"]
            }
        }
        
        for name, schema in schemas.items():
            self.openapi_generator.add_schema(name, schema)
        
        # Add sample endpoints
        self._add_sample_endpoints()
    
    def _add_sample_endpoints(self):
        """Add sample endpoint documentation"""
        
        # Properties endpoints
        properties_list = APIEndpointDoc(
            path="/api/v1/properties",
            method="GET",
            summary="List properties",
            description="Retrieve a list of properties with optional filtering and pagination",
            tags=["Properties"],
            parameters=[
                APIParameter("page", ParameterType.INTEGER, ParameterLocation.QUERY, 
                           "Page number for pagination", default_value=1, example=1),
                APIParameter("per_page", ParameterType.INTEGER, ParameterLocation.QUERY,
                           "Number of items per page", default_value=10, example=10),
                APIParameter("type", ParameterType.STRING, ParameterLocation.QUERY,
                           "Filter by property type", enum_values=["apartment", "house", "condo", "commercial"]),
                APIParameter("status", ParameterType.STRING, ParameterLocation.QUERY,
                           "Filter by property status", enum_values=["active", "inactive", "maintenance"])
            ],
            responses=[
                APIResponse(200, "Successful response", {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Property"}
                        },
                        "meta": {"$ref": "#/components/schemas/PaginationMeta"}
                    }
                }),
                APIResponse(400, "Bad request", {"$ref": "#/components/schemas/Error"}),
                APIResponse(401, "Unauthorized", {"$ref": "#/components/schemas/Error"}),
                APIResponse(403, "Forbidden", {"$ref": "#/components/schemas/Error"})
            ],
            security=[{"ApiKeyAuth": []}, {"BearerAuth": []}],
            rate_limit="100 requests per minute",
            scopes=["read", "properties:read"]
        )
        
        self.openapi_generator.add_endpoint(properties_list)
        
        # Tenants endpoints
        tenants_list = APIEndpointDoc(
            path="/api/v1/tenants",
            method="GET",
            summary="List tenants",
            description="Retrieve a list of tenants with optional filtering and pagination",
            tags=["Tenants"],
            parameters=[
                APIParameter("page", ParameterType.INTEGER, ParameterLocation.QUERY, 
                           "Page number for pagination", default_value=1),
                APIParameter("per_page", ParameterType.INTEGER, ParameterLocation.QUERY,
                           "Number of items per page", default_value=10),
                APIParameter("property_id", ParameterType.STRING, ParameterLocation.QUERY,
                           "Filter by property ID")
            ],
            responses=[
                APIResponse(200, "Successful response", {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/Tenant"}
                        },
                        "meta": {"$ref": "#/components/schemas/PaginationMeta"}
                    }
                }),
                APIResponse(401, "Unauthorized", {"$ref": "#/components/schemas/Error"}),
                APIResponse(403, "Forbidden", {"$ref": "#/components/schemas/Error"})
            ],
            security=[{"ApiKeyAuth": []}, {"BearerAuth": []}],
            scopes=["read", "tenants:read"]
        )
        
        self.openapi_generator.add_endpoint(tenants_list)
    
    def generate_documentation(self) -> Dict[str, Any]:
        """Generate complete API documentation"""
        return self.openapi_generator.generate_openapi_spec()
    
    def generate_code_samples(self, endpoint_path: str, method: str) -> List[CodeExample]:
        """Generate code samples for specific endpoint"""
        for endpoint in self.openapi_generator.endpoints:
            if endpoint.path == endpoint_path and endpoint.method.upper() == method.upper():
                return self.code_generator.generate_samples(
                    endpoint, 
                    os.environ.get('API_BASE_URL', 'https://api.estatecore.com')
                )
        return []
    
    def generate_sdk(self, language: str) -> Dict[str, str]:
        """Generate SDK for specified language"""
        openapi_spec = self.generate_documentation()
        sdk_generator = SDKGenerator(openapi_spec)
        
        if language == 'python':
            return sdk_generator.generate_python_sdk()
        elif language == 'javascript':
            return sdk_generator.generate_javascript_sdk()
        elif language == 'java':
            return sdk_generator.generate_java_sdk()
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def generate_api_explorer(self) -> str:
        """Generate interactive API explorer HTML"""
        openapi_spec = self.generate_documentation()
        return self.explorer_generator.generate_explorer_html(openapi_spec)
    
    def get_sandbox_client(self, client_name: str, scopes: List[str]) -> Dict[str, str]:
        """Create sandbox API client"""
        return self.sandbox.create_sandbox_client(client_name, scopes)
    
    def get_sandbox_response(self, endpoint: str, method: str) -> Optional[Dict[str, Any]]:
        """Get sandbox mock response"""
        return self.sandbox.get_mock_response(endpoint, method)

# Global documentation service instance
_documentation_service = None

def get_documentation_service() -> APIDocumentationService:
    """Get or create the API documentation service instance"""
    global _documentation_service
    if _documentation_service is None:
        _documentation_service = APIDocumentationService()
    return _documentation_service
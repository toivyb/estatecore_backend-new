"""
White-Label Multi-Tenant Integration Module
Integrates all white-label components with the existing EstateCore application.
"""
import os
from flask import Flask
from typing import Dict, Any

def setup_white_label_system(app: Flask, config: Dict[str, Any] = None) -> None:
    """
    Setup complete white-label multi-tenant system integration.
    
    Args:
        app: Flask application instance
        config: Optional configuration dictionary
    """
    # Default configuration
    default_config = {
        'tenant_middleware': {
            'require_tenant_for_api': True,
            'require_tenant_for_frontend': False,
            'allowed_no_tenant_paths': [
                '/health',
                '/api/health',
                '/api/system',
                '/admin',
                '/static',
                '/favicon.ico'
            ]
        },
        'branding': {
            'cdn_url': os.environ.get('CDN_URL', ''),
            'bucket_name': os.environ.get('BRANDING_BUCKET', 'estatecore-branding')
        },
        'sso': {
            'private_key_path': os.environ.get('SSO_PRIVATE_KEY'),
            'public_key_path': os.environ.get('SSO_PUBLIC_KEY')
        },
        'monitoring': {
            'buffer_size': 1000,
            'flush_interval': 60
        }
    }
    
    # Merge configuration
    if config:
        default_config.update(config)
    
    # Store config in app
    app.config['WHITE_LABEL'] = default_config
    
    # 1. Setup Database Models
    _setup_database_models(app)
    
    # 2. Setup Tenant Middleware
    _setup_tenant_middleware(app, default_config['tenant_middleware'])
    
    # 3. Register API Routes
    _register_api_routes(app)
    
    # 4. Setup Template Functions
    _setup_template_functions(app)
    
    # 5. Initialize Services
    _initialize_services(app, default_config)
    
    # 6. Setup Error Handlers
    _setup_error_handlers(app)
    
    app.logger.info("White-label multi-tenant system initialized successfully")

def _setup_database_models(app: Flask) -> None:
    """Setup database models and relationships."""
    with app.app_context():
        try:
            # Import models to register them
            from models.white_label_tenant import (
                WhiteLabelTenant, Partner, TenantDomain, 
                TenantUsageLog, TenantConfiguration
            )
            
            # Create tables if they don't exist
            from models.white_label_tenant import db
            db.create_all()
            
            app.logger.info("White-label database models initialized")
        except Exception as e:
            app.logger.error(f"Error setting up database models: {str(e)}")

def _setup_tenant_middleware(app: Flask, config: Dict[str, Any]) -> None:
    """Setup tenant resolution middleware."""
    try:
        from middleware.tenant_middleware import setup_tenant_middleware
        setup_tenant_middleware(app, config)
        app.logger.info("Tenant middleware initialized")
    except Exception as e:
        app.logger.error(f"Error setting up tenant middleware: {str(e)}")

def _register_api_routes(app: Flask) -> None:
    """Register white-label API routes."""
    try:
        from routes.white_label_api import white_label_bp
        app.register_blueprint(white_label_bp)
        
        # Register SSO routes
        _register_sso_routes(app)
        
        app.logger.info("White-label API routes registered")
    except Exception as e:
        app.logger.error(f"Error registering API routes: {str(e)}")

def _register_sso_routes(app: Flask) -> None:
    """Register SSO authentication routes."""
    from flask import Blueprint, request, redirect, url_for, session, jsonify
    from services.sso_service import get_sso_service, SSOProvider
    from services.tenant_context import get_current_tenant_context
    
    sso_bp = Blueprint('sso', __name__, url_prefix='/sso')
    
    @sso_bp.route('/login/<provider>')
    def sso_login(provider):
        """Initiate SSO login."""
        try:
            context = get_current_tenant_context()
            if not context or not context.tenant:
                return jsonify({"error": "Tenant context required"}), 400
            
            provider_type = SSOProvider(provider)
            return_url = request.args.get('return_url')
            
            sso_service = get_sso_service()
            success, message, auth_url = sso_service.initiate_sso_login(
                context.tenant_id, provider_type, return_url
            )
            
            if success:
                return redirect(auth_url)
            else:
                return jsonify({"error": message}), 400
                
        except Exception as e:
            app.logger.error(f"SSO login error: {str(e)}")
            return jsonify({"error": "SSO login failed"}), 500
    
    @sso_bp.route('/callback/<provider>')
    def sso_callback(provider):
        """Handle SSO authentication callback."""
        try:
            context = get_current_tenant_context()
            if not context or not context.tenant:
                return jsonify({"error": "Tenant context required"}), 400
            
            provider_type = SSOProvider(provider)
            callback_data = dict(request.args)
            
            sso_service = get_sso_service()
            success, message, user_info = sso_service.handle_sso_callback(
                context.tenant_id, provider_type, callback_data
            )
            
            if success:
                # Redirect to application with user info
                return_url = session.get('return_url', url_for('dashboard'))
                return redirect(return_url)
            else:
                return jsonify({"error": message}), 400
                
        except Exception as e:
            app.logger.error(f"SSO callback error: {str(e)}")
            return jsonify({"error": "SSO authentication failed"}), 500
    
    app.register_blueprint(sso_bp)

def _setup_template_functions(app: Flask) -> None:
    """Setup template functions for white-label features."""
    try:
        # Register tenant context template functions
        from services.tenant_context import register_tenant_template_functions
        register_tenant_template_functions(app)
        
        # Register feature flag template functions
        from services.feature_flags import register_template_functions
        register_template_functions(app)
        
        # Add custom template functions
        @app.template_global()
        def tenant_theme_css():
            """Generate tenant-specific CSS URL."""
            from services.tenant_context import get_current_tenant_context
            context = get_current_tenant_context()
            if context and context.tenant:
                return url_for('white_label.get_tenant_theme_css', tenant_id=context.tenant_id)
            return None
        
        @app.template_global()
        def tenant_logo_url():
            """Get tenant logo URL."""
            from services.tenant_context import get_current_tenant_context
            context = get_current_tenant_context()
            if context:
                return context.get_brand_setting('logo.primary', '/static/assets/logo.png')
            return '/static/assets/logo.png'
        
        @app.template_global()
        def tenant_name():
            """Get tenant display name."""
            from services.tenant_context import get_current_tenant_context
            context = get_current_tenant_context()
            if context:
                return context.get_brand_setting('name', 'EstateCore')
            return 'EstateCore'
        
        app.logger.info("Template functions registered")
    except Exception as e:
        app.logger.error(f"Error setting up template functions: {str(e)}")

def _initialize_services(app: Flask, config: Dict[str, Any]) -> None:
    """Initialize white-label services."""
    try:
        # Initialize monitoring service
        from services.tenant_monitoring import get_tenant_monitoring_service
        monitoring_service = get_tenant_monitoring_service()
        
        # Initialize feature flag service
        from services.feature_flags import get_feature_flag_service
        feature_service = get_feature_flag_service()
        
        # Initialize branding service
        from services.branding_service import get_branding_service
        branding_service = get_branding_service()
        
        # Initialize tenant management service
        from services.tenant_management import get_tenant_management_service
        management_service = get_tenant_management_service()
        
        # Initialize SSO service
        from services.sso_service import get_sso_service
        sso_service = get_sso_service()
        
        app.logger.info("White-label services initialized")
    except Exception as e:
        app.logger.error(f"Error initializing services: {str(e)}")

def _setup_error_handlers(app: Flask) -> None:
    """Setup error handlers for white-label operations."""
    @app.errorhandler(400)
    def handle_bad_request(error):
        from flask import jsonify
        return jsonify({
            "error": "Bad Request",
            "message": str(error.description) if error.description else "Invalid request"
        }), 400
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        from flask import jsonify
        return jsonify({
            "error": "Forbidden",
            "message": str(error.description) if error.description else "Access denied"
        }), 403

def create_sample_partner_and_tenant(app: Flask) -> Dict[str, Any]:
    """
    Create sample partner and tenant for testing.
    This should only be used in development/testing environments.
    """
    if not app.debug:
        app.logger.warning("Sample partner creation skipped in production mode")
        return {}
    
    try:
        from models.white_label_tenant import Partner, WhiteLabelTenant, db
        from models.organization import Organization, PlanType
        import secrets
        
        with app.app_context():
            # Check if sample partner already exists
            partner = Partner.query.filter_by(name="Sample Partner").first()
            if not partner:
                # Create sample partner
                api_key = secrets.token_urlsafe(32)
                partner = Partner(
                    name="Sample Partner",
                    contact_email="partner@example.com",
                    contact_person="John Partner",
                    phone="+1-555-PARTNER",
                    api_key=api_key,
                    webhook_url="https://webhook.example.com/estatecore",
                    default_revenue_share=15.0,
                    billing_model="revenue_share"
                )
                db.session.add(partner)
                db.session.flush()
            
            # Check if sample tenant already exists
            tenant = WhiteLabelTenant.query.filter_by(tenant_key="demo").first()
            if not tenant:
                # Create sample organization
                organization = Organization(
                    name="Demo Property Management",
                    contact_email="demo@example.com",
                    phone="+1-555-DEMO",
                    plan_type=PlanType.PROFESSIONAL,
                    max_properties=100,
                    max_units=1000,
                    max_users=50,
                    has_ai_features=True,
                    has_lpr_access=True,
                    has_video_inspection=True,
                    has_advanced_reporting=True
                )
                db.session.add(organization)
                db.session.flush()
                
                # Create sample tenant
                tenant = WhiteLabelTenant(
                    organization_id=organization.id,
                    partner_id=partner.id,
                    tenant_key="demo",
                    display_name="Demo Property Management",
                    subdomain="demo",
                    status="active",
                    brand_config={
                        "name": "Demo Properties",
                        "tagline": "Professional Property Management Demo",
                        "colors": {
                            "primary": "#007bff",
                            "secondary": "#6c757d"
                        },
                        "logo": {
                            "primary": "/static/assets/demo-logo.png"
                        }
                    },
                    feature_flags={
                        "ai_analytics": True,
                        "advanced_reporting": True,
                        "api_access": True,
                        "custom_branding": True
                    },
                    resource_quotas={
                        "api_calls_monthly": 50000,
                        "storage_gb": 25,
                        "users": 50,
                        "properties": 100,
                        "units": 1000
                    },
                    technical_contact_email="tech@demo.example.com",
                    billing_contact_email="billing@demo.example.com"
                )
                db.session.add(tenant)
            
            db.session.commit()
            
            app.logger.info("Sample partner and tenant created successfully")
            return {
                "partner_api_key": partner.api_key,
                "tenant_key": tenant.tenant_key,
                "tenant_subdomain": f"{tenant.subdomain}.estatecore.com"
            }
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating sample partner and tenant: {str(e)}")
        return {}

def migrate_existing_organizations(app: Flask) -> None:
    """
    Migrate existing organizations to white-label tenants.
    This is for upgrading existing EstateCore installations.
    """
    try:
        from models.organization import Organization
        from models.white_label_tenant import WhiteLabelTenant, Partner, db
        import secrets
        
        with app.app_context():
            # Get or create default partner
            default_partner = Partner.query.filter_by(name="EstateCore Default").first()
            if not default_partner:
                default_partner = Partner(
                    name="EstateCore Default",
                    contact_email="admin@estatecore.com",
                    api_key=secrets.token_urlsafe(32),
                    default_revenue_share=0.0,
                    billing_model="direct"
                )
                db.session.add(default_partner)
                db.session.flush()
            
            # Migrate organizations without white-label tenants
            organizations = Organization.query.filter(
                ~Organization.id.in_(
                    db.session.query(WhiteLabelTenant.organization_id)
                )
            ).all()
            
            for org in organizations:
                # Generate tenant key from organization name
                tenant_key = org.name.lower().replace(' ', '').replace('-', '')[:20]
                
                # Ensure uniqueness
                counter = 1
                original_key = tenant_key
                while WhiteLabelTenant.query.filter_by(tenant_key=tenant_key).first():
                    tenant_key = f"{original_key}{counter}"
                    counter += 1
                
                # Create white-label tenant
                tenant = WhiteLabelTenant(
                    organization_id=org.id,
                    partner_id=default_partner.id,
                    tenant_key=tenant_key,
                    display_name=org.name,
                    subdomain=tenant_key,
                    status="active",
                    brand_config={
                        "name": org.name,
                        "colors": {
                            "primary": "#007bff",
                            "secondary": "#6c757d"
                        }
                    },
                    feature_flags={
                        "ai_analytics": org.has_ai_features,
                        "lpr_integration": org.has_lpr_access,
                        "video_inspection": org.has_video_inspection,
                        "advanced_reporting": org.has_advanced_reporting
                    },
                    resource_quotas={
                        "properties": org.max_properties,
                        "units": org.max_units,
                        "users": org.max_users,
                        "api_calls_monthly": 10000,
                        "storage_gb": 10
                    }
                )
                db.session.add(tenant)
            
            db.session.commit()
            app.logger.info(f"Migrated {len(organizations)} organizations to white-label tenants")
            
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error migrating organizations: {str(e)}")

# Utility functions for integration testing
def test_white_label_system(app: Flask) -> Dict[str, Any]:
    """
    Test the white-label system integration.
    Returns test results and system status.
    """
    results = {
        "overall_status": "unknown",
        "components": {},
        "errors": []
    }
    
    try:
        with app.app_context():
            # Test database models
            try:
                from models.white_label_tenant import WhiteLabelTenant
                tenant_count = WhiteLabelTenant.query.count()
                results["components"]["database"] = {
                    "status": "ok",
                    "tenant_count": tenant_count
                }
            except Exception as e:
                results["components"]["database"] = {"status": "error", "error": str(e)}
                results["errors"].append(f"Database: {str(e)}")
            
            # Test services
            services = [
                ("tenant_monitoring", "services.tenant_monitoring", "get_tenant_monitoring_service"),
                ("feature_flags", "services.feature_flags", "get_feature_flag_service"),
                ("branding", "services.branding_service", "get_branding_service"),
                ("tenant_management", "services.tenant_management", "get_tenant_management_service"),
                ("sso", "services.sso_service", "get_sso_service")
            ]
            
            for service_name, module_name, function_name in services:
                try:
                    module = __import__(module_name, fromlist=[function_name])
                    service_func = getattr(module, function_name)
                    service = service_func()
                    results["components"][service_name] = {"status": "ok"}
                except Exception as e:
                    results["components"][service_name] = {"status": "error", "error": str(e)}
                    results["errors"].append(f"{service_name}: {str(e)}")
            
            # Overall status
            if results["errors"]:
                results["overall_status"] = "degraded" if len(results["errors"]) < 3 else "error"
            else:
                results["overall_status"] = "ok"
                
    except Exception as e:
        results["overall_status"] = "error"
        results["errors"].append(f"System test failed: {str(e)}")
    
    return results
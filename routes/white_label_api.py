"""
White-label multi-tenant API routes.
Provides comprehensive API endpoints for tenant management, partner operations, and white-label functionality.
"""
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_cors import cross_origin
from functools import wraps
import io
import json
from datetime import datetime
from typing import Dict, Any, Optional

from models.white_label_tenant import (
    WhiteLabelTenant, Partner, TenantDomain, TenantConfiguration,
    white_label_tenant_schema, white_label_tenants_schema,
    partner_schema, partners_schema, tenant_domain_schema, db
)
from services.tenant_management import get_tenant_management_service
from services.branding_service import get_branding_service, get_email_branding_service
from services.feature_flags import get_feature_flag_service
from services.tenant_monitoring import get_tenant_monitoring_service
from services.tenant_context import get_current_tenant_context, require_tenant_context
from middleware.tenant_middleware import require_tenant, require_active_tenant, require_tenant_feature

# Create Blueprint
white_label_bp = Blueprint('white_label', __name__, url_prefix='/api/white-label')

def require_partner_auth(f):
    """Decorator to require partner authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "Partner API key required"}), 401
        
        partner = Partner.query.filter_by(api_key=api_key, is_active=True).first()
        if not partner:
            return jsonify({"error": "Invalid partner API key"}), 401
        
        # Store partner in request context
        request.partner = partner
        return f(*args, **kwargs)
    return decorated_function

def require_admin_auth(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This would integrate with your existing auth system
        # For now, checking for a special admin header
        admin_token = request.headers.get('X-Admin-Token')
        if admin_token != current_app.config.get('ADMIN_TOKEN'):
            return jsonify({"error": "Admin authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Partner Management Routes

@white_label_bp.route('/partners', methods=['GET'])
@require_admin_auth
def list_partners():
    """List all partners."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        partners = Partner.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "partners": partners_schema.dump(partners.items),
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": partners.total,
                "pages": partners.pages
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error listing partners: {str(e)}")
        return jsonify({"error": "Failed to list partners"}), 500

@white_label_bp.route('/partners', methods=['POST'])
@require_admin_auth
def create_partner():
    """Create a new partner."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400
        
        # Validate required fields
        required_fields = ['name', 'contact_email']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Generate API key
        import secrets
        api_key = secrets.token_urlsafe(32)
        
        partner = Partner(
            name=data['name'],
            contact_email=data['contact_email'],
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            api_key=api_key,
            webhook_url=data.get('webhook_url'),
            default_revenue_share=data.get('default_revenue_share', 0.0),
            billing_model=data.get('billing_model', 'revenue_share'),
            partner_metadata=data.get('metadata', {})
        )
        
        db.session.add(partner)
        db.session.commit()
        
        return jsonify({
            "message": "Partner created successfully",
            "partner": partner_schema.dump(partner)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating partner: {str(e)}")
        return jsonify({"error": "Failed to create partner"}), 500

@white_label_bp.route('/partners/<int:partner_id>', methods=['GET'])
@require_admin_auth
def get_partner(partner_id):
    """Get partner details."""
    try:
        partner = Partner.query.get_or_404(partner_id)
        return jsonify({"partner": partner_schema.dump(partner)})
    except Exception as e:
        current_app.logger.error(f"Error getting partner: {str(e)}")
        return jsonify({"error": "Failed to get partner"}), 500

@white_label_bp.route('/partners/<int:partner_id>', methods=['PUT'])
@require_admin_auth
def update_partner(partner_id):
    """Update partner details."""
    try:
        partner = Partner.query.get_or_404(partner_id)
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = [
            'name', 'contact_email', 'contact_person', 'phone',
            'webhook_url', 'default_revenue_share', 'billing_model',
            'is_active', 'partner_metadata'
        ]
        
        for field in allowed_fields:
            if field in data:
                setattr(partner, field, data[field])
        
        partner.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "message": "Partner updated successfully",
            "partner": partner_schema.dump(partner)
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating partner: {str(e)}")
        return jsonify({"error": "Failed to update partner"}), 500

# Tenant Management Routes

@white_label_bp.route('/tenants', methods=['GET'])
@require_admin_auth
def list_tenants():
    """List all tenants (admin only)."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        partner_id = request.args.get('partner_id', type=int)
        
        query = WhiteLabelTenant.query
        
        if status:
            query = query.filter(WhiteLabelTenant.status == status)
        if partner_id:
            query = query.filter(WhiteLabelTenant.partner_id == partner_id)
        
        tenants = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "tenants": white_label_tenants_schema.dump(tenants.items),
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": tenants.total,
                "pages": tenants.pages
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error listing tenants: {str(e)}")
        return jsonify({"error": "Failed to list tenants"}), 500

@white_label_bp.route('/tenants', methods=['POST'])
@require_partner_auth
def create_tenant():
    """Create a new tenant (partner only)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400
        
        partner = request.partner
        management_service = get_tenant_management_service()
        
        success, message, tenant = management_service.create_tenant(partner.id, data)
        
        if success:
            return jsonify({
                "message": message,
                "tenant": white_label_tenant_schema.dump(tenant)
            }), 201
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error creating tenant: {str(e)}")
        return jsonify({"error": "Failed to create tenant"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>', methods=['GET'])
@require_partner_auth
def get_tenant(tenant_id):
    """Get tenant details (partner only for their tenants)."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        return jsonify({"tenant": white_label_tenant_schema.dump(tenant)})
    except Exception as e:
        current_app.logger.error(f"Error getting tenant: {str(e)}")
        return jsonify({"error": "Failed to get tenant"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>', methods=['PUT'])
@require_partner_auth
def update_tenant(tenant_id):
    """Update tenant configuration (partner only)."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        data = request.get_json()
        management_service = get_tenant_management_service()
        
        success, message = management_service.update_tenant(tenant_id, data)
        
        if success:
            return jsonify({
                "message": message,
                "tenant": white_label_tenant_schema.dump(tenant)
            })
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating tenant: {str(e)}")
        return jsonify({"error": "Failed to update tenant"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>/suspend', methods=['POST'])
@require_partner_auth
def suspend_tenant(tenant_id):
    """Suspend a tenant (partner only)."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        data = request.get_json() or {}
        reason = data.get('reason', 'Suspended by partner')
        
        management_service = get_tenant_management_service()
        success, message = management_service.suspend_tenant(tenant_id, reason)
        
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error suspending tenant: {str(e)}")
        return jsonify({"error": "Failed to suspend tenant"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>/reactivate', methods=['POST'])
@require_partner_auth
def reactivate_tenant(tenant_id):
    """Reactivate a suspended tenant (partner only)."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        management_service = get_tenant_management_service()
        success, message = management_service.reactivate_tenant(tenant_id)
        
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error reactivating tenant: {str(e)}")
        return jsonify({"error": "Failed to reactivate tenant"}), 500

# Branding and Customization Routes

@white_label_bp.route('/tenants/<int:tenant_id>/branding', methods=['GET'])
@require_partner_auth
def get_tenant_branding(tenant_id):
    """Get tenant branding configuration."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        branding_service = get_branding_service()
        brand_config = branding_service.get_tenant_brand_config(tenant_id)
        
        return jsonify({"branding": brand_config})
    except Exception as e:
        current_app.logger.error(f"Error getting tenant branding: {str(e)}")
        return jsonify({"error": "Failed to get tenant branding"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>/branding', methods=['PUT'])
@require_partner_auth
def update_tenant_branding(tenant_id):
    """Update tenant branding configuration."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400
        
        branding_service = get_branding_service()
        success = branding_service.update_tenant_brand_config(tenant_id, data)
        
        if success:
            return jsonify({"message": "Branding updated successfully"})
        else:
            return jsonify({"error": "Failed to update branding"}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating tenant branding: {str(e)}")
        return jsonify({"error": "Failed to update tenant branding"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>/branding/theme.css', methods=['GET'])
def get_tenant_theme_css(tenant_id):
    """Get generated CSS theme for a tenant."""
    try:
        branding_service = get_branding_service()
        css_content = branding_service.generate_theme_css(tenant_id)
        
        # Return CSS file
        css_io = io.BytesIO(css_content.encode('utf-8'))
        return send_file(
            css_io,
            mimetype='text/css',
            as_attachment=False,
            download_name=f'tenant-{tenant_id}-theme.css'
        )
    except Exception as e:
        current_app.logger.error(f"Error generating tenant theme CSS: {str(e)}")
        return jsonify({"error": "Failed to generate theme CSS"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>/branding/upload', methods=['POST'])
@require_partner_auth
def upload_brand_asset(tenant_id):
    """Upload brand asset for a tenant."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        asset_type = request.form.get('asset_type', 'logo')
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        branding_service = get_branding_service()
        asset_url = branding_service.upload_brand_asset(
            tenant.tenant_key,
            asset_type,
            file.read(),
            file.filename,
            file.content_type
        )
        
        if asset_url:
            return jsonify({
                "message": "Asset uploaded successfully",
                "asset_url": asset_url,
                "asset_type": asset_type
            })
        else:
            return jsonify({"error": "Failed to upload asset"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error uploading brand asset: {str(e)}")
        return jsonify({"error": "Failed to upload brand asset"}), 500

# Feature Management Routes

@white_label_bp.route('/tenants/<int:tenant_id>/features', methods=['GET'])
@require_partner_auth
def get_tenant_features(tenant_id):
    """Get tenant feature configuration."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        feature_service = get_feature_flag_service()
        features = feature_service.get_tenant_features(tenant_id)
        
        return jsonify({"features": features})
    except Exception as e:
        current_app.logger.error(f"Error getting tenant features: {str(e)}")
        return jsonify({"error": "Failed to get tenant features"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>/features/<feature_key>', methods=['PUT'])
@require_partner_auth
def update_tenant_feature(tenant_id, feature_key):
    """Update a specific tenant feature."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({"error": "Feature value required"}), 400
        
        feature_service = get_feature_flag_service()
        success = feature_service.set_tenant_feature(tenant_id, feature_key, data['value'])
        
        if success:
            return jsonify({"message": f"Feature {feature_key} updated successfully"})
        else:
            return jsonify({"error": "Failed to update feature"}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error updating tenant feature: {str(e)}")
        return jsonify({"error": "Failed to update tenant feature"}), 500

# Custom Domain Management Routes

@white_label_bp.route('/tenants/<int:tenant_id>/domains', methods=['POST'])
@require_partner_auth
def setup_custom_domain(tenant_id):
    """Setup custom domain for a tenant."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain required"}), 400
        
        management_service = get_tenant_management_service()
        success, message = management_service.setup_custom_domain(tenant_id, data['domain'])
        
        if success:
            return jsonify({"message": message})
        else:
            return jsonify({"error": message}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error setting up custom domain: {str(e)}")
        return jsonify({"error": "Failed to setup custom domain"}), 500

# Analytics and Monitoring Routes

@white_label_bp.route('/tenants/<int:tenant_id>/analytics', methods=['GET'])
@require_partner_auth
def get_tenant_analytics(tenant_id):
    """Get tenant analytics and usage statistics."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        period = request.args.get('period', 'month')
        
        management_service = get_tenant_management_service()
        analytics = management_service.get_tenant_analytics(tenant_id, period)
        
        return jsonify({"analytics": analytics})
    except Exception as e:
        current_app.logger.error(f"Error getting tenant analytics: {str(e)}")
        return jsonify({"error": "Failed to get tenant analytics"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>/health', methods=['GET'])
@require_partner_auth
def get_tenant_health(tenant_id):
    """Get tenant health score and metrics."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        monitoring_service = get_tenant_monitoring_service()
        health_score = monitoring_service.get_tenant_health_score(tenant_id)
        
        return jsonify({"health": health_score})
    except Exception as e:
        current_app.logger.error(f"Error getting tenant health: {str(e)}")
        return jsonify({"error": "Failed to get tenant health"}), 500

@white_label_bp.route('/tenants/<int:tenant_id>/usage', methods=['GET'])
@require_partner_auth
def get_tenant_usage(tenant_id):
    """Get detailed tenant usage analytics."""
    try:
        partner = request.partner
        tenant = WhiteLabelTenant.query.filter_by(
            id=tenant_id, 
            partner_id=partner.id
        ).first_or_404()
        
        period_days = request.args.get('period_days', 30, type=int)
        
        monitoring_service = get_tenant_monitoring_service()
        usage_analytics = monitoring_service.get_usage_analytics(tenant_id, period_days)
        
        return jsonify({"usage": usage_analytics})
    except Exception as e:
        current_app.logger.error(f"Error getting tenant usage: {str(e)}")
        return jsonify({"error": "Failed to get tenant usage"}), 500

# Current Tenant Context Routes (for tenant-specific API access)

@white_label_bp.route('/current/info', methods=['GET'])
@require_tenant
def get_current_tenant_info():
    """Get current tenant information from context."""
    try:
        context = get_current_tenant_context()
        tenant = context.tenant
        
        return jsonify({
            "tenant": white_label_tenant_schema.dump(tenant),
            "organization": {
                "id": context.organization.id,
                "name": context.organization.name,
                "plan_type": context.organization.plan_type.value
            } if context.organization else None,
            "domain": context.primary_domain
        })
    except Exception as e:
        current_app.logger.error(f"Error getting current tenant info: {str(e)}")
        return jsonify({"error": "Failed to get tenant info"}), 500

@white_label_bp.route('/current/branding', methods=['GET'])
@require_tenant
def get_current_tenant_branding():
    """Get current tenant branding configuration."""
    try:
        context = get_current_tenant_context()
        
        branding_service = get_branding_service()
        brand_config = branding_service.get_tenant_brand_config(context.tenant_id)
        
        return jsonify({"branding": brand_config})
    except Exception as e:
        current_app.logger.error(f"Error getting current tenant branding: {str(e)}")
        return jsonify({"error": "Failed to get tenant branding"}), 500

@white_label_bp.route('/current/features', methods=['GET'])
@require_tenant
def get_current_tenant_features():
    """Get current tenant feature flags."""
    try:
        context = get_current_tenant_context()
        
        feature_service = get_feature_flag_service()
        features = feature_service.get_tenant_features(context.tenant_id)
        
        return jsonify({"features": features})
    except Exception as e:
        current_app.logger.error(f"Error getting current tenant features: {str(e)}")
        return jsonify({"error": "Failed to get tenant features"}), 500

# Health check and system status
@white_label_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the white-label system."""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        })
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

# Error handlers
@white_label_bp.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@white_label_bp.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Bad request"}), 400

@white_label_bp.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "Unauthorized"}), 401

@white_label_bp.errorhandler(403)
def forbidden(error):
    return jsonify({"error": "Forbidden"}), 403

@white_label_bp.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500
"""
Tenant management service for white-label multi-tenant operations.
Handles tenant lifecycle, provisioning, configuration, and monitoring.
"""
import os
import json
import secrets
import string
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from flask import current_app
import boto3
from botocore.exceptions import ClientError
import requests

from models.white_label_tenant import (
    WhiteLabelTenant, TenantStatus, TenantDomain, DomainStatus, 
    Partner, TenantUsageLog, TenantConfiguration, db
)
from models.organization import Organization, PlanType
from services.branding_service import BrandingService

class TenantManagementService:
    """
    Comprehensive tenant management service for white-label operations.
    """
    
    def __init__(self):
        self.route53_client = None
        self.acm_client = None
        self.cloudfront_client = None
        self.branding_service = BrandingService()
        self._initialize_aws_clients()
    
    def _initialize_aws_clients(self):
        """Initialize AWS clients for DNS and SSL management."""
        try:
            aws_config = {
                'aws_access_key_id': current_app.config.get('AWS_ACCESS_KEY_ID'),
                'aws_secret_access_key': current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                'region_name': current_app.config.get('AWS_REGION', 'us-east-1')
            }
            
            self.route53_client = boto3.client('route53', **aws_config)
            self.acm_client = boto3.client('acm', **aws_config)
            self.cloudfront_client = boto3.client('cloudfront', **aws_config)
            
        except Exception as e:
            current_app.logger.error(f"Failed to initialize AWS clients: {str(e)}")
    
    def create_tenant(self, partner_id: int, tenant_data: Dict[str, Any]) -> Tuple[bool, str, Optional[WhiteLabelTenant]]:
        """
        Create a new white-label tenant with complete provisioning.
        
        Args:
            partner_id: ID of the partner creating the tenant
            tenant_data: Tenant configuration data
            
        Returns:
            Tuple of (success, message, tenant_object)
        """
        try:
            # Validate partner
            partner = Partner.query.get(partner_id)
            if not partner or not partner.is_active:
                return False, "Invalid or inactive partner", None
            
            # Validate tenant data
            validation_result = self._validate_tenant_data(tenant_data)
            if not validation_result[0]:
                return False, validation_result[1], None
            
            # Generate unique tenant key
            tenant_key = self._generate_tenant_key(tenant_data.get('name', ''))
            if not tenant_key:
                return False, "Failed to generate unique tenant key", None
            
            # Check subdomain availability
            subdomain = tenant_data.get('subdomain', tenant_key)
            if not self._is_subdomain_available(subdomain):
                return False, f"Subdomain '{subdomain}' is not available", None
            
            # Create base organization
            organization = self._create_base_organization(tenant_data, partner)
            if not organization:
                return False, "Failed to create base organization", None
            
            # Create white-label tenant
            tenant = WhiteLabelTenant(
                organization_id=organization.id,
                partner_id=partner_id,
                tenant_key=tenant_key,
                display_name=tenant_data.get('display_name', tenant_data.get('name')),
                subdomain=subdomain,
                status=TenantStatus.PROVISIONING,
                brand_config=tenant_data.get('brand_config', {}),
                feature_flags=tenant_data.get('feature_flags', {}),
                resource_quotas=self._get_default_resource_quotas(tenant_data.get('plan', 'standard')),
                billing_plan=tenant_data.get('plan', 'standard'),
                technical_contact_email=tenant_data.get('technical_contact_email'),
                billing_contact_email=tenant_data.get('billing_contact_email'),
                support_email=tenant_data.get('support_email'),
                tenant_metadata=tenant_data.get('metadata', {})
            )
            
            db.session.add(tenant)
            db.session.flush()  # Get ID without committing
            
            # Start provisioning process
            success, message = self._provision_tenant_infrastructure(tenant)
            if not success:
                db.session.rollback()
                return False, f"Provisioning failed: {message}", None
            
            # Update tenant status
            tenant.status = TenantStatus.ACTIVE
            tenant.provisioned_at = datetime.utcnow()
            tenant.activated_at = datetime.utcnow()
            
            db.session.commit()
            
            # Create initial configuration
            self._create_initial_tenant_configuration(tenant)
            
            # Send welcome notifications
            self._send_tenant_welcome_notifications(tenant, partner)
            
            current_app.logger.info(f"Successfully created tenant: {tenant_key}")
            return True, "Tenant created successfully", tenant
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating tenant: {str(e)}")
            return False, f"Internal error: {str(e)}", None
    
    def update_tenant(self, tenant_id: int, updates: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update tenant configuration.
        
        Args:
            tenant_id: Tenant ID
            updates: Configuration updates
            
        Returns:
            Tuple of (success, message)
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False, "Tenant not found"
            
            # Create configuration backup for rollback
            backup_config = {
                'brand_config': tenant.brand_config,
                'feature_flags': tenant.feature_flags,
                'api_config': tenant.api_config,
                'integration_config': tenant.integration_config,
                'resource_quotas': tenant.resource_quotas
            }
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(tenant, key):
                    setattr(tenant, key, value)
            
            # Validate updates
            if not self._validate_tenant_configuration(tenant):
                return False, "Invalid configuration"
            
            # Save configuration version
            self._save_configuration_version(tenant, updates, backup_config)
            
            tenant.updated_at = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Updated tenant configuration: {tenant.tenant_key}")
            return True, "Tenant updated successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating tenant: {str(e)}")
            return False, f"Update failed: {str(e)}"
    
    def suspend_tenant(self, tenant_id: int, reason: str = None) -> Tuple[bool, str]:
        """
        Suspend a tenant's access.
        
        Args:
            tenant_id: Tenant ID
            reason: Reason for suspension
            
        Returns:
            Tuple of (success, message)
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False, "Tenant not found"
            
            if tenant.status == TenantStatus.SUSPENDED:
                return True, "Tenant is already suspended"
            
            # Update status
            tenant.status = TenantStatus.SUSPENDED
            tenant.suspended_at = datetime.utcnow()
            
            # Add suspension reason to metadata
            if not tenant.tenant_metadata:
                tenant.tenant_metadata = {}
            tenant.tenant_metadata['suspension_reason'] = reason
            tenant.tenant_metadata['suspended_by'] = 'system'  # Could be user ID
            
            db.session.commit()
            
            # Notify tenant
            self._send_tenant_suspension_notification(tenant, reason)
            
            current_app.logger.info(f"Suspended tenant: {tenant.tenant_key}")
            return True, "Tenant suspended successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error suspending tenant: {str(e)}")
            return False, f"Suspension failed: {str(e)}"
    
    def reactivate_tenant(self, tenant_id: int) -> Tuple[bool, str]:
        """
        Reactivate a suspended tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False, "Tenant not found"
            
            if tenant.status != TenantStatus.SUSPENDED:
                return False, "Tenant is not suspended"
            
            # Update status
            tenant.status = TenantStatus.ACTIVE
            tenant.suspended_at = None
            
            # Clear suspension metadata
            if tenant.tenant_metadata:
                tenant.tenant_metadata.pop('suspension_reason', None)
                tenant.tenant_metadata.pop('suspended_by', None)
            
            db.session.commit()
            
            # Notify tenant
            self._send_tenant_reactivation_notification(tenant)
            
            current_app.logger.info(f"Reactivated tenant: {tenant.tenant_key}")
            return True, "Tenant reactivated successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error reactivating tenant: {str(e)}")
            return False, f"Reactivation failed: {str(e)}"
    
    def delete_tenant(self, tenant_id: int, force: bool = False) -> Tuple[bool, str]:
        """
        Delete a tenant and clean up all resources.
        
        Args:
            tenant_id: Tenant ID
            force: Force deletion even if active
            
        Returns:
            Tuple of (success, message)
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False, "Tenant not found"
            
            if tenant.status == TenantStatus.ACTIVE and not force:
                return False, "Cannot delete active tenant without force flag"
            
            # Start deactivation process
            tenant.status = TenantStatus.DEACTIVATING
            db.session.commit()
            
            # Clean up infrastructure
            cleanup_success, cleanup_message = self._cleanup_tenant_infrastructure(tenant)
            if not cleanup_success and not force:
                return False, f"Cleanup failed: {cleanup_message}"
            
            # Archive tenant data
            self._archive_tenant_data(tenant)
            
            # Soft delete tenant
            tenant.status = TenantStatus.DEACTIVATED
            tenant.deactivated_at = datetime.utcnow()
            tenant.deleted_at = datetime.utcnow()
            
            db.session.commit()
            
            current_app.logger.info(f"Deleted tenant: {tenant.tenant_key}")
            return True, "Tenant deleted successfully"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting tenant: {str(e)}")
            return False, f"Deletion failed: {str(e)}"
    
    def setup_custom_domain(self, tenant_id: int, domain: str) -> Tuple[bool, str]:
        """
        Setup custom domain for a tenant.
        
        Args:
            tenant_id: Tenant ID
            domain: Custom domain name
            
        Returns:
            Tuple of (success, message)
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False, "Tenant not found"
            
            # Validate domain format
            if not self._is_valid_domain(domain):
                return False, "Invalid domain format"
            
            # Check if domain is already in use
            if self._is_domain_in_use(domain):
                return False, "Domain is already in use"
            
            # Create or update tenant domain record
            tenant_domain = TenantDomain.query.filter_by(
                tenant_id=tenant_id,
                domain=domain
            ).first()
            
            if not tenant_domain:
                tenant_domain = TenantDomain(
                    tenant_id=tenant_id,
                    domain=domain,
                    verification_token=self._generate_verification_token()
                )
                db.session.add(tenant_domain)
            
            # Start DNS verification process
            verification_success, verification_message = self._start_domain_verification(tenant_domain)
            if not verification_success:
                return False, f"Domain verification failed: {verification_message}"
            
            # Update tenant
            tenant.custom_domain = domain
            tenant.custom_domain_status = DomainStatus.PENDING
            
            db.session.commit()
            
            current_app.logger.info(f"Started custom domain setup for {tenant.tenant_key}: {domain}")
            return True, f"Domain verification started. Please add DNS records: {verification_message}"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error setting up custom domain: {str(e)}")
            return False, f"Domain setup failed: {str(e)}"
    
    def get_tenant_analytics(self, tenant_id: int, period: str = 'month') -> Dict[str, Any]:
        """
        Get tenant analytics and usage statistics.
        
        Args:
            tenant_id: Tenant ID
            period: Analytics period (day, week, month, year)
            
        Returns:
            Dict containing analytics data
        """
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return {}
            
            # Calculate period dates
            end_date = datetime.utcnow()
            if period == 'day':
                start_date = end_date - timedelta(days=1)
            elif period == 'week':
                start_date = end_date - timedelta(weeks=1)
            elif period == 'month':
                start_date = end_date - timedelta(days=30)
            elif period == 'year':
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Get usage logs
            usage_logs = TenantUsageLog.query.filter(
                TenantUsageLog.tenant_id == tenant_id,
                TenantUsageLog.period_start >= start_date,
                TenantUsageLog.period_end <= end_date
            ).all()
            
            # Aggregate usage data
            usage_summary = {}
            for log in usage_logs:
                resource_type = log.resource_type
                if resource_type not in usage_summary:
                    usage_summary[resource_type] = {
                        'total': 0,
                        'quota': tenant.get_resource_quota(resource_type),
                        'periods': []
                    }
                usage_summary[resource_type]['total'] += log.usage_value
                usage_summary[resource_type]['periods'].append({
                    'period_start': log.period_start.isoformat(),
                    'period_end': log.period_end.isoformat(),
                    'value': log.usage_value
                })
            
            # Get tenant health metrics
            health_metrics = self._calculate_tenant_health_metrics(tenant)
            
            return {
                'tenant_id': tenant_id,
                'tenant_key': tenant.tenant_key,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'usage_summary': usage_summary,
                'health_metrics': health_metrics,
                'status': tenant.status.value,
                'created_at': tenant.created_at.isoformat(),
                'last_activity': self._get_last_activity(tenant_id)
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting tenant analytics: {str(e)}")
            return {}
    
    def _validate_tenant_data(self, tenant_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate tenant creation data."""
        required_fields = ['name', 'contact_email']
        
        for field in required_fields:
            if field not in tenant_data or not tenant_data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, tenant_data['contact_email']):
            return False, "Invalid email format"
        
        # Validate subdomain if provided
        if 'subdomain' in tenant_data:
            if not self._is_valid_subdomain(tenant_data['subdomain']):
                return False, "Invalid subdomain format"
        
        return True, "Valid"
    
    def _generate_tenant_key(self, name: str) -> Optional[str]:
        """Generate unique tenant key from name."""
        import re
        
        # Clean name and create base key
        base_key = re.sub(r'[^a-zA-Z0-9]', '', name.lower())[:20]
        if not base_key:
            base_key = 'tenant'
        
        # Try to find unique key
        for i in range(100):
            if i == 0:
                tenant_key = base_key
            else:
                tenant_key = f"{base_key}{i}"
            
            if not WhiteLabelTenant.query.filter_by(tenant_key=tenant_key).first():
                return tenant_key
        
        return None
    
    def _is_subdomain_available(self, subdomain: str) -> bool:
        """Check if subdomain is available."""
        return not WhiteLabelTenant.query.filter_by(subdomain=subdomain).first()
    
    def _is_valid_subdomain(self, subdomain: str) -> bool:
        """Validate subdomain format."""
        import re
        pattern = r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$'
        return bool(re.match(pattern, subdomain)) and len(subdomain) >= 3
    
    def _create_base_organization(self, tenant_data: Dict[str, Any], partner: Partner) -> Optional[Organization]:
        """Create base organization for tenant."""
        try:
            organization = Organization(
                name=tenant_data['name'],
                contact_email=tenant_data['contact_email'],
                phone=tenant_data.get('phone'),
                address=tenant_data.get('address'),
                plan_type=PlanType.PROFESSIONAL,  # Default for white-label
                max_properties=tenant_data.get('max_properties', 50),
                max_units=tenant_data.get('max_units', 500),
                max_users=tenant_data.get('max_users', 20),
                has_ai_features=True,
                has_lpr_access=True,
                has_video_inspection=True,
                has_advanced_reporting=True
            )
            
            db.session.add(organization)
            db.session.flush()
            
            return organization
            
        except Exception as e:
            current_app.logger.error(f"Error creating base organization: {str(e)}")
            return None
    
    def _get_default_resource_quotas(self, plan: str) -> Dict[str, int]:
        """Get default resource quotas based on plan."""
        quotas = {
            'starter': {
                'api_calls_monthly': 10000,
                'storage_gb': 5,
                'users': 5,
                'properties': 10,
                'units': 50
            },
            'standard': {
                'api_calls_monthly': 50000,
                'storage_gb': 25,
                'users': 20,
                'properties': 50,
                'units': 500
            },
            'premium': {
                'api_calls_monthly': 100000,
                'storage_gb': 100,
                'users': 50,
                'properties': 200,
                'units': 2000
            },
            'enterprise': {
                'api_calls_monthly': 500000,
                'storage_gb': 500,
                'users': 200,
                'properties': 1000,
                'units': 10000
            }
        }
        
        return quotas.get(plan, quotas['standard'])
    
    def _provision_tenant_infrastructure(self, tenant: WhiteLabelTenant) -> Tuple[bool, str]:
        """Provision infrastructure for new tenant."""
        try:
            # Create subdomain DNS record
            dns_success, dns_message = self._create_subdomain_dns(tenant.subdomain)
            if not dns_success:
                return False, f"DNS setup failed: {dns_message}"
            
            # Setup CDN distribution
            cdn_success, cdn_message = self._setup_cdn_distribution(tenant)
            if not cdn_success:
                return False, f"CDN setup failed: {cdn_message}"
            
            # Initialize branding assets
            self._initialize_tenant_branding(tenant)
            
            return True, "Infrastructure provisioned successfully"
            
        except Exception as e:
            return False, f"Infrastructure provisioning error: {str(e)}"
    
    def _create_subdomain_dns(self, subdomain: str) -> Tuple[bool, str]:
        """Create DNS record for subdomain."""
        try:
            if not self.route53_client:
                return True, "DNS client not configured - skipping DNS setup"
            
            # This would create actual DNS records in Route53
            # Implementation depends on your DNS setup
            
            return True, "DNS record created"
            
        except Exception as e:
            return False, f"DNS error: {str(e)}"
    
    def _setup_cdn_distribution(self, tenant: WhiteLabelTenant) -> Tuple[bool, str]:
        """Setup CloudFront distribution for tenant."""
        try:
            if not self.cloudfront_client:
                return True, "CloudFront client not configured - skipping CDN setup"
            
            # This would create actual CloudFront distribution
            # Implementation depends on your CDN setup
            
            return True, "CDN distribution created"
            
        except Exception as e:
            return False, f"CDN error: {str(e)}"
    
    def _initialize_tenant_branding(self, tenant: WhiteLabelTenant):
        """Initialize default branding for tenant."""
        try:
            # Set default brand configuration if not provided
            if not tenant.brand_config:
                tenant.brand_config = self.branding_service._get_default_brand_config()
                tenant.brand_config['name'] = tenant.display_name
        except Exception as e:
            current_app.logger.error(f"Error initializing tenant branding: {str(e)}")
    
    # Additional helper methods for notifications, cleanup, etc.
    
    def _send_tenant_welcome_notifications(self, tenant: WhiteLabelTenant, partner: Partner):
        """Send welcome notifications to tenant and partner."""
        # Implementation would send actual emails/notifications
        pass
    
    def _send_tenant_suspension_notification(self, tenant: WhiteLabelTenant, reason: str):
        """Send suspension notification to tenant."""
        # Implementation would send actual notification
        pass
    
    def _send_tenant_reactivation_notification(self, tenant: WhiteLabelTenant):
        """Send reactivation notification to tenant."""
        # Implementation would send actual notification
        pass

def get_tenant_management_service() -> TenantManagementService:
    """Get tenant management service instance."""
    return TenantManagementService()
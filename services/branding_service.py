"""
Branding and customization service for white-label tenants.
Handles theme management, asset customization, and brand-specific configurations.
"""
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from flask import current_app, url_for
from PIL import Image
import boto3
from botocore.exceptions import ClientError
import requests
from datetime import datetime, timedelta

from services.tenant_context import get_current_tenant_context

class BrandingService:
    """
    Service for managing tenant-specific branding and customization.
    """
    
    def __init__(self):
        self.s3_client = None
        self.cdn_url = current_app.config.get('CDN_URL', '')
        self.bucket_name = current_app.config.get('BRANDING_BUCKET', 'estatecore-branding')
        self._initialize_s3()
    
    def _initialize_s3(self):
        """Initialize S3 client for asset storage."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
                region_name=current_app.config.get('AWS_REGION', 'us-east-1')
            )
        except Exception as e:
            current_app.logger.error(f"Failed to initialize S3 client: {str(e)}")
    
    def get_tenant_brand_config(self, tenant_id: int = None) -> Dict[str, Any]:
        """
        Get complete brand configuration for a tenant.
        
        Args:
            tenant_id: Tenant ID (uses current context if None)
            
        Returns:
            Dict containing complete brand configuration
        """
        from models.white_label_tenant import WhiteLabelTenant
        
        if tenant_id is None:
            context = get_current_tenant_context()
            if not context or not context.tenant:
                return self._get_default_brand_config()
            tenant = context.tenant
        else:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return self._get_default_brand_config()
        
        # Merge default config with tenant-specific overrides
        brand_config = self._get_default_brand_config()
        if tenant.brand_config:
            brand_config.update(tenant.brand_config)
        
        # Process asset URLs
        brand_config = self._process_asset_urls(brand_config, tenant.tenant_key)
        
        return brand_config
    
    def _get_default_brand_config(self) -> Dict[str, Any]:
        """Get default brand configuration."""
        return {
            'name': 'EstateCore',
            'tagline': 'Professional Property Management',
            'description': 'Comprehensive property management solution',
            'website': 'https://estatecore.com',
            'support_email': 'support@estatecore.com',
            'support_phone': '+1-555-ESTATE',
            
            # Logo configuration
            'logo': {
                'primary': '/static/assets/logo-primary.png',
                'secondary': '/static/assets/logo-secondary.png',
                'icon': '/static/assets/icon.png',
                'favicon': '/static/assets/favicon.ico',
                'watermark': '/static/assets/watermark.png'
            },
            
            # Color scheme
            'colors': {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'success': '#28a745',
                'danger': '#dc3545',
                'warning': '#ffc107',
                'info': '#17a2b8',
                'light': '#f8f9fa',
                'dark': '#343a40',
                'background': '#ffffff',
                'surface': '#f8f9fa',
                'text_primary': '#212529',
                'text_secondary': '#6c757d'
            },
            
            # Typography
            'typography': {
                'font_family_primary': "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                'font_family_secondary': "'Roboto', sans-serif",
                'font_size_base': '1rem',
                'font_weight_normal': '400',
                'font_weight_bold': '600',
                'line_height_base': '1.5'
            },
            
            # Layout and spacing
            'layout': {
                'border_radius': '0.5rem',
                'box_shadow': '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
                'container_max_width': '1200px',
                'sidebar_width': '280px',
                'header_height': '70px'
            },
            
            # Email branding
            'email': {
                'header_color': '#007bff',
                'footer_color': '#f8f9fa',
                'link_color': '#007bff',
                'signature': 'Best regards,<br>The EstateCore Team'
            },
            
            # Custom CSS
            'custom_css': '',
            
            # Feature customization
            'features': {
                'show_powered_by': True,
                'custom_dashboard_layout': False,
                'custom_login_page': False,
                'custom_404_page': False
            },
            
            # Legal documents
            'legal': {
                'terms_of_service': '/legal/terms',
                'privacy_policy': '/legal/privacy',
                'cookie_policy': '/legal/cookies'
            },
            
            # Social media
            'social': {
                'facebook': '',
                'twitter': '',
                'linkedin': '',
                'instagram': ''
            }
        }
    
    def update_tenant_brand_config(self, tenant_id: int, config_updates: Dict[str, Any]) -> bool:
        """
        Update tenant brand configuration.
        
        Args:
            tenant_id: Tenant ID
            config_updates: Dict of configuration updates
            
        Returns:
            True if successful, False otherwise
        """
        from models.white_label_tenant import WhiteLabelTenant, db
        
        try:
            tenant = WhiteLabelTenant.query.get(tenant_id)
            if not tenant:
                return False
            
            # Validate configuration updates
            validated_config = self._validate_brand_config(config_updates)
            
            # Merge with existing configuration
            current_config = tenant.brand_config or {}
            current_config.update(validated_config)
            
            # Update tenant
            tenant.brand_config = current_config
            tenant.updated_at = datetime.utcnow()
            
            db.session.add(tenant)
            db.session.commit()
            
            # Clear any cached branding data
            self._clear_branding_cache(tenant.tenant_key)
            
            current_app.logger.info(f"Updated brand configuration for tenant {tenant.tenant_key}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error updating brand configuration: {str(e)}")
            return False
    
    def upload_brand_asset(self, tenant_key: str, asset_type: str, file_data: bytes, 
                          filename: str, content_type: str = None) -> Optional[str]:
        """
        Upload a brand asset (logo, image, etc.) for a tenant.
        
        Args:
            tenant_key: Tenant key
            asset_type: Type of asset (logo, icon, background, etc.)
            file_data: Binary file data
            filename: Original filename
            content_type: MIME content type
            
        Returns:
            URL of uploaded asset or None if failed
        """
        if not self.s3_client:
            current_app.logger.error("S3 client not initialized")
            return None
        
        try:
            # Validate and process image
            if not self._validate_image(file_data, asset_type):
                return None
            
            # Generate S3 key
            file_extension = os.path.splitext(filename)[1].lower()
            s3_key = f"tenants/{tenant_key}/assets/{asset_type}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            
            # Upload to S3
            upload_params = {
                'Bucket': self.bucket_name,
                'Key': s3_key,
                'Body': file_data,
                'ContentType': content_type or 'application/octet-stream',
                'ACL': 'public-read'
            }
            
            self.s3_client.put_object(**upload_params)
            
            # Generate URL
            asset_url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            if self.cdn_url:
                asset_url = f"{self.cdn_url}/{s3_key}"
            
            current_app.logger.info(f"Uploaded brand asset for {tenant_key}: {asset_url}")
            return asset_url
            
        except Exception as e:
            current_app.logger.error(f"Error uploading brand asset: {str(e)}")
            return None
    
    def generate_theme_css(self, tenant_id: int = None) -> str:
        """
        Generate CSS for tenant-specific theme.
        
        Args:
            tenant_id: Tenant ID (uses current context if None)
            
        Returns:
            Generated CSS string
        """
        brand_config = self.get_tenant_brand_config(tenant_id)
        
        # Generate CSS variables
        css_vars = self._generate_css_variables(brand_config)
        
        # Generate component styles
        component_styles = self._generate_component_styles(brand_config)
        
        # Combine with custom CSS
        custom_css = brand_config.get('custom_css', '')
        
        css_content = f"""
/* Auto-generated tenant theme CSS */
:root {{
{css_vars}
}}

{component_styles}

/* Custom CSS */
{custom_css}
        """.strip()
        
        return css_content
    
    def _generate_css_variables(self, brand_config: Dict[str, Any]) -> str:
        """Generate CSS custom properties from brand configuration."""
        colors = brand_config.get('colors', {})
        typography = brand_config.get('typography', {})
        layout = brand_config.get('layout', {})
        
        css_vars = []
        
        # Color variables
        for color_name, color_value in colors.items():
            css_vars.append(f"  --color-{color_name.replace('_', '-')}: {color_value};")
        
        # Typography variables
        for typo_name, typo_value in typography.items():
            css_vars.append(f"  --{typo_name.replace('_', '-')}: {typo_value};")
        
        # Layout variables
        for layout_name, layout_value in layout.items():
            css_vars.append(f"  --{layout_name.replace('_', '-')}: {layout_value};")
        
        return '\n'.join(css_vars)
    
    def _generate_component_styles(self, brand_config: Dict[str, Any]) -> str:
        """Generate component-specific styles."""
        return """
/* Button styles */
.btn-primary {
    background-color: var(--color-primary);
    border-color: var(--color-primary);
}

.btn-primary:hover {
    background-color: var(--color-primary);
    border-color: var(--color-primary);
    opacity: 0.9;
}

/* Header styles */
.navbar {
    background-color: var(--color-primary) !important;
    height: var(--header-height);
}

/* Sidebar styles */
.sidebar {
    width: var(--sidebar-width);
    background-color: var(--color-surface);
}

/* Container styles */
.container-fluid {
    max-width: var(--container-max-width);
}

/* Typography */
body {
    font-family: var(--font-family-primary);
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--color-text-primary);
}

/* Card styles */
.card {
    border-radius: var(--border-radius);
    box-shadow: var(--box-shadow);
}
        """
    
    def _validate_image(self, file_data: bytes, asset_type: str) -> bool:
        """Validate uploaded image file."""
        try:
            # Basic size check
            if len(file_data) > 5 * 1024 * 1024:  # 5MB limit
                current_app.logger.warning("Image file too large")
                return False
            
            # Try to open with PIL to validate format
            image = Image.open(io.BytesIO(file_data))
            
            # Check format
            if image.format not in ['PNG', 'JPEG', 'JPG', 'GIF', 'WEBP']:
                current_app.logger.warning(f"Invalid image format: {image.format}")
                return False
            
            # Asset-specific validation
            if asset_type == 'logo':
                # Logo should be reasonable dimensions
                if image.width > 2000 or image.height > 2000:
                    current_app.logger.warning("Logo dimensions too large")
                    return False
            elif asset_type == 'icon':
                # Icon should be square and reasonable size
                if abs(image.width - image.height) > 10:  # Allow small variation
                    current_app.logger.warning("Icon should be square")
                    return False
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Image validation error: {str(e)}")
            return False
    
    def _validate_brand_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize brand configuration."""
        validated = {}
        
        # Validate color values
        if 'colors' in config:
            validated['colors'] = {}
            for color_name, color_value in config['colors'].items():
                if self._is_valid_color(color_value):
                    validated['colors'][color_name] = color_value
        
        # Validate typography
        if 'typography' in config:
            validated['typography'] = {}
            for typo_name, typo_value in config['typography'].items():
                if isinstance(typo_value, str) and len(typo_value) < 200:
                    validated['typography'][typo_name] = typo_value
        
        # Validate text fields
        text_fields = ['name', 'tagline', 'description', 'website', 'support_email']
        for field in text_fields:
            if field in config and isinstance(config[field], str):
                validated[field] = config[field][:500]  # Limit length
        
        # Validate nested objects
        for nested_field in ['layout', 'email', 'features', 'legal', 'social']:
            if nested_field in config and isinstance(config[nested_field], dict):
                validated[nested_field] = config[nested_field]
        
        return validated
    
    def _is_valid_color(self, color: str) -> bool:
        """Validate CSS color value."""
        if not isinstance(color, str):
            return False
        
        # Check hex colors
        if color.startswith('#') and len(color) in [4, 7]:
            try:
                int(color[1:], 16)
                return True
            except ValueError:
                pass
        
        # Check named colors (basic validation)
        if color.lower() in ['red', 'blue', 'green', 'yellow', 'black', 'white', 'gray', 'grey']:
            return True
        
        # Check rgb/rgba
        if color.startswith(('rgb(', 'rgba(')):
            return True
        
        return False
    
    def _process_asset_urls(self, brand_config: Dict[str, Any], tenant_key: str) -> Dict[str, Any]:
        """Process asset URLs to ensure they're properly formatted."""
        logo_config = brand_config.get('logo', {})
        
        for asset_type, asset_url in logo_config.items():
            if asset_url and not asset_url.startswith(('http://', 'https://', '//')):
                # Convert relative URLs to CDN URLs if needed
                if asset_url.startswith('/'):
                    if self.cdn_url:
                        logo_config[asset_type] = f"{self.cdn_url}{asset_url}"
                else:
                    # Assume it's a tenant-specific asset
                    if self.cdn_url:
                        logo_config[asset_type] = f"{self.cdn_url}/tenants/{tenant_key}/assets/{asset_url}"
        
        brand_config['logo'] = logo_config
        return brand_config
    
    def _clear_branding_cache(self, tenant_key: str):
        """Clear cached branding data for a tenant."""
        # This would integrate with your caching system (Redis, Memcached, etc.)
        try:
            # Example: cache.delete(f"branding:{tenant_key}")
            pass
        except Exception as e:
            current_app.logger.error(f"Error clearing branding cache: {str(e)}")

class EmailBrandingService:
    """
    Service for managing branded email templates.
    """
    
    def __init__(self):
        self.template_path = current_app.config.get('EMAIL_TEMPLATE_PATH', 'templates/email')
    
    def render_branded_email(self, template_name: str, tenant_id: int = None, **context) -> str:
        """
        Render email template with tenant branding.
        
        Args:
            template_name: Email template name
            tenant_id: Tenant ID (uses current context if None)
            **context: Template context variables
            
        Returns:
            Rendered HTML email content
        """
        branding_service = BrandingService()
        brand_config = branding_service.get_tenant_brand_config(tenant_id)
        
        # Add branding to template context
        context.update({
            'brand': brand_config,
            'tenant_brand': brand_config  # Alias for backward compatibility
        })
        
        # Render template with Flask's render_template
        from flask import render_template
        return render_template(f"email/{template_name}", **context)
    
    def get_email_branding_config(self, tenant_id: int = None) -> Dict[str, Any]:
        """Get email-specific branding configuration."""
        branding_service = BrandingService()
        brand_config = branding_service.get_tenant_brand_config(tenant_id)
        
        return {
            'header_color': brand_config.get('email', {}).get('header_color', '#007bff'),
            'footer_color': brand_config.get('email', {}).get('footer_color', '#f8f9fa'),
            'link_color': brand_config.get('email', {}).get('link_color', '#007bff'),
            'signature': brand_config.get('email', {}).get('signature', ''),
            'logo_url': brand_config.get('logo', {}).get('primary', ''),
            'company_name': brand_config.get('name', 'EstateCore'),
            'support_email': brand_config.get('support_email', 'support@estatecore.com'),
            'website': brand_config.get('website', 'https://estatecore.com')
        }

def get_branding_service() -> BrandingService:
    """Get branding service instance."""
    return BrandingService()

def get_email_branding_service() -> EmailBrandingService:
    """Get email branding service instance."""
    return EmailBrandingService()
#!/usr/bin/env python3
"""
EstateCore API Gateway Setup Script
Automated setup and configuration for the enterprise API Gateway
"""

import os
import sys
import json
import yaml
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import secrets
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIGatewaySetup:
    """API Gateway setup and configuration manager"""
    
    def __init__(self, config_path: str = None):
        self.project_root = Path(__file__).parent
        self.config_path = config_path or self.project_root / "api_gateway_config.yaml"
        self.config = self.load_configuration()
        
    def load_configuration(self):
        """Load API Gateway configuration"""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            return {}
    
    def validate_environment(self):
        """Validate the environment for API Gateway deployment"""
        logger.info("Validating environment...")
        
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 8):
            issues.append("Python 3.8+ is required")
        
        # Check required directories
        required_dirs = [
            'templates/code_samples',
            'templates/explorer',
            'instance'
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {full_path}")
                except Exception as e:
                    issues.append(f"Cannot create directory {full_path}: {str(e)}")
        
        # Check required environment variables
        required_env_vars = [
            'SECRET_KEY',
            'DATABASE_URL'
        ]
        
        missing_env_vars = []
        for var in required_env_vars:
            if not os.environ.get(var):
                missing_env_vars.append(var)
        
        if missing_env_vars:
            logger.warning(f"Missing environment variables: {', '.join(missing_env_vars)}")
            logger.info("These will be generated or set to defaults")
        
        # Check file permissions
        important_files = [
            'api_gateway_service.py',
            'api_key_management_service.py',
            'oauth_authentication_service.py'
        ]
        
        for file_name in important_files:
            file_path = self.project_root / file_name
            if not file_path.exists():
                issues.append(f"Missing required file: {file_name}")
            elif not os.access(file_path, os.R_OK):
                issues.append(f"Cannot read file: {file_name}")
        
        if issues:
            logger.error("Environment validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("Environment validation passed")
        return True
    
    def setup_environment_variables(self):
        """Setup required environment variables"""
        logger.info("Setting up environment variables...")
        
        env_file = self.project_root / ".env"
        env_vars = {}
        
        # Load existing .env file if it exists
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        # Generate missing critical variables
        if 'SECRET_KEY' not in env_vars:
            env_vars['SECRET_KEY'] = secrets.token_urlsafe(32)
            logger.info("Generated new SECRET_KEY")
        
        if 'JWT_SECRET_KEY' not in env_vars:
            env_vars['JWT_SECRET_KEY'] = secrets.token_urlsafe(32)
            logger.info("Generated new JWT_SECRET_KEY")
        
        if 'API_KEY_MASTER_KEY' not in env_vars:
            env_vars['API_KEY_MASTER_KEY'] = secrets.token_urlsafe(32)
            logger.info("Generated new API_KEY_MASTER_KEY")
        
        if 'DATABASE_URL' not in env_vars:
            env_vars['DATABASE_URL'] = 'sqlite:///instance/estatecore.db'
            logger.info("Set default DATABASE_URL")
        
        # API Gateway specific variables
        gateway_vars = {
            'API_GATEWAY_CONFIG': str(self.config_path),
            'API_BASE_URL': 'http://localhost:5000',
            'API_SANDBOX_URL': 'http://localhost:5000/sandbox',
            'OAUTH_AUTHORIZE_URL': 'http://localhost:5000/oauth/authorize',
            'JWT_ISSUER': 'estatecore-api-gateway',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:5173',
            'API_KEYS_STORAGE_PATH': 'instance/api_keys.json',
            'TENANT_CONFIG_PATH': 'instance/tenant_configs.json',
            'BACKUP_ROOT_DIR': 'instance/backups',
            'BACKUP_ENCRYPTION_KEY': secrets.token_urlsafe(32)
        }
        
        for key, value in gateway_vars.items():
            if key not in env_vars:
                env_vars[key] = value
        
        # Write .env file
        with open(env_file, 'w') as f:
            f.write("# EstateCore API Gateway Environment Variables\n")
            f.write(f"# Generated on {datetime.utcnow().isoformat()}\n\n")
            
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        logger.info(f"Environment variables written to {env_file}")
        
        # Set variables in current environment
        for key, value in env_vars.items():
            os.environ[key] = value
    
    def install_dependencies(self):
        """Install required Python dependencies"""
        logger.info("Installing Python dependencies...")
        
        # Check if we're in a virtual environment
        if sys.prefix == sys.base_prefix:
            logger.warning("Not running in a virtual environment. Consider using venv or conda.")
        
        # Additional requirements for API Gateway
        gateway_requirements = [
            'pyyaml>=6.0',
            'jinja2>=3.0.0',
            'aiohttp>=3.8.0',
            'cryptography>=41.0.0',
            'psutil>=5.9.0'
        ]
        
        try:
            for requirement in gateway_requirements:
                logger.info(f"Installing {requirement}...")
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', requirement
                ], check=True, capture_output=True, text=True)
            
            logger.info("Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            logger.error(f"Output: {e.stdout}")
            logger.error(f"Error: {e.stderr}")
            return False
        
        return True
    
    def initialize_database(self):
        """Initialize database for API Gateway"""
        logger.info("Initializing database...")
        
        try:
            # Import after dependencies are installed
            from api_key_management_service import get_api_key_service, APIKeyType, APIKeyPermissions
            from enterprise_features_service import get_enterprise_service, TenantTier
            
            # Initialize services
            key_service = get_api_key_service()
            enterprise_service = get_enterprise_service()
            
            # Create demo tenant
            if not enterprise_service.tenant_manager.tenants:
                demo_tenant = enterprise_service.tenant_manager.create_tenant(
                    organization_id="demo_org",
                    tenant_name="Demo Organization",
                    tier=TenantTier.PROFESSIONAL,
                    custom_domain=None
                )
                logger.info(f"Created demo tenant: {demo_tenant.tenant_id}")
                
                # Create demo API key
                demo_permissions = APIKeyPermissions(
                    endpoints=["/api/v1/*"],
                    methods=["GET", "POST", "PUT", "DELETE"],
                    rate_limits={"default": 100},
                    data_access_level="standard"
                )
                
                demo_key, demo_key_obj = key_service.create_api_key(
                    client_id="demo_client",
                    organization_id="demo_org",
                    name="Demo API Key",
                    description="Demo API key for testing",
                    key_type=APIKeyType.FULL_ACCESS,
                    permissions=demo_permissions
                )
                
                logger.info(f"Created demo API key: {demo_key}")
                logger.info(f"Key ID: {demo_key_obj.key_id}")
            
            logger.info("Database initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    def setup_monitoring(self):
        """Setup monitoring and analytics"""
        logger.info("Setting up monitoring and analytics...")
        
        try:
            from api_monitoring_service import get_monitoring_service
            
            monitoring_service = get_monitoring_service()
            
            # The monitoring service will auto-initialize with default settings
            logger.info("Monitoring service initialized")
            
            # Create monitoring directories
            monitoring_dirs = [
                'instance/logs',
                'instance/metrics',
                'instance/alerts'
            ]
            
            for dir_path in monitoring_dirs:
                full_path = self.project_root / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
            
            logger.info("Monitoring setup completed")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {str(e)}")
            return False
    
    def generate_documentation(self):
        """Generate initial API documentation"""
        logger.info("Generating API documentation...")
        
        try:
            from api_documentation_service import get_documentation_service
            
            doc_service = get_documentation_service()
            
            # Generate OpenAPI spec
            openapi_spec = doc_service.generate_documentation()
            
            # Save OpenAPI spec
            docs_dir = self.project_root / "docs" / "api"
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            spec_file = docs_dir / "openapi.json"
            with open(spec_file, 'w') as f:
                json.dump(openapi_spec, f, indent=2)
            
            logger.info(f"OpenAPI specification saved to {spec_file}")
            
            # Generate API explorer
            explorer_html = doc_service.generate_api_explorer()
            
            explorer_file = docs_dir / "index.html"
            with open(explorer_file, 'w') as f:
                f.write(explorer_html)
            
            logger.info(f"API explorer saved to {explorer_file}")
            
            logger.info("Documentation generation completed")
            return True
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {str(e)}")
            return False
    
    def create_startup_script(self):
        """Create startup script for API Gateway"""
        logger.info("Creating startup script...")
        
        startup_script_content = '''#!/usr/bin/env python3
"""
EstateCore API Gateway Startup Script
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import and setup API Gateway
from api_gateway_routes import setup_api_gateway_integration
from app import create_app

def main():
    """Main entry point for API Gateway"""
    print("Starting EstateCore API Gateway...")
    
    # Create Flask app
    app = create_app()
    
    # Setup API Gateway integration
    middleware = setup_api_gateway_integration(app)
    
    print("API Gateway integration setup completed")
    print(f"Gateway endpoints registered: {len(middleware.gateway_service.endpoints)}")
    print(f"Gateway clients registered: {len(middleware.gateway_service.clients)}")
    
    # Get configuration
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting server on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"API documentation available at: http://{host}:{port}/api/gateway/docs")
    print(f"API gateway status: http://{host}:{port}/api/gateway/status")
    
    # Start the application
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
'''
        
        startup_script = self.project_root / "start_api_gateway.py"
        with open(startup_script, 'w') as f:
            f.write(startup_script_content)
        
        # Make executable on Unix systems
        if os.name != 'nt':
            os.chmod(startup_script, 0o755)
        
        logger.info(f"Startup script created: {startup_script}")
    
    def create_docker_setup(self):
        """Create Docker setup files"""
        logger.info("Creating Docker setup files...")
        
        # Dockerfile for API Gateway
        dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install API Gateway specific dependencies
RUN pip install --no-cache-dir \\
    pyyaml>=6.0 \\
    jinja2>=3.0.0 \\
    aiohttp>=3.8.0 \\
    cryptography>=41.0.0 \\
    psutil>=5.9.0

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p instance/logs instance/metrics instance/alerts instance/backups templates/code_samples templates/explorer

# Set environment variables
ENV FLASK_APP=start_api_gateway.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:5000/api/gateway/health || exit 1

# Start command
CMD ["python", "start_api_gateway.py"]
'''
        
        dockerfile = self.project_root / "Dockerfile.apigateway"
        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)
        
        # Docker Compose for API Gateway
        docker_compose_content = '''version: '3.8'

services:
  api-gateway:
    build:
      context: .
      dockerfile: Dockerfile.apigateway
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/estatecore
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - API_KEY_MASTER_KEY=${API_KEY_MASTER_KEY}
      - API_BASE_URL=http://localhost:5000
      - CORS_ORIGINS=http://localhost:3000,http://localhost:5173
    volumes:
      - ./instance:/app/instance
      - ./docs:/app/docs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/gateway/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=estatecore
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api-gateway
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
'''
        
        compose_file = self.project_root / "docker-compose.apigateway.yml"
        with open(compose_file, 'w') as f:
            f.write(docker_compose_content)
        
        logger.info("Docker setup files created")
    
    def run_tests(self):
        """Run API Gateway tests"""
        logger.info("Running API Gateway tests...")
        
        try:
            test_file = self.project_root / "test_api_gateway.py"
            if not test_file.exists():
                logger.warning("Test file not found, skipping tests")
                return True
            
            result = subprocess.run([
                sys.executable, str(test_file)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("All tests passed")
                return True
            else:
                logger.error("Some tests failed")
                logger.error(f"Test output: {result.stdout}")
                logger.error(f"Test errors: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Test execution failed: {str(e)}")
            return False
    
    def print_summary(self):
        """Print setup summary and next steps"""
        print("\n" + "="*60)
        print("EstateCore API Gateway Setup Complete!")
        print("="*60)
        print()
        print("Configuration:")
        print(f"  - Config file: {self.config_path}")
        print(f"  - Environment file: {self.project_root}/.env")
        print(f"  - Instance directory: {self.project_root}/instance")
        print()
        print("To start the API Gateway:")
        print(f"  python {self.project_root}/start_api_gateway.py")
        print()
        print("API Endpoints:")
        print("  - Gateway Status: http://localhost:5000/api/gateway/status")
        print("  - API Documentation: http://localhost:5000/api/gateway/docs")
        print("  - OpenAPI Spec: http://localhost:5000/api/gateway/docs/openapi.json")
        print("  - Health Check: http://localhost:5000/api/gateway/health")
        print()
        print("Management Endpoints:")
        print("  - Create API Key: POST /api/gateway/keys")
        print("  - OAuth Token: POST /api/gateway/oauth/token")
        print("  - Metrics: GET /api/gateway/metrics")
        print("  - Analytics: GET /api/gateway/analytics/dashboard")
        print()
        print("Docker Deployment:")
        print("  docker-compose -f docker-compose.apigateway.yml up -d")
        print()
        print("Need help? Check the documentation at:")
        print("  - API Docs: http://localhost:5000/api/gateway/docs")
        print("  - Project README: https://github.com/estatecore/api-gateway")
        print()
        print("="*60)

def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description='Setup EstateCore API Gateway')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--skip-deps', action='store_true', help='Skip installing dependencies')
    parser.add_argument('--docker-only', action='store_true', help='Only create Docker setup files')
    args = parser.parse_args()
    
    setup = APIGatewaySetup(args.config)
    
    logger.info("Starting EstateCore API Gateway setup...")
    
    if args.docker_only:
        setup.create_docker_setup()
        logger.info("Docker setup files created successfully")
        return
    
    # Validate environment
    if not setup.validate_environment():
        logger.error("Environment validation failed. Please fix the issues and try again.")
        sys.exit(1)
    
    # Setup environment variables
    setup.setup_environment_variables()
    
    # Install dependencies
    if not args.skip_deps:
        if not setup.install_dependencies():
            logger.error("Dependency installation failed")
            sys.exit(1)
    
    # Initialize database
    if not setup.initialize_database():
        logger.error("Database initialization failed")
        sys.exit(1)
    
    # Setup monitoring
    if not setup.setup_monitoring():
        logger.error("Monitoring setup failed")
        sys.exit(1)
    
    # Generate documentation
    if not setup.generate_documentation():
        logger.error("Documentation generation failed")
        sys.exit(1)
    
    # Create startup script
    setup.create_startup_script()
    
    # Create Docker setup
    setup.create_docker_setup()
    
    # Run tests
    if not args.skip_tests:
        if not setup.run_tests():
            logger.warning("Some tests failed, but setup will continue")
    
    # Print summary
    setup.print_summary()
    
    logger.info("EstateCore API Gateway setup completed successfully!")

if __name__ == '__main__':
    main()
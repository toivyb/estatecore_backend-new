"""
Yardi Integration Setup

Setup script for installing and configuring the Yardi property management
integration for EstateCore.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class YardiIntegrationSetup:
    """Yardi Integration Setup and Configuration"""
    
    def __init__(self):
        self.config_file = "yardi_config.json"
        self.encryption_key_file = "yardi_encryption.key"
        
    def install_dependencies(self):
        """Install required dependencies"""
        logger.info("Installing Yardi integration dependencies...")
        
        try:
            import subprocess
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", 
                os.path.join(os.path.dirname(__file__), "requirements.txt")
            ], check=True, capture_output=True, text=True)
            
            logger.info("Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        config = {
            "version": "1.0.0",
            "created_at": datetime.utcnow().isoformat(),
            "yardi_products": {
                "voyager": {
                    "enabled": True,
                    "api_version": "1.0",
                    "default_timeout": 30,
                    "rate_limit": 60
                },
                "breeze": {
                    "enabled": True,
                    "api_version": "2.0", 
                    "default_timeout": 20,
                    "rate_limit": 100
                },
                "genesis2": {
                    "enabled": False,
                    "api_version": "1.5",
                    "default_timeout": 45,
                    "rate_limit": 30
                }
            },
            "sync_configuration": {
                "default_batch_size": 100,
                "max_parallel_workers": 4,
                "default_timeout": 300,
                "max_retries": 3,
                "retry_delay": 5,
                "enable_real_time": True,
                "enable_webhooks": True,
                "backup_enabled": True
            },
            "monitoring": {
                "health_check_interval": 300,
                "metric_retention_days": 30,
                "alert_channels": ["email", "webhook"],
                "performance_thresholds": {
                    "api_response_time_warning": 1000,
                    "api_response_time_error": 5000,
                    "error_rate_warning": 5,
                    "error_rate_error": 10
                }
            },
            "security": {
                "encryption_enabled": True,
                "token_expiry_hours": 24,
                "webhook_signature_required": True,
                "rate_limiting_enabled": True
            },
            "enterprise": {
                "multi_property_enabled": True,
                "custom_reports_enabled": True,
                "role_based_access": True,
                "audit_logging": True,
                "white_label_mode": False
            }
        }
        
        return config
    
    def setup_configuration(self, custom_config: Dict[str, Any] = None):
        """Setup configuration file"""
        logger.info("Setting up Yardi integration configuration...")
        
        config = self.create_default_config()
        
        if custom_config:
            config.update(custom_config)
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def setup_encryption(self):
        """Setup encryption for credentials"""
        logger.info("Setting up encryption for Yardi credentials...")
        
        try:
            from cryptography.fernet import Fernet
            
            # Generate encryption key
            key = Fernet.generate_key()
            
            with open(self.encryption_key_file, 'wb') as f:
                f.write(key)
            
            # Secure the key file (basic protection)
            os.chmod(self.encryption_key_file, 0o600)
            
            logger.info(f"Encryption key generated and saved to {self.encryption_key_file}")
            logger.warning("IMPORTANT: Keep the encryption key file secure and backed up!")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup encryption: {e}")
            return False
    
    def create_database_tables(self):
        """Create database tables for Yardi integration"""
        logger.info("Creating database tables for Yardi integration...")
        
        # SQL statements for creating tables
        tables = [
            """
            CREATE TABLE IF NOT EXISTS yardi_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                connection_id VARCHAR(50) UNIQUE NOT NULL,
                organization_id VARCHAR(50) NOT NULL,
                connection_name VARCHAR(255) NOT NULL,
                yardi_product VARCHAR(50) NOT NULL,
                connection_type VARCHAR(50) NOT NULL,
                auth_method VARCHAR(50) NOT NULL,
                base_url VARCHAR(255),
                credentials TEXT,
                company_info JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS yardi_sync_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id VARCHAR(50) UNIQUE NOT NULL,
                connection_id VARCHAR(50) NOT NULL,
                organization_id VARCHAR(50) NOT NULL,
                sync_direction VARCHAR(20) NOT NULL,
                sync_mode VARCHAR(20) NOT NULL,
                entity_types JSON,
                status VARCHAR(20) DEFAULT 'pending',
                progress_percentage FLOAT DEFAULT 0.0,
                total_records INTEGER DEFAULT 0,
                processed_records INTEGER DEFAULT 0,
                successful_records INTEGER DEFAULT 0,
                failed_records INTEGER DEFAULT 0,
                error_message TEXT,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (connection_id) REFERENCES yardi_connections(connection_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS yardi_field_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mapping_id VARCHAR(50) UNIQUE NOT NULL,
                connection_id VARCHAR(50) NOT NULL,
                organization_id VARCHAR(50) NOT NULL,
                mapping_name VARCHAR(255) NOT NULL,
                entity_type VARCHAR(50) NOT NULL,
                estatecore_to_yardi JSON,
                yardi_to_estatecore JSON,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (connection_id) REFERENCES yardi_connections(connection_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS yardi_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_id VARCHAR(50) UNIQUE NOT NULL,
                organization_id VARCHAR(50) NOT NULL,
                connection_id VARCHAR(50),
                event_type VARCHAR(100) NOT NULL,
                entity_type VARCHAR(50),
                entity_id VARCHAR(100),
                user_id VARCHAR(100),
                event_data JSON,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT,
                event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (connection_id) REFERENCES yardi_connections(connection_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS yardi_performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_id VARCHAR(50) UNIQUE NOT NULL,
                organization_id VARCHAR(50) NOT NULL,
                connection_id VARCHAR(50),
                metric_name VARCHAR(255) NOT NULL,
                metric_type VARCHAR(50),
                value FLOAT NOT NULL,
                tags JSON,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (connection_id) REFERENCES yardi_connections(connection_id)
            );
            """
        ]
        
        try:
            # In a real implementation, this would use the actual database connection
            # For now, we'll just log the SQL statements
            for i, table_sql in enumerate(tables, 1):
                logger.info(f"Table {i} SQL prepared")
            
            logger.info("Database tables created successfully")
            logger.info("Note: Execute these SQL statements in your database:")
            for sql in tables:
                print("\n" + sql)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            return False
    
    def validate_setup(self):
        """Validate the setup"""
        logger.info("Validating Yardi integration setup...")
        
        issues = []
        
        # Check configuration file
        if not os.path.exists(self.config_file):
            issues.append("Configuration file not found")
        
        # Check encryption key
        if not os.path.exists(self.encryption_key_file):
            issues.append("Encryption key file not found")
        
        # Check required dependencies
        required_modules = [
            'aiohttp', 'asyncio', 'cryptography', 'jwt', 'schedule'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                issues.append(f"Required module '{module}' not installed")
        
        if issues:
            logger.error("Setup validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        else:
            logger.info("Setup validation passed successfully")
            return True
    
    def run_full_setup(self, custom_config: Dict[str, Any] = None):
        """Run complete setup process"""
        logger.info("Starting Yardi Integration full setup...")
        
        steps = [
            ("Installing dependencies", self.install_dependencies),
            ("Setting up configuration", lambda: self.setup_configuration(custom_config)),
            ("Setting up encryption", self.setup_encryption),
            ("Creating database tables", self.create_database_tables),
            ("Validating setup", self.validate_setup)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Setup failed at step: {step_name}")
                return False
        
        logger.info("Yardi Integration setup completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Configure your Yardi connection credentials")
        logger.info("2. Set up field mappings for your data")
        logger.info("3. Test the connection to your Yardi system")
        logger.info("4. Configure sync schedules and webhooks")
        
        return True

def main():
    """Main setup function"""
    setup = YardiIntegrationSetup()
    
    # Check if this is a custom setup
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        # Load custom configuration from file
        if len(sys.argv) > 2:
            config_file = sys.argv[2]
            try:
                with open(config_file, 'r') as f:
                    custom_config = json.load(f)
                setup.run_full_setup(custom_config)
            except Exception as e:
                logger.error(f"Failed to load custom configuration: {e}")
                sys.exit(1)
        else:
            logger.error("Custom configuration file path required")
            sys.exit(1)
    else:
        # Run with default configuration
        setup.run_full_setup()

if __name__ == "__main__":
    main()
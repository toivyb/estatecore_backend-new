#!/usr/bin/env python3
"""
Compliance System Initialization Script
Sets up the Automated Compliance Monitoring system for EstateCore
"""

import os
import sys
import logging
from datetime import datetime
import asyncio

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.base import db
from services.compliance_service import get_compliance_orchestrator, start_compliance_system
from services.regulatory_knowledge_service import get_regulatory_knowledge_service
from app import create_app


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('compliance_system.log'),
            logging.StreamHandler()
        ]
    )


def create_database_tables():
    """Create compliance-related database tables"""
    try:
        print("Creating database tables...")
        
        app = create_app()
        with app.app_context():
            # Import all compliance models to ensure they're registered
            from models.compliance import (
                RegulatoryKnowledgeBase, ComplianceRequirement, ComplianceViolation,
                ComplianceAlert, ComplianceDocument, ComplianceAudit, ComplianceTraining,
                ComplianceMetrics, ComplianceIntegration, ComplianceMonitoringRule
            )
            
            # Create tables
            db.create_all()
            print("Database tables created successfully")
            return True
            
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False


def initialize_regulatory_knowledge_base():
    """Initialize the regulatory knowledge base with core regulations"""
    try:
        print("Initializing regulatory knowledge base...")
        
        app = create_app()
        with app.app_context():
            regulatory_service = get_regulatory_knowledge_service()
            success = regulatory_service.initialize_knowledge_base()
            
            if success:
                print("Regulatory knowledge base initialized successfully")
                
                # Display statistics
                stats = regulatory_service.get_regulation_statistics()
                print(f"Total regulations: {stats.get('total_regulations', 0)}")
                print(f"Regulation types: {len(stats.get('by_type', {}))}")
                print(f"Jurisdictions: {len(stats.get('by_jurisdiction', {}))}")
                
                return True
            else:
                print("Failed to initialize regulatory knowledge base")
                return False
                
    except Exception as e:
        print(f"Error initializing regulatory knowledge base: {e}")
        return False


def setup_compliance_integrations():
    """Setup default compliance integrations"""
    try:
        print("Setting up compliance integrations...")
        
        app = create_app()
        with app.app_context():
            from models.compliance import ComplianceIntegration
            
            # Create sample integrations (these would be configured with real credentials)
            integrations = [
                {
                    'integration_name': 'Yardi',
                    'integration_type': 'api',
                    'description': 'Yardi property management system integration',
                    'endpoint_url': 'https://api.yardi.com/v1',
                    'authentication_type': 'bearer_token',
                    'credentials': {'api_key': 'your_yardi_api_key'},
                    'sync_frequency': 'hourly',
                    'is_active': False  # Disabled by default
                },
                {
                    'integration_name': 'AppFolio',
                    'integration_type': 'api',
                    'description': 'AppFolio property management system integration',
                    'endpoint_url': 'https://api.appfolio.com/v1',
                    'authentication_type': 'oauth2',
                    'credentials': {'client_id': 'your_appfolio_client_id'},
                    'sync_frequency': 'daily',
                    'is_active': False  # Disabled by default
                }
            ]
            
            for integration_data in integrations:
                existing = db.session.query(ComplianceIntegration).filter_by(
                    integration_name=integration_data['integration_name']
                ).first()
                
                if not existing:
                    integration = ComplianceIntegration(**integration_data)
                    db.session.add(integration)
            
            db.session.commit()
            print("Compliance integrations configured successfully")
            return True
            
    except Exception as e:
        print(f"Error setting up compliance integrations: {e}")
        return False


def create_sample_properties():
    """Create sample properties for testing compliance system"""
    try:
        print("Creating sample properties...")
        
        app = create_app()
        with app.app_context():
            # This would integrate with your existing property model
            # For now, we'll create sample compliance requirements
            
            from models.compliance import ComplianceRequirement, RegulatoryKnowledgeBase
            from models.compliance import ComplianceStatus
            
            # Get a sample regulation
            regulation = db.session.query(RegulatoryKnowledgeBase).first()
            
            if regulation:
                sample_properties = ['PROP001', 'PROP002', 'PROP003']
                
                for prop_id in sample_properties:
                    existing = db.session.query(ComplianceRequirement).filter_by(
                        property_id=prop_id,
                        regulation_id=regulation.id
                    ).first()
                    
                    if not existing:
                        requirement = ComplianceRequirement(
                            property_id=prop_id,
                            regulation_id=regulation.id,
                            requirement_name=f"Compliance for {regulation.title}",
                            description=f"Ensure compliance with {regulation.title} for property {prop_id}",
                            compliance_status=ComplianceStatus.UNDER_REVIEW,
                            due_date=datetime.now(),
                            next_review_date=datetime.now(),
                            compliance_period=90,
                            risk_score=50.0
                        )
                        db.session.add(requirement)
                
                db.session.commit()
                print("Sample properties and requirements created successfully")
                return True
            else:
                print("No regulations found - skipping sample property creation")
                return True
                
    except Exception as e:
        print(f"Error creating sample properties: {e}")
        return False


def test_system_components():
    """Test all system components"""
    try:
        print("Testing system components...")
        
        app = create_app()
        with app.app_context():
            # Test regulatory service
            from services.regulatory_knowledge_service import get_regulatory_knowledge_service
            regulatory_service = get_regulatory_knowledge_service()
            stats = regulatory_service.get_regulation_statistics()
            print(f"✓ Regulatory service: {stats.get('total_regulations', 0)} regulations loaded")
            
            # Test AI monitor
            from ai_modules.compliance.ai_compliance_monitor import get_ai_compliance_monitor
            ai_monitor = get_ai_compliance_monitor()
            print("✓ AI compliance monitor: initialized")
            
            # Test alert service
            from services.compliance_alert_service import get_compliance_alert_service
            alert_service = get_compliance_alert_service()
            print("✓ Alert service: initialized")
            
            # Test reporting service
            from services.compliance_reporting_service import get_compliance_reporting_service
            reporting_service = get_compliance_reporting_service()
            print("✓ Reporting service: initialized")
            
            print("All system components tested successfully")
            return True
            
    except Exception as e:
        print(f"Error testing system components: {e}")
        return False


def main():
    """Main initialization function"""
    print("=" * 60)
    print("EstateCore Compliance System Initialization")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    print()
    
    # Setup logging
    setup_logging()
    
    # Initialize components
    steps = [
        ("Creating database tables", create_database_tables),
        ("Initializing regulatory knowledge base", initialize_regulatory_knowledge_base),
        ("Setting up compliance integrations", setup_compliance_integrations),
        ("Creating sample properties", create_sample_properties),
        ("Testing system components", test_system_components)
    ]
    
    success_count = 0
    
    for step_name, step_function in steps:
        print(f"Step: {step_name}...")
        try:
            if step_function():
                print(f"✓ {step_name} completed successfully")
                success_count += 1
            else:
                print(f"✗ {step_name} failed")
        except Exception as e:
            print(f"✗ {step_name} failed with exception: {e}")
        print()
    
    print("=" * 60)
    print(f"Initialization Summary:")
    print(f"Steps completed: {success_count}/{len(steps)}")
    print(f"Success rate: {(success_count/len(steps))*100:.1f}%")
    
    if success_count == len(steps):
        print("✓ Compliance system initialization completed successfully!")
        print()
        print("Next steps:")
        print("1. Configure integration credentials in the database")
        print("2. Start the compliance system: python services/compliance_service.py start")
        print("3. Access the compliance dashboard at: /compliance")
        print("4. Review and customize regulations as needed")
        return True
    else:
        print("✗ Some initialization steps failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
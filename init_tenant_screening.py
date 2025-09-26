#!/usr/bin/env python3
"""
Tenant Screening System Initialization Script
Sets up the Predictive Tenant Screening system for EstateCore
"""

import os
import sys
import logging
from datetime import datetime
import asyncio
import pandas as pd
import numpy as np

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.base import db
from ai_modules.tenant_screening.predictive_screening_engine import get_predictive_screening_engine
from services.tenant_screening_service import get_tenant_screening_service
from app import create_app


def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('tenant_screening_system.log'),
            logging.StreamHandler()
        ]
    )


def create_database_tables():
    """Create tenant screening database tables"""
    try:
        print("Creating tenant screening database tables...")
        
        app = create_app()
        with app.app_context():
            # Import all screening models to ensure they're registered
            from models.tenant_screening import (
                TenantApplication, ScreeningResult, CreditAssessment,
                RentalHistoryAnalysis, FraudDetection, RiskProfile, ScreeningMetrics
            )
            
            # Create tables
            db.create_all()
            print("Tenant screening database tables created successfully")
            return True
            
    except Exception as e:
        print(f"Error creating database tables: {e}")
        return False


def generate_training_data():
    """Generate synthetic training data for ML models"""
    try:
        print("Generating synthetic training data...")
        
        # Generate 1000 synthetic applications for training
        np.random.seed(42)  # For reproducible results
        
        n_samples = 1000
        
        # Generate features
        credit_scores = np.random.normal(680, 80, n_samples).clip(300, 850)
        annual_incomes = np.random.exponential(50000, n_samples).clip(15000, 200000)
        employment_lengths = np.random.exponential(18, n_samples).clip(0, 120)
        rental_history_lengths = np.random.exponential(24, n_samples).clip(0, 240)
        previous_evictions = np.random.poisson(0.1, n_samples)
        late_payments = np.random.poisson(0.5, n_samples)
        num_references = np.random.poisson(2.5, n_samples).clip(0, 6)
        debt_to_income_ratios = np.random.beta(2, 5, n_samples)
        monthly_rents = np.random.normal(1500, 400, n_samples).clip(500, 5000)
        
        # Employment types
        employment_types = np.random.choice(
            ['full_time', 'part_time', 'contract', 'self_employed', 'unemployed'], 
            n_samples, 
            p=[0.6, 0.15, 0.1, 0.1, 0.05]
        )
        
        # Calculate income to rent ratios
        income_to_rent_ratios = (annual_incomes / 12) / monthly_rents
        
        # Generate outcomes based on rules (for supervised learning)
        # Base approval probability on multiple factors
        approval_scores = (
            (credit_scores - 300) / 550 * 30 +  # Credit component (0-30)
            np.clip(income_to_rent_ratios, 0, 5) / 5 * 25 +  # Income ratio component (0-25)
            np.clip(employment_lengths, 0, 36) / 36 * 20 +  # Employment stability (0-20)
            np.clip(rental_history_lengths, 0, 60) / 60 * 15 +  # Rental history (0-15)
            (6 - np.clip(previous_evictions, 0, 6)) / 6 * 10  # Eviction penalty (0-10)
        )
        
        # Add some noise and randomness
        approval_scores += np.random.normal(0, 5, n_samples)
        approval_scores = np.clip(approval_scores, 0, 100)
        
        # Convert to binary outcomes
        approval_outcomes = (approval_scores > 65).astype(int)
        
        # Generate fraud labels (low rate)
        fraud_probability = np.where(
            (annual_incomes > 100000) & (employment_lengths < 3), 0.3,
            np.where(debt_to_income_ratios > 0.7, 0.2, 0.05)
        )
        fraud_detected = np.random.binomial(1, fraud_probability)
        
        # Create DataFrame
        training_data = pd.DataFrame({
            'credit_score': credit_scores.astype(int),
            'annual_income': annual_incomes,
            'employment_length_months': employment_lengths.astype(int),
            'rental_history_length': rental_history_lengths.astype(int),
            'previous_evictions': previous_evictions,
            'late_payment_count': late_payments,
            'number_of_references': num_references,
            'debt_to_income_ratio': debt_to_income_ratios,
            'monthly_rent': monthly_rents,
            'employment_type': employment_types,
            'income_to_rent_ratio': income_to_rent_ratios,
            'approval_outcome': approval_outcomes,
            'risk_score': 100 - approval_scores,  # Inverse for risk
            'fraud_detected': fraud_detected
        })
        
        # Add categorical mappings for model training
        categorical_mappings = {
            'housing_history_type': np.random.choice(['rental', 'homeowner', 'first_time'], n_samples, p=[0.7, 0.2, 0.1]),
            'reference_quality': np.random.choice(['excellent', 'good', 'fair', 'poor'], n_samples, p=[0.3, 0.4, 0.2, 0.1]),
            'application_completeness': np.random.choice(['complete', 'incomplete'], n_samples, p=[0.8, 0.2])
        }
        
        for key, values in categorical_mappings.items():
            training_data[key] = values
        
        # Save training data
        training_data.to_csv('tenant_screening_training_data.csv', index=False)
        
        print(f"Generated {n_samples} training samples")
        print(f"Approval rate: {approval_outcomes.mean():.1%}")
        print(f"Fraud rate: {fraud_detected.mean():.1%}")
        
        return training_data
        
    except Exception as e:
        print(f"Error generating training data: {e}")
        return None


def train_ml_models():
    """Train machine learning models"""
    try:
        print("Training machine learning models...")
        
        # Load or generate training data
        if os.path.exists('tenant_screening_training_data.csv'):
            training_data = pd.read_csv('tenant_screening_training_data.csv')
        else:
            training_data = generate_training_data()
            if training_data is None:
                return False
        
        # Get the screening engine
        screening_engine = get_predictive_screening_engine()
        
        # Train the models
        success = screening_engine.train_models(training_data)
        
        if success:
            # Save the trained models
            models_saved = screening_engine.save_models('tenant_screening_models.joblib')
            if models_saved:
                print("Machine learning models trained and saved successfully")
                return True
            else:
                print("Models trained but failed to save")
                return False
        else:
            print("Failed to train machine learning models")
            return False
            
    except Exception as e:
        print(f"Error training ML models: {e}")
        return False


def create_sample_applications():
    """Create sample tenant applications for testing"""
    try:
        print("Creating sample tenant applications...")
        
        app = create_app()
        with app.app_context():
            from models.tenant_screening import TenantApplication, ApplicationStatus
            
            sample_applications = [
                {
                    'property_id': 'PROP001',
                    'applicant_name': 'John Smith',
                    'email': 'john.smith@email.com',
                    'phone_number': '555-0101',
                    'annual_income': 75000,
                    'employment_type': 'full_time',
                    'employment_length_months': 36,
                    'credit_score': 720,
                    'rental_history_length': 48,
                    'previous_evictions': 0,
                    'late_payment_count': 1,
                    'monthly_rent_budget': 2000,
                    'number_of_references': 3,
                    'debt_to_income_ratio': 0.25
                },
                {
                    'property_id': 'PROP002',
                    'applicant_name': 'Sarah Johnson',
                    'email': 'sarah.johnson@email.com',
                    'phone_number': '555-0102',
                    'annual_income': 45000,
                    'employment_type': 'part_time',
                    'employment_length_months': 12,
                    'credit_score': 640,
                    'rental_history_length': 24,
                    'previous_evictions': 1,
                    'late_payment_count': 3,
                    'monthly_rent_budget': 1200,
                    'number_of_references': 2,
                    'debt_to_income_ratio': 0.45
                },
                {
                    'property_id': 'PROP003',
                    'applicant_name': 'Michael Davis',
                    'email': 'michael.davis@email.com',
                    'phone_number': '555-0103',
                    'annual_income': 95000,
                    'employment_type': 'full_time',
                    'employment_length_months': 72,
                    'credit_score': 780,
                    'rental_history_length': 96,
                    'previous_evictions': 0,
                    'late_payment_count': 0,
                    'monthly_rent_budget': 2500,
                    'number_of_references': 4,
                    'debt_to_income_ratio': 0.15
                }
            ]
            
            created_count = 0
            for app_data in sample_applications:
                # Check if application already exists
                existing = db.session.query(TenantApplication).filter_by(
                    email=app_data['email']
                ).first()
                
                if not existing:
                    application = TenantApplication(**app_data)
                    application.status = ApplicationStatus.SUBMITTED.value
                    db.session.add(application)
                    created_count += 1
            
            db.session.commit()
            print(f"Created {created_count} sample applications")
            return True
            
    except Exception as e:
        print(f"Error creating sample applications: {e}")
        return False


def test_screening_system():
    """Test the tenant screening system components"""
    try:
        print("Testing tenant screening system components...")
        
        app = create_app()
        with app.app_context():
            # Test screening engine
            screening_engine = get_predictive_screening_engine()
            
            # Test with sample data
            sample_data = {
                'applicant_name': 'Test Applicant',
                'annual_income': 60000,
                'credit_score': 700,
                'employment_length_months': 24,
                'rental_history_length': 36,
                'previous_evictions': 0,
                'late_payment_count': 0,
                'number_of_references': 3,
                'debt_to_income_ratio': 0.3,
                'monthly_rent': 1500,
                'employment_type': 'full_time'
            }
            
            # Run screening
            screening_score = asyncio.run(screening_engine.screen_applicant(sample_data))
            
            print(f"✓ Screening engine: Overall score {screening_score.overall_score:.1f}")
            print(f"  Risk level: {screening_score.risk_level.value}")
            print(f"  Recommendation: {screening_score.recommendation.value}")
            print(f"  Confidence: {screening_score.confidence:.2f}")
            
            # Test screening service
            screening_service = get_tenant_screening_service()
            print("✓ Tenant screening service: initialized")
            
            print("All system components tested successfully")
            return True
            
    except Exception as e:
        print(f"Error testing system components: {e}")
        return False


def main():
    """Main initialization function"""
    print("=" * 60)
    print("EstateCore Predictive Tenant Screening System Initialization")
    print("=" * 60)
    print(f"Started at: {datetime.now()}")
    print()
    
    # Setup logging
    setup_logging()
    
    # Initialize components
    steps = [
        ("Creating database tables", create_database_tables),
        ("Generating training data", generate_training_data),
        ("Training ML models", train_ml_models),
        ("Creating sample applications", create_sample_applications),
        ("Testing system components", test_screening_system)
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
        print("✓ Tenant screening system initialization completed successfully!")
        print()
        print("Next steps:")
        print("1. Start the EstateCore backend server")
        print("2. Access the tenant screening dashboard at: /tenant-screening")
        print("3. Create new tenant applications and run AI-powered screening")
        print("4. Review screening results and make approval decisions")
        print("5. Monitor system analytics and performance")
        return True
    else:
        print("✗ Some initialization steps failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
"""
Predictive Tenant Screening Engine
AI-powered tenant evaluation and risk assessment system
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from dataclasses import dataclass
from enum import Enum
import joblib
import json
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
import asyncio

from models.base import db
from models.tenant_screening import (
    TenantApplication, ScreeningResult, CreditAssessment, 
    RentalHistoryAnalysis, FraudDetection, RiskProfile
)


logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalRecommendation(Enum):
    APPROVE = "approve"
    CONDITIONAL_APPROVE = "conditional_approve"
    DECLINE = "decline"
    REQUIRE_COSIGNER = "require_cosigner"


@dataclass
class ScreeningScore:
    """Tenant screening score breakdown"""
    overall_score: float
    credit_score: float
    income_score: float
    rental_history_score: float
    employment_score: float
    reference_score: float
    fraud_risk_score: float
    risk_level: RiskLevel
    recommendation: ApprovalRecommendation
    confidence: float


@dataclass
class ScreeningInsights:
    """AI-generated insights about the applicant"""
    strengths: List[str]
    concerns: List[str]
    recommendations: List[str]
    similar_cases: List[Dict[str, Any]]
    probability_of_success: float


class PredictiveTenantScreeningEngine:
    """AI-powered predictive tenant screening engine"""
    
    def __init__(self):
        self.approval_model = None
        self.risk_model = None
        self.fraud_model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.is_trained = False
        
    def train_models(self, training_data: pd.DataFrame) -> bool:
        """Train the predictive models with historical data"""
        try:
            logger.info("Training predictive tenant screening models...")
            
            # Prepare features
            features = self._prepare_features(training_data)
            
            # Approval prediction model
            if 'approval_outcome' in training_data.columns:
                X_approval = features
                y_approval = training_data['approval_outcome']
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X_approval, y_approval, test_size=0.2, random_state=42
                )
                
                self.approval_model = RandomForestClassifier(
                    n_estimators=100, 
                    max_depth=10, 
                    random_state=42,
                    class_weight='balanced'
                )
                self.approval_model.fit(X_train, y_train)
                
                # Evaluate approval model
                y_pred = self.approval_model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                logger.info(f"Approval model accuracy: {accuracy:.3f}")
            
            # Risk prediction model
            if 'risk_score' in training_data.columns:
                X_risk = features
                y_risk = training_data['risk_score']
                
                self.risk_model = GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=6,
                    random_state=42
                )
                self.risk_model.fit(X_risk, y_risk)
                
                logger.info("Risk prediction model trained successfully")
            
            # Fraud detection model
            if 'fraud_detected' in training_data.columns:
                X_fraud = features
                y_fraud = training_data['fraud_detected']
                
                self.fraud_model = RandomForestClassifier(
                    n_estimators=150,
                    max_depth=8,
                    random_state=42,
                    class_weight='balanced'
                )
                self.fraud_model.fit(X_fraud, y_fraud)
                
                logger.info("Fraud detection model trained successfully")
            
            self.is_trained = True
            logger.info("All predictive models trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for ML models"""
        try:
            features = data.copy()
            
            # Numerical features
            numerical_features = [
                'credit_score', 'annual_income', 'monthly_rent',
                'employment_length_months', 'rental_history_length',
                'number_of_references', 'debt_to_income_ratio',
                'savings_months', 'previous_evictions'
            ]
            
            # Categorical features
            categorical_features = [
                'employment_type', 'housing_history_type',
                'reference_quality', 'application_completeness'
            ]
            
            # Handle missing values
            for col in numerical_features:
                if col in features.columns:
                    features[col] = features[col].fillna(features[col].median())
            
            for col in categorical_features:
                if col in features.columns:
                    features[col] = features[col].fillna('unknown')
                    
                    # Label encoding
                    if col not in self.label_encoders:
                        self.label_encoders[col] = LabelEncoder()
                        features[col] = self.label_encoders[col].fit_transform(features[col])
                    else:
                        features[col] = self.label_encoders[col].transform(features[col])
            
            # Feature engineering
            if 'annual_income' in features.columns and 'monthly_rent' in features.columns:
                features['income_to_rent_ratio'] = features['annual_income'] / (features['monthly_rent'] * 12)
            
            if 'credit_score' in features.columns:
                features['credit_score_normalized'] = (features['credit_score'] - 300) / (850 - 300)
            
            # Select features for modeling
            model_features = []
            for col in numerical_features + categorical_features:
                if col in features.columns:
                    model_features.append(col)
            
            # Add engineered features
            if 'income_to_rent_ratio' in features.columns:
                model_features.append('income_to_rent_ratio')
            if 'credit_score_normalized' in features.columns:
                model_features.append('credit_score_normalized')
            
            result = features[model_features]
            
            # Scale numerical features
            numerical_cols = [col for col in model_features if col in numerical_features + ['income_to_rent_ratio', 'credit_score_normalized']]
            if numerical_cols:
                result[numerical_cols] = self.scaler.fit_transform(result[numerical_cols])
            
            return result
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return pd.DataFrame()
    
    async def screen_applicant(self, application_data: Dict[str, Any]) -> ScreeningScore:
        """Perform comprehensive AI-powered screening of tenant applicant"""
        try:
            logger.info(f"Screening applicant: {application_data.get('applicant_name', 'Unknown')}")
            
            if not self.is_trained:
                # Load pre-trained models or use default scoring
                logger.warning("Models not trained, using rule-based scoring")
                return self._rule_based_scoring(application_data)
            
            # Convert to DataFrame for prediction
            df = pd.DataFrame([application_data])
            features = self._prepare_features(df)
            
            # Credit assessment
            credit_score = self._assess_credit_risk(application_data)
            
            # Income assessment  
            income_score = self._assess_income_stability(application_data)
            
            # Rental history assessment
            rental_history_score = self._assess_rental_history(application_data)
            
            # Employment assessment
            employment_score = self._assess_employment(application_data)
            
            # Reference assessment
            reference_score = self._assess_references(application_data)
            
            # Fraud risk assessment
            fraud_risk_score = await self._assess_fraud_risk(application_data, features)
            
            # Calculate overall score (weighted average)
            weights = {
                'credit': 0.25,
                'income': 0.20,
                'rental_history': 0.20,
                'employment': 0.15,
                'references': 0.10,
                'fraud_risk': 0.10
            }
            
            overall_score = (
                credit_score * weights['credit'] +
                income_score * weights['income'] +
                rental_history_score * weights['rental_history'] +
                employment_score * weights['employment'] +
                reference_score * weights['references'] +
                fraud_risk_score * weights['fraud_risk']
            )
            
            # Determine risk level and recommendation
            risk_level, recommendation = self._determine_risk_and_recommendation(
                overall_score, fraud_risk_score, credit_score
            )
            
            # Calculate confidence based on data completeness and model certainty
            confidence = self._calculate_confidence(application_data, features)
            
            return ScreeningScore(
                overall_score=overall_score,
                credit_score=credit_score,
                income_score=income_score,
                rental_history_score=rental_history_score,
                employment_score=employment_score,
                reference_score=reference_score,
                fraud_risk_score=fraud_risk_score,
                risk_level=risk_level,
                recommendation=recommendation,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error screening applicant: {e}")
            # Return default low-confidence score
            return ScreeningScore(
                overall_score=50.0,
                credit_score=50.0,
                income_score=50.0,
                rental_history_score=50.0,
                employment_score=50.0,
                reference_score=50.0,
                fraud_risk_score=50.0,
                risk_level=RiskLevel.HIGH,
                recommendation=ApprovalRecommendation.DECLINE,
                confidence=0.1
            )
    
    def _assess_credit_risk(self, data: Dict[str, Any]) -> float:
        """Assess credit-related risk factors"""
        try:
            credit_score = data.get('credit_score', 600)
            debt_to_income = data.get('debt_to_income_ratio', 0.5)
            payment_history = data.get('payment_history_score', 70)
            
            # Credit score component (0-100)
            if credit_score >= 750:
                score_component = 100
            elif credit_score >= 700:
                score_component = 85
            elif credit_score >= 650:
                score_component = 70
            elif credit_score >= 600:
                score_component = 55
            else:
                score_component = 30
            
            # Debt-to-income component
            if debt_to_income <= 0.2:
                debt_component = 100
            elif debt_to_income <= 0.3:
                debt_component = 85
            elif debt_to_income <= 0.4:
                debt_component = 70
            else:
                debt_component = 40
            
            # Payment history component
            payment_component = min(100, payment_history)
            
            # Weighted average
            final_score = (score_component * 0.6 + debt_component * 0.25 + payment_component * 0.15)
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"Error assessing credit risk: {e}")
            return 50.0
    
    def _assess_income_stability(self, data: Dict[str, Any]) -> float:
        """Assess income stability and adequacy"""
        try:
            annual_income = data.get('annual_income', 50000)
            monthly_rent = data.get('monthly_rent', 1500)
            employment_length = data.get('employment_length_months', 12)
            employment_type = data.get('employment_type', 'full_time')
            
            # Income-to-rent ratio (should be 3:1 or better)
            monthly_income = annual_income / 12
            income_ratio = monthly_income / monthly_rent if monthly_rent > 0 else 0
            
            if income_ratio >= 4:
                ratio_score = 100
            elif income_ratio >= 3:
                ratio_score = 85
            elif income_ratio >= 2.5:
                ratio_score = 60
            else:
                ratio_score = 30
            
            # Employment stability
            if employment_length >= 24:
                stability_score = 100
            elif employment_length >= 12:
                stability_score = 80
            elif employment_length >= 6:
                stability_score = 60
            else:
                stability_score = 40
            
            # Employment type modifier
            type_multiplier = {
                'full_time': 1.0,
                'part_time': 0.8,
                'contract': 0.7,
                'self_employed': 0.6,
                'unemployed': 0.1
            }
            
            multiplier = type_multiplier.get(employment_type, 0.7)
            
            final_score = (ratio_score * 0.7 + stability_score * 0.3) * multiplier
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"Error assessing income stability: {e}")
            return 50.0
    
    def _assess_rental_history(self, data: Dict[str, Any]) -> float:
        """Assess rental history and landlord references"""
        try:
            rental_length = data.get('rental_history_length', 12)
            evictions = data.get('previous_evictions', 0)
            late_payments = data.get('late_payment_count', 0)
            landlord_references = data.get('landlord_reference_quality', 'fair')
            
            # Rental length component
            if rental_length >= 36:
                length_score = 100
            elif rental_length >= 24:
                length_score = 85
            elif rental_length >= 12:
                length_score = 70
            else:
                length_score = 50
            
            # Eviction penalty
            eviction_penalty = min(50, evictions * 25)
            
            # Late payment penalty
            late_penalty = min(30, late_payments * 5)
            
            # Reference quality
            reference_scores = {
                'excellent': 100,
                'good': 85,
                'fair': 70,
                'poor': 40,
                'none': 20
            }
            
            reference_score = reference_scores.get(landlord_references, 50)
            
            final_score = (length_score * 0.4 + reference_score * 0.6) - eviction_penalty - late_penalty
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"Error assessing rental history: {e}")
            return 50.0
    
    def _assess_employment(self, data: Dict[str, Any]) -> float:
        """Assess employment status and stability"""
        try:
            employment_type = data.get('employment_type', 'full_time')
            employment_length = data.get('employment_length_months', 12)
            industry = data.get('industry', 'other')
            job_title = data.get('job_title', '')
            
            # Base score by employment type
            type_scores = {
                'full_time': 90,
                'part_time': 60,
                'contract': 55,
                'self_employed': 50,
                'unemployed': 10,
                'retired': 75,
                'student': 40
            }
            
            base_score = type_scores.get(employment_type, 50)
            
            # Length bonus
            if employment_length >= 36:
                length_bonus = 10
            elif employment_length >= 24:
                length_bonus = 8
            elif employment_length >= 12:
                length_bonus = 5
            else:
                length_bonus = 0
            
            # Industry stability modifier
            stable_industries = ['government', 'healthcare', 'education', 'utilities']
            if industry.lower() in stable_industries:
                industry_bonus = 5
            else:
                industry_bonus = 0
            
            final_score = base_score + length_bonus + industry_bonus
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"Error assessing employment: {e}")
            return 50.0
    
    def _assess_references(self, data: Dict[str, Any]) -> float:
        """Assess quality and quantity of references"""
        try:
            num_references = data.get('number_of_references', 0)
            reference_quality = data.get('reference_quality', 'fair')
            reference_types = data.get('reference_types', [])
            
            # Quantity component
            if num_references >= 3:
                quantity_score = 100
            elif num_references >= 2:
                quantity_score = 80
            elif num_references >= 1:
                quantity_score = 60
            else:
                quantity_score = 20
            
            # Quality component
            quality_scores = {
                'excellent': 100,
                'good': 85,
                'fair': 70,
                'poor': 40,
                'none': 10
            }
            
            quality_score = quality_scores.get(reference_quality, 50)
            
            # Reference type bonus
            valuable_types = ['employer', 'landlord', 'professional']
            type_bonus = len([t for t in reference_types if t in valuable_types]) * 5
            
            final_score = (quantity_score * 0.4 + quality_score * 0.6) + type_bonus
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"Error assessing references: {e}")
            return 50.0
    
    async def _assess_fraud_risk(self, data: Dict[str, Any], features: pd.DataFrame) -> float:
        """Assess fraud risk using AI and heuristics"""
        try:
            fraud_indicators = []
            
            # Check for inconsistencies
            annual_income = data.get('annual_income', 0)
            claimed_savings = data.get('claimed_savings', 0)
            
            # Income vs savings consistency
            if claimed_savings > annual_income * 2:
                fraud_indicators.append("Savings unusually high relative to income")
            
            # Employment consistency
            employment_length = data.get('employment_length_months', 0)
            if employment_length < 3 and annual_income > 100000:
                fraud_indicators.append("High income with very short employment history")
            
            # Contact information patterns
            phone = data.get('phone_number', '')
            email = data.get('email', '')
            
            if phone and len(set(phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', ''))) <= 2:
                fraud_indicators.append("Suspicious phone number pattern")
            
            # Document consistency (would integrate with document verification)
            document_quality = data.get('document_quality_score', 80)
            if document_quality < 50:
                fraud_indicators.append("Poor document quality detected")
            
            # Use fraud model if trained
            fraud_probability = 0.1
            if self.fraud_model is not None and not features.empty:
                try:
                    fraud_probability = self.fraud_model.predict_proba(features)[0][1]
                except Exception as e:
                    logger.warning(f"Fraud model prediction failed: {e}")
            
            # Combine heuristic and model scores
            heuristic_risk = min(100, len(fraud_indicators) * 20)
            model_risk = fraud_probability * 100
            
            final_risk = (heuristic_risk * 0.3 + model_risk * 0.7)
            
            # Convert to score (lower risk = higher score)
            fraud_score = max(0, 100 - final_risk)
            
            return fraud_score
            
        except Exception as e:
            logger.error(f"Error assessing fraud risk: {e}")
            return 50.0
    
    def _determine_risk_and_recommendation(
        self, overall_score: float, fraud_score: float, credit_score: float
    ) -> Tuple[RiskLevel, ApprovalRecommendation]:
        """Determine risk level and approval recommendation"""
        
        # High fraud risk overrides other scores
        if fraud_score < 30:
            return RiskLevel.CRITICAL, ApprovalRecommendation.DECLINE
        
        if overall_score >= 85:
            return RiskLevel.LOW, ApprovalRecommendation.APPROVE
        elif overall_score >= 75:
            return RiskLevel.LOW, ApprovalRecommendation.APPROVE
        elif overall_score >= 65:
            if credit_score >= 70:
                return RiskLevel.MEDIUM, ApprovalRecommendation.CONDITIONAL_APPROVE
            else:
                return RiskLevel.MEDIUM, ApprovalRecommendation.REQUIRE_COSIGNER
        elif overall_score >= 50:
            return RiskLevel.HIGH, ApprovalRecommendation.REQUIRE_COSIGNER
        else:
            return RiskLevel.CRITICAL, ApprovalRecommendation.DECLINE
    
    def _calculate_confidence(self, data: Dict[str, Any], features: pd.DataFrame) -> float:
        """Calculate confidence in the screening decision"""
        try:
            # Data completeness factor
            required_fields = [
                'credit_score', 'annual_income', 'employment_length_months',
                'rental_history_length', 'number_of_references'
            ]
            
            completeness = sum(1 for field in required_fields if data.get(field) is not None) / len(required_fields)
            
            # Model uncertainty factor (if models are trained)
            model_confidence = 0.8  # Default confidence
            
            if self.approval_model is not None and not features.empty:
                try:
                    probabilities = self.approval_model.predict_proba(features)[0]
                    model_confidence = max(probabilities)
                except Exception:
                    pass
            
            # Final confidence
            final_confidence = (completeness * 0.4 + model_confidence * 0.6)
            
            return min(1.0, max(0.1, final_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _rule_based_scoring(self, data: Dict[str, Any]) -> ScreeningScore:
        """Fallback rule-based scoring when models aren't trained"""
        try:
            # Simple rule-based assessment
            credit_score = self._assess_credit_risk(data)
            income_score = self._assess_income_stability(data)
            rental_history_score = self._assess_rental_history(data)
            employment_score = self._assess_employment(data)
            reference_score = self._assess_references(data)
            
            # Basic fraud check
            fraud_score = 80.0  # Default to low fraud risk
            
            # Calculate overall score
            overall_score = (
                credit_score * 0.25 +
                income_score * 0.20 +
                rental_history_score * 0.20 +
                employment_score * 0.15 +
                reference_score * 0.10 +
                fraud_score * 0.10
            )
            
            # Determine risk and recommendation
            risk_level, recommendation = self._determine_risk_and_recommendation(
                overall_score, fraud_score, credit_score
            )
            
            return ScreeningScore(
                overall_score=overall_score,
                credit_score=credit_score,
                income_score=income_score,
                rental_history_score=rental_history_score,
                employment_score=employment_score,
                reference_score=reference_score,
                fraud_risk_score=fraud_score,
                risk_level=risk_level,
                recommendation=recommendation,
                confidence=0.7  # Moderate confidence for rule-based
            )
            
        except Exception as e:
            logger.error(f"Error in rule-based scoring: {e}")
            return ScreeningScore(
                overall_score=50.0,
                credit_score=50.0,
                income_score=50.0,
                rental_history_score=50.0,
                employment_score=50.0,
                reference_score=50.0,
                fraud_risk_score=50.0,
                risk_level=RiskLevel.HIGH,
                recommendation=ApprovalRecommendation.DECLINE,
                confidence=0.3
            )
    
    async def generate_screening_insights(self, application_data: Dict[str, Any], score: ScreeningScore) -> ScreeningInsights:
        """Generate AI-powered insights about the screening decision"""
        try:
            strengths = []
            concerns = []
            recommendations = []
            
            # Analyze strengths
            if score.credit_score >= 80:
                strengths.append("Strong credit profile with good payment history")
            if score.income_score >= 80:
                strengths.append("Stable income that adequately covers rent obligations")
            if score.rental_history_score >= 80:
                strengths.append("Positive rental history with good landlord references")
            if score.employment_score >= 80:
                strengths.append("Stable employment history")
            
            # Analyze concerns
            if score.credit_score < 60:
                concerns.append("Credit score below preferred threshold")
            if score.income_score < 60:
                concerns.append("Income may be insufficient for rent obligations")
            if score.rental_history_score < 60:
                concerns.append("Limited or problematic rental history")
            if score.fraud_risk_score < 70:
                concerns.append("Potential fraud indicators detected")
            
            # Generate recommendations
            if score.recommendation == ApprovalRecommendation.CONDITIONAL_APPROVE:
                recommendations.append("Consider approval with security deposit increase")
                recommendations.append("Require additional documentation verification")
            elif score.recommendation == ApprovalRecommendation.REQUIRE_COSIGNER:
                recommendations.append("Require qualified cosigner for approval")
                recommendations.append("Verify cosigner's financial capacity")
            elif score.recommendation == ApprovalRecommendation.DECLINE:
                recommendations.append("Decline application due to high risk factors")
                recommendations.append("Provide feedback for improvement if legally permissible")
            
            # Find similar cases (simplified - would use ML similarity in production)
            similar_cases = [
                {
                    "case_id": "SC001",
                    "similarity_score": 0.85,
                    "outcome": "approved",
                    "duration": "18 months",
                    "performance": "excellent"
                }
            ]
            
            # Calculate probability of success
            probability_factors = [
                score.credit_score / 100,
                score.income_score / 100,
                score.rental_history_score / 100,
                score.employment_score / 100
            ]
            
            probability_of_success = sum(probability_factors) / len(probability_factors)
            
            return ScreeningInsights(
                strengths=strengths,
                concerns=concerns,
                recommendations=recommendations,
                similar_cases=similar_cases,
                probability_of_success=probability_of_success
            )
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return ScreeningInsights(
                strengths=[],
                concerns=["Error generating insights"],
                recommendations=["Manual review required"],
                similar_cases=[],
                probability_of_success=0.5
            )
    
    def save_models(self, filepath: str) -> bool:
        """Save trained models to disk"""
        try:
            models_data = {
                'approval_model': self.approval_model,
                'risk_model': self.risk_model,
                'fraud_model': self.fraud_model,
                'scaler': self.scaler,
                'label_encoders': self.label_encoders,
                'is_trained': self.is_trained
            }
            
            joblib.dump(models_data, filepath)
            logger.info(f"Models saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving models: {e}")
            return False
    
    def load_models(self, filepath: str) -> bool:
        """Load trained models from disk"""
        try:
            models_data = joblib.load(filepath)
            
            self.approval_model = models_data['approval_model']
            self.risk_model = models_data['risk_model']
            self.fraud_model = models_data['fraud_model']
            self.scaler = models_data['scaler']
            self.label_encoders = models_data['label_encoders']
            self.is_trained = models_data['is_trained']
            
            logger.info(f"Models loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False


# Global instance
_predictive_screening_engine = None


def get_predictive_screening_engine() -> PredictiveTenantScreeningEngine:
    """Get or create the predictive screening engine instance"""
    global _predictive_screening_engine
    if _predictive_screening_engine is None:
        _predictive_screening_engine = PredictiveTenantScreeningEngine()
    return _predictive_screening_engine
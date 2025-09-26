"""
Smart Renewal Prediction Engine
Advanced AI/ML models for predicting tenant renewal behavior and optimizing lease terms
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import joblib
import logging
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, mean_squared_error
import xgboost as xgb
from dataclasses import dataclass, asdict
import json
import pickle
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RenewalPrediction:
    """Data class for renewal prediction results"""
    tenant_id: str
    property_id: str
    lease_id: str
    renewal_probability: float
    churn_risk_score: float
    predicted_lease_terms: Dict[str, Any]
    confidence_score: float
    risk_factors: List[str]
    recommended_actions: List[str]
    optimal_timing: Dict[str, str]
    market_factors: Dict[str, float]
    tenant_satisfaction_score: float
    financial_stability_score: float
    property_attractiveness_score: float
    prediction_date: str
    model_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

@dataclass
class TenantProfile:
    """Comprehensive tenant profile for ML features"""
    tenant_id: str
    demographic_features: Dict[str, Any]
    financial_features: Dict[str, Any]
    behavioral_features: Dict[str, Any]
    satisfaction_features: Dict[str, Any]
    lease_history_features: Dict[str, Any]
    property_interaction_features: Dict[str, Any]
    communication_features: Dict[str, Any]
    maintenance_features: Dict[str, Any]
    payment_features: Dict[str, Any]
    location_preferences: Dict[str, Any]

class SmartRenewalPredictionEngine:
    """
    Advanced ML-powered prediction engine for lease renewals
    """
    
    def __init__(self, model_dir: str = "ai_models/renewal_models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        self.renewal_classifier = None
        self.churn_risk_regressor = None
        self.satisfaction_predictor = None
        self.rent_optimizer = None
        self.neural_network = None
        self.feature_scaler = StandardScaler()
        self.label_encoders = {}
        
        # Model performance metrics
        self.model_metrics = {}
        self.feature_importance = {}
        
        # Load existing models if available
        self._load_models()
    
    def predict_renewal(self, tenant_data: Dict[str, Any], 
                       lease_data: Dict[str, Any],
                       property_data: Dict[str, Any],
                       market_data: Dict[str, Any],
                       historical_data: Optional[Dict[str, Any]] = None) -> RenewalPrediction:
        """
        Generate comprehensive renewal prediction using ensemble ML models
        """
        try:
            # Extract and engineer features
            features = self._extract_features(tenant_data, lease_data, property_data, market_data, historical_data)
            
            # Get base predictions from multiple models
            base_predictions = self._get_base_predictions(features)
            
            # Ensemble prediction combining multiple models
            renewal_probability = self._ensemble_prediction(base_predictions, features)
            
            # Calculate component scores
            satisfaction_score = self._predict_satisfaction(features)
            financial_stability = self._assess_financial_stability(features)
            property_attractiveness = self._calculate_property_score(features)
            
            # Risk assessment
            churn_risk = 1.0 - renewal_probability
            risk_factors = self._identify_risk_factors(features, churn_risk)
            
            # Generate optimal lease terms
            optimal_terms = self._optimize_lease_terms(features, renewal_probability, market_data)
            
            # Calculate confidence score
            confidence = self._calculate_confidence(features, base_predictions)
            
            # Generate recommendations
            recommended_actions = self._generate_recommendations(
                renewal_probability, risk_factors, features, optimal_terms
            )
            
            # Optimal timing strategy
            optimal_timing = self._calculate_optimal_timing(lease_data, renewal_probability)
            
            # Market factors analysis
            market_factors = self._analyze_market_factors(market_data, features)
            
            return RenewalPrediction(
                tenant_id=tenant_data.get('tenant_id', ''),
                property_id=property_data.get('property_id', ''),
                lease_id=lease_data.get('lease_id', ''),
                renewal_probability=round(renewal_probability, 4),
                churn_risk_score=round(churn_risk, 4),
                predicted_lease_terms=optimal_terms,
                confidence_score=round(confidence, 4),
                risk_factors=risk_factors,
                recommended_actions=recommended_actions,
                optimal_timing=optimal_timing,
                market_factors=market_factors,
                tenant_satisfaction_score=round(satisfaction_score, 4),
                financial_stability_score=round(financial_stability, 4),
                property_attractiveness_score=round(property_attractiveness, 4),
                prediction_date=datetime.now().isoformat(),
                model_version=self._get_model_version()
            )
            
        except Exception as e:
            logger.error(f"Error in renewal prediction: {str(e)}")
            # Return safe default prediction
            return self._get_default_prediction(tenant_data, lease_data, property_data)
    
    def batch_predict(self, tenant_portfolio: List[Dict[str, Any]]) -> List[RenewalPrediction]:
        """
        Predict renewals for entire tenant portfolio
        """
        predictions = []
        
        for tenant_package in tenant_portfolio:
            try:
                prediction = self.predict_renewal(
                    tenant_package.get('tenant_data', {}),
                    tenant_package.get('lease_data', {}),
                    tenant_package.get('property_data', {}),
                    tenant_package.get('market_data', {}),
                    tenant_package.get('historical_data', {})
                )
                predictions.append(prediction)
                
            except Exception as e:
                logger.error(f"Error predicting for tenant {tenant_package.get('tenant_data', {}).get('tenant_id', 'unknown')}: {str(e)}")
                continue
        
        return predictions
    
    def train_models(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Train all ML models with historical data
        """
        logger.info("Starting model training...")
        
        try:
            # Prepare features and targets
            X, y_renewal, y_satisfaction, y_churn = self._prepare_training_data(training_data)
            
            # Split data
            X_train, X_test, y_renewal_train, y_renewal_test = train_test_split(
                X, y_renewal, test_size=0.2, random_state=42, stratify=y_renewal
            )
            
            _, _, y_sat_train, y_sat_test = train_test_split(
                X, y_satisfaction, test_size=0.2, random_state=42
            )
            
            _, _, y_churn_train, y_churn_test = train_test_split(
                X, y_churn, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.feature_scaler.fit_transform(X_train)
            X_test_scaled = self.feature_scaler.transform(X_test)
            
            # Train renewal classifier (Random Forest + XGBoost ensemble)
            self.renewal_classifier = self._train_renewal_classifier(X_train_scaled, y_renewal_train)
            
            # Train churn risk regressor
            self.churn_risk_regressor = self._train_churn_regressor(X_train_scaled, y_churn_train)
            
            # Train satisfaction predictor
            self.satisfaction_predictor = self._train_satisfaction_predictor(X_train_scaled, y_sat_train)
            
            # Train neural network for complex patterns
            self.neural_network = self._train_neural_network(X_train_scaled, y_renewal_train)
            
            # Evaluate models
            metrics = self._evaluate_models(X_test_scaled, y_renewal_test, y_sat_test, y_churn_test)
            
            # Calculate feature importance
            self.feature_importance = self._calculate_feature_importance(X.columns)
            
            # Save models
            self._save_models()
            
            logger.info("Model training completed successfully")
            
            return {
                'training_status': 'success',
                'model_metrics': metrics,
                'feature_importance': self.feature_importance,
                'training_samples': len(X_train),
                'test_samples': len(X_test),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in model training: {str(e)}")
            return {
                'training_status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def update_models_incremental(self, new_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Update models with new data (online learning)
        """
        try:
            # Prepare new features
            X_new, y_renewal_new, y_satisfaction_new, y_churn_new = self._prepare_training_data(new_data)
            X_new_scaled = self.feature_scaler.transform(X_new)
            
            # Update models that support incremental learning
            if hasattr(self.neural_network, 'partial_fit'):
                self.neural_network.partial_fit(X_new_scaled, y_renewal_new)
            
            # For other models, retrain with combined data or use online variants
            # This is a simplified approach - in production, you'd want more sophisticated online learning
            
            # Re-evaluate performance
            if len(X_new) > 10:  # Only if we have enough samples
                metrics = self._evaluate_models(X_new_scaled, y_renewal_new, y_satisfaction_new, y_churn_new)
                self.model_metrics.update(metrics)
            
            # Save updated models
            self._save_models()
            
            return {
                'update_status': 'success',
                'new_samples': len(X_new),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in incremental model update: {str(e)}")
            return {
                'update_status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_model_insights(self) -> Dict[str, Any]:
        """
        Get insights about model performance and feature importance
        """
        return {
            'model_metrics': self.model_metrics,
            'feature_importance': self.feature_importance,
            'model_versions': self._get_model_version(),
            'last_training': self._get_last_training_date(),
            'prediction_accuracy': self._get_prediction_accuracy()
        }
    
    # Private methods
    
    def _extract_features(self, tenant_data: Dict, lease_data: Dict, 
                         property_data: Dict, market_data: Dict,
                         historical_data: Optional[Dict] = None) -> pd.DataFrame:
        """
        Extract and engineer features for ML models
        """
        features = {}
        
        # Tenant demographic features
        features['tenant_age'] = tenant_data.get('age', 35)
        features['tenant_income'] = tenant_data.get('monthly_income', 5000)
        features['tenant_credit_score'] = tenant_data.get('credit_score', 700)
        features['employment_length'] = tenant_data.get('employment_length_months', 24)
        features['previous_addresses_count'] = len(tenant_data.get('previous_addresses', []))
        
        # Financial features
        current_rent = lease_data.get('monthly_rent', 1500)
        features['rent_to_income_ratio'] = current_rent / max(features['tenant_income'], 1)
        features['current_rent'] = current_rent
        features['security_deposit'] = lease_data.get('security_deposit', current_rent)
        
        # Payment behavior features
        payment_history = tenant_data.get('payment_history', [])
        if payment_history:
            features['avg_payment_delay_days'] = np.mean([p.get('days_late', 0) for p in payment_history])
            features['on_time_payment_rate'] = sum(1 for p in payment_history if p.get('days_late', 0) == 0) / len(payment_history)
            features['late_payment_count'] = sum(1 for p in payment_history if p.get('days_late', 0) > 5)
            features['payment_consistency'] = 1.0 - np.std([p.get('days_late', 0) for p in payment_history]) / 30.0
        else:
            features['avg_payment_delay_days'] = 0
            features['on_time_payment_rate'] = 0.8  # Default assumption
            features['late_payment_count'] = 0
            features['payment_consistency'] = 0.8
        
        # Lease history features
        features['lease_length_months'] = lease_data.get('lease_length_months', 12)
        features['months_in_current_lease'] = lease_data.get('months_occupied', 12)
        features['lease_renewals_count'] = lease_data.get('renewal_count', 0)
        features['total_tenancy_months'] = tenant_data.get('total_tenancy_months', 12)
        
        # Property features
        features['property_age'] = property_data.get('age_years', 10)
        features['property_size_sqft'] = property_data.get('size_sqft', 1000)
        features['bedrooms'] = property_data.get('bedrooms', 2)
        features['bathrooms'] = property_data.get('bathrooms', 1)
        features['parking_spaces'] = property_data.get('parking_spaces', 1)
        features['amenities_count'] = len(property_data.get('amenities', []))
        
        # Location features
        features['walkability_score'] = property_data.get('walkability_score', 50)
        features['school_rating'] = property_data.get('school_rating', 7)
        features['crime_rate_percentile'] = property_data.get('crime_rate_percentile', 50)
        features['proximity_to_transit'] = property_data.get('transit_distance_miles', 2.0)
        
        # Market features
        features['market_rent'] = market_data.get('average_market_rent', current_rent)
        features['rent_vs_market_ratio'] = current_rent / max(features['market_rent'], 1)
        features['vacancy_rate'] = market_data.get('local_vacancy_rate', 0.05)
        features['market_rent_growth'] = market_data.get('annual_rent_growth', 0.03)
        features['new_supply_ratio'] = market_data.get('new_supply_ratio', 0.02)
        
        # Maintenance and service features
        maintenance_requests = tenant_data.get('maintenance_requests', [])
        if maintenance_requests:
            features['maintenance_requests_count'] = len(maintenance_requests)
            features['avg_response_time_hours'] = np.mean([req.get('response_time_hours', 48) for req in maintenance_requests])
            features['maintenance_satisfaction'] = np.mean([req.get('satisfaction_rating', 3) for req in maintenance_requests])
        else:
            features['maintenance_requests_count'] = 0
            features['avg_response_time_hours'] = 24
            features['maintenance_satisfaction'] = 4.0
        
        # Communication features
        features['communication_responsiveness'] = tenant_data.get('communication_rating', 4.0)
        features['complaint_count'] = tenant_data.get('complaint_count', 0)
        features['lease_violations'] = tenant_data.get('lease_violations', 0)
        
        # Seasonal features
        current_month = datetime.now().month
        features['current_month'] = current_month
        features['is_peak_moving_season'] = 1 if current_month in [5, 6, 7, 8] else 0
        
        # Historical performance features (if available)
        if historical_data:
            features['portfolio_retention_rate'] = historical_data.get('portfolio_retention_rate', 0.85)
            features['property_retention_rate'] = historical_data.get('property_retention_rate', 0.80)
            features['similar_tenant_retention_rate'] = historical_data.get('similar_tenant_retention_rate', 0.75)
        else:
            features['portfolio_retention_rate'] = 0.85
            features['property_retention_rate'] = 0.80
            features['similar_tenant_retention_rate'] = 0.75
        
        # Convert to DataFrame
        return pd.DataFrame([features])
    
    def _get_base_predictions(self, features: pd.DataFrame) -> Dict[str, float]:
        """
        Get predictions from all base models
        """
        features_scaled = self.feature_scaler.transform(features)
        
        predictions = {}
        
        if self.renewal_classifier is not None:
            predictions['random_forest'] = self.renewal_classifier.predict_proba(features_scaled)[0][1]
        
        if self.churn_risk_regressor is not None:
            churn_risk = self.churn_risk_regressor.predict(features_scaled)[0]
            predictions['churn_regressor'] = max(0, min(1, 1.0 - churn_risk))
        
        if self.neural_network is not None:
            predictions['neural_network'] = self.neural_network.predict_proba(features_scaled)[0][1]
        
        # Rule-based prediction as baseline
        predictions['rule_based'] = self._rule_based_prediction(features)
        
        return predictions
    
    def _ensemble_prediction(self, base_predictions: Dict[str, float], features: pd.DataFrame) -> float:
        """
        Combine predictions from multiple models using weighted ensemble
        """
        if not base_predictions:
            return 0.5  # Neutral prediction
        
        # Weights based on model performance (these would be learned from validation data)
        weights = {
            'random_forest': 0.35,
            'churn_regressor': 0.25,
            'neural_network': 0.25,
            'rule_based': 0.15
        }
        
        weighted_prediction = 0
        total_weight = 0
        
        for model, prediction in base_predictions.items():
            weight = weights.get(model, 0.1)
            weighted_prediction += prediction * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_prediction /= total_weight
        
        # Apply confidence-based adjustment
        confidence_adjustment = self._get_confidence_adjustment(features)
        
        return max(0.05, min(0.95, weighted_prediction * confidence_adjustment))
    
    def _rule_based_prediction(self, features: pd.DataFrame) -> float:
        """
        Rule-based prediction as baseline
        """
        feature_row = features.iloc[0]
        
        base_score = 0.7  # Start with moderate probability
        
        # Payment history impact
        if feature_row['on_time_payment_rate'] >= 0.9:
            base_score += 0.15
        elif feature_row['on_time_payment_rate'] <= 0.7:
            base_score -= 0.2
        
        # Rent affordability impact
        if feature_row['rent_to_income_ratio'] <= 0.25:
            base_score += 0.1
        elif feature_row['rent_to_income_ratio'] >= 0.4:
            base_score -= 0.15
        
        # Tenancy length impact
        if feature_row['months_in_current_lease'] >= 24:
            base_score += 0.1
        elif feature_row['months_in_current_lease'] <= 6:
            base_score -= 0.1
        
        # Market competitiveness
        if feature_row['rent_vs_market_ratio'] <= 0.95:
            base_score += 0.1
        elif feature_row['rent_vs_market_ratio'] >= 1.1:
            base_score -= 0.15
        
        # Maintenance satisfaction
        if feature_row['maintenance_satisfaction'] >= 4.0:
            base_score += 0.05
        elif feature_row['maintenance_satisfaction'] <= 2.5:
            base_score -= 0.1
        
        return max(0.1, min(0.9, base_score))
    
    def _predict_satisfaction(self, features: pd.DataFrame) -> float:
        """
        Predict tenant satisfaction score
        """
        if self.satisfaction_predictor is not None:
            features_scaled = self.feature_scaler.transform(features)
            return max(0, min(100, self.satisfaction_predictor.predict(features_scaled)[0]))
        
        # Fallback calculation
        feature_row = features.iloc[0]
        
        satisfaction = 75.0  # Base satisfaction
        
        # Payment behavior impact
        satisfaction += (feature_row['on_time_payment_rate'] - 0.8) * 25
        
        # Maintenance satisfaction
        satisfaction += (feature_row['maintenance_satisfaction'] - 3.0) * 10
        
        # Communication quality
        satisfaction += (feature_row['communication_responsiveness'] - 3.0) * 8
        
        # Property quality indicators
        if feature_row['property_age'] <= 5:
            satisfaction += 10
        elif feature_row['property_age'] >= 20:
            satisfaction -= 5
        
        # Market competitiveness
        if feature_row['rent_vs_market_ratio'] <= 0.95:
            satisfaction += 15
        elif feature_row['rent_vs_market_ratio'] >= 1.05:
            satisfaction -= 10
        
        return max(0, min(100, satisfaction))
    
    def _assess_financial_stability(self, features: pd.DataFrame) -> float:
        """
        Assess tenant's financial stability
        """
        feature_row = features.iloc[0]
        
        stability = 70.0  # Base stability
        
        # Income to rent ratio
        ratio = feature_row['rent_to_income_ratio']
        if ratio <= 0.25:
            stability += 20
        elif ratio <= 0.30:
            stability += 10
        elif ratio >= 0.40:
            stability -= 20
        
        # Employment stability
        if feature_row['employment_length'] >= 24:
            stability += 15
        elif feature_row['employment_length'] <= 6:
            stability -= 15
        
        # Payment consistency
        stability += (feature_row['payment_consistency'] - 0.7) * 30
        
        # Credit score impact
        credit = feature_row['tenant_credit_score']
        if credit >= 750:
            stability += 15
        elif credit >= 700:
            stability += 10
        elif credit <= 600:
            stability -= 20
        
        return max(0, min(100, stability))
    
    def _calculate_property_score(self, features: pd.DataFrame) -> float:
        """
        Calculate property attractiveness score
        """
        feature_row = features.iloc[0]
        
        score = 70.0  # Base attractiveness
        
        # Age factor
        age = feature_row['property_age']
        if age <= 5:
            score += 15
        elif age <= 15:
            score += 5
        elif age >= 25:
            score -= 10
        
        # Size factor
        size = feature_row['property_size_sqft']
        if size >= 1500:
            score += 10
        elif size <= 800:
            score -= 5
        
        # Amenities
        score += feature_row['amenities_count'] * 2
        
        # Location factors
        score += (feature_row['walkability_score'] - 50) * 0.2
        score += (feature_row['school_rating'] - 5) * 3
        score += (50 - feature_row['crime_rate_percentile']) * 0.1
        
        # Parking
        if feature_row['parking_spaces'] >= 1:
            score += 8
        
        return max(0, min(100, score))
    
    def _identify_risk_factors(self, features: pd.DataFrame, churn_risk: float) -> List[str]:
        """
        Identify primary risk factors for churn
        """
        feature_row = features.iloc[0]
        risk_factors = []
        
        if feature_row['on_time_payment_rate'] < 0.8:
            risk_factors.append('poor_payment_history')
        
        if feature_row['rent_to_income_ratio'] > 0.35:
            risk_factors.append('rent_affordability_stress')
        
        if feature_row['rent_vs_market_ratio'] > 1.05:
            risk_factors.append('above_market_rent')
        
        if feature_row['maintenance_satisfaction'] < 3.0:
            risk_factors.append('maintenance_dissatisfaction')
        
        if feature_row['lease_violations'] > 2:
            risk_factors.append('lease_compliance_issues')
        
        if feature_row['complaint_count'] > 3:
            risk_factors.append('frequent_complaints')
        
        if feature_row['vacancy_rate'] > 0.08:
            risk_factors.append('high_market_vacancy')
        
        if feature_row['months_in_current_lease'] < 6:
            risk_factors.append('short_tenancy_period')
        
        return risk_factors
    
    def _optimize_lease_terms(self, features: pd.DataFrame, renewal_prob: float, market_data: Dict) -> Dict[str, Any]:
        """
        Optimize lease terms based on renewal probability and market conditions
        """
        feature_row = features.iloc[0]
        current_rent = feature_row['current_rent']
        market_rent = feature_row['market_rent']
        
        # Determine optimal rent based on renewal probability
        if renewal_prob >= 0.8:  # High probability
            optimal_rent = min(market_rent * 1.02, current_rent * 1.04)
            concessions = []
        elif renewal_prob >= 0.6:  # Medium probability  
            optimal_rent = min(market_rent, current_rent * 1.02)
            concessions = ['minor_upgrade']
        elif renewal_prob >= 0.4:  # Low probability
            optimal_rent = current_rent
            concessions = ['one_month_free', 'minor_upgrade']
        else:  # Very low probability
            optimal_rent = current_rent * 0.98
            concessions = ['two_months_free', 'major_upgrade', 'extended_lease_option']
        
        # Lease length optimization
        if renewal_prob >= 0.7:
            recommended_length = 12  # Standard lease
        else:
            recommended_length = 18  # Longer commitment with incentives
        
        return {
            'recommended_rent': round(optimal_rent, 2),
            'rent_change_percentage': round(((optimal_rent - current_rent) / current_rent) * 100, 2),
            'recommended_lease_length': recommended_length,
            'concessions': concessions,
            'security_deposit': current_rent,  # Standard
            'early_renewal_discount': self._calculate_early_discount(renewal_prob),
            'total_concession_value': self._calculate_concession_value(concessions, current_rent)
        }
    
    def _calculate_confidence(self, features: pd.DataFrame, predictions: Dict[str, float]) -> float:
        """
        Calculate prediction confidence score
        """
        feature_row = features.iloc[0]
        
        # Base confidence from data completeness
        confidence = 0.7
        
        # Increase confidence based on data quality
        if feature_row['total_tenancy_months'] >= 12:
            confidence += 0.1
        
        if len([p for p in predictions.values() if p > 0]) >= 3:
            confidence += 0.1
        
        # Prediction agreement between models
        pred_values = list(predictions.values())
        if pred_values:
            pred_std = np.std(pred_values)
            if pred_std < 0.1:  # Models agree
                confidence += 0.1
            elif pred_std > 0.3:  # Models disagree
                confidence -= 0.1
        
        return max(0.3, min(1.0, confidence))
    
    def _generate_recommendations(self, renewal_prob: float, risk_factors: List[str], 
                                features: pd.DataFrame, optimal_terms: Dict[str, Any]) -> List[str]:
        """
        Generate actionable recommendations
        """
        recommendations = []
        
        if renewal_prob < 0.5:
            recommendations.append('schedule_immediate_retention_meeting')
            recommendations.append('conduct_satisfaction_survey')
        
        if renewal_prob >= 0.7:
            recommendations.append('send_early_renewal_offer')
            recommendations.append('highlight_lease_value_proposition')
        
        # Risk-specific recommendations
        if 'poor_payment_history' in risk_factors:
            recommendations.append('discuss_payment_plan_options')
        
        if 'above_market_rent' in risk_factors:
            recommendations.append('justify_rent_premium_or_adjust')
        
        if 'maintenance_dissatisfaction' in risk_factors:
            recommendations.append('prioritize_outstanding_maintenance')
            recommendations.append('improve_response_time')
        
        if 'rent_affordability_stress' in risk_factors:
            recommendations.append('explore_income_support_programs')
            recommendations.append('consider_rent_adjustment')
        
        return recommendations
    
    def _calculate_optimal_timing(self, lease_data: Dict, renewal_prob: float) -> Dict[str, str]:
        """
        Calculate optimal timing for renewal activities
        """
        lease_end = lease_data.get('lease_end_date')
        if not lease_end:
            return {}
        
        lease_end_date = datetime.fromisoformat(lease_end) if isinstance(lease_end, str) else lease_end
        
        # Adjust timing based on renewal probability
        if renewal_prob >= 0.8:
            days_advance = 90  # Standard timing
        elif renewal_prob >= 0.6:
            days_advance = 120  # Earlier engagement
        else:
            days_advance = 150  # Much earlier for at-risk tenants
        
        initial_contact = lease_end_date - timedelta(days=days_advance)
        formal_offer = lease_end_date - timedelta(days=60)
        final_decision = lease_end_date - timedelta(days=30)
        
        return {
            'initial_contact_date': initial_contact.isoformat(),
            'formal_offer_date': formal_offer.isoformat(),
            'final_decision_date': final_decision.isoformat(),
            'lease_expiration_date': lease_end_date.isoformat()
        }
    
    def _analyze_market_factors(self, market_data: Dict, features: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze market factors affecting renewal decision
        """
        feature_row = features.iloc[0]
        
        return {
            'vacancy_rate_impact': max(-0.2, min(0.2, (0.05 - feature_row['vacancy_rate']) * 2)),
            'rent_growth_pressure': max(-0.15, min(0.15, (feature_row['market_rent_growth'] - 0.03) * 3)),
            'market_competitiveness': max(-0.25, min(0.25, (1.0 - feature_row['rent_vs_market_ratio']) * 0.5)),
            'new_supply_threat': max(-0.1, min(0.1, (0.02 - feature_row['new_supply_ratio']) * 5)),
            'seasonal_factor': self._get_seasonal_factor()
        }
    
    def _get_seasonal_factor(self) -> float:
        """Get seasonal adjustment factor"""
        month = datetime.now().month
        seasonal_adjustments = {
            1: -0.05, 2: -0.05, 3: 0.0, 4: 0.05, 5: 0.1, 6: 0.15,
            7: 0.1, 8: 0.05, 9: 0.0, 10: -0.05, 11: -0.1, 12: -0.1
        }
        return seasonal_adjustments.get(month, 0.0)
    
    def _calculate_early_discount(self, renewal_prob: float) -> float:
        """Calculate early renewal discount percentage"""
        if renewal_prob >= 0.8:
            return 0.01  # 1%
        elif renewal_prob >= 0.6:
            return 0.02  # 2%
        else:
            return 0.03  # 3%
    
    def _calculate_concession_value(self, concessions: List[str], monthly_rent: float) -> float:
        """Calculate total value of concessions"""
        concession_values = {
            'one_month_free': monthly_rent,
            'two_months_free': monthly_rent * 2,
            'minor_upgrade': monthly_rent * 0.5,
            'major_upgrade': monthly_rent * 2.0,
            'extended_lease_option': 0
        }
        
        return sum(concession_values.get(c, 0) for c in concessions)
    
    # Model training methods
    
    def _train_renewal_classifier(self, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Train renewal prediction classifier"""
        # Use Random Forest as primary classifier
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        rf.fit(X_train, y_train)
        return rf
    
    def _train_churn_regressor(self, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Train churn risk regressor"""
        gbr = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        gbr.fit(X_train, y_train)
        return gbr
    
    def _train_satisfaction_predictor(self, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Train satisfaction predictor"""
        # Use XGBoost for satisfaction prediction
        xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        xgb_model.fit(X_train, y_train)
        return xgb_model
    
    def _train_neural_network(self, X_train: np.ndarray, y_train: np.ndarray) -> Any:
        """Train neural network for complex pattern recognition"""
        nn = MLPClassifier(
            hidden_layer_sizes=(50, 30),
            activation='relu',
            solver='adam',
            learning_rate_init=0.001,
            max_iter=500,
            random_state=42
        )
        nn.fit(X_train, y_train)
        return nn
    
    def _prepare_training_data(self, training_data: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training data for model training"""
        # This would extract features and targets from historical data
        # For now, we'll create synthetic preparation logic
        
        # Extract features (this would be the same feature engineering as in _extract_features)
        feature_columns = [col for col in training_data.columns if col not in ['renewed', 'satisfaction_score', 'churn_risk']]
        X = training_data[feature_columns]
        
        # Extract targets
        y_renewal = training_data['renewed'].astype(int)
        y_satisfaction = training_data.get('satisfaction_score', np.random.normal(75, 15, len(training_data)))
        y_churn = training_data.get('churn_risk', 1 - training_data['renewed'])
        
        return X, y_renewal, y_satisfaction, y_churn
    
    def _evaluate_models(self, X_test: np.ndarray, y_renewal_test: np.ndarray, 
                        y_satisfaction_test: np.ndarray, y_churn_test: np.ndarray) -> Dict[str, float]:
        """Evaluate all trained models"""
        metrics = {}
        
        if self.renewal_classifier is not None:
            renewal_pred = self.renewal_classifier.predict(X_test)
            renewal_proba = self.renewal_classifier.predict_proba(X_test)[:, 1]
            metrics['renewal_accuracy'] = accuracy_score(y_renewal_test, renewal_pred)
            metrics['renewal_auc'] = roc_auc_score(y_renewal_test, renewal_proba)
        
        if self.satisfaction_predictor is not None:
            satisfaction_pred = self.satisfaction_predictor.predict(X_test)
            metrics['satisfaction_mse'] = mean_squared_error(y_satisfaction_test, satisfaction_pred)
        
        if self.churn_risk_regressor is not None:
            churn_pred = self.churn_risk_regressor.predict(X_test)
            metrics['churn_mse'] = mean_squared_error(y_churn_test, churn_pred)
        
        self.model_metrics = metrics
        return metrics
    
    def _calculate_feature_importance(self, feature_columns: pd.Index) -> Dict[str, float]:
        """Calculate feature importance across models"""
        importance_dict = {}
        
        if self.renewal_classifier is not None and hasattr(self.renewal_classifier, 'feature_importances_'):
            for i, col in enumerate(feature_columns):
                importance_dict[col] = float(self.renewal_classifier.feature_importances_[i])
        
        return importance_dict
    
    def _save_models(self) -> None:
        """Save all trained models to disk"""
        try:
            # Save models
            if self.renewal_classifier is not None:
                joblib.dump(self.renewal_classifier, self.model_dir / 'renewal_classifier.pkl')
            
            if self.churn_risk_regressor is not None:
                joblib.dump(self.churn_risk_regressor, self.model_dir / 'churn_regressor.pkl')
            
            if self.satisfaction_predictor is not None:
                joblib.dump(self.satisfaction_predictor, self.model_dir / 'satisfaction_predictor.pkl')
            
            if self.neural_network is not None:
                joblib.dump(self.neural_network, self.model_dir / 'neural_network.pkl')
            
            # Save scaler and encoders
            joblib.dump(self.feature_scaler, self.model_dir / 'feature_scaler.pkl')
            joblib.dump(self.label_encoders, self.model_dir / 'label_encoders.pkl')
            
            # Save metadata
            metadata = {
                'model_version': self._get_model_version(),
                'training_date': datetime.now().isoformat(),
                'model_metrics': self.model_metrics,
                'feature_importance': self.feature_importance
            }
            
            with open(self.model_dir / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving models: {str(e)}")
    
    def _load_models(self) -> None:
        """Load existing models from disk"""
        try:
            model_files = {
                'renewal_classifier': self.model_dir / 'renewal_classifier.pkl',
                'churn_regressor': self.model_dir / 'churn_regressor.pkl', 
                'satisfaction_predictor': self.model_dir / 'satisfaction_predictor.pkl',
                'neural_network': self.model_dir / 'neural_network.pkl'
            }
            
            for model_name, model_path in model_files.items():
                if model_path.exists():
                    setattr(self, model_name.replace('regressor', '_regressor').replace('predictor', '_predictor').replace('network', '_network'), 
                           joblib.load(model_path))
            
            # Load scaler and encoders
            scaler_path = self.model_dir / 'feature_scaler.pkl'
            if scaler_path.exists():
                self.feature_scaler = joblib.load(scaler_path)
            
            encoders_path = self.model_dir / 'label_encoders.pkl'
            if encoders_path.exists():
                self.label_encoders = joblib.load(encoders_path)
            
            # Load metadata
            metadata_path = self.model_dir / 'metadata.json'
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    self.model_metrics = metadata.get('model_metrics', {})
                    self.feature_importance = metadata.get('feature_importance', {})
                    
        except Exception as e:
            logger.error(f"Error loading models: {str(e)}")
    
    def _get_model_version(self) -> str:
        """Get current model version"""
        return "1.0.0"
    
    def _get_last_training_date(self) -> Optional[str]:
        """Get last training date"""
        metadata_path = self.model_dir / 'metadata.json'
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get('training_date')
            except:
                pass
        return None
    
    def _get_prediction_accuracy(self) -> Dict[str, float]:
        """Get current prediction accuracy metrics"""
        return self.model_metrics
    
    def _get_confidence_adjustment(self, features: pd.DataFrame) -> float:
        """Calculate confidence adjustment factor"""
        # This would implement confidence-based adjustments
        return 1.0  # Neutral adjustment for now
    
    def _get_default_prediction(self, tenant_data: Dict, lease_data: Dict, property_data: Dict) -> RenewalPrediction:
        """Return safe default prediction when main prediction fails"""
        return RenewalPrediction(
            tenant_id=tenant_data.get('tenant_id', ''),
            property_id=property_data.get('property_id', ''),
            lease_id=lease_data.get('lease_id', ''),
            renewal_probability=0.65,  # Moderate default
            churn_risk_score=0.35,
            predicted_lease_terms={
                'recommended_rent': lease_data.get('monthly_rent', 1500),
                'rent_change_percentage': 3.0,
                'recommended_lease_length': 12,
                'concessions': [],
                'security_deposit': lease_data.get('monthly_rent', 1500)
            },
            confidence_score=0.3,  # Low confidence for default
            risk_factors=['insufficient_data'],
            recommended_actions=['collect_more_tenant_data', 'conduct_satisfaction_survey'],
            optimal_timing={
                'initial_contact_date': (datetime.now() + timedelta(days=60)).isoformat(),
                'formal_offer_date': (datetime.now() + timedelta(days=90)).isoformat(),
                'final_decision_date': (datetime.now() + timedelta(days=120)).isoformat()
            },
            market_factors={},
            tenant_satisfaction_score=65.0,
            financial_stability_score=65.0,
            property_attractiveness_score=65.0,
            prediction_date=datetime.now().isoformat(),
            model_version=self._get_model_version()
        )
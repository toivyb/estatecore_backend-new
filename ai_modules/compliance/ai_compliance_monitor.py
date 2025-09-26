"""
AI-Powered Compliance Monitoring Engine
Uses machine learning and NLP to detect and predict compliance violations
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import json
import re
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import openai
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import spacy
from textblob import TextBlob

from models.compliance import (
    ComplianceViolation, ComplianceRequirement, RegulatoryKnowledgeBase,
    ViolationSeverity, ComplianceStatus, RegulationType
)
from models.base import db


logger = logging.getLogger(__name__)


@dataclass
class ComplianceRisk:
    """Data structure for compliance risk assessment"""
    property_id: str
    regulation_type: RegulationType
    risk_score: float
    risk_factors: List[str]
    confidence: float
    recommendations: List[str]
    predicted_violation_date: Optional[datetime] = None


@dataclass
class ViolationPrediction:
    """Data structure for violation predictions"""
    property_id: str
    violation_type: str
    probability: float
    severity: ViolationSeverity
    confidence: float
    contributing_factors: List[str]
    prevention_actions: List[str]


class NLPProcessor:
    """Natural Language Processing for compliance documents and communications"""
    
    def __init__(self):
        try:
            # Load spaCy model for NLP tasks
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, some features may be limited")
            self.nlp = None
        
        # Initialize sentiment analysis
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )
        except Exception as e:
            logger.warning(f"Could not load sentiment analyzer: {e}")
            self.sentiment_analyzer = None
        
        # Compliance-specific keyword patterns
        self.compliance_patterns = {
            'fair_housing_violations': [
                r'\b(discriminat\w+|bias|preference|no \w+ allowed)\b',
                r'\b(credit score|income requirement) \d+\b',
                r'\b(no pets|no children|adults only)\b'
            ],
            'safety_violations': [
                r'\b(fire hazard|electrical problem|gas leak)\b',
                r'\b(broken|damaged|unsafe|hazardous)\b',
                r'\b(emergency|urgent|immediate attention)\b'
            ],
            'maintenance_violations': [
                r'\b(mold|mildew|water damage|leak)\b',
                r'\b(heating|cooling|hvac) (not working|broken|problem)\b',
                r'\b(pest|insect|rodent|infestation)\b'
            ],
            'accessibility_violations': [
                r'\b(wheelchair access|ada compliance|disability accommodat\w+)\b',
                r'\b(ramp|grab bar|accessible|modification)\b',
                r'\b(service animal|emotional support)\b'
            ]
        }
    
    def extract_compliance_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract compliance-related entities from text"""
        entities = {
            'violations': [],
            'requirements': [],
            'regulations': [],
            'dates': [],
            'locations': [],
            'people': []
        }
        
        if not self.nlp:
            return entities
        
        try:
            doc = self.nlp(text)
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ in ['DATE', 'TIME']:
                    entities['dates'].append(ent.text)
                elif ent.label_ in ['GPE', 'LOC']:
                    entities['locations'].append(ent.text)
                elif ent.label_ == 'PERSON':
                    entities['people'].append(ent.text)
            
            # Extract compliance-specific patterns
            for violation_type, patterns in self.compliance_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        entities['violations'].extend(matches)
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return entities
    
    def analyze_document_compliance(self, document_text: str) -> Dict[str, Any]:
        """Analyze a document for compliance issues"""
        analysis = {
            'compliance_score': 0.0,
            'violations_detected': [],
            'risk_indicators': [],
            'sentiment': 'neutral',
            'urgency_level': 'low',
            'entities': {}
        }
        
        try:
            # Extract entities
            analysis['entities'] = self.extract_compliance_entities(document_text)
            
            # Analyze sentiment
            if self.sentiment_analyzer:
                sentiment_result = self.sentiment_analyzer(document_text[:512])  # Limit text length
                analysis['sentiment'] = sentiment_result[0]['label'].lower()
            
            # Detect potential violations
            violation_score = 0
            for violation_type, patterns in self.compliance_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, document_text, re.IGNORECASE):
                        analysis['violations_detected'].append(violation_type)
                        violation_score += 10
            
            # Calculate compliance score (inverse of violation indicators)
            analysis['compliance_score'] = max(0, 100 - violation_score)
            
            # Determine urgency based on keywords
            urgent_keywords = ['emergency', 'immediate', 'urgent', 'critical', 'violation']
            urgency_score = sum(1 for keyword in urgent_keywords 
                              if keyword.lower() in document_text.lower())
            
            if urgency_score >= 3:
                analysis['urgency_level'] = 'critical'
            elif urgency_score >= 2:
                analysis['urgency_level'] = 'high'
            elif urgency_score >= 1:
                analysis['urgency_level'] = 'medium'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing document compliance: {e}")
            return analysis


class ComplianceMLModels:
    """Machine learning models for compliance monitoring and prediction"""
    
    def __init__(self):
        self.violation_classifier = None
        self.risk_predictor = None
        self.anomaly_detector = None
        self.feature_scaler = StandardScaler()
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        
        # Model paths for persistence
        self.model_paths = {
            'violation_classifier': 'models/compliance_violation_classifier.joblib',
            'risk_predictor': 'models/compliance_risk_predictor.joblib',
            'anomaly_detector': 'models/compliance_anomaly_detector.joblib',
            'feature_scaler': 'models/compliance_feature_scaler.joblib',
            'text_vectorizer': 'models/compliance_text_vectorizer.joblib'
        }
    
    def prepare_features(self, property_data: Dict, historical_data: List[Dict]) -> np.ndarray:
        """Prepare features for ML models"""
        features = []
        
        # Property characteristics
        features.extend([
            property_data.get('unit_count', 0),
            property_data.get('build_year', 2000) - 1900,  # Normalize build year
            1 if property_data.get('affordable_housing_program') else 0,
            property_data.get('occupancy_rate', 0.95),
            property_data.get('average_rent', 0) / 1000,  # Normalize rent
            len(property_data.get('amenities', []))
        ])
        
        # Historical compliance data
        violation_count = len([h for h in historical_data if h.get('type') == 'violation'])
        avg_resolution_time = np.mean([h.get('resolution_days', 0) for h in historical_data]) if historical_data else 0
        
        features.extend([
            violation_count,
            avg_resolution_time,
            len(historical_data)
        ])
        
        # Time-based features
        current_date = datetime.now()
        features.extend([
            current_date.month,
            current_date.quarter,
            1 if current_date.weekday() < 5 else 0  # Weekday vs weekend
        ])
        
        return np.array(features).reshape(1, -1)
    
    def train_violation_classifier(self, training_data: List[Dict]) -> bool:
        """Train the violation classification model"""
        try:
            if len(training_data) < 10:
                logger.warning("Insufficient training data for violation classifier")
                return False
            
            # Prepare training data
            X = []
            y = []
            
            for data in training_data:
                features = self.prepare_features(data['property'], data.get('historical', []))
                X.append(features.flatten())
                y.append(1 if data.get('has_violation', False) else 0)
            
            X = np.array(X)
            y = np.array(y)
            
            # Scale features
            X_scaled = self.feature_scaler.fit_transform(X)
            
            # Train classifier
            self.violation_classifier = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                class_weight='balanced'
            )
            self.violation_classifier.fit(X_scaled, y)
            
            # Save model
            joblib.dump(self.violation_classifier, self.model_paths['violation_classifier'])
            joblib.dump(self.feature_scaler, self.model_paths['feature_scaler'])
            
            logger.info("Violation classifier trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train violation classifier: {e}")
            return False
    
    def train_risk_predictor(self, training_data: List[Dict]) -> bool:
        """Train the compliance risk prediction model"""
        try:
            if len(training_data) < 10:
                logger.warning("Insufficient training data for risk predictor")
                return False
            
            X = []
            y = []
            
            for data in training_data:
                features = self.prepare_features(data['property'], data.get('historical', []))
                X.append(features.flatten())
                y.append(data.get('risk_score', 50.0))  # Risk score 0-100
            
            X = np.array(X)
            y = np.array(y)
            
            X_scaled = self.feature_scaler.fit_transform(X)
            
            # Train risk predictor
            self.risk_predictor = RandomForestClassifier(
                n_estimators=100,
                random_state=42
            )
            
            # Convert continuous risk scores to categories for classification
            y_categorical = np.digitize(y, bins=[0, 25, 50, 75, 100]) - 1
            self.risk_predictor.fit(X_scaled, y_categorical)
            
            joblib.dump(self.risk_predictor, self.model_paths['risk_predictor'])
            
            logger.info("Risk predictor trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train risk predictor: {e}")
            return False
    
    def train_anomaly_detector(self, training_data: List[Dict]) -> bool:
        """Train the anomaly detection model for unusual patterns"""
        try:
            X = []
            
            for data in training_data:
                features = self.prepare_features(data['property'], data.get('historical', []))
                X.append(features.flatten())
            
            X = np.array(X)
            X_scaled = self.feature_scaler.fit_transform(X)
            
            # Train anomaly detector
            self.anomaly_detector = IsolationForest(
                contamination=0.1,  # Expect 10% anomalies
                random_state=42
            )
            self.anomaly_detector.fit(X_scaled)
            
            joblib.dump(self.anomaly_detector, self.model_paths['anomaly_detector'])
            
            logger.info("Anomaly detector trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train anomaly detector: {e}")
            return False
    
    def predict_violation_probability(self, property_data: Dict, historical_data: List[Dict]) -> float:
        """Predict probability of compliance violation"""
        try:
            if not self.violation_classifier:
                self.load_models()
            
            if not self.violation_classifier:
                return 0.5  # Default medium risk if model not available
            
            features = self.prepare_features(property_data, historical_data)
            features_scaled = self.feature_scaler.transform(features)
            
            # Get probability of violation (class 1)
            probabilities = self.violation_classifier.predict_proba(features_scaled)
            return probabilities[0][1] if len(probabilities[0]) > 1 else 0.5
            
        except Exception as e:
            logger.error(f"Error predicting violation probability: {e}")
            return 0.5
    
    def predict_risk_score(self, property_data: Dict, historical_data: List[Dict]) -> float:
        """Predict compliance risk score"""
        try:
            if not self.risk_predictor:
                self.load_models()
            
            if not self.risk_predictor:
                return 50.0  # Default medium risk
            
            features = self.prepare_features(property_data, historical_data)
            features_scaled = self.feature_scaler.transform(features)
            
            # Predict risk category and convert back to score
            risk_category = self.risk_predictor.predict(features_scaled)[0]
            risk_score = (risk_category + 1) * 25  # Convert category to 0-100 scale
            
            return min(max(risk_score, 0), 100)
            
        except Exception as e:
            logger.error(f"Error predicting risk score: {e}")
            return 50.0
    
    def detect_anomalies(self, property_data: Dict, historical_data: List[Dict]) -> bool:
        """Detect anomalous patterns that might indicate compliance issues"""
        try:
            if not self.anomaly_detector:
                self.load_models()
            
            if not self.anomaly_detector:
                return False
            
            features = self.prepare_features(property_data, historical_data)
            features_scaled = self.feature_scaler.transform(features)
            
            # -1 indicates anomaly, 1 indicates normal
            prediction = self.anomaly_detector.predict(features_scaled)
            return prediction[0] == -1
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return False
    
    def load_models(self) -> bool:
        """Load pre-trained models"""
        try:
            self.violation_classifier = joblib.load(self.model_paths['violation_classifier'])
            self.risk_predictor = joblib.load(self.model_paths['risk_predictor'])
            self.anomaly_detector = joblib.load(self.model_paths['anomaly_detector'])
            self.feature_scaler = joblib.load(self.model_paths['feature_scaler'])
            
            logger.info("ML models loaded successfully")
            return True
            
        except FileNotFoundError:
            logger.warning("ML models not found, will use defaults until trained")
            return False
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            return False


class AIComplianceMonitor:
    """Main AI-powered compliance monitoring engine"""
    
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.ml_models = ComplianceMLModels()
        self.session = db.session
        
        # Load existing models
        self.ml_models.load_models()
    
    def analyze_property_compliance(self, property_id: str) -> ComplianceRisk:
        """Comprehensive AI analysis of property compliance risk"""
        try:
            # Get property data (this would come from your property model)
            property_data = self._get_property_data(property_id)
            historical_data = self._get_historical_compliance_data(property_id)
            
            # ML predictions
            violation_probability = self.ml_models.predict_violation_probability(property_data, historical_data)
            risk_score = self.ml_models.predict_risk_score(property_data, historical_data)
            is_anomaly = self.ml_models.detect_anomalies(property_data, historical_data)
            
            # Analyze recent documents and communications
            document_analysis = self._analyze_recent_documents(property_id)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(
                property_data, historical_data, document_analysis, is_anomaly
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(risk_factors, property_data)
            
            # Predict violation date if high risk
            predicted_date = None
            if risk_score > 75:
                predicted_date = self._predict_violation_date(historical_data, violation_probability)
            
            # Determine regulation type with highest risk
            primary_regulation_type = self._get_primary_risk_regulation(property_data, risk_factors)
            
            return ComplianceRisk(
                property_id=property_id,
                regulation_type=primary_regulation_type,
                risk_score=risk_score,
                risk_factors=risk_factors,
                confidence=min(violation_probability * 100, 95),  # Cap confidence at 95%
                recommendations=recommendations,
                predicted_violation_date=predicted_date
            )
            
        except Exception as e:
            logger.error(f"Error analyzing property compliance: {e}")
            # Return default risk assessment
            return ComplianceRisk(
                property_id=property_id,
                regulation_type=RegulationType.FEDERAL_HOUSING,
                risk_score=50.0,
                risk_factors=["Analysis unavailable"],
                confidence=0.0,
                recommendations=["Manual review recommended"]
            )
    
    def detect_potential_violations(self, property_ids: List[str] = None) -> List[ViolationPrediction]:
        """Detect potential violations across properties"""
        predictions = []
        
        try:
            # Get properties to analyze
            if property_ids:
                properties_to_check = property_ids
            else:
                # Get all active properties (this would come from your property model)
                properties_to_check = self._get_all_property_ids()
            
            for property_id in properties_to_check:
                # Analyze each property
                risk_assessment = self.analyze_property_compliance(property_id)
                
                # Convert risk assessment to violation predictions
                if risk_assessment.risk_score > 60:  # Threshold for potential violation
                    # Determine most likely violation types
                    violation_types = self._predict_violation_types(risk_assessment)
                    
                    for violation_type in violation_types:
                        prediction = ViolationPrediction(
                            property_id=property_id,
                            violation_type=violation_type['type'],
                            probability=violation_type['probability'],
                            severity=self._determine_severity(violation_type['probability']),
                            confidence=risk_assessment.confidence,
                            contributing_factors=risk_assessment.risk_factors,
                            prevention_actions=self._get_prevention_actions(violation_type['type'])
                        )
                        predictions.append(prediction)
            
            logger.info(f"Generated {len(predictions)} violation predictions")
            return predictions
            
        except Exception as e:
            logger.error(f"Error detecting potential violations: {e}")
            return []
    
    def analyze_communication_patterns(self, property_id: str, days_back: int = 30) -> Dict[str, Any]:
        """Analyze communication patterns for compliance issues"""
        analysis = {
            'sentiment_trend': 'neutral',
            'complaint_frequency': 0,
            'escalation_indicators': [],
            'compliance_mentions': 0,
            'urgency_level': 'low'
        }
        
        try:
            # Get recent communications (emails, messages, maintenance requests, etc.)
            communications = self._get_recent_communications(property_id, days_back)
            
            if not communications:
                return analysis
            
            # Analyze each communication
            sentiments = []
            complaint_count = 0
            compliance_keywords = 0
            
            for comm in communications:
                text = comm.get('content', '')
                
                # NLP analysis
                doc_analysis = self.nlp_processor.analyze_document_compliance(text)
                
                # Track sentiments
                if doc_analysis['sentiment'] in ['negative', 'NEGATIVE']:
                    sentiments.append(-1)
                elif doc_analysis['sentiment'] in ['positive', 'POSITIVE']:
                    sentiments.append(1)
                else:
                    sentiments.append(0)
                
                # Count complaints and compliance mentions
                if any(word in text.lower() for word in ['complaint', 'problem', 'issue', 'broken']):
                    complaint_count += 1
                
                if any(word in text.lower() for word in ['violation', 'compliance', 'code', 'regulation']):
                    compliance_keywords += 1
                
                # Check for escalation indicators
                if doc_analysis['urgency_level'] in ['high', 'critical']:
                    analysis['escalation_indicators'].append({
                        'type': 'urgent_communication',
                        'date': comm.get('date'),
                        'content_preview': text[:100]
                    })
            
            # Calculate overall sentiment trend
            if sentiments:
                avg_sentiment = np.mean(sentiments)
                if avg_sentiment < -0.3:
                    analysis['sentiment_trend'] = 'negative'
                elif avg_sentiment > 0.3:
                    analysis['sentiment_trend'] = 'positive'
            
            analysis['complaint_frequency'] = complaint_count
            analysis['compliance_mentions'] = compliance_keywords
            
            # Determine overall urgency
            if len(analysis['escalation_indicators']) > 2:
                analysis['urgency_level'] = 'high'
            elif len(analysis['escalation_indicators']) > 0:
                analysis['urgency_level'] = 'medium'
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing communication patterns: {e}")
            return analysis
    
    def train_models_with_new_data(self) -> bool:
        """Retrain ML models with new compliance data"""
        try:
            # Collect training data from database
            training_data = self._collect_training_data()
            
            if len(training_data) < 50:
                logger.warning("Insufficient data for model training")
                return False
            
            # Train models
            success = True
            success &= self.ml_models.train_violation_classifier(training_data)
            success &= self.ml_models.train_risk_predictor(training_data)
            success &= self.ml_models.train_anomaly_detector(training_data)
            
            if success:
                logger.info("ML models retrained successfully")
            else:
                logger.error("Some models failed to train")
            
            return success
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    # Helper methods
    
    def _get_property_data(self, property_id: str) -> Dict:
        """Get property data for analysis"""
        # This would integrate with your property model
        # Placeholder implementation
        return {
            'property_id': property_id,
            'unit_count': 24,
            'build_year': 1985,
            'affordable_housing_program': 'Section 8',
            'occupancy_rate': 0.92,
            'average_rent': 1200,
            'amenities': ['parking', 'laundry'],
            'location': {'state': 'CA', 'city': 'San Francisco'}
        }
    
    def _get_historical_compliance_data(self, property_id: str) -> List[Dict]:
        """Get historical compliance data for property"""
        violations = self.session.query(ComplianceViolation).filter_by(
            property_id=property_id
        ).order_by(ComplianceViolation.detected_date.desc()).limit(50).all()
        
        return [
            {
                'type': 'violation',
                'date': v.detected_date,
                'severity': v.severity.value,
                'resolved': v.is_resolved,
                'resolution_days': (v.resolved_date - v.detected_date).days if v.resolved_date else None
            }
            for v in violations
        ]
    
    def _analyze_recent_documents(self, property_id: str) -> Dict:
        """Analyze recent documents for compliance issues"""
        # This would integrate with document management system
        return {
            'total_documents': 0,
            'compliance_score': 85.0,
            'violations_detected': [],
            'expired_documents': 0
        }
    
    def _identify_risk_factors(
        self, 
        property_data: Dict, 
        historical_data: List[Dict], 
        document_analysis: Dict, 
        is_anomaly: bool
    ) -> List[str]:
        """Identify specific risk factors"""
        risk_factors = []
        
        # Age-based risks
        build_year = property_data.get('build_year', 2000)
        if build_year < 1978:
            risk_factors.append("Pre-1978 construction - lead paint compliance required")
        if build_year < 1990:
            risk_factors.append("Older building - increased maintenance compliance risk")
        
        # Program-specific risks
        if property_data.get('affordable_housing_program'):
            risk_factors.append(f"{property_data['affordable_housing_program']} program compliance requirements")
        
        # Historical pattern risks
        recent_violations = len([h for h in historical_data if h.get('date', datetime.min) > datetime.now() - timedelta(days=365)])
        if recent_violations > 2:
            risk_factors.append(f"{recent_violations} violations in past year")
        
        # Occupancy risks
        occupancy = property_data.get('occupancy_rate', 1.0)
        if occupancy < 0.8:
            risk_factors.append("Low occupancy rate - potential financial stress")
        
        # Anomaly detection
        if is_anomaly:
            risk_factors.append("Unusual pattern detected - requires investigation")
        
        # Document compliance
        if document_analysis.get('expired_documents', 0) > 0:
            risk_factors.append(f"{document_analysis['expired_documents']} expired compliance documents")
        
        return risk_factors
    
    def _generate_recommendations(self, risk_factors: List[str], property_data: Dict) -> List[str]:
        """Generate AI recommendations for compliance improvement"""
        recommendations = []
        
        # Risk factor-specific recommendations
        for factor in risk_factors:
            if "lead paint" in factor.lower():
                recommendations.append("Schedule EPA-certified lead paint inspection and remediation")
            elif "violations in past year" in factor.lower():
                recommendations.append("Implement proactive compliance monitoring program")
            elif "low occupancy" in factor.lower():
                recommendations.append("Review financial stability and maintenance funding")
            elif "expired documents" in factor.lower():
                recommendations.append("Update and renew all expired compliance documents")
            elif "unusual pattern" in factor.lower():
                recommendations.append("Conduct comprehensive compliance audit")
        
        # Program-specific recommendations
        program = property_data.get('affordable_housing_program')
        if program == 'Section 8':
            recommendations.append("Ensure HQS inspection is current and passing")
        elif program == 'LIHTC':
            recommendations.append("Verify income certifications and rent limits")
        
        # Default recommendations if none specific
        if not recommendations:
            recommendations.extend([
                "Review and update compliance documentation",
                "Schedule routine compliance assessment",
                "Ensure staff training on current regulations"
            ])
        
        return recommendations
    
    def _predict_violation_date(self, historical_data: List[Dict], probability: float) -> datetime:
        """Predict when a violation might occur"""
        if not historical_data:
            return datetime.now() + timedelta(days=30)
        
        # Calculate average time between violations
        violation_dates = [h['date'] for h in historical_data if h.get('type') == 'violation']
        if len(violation_dates) > 1:
            avg_interval = sum((violation_dates[i] - violation_dates[i+1]).days 
                             for i in range(len(violation_dates) - 1)) / (len(violation_dates) - 1)
        else:
            avg_interval = 365  # Default to one year
        
        # Adjust based on probability
        predicted_days = avg_interval * (1 - probability)
        return datetime.now() + timedelta(days=max(predicted_days, 7))
    
    def _get_primary_risk_regulation(self, property_data: Dict, risk_factors: List[str]) -> RegulationType:
        """Determine the primary regulation type at risk"""
        # Analyze risk factors to determine most likely violation area
        program = property_data.get('affordable_housing_program')
        
        for factor in risk_factors:
            if "lead paint" in factor.lower():
                return RegulationType.ENVIRONMENTAL_EPA
            elif "fair housing" in factor.lower() or "discrimination" in factor.lower():
                return RegulationType.FAIR_HOUSING
            elif "accessibility" in factor.lower() or "ada" in factor.lower():
                return RegulationType.ACCESSIBILITY_ADA
        
        # Default based on property program
        if program == 'Section 8':
            return RegulationType.SECTION_8
        elif program == 'LIHTC':
            return RegulationType.LIHTC
        else:
            return RegulationType.FEDERAL_HOUSING
    
    def _predict_violation_types(self, risk_assessment: ComplianceRisk) -> List[Dict]:
        """Predict specific types of violations that might occur"""
        violation_types = []
        
        # Base probability from risk score
        base_probability = risk_assessment.risk_score / 100
        
        # Analyze risk factors for specific violation types
        for factor in risk_assessment.risk_factors:
            if "lead paint" in factor.lower():
                violation_types.append({
                    'type': 'Environmental EPA Violation',
                    'probability': min(base_probability + 0.2, 0.95)
                })
            elif "discrimination" in factor.lower():
                violation_types.append({
                    'type': 'Fair Housing Violation',
                    'probability': min(base_probability + 0.3, 0.95)
                })
            elif "maintenance" in factor.lower():
                violation_types.append({
                    'type': 'Housing Quality Standards Violation',
                    'probability': min(base_probability + 0.15, 0.95)
                })
        
        # Default violation type if none specific
        if not violation_types:
            violation_types.append({
                'type': 'General Compliance Violation',
                'probability': base_probability
            })
        
        return violation_types
    
    def _determine_severity(self, probability: float) -> ViolationSeverity:
        """Determine violation severity based on probability"""
        if probability >= 0.8:
            return ViolationSeverity.CRITICAL
        elif probability >= 0.6:
            return ViolationSeverity.HIGH
        elif probability >= 0.4:
            return ViolationSeverity.MEDIUM
        else:
            return ViolationSeverity.LOW
    
    def _get_prevention_actions(self, violation_type: str) -> List[str]:
        """Get prevention actions for specific violation types"""
        action_map = {
            'Environmental EPA Violation': [
                'Schedule EPA-certified lead inspection',
                'Implement lead-safe work practices',
                'Update lead disclosure forms'
            ],
            'Fair Housing Violation': [
                'Review tenant screening criteria',
                'Conduct fair housing training',
                'Update rental policies and procedures'
            ],
            'Housing Quality Standards Violation': [
                'Schedule comprehensive property inspection',
                'Address deferred maintenance items',
                'Update preventive maintenance schedule'
            ]
        }
        
        return action_map.get(violation_type, [
            'Conduct compliance assessment',
            'Review relevant regulations',
            'Implement corrective actions'
        ])
    
    def _get_all_property_ids(self) -> List[str]:
        """Get all property IDs for analysis"""
        # This would integrate with your property model
        # Placeholder implementation
        return ['prop_1', 'prop_2', 'prop_3']
    
    def _get_recent_communications(self, property_id: str, days_back: int) -> List[Dict]:
        """Get recent communications for property"""
        # This would integrate with your communication/message system
        # Placeholder implementation
        return []
    
    def _collect_training_data(self) -> List[Dict]:
        """Collect training data from database"""
        # This would collect historical compliance data for training
        # Placeholder implementation
        return []


# Global service instance
_ai_compliance_monitor = None


def get_ai_compliance_monitor() -> AIComplianceMonitor:
    """Get or create the AI compliance monitor instance"""
    global _ai_compliance_monitor
    if _ai_compliance_monitor is None:
        _ai_compliance_monitor = AIComplianceMonitor()
    return _ai_compliance_monitor
#!/usr/bin/env python3
"""
Advanced Document Processing System for EstateCore Phase 6
Natural Language Processing for lease agreements, contracts, and property documents
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Try importing NLP libraries with fallbacks
try:
    import spacy
    # Try to load English model
    try:
        nlp = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except OSError:
        SPACY_AVAILABLE = False
        print("spaCy English model not available, using simplified NLP")
except ImportError:
    SPACY_AVAILABLE = False
    print("spaCy not available, using rule-based text processing")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    NLTK_AVAILABLE = True
    
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('vader_lexicon')
        nltk.data.find('corpora/wordnet')
    except LookupError:
        print("Downloading NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('wordnet', quiet=True)
        
except ImportError:
    NLTK_AVAILABLE = False
    print("NLTK not available, using basic text processing")

class DocumentType(Enum):
    LEASE_AGREEMENT = "lease_agreement"
    RENTAL_APPLICATION = "rental_application"
    MAINTENANCE_REQUEST = "maintenance_request"
    INSPECTION_REPORT = "inspection_report"
    LEGAL_NOTICE = "legal_notice"
    INSURANCE_DOCUMENT = "insurance_document"
    PROPERTY_DEED = "property_deed"
    HOA_DOCUMENT = "hoa_document"
    TENANT_COMMUNICATION = "tenant_communication"
    VENDOR_CONTRACT = "vendor_contract"
    UNKNOWN = "unknown"

class ExtractionConfidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class ExtractedEntity:
    """Extracted named entity from document"""
    text: str
    entity_type: str
    confidence: float
    start_pos: int
    end_pos: int
    context: str
    normalized_value: Optional[str] = None

@dataclass
class ExtractedDate:
    """Extracted date information"""
    text: str
    parsed_date: datetime
    date_type: str  # lease_start, lease_end, due_date, etc.
    confidence: float
    context: str

@dataclass
class ExtractedAmount:
    """Extracted monetary amount"""
    text: str
    amount: float
    currency: str
    amount_type: str  # rent, deposit, fee, etc.
    confidence: float
    context: str

@dataclass
class ExtractedClause:
    """Extracted legal/contract clause"""
    clause_type: str
    text: str
    importance: str  # low, medium, high, critical
    risk_level: str
    summary: str
    position: Tuple[int, int]  # start, end character positions

@dataclass
class DocumentAnalysis:
    """Complete document analysis result"""
    document_id: str
    document_type: DocumentType
    confidence: ExtractionConfidence
    processing_time: float
    text_length: int
    language: str
    
    # Extracted information
    entities: List[ExtractedEntity]
    dates: List[ExtractedDate]
    amounts: List[ExtractedAmount]
    clauses: List[ExtractedClause]
    
    # Analysis results
    sentiment_score: float
    readability_score: float
    complexity_score: float
    legal_risk_score: float
    
    # Key information summary
    key_terms: Dict[str, Any]
    summary: str
    recommendations: List[str]
    warnings: List[str]
    
    # Metadata
    processed_at: datetime
    processor_version: str

class DocumentProcessor:
    """Advanced document processing and analysis system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.spacy_available = SPACY_AVAILABLE
        self.nltk_available = NLTK_AVAILABLE
        
        # Initialize NLP components
        if self.nltk_available:
            self.sentiment_analyzer = SentimentIntensityAnalyzer()
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))
        
        # Load document templates and patterns
        self.document_patterns = self._load_document_patterns()
        self.extraction_rules = self._load_extraction_rules()
        self.legal_terms_database = self._load_legal_terms()
        
        self.logger.info(f"DocumentProcessor initialized - spaCy: {SPACY_AVAILABLE}, NLTK: {NLTK_AVAILABLE}")

    def _load_document_patterns(self) -> Dict:
        """Load document type identification patterns"""
        return {
            DocumentType.LEASE_AGREEMENT: {
                'keywords': ['lease', 'tenant', 'landlord', 'rent', 'premises', 'term of lease'],
                'required_fields': ['tenant_name', 'monthly_rent', 'lease_term'],
                'patterns': [
                    r'lease agreement',
                    r'residential lease',
                    r'rental agreement',
                    r'month-to-month'
                ]
            },
            DocumentType.RENTAL_APPLICATION: {
                'keywords': ['application', 'applicant', 'employment', 'references', 'income'],
                'required_fields': ['applicant_name', 'employment_info', 'income'],
                'patterns': [
                    r'rental application',
                    r'tenant application',
                    r'application to lease'
                ]
            },
            DocumentType.MAINTENANCE_REQUEST: {
                'keywords': ['repair', 'maintenance', 'issue', 'problem', 'broken', 'fix'],
                'required_fields': ['issue_description', 'location', 'urgency'],
                'patterns': [
                    r'maintenance request',
                    r'repair request',
                    r'work order'
                ]
            },
            DocumentType.INSPECTION_REPORT: {
                'keywords': ['inspection', 'condition', 'report', 'findings', 'checklist'],
                'required_fields': ['inspection_date', 'inspector', 'findings'],
                'patterns': [
                    r'inspection report',
                    r'property inspection',
                    r'condition report'
                ]
            }
        }

    def _load_extraction_rules(self) -> Dict:
        """Load information extraction rules"""
        return {
            'dates': {
                'patterns': [
                    r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
                    r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
                    r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                    r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
                ],
                'context_keywords': {
                    'lease_start': ['commence', 'begin', 'start', 'effective'],
                    'lease_end': ['expire', 'terminate', 'end', 'expiration'],
                    'due_date': ['due', 'payment', 'rent due'],
                    'inspection_date': ['inspected', 'inspection date', 'examined']
                }
            },
            'amounts': {
                'patterns': [
                    r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # $1,000.00
                    r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*dollars?\b',  # 1000 dollars
                    r'\b(?:USD|usd)\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?\b'  # USD1000
                ],
                'context_keywords': {
                    'rent': ['monthly rent', 'rent', 'rental amount'],
                    'deposit': ['security deposit', 'deposit', 'damage deposit'],
                    'fee': ['fee', 'charge', 'cost', 'expense'],
                    'penalty': ['penalty', 'late fee', 'fine']
                }
            },
            'entities': {
                'person_patterns': [
                    r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Last
                    r'\b[A-Z][a-z]+\s+[A-Z]\.\s*[A-Z][a-z]+\b'  # First M. Last
                ],
                'address_patterns': [
                    r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Boulevard|Blvd|Lane|Ln|Circle|Cir|Court|Ct|Place|Pl)',
                    r'\b\d+\s+[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b'
                ],
                'phone_patterns': [
                    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',
                    r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}\b'
                ],
                'email_patterns': [
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                ]
            }
        }

    def _load_legal_terms(self) -> Dict:
        """Load legal terms and clause analysis database"""
        return {
            'high_risk_clauses': [
                'arbitration', 'waiver', 'indemnification', 'liquidated damages',
                'attorney fees', 'non-disclosure', 'non-compete', 'force majeure'
            ],
            'important_lease_terms': [
                'rent escalation', 'renewal option', 'early termination',
                'maintenance responsibility', 'utilities', 'parking',
                'pet policy', 'smoking policy', 'guest policy'
            ],
            'compliance_keywords': [
                'fair housing', 'ada compliance', 'lead paint', 'asbestos',
                'equal opportunity', 'discrimination', 'reasonable accommodation'
            ],
            'financial_terms': [
                'late fee', 'security deposit', 'application fee', 'pet deposit',
                'cleaning fee', 'key deposit', 'utility deposit'
            ]
        }

    def process_document(self, text: str, document_id: str = None) -> DocumentAnalysis:
        """
        Process document text and extract structured information
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Processing document: {document_id}")
            
            if not text or len(text.strip()) < 10:
                raise ValueError("Document text is too short or empty")
            
            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text)
            
            # Identify document type
            doc_type, type_confidence = self._identify_document_type(cleaned_text)
            
            # Extract information using available NLP libraries
            if self.spacy_available:
                entities = self._extract_entities_spacy(cleaned_text)
            else:
                entities = self._extract_entities_rules(cleaned_text)
            
            # Extract dates, amounts, and clauses
            dates = self._extract_dates(cleaned_text)
            amounts = self._extract_amounts(cleaned_text)
            clauses = self._extract_clauses(cleaned_text, doc_type)
            
            # Perform analysis
            sentiment_score = self._analyze_sentiment(cleaned_text)
            readability_score = self._calculate_readability(cleaned_text)
            complexity_score = self._calculate_complexity(cleaned_text)
            legal_risk_score = self._assess_legal_risk(clauses, cleaned_text)
            
            # Generate key terms summary
            key_terms = self._extract_key_terms(cleaned_text, doc_type, entities, dates, amounts)
            
            # Generate summary and recommendations
            summary = self._generate_summary(cleaned_text, doc_type, key_terms)
            recommendations = self._generate_recommendations(doc_type, clauses, legal_risk_score)
            warnings = self._generate_warnings(clauses, legal_risk_score, amounts)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create analysis result
            analysis = DocumentAnalysis(
                document_id=document_id or f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                document_type=doc_type,
                confidence=type_confidence,
                processing_time=processing_time,
                text_length=len(cleaned_text),
                language="en",  # Assume English for now
                entities=entities,
                dates=dates,
                amounts=amounts,
                clauses=clauses,
                sentiment_score=sentiment_score,
                readability_score=readability_score,
                complexity_score=complexity_score,
                legal_risk_score=legal_risk_score,
                key_terms=key_terms,
                summary=summary,
                recommendations=recommendations,
                warnings=warnings,
                processed_at=datetime.now(),
                processor_version="1.0.0"
            )
            
            self.logger.info(f"Document processing completed in {processing_time:.2f}s - "
                           f"Type: {doc_type.value}, Entities: {len(entities)}, "
                           f"Risk Score: {legal_risk_score:.1f}")
            
            return analysis
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            error_msg = f"Document processing failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Return error analysis
            return DocumentAnalysis(
                document_id=document_id or "error_doc",
                document_type=DocumentType.UNKNOWN,
                confidence=ExtractionConfidence.LOW,
                processing_time=processing_time,
                text_length=len(text) if text else 0,
                language="en",
                entities=[],
                dates=[],
                amounts=[],
                clauses=[],
                sentiment_score=0.0,
                readability_score=0.0,
                complexity_score=0.0,
                legal_risk_score=0.0,
                key_terms={},
                summary=f"Processing failed: {str(e)}",
                recommendations=[],
                warnings=[error_msg],
                processed_at=datetime.now(),
                processor_version="1.0.0"
            )

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess document text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\$\(\)\/\@]', '', text)
        
        # Fix common OCR errors (if text came from image)
        text = text.replace('|', 'I')  # Pipe to I
        text = text.replace('0', 'O')  # Zero to O in some contexts
        
        return text.strip()

    def _identify_document_type(self, text: str) -> Tuple[DocumentType, ExtractionConfidence]:
        """Identify the type of document based on content"""
        text_lower = text.lower()
        type_scores = {}
        
        # Score each document type based on keyword presence
        for doc_type, patterns in self.document_patterns.items():
            score = 0
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword.lower() in text_lower:
                    score += 2
            
            # Check regex patterns
            for pattern in patterns.get('patterns', []):
                if re.search(pattern, text_lower):
                    score += 5
            
            # Check for required fields (estimate presence)
            for field in patterns['required_fields']:
                if self._estimate_field_presence(text_lower, field):
                    score += 3
            
            type_scores[doc_type] = score
        
        # Determine best match
        if not type_scores or max(type_scores.values()) == 0:
            return DocumentType.UNKNOWN, ExtractionConfidence.LOW
        
        best_type = max(type_scores, key=type_scores.get)
        best_score = type_scores[best_type]
        
        # Determine confidence based on score
        if best_score >= 15:
            confidence = ExtractionConfidence.VERY_HIGH
        elif best_score >= 10:
            confidence = ExtractionConfidence.HIGH
        elif best_score >= 5:
            confidence = ExtractionConfidence.MEDIUM
        else:
            confidence = ExtractionConfidence.LOW
        
        return best_type, confidence

    def _estimate_field_presence(self, text: str, field: str) -> bool:
        """Estimate if a required field is present in text"""
        field_indicators = {
            'tenant_name': ['tenant', 'lessee', 'renter'],
            'monthly_rent': ['rent', '$', 'monthly', 'payment'],
            'lease_term': ['term', 'month', 'year', 'period'],
            'applicant_name': ['applicant', 'name', 'tenant'],
            'employment_info': ['employment', 'employer', 'job', 'occupation'],
            'income': ['income', 'salary', 'wages', '$'],
            'issue_description': ['repair', 'broken', 'issue', 'problem'],
            'location': ['apartment', 'unit', 'room', 'address'],
            'urgency': ['urgent', 'emergency', 'priority'],
            'inspection_date': ['inspection', 'date', 'examined'],
            'inspector': ['inspector', 'examined by', 'conducted by'],
            'findings': ['condition', 'found', 'observed', 'noted']
        }
        
        indicators = field_indicators.get(field, [field])
        return any(indicator in text for indicator in indicators)

    def _extract_entities_spacy(self, text: str) -> List[ExtractedEntity]:
        """Extract named entities using spaCy"""
        entities = []
        
        try:
            doc = nlp(text)
            
            for ent in doc.ents:
                # Map spaCy entity types to our types
                entity_type = self._map_spacy_entity_type(ent.label_)
                
                if entity_type:  # Only include relevant entity types
                    entities.append(ExtractedEntity(
                        text=ent.text,
                        entity_type=entity_type,
                        confidence=0.8,  # spaCy doesn't provide confidence scores directly
                        start_pos=ent.start_char,
                        end_pos=ent.end_char,
                        context=self._get_entity_context(text, ent.start_char, ent.end_char),
                        normalized_value=self._normalize_entity_value(ent.text, entity_type)
                    ))
        
        except Exception as e:
            self.logger.error(f"spaCy entity extraction error: {str(e)}")
        
        return entities

    def _extract_entities_rules(self, text: str) -> List[ExtractedEntity]:
        """Extract entities using rule-based patterns"""
        entities = []
        
        try:
            entity_rules = self.extraction_rules['entities']
            
            # Extract persons
            for pattern in entity_rules['person_patterns']:
                for match in re.finditer(pattern, text):
                    entities.append(ExtractedEntity(
                        text=match.group(),
                        entity_type='PERSON',
                        confidence=0.7,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=self._get_entity_context(text, match.start(), match.end()),
                        normalized_value=match.group().title()
                    ))
            
            # Extract addresses
            for pattern in entity_rules['address_patterns']:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(ExtractedEntity(
                        text=match.group(),
                        entity_type='ADDRESS',
                        confidence=0.8,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=self._get_entity_context(text, match.start(), match.end()),
                        normalized_value=match.group().title()
                    ))
            
            # Extract phone numbers
            for pattern in entity_rules['phone_patterns']:
                for match in re.finditer(pattern, text):
                    entities.append(ExtractedEntity(
                        text=match.group(),
                        entity_type='PHONE',
                        confidence=0.9,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=self._get_entity_context(text, match.start(), match.end()),
                        normalized_value=re.sub(r'[^\d]', '', match.group())
                    ))
            
            # Extract emails
            for pattern in entity_rules['email_patterns']:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    entities.append(ExtractedEntity(
                        text=match.group(),
                        entity_type='EMAIL',
                        confidence=0.95,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        context=self._get_entity_context(text, match.start(), match.end()),
                        normalized_value=match.group().lower()
                    ))
        
        except Exception as e:
            self.logger.error(f"Rule-based entity extraction error: {str(e)}")
        
        return entities

    def _extract_dates(self, text: str) -> List[ExtractedDate]:
        """Extract date information from text"""
        dates = []
        
        try:
            date_patterns = self.extraction_rules['dates']['patterns']
            context_keywords = self.extraction_rules['dates']['context_keywords']
            
            for pattern in date_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    date_text = match.group()
                    
                    # Try to parse the date
                    parsed_date = self._parse_date(date_text)
                    if parsed_date:
                        # Determine date type from context
                        date_type = self._classify_date_type(text, match.start(), context_keywords)
                        
                        dates.append(ExtractedDate(
                            text=date_text,
                            parsed_date=parsed_date,
                            date_type=date_type,
                            confidence=0.8,
                            context=self._get_entity_context(text, match.start(), match.end())
                        ))
        
        except Exception as e:
            self.logger.error(f"Date extraction error: {str(e)}")
        
        return dates

    def _extract_amounts(self, text: str) -> List[ExtractedAmount]:
        """Extract monetary amounts from text"""
        amounts = []
        
        try:
            amount_patterns = self.extraction_rules['amounts']['patterns']
            context_keywords = self.extraction_rules['amounts']['context_keywords']
            
            for pattern in amount_patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    amount_text = match.group()
                    
                    # Parse the amount
                    parsed_amount = self._parse_amount(amount_text)
                    if parsed_amount:
                        # Determine amount type from context
                        amount_type = self._classify_amount_type(text, match.start(), context_keywords)
                        
                        amounts.append(ExtractedAmount(
                            text=amount_text,
                            amount=parsed_amount,
                            currency='USD',
                            amount_type=amount_type,
                            confidence=0.9,
                            context=self._get_entity_context(text, match.start(), match.end())
                        ))
        
        except Exception as e:
            self.logger.error(f"Amount extraction error: {str(e)}")
        
        return amounts

    def _extract_clauses(self, text: str, doc_type: DocumentType) -> List[ExtractedClause]:
        """Extract important clauses and terms from document"""
        clauses = []
        
        try:
            # Split text into sentences/paragraphs for clause analysis
            if self.nltk_available:
                sentences = sent_tokenize(text)
            else:
                sentences = re.split(r'[.!?]+', text)
            
            current_pos = 0
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:  # Skip very short sentences
                    current_pos += len(sentence) + 1
                    continue
                
                # Analyze sentence for important clauses
                clause_analysis = self._analyze_sentence_for_clauses(sentence, doc_type)
                
                if clause_analysis:
                    clause_type, importance, risk_level, summary = clause_analysis
                    
                    clauses.append(ExtractedClause(
                        clause_type=clause_type,
                        text=sentence,
                        importance=importance,
                        risk_level=risk_level,
                        summary=summary,
                        position=(current_pos, current_pos + len(sentence))
                    ))
                
                current_pos += len(sentence) + 1
        
        except Exception as e:
            self.logger.error(f"Clause extraction error: {str(e)}")
        
        return clauses

    def _analyze_sentiment(self, text: str) -> float:
        """Analyze document sentiment"""
        if self.nltk_available:
            try:
                scores = self.sentiment_analyzer.polarity_scores(text)
                return scores['compound']  # Range: -1 to 1
            except Exception as e:
                self.logger.error(f"Sentiment analysis error: {str(e)}")
        
        # Fallback simple sentiment analysis
        positive_words = ['good', 'excellent', 'satisfied', 'agree', 'accept', 'approved']
        negative_words = ['bad', 'poor', 'unsatisfied', 'disagree', 'reject', 'denied', 'breach']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text_lower.split())
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / max(total_words / 100, 1)
        return max(-1.0, min(1.0, sentiment))

    def _calculate_readability(self, text: str) -> float:
        """Calculate document readability score (simplified Flesch Reading Ease)"""
        try:
            sentences = len(re.split(r'[.!?]+', text))
            words = len(text.split())
            syllables = self._count_syllables(text)
            
            if sentences == 0 or words == 0:
                return 0.0
            
            # Simplified Flesch Reading Ease formula
            score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            self.logger.error(f"Readability calculation error: {str(e)}")
            return 50.0  # Default moderate readability

    def _calculate_complexity(self, text: str) -> float:
        """Calculate document complexity score"""
        try:
            # Factors that increase complexity
            long_words = len([word for word in text.split() if len(word) > 6])
            total_words = len(text.split())
            long_sentences = len([sent for sent in re.split(r'[.!?]+', text) if len(sent.split()) > 20])
            total_sentences = len(re.split(r'[.!?]+', text))
            
            legal_terms = sum(1 for term in self.legal_terms_database['high_risk_clauses'] 
                            if term.lower() in text.lower())
            
            if total_words == 0:
                return 0.0
            
            # Calculate complexity score (0-100)
            word_complexity = (long_words / total_words) * 40
            sentence_complexity = (long_sentences / max(total_sentences, 1)) * 30
            legal_complexity = min(legal_terms * 5, 30)
            
            return min(100.0, word_complexity + sentence_complexity + legal_complexity)
            
        except Exception as e:
            self.logger.error(f"Complexity calculation error: {str(e)}")
            return 50.0

    def _assess_legal_risk(self, clauses: List[ExtractedClause], text: str) -> float:
        """Assess legal risk score of document"""
        try:
            risk_score = 0.0
            
            # Risk from high-risk clauses
            high_risk_count = sum(1 for clause in clauses if clause.risk_level == 'high')
            risk_score += high_risk_count * 15
            
            # Risk from specific terms
            high_risk_terms = self.legal_terms_database['high_risk_clauses']
            text_lower = text.lower()
            
            for term in high_risk_terms:
                if term in text_lower:
                    risk_score += 10
            
            # Risk from missing important terms (for leases)
            important_terms = self.legal_terms_database['important_lease_terms']
            missing_important = sum(1 for term in important_terms if term not in text_lower)
            risk_score += missing_important * 5
            
            return min(100.0, risk_score)
            
        except Exception as e:
            self.logger.error(f"Legal risk assessment error: {str(e)}")
            return 25.0  # Default moderate risk

    def _extract_key_terms(self, text: str, doc_type: DocumentType, 
                         entities: List[ExtractedEntity], dates: List[ExtractedDate], 
                         amounts: List[ExtractedAmount]) -> Dict[str, Any]:
        """Extract key terms and information summary"""
        key_terms = {}
        
        try:
            # Extract based on document type
            if doc_type == DocumentType.LEASE_AGREEMENT:
                key_terms = self._extract_lease_terms(text, entities, dates, amounts)
            elif doc_type == DocumentType.RENTAL_APPLICATION:
                key_terms = self._extract_application_terms(text, entities, amounts)
            elif doc_type == DocumentType.MAINTENANCE_REQUEST:
                key_terms = self._extract_maintenance_terms(text, entities)
            else:
                key_terms = self._extract_general_terms(text, entities, dates, amounts)
        
        except Exception as e:
            self.logger.error(f"Key terms extraction error: {str(e)}")
            key_terms = {'error': str(e)}
        
        return key_terms

    def _extract_lease_terms(self, text: str, entities: List[ExtractedEntity], 
                           dates: List[ExtractedDate], amounts: List[ExtractedAmount]) -> Dict[str, Any]:
        """Extract key terms from lease agreement"""
        terms = {}
        
        # Extract tenant and landlord
        persons = [e for e in entities if e.entity_type == 'PERSON']
        if len(persons) >= 2:
            terms['tenant'] = persons[0].text
            terms['landlord'] = persons[1].text
        elif len(persons) == 1:
            terms['tenant'] = persons[0].text
        
        # Extract property address
        addresses = [e for e in entities if e.entity_type == 'ADDRESS']
        if addresses:
            terms['property_address'] = addresses[0].text
        
        # Extract lease dates
        lease_start = next((d for d in dates if d.date_type == 'lease_start'), None)
        lease_end = next((d for d in dates if d.date_type == 'lease_end'), None)
        
        if lease_start:
            terms['lease_start_date'] = lease_start.parsed_date.strftime('%Y-%m-%d')
        if lease_end:
            terms['lease_end_date'] = lease_end.parsed_date.strftime('%Y-%m-%d')
            
        # Calculate lease term
        if lease_start and lease_end:
            lease_days = (lease_end.parsed_date - lease_start.parsed_date).days
            terms['lease_term_months'] = round(lease_days / 30.44)
        
        # Extract rent and deposits
        rent_amounts = [a for a in amounts if a.amount_type == 'rent']
        deposit_amounts = [a for a in amounts if a.amount_type == 'deposit']
        
        if rent_amounts:
            terms['monthly_rent'] = rent_amounts[0].amount
        if deposit_amounts:
            terms['security_deposit'] = deposit_amounts[0].amount
        
        return terms

    def _extract_application_terms(self, text: str, entities: List[ExtractedEntity], 
                                 amounts: List[ExtractedAmount]) -> Dict[str, Any]:
        """Extract key terms from rental application"""
        terms = {}
        
        # Extract applicant info
        persons = [e for e in entities if e.entity_type == 'PERSON']
        if persons:
            terms['applicant_name'] = persons[0].text
        
        phones = [e for e in entities if e.entity_type == 'PHONE']
        emails = [e for e in entities if e.entity_type == 'EMAIL']
        
        if phones:
            terms['phone'] = phones[0].normalized_value
        if emails:
            terms['email'] = emails[0].normalized_value
        
        # Extract income information
        income_amounts = [a for a in amounts if 'income' in a.context.lower() or 'salary' in a.context.lower()]
        if income_amounts:
            terms['monthly_income'] = income_amounts[0].amount
        
        return terms

    def _extract_maintenance_terms(self, text: str, entities: List[ExtractedEntity]) -> Dict[str, Any]:
        """Extract key terms from maintenance request"""
        terms = {}
        
        # Extract location
        addresses = [e for e in entities if e.entity_type == 'ADDRESS']
        if addresses:
            terms['location'] = addresses[0].text
        
        # Extract issue description (simplified)
        issue_keywords = ['broken', 'leaking', 'not working', 'damaged', 'cracked', 'loose']
        text_lower = text.lower()
        
        found_issues = [keyword for keyword in issue_keywords if keyword in text_lower]
        if found_issues:
            terms['issue_type'] = found_issues[0]
        
        # Determine urgency
        urgent_keywords = ['urgent', 'emergency', 'immediate', 'asap', 'critical']
        if any(keyword in text_lower for keyword in urgent_keywords):
            terms['urgency'] = 'high'
        else:
            terms['urgency'] = 'normal'
        
        return terms

    def _extract_general_terms(self, text: str, entities: List[ExtractedEntity], 
                             dates: List[ExtractedDate], amounts: List[ExtractedAmount]) -> Dict[str, Any]:
        """Extract general key terms for unknown document types"""
        terms = {}
        
        # Summary of extracted information
        terms['entities_found'] = len(entities)
        terms['dates_found'] = len(dates)
        terms['amounts_found'] = len(amounts)
        
        if entities:
            terms['key_entities'] = [e.text for e in entities[:5]]  # Top 5
        if amounts:
            terms['total_amount'] = sum(a.amount for a in amounts)
        
        return terms

    def _generate_summary(self, text: str, doc_type: DocumentType, key_terms: Dict[str, Any]) -> str:
        """Generate document summary"""
        try:
            if doc_type == DocumentType.LEASE_AGREEMENT:
                tenant = key_terms.get('tenant', 'Unknown tenant')
                rent = key_terms.get('monthly_rent', 'Unknown amount')
                address = key_terms.get('property_address', 'property address not specified')
                
                return f"Lease agreement for {tenant} at {address} with monthly rent of ${rent:.0f}" if isinstance(rent, (int, float)) else f"Lease agreement for {tenant} at {address}"
            
            elif doc_type == DocumentType.RENTAL_APPLICATION:
                applicant = key_terms.get('applicant_name', 'Unknown applicant')
                income = key_terms.get('monthly_income', None)
                
                if income:
                    return f"Rental application from {applicant} with monthly income of ${income:.0f}"
                else:
                    return f"Rental application from {applicant}"
            
            elif doc_type == DocumentType.MAINTENANCE_REQUEST:
                location = key_terms.get('location', 'unspecified location')
                issue = key_terms.get('issue_type', 'maintenance issue')
                urgency = key_terms.get('urgency', 'normal')
                
                return f"Maintenance request for {issue} at {location} (urgency: {urgency})"
            
            else:
                # Generic summary based on length and content
                word_count = len(text.split())
                return f"{doc_type.value.replace('_', ' ').title()} document with {word_count} words"
        
        except Exception as e:
            self.logger.error(f"Summary generation error: {str(e)}")
            return "Document summary could not be generated"

    def _generate_recommendations(self, doc_type: DocumentType, clauses: List[ExtractedClause], 
                                legal_risk_score: float) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        try:
            # General recommendations based on risk score
            if legal_risk_score > 70:
                recommendations.append("HIGH RISK: This document should be reviewed by legal counsel before signing")
            elif legal_risk_score > 50:
                recommendations.append("MEDIUM RISK: Consider legal review of high-risk clauses")
            
            # Document-type specific recommendations
            if doc_type == DocumentType.LEASE_AGREEMENT:
                recommendations.extend([
                    "Verify all dates, amounts, and property details before signing",
                    "Ensure security deposit terms and return conditions are clearly stated",
                    "Review maintenance and repair responsibilities"
                ])
            
            elif doc_type == DocumentType.RENTAL_APPLICATION:
                recommendations.extend([
                    "Verify all personal information and supporting documentation",
                    "Confirm income verification requirements are met",
                    "Review application fees and deposit requirements"
                ])
            
            # Clause-specific recommendations
            high_risk_clauses = [c for c in clauses if c.risk_level == 'high']
            if high_risk_clauses:
                recommendations.append(f"Pay special attention to {len(high_risk_clauses)} high-risk clause(s)")
            
        except Exception as e:
            self.logger.error(f"Recommendations generation error: {str(e)}")
            recommendations.append("Unable to generate specific recommendations")
        
        return recommendations[:10]  # Limit to top 10

    def _generate_warnings(self, clauses: List[ExtractedClause], legal_risk_score: float, 
                         amounts: List[ExtractedAmount]) -> List[str]:
        """Generate warnings about potential issues"""
        warnings = []
        
        try:
            # Risk-based warnings
            critical_clauses = [c for c in clauses if c.importance == 'critical']
            if critical_clauses:
                warnings.append(f"CRITICAL: {len(critical_clauses)} critical clause(s) require immediate attention")
            
            # Amount-based warnings
            large_amounts = [a for a in amounts if a.amount > 10000]
            if large_amounts:
                warnings.append(f"Large financial amounts detected: review carefully")
            
            # Missing information warnings (simplified)
            if legal_risk_score < 20:  # Very low risk might indicate missing information
                warnings.append("Document may be incomplete - some standard terms may be missing")
        
        except Exception as e:
            self.logger.error(f"Warnings generation error: {str(e)}")
        
        return warnings

    # Helper methods (continued in next part due to length)
    def _map_spacy_entity_type(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to our entity types"""
        mapping = {
            'PERSON': 'PERSON',
            'GPE': 'LOCATION',  # Geopolitical entity
            'LOC': 'LOCATION',
            'ORG': 'ORGANIZATION',
            'MONEY': 'MONEY',
            'DATE': 'DATE',
            'CARDINAL': 'NUMBER',
            'ORDINAL': 'NUMBER'
        }
        return mapping.get(spacy_label)

    def _get_entity_context(self, text: str, start_pos: int, end_pos: int, 
                          context_size: int = 50) -> str:
        """Get context around an entity"""
        context_start = max(0, start_pos - context_size)
        context_end = min(len(text), end_pos + context_size)
        return text[context_start:context_end].strip()

    def _normalize_entity_value(self, text: str, entity_type: str) -> Optional[str]:
        """Normalize entity values"""
        if entity_type == 'PERSON':
            return text.title()
        elif entity_type == 'EMAIL':
            return text.lower()
        elif entity_type == 'PHONE':
            return re.sub(r'[^\d]', '', text)
        return text

    def _parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        date_formats = [
            '%m/%d/%Y', '%m-%d-%Y', '%m/%d/%y', '%m-%d-%y',
            '%Y/%m/%d', '%Y-%m-%d',
            '%B %d, %Y', '%B %d %Y', '%d %B %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_text.strip(), fmt)
            except ValueError:
                continue
        
        return None

    def _classify_date_type(self, text: str, position: int, context_keywords: Dict) -> str:
        """Classify date type based on surrounding context"""
        # Get context around the date
        context = self._get_entity_context(text, position, position + 10, 100).lower()
        
        # Check for specific date type indicators
        for date_type, keywords in context_keywords.items():
            if any(keyword in context for keyword in keywords):
                return date_type
        
        return 'general_date'

    def _parse_amount(self, amount_text: str) -> Optional[float]:
        """Parse monetary amount from text"""
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,\s]', '', amount_text)
        
        # Extract numeric part
        match = re.search(r'\d+(?:\.\d{2})?', cleaned)
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        
        return None

    def _classify_amount_type(self, text: str, position: int, context_keywords: Dict) -> str:
        """Classify amount type based on surrounding context"""
        context = self._get_entity_context(text, position, position + 10, 100).lower()
        
        for amount_type, keywords in context_keywords.items():
            if any(keyword in context for keyword in keywords):
                return amount_type
        
        return 'general_amount'

    def _analyze_sentence_for_clauses(self, sentence: str, doc_type: DocumentType) -> Optional[Tuple[str, str, str, str]]:
        """Analyze sentence to identify important clauses"""
        sentence_lower = sentence.lower()
        
        # Check for high-risk legal terms
        high_risk_terms = self.legal_terms_database['high_risk_clauses']
        for term in high_risk_terms:
            if term in sentence_lower:
                return (term, 'critical', 'high', f'Contains {term} clause')
        
        # Check for important lease terms
        important_terms = self.legal_terms_database['important_lease_terms']
        for term in important_terms:
            if term in sentence_lower:
                return (term, 'high', 'medium', f'Addresses {term}')
        
        # Check for compliance-related content
        compliance_terms = self.legal_terms_database['compliance_keywords']
        for term in compliance_terms:
            if term in sentence_lower:
                return ('compliance', 'high', 'medium', f'Compliance-related: {term}')
        
        # Check for financial terms
        financial_terms = self.legal_terms_database['financial_terms']
        for term in financial_terms:
            if term in sentence_lower:
                return ('financial', 'medium', 'low', f'Financial term: {term}')
        
        return None

    def _count_syllables(self, text: str) -> int:
        """Count syllables in text (simplified method)"""
        vowels = 'aeiouy'
        syllable_count = 0
        
        for word in text.lower().split():
            word_syllables = 0
            prev_was_vowel = False
            
            for char in word:
                if char in vowels:
                    if not prev_was_vowel:
                        word_syllables += 1
                    prev_was_vowel = True
                else:
                    prev_was_vowel = False
            
            # Adjust for silent 'e'
            if word.endswith('e') and word_syllables > 1:
                word_syllables -= 1
            
            # Ensure at least one syllable per word
            syllable_count += max(1, word_syllables)
        
        return syllable_count

# Global document processor instance
_document_processor = None

def get_document_processor():
    """Get the global document processor instance"""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor
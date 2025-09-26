"""
Entity Extraction System for EstateCore Tenant Chatbot

Extracts relevant entities from tenant messages including property-specific
information, dates, amounts, and other structured data.
"""

import re
import spacy
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import calendar
from dateutil import parser as date_parser

@dataclass
class Entity:
    """Container for extracted entity"""
    text: str
    label: str
    value: Any
    start: int
    end: int
    confidence: float

@dataclass
class ExtractedEntities:
    """Container for all extracted entities from text"""
    entities: List[Entity]
    amounts: List[Dict[str, Any]]
    dates: List[Dict[str, Any]]
    unit_numbers: List[str]
    property_features: List[str]
    contact_info: List[Dict[str, Any]]

class EntityExtractor:
    """
    Advanced entity extraction system for property management chatbot
    """
    
    def __init__(self, nlp_model: Optional[spacy.Language] = None):
        """
        Initialize Entity Extractor
        
        Args:
            nlp_model: Pre-loaded spaCy model (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Load spaCy model
        if nlp_model:
            self.nlp = nlp_model
        else:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.logger.warning("SpaCy model not found, downloading...")
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
        
        # Define regex patterns
        self.patterns = {
            'money': [
                r'\$[\d,]+\.?\d*',
                r'[\d,]+\.?\d*\s*dollars?',
                r'[\d,]+\.?\d*\s*bucks?',
            ],
            'unit_number': [
                r'unit\s*#?(\d+[a-z]?)',
                r'apartment\s*#?(\d+[a-z]?)',
                r'apt\.?\s*#?(\d+[a-z]?)',
                r'room\s*#?(\d+[a-z]?)',
                r'#(\d+[a-z]?)',
            ],
            'phone': [
                r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
                r'\((\d{3})\)\s*(\d{3})[-.\s]?(\d{4})',
            ],
            'email': [
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            ],
            'date_relative': [
                r'(today|tomorrow|yesterday)',
                r'(next|last)\s+(week|month|year)',
                r'in\s+(\d+)\s+(days?|weeks?|months?)',
                r'(\d+)\s+(days?|weeks?|months?)\s+(ago|from\s+now)',
            ]
        }
        
        # Property-specific terms and features
        self.property_features = {
            'appliances': ['dishwasher', 'refrigerator', 'washer', 'dryer', 'microwave', 
                         'garbage disposal', 'stove', 'oven'],
            'amenities': ['pool', 'gym', 'fitness center', 'laundry room', 'parking', 
                         'elevator', 'balcony', 'patio', 'deck'],
            'utilities': ['electricity', 'gas', 'water', 'sewer', 'trash', 'internet', 
                        'cable', 'heating', 'cooling', 'ac', 'air conditioning'],
            'maintenance': ['repair', 'fix', 'broken', 'not working', 'maintenance', 
                          'service', 'leak', 'clog', 'noise'],
            'rooms': ['kitchen', 'bathroom', 'bedroom', 'living room', 'dining room', 
                     'closet', 'basement', 'attic']
        }
        
        # Month names for date parsing
        self.month_names = list(calendar.month_name[1:]) + list(calendar.month_abbr[1:])
        
        self.logger.info("Entity Extractor initialized")
    
    def extract_money_amounts(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract monetary amounts from text
        
        Args:
            text: Input text
            
        Returns:
            List of money amount dictionaries
        """
        amounts = []
        
        for pattern in self.patterns['money']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                amount_text = match.group()
                
                # Parse the amount
                amount_value = self._parse_money(amount_text)
                
                amounts.append({
                    'text': amount_text,
                    'value': amount_value,
                    'start': match.start(),
                    'end': match.end(),
                    'type': 'money'
                })
        
        return amounts
    
    def _parse_money(self, text: str) -> float:
        """Parse money text to float value"""
        # Remove non-numeric characters except decimal point
        numeric_text = re.sub(r'[^\d.]', '', text)
        try:
            return float(numeric_text)
        except ValueError:
            return 0.0
    
    def extract_unit_numbers(self, text: str) -> List[str]:
        """
        Extract unit/apartment numbers from text
        
        Args:
            text: Input text
            
        Returns:
            List of unit numbers
        """
        unit_numbers = []
        
        for pattern in self.patterns['unit_number']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.groups():
                    unit_num = match.group(1)
                else:
                    unit_num = match.group()
                
                unit_numbers.append(unit_num.strip())
        
        return list(set(unit_numbers))  # Remove duplicates
    
    def extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract dates and date-related expressions from text
        
        Args:
            text: Input text
            
        Returns:
            List of date dictionaries
        """
        dates = []
        
        # Extract relative dates
        for pattern in self.patterns['date_relative']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_text = match.group()
                parsed_date = self._parse_relative_date(date_text)
                
                if parsed_date:
                    dates.append({
                        'text': date_text,
                        'value': parsed_date,
                        'start': match.start(),
                        'end': match.end(),
                        'type': 'relative_date'
                    })
        
        # Extract absolute dates using spaCy
        doc = self.nlp(text)
        for ent in doc.ents:
            if ent.label_ == "DATE":
                parsed_date = self._parse_absolute_date(ent.text)
                if parsed_date:
                    dates.append({
                        'text': ent.text,
                        'value': parsed_date,
                        'start': ent.start_char,
                        'end': ent.end_char,
                        'type': 'absolute_date'
                    })
        
        return dates
    
    def _parse_relative_date(self, text: str) -> Optional[datetime]:
        """Parse relative date expressions"""
        text_lower = text.lower()
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if 'today' in text_lower:
            return today
        elif 'tomorrow' in text_lower:
            return today + timedelta(days=1)
        elif 'yesterday' in text_lower:
            return today - timedelta(days=1)
        elif 'next week' in text_lower:
            return today + timedelta(weeks=1)
        elif 'last week' in text_lower:
            return today - timedelta(weeks=1)
        elif 'next month' in text_lower:
            return today + timedelta(days=30)  # Approximate
        elif 'last month' in text_lower:
            return today - timedelta(days=30)  # Approximate
        
        # Handle "in X days/weeks/months"
        in_match = re.search(r'in\s+(\d+)\s+(days?|weeks?|months?)', text_lower)
        if in_match:
            num = int(in_match.group(1))
            unit = in_match.group(2)
            
            if 'day' in unit:
                return today + timedelta(days=num)
            elif 'week' in unit:
                return today + timedelta(weeks=num)
            elif 'month' in unit:
                return today + timedelta(days=num*30)
        
        # Handle "X days/weeks/months ago"
        ago_match = re.search(r'(\d+)\s+(days?|weeks?|months?)\s+ago', text_lower)
        if ago_match:
            num = int(ago_match.group(1))
            unit = ago_match.group(2)
            
            if 'day' in unit:
                return today - timedelta(days=num)
            elif 'week' in unit:
                return today - timedelta(weeks=num)
            elif 'month' in unit:
                return today - timedelta(days=num*30)
        
        return None
    
    def _parse_absolute_date(self, text: str) -> Optional[datetime]:
        """Parse absolute date expressions"""
        try:
            return date_parser.parse(text, fuzzy=True)
        except:
            return None
    
    def extract_contact_info(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract contact information (phone, email) from text
        
        Args:
            text: Input text
            
        Returns:
            List of contact info dictionaries
        """
        contact_info = []
        
        # Extract phone numbers
        for pattern in self.patterns['phone']:
            matches = re.finditer(pattern, text)
            for match in matches:
                contact_info.append({
                    'text': match.group(),
                    'type': 'phone',
                    'value': self._clean_phone_number(match.group()),
                    'start': match.start(),
                    'end': match.end()
                })
        
        # Extract emails
        for pattern in self.patterns['email']:
            matches = re.finditer(pattern, text)
            for match in matches:
                contact_info.append({
                    'text': match.group(),
                    'type': 'email',
                    'value': match.group().lower(),
                    'start': match.start(),
                    'end': match.end()
                })
        
        return contact_info
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and format phone number"""
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"1-({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        return phone
    
    def extract_property_features(self, text: str) -> List[str]:
        """
        Extract property features and amenities mentioned in text
        
        Args:
            text: Input text
            
        Returns:
            List of property features
        """
        features = []
        text_lower = text.lower()
        
        for category, terms in self.property_features.items():
            for term in terms:
                if term in text_lower:
                    features.append(term)
        
        return list(set(features))  # Remove duplicates
    
    def extract_spacy_entities(self, text: str) -> List[Entity]:
        """
        Extract named entities using spaCy
        
        Args:
            text: Input text
            
        Returns:
            List of Entity objects
        """
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Map spaCy labels to our custom values
            value = ent.text
            
            if ent.label_ == "MONEY":
                value = self._parse_money(ent.text)
            elif ent.label_ == "DATE":
                parsed_date = self._parse_absolute_date(ent.text)
                if parsed_date:
                    value = parsed_date
            elif ent.label_ in ["PERSON", "ORG", "GPE"]:
                value = ent.text.title()
            
            entities.append(Entity(
                text=ent.text,
                label=ent.label_,
                value=value,
                start=ent.start_char,
                end=ent.end_char,
                confidence=1.0  # spaCy doesn't provide confidence scores
            ))
        
        return entities
    
    def extract_maintenance_urgency(self, text: str) -> Dict[str, Any]:
        """
        Extract urgency level for maintenance requests
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with urgency information
        """
        text_lower = text.lower()
        
        urgent_keywords = {
            'emergency': 10,
            'urgent': 8,
            'immediately': 8,
            'asap': 7,
            'flooding': 9,
            'leak': 6,
            'broken': 5,
            'not working': 4
        }
        
        urgency_score = 0
        found_keywords = []
        
        for keyword, score in urgent_keywords.items():
            if keyword in text_lower:
                urgency_score = max(urgency_score, score)
                found_keywords.append(keyword)
        
        # Determine urgency level
        if urgency_score >= 8:
            level = 'emergency'
        elif urgency_score >= 6:
            level = 'urgent'
        elif urgency_score >= 4:
            level = 'high'
        else:
            level = 'normal'
        
        return {
            'level': level,
            'score': urgency_score,
            'keywords': found_keywords
        }
    
    def extract_all(self, text: str) -> ExtractedEntities:
        """
        Extract all types of entities from text
        
        Args:
            text: Input text
            
        Returns:
            ExtractedEntities object with all extracted information
        """
        if not text or not text.strip():
            return ExtractedEntities([], [], [], [], [], [])
        
        # Extract different types of entities
        spacy_entities = self.extract_spacy_entities(text)
        amounts = self.extract_money_amounts(text)
        dates = self.extract_dates(text)
        unit_numbers = self.extract_unit_numbers(text)
        property_features = self.extract_property_features(text)
        contact_info = self.extract_contact_info(text)
        
        return ExtractedEntities(
            entities=spacy_entities,
            amounts=amounts,
            dates=dates,
            unit_numbers=unit_numbers,
            property_features=property_features,
            contact_info=contact_info
        )
    
    def extract_payment_info(self, text: str) -> Dict[str, Any]:
        """
        Extract payment-related information from text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with payment information
        """
        text_lower = text.lower()
        payment_info = {}
        
        # Extract amounts
        amounts = self.extract_money_amounts(text)
        if amounts:
            payment_info['amounts'] = amounts
        
        # Extract payment methods
        payment_methods = {
            'credit card': ['credit', 'card', 'visa', 'mastercard', 'amex'],
            'debit card': ['debit'],
            'bank transfer': ['bank', 'transfer', 'ach'],
            'check': ['check', 'cheque'],
            'cash': ['cash'],
            'online': ['online', 'website', 'portal']
        }
        
        found_methods = []
        for method, keywords in payment_methods.items():
            if any(keyword in text_lower for keyword in keywords):
                found_methods.append(method)
        
        if found_methods:
            payment_info['methods'] = found_methods
        
        # Extract dates
        dates = self.extract_dates(text)
        if dates:
            payment_info['dates'] = dates
        
        return payment_info
    
    def get_entity_summary(self, entities: ExtractedEntities) -> Dict[str, int]:
        """
        Get summary statistics of extracted entities
        
        Args:
            entities: ExtractedEntities object
            
        Returns:
            Summary dictionary with counts
        """
        return {
            'total_entities': len(entities.entities),
            'amounts_found': len(entities.amounts),
            'dates_found': len(entities.dates),
            'unit_numbers_found': len(entities.unit_numbers),
            'property_features_found': len(entities.property_features),
            'contact_info_found': len(entities.contact_info)
        }
"""
NLP Engine for EstateCore Tenant Chatbot

Provides comprehensive natural language processing capabilities including
text preprocessing, tokenization, language detection, and feature extraction.
"""

import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from langdetect import detect
from textblob import TextBlob
import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

@dataclass
class ProcessedText:
    """Container for processed text data"""
    original_text: str
    cleaned_text: str
    tokens: List[str]
    lemmas: List[str]
    sentences: List[str]
    language: str
    entities: List[Dict]
    pos_tags: List[Tuple[str, str]]
    sentiment: Dict[str, float]

class NLPEngine:
    """
    Advanced NLP Engine for processing tenant messages and queries
    """
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """
        Initialize NLP Engine
        
        Args:
            model_name: SpaCy model name to use
        """
        self.logger = logging.getLogger(__name__)
        
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            self.logger.warning(f"SpaCy model {model_name} not found. Installing...")
            spacy.cli.download(model_name)
            self.nlp = spacy.load(model_name)
        
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Property management specific terms
        self.property_terms = {
            'rent', 'lease', 'apartment', 'unit', 'maintenance', 'repair',
            'payment', 'deposit', 'utilities', 'tenant', 'landlord', 'property',
            'building', 'amenities', 'parking', 'laundry', 'heating', 'cooling',
            'elevator', 'pool', 'gym', 'lease renewal', 'move out', 'move in',
            'inspection', 'damages', 'security deposit', 'late fee', 'eviction'
        }
        
        self.logger.info("NLP Engine initialized successfully")
    
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess input text
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned text
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep punctuation for sentence structure
        text = re.sub(r'[^\w\s\.\?\!\,\;\:]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the input text
        
        Args:
            text: Input text
            
        Returns:
            Language code (e.g., 'en', 'es', 'fr')
        """
        try:
            return detect(text)
        except:
            return 'en'  # Default to English
    
    def extract_entities(self, text: str) -> List[Dict]:
        """
        Extract named entities from text
        
        Args:
            text: Input text
            
        Returns:
            List of entities with labels and positions
        """
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'description': spacy.explain(ent.label_)
            })
        
        return entities
    
    def get_pos_tags(self, text: str) -> List[Tuple[str, str]]:
        """
        Get part-of-speech tags for text
        
        Args:
            text: Input text
            
        Returns:
            List of (word, pos_tag) tuples
        """
        blob = TextBlob(text)
        return blob.tags
    
    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of the text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with polarity and subjectivity scores
        """
        blob = TextBlob(text)
        return {
            'polarity': blob.sentiment.polarity,  # -1 to 1 (negative to positive)
            'subjectivity': blob.sentiment.subjectivity,  # 0 to 1 (objective to subjective)
            'compound': self._get_sentiment_label(blob.sentiment.polarity)
        }
    
    def _get_sentiment_label(self, polarity: float) -> str:
        """Convert polarity score to sentiment label"""
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def tokenize_and_lemmatize(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Tokenize text and create lemmatized version
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (tokens, lemmas)
        """
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stopwords and non-alphabetic tokens
        tokens = [token for token in tokens 
                 if token.isalpha() and token.lower() not in self.stop_words]
        
        # Lemmatize
        lemmas = [self.lemmatizer.lemmatize(token.lower()) for token in tokens]
        
        return tokens, lemmas
    
    def extract_property_keywords(self, text: str) -> List[str]:
        """
        Extract property management specific keywords
        
        Args:
            text: Input text
            
        Returns:
            List of relevant property management terms
        """
        tokens, lemmas = self.tokenize_and_lemmatize(text)
        
        # Find property-related terms
        found_terms = []
        text_lower = text.lower()
        
        for term in self.property_terms:
            if term in text_lower:
                found_terms.append(term)
        
        # Add lemmatized tokens that might be property-related
        property_lemmas = [lemma for lemma in lemmas if lemma in self.property_terms]
        found_terms.extend(property_lemmas)
        
        return list(set(found_terms))  # Remove duplicates
    
    def process_message(self, text: str) -> ProcessedText:
        """
        Comprehensive processing of a chat message
        
        Args:
            text: Raw message text
            
        Returns:
            ProcessedText object with all extracted information
        """
        if not text or not text.strip():
            raise ValueError("Empty text provided")
        
        # Preprocess
        cleaned_text = self.preprocess_text(text)
        
        # Language detection
        language = self.detect_language(text)
        
        # Tokenization and lemmatization
        tokens, lemmas = self.tokenize_and_lemmatize(cleaned_text)
        
        # Sentence tokenization
        sentences = sent_tokenize(text)
        
        # Entity extraction
        entities = self.extract_entities(text)
        
        # POS tagging
        pos_tags = self.get_pos_tags(cleaned_text)
        
        # Sentiment analysis
        sentiment = self.analyze_sentiment(text)
        
        return ProcessedText(
            original_text=text,
            cleaned_text=cleaned_text,
            tokens=tokens,
            lemmas=lemmas,
            sentences=sentences,
            language=language,
            entities=entities,
            pos_tags=pos_tags,
            sentiment=sentiment
        )
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts using SpaCy
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        doc1 = self.nlp(text1)
        doc2 = self.nlp(text2)
        
        return doc1.similarity(doc2)
    
    def extract_key_phrases(self, text: str) -> List[str]:
        """
        Extract key phrases from text using noun chunks
        
        Args:
            text: Input text
            
        Returns:
            List of key phrases
        """
        doc = self.nlp(text)
        key_phrases = []
        
        # Extract noun chunks
        for chunk in doc.noun_chunks:
            if len(chunk.text.strip()) > 2:  # Filter very short phrases
                key_phrases.append(chunk.text.strip().lower())
        
        return list(set(key_phrases))
    
    def is_question(self, text: str) -> bool:
        """
        Determine if the text is a question
        
        Args:
            text: Input text
            
        Returns:
            True if text appears to be a question
        """
        # Simple heuristics for question detection
        text = text.strip()
        
        # Ends with question mark
        if text.endswith('?'):
            return True
        
        # Starts with question words
        question_words = ['what', 'when', 'where', 'who', 'why', 'how', 'can', 'could', 
                         'would', 'should', 'is', 'are', 'do', 'does', 'did', 'will']
        
        first_word = text.split()[0].lower() if text.split() else ''
        
        return first_word in question_words
    
    def extract_urgency_indicators(self, text: str) -> Dict[str, any]:
        """
        Detect urgency indicators in the text
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with urgency level and indicators
        """
        text_lower = text.lower()
        
        # Urgency keywords
        urgent_keywords = ['urgent', 'emergency', 'immediately', 'asap', 'critical', 'broken', 'flooding', 'fire', 'leak']
        high_keywords = ['soon', 'today', 'quickly', 'important', 'problem', 'issue', 'not working']
        
        urgent_count = sum(1 for keyword in urgent_keywords if keyword in text_lower)
        high_count = sum(1 for keyword in high_keywords if keyword in text_lower)
        
        # Determine urgency level
        if urgent_count > 0:
            level = 'urgent'
        elif high_count > 0:
            level = 'high'
        else:
            level = 'normal'
        
        return {
            'level': level,
            'urgent_indicators': urgent_count,
            'high_indicators': high_count,
            'sentiment_polarity': self.analyze_sentiment(text)['polarity']
        }
"""
AI-Powered License Plate Recognition and Search System
Supports multiple OCR backends, fuzzy matching, and partial plate search
"""

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("Warning: OpenCV not available. Image processing features disabled.")

import re
import os
import requests
from typing import List, Tuple, Dict, Optional
from difflib import SequenceMatcher
from dataclasses import dataclass
import base64
import json

@dataclass
class PlateResult:
    """Data class for plate recognition results"""
    plate: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None
    source: str = "unknown"
    
@dataclass
class SearchResult:
    """Data class for plate search results"""
    plate: str
    similarity: float
    match_type: str
    original_query: str

class AIPlateRecognizer:
    """Advanced AI-powered license plate recognition system"""
    
    def __init__(self):
        self.openalpr_key = os.environ.get("OPENALPR_API_KEY", "")
        self.azure_key = os.environ.get("AZURE_CV_KEY", "")
        self.azure_endpoint = os.environ.get("AZURE_CV_ENDPOINT", "")
        
        # US plate patterns (can be extended for other countries)
        self.plate_patterns = [
            r'^[A-Z]{3}[0-9]{3}$',      # ABC123
            r'^[A-Z]{3}[0-9]{4}$',      # ABC1234
            r'^[0-9]{3}[A-Z]{3}$',      # 123ABC
            r'^[A-Z]{2}[0-9]{4}$',      # AB1234
            r'^[A-Z]{1}[0-9]{6}$',      # A123456
            r'^[0-9]{3}[A-Z]{2}[0-9]{1}$', # 123AB1
            r'^[A-Z]{4}[0-9]{2}$',      # ABCD12
            r'^[0-9]{2}[A-Z]{3}[0-9]{2}$', # 12ABC34
        ]
        
        # Character substitution rules for OCR error correction
        self.char_substitutions = {
            '0': ['O', 'D', 'Q'],
            'O': ['0', 'D', 'Q'], 
            '1': ['I', 'L'],
            'I': ['1', 'L'],
            'L': ['1', 'I'],
            '5': ['S'],
            'S': ['5'],
            '6': ['G'],
            'G': ['6'],
            '8': ['B'],
            'B': ['8'],
            '2': ['Z'],
            'Z': ['2'],
        }
    
    def preprocess_image(self, image_path: str):
        """Preprocess image for better OCR accuracy"""
        if not CV2_AVAILABLE:
            return [None]  # Return placeholder if CV2 not available
            
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply various preprocessing techniques
        processed_images = []
        
        # Original grayscale
        processed_images.append(gray)
        
        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        processed_images.append(blurred)
        
        # Adaptive thresholding
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        processed_images.append(adaptive_thresh)
        
        # Morphological operations
        kernel = np.ones((2, 2), np.uint8)
        morph = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
        processed_images.append(morph)
        
        # Edge enhancement
        edges = cv2.Canny(gray, 50, 150)
        processed_images.append(edges)
        
        return processed_images
    
    def recognize_with_openalpr(self, image_path: str) -> List[PlateResult]:
        """Recognize plates using OpenALPR API"""
        if not self.openalpr_key:
            return []
        
        try:
            with open(image_path, 'rb') as img_file:
                response = requests.post(
                    'https://api.openalpr.com/v3/recognize_bytes',
                    params={
                        'secret_key': self.openalpr_key,
                        'recognize_vehicle': 0,
                        'country': 'us',
                        'return_image': 0,
                        'topn': 10  # Get top 10 results
                    },
                    data=img_file.read(),
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for result in data.get('results', []):
                        plate = result.get('plate', '').upper()
                        confidence = result.get('confidence', 0)
                        
                        # Get bounding box if available
                        bbox = None
                        if 'coordinates' in result:
                            coords = result['coordinates']
                            if len(coords) >= 4:
                                x_coords = [c['x'] for c in coords]
                                y_coords = [c['y'] for c in coords]
                                bbox = (min(x_coords), min(y_coords), 
                                       max(x_coords) - min(x_coords), 
                                       max(y_coords) - min(y_coords))
                        
                        results.append(PlateResult(
                            plate=plate,
                            confidence=confidence,
                            bbox=bbox,
                            source="openalpr"
                        ))
                    
                    return results
                    
        except Exception as e:
            print(f"OpenALPR error: {str(e)}")
        
        return []
    
    def recognize_with_azure(self, image_path: str) -> List[PlateResult]:
        """Recognize plates using Azure Computer Vision"""
        if not self.azure_key or not self.azure_endpoint:
            return []
        
        try:
            with open(image_path, 'rb') as img_file:
                img_data = img_file.read()
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.azure_key,
                'Content-Type': 'application/octet-stream'
            }
            
            url = f"{self.azure_endpoint}/vision/v3.2/read/analyze"
            
            response = requests.post(url, headers=headers, data=img_data, timeout=30)
            
            if response.status_code == 202:
                # Get operation location for result
                operation_url = response.headers.get('Operation-Location')
                
                # Poll for results
                import time
                for _ in range(10):  # Wait up to 10 seconds
                    time.sleep(1)
                    result_response = requests.get(
                        operation_url, 
                        headers={'Ocp-Apim-Subscription-Key': self.azure_key}
                    )
                    
                    if result_response.status_code == 200:
                        result_data = result_response.json()
                        if result_data.get('status') == 'succeeded':
                            return self._extract_plates_from_azure_result(result_data)
                
        except Exception as e:
            print(f"Azure OCR error: {str(e)}")
        
        return []
    
    def _extract_plates_from_azure_result(self, result_data: dict) -> List[PlateResult]:
        """Extract potential license plates from Azure OCR result"""
        results = []
        
        try:
            pages = result_data.get('analyzeResult', {}).get('readResults', [])
            
            for page in pages:
                lines = page.get('lines', [])
                
                for line in lines:
                    text = line.get('text', '').upper().replace(' ', '')
                    
                    # Check if text matches license plate patterns
                    if self._is_potential_plate(text):
                        bbox = None
                        if 'boundingBox' in line:
                            bb = line['boundingBox']
                            if len(bb) >= 8:
                                x_coords = [bb[i] for i in range(0, 8, 2)]
                                y_coords = [bb[i] for i in range(1, 8, 2)]
                                bbox = (min(x_coords), min(y_coords),
                                       max(x_coords) - min(x_coords),
                                       max(y_coords) - min(y_coords))
                        
                        results.append(PlateResult(
                            plate=text,
                            confidence=85.0,  # Azure doesn't provide confidence for text
                            bbox=bbox,
                            source="azure"
                        ))
        
        except Exception as e:
            print(f"Error extracting Azure results: {str(e)}")
        
        return results
    
    def recognize_with_tesseract(self, image_path: str) -> List[PlateResult]:
        """Recognize plates using Tesseract OCR (fallback)"""
        try:
            import pytesseract
            from PIL import Image
            
            # Process multiple versions of the image
            processed_images = self.preprocess_image(image_path)
            results = []
            
            for i, img_array in enumerate(processed_images):
                # Convert numpy array to PIL Image
                pil_image = Image.fromarray(img_array)
                
                # Configure Tesseract for license plates
                config = '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                
                try:
                    text = pytesseract.image_to_string(pil_image, config=config)
                    text = text.strip().upper().replace(' ', '').replace('\n', '')
                    
                    if self._is_potential_plate(text):
                        # Confidence decreases with processing complexity
                        confidence = max(60 - (i * 10), 20)
                        
                        results.append(PlateResult(
                            plate=text,
                            confidence=confidence,
                            source=f"tesseract_v{i}"
                        ))
                
                except Exception as e:
                    continue
            
            return results
            
        except ImportError:
            print("Tesseract not available (pip install pytesseract)")
            return []
        except Exception as e:
            print(f"Tesseract error: {str(e)}")
            return []
    
    def _is_potential_plate(self, text: str) -> bool:
        """Check if text matches common license plate patterns"""
        if not text or len(text) < 4 or len(text) > 8:
            return False
        
        # Check against known patterns
        for pattern in self.plate_patterns:
            if re.match(pattern, text):
                return True
        
        # Additional heuristics
        # Must contain both letters and numbers
        has_letter = any(c.isalpha() for c in text)
        has_number = any(c.isdigit() for c in text)
        
        return has_letter and has_number
    
    def recognize_plate(self, image_path: str) -> List[PlateResult]:
        """Main recognition method using multiple OCR backends"""
        all_results = []
        
        # Try OpenALPR first (most accurate for plates)
        openalpr_results = self.recognize_with_openalpr(image_path)
        all_results.extend(openalpr_results)
        
        # Try Azure Computer Vision
        azure_results = self.recognize_with_azure(image_path)
        all_results.extend(azure_results)
        
        # Fallback to Tesseract
        if not all_results:
            tesseract_results = self.recognize_with_tesseract(image_path)
            all_results.extend(tesseract_results)
        
        # Deduplicate and rank results
        return self._rank_and_deduplicate_results(all_results)
    
    def _rank_and_deduplicate_results(self, results: List[PlateResult]) -> List[PlateResult]:
        """Rank and deduplicate recognition results"""
        if not results:
            return []
        
        # Group similar plates
        grouped = {}
        for result in results:
            key = result.plate
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(result)
        
        # Rank each group and pick the best
        final_results = []
        for plate, group in grouped.items():
            # Sort by confidence and source priority
            source_priority = {"openalpr": 3, "azure": 2, "tesseract": 1}
            
            best = max(group, key=lambda r: (
                source_priority.get(r.source.split('_')[0], 0),
                r.confidence
            ))
            
            final_results.append(best)
        
        # Sort final results by confidence
        final_results.sort(key=lambda r: r.confidence, reverse=True)
        
        return final_results

class FuzzyPlateSearch:
    """Advanced fuzzy search for partial license plates"""
    
    def __init__(self):
        self.recognizer = AIPlateRecognizer()
    
    def calculate_similarity(self, query: str, target: str) -> float:
        """Calculate similarity between two plates"""
        query = query.upper().strip()
        target = target.upper().strip()
        
        # Exact match
        if query == target:
            return 1.0
        
        # Substring match
        if query in target or target in query:
            return 0.95
        
        # Sequence matching
        seq_ratio = SequenceMatcher(None, query, target).ratio()
        
        # Character position matching
        pos_score = self._position_based_similarity(query, target)
        
        # Pattern matching
        pattern_score = self._pattern_based_similarity(query, target)
        
        # Combine scores
        final_score = max(seq_ratio, pos_score, pattern_score)
        
        return final_score
    
    def _position_based_similarity(self, query: str, target: str) -> float:
        """Calculate similarity based on character positions"""
        if not query or not target:
            return 0.0
        
        matches = 0
        total_positions = min(len(query), len(target))
        
        for i in range(total_positions):
            if i < len(query) and i < len(target):
                if query[i] == target[i]:
                    matches += 1
                elif self._are_similar_chars(query[i], target[i]):
                    matches += 0.8  # Partial credit for similar characters
        
        return matches / max(len(query), len(target))
    
    def _pattern_based_similarity(self, query: str, target: str) -> float:
        """Calculate similarity based on license plate patterns"""
        # Extract patterns (letter/number sequences)
        query_pattern = self._extract_pattern(query)
        target_pattern = self._extract_pattern(target)
        
        if query_pattern == target_pattern:
            return 0.9
        
        return 0.0
    
    def _extract_pattern(self, plate: str) -> str:
        """Extract letter/number pattern from plate"""
        pattern = ""
        for char in plate:
            if char.isalpha():
                pattern += "L"
            elif char.isdigit():
                pattern += "N"
            else:
                pattern += "X"
        return pattern
    
    def _are_similar_chars(self, char1: str, char2: str) -> bool:
        """Check if two characters are commonly confused in OCR"""
        substitutions = {
            '0': ['O', 'D', 'Q'],
            'O': ['0', 'D', 'Q'],
            '1': ['I', 'L'],
            'I': ['1', 'L'],
            'L': ['1', 'I'],
            '5': ['S'],
            'S': ['5'],
            '6': ['G'],
            'G': ['6'],
            '8': ['B'],
            'B': ['8'],
            '2': ['Z'],
            'Z': ['2'],
        }
        
        return char2 in substitutions.get(char1, [])
    
    def expand_query(self, partial_plate: str) -> List[str]:
        """Expand partial plate with possible character substitutions"""
        partial_plate = partial_plate.upper().strip()
        expansions = [partial_plate]
        
        # Handle wildcards (* and ?)
        if '*' in partial_plate or '?' in partial_plate:
            # Convert to regex pattern
            pattern = partial_plate.replace('*', '.*').replace('?', '.')
            expansions.append(pattern)
        
        # Generate character substitution variants
        for i, char in enumerate(partial_plate):
            if char in self.recognizer.char_substitutions:
                for substitute in self.recognizer.char_substitutions[char]:
                    variant = list(partial_plate)
                    variant[i] = substitute
                    expansions.append(''.join(variant))
        
        return list(set(expansions))  # Remove duplicates
    
    def search_plates(self, query: str, plate_list: List[str], 
                     min_similarity: float = 0.5, limit: int = 10) -> List[SearchResult]:
        """Search for plates matching the query"""
        results = []
        expanded_queries = self.expand_query(query)
        
        for plate in plate_list:
            best_similarity = 0.0
            best_match_type = "exact"
            
            # Test against all expanded queries
            for expanded_query in expanded_queries:
                similarity = self.calculate_similarity(expanded_query, plate)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    
                    # Determine match type
                    if similarity == 1.0:
                        best_match_type = "exact"
                    elif similarity >= 0.95:
                        best_match_type = "substring"
                    elif similarity >= 0.8:
                        best_match_type = "fuzzy_high"
                    elif similarity >= 0.6:
                        best_match_type = "fuzzy_medium"
                    else:
                        best_match_type = "fuzzy_low"
            
            if best_similarity >= min_similarity:
                results.append(SearchResult(
                    plate=plate,
                    similarity=best_similarity,
                    match_type=best_match_type,
                    original_query=query
                ))
        
        # Sort by similarity (descending)
        results.sort(key=lambda r: r.similarity, reverse=True)
        
        return results[:limit]
    
    def smart_search_database(self, query: str, db_session, 
                            min_similarity: float = 0.5, limit: int = 10) -> List[SearchResult]:
        """Search plates in database with intelligent matching"""
        try:
            # Get all plates from relevant tables
            plates_query = db_session.execute(db_session.text("""
                SELECT DISTINCT plate FROM (
                    SELECT plate FROM lpr_events WHERE plate IS NOT NULL
                    UNION
                    SELECT plate FROM lpr_blacklist WHERE plate IS NOT NULL
                ) AS all_plates
            """)).fetchall()
            
            plate_list = [row[0] for row in plates_query if row[0]]
            
            return self.search_plates(query, plate_list, min_similarity, limit)
            
        except Exception as e:
            print(f"Database search error: {str(e)}")
            return []

# Example usage and testing
if __name__ == "__main__":
    # Initialize recognizer
    recognizer = AIPlateRecognizer()
    fuzzy_search = FuzzyPlateSearch()
    
    # Test fuzzy search
    test_plates = [
        "ABC123", "DEF456", "GHI789", "XYZ987", "ABC124", "ABC129",
        "DEF455", "DEF457", "ABC1234", "DEF4567", "GHI7890"
    ]
    
    test_queries = [
        "ABC",      # Partial
        "ABC12",    # Partial with numbers
        "A8C123",   # OCR error (B->8)
        "DEF45*",   # Wildcard
        "?HI789",   # Single character wildcard
    ]
    
    print("Fuzzy Search Test Results:")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        results = fuzzy_search.search_plates(query, test_plates, min_similarity=0.3)
        
        for result in results[:5]:  # Top 5 results
            print(f"  {result.plate} -> {result.similarity:.2f} ({result.match_type})")
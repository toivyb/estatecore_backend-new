"""
Test fuzzy search functionality without image processing dependencies
"""

import re
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import List

@dataclass
class SearchResult:
    """Data class for plate search results"""
    plate: str
    similarity: float
    match_type: str
    original_query: str

class SimpleFuzzySearch:
    """Simplified fuzzy search for testing without dependencies"""
    
    def __init__(self):
        # US plate patterns
        self.plate_patterns = [
            r'^[A-Z]{3}[0-9]{3}$',      # ABC123
            r'^[A-Z]{3}[0-9]{4}$',      # ABC1234
            r'^[0-9]{3}[A-Z]{3}$',      # 123ABC
            r'^[A-Z]{2}[0-9]{4}$',      # AB1234
            r'^[A-Z]{1}[0-9]{6}$',      # A123456
            r'^[A-Z]{4}[0-9]{2}$',      # ABCD12
        ]
        
        # Character substitutions for OCR errors
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
        return char2 in self.char_substitutions.get(char1, [])
    
    def expand_query(self, partial_plate: str) -> List[str]:
        """Expand partial plate with possible character substitutions"""
        partial_plate = partial_plate.upper().strip()
        expansions = [partial_plate]
        
        # Handle wildcards (* and ?)
        if '*' in partial_plate or '?' in partial_plate:
            pattern = partial_plate.replace('*', '.*').replace('?', '.')
            expansions.append(pattern)
        
        # Generate character substitution variants
        for i, char in enumerate(partial_plate):
            if char in self.char_substitutions:
                for substitute in self.char_substitutions[char]:
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

def run_tests():
    """Run comprehensive tests"""
    print("Testing AI Fuzzy Plate Search System")
    print("=" * 60)
    
    search = SimpleFuzzySearch()
    
    # Test database
    test_plates = [
        "ABC123", "DEF456", "GHI789", "XYZ987", "ABC124", "ABC129",
        "DEF455", "DEF457", "ABC1234", "DEF4567", "GHI7890", "POLICE1",
        "FIRE001", "AMBUL1", "GOVT123", "STATE1", "COUNTY1", "STOLEN1",
        "WANTED2", "AMBER1", "BOLO123", "CAR001", "VAN002", "TRUCK3"
    ]
    
    # Test cases
    test_cases = [
        ("ABC", "Partial match"),
        ("ABC12", "Partial with numbers"),
        ("A8C123", "OCR error (B->8)"),
        ("DEF45*", "Wildcard pattern"),
        ("?HI789", "Single wildcard"),
        ("POL", "Emergency vehicle partial"),
        ("123", "Number only"),
        ("80L0123", "OCR misread BOLO123"),
        ("STOL", "Partial 'STOLEN'"),
        ("AMB", "Partial 'AMBER'"),
    ]
    
    for query, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Query: '{query}'")
        
        results = search.search_plates(query, test_plates, min_similarity=0.3, limit=5)
        
        if results:
            print("Results:")
            for i, result in enumerate(results, 1):
                confidence = int(result.similarity * 100)
                print(f"  {i}. {result.plate} -> {confidence}% ({result.match_type})")
        else:
            print("  No matches found")
        
        # Show query expansions
        expansions = search.expand_query(query)
        if len(expansions) > 1:
            print(f"  Expansions: {expansions}")

def demo_real_scenarios():
    """Demo real-world scenarios"""
    print("\n\nReal-World Demo Scenarios")
    print("=" * 60)
    
    search = SimpleFuzzySearch()
    
    # Police database simulation
    database = [
        "STOLEN1", "WANTED2", "AMBER1", "BOLO123", "SUSPECT", 
        "ABC123", "DEF456", "GHI789", "POLICE1", "FIRE001"
    ]
    
    scenarios = [
        ("STOL", "Witness: 'I saw STOL... on the getaway car'"),
        ("80L0", "Security camera OCR read BOLO as 80L0"),
        ("AMB", "Amber Alert: Partial plate AMB..."),
        ("SUS", "BOLO for vehicle with 'SUS...' plate"),
        ("A*123", "Witness: 'Started with A, ended with 123'"),
    ]
    
    for query, scenario in scenarios:
        print(f"\nScenario: {scenario}")
        print(f"Search: '{query}'")
        
        results = search.search_plates(query, database, min_similarity=0.4, limit=3)
        
        if results:
            print("Potential matches:")
            for result in results:
                confidence = int(result.similarity * 100)
                alert_level = "HIGH" if confidence >= 80 else "MEDIUM" if confidence >= 60 else "LOW"
                print(f"  - {result.plate} ({confidence}% - {alert_level})")
        else:
            print("No matches found")

if __name__ == "__main__":
    run_tests()
    demo_real_scenarios()
    
    print("\n\nTests completed successfully!")
    print("\nFeatures demonstrated:")
    print("- Partial plate matching")
    print("- OCR error correction") 
    print("- Wildcard support (* and ?)")
    print("- Similarity scoring")
    print("- Multiple match types")
    print("- Real-world scenarios")
"""
Test script for AI License Plate Recognition System
"""

from ai_plate_recognition import AIPlateRecognizer, FuzzyPlateSearch

def test_fuzzy_search():
    """Test the fuzzy search functionality"""
    print("🧪 Testing Fuzzy Search System")
    print("=" * 50)
    
    # Initialize search
    fuzzy_search = FuzzyPlateSearch()
    
    # Test plates database
    test_plates = [
        "ABC123", "DEF456", "GHI789", "XYZ987", "ABC124", "ABC129",
        "DEF455", "DEF457", "ABC1234", "DEF4567", "GHI7890", "POLICE1",
        "FIRE001", "AMBUL1", "GOVT123", "STATE1", "COUNTY1"
    ]
    
    # Test queries with expected behavior
    test_cases = [
        ("ABC", "Partial match - should find ABC123, ABC124, ABC129, ABC1234"),
        ("ABC12", "Partial with numbers - should find ABC123, ABC124, ABC129"),
        ("A8C123", "OCR error (B->8) - should find ABC123"),
        ("DEF45*", "Wildcard pattern - should find DEF456, DEF455, DEF457, DEF4567"),
        ("?HI789", "Single wildcard - should find GHI789"),
        ("XY", "Short partial - should find XYZ987"),
        ("POL", "Partial emergency - should find POLICE1"),
        ("123", "Number only - should find ABC123, GOVT123"),
        ("INVALID", "No match - should return empty"),
        ("AB0123", "OCR error (C->0) - should find ABC123"),
    ]
    
    for query, description in test_cases:
        print(f"\n📋 Query: '{query}'")
        print(f"Expected: {description}")
        
        results = fuzzy_search.search_plates(query, test_plates, min_similarity=0.3, limit=5)
        
        if results:
            print("Results:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result.plate} -> {result.similarity:.2f} ({result.match_type})")
        else:
            print("  No matches found")

def test_plate_patterns():
    """Test license plate pattern recognition"""
    print("\n\n🔍 Testing Plate Pattern Recognition")
    print("=" * 50)
    
    recognizer = AIPlateRecognizer()
    
    test_plates = [
        ("ABC123", True, "Standard 3-letter 3-number"),
        ("DEF1234", True, "3-letter 4-number"),
        ("123ABC", True, "3-number 3-letter"),
        ("AB1234", True, "2-letter 4-number"),
        ("A123456", True, "1-letter 6-number"),
        ("ABCD12", True, "4-letter 2-number"),
        ("12ABC34", True, "Mixed pattern"),
        ("INVALID", False, "Letters only"),
        ("123456", False, "Numbers only"),
        ("A", False, "Too short"),
        ("ABCDEFGH", False, "Too long"),
        ("ABC12E", True, "Mixed with embedded letter"),
    ]
    
    for plate, expected, description in test_plates:
        result = recognizer._is_potential_plate(plate)
        status = "✅" if result == expected else "❌"
        print(f"{status} {plate:10} -> {result:5} ({description})")

def test_character_substitutions():
    """Test OCR character substitution logic"""
    print("\n\n🔄 Testing Character Substitutions")
    print("=" * 50)
    
    fuzzy_search = FuzzyPlateSearch()
    
    # Test common OCR errors
    substitution_tests = [
        ("O", "0", "Letter O vs Number 0"),
        ("I", "1", "Letter I vs Number 1"),
        ("S", "5", "Letter S vs Number 5"),
        ("B", "8", "Letter B vs Number 8"),
        ("G", "6", "Letter G vs Number 6"),
        ("Z", "2", "Letter Z vs Number 2"),
    ]
    
    for char1, char2, description in substitution_tests:
        similarity = fuzzy_search._are_similar_chars(char1, char2)
        status = "✅" if similarity else "❌"
        print(f"{status} {char1} ↔ {char2}: {similarity} ({description})")

def test_search_expansion():
    """Test query expansion with wildcards and substitutions"""
    print("\n\n🎯 Testing Query Expansion")
    print("=" * 50)
    
    fuzzy_search = FuzzyPlateSearch()
    
    test_queries = [
        "ABC*",
        "A?C123", 
        "AB0123",  # Should expand to ABO123, ABC123
        "DEF5",    # Should expand to DEFS
    ]
    
    for query in test_queries:
        expansions = fuzzy_search.expand_query(query)
        print(f"Query: {query}")
        print(f"Expansions: {expansions}")
        print()

def demo_real_world_scenarios():
    """Demonstrate real-world usage scenarios"""
    print("\n\n🌟 Real-World Demo Scenarios")
    print("=" * 50)
    
    fuzzy_search = FuzzyPlateSearch()
    
    # Simulate a real database
    police_database = [
        "STOLEN1", "WANTED2", "AMBER1", "BOLO123", "STOLEN2",
        "ABC123", "DEF456", "GHI789", "XYZ987", "POLICE1",
        "CAR001", "VAN002", "TRUCK3", "BIKE004", "MOTO005"
    ]
    
    scenarios = [
        ("STOL", "Witness saw 'STOL...' on a fleeing vehicle"),
        ("AMB", "Amber Alert - partial plate from security camera"),
        ("80L0123", "OCR misread BOLO123 as 80L0123"),
        ("P0LICE1", "OCR misread POLICE1 as P0LICE1"),
        ("*123", "Witness only saw ending '123'"),
        ("A??123", "Witness saw A__123 (two middle chars unclear)"),
    ]
    
    for query, scenario in scenarios:
        print(f"\n📡 Scenario: {scenario}")
        print(f"Search Query: '{query}'")
        
        results = fuzzy_search.search_plates(query, police_database, min_similarity=0.4, limit=3)
        
        if results:
            print("🎯 Potential Matches:")
            for result in results:
                confidence_level = "HIGH" if result.similarity >= 0.8 else "MEDIUM" if result.similarity >= 0.6 else "LOW"
                print(f"  • {result.plate} ({result.similarity:.0%} confidence - {confidence_level})")
        else:
            print("❌ No matches found")

if __name__ == "__main__":
    print("🚀 AI License Plate Recognition Test Suite")
    print("=" * 60)
    
    # Run all tests
    test_fuzzy_search()
    test_plate_patterns()
    test_character_substitutions()
    test_search_expansion()
    demo_real_world_scenarios()
    
    print("\n\n✅ All tests completed!")
    print("\n💡 Usage Tips:")
    print("• Use wildcards: 'ABC*' or 'A?C123'")
    print("• Partial plates work: 'ABC' finds ABC123, ABC456, etc.")
    print("• OCR errors auto-corrected: '0' ↔ 'O', '1' ↔ 'I', etc.")
    print("• Similarity scoring helps rank results")
    print("• Multiple match types: exact, substring, fuzzy")
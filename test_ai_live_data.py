#!/usr/bin/env python3
"""Test AI systems with live data"""

from ai_services.predictive_analytics.maintenance_predictor import PredictiveMaintenanceAI

def test_predictive_maintenance():
    print("Testing Predictive Maintenance with live data...")
    
    ai = PredictiveMaintenanceAI()
    predictions = ai.predict_maintenance_needs(1, 90)
    
    print(f"Found {len(predictions)} predictions for property 1 using live data!")
    
    for i, p in enumerate(predictions[:5]):
        print(f"{i+1}. {p.maintenance_type.value}: {p.predicted_date.strftime('%Y-%m-%d')} (confidence: {p.confidence_score:.2f})")
    
    # Test equipment data
    equipment = ai._get_property_equipment(1)
    print(f"Property 1 has {len(equipment)} equipment items in database")
    for eq in equipment:
        print(f"  - {eq.equipment_id}: {eq.brand} {eq.model} ({eq.equipment_type.value})")
    
    # Test maintenance history  
    history = ai._get_property_maintenance_history(1)
    print(f"Property 1 has {len(history)} maintenance records in database")
    for h in history[:3]:
        print(f"  - {h.completion_date.strftime('%Y-%m-%d')}: {h.description} (${h.cost})")

if __name__ == "__main__":
    test_predictive_maintenance()
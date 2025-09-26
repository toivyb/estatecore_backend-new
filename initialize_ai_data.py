#!/usr/bin/env python3
"""
Initialize sample data for AI systems in EstateCore
This ensures AI features have real data to work with instead of empty databases
"""

import os
import json
import logging
from datetime import datetime, timedelta
import random
from database_service import get_database_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_property_equipment():
    """Initialize sample equipment data for properties"""
    logger.info("Initializing property equipment data...")
    
    db_service = get_database_service()
    
    # Sample equipment data for properties 1-10
    equipment_data = [
        # Property 1
        {"property_id": 1, "equipment_id": "HVAC_001", "equipment_type": "hvac", "brand": "Carrier", "model": "24ACC636A003", "installation_date": "2020-03-15", "replacement_cost": 8500.0},
        {"property_id": 1, "equipment_id": "WH_001", "equipment_type": "plumbing", "brand": "Rheem", "model": "XG50T12DU38U0", "installation_date": "2021-06-10", "replacement_cost": 1200.0},
        {"property_id": 1, "equipment_id": "ELEC_001", "equipment_type": "electrical", "brand": "Square D", "model": "QO124L200G", "installation_date": "2019-08-20", "replacement_cost": 800.0},
        
        # Property 2 
        {"property_id": 2, "equipment_id": "HVAC_002", "equipment_type": "hvac", "brand": "Trane", "model": "XR17", "installation_date": "2018-11-22", "replacement_cost": 9200.0},
        {"property_id": 2, "equipment_id": "REF_001", "equipment_type": "appliance", "brand": "Whirlpool", "model": "WRF535SWHZ", "installation_date": "2022-01-15", "replacement_cost": 2100.0},
        
        # Property 3
        {"property_id": 3, "equipment_id": "HVAC_003", "equipment_type": "hvac", "brand": "Goodman", "model": "GSX140421", "installation_date": "2021-04-10", "replacement_cost": 7500.0},
        {"property_id": 3, "equipment_id": "ROOF_001", "equipment_type": "roofing", "brand": "GAF", "model": "Timberline HD", "installation_date": "2020-09-05", "replacement_cost": 15000.0},
        
        # Additional properties
        {"property_id": 4, "equipment_id": "HVAC_004", "equipment_type": "hvac", "brand": "Lennox", "model": "XC25", "installation_date": "2019-07-12", "replacement_cost": 10500.0},
        {"property_id": 5, "equipment_id": "HVAC_005", "equipment_type": "hvac", "brand": "York", "model": "YZF", "installation_date": "2022-02-28", "replacement_cost": 8800.0},
    ]
    
    try:
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            for equipment in equipment_data:
                try:
                    # Add some performance metrics and sensor readings
                    performance_metrics = {
                        "efficiency_rating": random.uniform(0.8, 0.95),
                        "energy_consumption": random.uniform(50, 200),
                        "uptime_percentage": random.uniform(95, 99.5)
                    }
                    
                    sensor_readings = {
                        "temperature": random.uniform(68, 78),
                        "humidity": random.uniform(30, 60),
                        "vibration": random.uniform(0.1, 2.0)
                    }
                    
                    maintenance_history_list = [
                        f"Installation completed on {equipment['installation_date']}",
                        "Annual inspection passed",
                        "Filter replacement scheduled"
                    ]
                    
                    if db_service.is_postgres:
                        cursor.execute("""
                            INSERT INTO property_equipment 
                            (property_id, equipment_id, equipment_type, brand, model, installation_date, 
                             operating_hours, energy_consumption, performance_metrics, sensor_readings, 
                             maintenance_history, replacement_cost)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (equipment_id) DO UPDATE SET
                            brand = EXCLUDED.brand,
                            model = EXCLUDED.model,
                            replacement_cost = EXCLUDED.replacement_cost
                        """, (
                            equipment["property_id"], equipment["equipment_id"], equipment["equipment_type"],
                            equipment["brand"], equipment["model"], equipment["installation_date"],
                            random.randint(1000, 8760), random.uniform(100, 500),
                            json.dumps(performance_metrics), json.dumps(sensor_readings),
                            json.dumps(maintenance_history_list), equipment["replacement_cost"]
                        ))
                    else:
                        cursor.execute("""
                            INSERT OR REPLACE INTO property_equipment 
                            (property_id, equipment_id, equipment_type, brand, model, installation_date,
                             operating_hours, energy_consumption, performance_metrics, sensor_readings,
                             maintenance_history, replacement_cost)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            equipment["property_id"], equipment["equipment_id"], equipment["equipment_type"],
                            equipment["brand"], equipment["model"], equipment["installation_date"],
                            random.randint(1000, 8760), random.uniform(100, 500),
                            json.dumps(performance_metrics), json.dumps(sensor_readings),
                            json.dumps(maintenance_history_list), equipment["replacement_cost"]
                        ))
                    
                    logger.info(f"Added equipment: {equipment['equipment_id']} for property {equipment['property_id']}")
                    
                except Exception as e:
                    logger.error(f"Error inserting equipment {equipment['equipment_id']}: {e}")
                    continue
            
            conn.commit()
            logger.info("Property equipment data initialized successfully!")
            
    except Exception as e:
        logger.error(f"Error initializing equipment data: {e}")

def initialize_maintenance_history():
    """Initialize sample maintenance history data"""
    logger.info("Initializing maintenance history data...")
    
    db_service = get_database_service()
    
    # Sample maintenance records for the past 2 years
    maintenance_types = ["hvac", "plumbing", "electrical", "appliance", "roofing"]
    priorities = ["low", "medium", "high"]
    contractors = ["ABC Maintenance", "Superior HVAC", "Elite Repairs", "Quick Fix Solutions", "Pro Maintenance Co"]
    
    maintenance_records = []
    
    # Generate records for properties 1-10 over past 2 years
    for property_id in range(1, 11):
        for _ in range(random.randint(3, 12)):  # 3-12 maintenance records per property
            # Random date in past 2 years
            days_ago = random.randint(1, 730)
            completed_date = datetime.now() - timedelta(days=days_ago)
            
            maintenance_type = random.choice(maintenance_types)
            equipment_id = f"{maintenance_type.upper()}_{property_id:03d}"
            
            descriptions = {
                "hvac": ["Filter replacement", "System cleaning", "Thermostat calibration", "Duct cleaning", "Annual inspection"],
                "plumbing": ["Pipe repair", "Drain cleaning", "Water heater maintenance", "Fixture replacement", "Leak repair"],
                "electrical": ["Panel inspection", "Outlet replacement", "Lighting repair", "Circuit upgrade", "Safety check"],
                "appliance": ["Refrigerator service", "Washer repair", "Dryer maintenance", "Dishwasher fix", "Range service"],
                "roofing": ["Shingle replacement", "Gutter cleaning", "Leak repair", "Inspection", "Ventilation check"]
            }
            
            record = {
                "property_id": property_id,
                "equipment_id": equipment_id,
                "maintenance_type": maintenance_type,
                "description": random.choice(descriptions[maintenance_type]),
                "completed_date": completed_date.isoformat(),
                "cost": round(random.uniform(50, 1500), 2),
                "priority": random.choice(priorities),
                "contractor": random.choice(contractors),
                "parts_replaced": json.dumps([f"Part-{random.randint(1000, 9999)}"]) if random.random() > 0.5 else "",
                "issue_severity": random.randint(1, 10),
                "customer_satisfaction": random.randint(3, 5),
                "weather_conditions": random.choice(["Clear", "Rainy", "Snow", "Hot", "Cold"]),
                "equipment_age_years": round(random.uniform(0.5, 15), 1),
                "last_maintenance_days": random.randint(30, 365),
                "property_age_years": random.randint(5, 50),
                "tenant_reported": random.choice([True, False])
            }
            
            maintenance_records.append(record)
    
    try:
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            for record in maintenance_records:
                try:
                    if db_service.is_postgres:
                        cursor.execute("""
                            INSERT INTO maintenance_history 
                            (property_id, equipment_id, maintenance_type, description, completed_date, 
                             cost, priority, contractor, parts_replaced, issue_severity, 
                             customer_satisfaction, weather_conditions, equipment_age_years, 
                             last_maintenance_days, property_age_years, tenant_reported)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            record["property_id"], record["equipment_id"], record["maintenance_type"],
                            record["description"], record["completed_date"], record["cost"],
                            record["priority"], record["contractor"], record["parts_replaced"],
                            record["issue_severity"], record["customer_satisfaction"], 
                            record["weather_conditions"], record["equipment_age_years"],
                            record["last_maintenance_days"], record["property_age_years"], 
                            record["tenant_reported"]
                        ))
                    else:
                        cursor.execute("""
                            INSERT INTO maintenance_history 
                            (property_id, equipment_id, maintenance_type, description, completed_date,
                             cost, priority, contractor, parts_replaced, issue_severity,
                             customer_satisfaction, weather_conditions, equipment_age_years,
                             last_maintenance_days, property_age_years, tenant_reported)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            record["property_id"], record["equipment_id"], record["maintenance_type"],
                            record["description"], record["completed_date"], record["cost"],
                            record["priority"], record["contractor"], record["parts_replaced"],
                            record["issue_severity"], record["customer_satisfaction"],
                            record["weather_conditions"], record["equipment_age_years"],
                            record["last_maintenance_days"], record["property_age_years"],
                            1 if record["tenant_reported"] else 0
                        ))
                    
                except Exception as e:
                    logger.error(f"Error inserting maintenance record: {e}")
                    continue
            
            conn.commit()
            logger.info(f"Maintenance history data initialized successfully! Added {len(maintenance_records)} records.")
            
    except Exception as e:
        logger.error(f"Error initializing maintenance history: {e}")

def initialize_ai_analysis_logs():
    """Initialize tables to store AI analysis results"""
    logger.info("Initializing AI analysis logging tables...")
    
    db_service = get_database_service()
    
    try:
        with db_service.get_connection() as conn:
            cursor = conn.cursor()
            
            # Computer Vision analysis logs
            if db_service.is_postgres:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_property_analysis (
                        id SERIAL PRIMARY KEY,
                        property_id INTEGER NOT NULL,
                        image_path TEXT,
                        overall_condition VARCHAR(20),
                        condition_score FLOAT,
                        confidence_score FLOAT,
                        features_detected TEXT,
                        recommendations TEXT,
                        analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_damage_assessment (
                        id SERIAL PRIMARY KEY,
                        property_id INTEGER NOT NULL,
                        image_path TEXT,
                        overall_damage_score FLOAT,
                        urgency_level VARCHAR(20),
                        damage_types TEXT,
                        affected_areas TEXT,
                        estimated_repair_cost FLOAT,
                        confidence_score FLOAT,
                        assessment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_document_processing (
                        id SERIAL PRIMARY KEY,
                        document_type VARCHAR(50),
                        processing_result TEXT,
                        entities_extracted TEXT,
                        risk_assessment TEXT,
                        confidence_score FLOAT,
                        processing_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_property_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        property_id INTEGER NOT NULL,
                        image_path TEXT,
                        overall_condition TEXT,
                        condition_score REAL,
                        confidence_score REAL,
                        features_detected TEXT,
                        recommendations TEXT,
                        analysis_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_damage_assessment (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        property_id INTEGER NOT NULL,
                        image_path TEXT,
                        overall_damage_score REAL,
                        urgency_level TEXT,
                        damage_types TEXT,
                        affected_areas TEXT,
                        estimated_repair_cost REAL,
                        confidence_score REAL,
                        assessment_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_document_processing (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_type TEXT,
                        processing_result TEXT,
                        entities_extracted TEXT,
                        risk_assessment TEXT,
                        confidence_score REAL,
                        processing_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            conn.commit()
            logger.info("AI analysis logging tables initialized successfully!")
            
    except Exception as e:
        logger.error(f"Error initializing AI logging tables: {e}")

def main():
    """Initialize all AI data"""
    logger.info("Starting AI data initialization...")
    
    try:
        initialize_property_equipment()
        initialize_maintenance_history()
        initialize_ai_analysis_logs()
        
        logger.info("✅ AI data initialization completed successfully!")
        logger.info("🎯 AI systems now have live data to work with!")
        
    except Exception as e:
        logger.error(f"❌ AI data initialization failed: {e}")

if __name__ == "__main__":
    main()
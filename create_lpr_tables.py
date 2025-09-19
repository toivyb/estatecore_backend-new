"""
Create LPR database tables
"""

from app import app, db

def create_lpr_tables():
    """Create LPR-related database tables"""
    
    with app.app_context():
        try:
            # Create lpr_events table
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS lpr_events (
                    id SERIAL PRIMARY KEY,
                    plate VARCHAR(20) NOT NULL,
                    confidence DECIMAL(5,2),
                    camera_id VARCHAR(50),
                    image_path TEXT,
                    timestamp VARCHAR(50),
                    is_blacklisted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create indexes for lpr_events
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_lpr_events_plate ON lpr_events (plate)
            """))
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_lpr_events_camera ON lpr_events (camera_id)
            """))
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_lpr_events_created ON lpr_events (created_at)
            """))
            
            # Create lpr_blacklist table
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS lpr_blacklist (
                    id SERIAL PRIMARY KEY,
                    plate VARCHAR(20) NOT NULL UNIQUE,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create index for lpr_blacklist
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_lpr_blacklist_plate ON lpr_blacklist (plate)
            """))
            
            # Create lpr_cameras table for camera management
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS lpr_cameras (
                    id SERIAL PRIMARY KEY,
                    camera_id VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(100),
                    location VARCHAR(200),
                    ftp_username VARCHAR(50),
                    ftp_password VARCHAR(50),
                    rtsp_url TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Create index for lpr_cameras
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_lpr_cameras_camera_id ON lpr_cameras (camera_id)
            """))
            
            # Create lpr_clients table for API clients
            db.session.execute(db.text("""
                CREATE TABLE IF NOT EXISTS lpr_clients (
                    id SERIAL PRIMARY KEY,
                    client_name VARCHAR(100) NOT NULL,
                    api_key VARCHAR(100) NOT NULL UNIQUE,
                    is_active BOOLEAN DEFAULT TRUE,
                    rate_limit_per_hour INTEGER DEFAULT 1000,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used_at TIMESTAMP
                )
            """))
            
            # Create index for lpr_clients
            db.session.execute(db.text("""
                CREATE INDEX IF NOT EXISTS idx_lpr_clients_api_key ON lpr_clients (api_key)
            """))
            
            db.session.commit()
            print("LPR tables created successfully!")
            
            # Insert sample data
            sample_cameras = [
                {'camera_id': 'cam001', 'name': 'Main Entrance', 'location': 'Front Gate', 'ftp_username': 'cam001', 'ftp_password': 'cam001pass'},
                {'camera_id': 'cam002', 'name': 'Back Entrance', 'location': 'Rear Gate', 'ftp_username': 'cam002', 'ftp_password': 'cam002pass'},
                {'camera_id': 'cam003', 'name': 'Parking Lot', 'location': 'Main Parking', 'ftp_username': 'cam003', 'ftp_password': 'cam003pass'},
            ]
            
            for cam in sample_cameras:
                db.session.execute(db.text("""
                    INSERT INTO lpr_cameras (camera_id, name, location, ftp_username, ftp_password)
                    VALUES (:camera_id, :name, :location, :ftp_username, :ftp_password)
                    ON CONFLICT (camera_id) DO NOTHING
                """), cam)
            
            # Insert sample blacklist entries
            sample_blacklist = [
                {'plate': 'ABC123', 'reason': 'Stolen vehicle'},
                {'plate': 'DEF456', 'reason': 'Banned person'},
                {'plate': 'GHI789', 'reason': 'Security concern'},
            ]
            
            for entry in sample_blacklist:
                db.session.execute(db.text("""
                    INSERT INTO lpr_blacklist (plate, reason)
                    VALUES (:plate, :reason)
                    ON CONFLICT (plate) DO NOTHING
                """), entry)
            
            # Insert sample API client
            import uuid
            api_key = f"lpr_{uuid.uuid4().hex}"
            db.session.execute(db.text("""
                INSERT INTO lpr_clients (client_name, api_key)
                VALUES (:client_name, :api_key)
                ON CONFLICT (api_key) DO NOTHING
            """), {'client_name': 'Demo Client', 'api_key': api_key})
            
            db.session.commit()
            print("Sample data inserted!")
            print(f"Demo API key: {api_key}")
            
        except Exception as e:
            print(f"Error creating tables: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    create_lpr_tables()
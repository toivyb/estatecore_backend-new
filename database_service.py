"""
Database Service for EstateCore
Provides real database operations to replace mock endpoints
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    database_url: str
    min_connections: int = 1
    max_connections: int = 20
    use_ssl: bool = True
    
class DatabaseService:
    def __init__(self, config: DatabaseConfig = None):
        """Initialize database service"""
        self.config = config or self._get_default_config()
        self.pool = None
        self.is_postgres = self.config.database_url.startswith(('postgres', 'postgresql'))
        self._initialize_connection_pool()
        
    def _get_default_config(self) -> DatabaseConfig:
        """Get database configuration from environment"""
        database_url = os.getenv('DATABASE_URL', 'sqlite:///estatecore.db')
        
        # Handle Render's postgres:// URLs
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
            
        return DatabaseConfig(
            database_url=database_url,
            min_connections=int(os.getenv('DB_MIN_CONNECTIONS', '1')),
            max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '20'))
        )
    
    def _initialize_connection_pool(self):
        """Initialize database connection pool"""
        try:
            if self.is_postgres:
                self.pool = ThreadedConnectionPool(
                    self.config.min_connections,
                    self.config.max_connections,
                    self.config.database_url
                )
                logger.info("PostgreSQL connection pool initialized")
            else:
                # SQLite doesn't use connection pooling
                logger.info("SQLite database configured")
                self._ensure_sqlite_tables()
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        if self.is_postgres:
            conn = self.pool.getconn()
            try:
                yield conn
            finally:
                self.pool.putconn(conn)
        else:
            conn = sqlite3.connect(self.config.database_url.replace('sqlite:///', ''))
            conn.row_factory = sqlite3.Row
            try:
                yield conn
            finally:
                conn.close()
    
    def _ensure_sqlite_tables(self):
        """Create SQLite tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    phone VARCHAR(20),
                    role VARCHAR(50) DEFAULT 'tenant',
                    is_active BOOLEAN DEFAULT 1,
                    is_deleted BOOLEAN DEFAULT 0,
                    password_hash VARCHAR(255),
                    temporary_password VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    deleted_at TIMESTAMP
                )
            ''')
            
            # Properties table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    address VARCHAR(500),
                    city VARCHAR(100),
                    state VARCHAR(50),
                    zip_code VARCHAR(20),
                    property_type VARCHAR(50),
                    total_units INTEGER DEFAULT 0,
                    year_built INTEGER,
                    square_footage INTEGER,
                    description TEXT,
                    amenities TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tenants table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tenants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    property_id INTEGER,
                    unit_number VARCHAR(20),
                    lease_start_date DATE,
                    lease_end_date DATE,
                    rent_amount DECIMAL(10,2),
                    security_deposit DECIMAL(10,2),
                    status VARCHAR(50) DEFAULT 'active',
                    move_in_date DATE,
                    move_out_date DATE,
                    emergency_contact_name VARCHAR(255),
                    emergency_contact_phone VARCHAR(20),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (property_id) REFERENCES properties(id)
                )
            ''')
            
            # Maintenance requests table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS maintenance_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    property_id INTEGER,
                    tenant_id INTEGER,
                    unit_number VARCHAR(20),
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    priority VARCHAR(20) DEFAULT 'medium',
                    status VARCHAR(50) DEFAULT 'open',
                    category VARCHAR(50),
                    assigned_to VARCHAR(255),
                    estimated_cost DECIMAL(10,2),
                    actual_cost DECIMAL(10,2),
                    scheduled_date TIMESTAMP,
                    completed_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES properties(id),
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                )
            ''')
            
            # Payments table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id INTEGER,
                    property_id INTEGER,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_type VARCHAR(50),
                    payment_method VARCHAR(50),
                    payment_date DATE,
                    due_date DATE,
                    status VARCHAR(50) DEFAULT 'pending',
                    transaction_id VARCHAR(255),
                    stripe_payment_intent_id VARCHAR(255),
                    description TEXT,
                    late_fee DECIMAL(10,2) DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                    FOREIGN KEY (property_id) REFERENCES properties(id)
                )
            ''')
            
            # Documents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    file_path VARCHAR(500),
                    file_size INTEGER,
                    file_type VARCHAR(50),
                    category VARCHAR(50),
                    description TEXT,
                    property_id INTEGER,
                    tenant_id INTEGER,
                    folder_id INTEGER,
                    uploaded_by INTEGER,
                    is_public BOOLEAN DEFAULT 0,
                    tags TEXT,
                    version INTEGER DEFAULT 1,
                    checksum VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (property_id) REFERENCES properties(id),
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id),
                    FOREIGN KEY (uploaded_by) REFERENCES users(id)
                )
            ''')
            
            # Document folders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS document_folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    parent_id INTEGER,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES document_folders(id)
                )
            ''')
            
            # Notifications table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title VARCHAR(255) NOT NULL,
                    message TEXT,
                    type VARCHAR(50),
                    priority VARCHAR(20) DEFAULT 'medium',
                    is_read BOOLEAN DEFAULT 0,
                    action_url VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')
            
            conn.commit()
            logger.info("SQLite tables created/verified")
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = None) -> Any:
        """Execute database query"""
        try:
            with self.get_connection() as conn:
                if self.is_postgres:
                    cursor = conn.cursor(cursor_factory=RealDictCursor)
                else:
                    cursor = conn.cursor()
                
                cursor.execute(query, params or ())
                
                if fetch == 'one':
                    result = cursor.fetchone()
                elif fetch == 'all':
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount
                
                conn.commit()
                return result
                
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise
    
    # User operations
    def get_users(self, active_only: bool = True) -> List[Dict]:
        """Get all users"""
        where_clause = "WHERE is_deleted = 0" if active_only else ""
        if self.is_postgres:
            where_clause += " AND is_deleted = false" if active_only else ""
        
        query = f"""
            SELECT id, email, first_name, last_name, phone, role, is_active, 
                   created_at, updated_at
            FROM users 
            {where_clause}
            ORDER BY created_at DESC
        """
        
        result = self.execute_query(query, fetch='all')
        return [dict(row) for row in result] if result else []
    
    def create_user(self, user_data: Dict) -> Dict:
        """Create new user"""
        query = """
            INSERT INTO users (email, first_name, last_name, phone, role, 
                             password_hash, temporary_password, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.utcnow()
        params = (
            user_data.get('email'),
            user_data.get('first_name', ''),
            user_data.get('last_name', ''),
            user_data.get('phone', ''),
            user_data.get('role', 'tenant'),
            user_data.get('password_hash', ''),
            user_data.get('temporary_password', ''),
            now,
            now
        )
        
        self.execute_query(query, params)
        
        # Get the created user
        return self.get_user_by_email(user_data.get('email'))
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = ? AND is_deleted = 0"
        result = self.execute_query(query, (email,), fetch='one')
        return dict(result) if result else None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = ? AND is_deleted = 0"
        result = self.execute_query(query, (user_id,), fetch='one')
        return dict(result) if result else None
    
    def update_user(self, user_id: int, user_data: Dict) -> bool:
        """Update user"""
        query = """
            UPDATE users 
            SET first_name = ?, last_name = ?, phone = ?, role = ?, 
                is_active = ?, updated_at = ?
            WHERE id = ? AND is_deleted = 0
        """
        
        params = (
            user_data.get('first_name', ''),
            user_data.get('last_name', ''),
            user_data.get('phone', ''),
            user_data.get('role', 'tenant'),
            user_data.get('is_active', True),
            datetime.utcnow(),
            user_id
        )
        
        return self.execute_query(query, params) > 0
    
    def delete_user(self, user_id: int) -> bool:
        """Soft delete user"""
        query = """
            UPDATE users 
            SET is_deleted = 1, deleted_at = ?, updated_at = ?
            WHERE id = ?
        """
        
        now = datetime.utcnow()
        return self.execute_query(query, (now, now, user_id)) > 0
    
    # Property operations
    def get_properties(self, active_only: bool = True) -> List[Dict]:
        """Get all properties"""
        where_clause = "WHERE is_active = 1" if active_only else ""
        
        query = f"""
            SELECT id, name, address, city, state, zip_code, property_type,
                   total_units, year_built, square_footage, description, 
                   amenities, is_active, created_at, updated_at
            FROM properties 
            {where_clause}
            ORDER BY name
        """
        
        result = self.execute_query(query, fetch='all')
        return [dict(row) for row in result] if result else []
    
    def create_property(self, property_data: Dict) -> Dict:
        """Create new property"""
        query = """
            INSERT INTO properties (name, address, city, state, zip_code, 
                                  property_type, total_units, year_built, 
                                  square_footage, description, amenities, 
                                  created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.utcnow()
        params = (
            property_data.get('name'),
            property_data.get('address'),
            property_data.get('city'),
            property_data.get('state'),
            property_data.get('zip_code'),
            property_data.get('property_type', 'APARTMENT'),
            property_data.get('total_units', 0),
            property_data.get('year_built'),
            property_data.get('square_footage'),
            property_data.get('description', ''),
            json.dumps(property_data.get('amenities', [])),
            now,
            now
        )
        
        self.execute_query(query, params)
        
        # Get the created property
        query = "SELECT * FROM properties WHERE name = ? ORDER BY id DESC LIMIT 1"
        result = self.execute_query(query, (property_data.get('name'),), fetch='one')
        return dict(result) if result else None
    
    # Tenant operations
    def get_tenants(self, property_id: int = None) -> List[Dict]:
        """Get tenants with user and property information"""
        query = """
            SELECT t.*, u.email, u.first_name, u.last_name, u.phone,
                   p.name as property_name, p.address as property_address
            FROM tenants t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN properties p ON t.property_id = p.id
            WHERE t.status != 'inactive'
        """
        
        params = ()
        if property_id:
            query += " AND t.property_id = ?"
            params = (property_id,)
        
        query += " ORDER BY t.created_at DESC"
        
        result = self.execute_query(query, params, fetch='all')
        return [dict(row) for row in result] if result else []
    
    def create_tenant(self, tenant_data: Dict) -> Dict:
        """Create new tenant"""
        query = """
            INSERT INTO tenants (user_id, property_id, unit_number, lease_start_date,
                               lease_end_date, rent_amount, security_deposit, status,
                               move_in_date, emergency_contact_name, emergency_contact_phone,
                               created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.utcnow()
        params = (
            tenant_data.get('user_id'),
            tenant_data.get('property_id'),
            tenant_data.get('unit_number'),
            tenant_data.get('lease_start_date'),
            tenant_data.get('lease_end_date'),
            tenant_data.get('rent_amount', 0),
            tenant_data.get('security_deposit', 0),
            tenant_data.get('status', 'active'),
            tenant_data.get('move_in_date'),
            tenant_data.get('emergency_contact_name', ''),
            tenant_data.get('emergency_contact_phone', ''),
            now,
            now
        )
        
        self.execute_query(query, params)
        
        # Get the created tenant
        query = """
            SELECT t.*, u.email, u.first_name, u.last_name, p.name as property_name
            FROM tenants t
            LEFT JOIN users u ON t.user_id = u.id
            LEFT JOIN properties p ON t.property_id = p.id
            WHERE t.user_id = ? AND t.property_id = ?
            ORDER BY t.id DESC LIMIT 1
        """
        
        result = self.execute_query(query, (tenant_data.get('user_id'), tenant_data.get('property_id')), fetch='one')
        return dict(result) if result else None
    
    # Maintenance operations
    def get_maintenance_requests(self, property_id: int = None, status: str = None) -> List[Dict]:
        """Get maintenance requests"""
        query = """
            SELECT m.*, p.name as property_name, p.address as property_address,
                   u.first_name, u.last_name, u.email as tenant_email
            FROM maintenance_requests m
            LEFT JOIN properties p ON m.property_id = p.id
            LEFT JOIN tenants t ON m.tenant_id = t.id
            LEFT JOIN users u ON t.user_id = u.id
            WHERE 1=1
        """
        
        params = []
        if property_id:
            query += " AND m.property_id = ?"
            params.append(property_id)
        
        if status:
            query += " AND m.status = ?"
            params.append(status)
        
        query += " ORDER BY m.created_at DESC"
        
        result = self.execute_query(query, tuple(params), fetch='all')
        return [dict(row) for row in result] if result else []
    
    def create_maintenance_request(self, request_data: Dict) -> Dict:
        """Create maintenance request"""
        query = """
            INSERT INTO maintenance_requests (property_id, tenant_id, unit_number,
                                            title, description, priority, status,
                                            category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.utcnow()
        params = (
            request_data.get('property_id'),
            request_data.get('tenant_id'),
            request_data.get('unit_number'),
            request_data.get('title'),
            request_data.get('description', ''),
            request_data.get('priority', 'medium'),
            request_data.get('status', 'open'),
            request_data.get('category', 'general'),
            now,
            now
        )
        
        self.execute_query(query, params)
        
        # Get the created request
        query = """
            SELECT m.*, p.name as property_name
            FROM maintenance_requests m
            LEFT JOIN properties p ON m.property_id = p.id
            WHERE m.title = ? AND m.property_id = ?
            ORDER BY m.id DESC LIMIT 1
        """
        
        result = self.execute_query(query, (request_data.get('title'), request_data.get('property_id')), fetch='one')
        return dict(result) if result else None
    
    # Payment operations
    def get_payments(self, tenant_id: int = None, property_id: int = None) -> List[Dict]:
        """Get payments"""
        query = """
            SELECT p.*, t.unit_number, prop.name as property_name,
                   u.first_name, u.last_name, u.email as tenant_email
            FROM payments p
            LEFT JOIN tenants t ON p.tenant_id = t.id
            LEFT JOIN properties prop ON p.property_id = prop.id
            LEFT JOIN users u ON t.user_id = u.id
            WHERE 1=1
        """
        
        params = []
        if tenant_id:
            query += " AND p.tenant_id = ?"
            params.append(tenant_id)
        
        if property_id:
            query += " AND p.property_id = ?"
            params.append(property_id)
        
        query += " ORDER BY p.created_at DESC"
        
        result = self.execute_query(query, tuple(params), fetch='all')
        return [dict(row) for row in result] if result else []
    
    def create_payment(self, payment_data: Dict) -> Dict:
        """Create payment record"""
        query = """
            INSERT INTO payments (tenant_id, property_id, amount, payment_type,
                                payment_method, payment_date, due_date, status,
                                transaction_id, stripe_payment_intent_id, description,
                                created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.utcnow()
        params = (
            payment_data.get('tenant_id'),
            payment_data.get('property_id'),
            payment_data.get('amount'),
            payment_data.get('payment_type', 'rent'),
            payment_data.get('payment_method', 'online'),
            payment_data.get('payment_date', now.date()),
            payment_data.get('due_date'),
            payment_data.get('status', 'completed'),
            payment_data.get('transaction_id'),
            payment_data.get('stripe_payment_intent_id'),
            payment_data.get('description', ''),
            now,
            now
        )
        
        self.execute_query(query, params)
        
        # Get the created payment
        query = """
            SELECT p.*, prop.name as property_name, t.unit_number
            FROM payments p
            LEFT JOIN properties prop ON p.property_id = prop.id
            LEFT JOIN tenants t ON p.tenant_id = t.id
            WHERE p.transaction_id = ?
            ORDER BY p.id DESC LIMIT 1
        """
        
        result = self.execute_query(query, (payment_data.get('transaction_id'),), fetch='one')
        return dict(result) if result else None
    
    # Analytics operations
    def get_analytics_data(self, days: int = 30) -> Dict:
        """Get analytics data for dashboard"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Total properties
        total_properties = self.execute_query(
            "SELECT COUNT(*) as count FROM properties WHERE is_active = 1",
            fetch='one'
        )
        
        # Total tenants
        total_tenants = self.execute_query(
            "SELECT COUNT(*) as count FROM tenants WHERE status = 'active'",
            fetch='one'
        )
        
        # Total revenue (last 30 days)
        total_revenue = self.execute_query(
            "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE payment_date >= ? AND status = 'completed'",
            (start_date.date(),),
            fetch='one'
        )
        
        # Maintenance requests by status
        maintenance_stats = self.execute_query(
            "SELECT status, COUNT(*) as count FROM maintenance_requests GROUP BY status",
            fetch='all'
        )
        
        # Recent payments
        recent_payments = self.execute_query(
            """
            SELECT p.amount, p.payment_date, prop.name as property_name, t.unit_number
            FROM payments p
            LEFT JOIN properties prop ON p.property_id = prop.id
            LEFT JOIN tenants t ON p.tenant_id = t.id
            WHERE p.payment_date >= ?
            ORDER BY p.payment_date DESC
            LIMIT 10
            """,
            (start_date.date(),),
            fetch='all'
        )
        
        return {
            'overview': {
                'total_properties': total_properties['count'] if total_properties else 0,
                'total_tenants': total_tenants['count'] if total_tenants else 0,
                'total_revenue': float(total_revenue['total']) if total_revenue else 0,
                'maintenance_requests': {dict(row)['status']: dict(row)['count'] for row in maintenance_stats} if maintenance_stats else {}
            },
            'recent_payments': [dict(row) for row in recent_payments] if recent_payments else [],
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }

# Singleton instance
_db_service = None

def get_database_service() -> DatabaseService:
    """Get singleton database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service

def initialize_database():
    """Initialize database and create tables"""
    service = get_database_service()
    logger.info("Database service initialized successfully")
    return service

if __name__ == "__main__":
    # Test database service
    service = initialize_database()
    
    # Test basic operations
    try:
        # Test user creation
        test_user = service.create_user({
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'tenant'
        })
        print(f"✅ Test user created: {test_user}")
        
        # Test property creation
        test_property = service.create_property({
            'name': 'Test Property',
            'address': '123 Test St',
            'city': 'Test City',
            'state': 'TS',
            'zip_code': '12345',
            'property_type': 'APARTMENT'
        })
        print(f"✅ Test property created: {test_property}")
        
        print("✅ Database service is working correctly!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
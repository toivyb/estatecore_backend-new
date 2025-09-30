#!/usr/bin/env python3
"""
Database connection and data access layer for EstateCore
Handles all database operations and provides data models
"""

import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

DATABASE_PATH = "estatecore.db"

def get_db_connection():
    """Get database connection with row factory"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

class DatabaseManager:
    """Handles all database operations"""
    
    @staticmethod
    def execute_query(query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False):
        """Execute a database query and return results"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(query, params)
            
            if fetch_one:
                result = cursor.fetchone()
                return dict(result) if result else None
            elif fetch_all:
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                conn.commit()
                # Return rowcount for DELETE/UPDATE, lastrowid for INSERT
                if query.strip().upper().startswith(('DELETE', 'UPDATE')):
                    return cursor.rowcount
                else:
                    return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_companies() -> List[Dict]:
        """Get all companies"""
        query = "SELECT * FROM companies ORDER BY name"
        return DatabaseManager.execute_query(query, fetch_all=True)
    
    @staticmethod
    def get_company_by_id(company_id: int) -> Optional[Dict]:
        """Get company by ID"""
        query = "SELECT * FROM companies WHERE id = ?"
        return DatabaseManager.execute_query(query, (company_id,), fetch_one=True)
    
    @staticmethod
    def create_company(company_data: Dict) -> int:
        """Create a new company"""
        try:
            query = """
                INSERT INTO companies (name, subscription_plan, billing_email, created_at, status, 
                                     trial_ends_at, custom_domain, logo_url, phone, address, 
                                     payment_method, auto_billing, mrr_override)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                company_data['name'],
                company_data.get('subscription_plan', 'basic'),
                company_data['billing_email'],
                company_data.get('created_at', datetime.now().isoformat()),
                company_data.get('status', 'active'),
                company_data.get('trial_ends_at'),
                company_data.get('custom_domain'),
                company_data.get('logo_url'),
                company_data.get('phone'),
                company_data.get('address'),
                company_data.get('payment_method', 'card'),
                company_data.get('auto_billing', True),
                company_data.get('mrr_override')
            )
            print(f"Creating company with params: {params}")
            return DatabaseManager.execute_query(query, params)
        except Exception as e:
            print(f"Database error in create_company: {str(e)}")
            raise Exception(f"Failed to create company: {str(e)}")
    
    @staticmethod
    def update_company(company_id: int, company_data: Dict) -> bool:
        """Update company information"""
        query = """
            UPDATE companies 
            SET name=?, subscription_plan=?, billing_email=?, status=?, 
                trial_ends_at=?, custom_domain=?, logo_url=?, phone=?, 
                address=?, payment_method=?, auto_billing=?, mrr_override=?,
                updated_at=?
            WHERE id=?
        """
        params = (
            company_data['name'],
            company_data['subscription_plan'],
            company_data['billing_email'],
            company_data['status'],
            company_data.get('trial_ends_at'),
            company_data.get('custom_domain'),
            company_data.get('logo_url'),
            company_data.get('phone'),
            company_data.get('address'),
            company_data.get('payment_method', 'card'),
            company_data.get('auto_billing', True),
            company_data.get('mrr_override'),
            datetime.now().isoformat(),
            company_id
        )
        DatabaseManager.execute_query(query, params)
        return True
    
    @staticmethod
    def delete_company(company_id: int) -> bool:
        """Delete a company"""
        query = "DELETE FROM companies WHERE id = ?"
        DatabaseManager.execute_query(query, (company_id,))
        return True
    
    @staticmethod
    def get_users() -> List[Dict]:
        """Get all users"""
        query = "SELECT * FROM users ORDER BY name"
        return DatabaseManager.execute_query(query, fetch_all=True)
    
    @staticmethod
    def get_user_by_id(user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = "SELECT * FROM users WHERE id = ?"
        return DatabaseManager.execute_query(query, (user_id,), fetch_one=True)
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        """Get user by email"""
        query = "SELECT * FROM users WHERE email = ?"
        return DatabaseManager.execute_query(query, (email,), fetch_one=True)
    
    @staticmethod
    def create_user(user_data: Dict) -> int:
        """Create a new user"""
        query = """
            INSERT INTO users (name, email, company_id, role, password_hash, 
                             otp, is_first_login, phone, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            user_data['name'],
            user_data['email'],
            user_data.get('company_id'),
            user_data['role'],
            user_data.get('password_hash'),
            user_data.get('otp'),
            user_data.get('is_first_login', True),
            user_data.get('phone'),
            user_data.get('status', 'active')
        )
        return DatabaseManager.execute_query(query, params)
    
    @staticmethod
    def update_user(user_id: int, user_data: Dict) -> bool:
        """Update user information"""
        query = """
            UPDATE users 
            SET name=?, email=?, company_id=?, role=?, password_hash=?, 
                otp=?, is_first_login=?, phone=?, status=?, updated_at=?
            WHERE id=?
        """
        params = (
            user_data['name'],
            user_data['email'],
            user_data.get('company_id'),
            user_data['role'],
            user_data.get('password_hash'),
            user_data.get('otp'),
            user_data.get('is_first_login'),
            user_data.get('phone'),
            user_data.get('status'),
            datetime.now().isoformat(),
            user_id
        )
        DatabaseManager.execute_query(query, params)
        return True
    
    @staticmethod
    def get_properties() -> List[Dict]:
        """Get all properties"""
        query = "SELECT * FROM properties ORDER BY name"
        return DatabaseManager.execute_query(query, fetch_all=True)
    
    @staticmethod
    def get_property_by_id(property_id: int) -> Optional[Dict]:
        """Get property by ID"""
        query = "SELECT * FROM properties WHERE id = ?"
        return DatabaseManager.execute_query(query, (property_id,), fetch_one=True)
    
    @staticmethod
    def get_properties_by_company(company_id: int) -> List[Dict]:
        """Get properties for a specific company"""
        query = "SELECT * FROM properties WHERE company_id = ? ORDER BY name"
        return DatabaseManager.execute_query(query, (company_id,), fetch_all=True)
    
    @staticmethod
    def create_property(property_data: Dict) -> int:
        """Create a new property"""
        query = """
            INSERT INTO properties (name, address, units, occupied_units, rent_amount, 
                                  company_id, property_manager_id, type, bedrooms, 
                                  bathrooms, description, is_available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            property_data['name'],
            property_data['address'],
            property_data.get('units', 1),
            property_data.get('occupied_units', 0),
            property_data.get('rent_amount'),
            property_data['company_id'],
            property_data.get('property_manager_id'),
            property_data.get('type', 'apartment'),
            property_data.get('bedrooms'),
            property_data.get('bathrooms'),
            property_data.get('description'),
            property_data.get('is_available', True)
        )
        return DatabaseManager.execute_query(query, params)
    
    @staticmethod
    def update_property(property_id: int, property_data: Dict) -> bool:
        """Update property information"""
        query = """
            UPDATE properties 
            SET name=?, address=?, units=?, occupied_units=?, rent_amount=?, 
                company_id=?, property_manager_id=?, type=?, bedrooms=?, 
                bathrooms=?, description=?, is_available=?, updated_at=?
            WHERE id=?
        """
        params = (
            property_data['name'],
            property_data['address'],
            property_data.get('units', 1),
            property_data.get('occupied_units', 0),
            property_data.get('rent_amount'),
            property_data['company_id'],
            property_data.get('property_manager_id'),
            property_data.get('type', 'apartment'),
            property_data.get('bedrooms'),
            property_data.get('bathrooms'),
            property_data.get('description'),
            property_data.get('is_available', True),
            datetime.now().isoformat(),
            property_id
        )
        DatabaseManager.execute_query(query, params)
        return True
    
    @staticmethod
    def get_tenants() -> List[Dict]:
        """Get all tenants"""
        query = "SELECT * FROM tenants ORDER BY name"
        return DatabaseManager.execute_query(query, fetch_all=True)
    
    @staticmethod
    def get_tenant_by_id(tenant_id: int) -> Optional[Dict]:
        """Get tenant by ID"""
        query = "SELECT * FROM tenants WHERE id = ?"
        return DatabaseManager.execute_query(query, (tenant_id,), fetch_one=True)
    
    @staticmethod
    def get_tenants_by_property(property_id: int) -> List[Dict]:
        """Get tenants for a specific property"""
        query = "SELECT * FROM tenants WHERE property_id = ? ORDER BY name"
        return DatabaseManager.execute_query(query, (property_id,), fetch_all=True)
    
    @staticmethod
    def create_tenant(tenant_data: Dict) -> int:
        """Create a new tenant"""
        query = """
            INSERT INTO tenants (name, email, phone, property_id, unit_id, unit_number,
                               lease_start_date, lease_end_date, rent_amount, 
                               security_deposit, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            tenant_data['name'],
            tenant_data.get('email'),
            tenant_data.get('phone'),
            tenant_data['property_id'],
            tenant_data.get('unit_id'),
            tenant_data.get('unit_number'),
            tenant_data.get('lease_start_date'),
            tenant_data.get('lease_end_date'),
            tenant_data.get('rent_amount'),
            tenant_data.get('security_deposit'),
            tenant_data.get('status', 'active')
        )
        return DatabaseManager.execute_query(query, params)
    
    @staticmethod
    def get_payments() -> List[Dict]:
        """Get all payments"""
        query = "SELECT * FROM payments ORDER BY payment_date DESC"
        return DatabaseManager.execute_query(query, fetch_all=True)
    
    @staticmethod
    def get_payments_by_tenant(tenant_id: int) -> List[Dict]:
        """Get payments for a specific tenant"""
        query = "SELECT * FROM payments WHERE tenant_id = ? ORDER BY payment_date DESC"
        return DatabaseManager.execute_query(query, (tenant_id,), fetch_all=True)
    
    @staticmethod
    def delete_tenant(tenant_id: int) -> bool:
        """Delete a tenant"""
        query = "DELETE FROM tenants WHERE id = ?"
        DatabaseManager.execute_query(query, (tenant_id,))
        return True
    
    @staticmethod
    def create_payment(payment_data: Dict) -> int:
        """Create a new payment record"""
        query = """
            INSERT INTO payments (tenant_id, property_id, amount, payment_type, 
                                payment_method, status, payment_date, due_date, 
                                description, receipt_number, processing_fee, net_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            payment_data['tenant_id'],
            payment_data['property_id'],
            payment_data['amount'],
            payment_data['payment_type'],
            payment_data.get('payment_method', 'credit_card'),
            payment_data.get('status', 'pending'),
            payment_data.get('payment_date'),
            payment_data.get('due_date'),
            payment_data.get('description'),
            payment_data.get('receipt_number'),
            payment_data.get('processing_fee', 0),
            payment_data.get('net_amount')
        )
        return DatabaseManager.execute_query(query, params)
    
    @staticmethod
    def get_maintenance_requests() -> List[Dict]:
        """Get all maintenance requests"""
        query = "SELECT * FROM maintenance_requests ORDER BY created_at DESC"
        return DatabaseManager.execute_query(query, fetch_all=True)
    
    @staticmethod
    def get_maintenance_by_property(property_id: int) -> List[Dict]:
        """Get maintenance requests for a specific property"""
        query = "SELECT * FROM maintenance_requests WHERE property_id = ? ORDER BY created_at DESC"
        return DatabaseManager.execute_query(query, (property_id,), fetch_all=True)
    
    @staticmethod
    def create_maintenance_request(maintenance_data: Dict) -> int:
        """Create a new maintenance request"""
        query = """
            INSERT INTO maintenance_requests (property_id, unit_id, tenant_id, title, 
                                            description, priority, status, assigned_to, 
                                            estimated_cost, actual_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            maintenance_data['property_id'],
            maintenance_data.get('unit_id'),
            maintenance_data.get('tenant_id'),
            maintenance_data['title'],
            maintenance_data.get('description'),
            maintenance_data.get('priority', 'medium'),
            maintenance_data.get('status', 'open'),
            maintenance_data.get('assigned_to'),
            maintenance_data.get('estimated_cost'),
            maintenance_data.get('actual_cost')
        )
        return DatabaseManager.execute_query(query, params)
    
    # =================== UNITS METHODS ===================
    
    @staticmethod
    def get_units_by_property(property_id: int) -> List[Dict]:
        """Get all units for a specific property"""
        query = """
            SELECT * FROM units 
            WHERE property_id = ? 
            ORDER BY unit_number
        """
        return DatabaseManager.execute_query(query, (property_id,), fetch_all=True)
    
    @staticmethod
    def get_unit_by_id(unit_id: int) -> Optional[Dict]:
        """Get unit by ID"""
        query = "SELECT * FROM units WHERE id = ?"
        return DatabaseManager.execute_query(query, (unit_id,), fetch_one=True)
    
    @staticmethod
    def create_unit(unit_data: Dict) -> int:
        """Create a new unit"""
        query = """
            INSERT INTO units (property_id, unit_number, bedrooms, bathrooms, 
                             square_feet, rent, status, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            unit_data['property_id'],
            unit_data['unit_number'],
            unit_data.get('bedrooms', 1),
            unit_data.get('bathrooms', 1),
            unit_data.get('square_feet', 0),
            unit_data.get('rent', 0),
            unit_data.get('status', 'vacant'),
            unit_data.get('description', ''),
            unit_data.get('created_at'),
            unit_data.get('updated_at')
        )
        return DatabaseManager.execute_query(query, params)
    
    @staticmethod
    def update_unit(unit_id: int, unit_data: Dict) -> bool:
        """Update an existing unit"""
        # Build dynamic update query based on provided fields
        fields = []
        params = []
        
        updateable_fields = ['unit_number', 'bedrooms', 'bathrooms', 'square_feet', 
                           'rent', 'status', 'description', 'updated_at']
        
        for field in updateable_fields:
            if field in unit_data:
                fields.append(f"{field} = ?")
                params.append(unit_data[field])
        
        if not fields:
            return False
        
        params.append(unit_id)
        query = f"UPDATE units SET {', '.join(fields)} WHERE id = ?"
        
        rows_affected = DatabaseManager.execute_query(query, params)
        return rows_affected > 0
    
    @staticmethod
    def delete_unit(unit_id: int) -> bool:
        """Delete a unit"""
        query = "DELETE FROM units WHERE id = ?"
        rows_affected = DatabaseManager.execute_query(query, (unit_id,))
        return rows_affected > 0

# Data model classes that work with the database
class Company:
    def __init__(self, data: Dict):
        """Initialize Company from database row"""
        self.id = data['id']
        self.name = data['name']
        self.subscription_plan = data['subscription_plan']
        self.billing_email = data['billing_email']
        self.created_at = data['created_at']
        self.status = data['status']
        self.trial_ends_at = data.get('trial_ends_at')
        self.custom_domain = data.get('custom_domain')
        self.logo_url = data.get('logo_url')
        self.phone = data.get('phone')
        self.address = data.get('address')
        self.payment_method = data.get('payment_method', 'card')
        self.auto_billing = bool(data.get('auto_billing', True))
        self.mrr_override = data.get('mrr_override')
    
    def calculate_monthly_fee(self, total_units=0):
        """Calculate monthly fee based on units and plan"""
        if self.mrr_override:
            return self.mrr_override
            
        unit_prices = {
            'trial': 0.0,
            'basic': 2.0, 
            'premium': 2.5,
            'enterprise': 3.0
        }
        unit_price = unit_prices.get(self.subscription_plan, 2.0)
        return total_units * unit_price
    
    @property
    def monthly_fee(self):
        """Calculate based on company's total units"""
        company_properties = DatabaseManager.get_properties_by_company(self.id)
        total_units = sum(p['units'] for p in company_properties)
        return self.calculate_monthly_fee(total_units)

class User:
    def __init__(self, data: Dict):
        """Initialize User from database row"""
        self.id = data['id']
        self.name = data['name']
        self.email = data['email']
        self.company_id = data.get('company_id')
        self.role = data['role']
        self.password_hash = data.get('password_hash')
        self.otp = data.get('otp')
        self.is_first_login = bool(data.get('is_first_login', True))
        self.last_login = data.get('last_login')
        self.status = data.get('status', 'active')
        self.phone = data.get('phone')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
    
    def generate_otp(self, length=8):
        """Generate a new OTP for the user"""
        import secrets
        import string
        characters = string.ascii_letters + string.digits
        self.otp = ''.join(secrets.choice(characters) for _ in range(length))
        return self.otp
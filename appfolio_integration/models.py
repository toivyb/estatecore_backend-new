"""
AppFolio Integration Data Models

Core data models for AppFolio integration including property management,
investment management, financial data, and enterprise features.
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

class PropertyType(Enum):
    """Property types in AppFolio"""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    RETAIL = "retail"
    OFFICE = "office"
    INDUSTRIAL = "industrial"
    LAND = "land"
    PARKING = "parking"

class UnitType(Enum):
    """Unit types in AppFolio"""
    APARTMENT = "apartment"
    HOUSE = "house"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    STUDIO = "studio"
    ROOM = "room"
    COMMERCIAL_SPACE = "commercial_space"
    PARKING_SPACE = "parking_space"
    STORAGE = "storage"

class LeaseStatus(Enum):
    """Lease status in AppFolio"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"
    CANCELLED = "cancelled"

class PaymentStatus(Enum):
    """Payment status in AppFolio"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    PARTIAL = "partial"

class WorkOrderStatus(Enum):
    """Work order status in AppFolio"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class WorkOrderPriority(Enum):
    """Work order priority in AppFolio"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"

@dataclass
class AppFolioProperty:
    """AppFolio Property model"""
    id: str
    name: str
    address: Dict[str, str]
    property_type: PropertyType
    unit_count: int
    portfolio_id: Optional[str] = None
    manager_id: Optional[str] = None
    description: Optional[str] = None
    year_built: Optional[int] = None
    square_footage: Optional[float] = None
    lot_size: Optional[float] = None
    amenities: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    
    # Investment tracking
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[float] = None
    current_value: Optional[float] = None
    
    # Financial tracking
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    net_operating_income: Optional[float] = None
    cap_rate: Optional[float] = None
    
    # Management info
    management_company: Optional[str] = None
    management_fee_percentage: Optional[float] = None
    insurance_carrier: Optional[str] = None
    insurance_policy_number: Optional[str] = None

@dataclass
class AppFolioUnit:
    """AppFolio Unit model"""
    id: str
    property_id: str
    unit_number: str
    unit_type: UnitType
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[float] = None
    rent_amount: Optional[float] = None
    security_deposit: Optional[float] = None
    available_date: Optional[date] = None
    lease_id: Optional[str] = None
    tenant_id: Optional[str] = None
    amenities: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    
    # Rental tracking
    market_rent: Optional[float] = None
    last_rent_increase: Optional[date] = None
    next_rent_review: Optional[date] = None
    
    # Maintenance
    last_inspection: Optional[date] = None
    next_inspection: Optional[date] = None
    maintenance_notes: Optional[str] = None

@dataclass
class AppFolioTenant:
    """AppFolio Tenant/Resident model"""
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    emergency_contact: Optional[Dict[str, str]] = None
    employment_info: Optional[Dict[str, Any]] = None
    background_check_status: Optional[str] = None
    credit_score: Optional[int] = None
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    
    # Contact preferences
    preferred_contact_method: Optional[str] = None
    communication_preferences: Dict[str, bool] = field(default_factory=dict)
    
    # Financial
    monthly_income: Optional[float] = None
    debt_to_income_ratio: Optional[float] = None
    
    # Additional residents
    additional_residents: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class AppFolioLease:
    """AppFolio Lease model"""
    id: str
    property_id: str
    unit_id: str
    tenant_id: str
    start_date: date
    end_date: date
    status: LeaseStatus
    rent_amount: float
    security_deposit: Optional[float] = None
    pet_deposit: Optional[float] = None
    lease_terms: Optional[str] = None
    auto_renew: bool = False
    renewal_notice_days: Optional[int] = None
    rent_due_day: int = 1
    late_fee_amount: Optional[float] = None
    late_fee_grace_days: Optional[int] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Rent tracking
    last_rent_increase: Optional[date] = None
    next_rent_review: Optional[date] = None
    rent_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Additional charges
    additional_charges: List[Dict[str, Any]] = field(default_factory=list)
    
    # Co-signers and guarantors
    guarantors: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class AppFolioPayment:
    """AppFolio Payment model"""
    id: str
    tenant_id: str
    lease_id: str
    property_id: str
    unit_id: str
    amount: float
    payment_date: date
    payment_method: str
    status: PaymentStatus
    reference_number: Optional[str] = None
    description: Optional[str] = None
    charges: List[Dict[str, Any]] = field(default_factory=list)
    fees: List[Dict[str, Any]] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Processing details
    processor_transaction_id: Optional[str] = None
    processing_fee: Optional[float] = None
    
    # Accounting
    account_id: Optional[str] = None
    category: Optional[str] = None
    tax_amount: Optional[float] = None

@dataclass
class AppFolioWorkOrder:
    """AppFolio Work Order model"""
    id: str
    property_id: str
    unit_id: Optional[str] = None
    tenant_id: Optional[str] = None
    vendor_id: Optional[str] = None
    title: str
    description: str
    status: WorkOrderStatus
    priority: WorkOrderPriority
    category: Optional[str] = None
    created_date: date
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    labor_hours: Optional[float] = None
    notes: Optional[str] = None
    photos: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Tracking
    assigned_to: Optional[str] = None
    permission_to_enter: bool = False
    requires_tenant_presence: bool = False
    
    # Parts and materials
    materials: List[Dict[str, Any]] = field(default_factory=list)
    
    # Time tracking
    time_entries: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class AppFolioVendor:
    """AppFolio Vendor model"""
    id: str
    name: str
    business_type: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    license_number: Optional[str] = None
    insurance_info: Optional[Dict[str, Any]] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    hourly_rate: Optional[float] = None
    services: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    
    # Rating and feedback
    rating: Optional[float] = None
    review_count: int = 0
    
    # Financial
    total_paid: Optional[float] = None
    outstanding_balance: Optional[float] = None

@dataclass
class AppFolioAccount:
    """AppFolio Accounting Account model"""
    id: str
    name: str
    account_type: str
    account_number: Optional[str] = None
    description: Optional[str] = None
    parent_account_id: Optional[str] = None
    balance: float = 0.0
    is_active: bool = True
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AppFolioTransaction:
    """AppFolio Financial Transaction model"""
    id: str
    account_id: str
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    tenant_id: Optional[str] = None
    vendor_id: Optional[str] = None
    amount: float
    transaction_date: date
    transaction_type: str
    description: str
    reference_number: Optional[str] = None
    category: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AppFolioDocument:
    """AppFolio Document model"""
    id: str
    name: str
    document_type: str
    file_size: int
    mime_type: str
    upload_date: datetime
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    tenant_id: Optional[str] = None
    lease_id: Optional[str] = None
    work_order_id: Optional[str] = None
    vendor_id: Optional[str] = None
    url: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AppFolioPortfolio:
    """AppFolio Investment Portfolio model"""
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    property_ids: List[str] = field(default_factory=list)
    total_value: Optional[float] = None
    total_units: int = 0
    total_monthly_income: Optional[float] = None
    total_monthly_expenses: Optional[float] = None
    net_operating_income: Optional[float] = None
    overall_cap_rate: Optional[float] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True

@dataclass
class AppFolioApplication:
    """AppFolio Rental Application model"""
    id: str
    property_id: str
    unit_id: str
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    application_date: date
    status: str
    desired_move_in_date: Optional[date] = None
    monthly_income: Optional[float] = None
    employment_info: Optional[Dict[str, Any]] = None
    rental_history: List[Dict[str, Any]] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)
    background_check_results: Optional[Dict[str, Any]] = None
    credit_check_results: Optional[Dict[str, Any]] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AppFolioMessage:
    """AppFolio Communication Message model"""
    id: str
    sender_id: str
    recipient_id: str
    subject: str
    body: str
    message_type: str
    sent_date: datetime
    read_date: Optional[datetime] = None
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    work_order_id: Optional[str] = None
    attachments: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Utility functions for model conversion

def dict_to_property(data: Dict[str, Any]) -> AppFolioProperty:
    """Convert dictionary to AppFolioProperty"""
    return AppFolioProperty(
        id=data.get('id'),
        name=data.get('name'),
        address=data.get('address', {}),
        property_type=PropertyType(data.get('property_type', 'residential')),
        unit_count=data.get('unit_count', 0),
        portfolio_id=data.get('portfolio_id'),
        manager_id=data.get('manager_id'),
        description=data.get('description'),
        year_built=data.get('year_built'),
        square_footage=data.get('square_footage'),
        lot_size=data.get('lot_size'),
        amenities=data.get('amenities', []),
        custom_fields=data.get('custom_fields', {}),
        created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
        updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        active=data.get('active', True),
        acquisition_date=date.fromisoformat(data['acquisition_date']) if data.get('acquisition_date') else None,
        acquisition_cost=data.get('acquisition_cost'),
        current_value=data.get('current_value'),
        monthly_income=data.get('monthly_income'),
        monthly_expenses=data.get('monthly_expenses'),
        net_operating_income=data.get('net_operating_income'),
        cap_rate=data.get('cap_rate'),
        management_company=data.get('management_company'),
        management_fee_percentage=data.get('management_fee_percentage'),
        insurance_carrier=data.get('insurance_carrier'),
        insurance_policy_number=data.get('insurance_policy_number')
    )

def property_to_dict(prop: AppFolioProperty) -> Dict[str, Any]:
    """Convert AppFolioProperty to dictionary"""
    return {
        'id': prop.id,
        'name': prop.name,
        'address': prop.address,
        'property_type': prop.property_type.value,
        'unit_count': prop.unit_count,
        'portfolio_id': prop.portfolio_id,
        'manager_id': prop.manager_id,
        'description': prop.description,
        'year_built': prop.year_built,
        'square_footage': prop.square_footage,
        'lot_size': prop.lot_size,
        'amenities': prop.amenities,
        'custom_fields': prop.custom_fields,
        'created_at': prop.created_at.isoformat() if prop.created_at else None,
        'updated_at': prop.updated_at.isoformat() if prop.updated_at else None,
        'active': prop.active,
        'acquisition_date': prop.acquisition_date.isoformat() if prop.acquisition_date else None,
        'acquisition_cost': prop.acquisition_cost,
        'current_value': prop.current_value,
        'monthly_income': prop.monthly_income,
        'monthly_expenses': prop.monthly_expenses,
        'net_operating_income': prop.net_operating_income,
        'cap_rate': prop.cap_rate,
        'management_company': prop.management_company,
        'management_fee_percentage': prop.management_fee_percentage,
        'insurance_carrier': prop.insurance_carrier,
        'insurance_policy_number': prop.insurance_policy_number
    }
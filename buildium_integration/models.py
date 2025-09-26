"""
Buildium Integration Data Models

Comprehensive data models for Buildium entities with support for:
- Properties and units
- Tenants and leases
- Payments and rent collection
- Maintenance and work orders
- Tenant screening and applications
- Document management
- Owner/investor information
- Small portfolio optimizations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, date
from enum import Enum
from decimal import Decimal
import uuid


class BuildiumProductType(Enum):
    """Buildium product/module types"""
    PROPERTY_MANAGEMENT = "property_management"
    RENT_COLLECTION = "rent_collection"
    MAINTENANCE = "maintenance"
    TENANT_SCREENING = "tenant_screening"
    ACCOUNTING = "accounting"
    OWNER_REPORTING = "owner_reporting"
    VENDOR_MANAGEMENT = "vendor_management"
    DOCUMENT_MANAGEMENT = "document_management"


class PropertyType(Enum):
    """Property types supported by Buildium"""
    APARTMENT = "apartment"
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    DUPLEX = "duplex"
    COMMERCIAL = "commercial"
    MIXED_USE = "mixed_use"
    STUDENT_HOUSING = "student_housing"
    VACATION_RENTAL = "vacation_rental"


class UnitType(Enum):
    """Unit types"""
    STUDIO = "studio"
    ONE_BEDROOM = "1_bedroom"
    TWO_BEDROOM = "2_bedroom"
    THREE_BEDROOM = "3_bedroom"
    FOUR_BEDROOM = "4_bedroom"
    FIVE_PLUS_BEDROOM = "5plus_bedroom"
    COMMERCIAL_SPACE = "commercial_space"
    STORAGE = "storage"
    PARKING = "parking"


class LeaseStatus(Enum):
    """Lease status types"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    NOTICE_GIVEN = "notice_given"
    RENEWAL_PENDING = "renewal_pending"


class PaymentStatus(Enum):
    """Payment status types"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class MaintenanceRequestStatus(Enum):
    """Maintenance request status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class MaintenancePriority(Enum):
    """Maintenance priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EMERGENCY = "emergency"


class ApplicationStatus(Enum):
    """Tenant application status"""
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"
    INCOMPLETE = "incomplete"


class DocumentType(Enum):
    """Document types"""
    LEASE = "lease"
    APPLICATION = "application"
    SCREENING_REPORT = "screening_report"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    MAINTENANCE_PHOTO = "maintenance_photo"
    PROPERTY_PHOTO = "property_photo"
    INSURANCE = "insurance"
    INSPECTION = "inspection"
    OTHER = "other"


@dataclass
class BuildiumProperty:
    """Buildium property data model"""
    id: str
    name: str
    address: Dict[str, str]
    property_type: PropertyType
    unit_count: int
    owner_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    monthly_income: Optional[Decimal] = None
    operating_expenses: Optional[Decimal] = None
    year_built: Optional[int] = None
    square_footage: Optional[int] = None
    lot_size: Optional[str] = None
    amenities: List[str] = field(default_factory=list)
    pet_policy: Optional[Dict[str, Any]] = None
    parking_spaces: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumUnit:
    """Buildium unit data model"""
    id: str
    property_id: str
    unit_number: str
    unit_type: UnitType
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[int] = None
    rent_amount: Optional[Decimal] = None
    security_deposit: Optional[Decimal] = None
    is_available: bool = True
    availability_date: Optional[date] = None
    market_rent: Optional[Decimal] = None
    amenities: List[str] = field(default_factory=list)
    appliances: List[str] = field(default_factory=list)
    floor_plan: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumTenant:
    """Buildium tenant data model"""
    id: str
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    date_of_birth: Optional[date] = None
    ssn_last_four: Optional[str] = None
    emergency_contact: Optional[Dict[str, str]] = None
    employer_info: Optional[Dict[str, str]] = None
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    is_active: bool = True
    tenant_portal_enabled: bool = True
    auto_pay_enabled: bool = False
    communication_preferences: Dict[str, bool] = field(default_factory=dict)
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumLease:
    """Buildium lease data model"""
    id: str
    property_id: str
    unit_id: str
    tenant_id: str
    lease_start_date: date
    lease_end_date: date
    rent_amount: Decimal
    security_deposit: Decimal
    lease_status: LeaseStatus
    lease_type: str = "fixed_term"  # fixed_term, month_to_month, etc.
    payment_frequency: str = "monthly"
    late_fee_amount: Optional[Decimal] = None
    late_fee_grace_days: int = 5
    pet_deposit: Optional[Decimal] = None
    pet_fee: Optional[Decimal] = None
    utilities_included: List[str] = field(default_factory=list)
    additional_occupants: List[Dict[str, str]] = field(default_factory=list)
    renewal_terms: Optional[Dict[str, Any]] = None
    move_in_checklist: Optional[Dict[str, Any]] = None
    move_out_checklist: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumPayment:
    """Buildium payment data model"""
    id: str
    tenant_id: str
    lease_id: str
    amount: Decimal
    payment_date: date
    payment_method: str
    payment_type: str = "rent"  # rent, late_fee, security_deposit, etc.
    status: PaymentStatus
    reference_number: Optional[str] = None
    memo: Optional[str] = None
    fees: List[Dict[str, Decimal]] = field(default_factory=list)
    refund_amount: Optional[Decimal] = None
    refund_date: Optional[date] = None
    bank_account_info: Optional[Dict[str, str]] = None
    is_auto_pay: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumMaintenanceRequest:
    """Buildium maintenance request data model"""
    id: str
    property_id: str
    unit_id: Optional[str] = None
    tenant_id: Optional[str] = None
    title: str
    description: str
    priority: MaintenancePriority
    status: MaintenanceRequestStatus
    category: str
    requested_date: date
    scheduled_date: Optional[date] = None
    completed_date: Optional[date] = None
    vendor_id: Optional[str] = None
    estimated_cost: Optional[Decimal] = None
    actual_cost: Optional[Decimal] = None
    tenant_caused: bool = False
    permission_to_enter: bool = False
    photos: List[str] = field(default_factory=list)  # URLs or file paths
    work_notes: Optional[str] = None
    tenant_satisfaction: Optional[int] = None  # 1-5 rating
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumVendor:
    """Buildium vendor data model"""
    id: str
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    specialty: Optional[str] = None
    license_number: Optional[str] = None
    insurance_info: Optional[Dict[str, Any]] = None
    payment_terms: Optional[str] = None
    tax_id: Optional[str] = None
    w9_on_file: bool = False
    is_active: bool = True
    rating: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumApplication:
    """Buildium tenant application data model"""
    id: str
    property_id: str
    unit_id: str
    applicant_info: Dict[str, Any]
    co_applicants: List[Dict[str, Any]] = field(default_factory=list)
    status: ApplicationStatus
    submitted_date: date
    screening_fee: Optional[Decimal] = None
    screening_results: Optional[Dict[str, Any]] = None
    credit_score: Optional[int] = None
    income_verification: Optional[Dict[str, Any]] = None
    employment_verification: Optional[Dict[str, Any]] = None
    rental_history: Optional[Dict[str, Any]] = None
    references: List[Dict[str, str]] = field(default_factory=list)
    approval_conditions: List[str] = field(default_factory=list)
    denial_reasons: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumOwner:
    """Buildium property owner data model"""
    id: str
    first_name: str
    last_name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None
    tax_id: Optional[str] = None
    ownership_percentage: float = 100.0
    management_fee_percentage: Optional[float] = None
    portal_access: bool = True
    statement_frequency: str = "monthly"
    payment_method: Optional[str] = None
    bank_account_info: Optional[Dict[str, str]] = None
    properties: List[str] = field(default_factory=list)  # property IDs
    is_active: bool = True
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumDocument:
    """Buildium document data model"""
    id: str
    name: str
    document_type: DocumentType
    file_path: str
    file_size: int
    mime_type: str
    entity_type: str  # property, unit, tenant, lease, etc.
    entity_id: str
    uploaded_by: str
    is_private: bool = False
    tags: List[str] = field(default_factory=list)
    description: Optional[str] = None
    expiration_date: Optional[date] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumFinancialTransaction:
    """Buildium financial transaction data model"""
    id: str
    transaction_date: date
    amount: Decimal
    transaction_type: str  # income, expense, transfer
    category: str
    account: str
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    tenant_id: Optional[str] = None
    vendor_id: Optional[str] = None
    description: str
    reference_number: Optional[str] = None
    check_number: Optional[str] = None
    is_reconciled: bool = False
    tax_deductible: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    buildium_id: Optional[str] = None
    estatecore_id: Optional[str] = None
    sync_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BuildiumIntegrationConfig:
    """Integration configuration for Buildium"""
    organization_id: str
    api_key: str
    api_secret: str
    base_url: str = "https://api.buildium.com"
    environment: str = "production"  # production or sandbox
    webhook_enabled: bool = True
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    sync_frequency: int = 15  # minutes
    auto_sync_enabled: bool = True
    retry_attempts: int = 3
    timeout_seconds: int = 30
    rate_limit_requests_per_minute: int = 100
    small_portfolio_mode: bool = False
    self_service_features: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


# Small Portfolio Specific Models

@dataclass
class SmallPortfolioSettings:
    """Settings optimized for small property managers and individual investors"""
    organization_id: str
    simplified_workflows: bool = True
    automated_routine_tasks: bool = True
    basic_compliance_mode: bool = True
    cost_effective_features_only: bool = True
    mobile_optimized: bool = True
    quick_setup_completed: bool = False
    self_service_portal_enabled: bool = True
    basic_reporting_only: bool = True
    property_limit: int = 10  # Limit for small portfolio pricing
    unit_limit: int = 50
    tenant_limit: int = 50
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AutomatedTask:
    """Automated task configuration for small portfolios"""
    id: str
    organization_id: str
    task_name: str
    task_type: str  # rent_reminder, late_fee_application, maintenance_follow_up, etc.
    trigger_conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_enabled: bool = True
    frequency: str = "daily"  # daily, weekly, monthly
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
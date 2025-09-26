"""
RentManager Integration Data Models

Comprehensive data models for RentManager integration including multi-family,
commercial, affordable housing, student housing, HOA management, and compliance features.
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

# ==============================================
# ENUMS FOR RENTMANAGER INTEGRATION
# ==============================================

class PropertyType(Enum):
    """Property types in RentManager"""
    MULTI_FAMILY = "multi_family"
    COMMERCIAL = "commercial"
    AFFORDABLE_HOUSING = "affordable_housing"
    STUDENT_HOUSING = "student_housing"
    SENIOR_HOUSING = "senior_housing"
    MIXED_USE = "mixed_use"
    RETAIL = "retail"
    OFFICE = "office"
    INDUSTRIAL = "industrial"
    WAREHOUSE = "warehouse"
    HOA_COMMUNITY = "hoa_community"
    CONDOMINIUM = "condominium"
    TOWNHOME = "townhome"
    SINGLE_FAMILY = "single_family"

class UnitType(Enum):
    """Unit types in RentManager"""
    APARTMENT = "apartment"
    STUDIO = "studio"
    ONE_BEDROOM = "one_bedroom"
    TWO_BEDROOM = "two_bedroom"
    THREE_BEDROOM = "three_bedroom"
    FOUR_BEDROOM = "four_bedroom"
    PENTHOUSE = "penthouse"
    TOWNHOUSE = "townhouse"
    LOFT = "loft"
    DUPLEX = "duplex"
    COMMERCIAL_SPACE = "commercial_space"
    RETAIL_SPACE = "retail_space"
    OFFICE_SPACE = "office_space"
    WAREHOUSE_SPACE = "warehouse_space"
    PARKING_SPACE = "parking_space"
    STORAGE_UNIT = "storage_unit"
    STUDENT_ROOM = "student_room"
    SHARED_ROOM = "shared_room"

class LeaseStatus(Enum):
    """Lease status in RentManager"""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"
    CANCELLED = "cancelled"
    FUTURE = "future"
    HOLDOVER = "holdover"
    NOTICE_GIVEN = "notice_given"
    EVICTION_PENDING = "eviction_pending"

class ComplianceType(Enum):
    """Affordable housing compliance types"""
    LIHTC = "lihtc"  # Low-Income Housing Tax Credit
    SECTION_8 = "section_8"
    HUD = "hud"
    HOME = "home"  # HOME Investment Partnerships Program
    CDBG = "cdbg"  # Community Development Block Grant
    USDA_RURAL = "usda_rural"
    TAX_EXEMPT = "tax_exempt"
    STATE_PROGRAM = "state_program"
    LOCAL_PROGRAM = "local_program"

class PaymentStatus(Enum):
    """Payment status in RentManager"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
    PARTIAL = "partial"
    NSUF = "nsuf"  # Non-Sufficient Funds
    CHARGEBACK = "chargeback"

class WorkOrderStatus(Enum):
    """Work order status in RentManager"""
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"
    PENDING_APPROVAL = "pending_approval"
    PENDING_PARTS = "pending_parts"

class WorkOrderPriority(Enum):
    """Work order priority in RentManager"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class VendorType(Enum):
    """Vendor types in RentManager"""
    MAINTENANCE = "maintenance"
    CONTRACTOR = "contractor"
    SUPPLIER = "supplier"
    PROFESSIONAL_SERVICE = "professional_service"
    LANDSCAPING = "landscaping"
    CLEANING = "cleaning"
    SECURITY = "security"
    LEGAL = "legal"
    ACCOUNTING = "accounting"
    INSURANCE = "insurance"
    UTILITY = "utility"

class ResidentStatus(Enum):
    """Resident/tenant status"""
    CURRENT = "current"
    PROSPECTIVE = "prospective"
    FORMER = "former"
    APPLICANT = "applicant"
    APPROVED = "approved"
    DENIED = "denied"
    WAITLIST = "waitlist"

# ==============================================
# CORE PROPERTY MANAGEMENT MODELS
# ==============================================

@dataclass
class RentManagerProperty:
    """RentManager Property model with comprehensive features"""
    id: str
    name: str
    address: Dict[str, str]
    property_type: PropertyType
    unit_count: int
    
    # Basic property info
    portfolio_id: Optional[str] = None
    manager_id: Optional[str] = None
    description: Optional[str] = None
    year_built: Optional[int] = None
    total_square_footage: Optional[float] = None
    lot_size: Optional[float] = None
    building_count: Optional[int] = None
    floor_count: Optional[int] = None
    
    # Amenities and features
    amenities: List[str] = field(default_factory=list)
    building_features: List[str] = field(default_factory=list)
    community_features: List[str] = field(default_factory=list)
    
    # Financial information
    acquisition_date: Optional[date] = None
    acquisition_cost: Optional[float] = None
    current_market_value: Optional[float] = None
    monthly_income: Optional[float] = None
    monthly_expenses: Optional[float] = None
    net_operating_income: Optional[float] = None
    cap_rate: Optional[float] = None
    
    # Management information
    management_company: Optional[str] = None
    management_fee_percentage: Optional[float] = None
    regional_manager_id: Optional[str] = None
    property_manager_id: Optional[str] = None
    assistant_manager_id: Optional[str] = None
    
    # Insurance and compliance
    insurance_carrier: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    insurance_expiry: Optional[date] = None
    compliance_programs: List[ComplianceType] = field(default_factory=list)
    compliance_expiry_dates: Dict[str, date] = field(default_factory=dict)
    
    # Student housing specific
    university_partnerships: List[str] = field(default_factory=list)
    academic_year_start: Optional[date] = None
    academic_year_end: Optional[date] = None
    
    # Commercial specific
    anchor_tenants: List[str] = field(default_factory=list)
    retail_classification: Optional[str] = None
    office_class: Optional[str] = None
    
    # HOA specific
    hoa_management: bool = False
    association_name: Optional[str] = None
    board_members: List[Dict[str, Any]] = field(default_factory=list)
    
    # Maintenance and operations
    maintenance_supervisor_id: Optional[str] = None
    emergency_contact: Optional[Dict[str, str]] = None
    operating_hours: Optional[Dict[str, str]] = None
    
    # Audit and tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    
    # Regulatory compliance
    regulatory_licenses: List[Dict[str, Any]] = field(default_factory=list)
    inspection_schedule: Dict[str, Any] = field(default_factory=dict)
    
    # Environmental and energy
    energy_certifications: List[str] = field(default_factory=list)
    environmental_compliance: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RentManagerUnit:
    """RentManager Unit model with multi-family and commercial features"""
    id: str
    property_id: str
    unit_number: str
    unit_type: UnitType
    
    # Physical characteristics
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_footage: Optional[float] = None
    floor_number: Optional[int] = None
    building_section: Optional[str] = None
    balcony: bool = False
    view_type: Optional[str] = None
    
    # Rental information
    market_rent: Optional[float] = None
    current_rent: Optional[float] = None
    security_deposit: Optional[float] = None
    pet_deposit: Optional[float] = None
    available_date: Optional[date] = None
    lease_id: Optional[str] = None
    
    # Occupancy
    max_occupancy: Optional[int] = None
    current_occupancy: int = 0
    residents: List[str] = field(default_factory=list)  # Resident IDs
    
    # Amenities and features
    unit_amenities: List[str] = field(default_factory=list)
    appliances: List[str] = field(default_factory=list)
    accessibility_features: List[str] = field(default_factory=list)
    
    # Commercial specific
    cam_charges: Optional[float] = None  # Common Area Maintenance
    percentage_rent_threshold: Optional[float] = None
    tenant_improvements: List[Dict[str, Any]] = field(default_factory=list)
    lease_type: Optional[str] = None  # gross, net, modified_gross
    
    # Student housing specific
    academic_year_lease: bool = False
    roommate_matching_enabled: bool = False
    room_assignment_gender: Optional[str] = None
    
    # Affordable housing compliance
    income_restrictions: Optional[Dict[str, Any]] = None
    ami_percentage: Optional[int] = None  # Area Median Income percentage
    compliance_monitoring: Dict[str, Any] = field(default_factory=dict)
    
    # Maintenance and condition
    last_inspection: Optional[date] = None
    next_inspection: Optional[date] = None
    condition_rating: Optional[int] = None  # 1-10 scale
    maintenance_notes: Optional[str] = None
    last_renovation: Optional[date] = None
    
    # Rent control and regulation
    rent_control_status: bool = False
    maximum_allowable_rent: Optional[float] = None
    last_rent_increase: Optional[date] = None
    next_allowable_increase: Optional[date] = None
    
    # Utilities
    utility_inclusions: List[str] = field(default_factory=list)
    utility_allowances: Dict[str, float] = field(default_factory=dict)
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True

@dataclass
class RentManagerResident:
    """RentManager Resident/Tenant model with comprehensive features"""
    id: str
    first_name: str
    last_name: str
    
    # Contact information
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    work_phone: Optional[str] = None
    emergency_contact: Optional[Dict[str, str]] = None
    
    # Personal information
    date_of_birth: Optional[date] = None
    ssn_last_four: Optional[str] = None
    government_id_type: Optional[str] = None
    government_id_number: Optional[str] = None
    
    # Residence information
    current_unit_id: Optional[str] = None
    current_property_id: Optional[str] = None
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    resident_status: ResidentStatus = ResidentStatus.PROSPECTIVE
    
    # Financial information
    monthly_income: Optional[float] = None
    annual_income: Optional[float] = None
    debt_to_income_ratio: Optional[float] = None
    credit_score: Optional[int] = None
    employment_info: Optional[Dict[str, Any]] = None
    
    # Background and screening
    background_check_status: Optional[str] = None
    background_check_date: Optional[date] = None
    credit_check_status: Optional[str] = None
    credit_check_date: Optional[date] = None
    eviction_history: List[Dict[str, Any]] = field(default_factory=list)
    criminal_background: Optional[Dict[str, Any]] = None
    
    # Student housing specific
    student_id: Optional[str] = None
    university: Optional[str] = None
    graduation_date: Optional[date] = None
    academic_standing: Optional[str] = None
    parent_guarantor: Optional[Dict[str, Any]] = None
    
    # Affordable housing compliance
    income_certification: Optional[Dict[str, Any]] = None
    household_size: Optional[int] = None
    household_members: List[Dict[str, Any]] = field(default_factory=list)
    asset_information: Optional[Dict[str, Any]] = None
    eligibility_status: Optional[str] = None
    recertification_date: Optional[date] = None
    
    # Communication preferences
    preferred_contact_method: Optional[str] = None
    communication_preferences: Dict[str, bool] = field(default_factory=dict)
    language_preference: Optional[str] = None
    
    # Additional residents and occupants
    additional_occupants: List[Dict[str, Any]] = field(default_factory=list)
    authorized_contacts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Pet information
    pets: List[Dict[str, Any]] = field(default_factory=list)
    
    # Vehicle information
    vehicles: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tracking and audit
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True
    
    # Legal and compliance
    lease_violations: List[Dict[str, Any]] = field(default_factory=list)
    court_proceedings: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class RentManagerLease:
    """RentManager Lease model with comprehensive lease management"""
    id: str
    property_id: str
    unit_id: str
    primary_resident_id: str
    
    # Lease terms
    start_date: date
    end_date: date
    status: LeaseStatus
    lease_type: str  # fixed_term, month_to_month, commercial, student
    
    # Financial terms
    base_rent: float
    security_deposit: Optional[float] = None
    pet_deposit: Optional[float] = None
    key_deposit: Optional[float] = None
    other_deposits: Dict[str, float] = field(default_factory=dict)
    
    # Rent and payment terms
    rent_due_day: int = 1
    proration_method: Optional[str] = None
    late_fee_amount: Optional[float] = None
    late_fee_percentage: Optional[float] = None
    late_fee_grace_days: Optional[int] = None
    nsf_fee: Optional[float] = None
    
    # Lease administration
    lease_document_url: Optional[str] = None
    lease_terms_text: Optional[str] = None
    special_provisions: List[str] = field(default_factory=list)
    addendums: List[Dict[str, Any]] = field(default_factory=list)
    
    # Renewal and termination
    auto_renew: bool = False
    renewal_notice_days: Optional[int] = None
    termination_notice_days: Optional[int] = None
    early_termination_fee: Optional[float] = None
    
    # Commercial lease specific
    cam_charges: Optional[float] = None
    percentage_rent_rate: Optional[float] = None
    percentage_rent_threshold: Optional[float] = None
    expense_escalations: List[Dict[str, Any]] = field(default_factory=list)
    operating_expense_caps: Dict[str, float] = field(default_factory=dict)
    
    # Student housing specific
    academic_year_lease: bool = False
    roommate_assignments: List[str] = field(default_factory=list)
    parent_guarantor_required: bool = False
    
    # Affordable housing compliance
    income_limit_compliance: Optional[Dict[str, Any]] = None
    rent_limit_compliance: Optional[Dict[str, Any]] = None
    compliance_monitoring_schedule: Optional[Dict[str, Any]] = None
    
    # Utilities and services
    utility_inclusions: List[str] = field(default_factory=list)
    utility_allowances: Dict[str, float] = field(default_factory=dict)
    service_inclusions: List[str] = field(default_factory=list)
    
    # Additional charges and concessions
    recurring_charges: List[Dict[str, Any]] = field(default_factory=list)
    one_time_charges: List[Dict[str, Any]] = field(default_factory=list)
    concessions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Co-signers and guarantors
    guarantors: List[Dict[str, Any]] = field(default_factory=list)
    co_signers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Rent history and adjustments
    rent_history: List[Dict[str, Any]] = field(default_factory=list)
    rent_adjustments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Insurance requirements
    renters_insurance_required: bool = False
    renters_insurance_minimum: Optional[float] = None
    liability_coverage_required: Optional[float] = None
    
    # Move-in/Move-out
    move_in_inspection: Optional[Dict[str, Any]] = None
    move_out_inspection: Optional[Dict[str, Any]] = None
    move_in_costs: Dict[str, float] = field(default_factory=dict)
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Legal and compliance
    lease_violations: List[Dict[str, Any]] = field(default_factory=list)
    court_orders: List[Dict[str, Any]] = field(default_factory=list)

# ==============================================
# FINANCIAL MANAGEMENT MODELS
# ==============================================

@dataclass
class RentManagerPayment:
    """RentManager Payment model with comprehensive tracking"""
    id: str
    resident_id: str
    lease_id: str
    property_id: str
    unit_id: str
    
    # Payment details
    amount: float
    payment_date: date
    payment_method: str
    status: PaymentStatus
    
    # Transaction details
    reference_number: Optional[str] = None
    confirmation_number: Optional[str] = None
    bank_reference: Optional[str] = None
    processor_transaction_id: Optional[str] = None
    
    # Payment breakdown
    rent_amount: Optional[float] = None
    late_fees: Optional[float] = None
    other_charges: Dict[str, float] = field(default_factory=dict)
    credits_applied: Dict[str, float] = field(default_factory=dict)
    
    # Processing information
    processing_fee: Optional[float] = None
    processor_name: Optional[str] = None
    processing_date: Optional[datetime] = None
    
    # Accounting
    account_id: Optional[str] = None
    gl_account: Optional[str] = None
    category: Optional[str] = None
    tax_amount: Optional[float] = None
    
    # Commercial specific
    cam_payment: Optional[float] = None
    percentage_rent: Optional[float] = None
    
    # Batch and deposit tracking
    batch_id: Optional[str] = None
    deposit_id: Optional[str] = None
    bank_deposit_date: Optional[date] = None
    
    # Tracking
    description: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class RentManagerAccount:
    """RentManager Chart of Accounts model"""
    id: str
    account_code: str
    account_name: str
    account_type: str
    
    # Account details
    description: Optional[str] = None
    parent_account_id: Optional[str] = None
    account_category: Optional[str] = None
    
    # Financial information
    current_balance: float = 0.0
    ytd_balance: float = 0.0
    budget_amount: Optional[float] = None
    
    # Property allocation
    property_allocations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Account configuration
    is_active: bool = True
    requires_approval: bool = False
    is_cash_account: bool = False
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class RentManagerTransaction:
    """RentManager Financial Transaction model"""
    id: str
    account_id: str
    
    # Transaction details
    transaction_date: date
    amount: float
    transaction_type: str  # debit, credit
    description: str
    
    # References
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    resident_id: Optional[str] = None
    vendor_id: Optional[str] = None
    lease_id: Optional[str] = None
    work_order_id: Optional[str] = None
    
    # Transaction identification
    reference_number: Optional[str] = None
    document_number: Optional[str] = None
    batch_id: Optional[str] = None
    
    # Categorization
    category: Optional[str] = None
    subcategory: Optional[str] = None
    gl_code: Optional[str] = None
    
    # Approval and workflow
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None
    approval_date: Optional[datetime] = None
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ==============================================
# MAINTENANCE AND OPERATIONS MODELS
# ==============================================

@dataclass
class RentManagerWorkOrder:
    """RentManager Work Order model with comprehensive tracking"""
    id: str
    property_id: str
    
    # Work order details
    title: str
    description: str
    status: WorkOrderStatus
    priority: WorkOrderPriority
    category: Optional[str] = None
    subcategory: Optional[str] = None
    
    # Location
    unit_id: Optional[str] = None
    building_area: Optional[str] = None
    specific_location: Optional[str] = None
    
    # Personnel
    requested_by: Optional[str] = None
    resident_id: Optional[str] = None
    assigned_to: Optional[str] = None
    supervisor_id: Optional[str] = None
    vendor_id: Optional[str] = None
    
    # Scheduling
    created_date: date
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    estimated_duration: Optional[int] = None  # minutes
    completed_date: Optional[datetime] = None
    
    # Access and permissions
    permission_to_enter: bool = False
    requires_resident_presence: bool = False
    emergency_entry: bool = False
    key_required: bool = False
    
    # Cost tracking
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    labor_cost: Optional[float] = None
    material_cost: Optional[float] = None
    vendor_cost: Optional[float] = None
    
    # Time tracking
    labor_hours: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Materials and parts
    materials_needed: List[Dict[str, Any]] = field(default_factory=list)
    materials_used: List[Dict[str, Any]] = field(default_factory=list)
    
    # Documentation
    photos_before: List[str] = field(default_factory=list)
    photos_after: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    
    # Completion details
    work_performed: Optional[str] = None
    resolution_notes: Optional[str] = None
    resident_satisfaction: Optional[int] = None  # 1-5 rating
    
    # Follow-up
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None
    warranty_period: Optional[int] = None  # days
    
    # Recurring maintenance
    is_recurring: bool = False
    recurrence_schedule: Optional[str] = None
    parent_work_order_id: Optional[str] = None
    
    # Compliance and safety
    safety_concerns: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    permits_required: List[str] = field(default_factory=list)
    
    # Tracking
    notes: Optional[str] = None
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class RentManagerVendor:
    """RentManager Vendor model with comprehensive management"""
    id: str
    vendor_name: str
    vendor_type: VendorType
    
    # Contact information
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile_phone: Optional[str] = None
    fax: Optional[str] = None
    website: Optional[str] = None
    
    # Address
    billing_address: Optional[Dict[str, str]] = None
    service_address: Optional[Dict[str, str]] = None
    
    # Business information
    business_license: Optional[str] = None
    tax_id: Optional[str] = None
    duns_number: Optional[str] = None
    
    # Insurance and compliance
    general_liability_insurance: Optional[Dict[str, Any]] = None
    workers_comp_insurance: Optional[Dict[str, Any]] = None
    bonding_information: Optional[Dict[str, Any]] = None
    certifications: List[str] = field(default_factory=list)
    
    # Financial terms
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = None
    discount_terms: Optional[str] = None
    
    # Service information
    services_provided: List[str] = field(default_factory=list)
    service_areas: List[str] = field(default_factory=list)
    hourly_rates: Dict[str, float] = field(default_factory=dict)
    
    # Emergency services
    emergency_services: bool = False
    emergency_contact: Optional[str] = None
    emergency_phone: Optional[str] = None
    
    # Performance tracking
    rating: Optional[float] = None
    review_count: int = 0
    total_work_orders: int = 0
    average_completion_time: Optional[float] = None
    
    # Financial tracking
    total_paid_ytd: Optional[float] = None
    total_paid_lifetime: Optional[float] = None
    outstanding_balance: Optional[float] = None
    
    # Preferred vendor settings
    is_preferred: bool = False
    preferred_categories: List[str] = field(default_factory=list)
    
    # Contract information
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    contract_terms: Optional[str] = None
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    active: bool = True

# ==============================================
# SPECIALIZED HOUSING MODELS
# ==============================================

@dataclass
class StudentHousingApplication:
    """Student housing specific application model"""
    id: str
    property_id: str
    unit_id: str
    
    # Student information
    student_id: str
    university: str
    expected_graduation: date
    academic_standing: str
    major: Optional[str] = None
    
    # Housing preferences
    preferred_roommates: List[str] = field(default_factory=list)
    lifestyle_preferences: Dict[str, Any] = field(default_factory=dict)
    study_habits: Optional[str] = None
    
    # Academic calendar
    move_in_preference: Optional[date] = None
    lease_term_preference: Optional[str] = None
    
    # Parent/guardian information
    parent_guarantor: Dict[str, Any] = field(default_factory=dict)
    
    # Application status
    application_status: str
    application_date: date
    decision_date: Optional[date] = None
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class AffordableHousingCompliance:
    """Affordable housing compliance tracking model"""
    id: str
    property_id: str
    unit_id: str
    resident_id: str
    
    # Compliance program
    program_type: ComplianceType
    program_name: str
    program_requirements: Dict[str, Any]
    
    # Income certification
    household_size: int
    household_income: float
    ami_percentage: int  # Area Median Income percentage
    income_limit: float
    income_sources: List[Dict[str, Any]] = field(default_factory=list)
    
    # Asset verification
    total_assets: Optional[float] = None
    asset_details: List[Dict[str, Any]] = field(default_factory=list)
    
    # Certification tracking
    initial_certification_date: date
    current_certification_date: date
    next_recertification_date: date
    certification_status: str
    
    # Rent restrictions
    maximum_allowable_rent: float
    current_rent: float
    utility_allowance: Optional[float] = None
    
    # Compliance monitoring
    monitoring_schedule: Dict[str, Any]
    last_monitoring_date: Optional[date] = None
    next_monitoring_date: Optional[date] = None
    
    # Violations and corrections
    compliance_violations: List[Dict[str, Any]] = field(default_factory=list)
    corrective_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Documentation
    required_documents: List[str] = field(default_factory=list)
    submitted_documents: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class HOAManagement:
    """HOA Community management model"""
    id: str
    property_id: str
    
    # Association information
    association_name: str
    association_type: str  # homeowners, condominium, townhome
    
    # Board information
    board_members: List[Dict[str, Any]] = field(default_factory=list)
    board_meeting_schedule: Optional[str] = None
    next_board_meeting: Optional[datetime] = None
    
    # Financial management
    annual_budget: Optional[float] = None
    reserve_fund_balance: Optional[float] = None
    operating_fund_balance: Optional[float] = None
    special_assessments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Assessment tracking
    monthly_assessment: Optional[float] = None
    assessment_due_date: int = 1  # day of month
    special_assessment_balance: Optional[float] = None
    
    # Community rules and regulations
    governing_documents: List[str] = field(default_factory=list)
    architectural_guidelines: Optional[str] = None
    community_rules: List[str] = field(default_factory=list)
    
    # Compliance and violations
    violation_tracking: List[Dict[str, Any]] = field(default_factory=list)
    fine_schedule: Dict[str, float] = field(default_factory=dict)
    
    # Amenities and common areas
    common_areas: List[str] = field(default_factory=list)
    amenity_reservations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Vendor and contractor management
    approved_vendors: List[str] = field(default_factory=list)
    maintenance_contracts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ==============================================
# DOCUMENT AND COMMUNICATION MODELS
# ==============================================

@dataclass
class RentManagerDocument:
    """RentManager Document management model"""
    id: str
    name: str
    document_type: str
    
    # File information
    file_size: int
    mime_type: str
    file_path: Optional[str] = None
    url: Optional[str] = None
    
    # Associated entities
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    resident_id: Optional[str] = None
    lease_id: Optional[str] = None
    work_order_id: Optional[str] = None
    vendor_id: Optional[str] = None
    
    # Document metadata
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # Security and access
    is_confidential: bool = False
    access_permissions: List[str] = field(default_factory=list)
    requires_signature: bool = False
    
    # Version control
    version: str = "1.0"
    parent_document_id: Optional[str] = None
    is_current_version: bool = True
    
    # Expiration and retention
    expiration_date: Optional[date] = None
    retention_period: Optional[int] = None  # years
    
    # Upload information
    uploaded_by: Optional[str] = None
    upload_date: datetime
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class RentManagerMessage:
    """RentManager Communication message model"""
    id: str
    sender_id: str
    recipient_id: str
    
    # Message content
    subject: str
    body: str
    message_type: str  # email, sms, portal, system
    
    # Message details
    sent_date: datetime
    read_date: Optional[datetime] = None
    priority: str = "normal"
    
    # Associated entities
    property_id: Optional[str] = None
    unit_id: Optional[str] = None
    work_order_id: Optional[str] = None
    lease_id: Optional[str] = None
    
    # Attachments
    attachments: List[str] = field(default_factory=list)
    
    # Delivery tracking
    delivery_status: str = "pending"
    delivery_attempts: int = 0
    bounce_reason: Optional[str] = None
    
    # Response tracking
    requires_response: bool = False
    response_due_date: Optional[datetime] = None
    parent_message_id: Optional[str] = None
    
    # Automation
    is_automated: bool = False
    automation_trigger: Optional[str] = None
    
    # Tracking
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ==============================================
# UTILITY CONVERSION FUNCTIONS
# ==============================================

def dict_to_property(data: Dict[str, Any]) -> RentManagerProperty:
    """Convert dictionary to RentManagerProperty"""
    return RentManagerProperty(
        id=data.get('id'),
        name=data.get('name'),
        address=data.get('address', {}),
        property_type=PropertyType(data.get('property_type', 'multi_family')),
        unit_count=data.get('unit_count', 0),
        portfolio_id=data.get('portfolio_id'),
        manager_id=data.get('manager_id'),
        description=data.get('description'),
        year_built=data.get('year_built'),
        total_square_footage=data.get('total_square_footage'),
        lot_size=data.get('lot_size'),
        building_count=data.get('building_count'),
        floor_count=data.get('floor_count'),
        amenities=data.get('amenities', []),
        building_features=data.get('building_features', []),
        community_features=data.get('community_features', []),
        acquisition_date=date.fromisoformat(data['acquisition_date']) if data.get('acquisition_date') else None,
        acquisition_cost=data.get('acquisition_cost'),
        current_market_value=data.get('current_market_value'),
        monthly_income=data.get('monthly_income'),
        monthly_expenses=data.get('monthly_expenses'),
        net_operating_income=data.get('net_operating_income'),
        cap_rate=data.get('cap_rate'),
        management_company=data.get('management_company'),
        management_fee_percentage=data.get('management_fee_percentage'),
        regional_manager_id=data.get('regional_manager_id'),
        property_manager_id=data.get('property_manager_id'),
        assistant_manager_id=data.get('assistant_manager_id'),
        insurance_carrier=data.get('insurance_carrier'),
        insurance_policy_number=data.get('insurance_policy_number'),
        insurance_expiry=date.fromisoformat(data['insurance_expiry']) if data.get('insurance_expiry') else None,
        compliance_programs=[ComplianceType(cp) for cp in data.get('compliance_programs', [])],
        compliance_expiry_dates={k: date.fromisoformat(v) for k, v in data.get('compliance_expiry_dates', {}).items()},
        university_partnerships=data.get('university_partnerships', []),
        academic_year_start=date.fromisoformat(data['academic_year_start']) if data.get('academic_year_start') else None,
        academic_year_end=date.fromisoformat(data['academic_year_end']) if data.get('academic_year_end') else None,
        anchor_tenants=data.get('anchor_tenants', []),
        retail_classification=data.get('retail_classification'),
        office_class=data.get('office_class'),
        hoa_management=data.get('hoa_management', False),
        association_name=data.get('association_name'),
        board_members=data.get('board_members', []),
        maintenance_supervisor_id=data.get('maintenance_supervisor_id'),
        emergency_contact=data.get('emergency_contact'),
        operating_hours=data.get('operating_hours'),
        custom_fields=data.get('custom_fields', {}),
        created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
        updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        active=data.get('active', True),
        regulatory_licenses=data.get('regulatory_licenses', []),
        inspection_schedule=data.get('inspection_schedule', {}),
        energy_certifications=data.get('energy_certifications', []),
        environmental_compliance=data.get('environmental_compliance', {})
    )

def property_to_dict(prop: RentManagerProperty) -> Dict[str, Any]:
    """Convert RentManagerProperty to dictionary"""
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
        'total_square_footage': prop.total_square_footage,
        'lot_size': prop.lot_size,
        'building_count': prop.building_count,
        'floor_count': prop.floor_count,
        'amenities': prop.amenities,
        'building_features': prop.building_features,
        'community_features': prop.community_features,
        'acquisition_date': prop.acquisition_date.isoformat() if prop.acquisition_date else None,
        'acquisition_cost': prop.acquisition_cost,
        'current_market_value': prop.current_market_value,
        'monthly_income': prop.monthly_income,
        'monthly_expenses': prop.monthly_expenses,
        'net_operating_income': prop.net_operating_income,
        'cap_rate': prop.cap_rate,
        'management_company': prop.management_company,
        'management_fee_percentage': prop.management_fee_percentage,
        'regional_manager_id': prop.regional_manager_id,
        'property_manager_id': prop.property_manager_id,
        'assistant_manager_id': prop.assistant_manager_id,
        'insurance_carrier': prop.insurance_carrier,
        'insurance_policy_number': prop.insurance_policy_number,
        'insurance_expiry': prop.insurance_expiry.isoformat() if prop.insurance_expiry else None,
        'compliance_programs': [cp.value for cp in prop.compliance_programs],
        'compliance_expiry_dates': {k: v.isoformat() for k, v in prop.compliance_expiry_dates.items()},
        'university_partnerships': prop.university_partnerships,
        'academic_year_start': prop.academic_year_start.isoformat() if prop.academic_year_start else None,
        'academic_year_end': prop.academic_year_end.isoformat() if prop.academic_year_end else None,
        'anchor_tenants': prop.anchor_tenants,
        'retail_classification': prop.retail_classification,
        'office_class': prop.office_class,
        'hoa_management': prop.hoa_management,
        'association_name': prop.association_name,
        'board_members': prop.board_members,
        'maintenance_supervisor_id': prop.maintenance_supervisor_id,
        'emergency_contact': prop.emergency_contact,
        'operating_hours': prop.operating_hours,
        'custom_fields': prop.custom_fields,
        'created_at': prop.created_at.isoformat() if prop.created_at else None,
        'updated_at': prop.updated_at.isoformat() if prop.updated_at else None,
        'active': prop.active,
        'regulatory_licenses': prop.regulatory_licenses,
        'inspection_schedule': prop.inspection_schedule,
        'energy_certifications': prop.energy_certifications,
        'environmental_compliance': prop.environmental_compliance
    }
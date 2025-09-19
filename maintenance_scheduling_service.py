"""
Maintenance Scheduling Service for EstateCore
Automated maintenance scheduling, work order management, and vendor coordination
"""

import os
import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaintenanceType(Enum):
    """Maintenance types"""
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    EMERGENCY = "emergency"
    INSPECTION = "inspection"
    CLEANING = "cleaning"
    REPAIR = "repair"
    REPLACEMENT = "replacement"

class MaintenanceStatus(Enum):
    """Maintenance request status"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class Priority(Enum):
    """Priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class VendorStatus(Enum):
    """Vendor availability status"""
    AVAILABLE = "available"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"

@dataclass
class MaintenanceItem:
    """Maintenance item/equipment"""
    id: str
    property_id: int
    name: str
    category: str
    model: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[datetime] = None
    warranty_expires: Optional[datetime] = None
    last_service_date: Optional[datetime] = None
    next_service_due: Optional[datetime] = None
    service_interval_days: int = 90
    is_active: bool = True
    metadata: Dict = field(default_factory=dict)

@dataclass
class MaintenanceSchedule:
    """Maintenance schedule template"""
    id: str
    item_id: str
    maintenance_type: MaintenanceType
    description: str
    frequency_days: int
    estimated_duration_hours: float
    required_skills: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    instructions: str = ""

@dataclass
class MaintenanceRequest:
    """Maintenance work order/request"""
    id: str
    property_id: int
    item_id: Optional[str]
    requested_by: int  # user_id
    title: str
    description: str
    maintenance_type: MaintenanceType
    priority: Priority
    status: MaintenanceStatus
    created_at: datetime
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    assigned_vendor_id: Optional[str] = None
    estimated_cost: float = 0.0
    actual_cost: float = 0.0
    estimated_hours: float = 0.0
    actual_hours: float = 0.0
    tenant_access_required: bool = False
    tenant_notification_sent: bool = False
    photos: List[str] = field(default_factory=list)
    notes: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

@dataclass
class Vendor:
    """Maintenance vendor/contractor"""
    id: str
    name: str
    contact_person: str
    email: str
    phone: str
    address: str
    specialties: List[str]
    rating: float = 0.0
    hourly_rate: float = 0.0
    availability_schedule: Dict = field(default_factory=dict)
    status: VendorStatus = VendorStatus.AVAILABLE
    insurance_expires: Optional[datetime] = None
    license_number: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

@dataclass
class WorkOrderAssignment:
    """Work order assignment to vendor"""
    id: str
    request_id: str
    vendor_id: str
    assigned_at: datetime
    scheduled_start: datetime
    scheduled_end: datetime
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    status: str = "assigned"
    notes: str = ""

class MaintenanceSchedulingService:
    def __init__(self):
        """Initialize maintenance scheduling service"""
        self.email_server = os.getenv('EMAIL_SERVER', 'smtp.gmail.com')
        self.email_port = int(os.getenv('EMAIL_PORT', '587'))
        self.email_username = os.getenv('EMAIL_USERNAME', '')
        self.email_password = os.getenv('EMAIL_PASSWORD', '')
        
        # In-memory storage for demonstration (would use database in production)
        self.maintenance_items = {}
        self.maintenance_schedules = {}
        self.maintenance_requests = {}
        self.vendors = {}
        self.work_assignments = {}
        
        # Initialize with sample data
        self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Initialize with sample maintenance data"""
        # Sample maintenance items
        hvac_item = MaintenanceItem(
            id="item_001",
            property_id=1,
            name="HVAC Unit - Building A",
            category="HVAC",
            model="Carrier 24ABC6",
            serial_number="CV123456789",
            installation_date=datetime(2020, 3, 15),
            warranty_expires=datetime(2025, 3, 15),
            service_interval_days=90
        )
        self.maintenance_items[hvac_item.id] = hvac_item
        
        # Sample vendors
        vendor = Vendor(
            id="vendor_001",
            name="ABC Maintenance Services",
            contact_person="John Smith",
            email="john@abcmaintenance.com",
            phone="555-1234",
            address="123 Service St",
            specialties=["HVAC", "Plumbing", "Electrical"],
            hourly_rate=75.0,
            rating=4.5
        )
        self.vendors[vendor.id] = vendor
        
        # Sample maintenance schedules
        hvac_schedule = MaintenanceSchedule(
            id="schedule_001",
            item_id="item_001",
            maintenance_type=MaintenanceType.PREVENTIVE,
            description="Quarterly HVAC filter replacement and inspection",
            frequency_days=90,
            estimated_duration_hours=2.0,
            required_skills=["HVAC", "Basic Electrical"],
            estimated_cost=150.0,
            instructions="Replace filters, check refrigerant levels, inspect ductwork"
        )
        self.maintenance_schedules[hvac_schedule.id] = hvac_schedule
        
        logger.info("Sample maintenance data initialized")
    
    def create_maintenance_item(self, property_id: int, name: str, category: str, 
                              **kwargs) -> Dict:
        """Create a new maintenance item"""
        try:
            item_id = str(uuid.uuid4())
            
            maintenance_item = MaintenanceItem(
                id=item_id,
                property_id=property_id,
                name=name,
                category=category,
                **kwargs
            )
            
            self.maintenance_items[item_id] = maintenance_item
            
            logger.info(f"Maintenance item created: {name}")
            return {
                'success': True,
                'item_id': item_id,
                'item': self._serialize_maintenance_item(maintenance_item)
            }
            
        except Exception as e:
            logger.error(f"Failed to create maintenance item: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_maintenance_schedule(self, item_id: str, maintenance_type: MaintenanceType,
                                  description: str, frequency_days: int, **kwargs) -> Dict:
        """Create a maintenance schedule for an item"""
        try:
            if item_id not in self.maintenance_items:
                return {'success': False, 'error': 'Maintenance item not found'}
            
            schedule_id = str(uuid.uuid4())
            
            schedule = MaintenanceSchedule(
                id=schedule_id,
                item_id=item_id,
                maintenance_type=maintenance_type,
                description=description,
                frequency_days=frequency_days,
                **kwargs
            )
            
            self.maintenance_schedules[schedule_id] = schedule
            
            # Update item's next service due date
            item = self.maintenance_items[item_id]
            if not item.next_service_due:
                item.next_service_due = datetime.utcnow() + timedelta(days=frequency_days)
            
            logger.info(f"Maintenance schedule created: {description}")
            return {
                'success': True,
                'schedule_id': schedule_id,
                'schedule': self._serialize_maintenance_schedule(schedule)
            }
            
        except Exception as e:
            logger.error(f"Failed to create maintenance schedule: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_maintenance_request(self, property_id: int, title: str, description: str,
                                 maintenance_type: MaintenanceType, priority: Priority,
                                 requested_by: int, **kwargs) -> Dict:
        """Create a new maintenance request"""
        try:
            request_id = str(uuid.uuid4())
            
            request = MaintenanceRequest(
                id=request_id,
                property_id=property_id,
                title=title,
                description=description,
                maintenance_type=maintenance_type,
                priority=priority,
                status=MaintenanceStatus.PENDING,
                requested_by=requested_by,
                created_at=datetime.utcnow(),
                **kwargs
            )
            
            self.maintenance_requests[request_id] = request
            
            # Auto-assign if emergency
            if priority == Priority.EMERGENCY:
                self._auto_assign_emergency_request(request)
            
            logger.info(f"Maintenance request created: {title}")
            return {
                'success': True,
                'request_id': request_id,
                'request': self._serialize_maintenance_request(request)
            }
            
        except Exception as e:
            logger.error(f"Failed to create maintenance request: {e}")
            return {'success': False, 'error': str(e)}
    
    def schedule_maintenance_request(self, request_id: str, scheduled_date: datetime,
                                   vendor_id: Optional[str] = None) -> Dict:
        """Schedule a maintenance request"""
        try:
            if request_id not in self.maintenance_requests:
                return {'success': False, 'error': 'Maintenance request not found'}
            
            request = self.maintenance_requests[request_id]
            
            # Find best vendor if not specified
            if not vendor_id:
                vendor_id = self._find_best_vendor(request)
                if not vendor_id:
                    return {'success': False, 'error': 'No available vendor found'}
            
            # Create work assignment
            assignment_id = str(uuid.uuid4())
            estimated_hours = request.estimated_hours or 2.0
            
            assignment = WorkOrderAssignment(
                id=assignment_id,
                request_id=request_id,
                vendor_id=vendor_id,
                assigned_at=datetime.utcnow(),
                scheduled_start=scheduled_date,
                scheduled_end=scheduled_date + timedelta(hours=estimated_hours)
            )
            
            self.work_assignments[assignment_id] = assignment
            
            # Update request
            request.status = MaintenanceStatus.SCHEDULED
            request.scheduled_date = scheduled_date
            request.assigned_vendor_id = vendor_id
            
            # Send notifications
            self._send_vendor_notification(vendor_id, request, scheduled_date)
            if request.tenant_access_required:
                self._send_tenant_notification(request)
            
            logger.info(f"Maintenance request scheduled: {request.title}")
            return {
                'success': True,
                'assignment_id': assignment_id,
                'scheduled_date': scheduled_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule maintenance request: {e}")
            return {'success': False, 'error': str(e)}
    
    def _find_best_vendor(self, request: MaintenanceRequest) -> Optional[str]:
        """Find the best available vendor for a request"""
        try:
            available_vendors = []
            
            for vendor in self.vendors.values():
                if not vendor.is_active or vendor.status != VendorStatus.AVAILABLE:
                    continue
                
                # Check if vendor has required specialties
                if request.item_id:
                    item = self.maintenance_items.get(request.item_id)
                    if item and item.category not in vendor.specialties:
                        continue
                
                # Calculate vendor score (rating, availability, cost)
                score = vendor.rating * 0.6 + (5.0 - vendor.hourly_rate/20) * 0.4
                available_vendors.append((vendor.id, score))
            
            if available_vendors:
                # Sort by score and return best vendor
                available_vendors.sort(key=lambda x: x[1], reverse=True)
                return available_vendors[0][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find best vendor: {e}")
            return None
    
    def _auto_assign_emergency_request(self, request: MaintenanceRequest):
        """Auto-assign emergency requests to available vendors"""
        try:
            vendor_id = self._find_best_vendor(request)
            if vendor_id:
                # Schedule for immediate response (within 2 hours)
                emergency_date = datetime.utcnow() + timedelta(hours=2)
                self.schedule_maintenance_request(request.id, emergency_date, vendor_id)
                
                # Send immediate alerts
                self._send_emergency_alerts(request, vendor_id)
                
        except Exception as e:
            logger.error(f"Failed to auto-assign emergency request: {e}")
    
    def update_maintenance_status(self, request_id: str, status: MaintenanceStatus,
                                notes: str = "", actual_hours: float = None,
                                actual_cost: float = None) -> Dict:
        """Update maintenance request status"""
        try:
            if request_id not in self.maintenance_requests:
                return {'success': False, 'error': 'Maintenance request not found'}
            
            request = self.maintenance_requests[request_id]
            old_status = request.status
            request.status = status
            
            # Add status note
            if notes:
                request.notes.append({
                    'timestamp': datetime.utcnow().isoformat(),
                    'type': 'status_update',
                    'content': notes,
                    'status_change': f"{old_status.value} -> {status.value}"
                })
            
            # Update completion details
            if status == MaintenanceStatus.COMPLETED:
                request.completed_date = datetime.utcnow()
                if actual_hours:
                    request.actual_hours = actual_hours
                if actual_cost:
                    request.actual_cost = actual_cost
                
                # Update item last service date
                if request.item_id and request.item_id in self.maintenance_items:
                    item = self.maintenance_items[request.item_id]
                    item.last_service_date = datetime.utcnow()
                    # Calculate next service due
                    schedules = [s for s in self.maintenance_schedules.values() 
                               if s.item_id == request.item_id and s.is_active]
                    if schedules:
                        next_due = min(item.last_service_date + timedelta(days=s.frequency_days) 
                                     for s in schedules)
                        item.next_service_due = next_due
            
            logger.info(f"Maintenance status updated: {request.title} -> {status.value}")
            return {
                'success': True,
                'request': self._serialize_maintenance_request(request)
            }
            
        except Exception as e:
            logger.error(f"Failed to update maintenance status: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_scheduled_maintenance(self, start_date: datetime = None, 
                                end_date: datetime = None) -> Dict:
        """Get scheduled maintenance for a date range"""
        try:
            if not start_date:
                start_date = datetime.utcnow()
            if not end_date:
                end_date = start_date + timedelta(days=30)
            
            # Get scheduled requests
            scheduled_requests = []
            for request in self.maintenance_requests.values():
                if (request.status == MaintenanceStatus.SCHEDULED and 
                    request.scheduled_date and
                    start_date <= request.scheduled_date <= end_date):
                    scheduled_requests.append(self._serialize_maintenance_request(request))
            
            # Get upcoming preventive maintenance
            upcoming_preventive = []
            for item in self.maintenance_items.values():
                if (item.next_service_due and item.is_active and
                    start_date <= item.next_service_due <= end_date):
                    upcoming_preventive.append({
                        'item': self._serialize_maintenance_item(item),
                        'due_date': item.next_service_due.isoformat(),
                        'overdue_days': max(0, (datetime.utcnow() - item.next_service_due).days)
                    })
            
            return {
                'success': True,
                'scheduled_requests': scheduled_requests,
                'upcoming_preventive': upcoming_preventive,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get scheduled maintenance: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_preventive_maintenance_requests(self) -> Dict:
        """Generate maintenance requests for overdue preventive maintenance"""
        try:
            generated_count = 0
            current_date = datetime.utcnow()
            
            for item in self.maintenance_items.values():
                if not item.is_active or not item.next_service_due:
                    continue
                
                # Check if preventive maintenance is due or overdue
                if item.next_service_due <= current_date:
                    # Find applicable schedules
                    schedules = [s for s in self.maintenance_schedules.values() 
                               if s.item_id == item.id and s.is_active]
                    
                    for schedule in schedules:
                        # Check if request already exists for this schedule
                        existing_requests = [r for r in self.maintenance_requests.values()
                                           if (r.item_id == item.id and 
                                               r.maintenance_type == schedule.maintenance_type and
                                               r.status in [MaintenanceStatus.PENDING, MaintenanceStatus.SCHEDULED])]
                        
                        if not existing_requests:
                            # Create preventive maintenance request
                            overdue_days = (current_date - item.next_service_due).days
                            priority = Priority.HIGH if overdue_days > 7 else Priority.MEDIUM
                            
                            request_result = self.create_maintenance_request(
                                property_id=item.property_id,
                                title=f"Scheduled {schedule.maintenance_type.value.title()}: {item.name}",
                                description=schedule.description,
                                maintenance_type=schedule.maintenance_type,
                                priority=priority,
                                requested_by=1,  # System user
                                item_id=item.id,
                                estimated_hours=schedule.estimated_duration_hours,
                                estimated_cost=schedule.estimated_cost
                            )
                            
                            if request_result['success']:
                                generated_count += 1
            
            logger.info(f"Generated {generated_count} preventive maintenance requests")
            return {
                'success': True,
                'generated_count': generated_count
            }
            
        except Exception as e:
            logger.error(f"Failed to generate preventive maintenance requests: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_maintenance_dashboard_data(self) -> Dict:
        """Get dashboard data for maintenance management"""
        try:
            current_date = datetime.utcnow()
            
            # Request statistics
            total_requests = len(self.maintenance_requests)
            pending_requests = len([r for r in self.maintenance_requests.values() 
                                  if r.status == MaintenanceStatus.PENDING])
            scheduled_requests = len([r for r in self.maintenance_requests.values() 
                                    if r.status == MaintenanceStatus.SCHEDULED])
            in_progress_requests = len([r for r in self.maintenance_requests.values() 
                                      if r.status == MaintenanceStatus.IN_PROGRESS])
            completed_requests = len([r for r in self.maintenance_requests.values() 
                                    if r.status == MaintenanceStatus.COMPLETED])
            
            # Emergency requests
            emergency_requests = [r for r in self.maintenance_requests.values() 
                                if r.priority == Priority.EMERGENCY and 
                                r.status not in [MaintenanceStatus.COMPLETED, MaintenanceStatus.CANCELLED]]
            
            # Overdue maintenance
            overdue_items = []
            for item in self.maintenance_items.values():
                if (item.is_active and item.next_service_due and 
                    item.next_service_due < current_date):
                    overdue_days = (current_date - item.next_service_due).days
                    overdue_items.append({
                        'item': self._serialize_maintenance_item(item),
                        'overdue_days': overdue_days
                    })
            
            # Vendor performance
            vendor_stats = {}
            for vendor in self.vendors.values():
                if vendor.is_active:
                    assigned_requests = [r for r in self.maintenance_requests.values() 
                                       if r.assigned_vendor_id == vendor.id]
                    completed = len([r for r in assigned_requests 
                                   if r.status == MaintenanceStatus.COMPLETED])
                    vendor_stats[vendor.id] = {
                        'name': vendor.name,
                        'total_assigned': len(assigned_requests),
                        'completed': completed,
                        'completion_rate': completed / len(assigned_requests) * 100 if assigned_requests else 0,
                        'rating': vendor.rating,
                        'status': vendor.status.value
                    }
            
            # Recent activity
            recent_requests = sorted(
                [self._serialize_maintenance_request(r) for r in self.maintenance_requests.values()],
                key=lambda x: x['created_at'], reverse=True
            )[:10]
            
            return {
                'success': True,
                'overview': {
                    'total_requests': total_requests,
                    'pending_requests': pending_requests,
                    'scheduled_requests': scheduled_requests,
                    'in_progress_requests': in_progress_requests,
                    'completed_requests': completed_requests,
                    'emergency_requests': len(emergency_requests),
                    'overdue_items': len(overdue_items),
                    'active_vendors': len([v for v in self.vendors.values() if v.is_active])
                },
                'emergency_requests': [self._serialize_maintenance_request(r) for r in emergency_requests],
                'overdue_maintenance': overdue_items,
                'vendor_performance': vendor_stats,
                'recent_activity': recent_requests
            }
            
        except Exception as e:
            logger.error(f"Failed to get maintenance dashboard data: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_vendor_notification(self, vendor_id: str, request: MaintenanceRequest, 
                                scheduled_date: datetime):
        """Send notification to vendor about new assignment"""
        try:
            if vendor_id not in self.vendors:
                return
            
            vendor = self.vendors[vendor_id]
            subject = f"New Maintenance Assignment: {request.title}"
            
            body = f"""
            Dear {vendor.contact_person},
            
            You have been assigned a new maintenance request:
            
            Request ID: {request.id}
            Title: {request.title}
            Description: {request.description}
            Priority: {request.priority.value.upper()}
            Scheduled Date: {scheduled_date.strftime('%Y-%m-%d %H:%M')}
            Property ID: {request.property_id}
            
            Please confirm your availability and contact the property manager if you have any questions.
            
            Best regards,
            EstateCore Maintenance Team
            """
            
            self._send_email(vendor.email, subject, body)
            logger.info(f"Vendor notification sent to {vendor.name}")
            
        except Exception as e:
            logger.error(f"Failed to send vendor notification: {e}")
    
    def _send_tenant_notification(self, request: MaintenanceRequest):
        """Send notification to tenant about upcoming maintenance"""
        try:
            # Would get tenant email from property/tenant data
            subject = f"Scheduled Maintenance Notice - {request.title}"
            
            body = f"""
            Dear Tenant,
            
            This is to inform you that maintenance has been scheduled for your unit:
            
            Maintenance Type: {request.maintenance_type.value.title()}
            Description: {request.description}
            Scheduled Date: {request.scheduled_date.strftime('%Y-%m-%d %H:%M') if request.scheduled_date else 'TBD'}
            
            Please ensure access to your unit is available during the scheduled time.
            
            If you have any questions or concerns, please contact the property management office.
            
            Best regards,
            Property Management Team
            """
            
            # Would send to actual tenant email
            logger.info(f"Tenant notification prepared for request {request.id}")
            
        except Exception as e:
            logger.error(f"Failed to send tenant notification: {e}")
    
    def _send_emergency_alerts(self, request: MaintenanceRequest, vendor_id: str):
        """Send emergency alerts for critical maintenance issues"""
        try:
            vendor = self.vendors.get(vendor_id)
            if vendor:
                subject = f"EMERGENCY MAINTENANCE - {request.title}"
                
                body = f"""
                EMERGENCY MAINTENANCE REQUEST
                
                This is an urgent maintenance request requiring immediate attention:
                
                Request ID: {request.id}
                Title: {request.title}
                Description: {request.description}
                Priority: EMERGENCY
                Property ID: {request.property_id}
                
                Please respond immediately and contact the property manager.
                
                Emergency Contact: [Property Manager Phone]
                """
                
                self._send_email(vendor.email, subject, body)
                logger.warning(f"Emergency alert sent for request {request.id}")
                
        except Exception as e:
            logger.error(f"Failed to send emergency alert: {e}")
    
    def _send_email(self, to_email: str, subject: str, body: str):
        """Send email notification"""
        try:
            if not self.email_username or not self.email_password:
                logger.info(f"Email simulation: {subject} to {to_email}")
                return
            
            msg = MIMEMultipart()
            msg['From'] = self.email_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_server, self.email_port)
            server.starttls()
            server.login(self.email_username, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_username, to_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
    
    def _serialize_maintenance_item(self, item: MaintenanceItem) -> Dict:
        """Serialize maintenance item to dictionary"""
        return {
            'id': item.id,
            'property_id': item.property_id,
            'name': item.name,
            'category': item.category,
            'model': item.model,
            'serial_number': item.serial_number,
            'installation_date': item.installation_date.isoformat() if item.installation_date else None,
            'warranty_expires': item.warranty_expires.isoformat() if item.warranty_expires else None,
            'last_service_date': item.last_service_date.isoformat() if item.last_service_date else None,
            'next_service_due': item.next_service_due.isoformat() if item.next_service_due else None,
            'service_interval_days': item.service_interval_days,
            'is_active': item.is_active,
            'metadata': item.metadata
        }
    
    def _serialize_maintenance_schedule(self, schedule: MaintenanceSchedule) -> Dict:
        """Serialize maintenance schedule to dictionary"""
        return {
            'id': schedule.id,
            'item_id': schedule.item_id,
            'maintenance_type': schedule.maintenance_type.value,
            'description': schedule.description,
            'frequency_days': schedule.frequency_days,
            'estimated_duration_hours': schedule.estimated_duration_hours,
            'required_skills': schedule.required_skills,
            'required_tools': schedule.required_tools,
            'estimated_cost': schedule.estimated_cost,
            'is_active': schedule.is_active,
            'created_at': schedule.created_at.isoformat(),
            'instructions': schedule.instructions
        }
    
    def _serialize_maintenance_request(self, request: MaintenanceRequest) -> Dict:
        """Serialize maintenance request to dictionary"""
        return {
            'id': request.id,
            'property_id': request.property_id,
            'item_id': request.item_id,
            'requested_by': request.requested_by,
            'title': request.title,
            'description': request.description,
            'maintenance_type': request.maintenance_type.value,
            'priority': request.priority.value,
            'status': request.status.value,
            'created_at': request.created_at.isoformat(),
            'scheduled_date': request.scheduled_date.isoformat() if request.scheduled_date else None,
            'completed_date': request.completed_date.isoformat() if request.completed_date else None,
            'assigned_vendor_id': request.assigned_vendor_id,
            'estimated_cost': request.estimated_cost,
            'actual_cost': request.actual_cost,
            'estimated_hours': request.estimated_hours,
            'actual_hours': request.actual_hours,
            'tenant_access_required': request.tenant_access_required,
            'tenant_notification_sent': request.tenant_notification_sent,
            'photos': request.photos,
            'notes': request.notes,
            'metadata': request.metadata
        }
    
    def _serialize_vendor(self, vendor: Vendor) -> Dict:
        """Serialize vendor to dictionary"""
        return {
            'id': vendor.id,
            'name': vendor.name,
            'contact_person': vendor.contact_person,
            'email': vendor.email,
            'phone': vendor.phone,
            'address': vendor.address,
            'specialties': vendor.specialties,
            'rating': vendor.rating,
            'hourly_rate': vendor.hourly_rate,
            'availability_schedule': vendor.availability_schedule,
            'status': vendor.status.value,
            'insurance_expires': vendor.insurance_expires.isoformat() if vendor.insurance_expires else None,
            'license_number': vendor.license_number,
            'created_at': vendor.created_at.isoformat(),
            'is_active': vendor.is_active
        }

# Singleton instance
_maintenance_service = None

def get_maintenance_service() -> MaintenanceSchedulingService:
    """Get singleton maintenance scheduling service instance"""
    global _maintenance_service
    if _maintenance_service is None:
        _maintenance_service = MaintenanceSchedulingService()
    return _maintenance_service

if __name__ == "__main__":
    # Test the maintenance scheduling service
    service = get_maintenance_service()
    
    print("🔧 Maintenance Scheduling Service Test")
    
    # Test maintenance request creation
    request_result = service.create_maintenance_request(
        property_id=1,
        title="HVAC Filter Replacement",
        description="Replace air filters in main HVAC unit",
        maintenance_type=MaintenanceType.PREVENTIVE,
        priority=Priority.MEDIUM,
        requested_by=1,
        estimated_hours=2.0,
        estimated_cost=100.0
    )
    print(f"Request creation: {request_result.get('success', False)}")
    
    # Test scheduling
    if request_result.get('success'):
        request_id = request_result['request_id']
        scheduled_date = datetime.utcnow() + timedelta(days=1)
        
        schedule_result = service.schedule_maintenance_request(request_id, scheduled_date)
        print(f"Scheduling: {schedule_result.get('success', False)}")
    
    # Test dashboard data
    dashboard = service.get_maintenance_dashboard_data()
    print(f"Dashboard data: {dashboard.get('success', False)}")
    
    # Test preventive maintenance generation
    preventive_result = service.generate_preventive_maintenance_requests()
    print(f"Preventive generation: {preventive_result.get('success', False)}")
    
    print("✅ Maintenance scheduling service is ready!")
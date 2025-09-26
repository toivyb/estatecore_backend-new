"""
Escalation Manager for EstateCore Tenant Chatbot

Manages conversation escalations to human agents with intelligent routing,
priority management, and notification systems.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import asyncio

from ai_modules.chatbot.conversation_manager import EscalationReason

class EscalationPriority(Enum):
    """Escalation priority levels"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class EscalationStatus(Enum):
    """Escalation status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"

@dataclass
class Agent:
    """Human agent information"""
    agent_id: str
    name: str
    email: str
    phone: Optional[str]
    department: str
    specialties: List[str]
    max_concurrent_cases: int
    current_cases: int
    availability_status: str  # available, busy, offline
    shift_start: Optional[str] = None
    shift_end: Optional[str] = None
    languages: List[str] = None
    
    def __post_init__(self):
        if self.languages is None:
            self.languages = ['en']

@dataclass
class EscalationTicket:
    """Escalation ticket"""
    ticket_id: str
    conversation_id: str
    user_id: str
    tenant_id: Optional[str]
    property_id: Optional[str]
    reason: EscalationReason
    priority: EscalationPriority
    status: EscalationStatus
    created_at: datetime
    assigned_agent: Optional[str] = None
    assigned_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    user_context: Optional[Dict] = None
    conversation_summary: Optional[str] = None
    estimated_resolution_time: Optional[int] = None  # minutes
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class EscalationManager:
    """
    Advanced escalation management system for tenant chatbot
    """
    
    def __init__(self):
        """Initialize Escalation Manager"""
        self.logger = logging.getLogger(__name__)
        
        # Storage (in production, use database)
        self.escalation_tickets: Dict[str, EscalationTicket] = {}
        self.agents: Dict[str, Agent] = {}
        self.escalation_queue: List[str] = []  # ticket_ids in priority order
        
        # Configuration
        self.sla_times = {  # in minutes
            EscalationPriority.EMERGENCY: 5,
            EscalationPriority.URGENT: 15,
            EscalationPriority.HIGH: 60,
            EscalationPriority.MEDIUM: 240,
            EscalationPriority.LOW: 1440  # 24 hours
        }
        
        self.auto_assignment_enabled = True
        self.notification_enabled = True
        self.max_queue_size = 100
        
        # Initialize with demo agents
        self._initialize_demo_agents()
        
        self.logger.info("Escalation Manager initialized")
    
    def escalate_conversation(self, conversation_id: str, reason: EscalationReason,
                            user_context: Optional[Dict] = None) -> bool:
        """
        Escalate a conversation to human agents
        
        Args:
            conversation_id: Conversation to escalate
            reason: Reason for escalation
            user_context: Additional user context
            
        Returns:
            True if escalation successful, False otherwise
        """
        try:
            # Determine priority based on reason
            priority = self._determine_priority(reason, user_context)
            
            # Create escalation ticket
            ticket = EscalationTicket(
                ticket_id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                user_id=user_context.get('user_id') if user_context else 'unknown',
                tenant_id=user_context.get('tenant_id') if user_context else None,
                property_id=user_context.get('property_id') if user_context else None,
                reason=reason,
                priority=priority,
                status=EscalationStatus.PENDING,
                created_at=datetime.now(),
                user_context=user_context,
                estimated_resolution_time=self.sla_times[priority]
            )
            
            # Add relevant tags
            ticket.tags = self._generate_tags(reason, user_context)
            
            # Store ticket
            self.escalation_tickets[ticket.ticket_id] = ticket
            
            # Add to queue
            self._add_to_queue(ticket.ticket_id, priority)
            
            # Auto-assign if enabled and agents available
            if self.auto_assignment_enabled:
                self._attempt_auto_assignment(ticket.ticket_id)
            
            # Send notifications
            if self.notification_enabled:
                self._send_escalation_notifications(ticket)
            
            self.logger.info(f"Escalated conversation {conversation_id} - Ticket: {ticket.ticket_id}, Priority: {priority.value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error escalating conversation: {e}")
            return False
    
    def assign_to_agent(self, ticket_id: str, agent_id: str) -> bool:
        """
        Assign escalation ticket to specific agent
        
        Args:
            ticket_id: Escalation ticket ID
            agent_id: Agent to assign to
            
        Returns:
            True if assignment successful, False otherwise
        """
        try:
            ticket = self.escalation_tickets.get(ticket_id)
            agent = self.agents.get(agent_id)
            
            if not ticket or not agent:
                return False
            
            # Check if agent is available and has capacity
            if not self._can_assign_to_agent(agent_id):
                return False
            
            # Update ticket
            ticket.assigned_agent = agent_id
            ticket.assigned_at = datetime.now()
            ticket.status = EscalationStatus.ASSIGNED
            
            # Update agent
            agent.current_cases += 1
            
            # Remove from queue
            if ticket_id in self.escalation_queue:
                self.escalation_queue.remove(ticket_id)
            
            # Notify agent
            self._notify_agent_assignment(agent_id, ticket)
            
            self.logger.info(f"Assigned ticket {ticket_id} to agent {agent_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error assigning ticket: {e}")
            return False
    
    def update_ticket_status(self, ticket_id: str, status: EscalationStatus,
                           resolution_notes: Optional[str] = None) -> bool:
        """
        Update escalation ticket status
        
        Args:
            ticket_id: Ticket ID
            status: New status
            resolution_notes: Optional resolution notes
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            ticket = self.escalation_tickets.get(ticket_id)
            if not ticket:
                return False
            
            old_status = ticket.status
            ticket.status = status
            
            if status == EscalationStatus.RESOLVED:
                ticket.resolved_at = datetime.now()
                ticket.resolution_notes = resolution_notes
                
                # Free up agent capacity
                if ticket.assigned_agent:
                    agent = self.agents.get(ticket.assigned_agent)
                    if agent and agent.current_cases > 0:
                        agent.current_cases -= 1
            
            elif status == EscalationStatus.IN_PROGRESS and old_status == EscalationStatus.ASSIGNED:
                # Agent has started working on the ticket
                pass
            
            self.logger.info(f"Updated ticket {ticket_id} status: {old_status.value} -> {status.value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating ticket status: {e}")
            return False
    
    def get_escalation_queue(self, priority_filter: Optional[EscalationPriority] = None) -> List[Dict]:
        """
        Get escalation queue with optional priority filtering
        
        Args:
            priority_filter: Optional priority filter
            
        Returns:
            List of escalation tickets in queue
        """
        try:
            queue_items = []
            
            for ticket_id in self.escalation_queue:
                ticket = self.escalation_tickets.get(ticket_id)
                if not ticket:
                    continue
                
                if priority_filter and ticket.priority != priority_filter:
                    continue
                
                # Calculate wait time
                wait_time = (datetime.now() - ticket.created_at).total_seconds() / 60
                
                # Check SLA breach
                sla_breach = wait_time > ticket.estimated_resolution_time
                
                queue_items.append({
                    'ticket_id': ticket.ticket_id,
                    'conversation_id': ticket.conversation_id,
                    'priority': ticket.priority.value,
                    'reason': ticket.reason.value,
                    'created_at': ticket.created_at.isoformat(),
                    'wait_time_minutes': int(wait_time),
                    'sla_breach': sla_breach,
                    'user_context': ticket.user_context,
                    'tags': ticket.tags
                })
            
            return queue_items
            
        except Exception as e:
            self.logger.error(f"Error getting escalation queue: {e}")
            return []
    
    def get_agent_workload(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get agent workload information
        
        Args:
            agent_id: Specific agent ID (None for all agents)
            
        Returns:
            Agent workload information
        """
        try:
            if agent_id:
                agent = self.agents.get(agent_id)
                if not agent:
                    return {}
                
                # Get tickets assigned to this agent
                assigned_tickets = [
                    ticket for ticket in self.escalation_tickets.values()
                    if ticket.assigned_agent == agent_id and ticket.status != EscalationStatus.RESOLVED
                ]
                
                return {
                    'agent_id': agent_id,
                    'name': agent.name,
                    'current_cases': agent.current_cases,
                    'max_concurrent_cases': agent.max_concurrent_cases,
                    'utilization': agent.current_cases / agent.max_concurrent_cases if agent.max_concurrent_cases > 0 else 0,
                    'availability_status': agent.availability_status,
                    'assigned_tickets': [ticket.ticket_id for ticket in assigned_tickets],
                    'department': agent.department,
                    'specialties': agent.specialties
                }
            else:
                # All agents summary
                agents_info = []
                for agent in self.agents.values():
                    agents_info.append(self.get_agent_workload(agent.agent_id))
                
                return {
                    'total_agents': len(self.agents),
                    'available_agents': len([a for a in self.agents.values() if a.availability_status == 'available']),
                    'total_capacity': sum(a.max_concurrent_cases for a in self.agents.values()),
                    'current_utilization': sum(a.current_cases for a in self.agents.values()),
                    'agents': agents_info
                }
                
        except Exception as e:
            self.logger.error(f"Error getting agent workload: {e}")
            return {}
    
    def get_escalation_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get escalation analytics for specified period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analytics dictionary
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter tickets in time period
            period_tickets = [
                ticket for ticket in self.escalation_tickets.values()
                if ticket.created_at >= cutoff_date
            ]
            
            if not period_tickets:
                return {'message': 'No escalations in specified period'}
            
            # Calculate metrics
            total_escalations = len(period_tickets)
            resolved_tickets = [t for t in period_tickets if t.status == EscalationStatus.RESOLVED]
            resolution_rate = len(resolved_tickets) / total_escalations if total_escalations > 0 else 0
            
            # Average resolution time (for resolved tickets)
            resolution_times = []
            for ticket in resolved_tickets:
                if ticket.resolved_at and ticket.created_at:
                    resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 60
                    resolution_times.append(resolution_time)
            
            avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            # Escalation reasons breakdown
            reason_counts = {}
            for ticket in period_tickets:
                reason = ticket.reason.value
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            # Priority breakdown
            priority_counts = {}
            for ticket in period_tickets:
                priority = ticket.priority.value
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # SLA compliance
            sla_breaches = 0
            for ticket in resolved_tickets:
                if ticket.resolved_at and ticket.created_at:
                    resolution_time = (ticket.resolved_at - ticket.created_at).total_seconds() / 60
                    if resolution_time > ticket.estimated_resolution_time:
                        sla_breaches += 1
            
            sla_compliance = 1 - (sla_breaches / len(resolved_tickets)) if resolved_tickets else 1
            
            return {
                'period_days': days,
                'total_escalations': total_escalations,
                'resolution_rate': resolution_rate,
                'average_resolution_time_minutes': avg_resolution_time,
                'sla_compliance_rate': sla_compliance,
                'escalation_reasons': reason_counts,
                'priority_distribution': priority_counts,
                'pending_escalations': len([t for t in period_tickets if t.status == EscalationStatus.PENDING])
            }
            
        except Exception as e:
            self.logger.error(f"Error getting escalation analytics: {e}")
            return {}
    
    def _determine_priority(self, reason: EscalationReason, 
                           user_context: Optional[Dict]) -> EscalationPriority:
        """Determine escalation priority based on reason and context"""
        
        # Emergency situations get highest priority
        if reason == EscalationReason.EMERGENCY:
            return EscalationPriority.EMERGENCY
        
        # Check user context for priority indicators
        if user_context:
            priority_override = user_context.get('priority')
            if priority_override in ['urgent', 'high']:
                return EscalationPriority.URGENT
        
        # Map reasons to priorities
        priority_mapping = {
            EscalationReason.NEGATIVE_SENTIMENT: EscalationPriority.HIGH,
            EscalationReason.MULTIPLE_FAILURES: EscalationPriority.HIGH,
            EscalationReason.COMPLEX_QUERY: EscalationPriority.MEDIUM,
            EscalationReason.LOW_CONFIDENCE: EscalationPriority.MEDIUM,
            EscalationReason.USER_REQUEST: EscalationPriority.LOW
        }
        
        return priority_mapping.get(reason, EscalationPriority.MEDIUM)
    
    def _generate_tags(self, reason: EscalationReason, 
                      user_context: Optional[Dict]) -> List[str]:
        """Generate tags for escalation ticket"""
        tags = [reason.value]
        
        if user_context:
            if user_context.get('tenant_id'):
                tags.append('tenant')
            if user_context.get('property_id'):
                tags.append(f"property:{user_context['property_id']}")
            if user_context.get('unit_number'):
                tags.append('unit_specific')
        
        return tags
    
    def _add_to_queue(self, ticket_id: str, priority: EscalationPriority):
        """Add ticket to escalation queue in priority order"""
        
        # Remove if already in queue
        if ticket_id in self.escalation_queue:
            self.escalation_queue.remove(ticket_id)
        
        # Find insertion position based on priority
        priority_order = [
            EscalationPriority.EMERGENCY,
            EscalationPriority.URGENT, 
            EscalationPriority.HIGH,
            EscalationPriority.MEDIUM,
            EscalationPriority.LOW
        ]
        
        priority_index = priority_order.index(priority)
        
        # Insert at appropriate position
        insert_index = 0
        for i, existing_ticket_id in enumerate(self.escalation_queue):
            existing_ticket = self.escalation_tickets.get(existing_ticket_id)
            if existing_ticket:
                existing_priority_index = priority_order.index(existing_ticket.priority)
                if existing_priority_index > priority_index:
                    insert_index = i
                    break
                insert_index = i + 1
        
        self.escalation_queue.insert(insert_index, ticket_id)
        
        # Maintain queue size limit
        if len(self.escalation_queue) > self.max_queue_size:
            # Remove oldest low priority items
            removed = []
            for i in range(len(self.escalation_queue) - 1, -1, -1):
                ticket = self.escalation_tickets.get(self.escalation_queue[i])
                if ticket and ticket.priority == EscalationPriority.LOW:
                    removed_id = self.escalation_queue.pop(i)
                    removed.append(removed_id)
                    if len(self.escalation_queue) <= self.max_queue_size:
                        break
            
            if removed:
                self.logger.warning(f"Removed {len(removed)} low priority tickets from queue due to size limit")
    
    def _attempt_auto_assignment(self, ticket_id: str) -> bool:
        """Attempt to auto-assign ticket to available agent"""
        try:
            ticket = self.escalation_tickets.get(ticket_id)
            if not ticket:
                return False
            
            # Find best available agent
            best_agent = self._find_best_agent(ticket)
            if best_agent:
                return self.assign_to_agent(ticket_id, best_agent.agent_id)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error in auto-assignment: {e}")
            return False
    
    def _find_best_agent(self, ticket: EscalationTicket) -> Optional[Agent]:
        """Find the best available agent for a ticket"""
        available_agents = [
            agent for agent in self.agents.values()
            if self._can_assign_to_agent(agent.agent_id)
        ]
        
        if not available_agents:
            return None
        
        # Score agents based on suitability
        agent_scores = []
        
        for agent in available_agents:
            score = 0
            
            # Specialization match
            if ticket.reason.value in agent.specialties:
                score += 10
            
            # Department match (basic implementation)
            if 'maintenance' in ticket.tags and agent.department == 'maintenance':
                score += 5
            elif 'leasing' in ticket.tags and agent.department == 'leasing':
                score += 5
            
            # Workload factor (prefer less busy agents)
            utilization = agent.current_cases / agent.max_concurrent_cases if agent.max_concurrent_cases > 0 else 1
            score += (1 - utilization) * 5
            
            agent_scores.append((agent, score))
        
        # Return agent with highest score
        best_agent, _ = max(agent_scores, key=lambda x: x[1])
        return best_agent
    
    def _can_assign_to_agent(self, agent_id: str) -> bool:
        """Check if agent can take new assignments"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        return (agent.availability_status == 'available' and 
                agent.current_cases < agent.max_concurrent_cases)
    
    def _send_escalation_notifications(self, ticket: EscalationTicket):
        """Send notifications about new escalation"""
        # This would integrate with your notification system
        # For now, just log
        self.logger.info(f"Notification: New {ticket.priority.value} priority escalation - Ticket {ticket.ticket_id}")
    
    def _notify_agent_assignment(self, agent_id: str, ticket: EscalationTicket):
        """Notify agent about assignment"""
        agent = self.agents.get(agent_id)
        if agent:
            self.logger.info(f"Notification to {agent.name}: Assigned escalation ticket {ticket.ticket_id}")
    
    def _initialize_demo_agents(self):
        """Initialize demo agents for testing"""
        demo_agents = [
            Agent(
                agent_id="agent_001",
                name="Sarah Johnson",
                email="sarah.johnson@estatecore.com",
                phone="(555) 123-4567",
                department="customer_service",
                specialties=["general_inquiry", "rent_payment", "account_balance"],
                max_concurrent_cases=5,
                current_cases=0,
                availability_status="available",
                shift_start="09:00",
                shift_end="17:00"
            ),
            Agent(
                agent_id="agent_002", 
                name="Mike Rodriguez",
                email="mike.rodriguez@estatecore.com",
                phone="(555) 123-4568",
                department="maintenance",
                specialties=["maintenance_request", "emergency"],
                max_concurrent_cases=3,
                current_cases=0,
                availability_status="available",
                shift_start="08:00",
                shift_end="16:00"
            ),
            Agent(
                agent_id="agent_003",
                name="Emily Chen", 
                email="emily.chen@estatecore.com",
                phone="(555) 123-4569",
                department="leasing",
                specialties=["lease_inquiry", "amenities_info", "move_in_out"],
                max_concurrent_cases=4,
                current_cases=0,
                availability_status="available", 
                shift_start="10:00",
                shift_end="18:00",
                languages=["en", "zh"]
            )
        ]
        
        for agent in demo_agents:
            self.agents[agent.agent_id] = agent
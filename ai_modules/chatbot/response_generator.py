"""
Response Generation System for EstateCore Tenant Chatbot

Generates intelligent, context-aware responses using templates,
property data integration, and AI-powered natural language generation.
"""

import logging
import json
import random
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from jinja2 import Template, Environment, DictLoader
import re

@dataclass
class ResponseContext:
    """Context information for response generation"""
    intent: str
    entities: Dict[str, Any]
    user_context: Dict[str, Any]
    conversation_history: List[Dict]
    property_data: Optional[Dict[str, Any]] = None
    tenant_data: Optional[Dict[str, Any]] = None
    confidence: float = 1.0

@dataclass
class GeneratedResponse:
    """Container for generated response"""
    text: str
    response_type: str  # 'text', 'quick_reply', 'card', 'escalation'
    quick_replies: Optional[List[str]] = None
    data: Optional[Dict[str, Any]] = None
    requires_action: bool = False
    escalate: bool = False

class ResponseGenerator:
    """
    Advanced response generation system for tenant chatbot
    """
    
    def __init__(self):
        """Initialize Response Generator"""
        self.logger = logging.getLogger(__name__)
        
        # Response templates organized by intent
        self.templates = self._load_response_templates()
        
        # Jinja2 environment for template rendering
        self.jinja_env = Environment(loader=DictLoader(self.templates))
        
        # Response variations for natural conversation
        self.variations = {
            'greeting': [
                "Hello! How can I help you today?",
                "Hi there! What can I assist you with?",
                "Welcome! How may I help you?",
                "Hello! I'm here to help with any questions you have."
            ],
            'acknowledgment': [
                "I understand.",
                "Got it.",
                "I see.",
                "Thanks for letting me know."
            ],
            'apology': [
                "I apologize for the inconvenience.",
                "Sorry about that.",
                "I'm sorry to hear about this issue.",
                "My apologies for any trouble."
            ],
            'clarification': [
                "Could you please provide more details?",
                "Can you be more specific?",
                "I need a bit more information to help you.",
                "Could you clarify what you mean?"
            ]
        }
        
        self.logger.info("Response Generator initialized")
    
    def generate_response(self, context: ResponseContext) -> GeneratedResponse:
        """
        Generate a response based on context
        
        Args:
            context: Response context information
            
        Returns:
            Generated response object
        """
        try:
            # Get appropriate handler for the intent
            handler_method = getattr(self, f'_handle_{context.intent}', None)
            
            if handler_method:
                return handler_method(context)
            else:
                # Fallback to generic handler
                return self._handle_general_inquiry(context)
        
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return GeneratedResponse(
                text="I apologize, but I'm having trouble processing your request. Could you please try again?",
                response_type='text',
                escalate=True
            )
    
    def _handle_rent_payment(self, context: ResponseContext) -> GeneratedResponse:
        """Handle rent payment related queries"""
        entities = context.entities
        tenant_data = context.tenant_data or {}
        
        # Check if asking about payment methods
        if any(term in context.user_context.get('original_text', '').lower() 
               for term in ['how', 'method', 'pay']):
            
            template = self.jinja_env.get_template('rent_payment_methods')
            response_text = template.render(
                user_name=context.user_context.get('user_name', 'there'),
                payment_methods=['Online portal', 'ACH bank transfer', 'Check', 'Money order']
            )
            
            return GeneratedResponse(
                text=response_text,
                response_type='quick_reply',
                quick_replies=['Pay online now', 'Payment history', 'Set up auto-pay']
            )
        
        # Check if asking about due date
        elif any(term in context.user_context.get('original_text', '').lower() 
                for term in ['when', 'due', 'date']):
            
            due_date = tenant_data.get('next_rent_due_date', 'the 1st of each month')
            
            template = self.jinja_env.get_template('rent_due_date')
            response_text = template.render(
                user_name=context.user_context.get('user_name', 'there'),
                due_date=due_date,
                current_balance=tenant_data.get('current_balance', 0)
            )
            
            return GeneratedResponse(
                text=response_text,
                response_type='text',
                quick_replies=['Pay now', 'Payment history', 'Late fee info']
            )
        
        # Generic rent payment response
        template = self.jinja_env.get_template('rent_payment_general')
        response_text = template.render(
            user_name=context.user_context.get('user_name', 'there'),
            current_balance=tenant_data.get('current_balance', 0)
        )
        
        return GeneratedResponse(
            text=response_text,
            response_type='quick_reply',
            quick_replies=['Pay rent', 'Payment methods', 'Payment history']
        )
    
    def _handle_maintenance_request(self, context: ResponseContext) -> GeneratedResponse:
        """Handle maintenance request queries"""
        entities = context.entities
        urgency = entities.get('urgency', {})
        
        # Check for emergency situations
        if urgency.get('level') == 'emergency':
            template = self.jinja_env.get_template('maintenance_emergency')
            response_text = template.render(
                emergency_number='(555) 123-HELP',
                user_name=context.user_context.get('user_name', 'there')
            )
            
            return GeneratedResponse(
                text=response_text,
                response_type='text',
                requires_action=True,
                escalate=True
            )
        
        # Regular maintenance request
        maintenance_type = entities.get('maintenance_type', 'general')
        
        template = self.jinja_env.get_template('maintenance_request')
        response_text = template.render(
            user_name=context.user_context.get('user_name', 'there'),
            maintenance_type=maintenance_type,
            unit_number=context.user_context.get('unit_number', 'your unit')
        )
        
        return GeneratedResponse(
            text=response_text,
            response_type='quick_reply',
            quick_replies=['Submit request', 'Check status', 'Upload photo'],
            requires_action=True
        )
    
    def _handle_lease_inquiry(self, context: ResponseContext) -> GeneratedResponse:
        """Handle lease-related inquiries"""
        tenant_data = context.tenant_data or {}
        
        # Check what type of lease information is needed
        query_text = context.user_context.get('original_text', '').lower()
        
        if 'renewal' in query_text or 'renew' in query_text:
            lease_end_date = tenant_data.get('lease_end_date', 'your lease end date')
            
            template = self.jinja_env.get_template('lease_renewal')
            response_text = template.render(
                user_name=context.user_context.get('user_name', 'there'),
                lease_end_date=lease_end_date,
                can_renew=tenant_data.get('renewal_eligible', True)
            )
            
            quick_replies = ['Renewal options', 'Schedule meeting', 'Renewal terms'] if tenant_data.get('renewal_eligible', True) else ['Contact leasing']
            
        elif 'document' in query_text or 'copy' in query_text:
            template = self.jinja_env.get_template('lease_documents')
            response_text = template.render(
                user_name=context.user_context.get('user_name', 'there')
            )
            
            quick_replies = ['Download lease', 'Email copy', 'View terms']
            
        else:
            # General lease information
            template = self.jinja_env.get_template('lease_general')
            response_text = template.render(
                user_name=context.user_context.get('user_name', 'there'),
                lease_start=tenant_data.get('lease_start_date', 'N/A'),
                lease_end=tenant_data.get('lease_end_date', 'N/A'),
                rent_amount=tenant_data.get('monthly_rent', 'N/A')
            )
            
            quick_replies = ['Lease terms', 'Renewal info', 'Document copy']
        
        return GeneratedResponse(
            text=response_text,
            response_type='quick_reply',
            quick_replies=quick_replies
        )
    
    def _handle_amenities_info(self, context: ResponseContext) -> GeneratedResponse:
        """Handle amenities and facilities inquiries"""
        property_data = context.property_data or {}
        amenities = property_data.get('amenities', [])
        
        # Check for specific amenity inquiries
        query_text = context.user_context.get('original_text', '').lower()
        
        specific_amenities = {
            'pool': 'swimming pool',
            'gym': 'fitness center',
            'parking': 'parking',
            'laundry': 'laundry facilities'
        }
        
        found_amenity = None
        for key, amenity in specific_amenities.items():
            if key in query_text:
                found_amenity = amenity
                break
        
        if found_amenity:
            template = self.jinja_env.get_template('specific_amenity')
            response_text = template.render(
                user_name=context.user_context.get('user_name', 'there'),
                amenity=found_amenity,
                available=found_amenity.lower() in [a.lower() for a in amenities],
                hours=property_data.get('amenity_hours', {}).get(found_amenity, 'Please contact the office for hours')
            )
        else:
            template = self.jinja_env.get_template('amenities_general')
            response_text = template.render(
                user_name=context.user_context.get('user_name', 'there'),
                amenities=amenities[:5],  # Show top 5 amenities
                total_count=len(amenities)
            )
        
        return GeneratedResponse(
            text=response_text,
            response_type='quick_reply',
            quick_replies=['Pool hours', 'Gym access', 'Parking info', 'All amenities']
        )
    
    def _handle_contact_info(self, context: ResponseContext) -> GeneratedResponse:
        """Handle contact information requests"""
        property_data = context.property_data or {}
        
        template = self.jinja_env.get_template('contact_info')
        response_text = template.render(
            user_name=context.user_context.get('user_name', 'there'),
            office_hours=property_data.get('office_hours', 'Monday-Friday 9AM-5PM'),
            office_phone=property_data.get('office_phone', '(555) 123-4567'),
            emergency_phone=property_data.get('emergency_phone', '(555) 123-HELP'),
            email=property_data.get('office_email', 'info@property.com'),
            address=property_data.get('office_address', 'Leasing Office')
        )
        
        return GeneratedResponse(
            text=response_text,
            response_type='text',
            quick_replies=['Call office', 'Emergency contact', 'Email office']
        )
    
    def _handle_account_balance(self, context: ResponseContext) -> GeneratedResponse:
        """Handle account balance inquiries"""
        tenant_data = context.tenant_data or {}
        
        current_balance = tenant_data.get('current_balance', 0)
        last_payment = tenant_data.get('last_payment', {})
        
        template = self.jinja_env.get_template('account_balance')
        response_text = template.render(
            user_name=context.user_context.get('user_name', 'there'),
            current_balance=current_balance,
            last_payment_amount=last_payment.get('amount', 0),
            last_payment_date=last_payment.get('date', 'N/A'),
            next_due_date=tenant_data.get('next_due_date', 'N/A')
        )
        
        quick_replies = ['Make payment', 'Payment history', 'Late fees'] if current_balance > 0 else ['Payment history', 'Auto-pay setup']
        
        return GeneratedResponse(
            text=response_text,
            response_type='quick_reply',
            quick_replies=quick_replies
        )
    
    def _handle_emergency(self, context: ResponseContext) -> GeneratedResponse:
        """Handle emergency situations"""
        emergency_type = context.entities.get('emergency_type', 'general')
        
        template = self.jinja_env.get_template('emergency_response')
        response_text = template.render(
            user_name=context.user_context.get('user_name', 'there'),
            emergency_type=emergency_type,
            emergency_number='911' if emergency_type in ['fire', 'medical'] else '(555) 123-HELP'
        )
        
        return GeneratedResponse(
            text=response_text,
            response_type='text',
            escalate=True,
            requires_action=True
        )
    
    def _handle_complaint(self, context: ResponseContext) -> GeneratedResponse:
        """Handle complaints"""
        template = self.jinja_env.get_template('complaint_response')
        response_text = template.render(
            user_name=context.user_context.get('user_name', 'there'),
            office_phone=context.property_data.get('office_phone', '(555) 123-4567') if context.property_data else '(555) 123-4567'
        )
        
        return GeneratedResponse(
            text=response_text,
            response_type='quick_reply',
            quick_replies=['File formal complaint', 'Speak to manager', 'Submit feedback'],
            escalate=True
        )
    
    def _handle_general_inquiry(self, context: ResponseContext) -> GeneratedResponse:
        """Handle general inquiries and greetings"""
        query_text = context.user_context.get('original_text', '').lower()
        
        # Check for greetings
        if any(greeting in query_text for greeting in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            response_text = random.choice(self.variations['greeting'])
            
            return GeneratedResponse(
                text=response_text,
                response_type='quick_reply',
                quick_replies=['Pay rent', 'Maintenance request', 'Account info', 'Contact office']
            )
        
        # Generic helpful response
        template = self.jinja_env.get_template('general_help')
        response_text = template.render(
            user_name=context.user_context.get('user_name', 'there')
        )
        
        return GeneratedResponse(
            text=response_text,
            response_type='quick_reply',
            quick_replies=['Pay rent', 'Maintenance', 'Lease info', 'Amenities', 'Contact']
        )
    
    def _load_response_templates(self) -> Dict[str, str]:
        """Load response templates"""
        return {
            'rent_payment_methods': """
Hi {{ user_name }}! You can pay your rent using any of these convenient methods:

{% for method in payment_methods %}
• {{ method }}
{% endfor %}

The easiest way is through our online portal where you can pay securely 24/7. Would you like me to help you with anything specific?
            """.strip(),
            
            'rent_due_date': """
Hi {{ user_name }}! Your rent is due on {{ due_date }}. 
{% if current_balance > 0 %}
Your current balance is ${{ current_balance }}.
{% else %}
Your account is current with no outstanding balance.
{% endif %}
            """.strip(),
            
            'rent_payment_general': """
Hi {{ user_name }}! I can help you with rent payments. 
{% if current_balance > 0 %}
Your current balance is ${{ current_balance }}.
{% endif %}
What would you like to do?
            """.strip(),
            
            'maintenance_emergency': """
🚨 This sounds like an emergency! For immediate assistance, please call our emergency line at {{ emergency_number }} right away.

If this is a life-threatening situation, please call 911 immediately.

I'm also escalating this to our maintenance team for urgent follow-up.
            """.strip(),
            
            'maintenance_request': """
Hi {{ user_name }}! I can help you with your {{ maintenance_type }} maintenance request for {{ unit_number }}.

To submit a request, I'll need a few details about the issue. Would you like to:
            """.strip(),
            
            'lease_renewal': """
Hi {{ user_name }}! Your lease ends on {{ lease_end_date }}.

{% if can_renew %}
Great news! You're eligible for lease renewal. I can help you explore your options.
{% else %}
Please contact our leasing office to discuss your situation.
{% endif %}
            """.strip(),
            
            'lease_documents': """
Hi {{ user_name }}! I can help you access your lease documents. You can download a copy from the tenant portal or I can email it to you.
            """.strip(),
            
            'lease_general': """
Hi {{ user_name }}! Here's your lease information:
• Lease Start: {{ lease_start }}
• Lease End: {{ lease_end }}
• Monthly Rent: ${{ rent_amount }}

What else would you like to know about your lease?
            """.strip(),
            
            'specific_amenity': """
Hi {{ user_name }}! 
{% if available %}
Yes, we have {{ amenity }} available! 
Hours: {{ hours }}
{% else %}
I'm sorry, but {{ amenity }} is not available at this property.
{% endif %}
            """.strip(),
            
            'amenities_general': """
Hi {{ user_name }}! Here are our available amenities:

{% for amenity in amenities %}
• {{ amenity }}
{% endfor %}
{% if total_count > 5 %}
...and {{ total_count - 5 }} more!
{% endif %}
            """.strip(),
            
            'contact_info': """
Hi {{ user_name }}! Here's our contact information:

📍 Office: {{ address }}
📞 Phone: {{ office_phone }}
📧 Email: {{ email }}
🕒 Hours: {{ office_hours }}

🚨 Emergency: {{ emergency_phone }}
            """.strip(),
            
            'account_balance': """
Hi {{ user_name }}! Here's your account summary:

Current Balance: ${{ current_balance }}
{% if last_payment_amount > 0 %}
Last Payment: ${{ last_payment_amount }} on {{ last_payment_date }}
{% endif %}
{% if next_due_date != 'N/A' %}
Next Due Date: {{ next_due_date }}
{% endif %}
            """.strip(),
            
            'emergency_response': """
🚨 I understand this is an emergency situation involving {{ emergency_type }}.

Please call {{ emergency_number }} immediately for assistance.

I'm escalating this to our management team for immediate attention.
            """.strip(),
            
            'complaint_response': """
Hi {{ user_name }}, I'm sorry to hear about your concern. Your feedback is important to us.

For the best resolution, I recommend speaking directly with our management team at {{ office_phone }}.

I'm also escalating this issue to ensure it gets proper attention.
            """.strip(),
            
            'general_help': """
Hi {{ user_name }}! I'm here to help you with:

• Rent payments and account information
• Maintenance requests
• Lease information and renewals  
• Property amenities and facilities
• Contact information and office hours

What can I assist you with today?
            """.strip()
        }
    
    def add_personality(self, response_text: str, sentiment: Optional[str] = None) -> str:
        """Add personality touches to response"""
        # Add appropriate emoji based on context
        if sentiment == 'positive':
            response_text += " 😊"
        elif 'emergency' in response_text.lower():
            response_text = "🚨 " + response_text
        elif 'thank' in response_text.lower():
            response_text += " 🙏"
        
        return response_text
    
    def generate_follow_up_questions(self, intent: str) -> List[str]:
        """Generate follow-up questions based on intent"""
        follow_ups = {
            'rent_payment': [
                "Would you like to set up automatic payments?",
                "Do you need help accessing the payment portal?",
                "Would you like to see your payment history?"
            ],
            'maintenance_request': [
                "Can you describe the issue in more detail?",
                "Is this affecting your daily activities?",
                "Would you like to schedule a convenient time for the repair?"
            ],
            'lease_inquiry': [
                "Are you interested in renewal options?",
                "Do you have questions about lease terms?",
                "Would you like to schedule a meeting with leasing?"
            ]
        }
        
        return follow_ups.get(intent, [
            "Is there anything else I can help you with?",
            "Do you have any other questions?",
            "Would you like assistance with anything else?"
        ])
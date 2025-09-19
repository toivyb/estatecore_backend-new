"""
SMS Service for EstateCore
Handles SMS notifications using Twilio for alerts, reminders, and urgent communications
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SMSConfig:
    """SMS configuration settings"""
    account_sid: str
    auth_token: str
    from_number: str
    webhook_url: str = None
    
    def __post_init__(self):
        if not self.from_number.startswith('+'):
            self.from_number = f'+{self.from_number}'

class SMSService:
    def __init__(self, config: SMSConfig = None):
        """Initialize SMS service with configuration"""
        self.config = config or self._get_default_config()
        self.client = None
        self._initialize_client()
        
    def _get_default_config(self) -> SMSConfig:
        """Get SMS configuration from environment variables"""
        return SMSConfig(
            account_sid=os.getenv('TWILIO_ACCOUNT_SID', ''),
            auth_token=os.getenv('TWILIO_AUTH_TOKEN', ''),
            from_number=os.getenv('TWILIO_FROM_NUMBER', ''),
            webhook_url=os.getenv('TWILIO_WEBHOOK_URL', '')
        )
    
    def _initialize_client(self):
        """Initialize Twilio client"""
        try:
            if self.config.account_sid and self.config.auth_token:
                from twilio.rest import Client
                self.client = Client(self.config.account_sid, self.config.auth_token)
                logger.info("Twilio client initialized successfully")
            else:
                logger.warning("Twilio credentials not provided - SMS service will use mock mode")
        except ImportError:
            logger.error("Twilio library not installed - SMS service will use mock mode")
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
    
    def _format_phone_number(self, phone_number: str) -> str:
        """Format phone number to E.164 format"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone_number)
        
        # Add country code if not present
        if len(digits) == 10:
            digits = '1' + digits  # US number
        elif len(digits) == 11 and digits.startswith('1'):
            pass  # Already has US country code
        
        return f'+{digits}'
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        formatted = self._format_phone_number(phone_number)
        return len(formatted) >= 11 and formatted.startswith('+')
    
    def send_sms(self, 
                 to_number: str, 
                 message: str,
                 media_urls: List[str] = None) -> Dict:
        """Send SMS message"""
        try:
            # Validate phone number
            if not self._validate_phone_number(to_number):
                return {
                    'success': False,
                    'error': 'Invalid phone number format'
                }
            
            formatted_number = self._format_phone_number(to_number)
            
            # Truncate message if too long
            if len(message) > 1600:
                message = message[:1597] + "..."
            
            if self.client:
                # Send real SMS via Twilio
                message_params = {
                    'body': message,
                    'from_': self.config.from_number,
                    'to': formatted_number
                }
                
                if media_urls:
                    message_params['media_url'] = media_urls
                
                twilio_message = self.client.messages.create(**message_params)
                
                logger.info(f"SMS sent successfully to {formatted_number}")
                return {
                    'success': True,
                    'message_sid': twilio_message.sid,
                    'status': twilio_message.status,
                    'to': formatted_number,
                    'from': self.config.from_number,
                    'body': message,
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                # Mock SMS sending
                logger.info(f"Mock SMS sent to {formatted_number}: {message[:50]}...")
                return {
                    'success': True,
                    'message_sid': f'mock_msg_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
                    'status': 'sent',
                    'to': formatted_number,
                    'from': self.config.from_number,
                    'body': message,
                    'timestamp': datetime.utcnow().isoformat(),
                    'mock': True
                }
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_bulk_sms(self, 
                      recipients: List[Dict[str, str]], 
                      message_template: str,
                      personalization_data: List[Dict] = None) -> Dict:
        """Send bulk SMS messages with personalization"""
        results = []
        success_count = 0
        
        personalization_data = personalization_data or [{}] * len(recipients)
        
        for i, recipient in enumerate(recipients):
            phone = recipient.get('phone', '')
            name = recipient.get('name', 'User')
            
            # Personalize message
            personalized_message = message_template
            personalization = personalization_data[i] if i < len(personalization_data) else {}
            
            # Replace common placeholders
            personalized_message = personalized_message.replace('{name}', name)
            personalized_message = personalized_message.replace('{phone}', phone)
            
            # Replace custom placeholders
            for key, value in personalization.items():
                personalized_message = personalized_message.replace(f'{{{key}}}', str(value))
            
            # Send SMS
            result = self.send_sms(phone, personalized_message)
            result['recipient'] = recipient
            results.append(result)
            
            if result['success']:
                success_count += 1
        
        return {
            'total_sent': len(recipients),
            'successful': success_count,
            'failed': len(recipients) - success_count,
            'results': results
        }
    
    def send_emergency_alert(self, 
                           emergency_contacts: List[str], 
                           alert_message: str,
                           property_name: str = None) -> Dict:
        """Send emergency alert to multiple contacts"""
        emergency_prefix = "🚨 EMERGENCY ALERT 🚨\n\n"
        
        if property_name:
            emergency_prefix += f"Property: {property_name}\n\n"
        
        full_message = emergency_prefix + alert_message
        
        results = []
        for contact in emergency_contacts:
            result = self.send_sms(contact, full_message)
            results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        
        return {
            'alert_type': 'emergency',
            'contacts_notified': len(emergency_contacts),
            'successful_notifications': success_count,
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        }
    
    def send_maintenance_alert(self, 
                             phone_number: str, 
                             tenant_name: str,
                             property_name: str,
                             unit_number: str,
                             maintenance_type: str,
                             urgency: str = 'normal') -> Dict:
        """Send maintenance-related SMS alert"""
        urgency_prefixes = {
            'low': '',
            'normal': '📋 ',
            'high': '⚠️ URGENT: ',
            'emergency': '🚨 EMERGENCY: '
        }
        
        prefix = urgency_prefixes.get(urgency.lower(), '')
        
        message = f"""{prefix}Maintenance {maintenance_type}

Hi {tenant_name},

Your maintenance request for {property_name} - Unit {unit_number} has been {maintenance_type.lower()}.

Please check your tenant portal for details or call our maintenance hotline.

- EstateCore Property Management"""
        
        return self.send_sms(phone_number, message)
    
    def send_rent_reminder(self, 
                          phone_number: str, 
                          tenant_name: str,
                          amount_due: float,
                          due_date: str,
                          property_name: str,
                          unit_number: str) -> Dict:
        """Send rent payment reminder"""
        message = f"""💰 Rent Reminder

Hi {tenant_name},

Your rent payment of ${amount_due:.2f} for {property_name} - Unit {unit_number} is due on {due_date}.

Pay online at your tenant portal or contact our office.

Thank you!
- EstateCore Management"""
        
        return self.send_sms(phone_number, message)
    
    def send_lease_expiration_reminder(self, 
                                     phone_number: str, 
                                     tenant_name: str,
                                     property_name: str,
                                     unit_number: str,
                                     days_until_expiry: int,
                                     lease_end_date: str) -> Dict:
        """Send lease expiration reminder"""
        message = f"""📄 Lease Expiration Notice

Hi {tenant_name},

Your lease for {property_name} - Unit {unit_number} expires in {days_until_expiry} days on {lease_end_date}.

Please contact us to discuss renewal or move-out procedures.

- EstateCore Management"""
        
        return self.send_sms(phone_number, message)
    
    def send_security_alert(self, 
                          security_contacts: List[str], 
                          alert_type: str,
                          location: str,
                          description: str,
                          timestamp: str = None) -> Dict:
        """Send security alert to designated contacts"""
        timestamp = timestamp or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"""🛡️ SECURITY ALERT

Type: {alert_type}
Location: {location}
Time: {timestamp}

Details: {description}

Immediate attention required.

- EstateCore Security System"""
        
        results = []
        for contact in security_contacts:
            result = self.send_sms(contact, message)
            results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        
        return {
            'alert_type': 'security',
            'contacts_notified': len(security_contacts),
            'successful_notifications': success_count,
            'timestamp': datetime.utcnow().isoformat(),
            'results': results
        }
    
    def send_payment_confirmation(self, 
                                phone_number: str, 
                                tenant_name: str,
                                amount: float,
                                transaction_id: str,
                                property_name: str,
                                unit_number: str) -> Dict:
        """Send payment confirmation SMS"""
        message = f"""✅ Payment Confirmed

Hi {tenant_name},

Your payment of ${amount:.2f} for {property_name} - Unit {unit_number} has been processed successfully.

Transaction ID: {transaction_id}

Thank you for your payment!
- EstateCore Management"""
        
        return self.send_sms(phone_number, message)
    
    def send_custom_notification(self, 
                               phone_numbers: List[str], 
                               message: str,
                               sender_name: str = "EstateCore") -> Dict:
        """Send custom notification to multiple recipients"""
        formatted_message = f"{message}\n\n- {sender_name}"
        
        results = []
        for phone in phone_numbers:
            result = self.send_sms(phone, formatted_message)
            results.append(result)
        
        success_count = sum(1 for r in results if r['success'])
        
        return {
            'message_type': 'custom',
            'recipients': len(phone_numbers),
            'successful': success_count,
            'failed': len(phone_numbers) - success_count,
            'results': results
        }
    
    def get_message_status(self, message_sid: str) -> Dict:
        """Get status of sent message"""
        try:
            if self.client:
                message = self.client.messages(message_sid).fetch()
                return {
                    'sid': message.sid,
                    'status': message.status,
                    'to': message.to,
                    'from': message.from_,
                    'body': message.body,
                    'date_created': message.date_created.isoformat() if message.date_created else None,
                    'date_sent': message.date_sent.isoformat() if message.date_sent else None,
                    'error_code': message.error_code,
                    'error_message': message.error_message
                }
            else:
                return {
                    'sid': message_sid,
                    'status': 'delivered',
                    'mock': True
                }
        except Exception as e:
            logger.error(f"Failed to get message status: {e}")
            return {
                'error': str(e)
            }
    
    def test_configuration(self) -> bool:
        """Test SMS configuration"""
        try:
            test_message = f"EstateCore SMS test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Send test message to the from number (self-test)
            result = self.send_sms(self.config.from_number, test_message)
            return result['success']
            
        except Exception as e:
            logger.error(f"SMS configuration test failed: {e}")
            return False

# Utility functions
def create_sms_service() -> SMSService:
    """Create SMS service with default configuration"""
    return SMSService()

def send_test_sms(phone_number: str) -> bool:
    """Send a test SMS to verify configuration"""
    service = create_sms_service()
    result = service.send_sms(
        phone_number, 
        f"EstateCore SMS test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    return result['success']

# Emergency notification shortcuts
def send_fire_alert(emergency_contacts: List[str], property_name: str, location: str) -> Dict:
    """Send fire emergency alert"""
    service = create_sms_service()
    return service.send_emergency_alert(
        emergency_contacts,
        f"FIRE DETECTED at {location}. Evacuate immediately and call 911.",
        property_name
    )

def send_security_breach_alert(security_contacts: List[str], property_name: str, details: str) -> Dict:
    """Send security breach alert"""
    service = create_sms_service()
    return service.send_security_alert(
        security_contacts,
        "Unauthorized Access",
        property_name,
        details
    )

if __name__ == "__main__":
    # Test the SMS service
    service = create_sms_service()
    
    # Test configuration
    if service.test_configuration():
        print("✅ SMS configuration is working!")
    else:
        print("❌ SMS configuration failed!")
    
    # Example usage
    # result = service.send_rent_reminder(
    #     phone_number="+1234567890",
    #     tenant_name="John Doe",
    #     amount_due=1500.00,
    #     due_date="April 1st",
    #     property_name="Sunset Apartments",
    #     unit_number="305"
    # )
    # print(f"SMS Result: {result}")
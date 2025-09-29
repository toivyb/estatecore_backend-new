#!/usr/bin/env python3
"""
Multi-Factor Authentication (MFA) Manager for EstateCore Phase 8D
Comprehensive MFA system supporting TOTP, SMS, Email, Hardware tokens, and Backup codes
"""

import os
import json
import hashlib
import hmac
import secrets
import asyncio
import logging
import qrcode
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import uuid
import pyotp
import aiosmtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import aiohttp
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MFAMethod(Enum):
    TOTP = "totp"  # Time-based One-Time Password (Google Authenticator, Authy)
    SMS = "sms"    # SMS Text Message
    EMAIL = "email"  # Email OTP
    HARDWARE = "hardware"  # Hardware security keys (FIDO2/WebAuthn)
    BACKUP_CODES = "backup_codes"  # One-time backup codes
    PUSH = "push"  # Push notification
    VOICE = "voice"  # Voice call

class MFAStatus(Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    PENDING_SETUP = "pending_setup"
    SUSPENDED = "suspended"

class TokenStatus(Enum):
    VALID = "valid"
    EXPIRED = "expired"
    USED = "used"
    INVALID = "invalid"

@dataclass
class MFAConfig:
    """MFA configuration for a user"""
    user_id: str
    method: MFAMethod
    status: MFAStatus
    secret: Optional[str]  # Encrypted secret for TOTP
    phone_number: Optional[str]  # For SMS/Voice
    email: Optional[str]  # For Email OTP
    backup_codes: List[str]  # Encrypted backup codes
    device_name: Optional[str]  # User-friendly device name
    created_at: datetime
    last_used: Optional[datetime]
    failure_count: int
    metadata: Dict[str, Any]

@dataclass
class MFAToken:
    """MFA token for verification"""
    token_id: str
    user_id: str
    method: MFAMethod
    token_value: str  # Encrypted token
    expires_at: datetime
    status: TokenStatus
    attempts: int
    max_attempts: int
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class MFAVerificationResult:
    """Result of MFA verification"""
    success: bool
    method: MFAMethod
    token_id: Optional[str]
    error_message: Optional[str]
    remaining_attempts: int
    next_allowed_attempt: Optional[datetime]
    backup_codes_remaining: int
    metadata: Dict[str, Any]

class MFAManager:
    """Multi-Factor Authentication Manager"""
    
    def __init__(self, database_path: str = "mfa_database.db"):
        self.database_path = database_path
        self.encryption_key = self._load_or_generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # MFA settings
        self.totp_issuer = "EstateCore"
        self.token_validity_minutes = 5
        self.max_attempts_per_token = 3
        self.lockout_duration_minutes = 15
        self.backup_codes_count = 10
        
        # Rate limiting
        self.rate_limits = {
            MFAMethod.SMS: {"max_per_hour": 10, "cooldown_minutes": 1},
            MFAMethod.EMAIL: {"max_per_hour": 20, "cooldown_minutes": 1},
            MFAMethod.VOICE: {"max_per_hour": 5, "cooldown_minutes": 2},
            MFAMethod.PUSH: {"max_per_hour": 30, "cooldown_minutes": 0.5}
        }
        
        # Initialize database
        self._initialize_database()
        
        logger.info("MFA Manager initialized")
    
    def _load_or_generate_key(self) -> bytes:
        """Load or generate encryption key"""
        key_file = "mfa_encryption.key"
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            return key
    
    def _initialize_database(self):
        """Initialize MFA database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # MFA configurations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mfa_configs (
                user_id TEXT NOT NULL,
                method TEXT NOT NULL,
                status TEXT NOT NULL,
                secret TEXT,
                phone_number TEXT,
                email TEXT,
                backup_codes TEXT,
                device_name TEXT,
                created_at TEXT NOT NULL,
                last_used TEXT,
                failure_count INTEGER DEFAULT 0,
                metadata TEXT,
                PRIMARY KEY (user_id, method)
            )
        """)
        
        # MFA tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mfa_tokens (
                token_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                method TEXT NOT NULL,
                token_value TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                created_at TEXT NOT NULL,
                metadata TEXT
            )
        """)
        
        # Rate limiting table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mfa_rate_limits (
                user_id TEXT NOT NULL,
                method TEXT NOT NULL,
                window_start TEXT NOT NULL,
                attempt_count INTEGER DEFAULT 1,
                last_attempt TEXT NOT NULL,
                PRIMARY KEY (user_id, method, window_start)
            )
        """)
        
        # Backup codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mfa_backup_codes (
                code_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                used BOOLEAN DEFAULT 0,
                used_at TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Hardware tokens table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mfa_hardware_tokens (
                token_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                public_key TEXT NOT NULL,
                credential_id TEXT NOT NULL,
                device_name TEXT,
                registered_at TEXT NOT NULL,
                last_used TEXT,
                usage_count INTEGER DEFAULT 0
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mfa_configs_user ON mfa_configs (user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mfa_tokens_user_method ON mfa_tokens (user_id, method)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mfa_tokens_expires ON mfa_tokens (expires_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_backup_codes_user ON mfa_backup_codes (user_id)")
        
        conn.commit()
        conn.close()
    
    async def setup_totp(self, user_id: str, device_name: str = "Authenticator App") -> Dict[str, Any]:
        """Set up TOTP authentication for user"""
        try:
            # Generate secret
            secret = pyotp.random_base32()
            
            # Create TOTP URI for QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user_id,
                issuer_name=self.totp_issuer
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            qr_buffer = io.BytesIO()
            qr_image.save(qr_buffer, format='PNG')
            qr_code_b64 = base64.b64encode(qr_buffer.getvalue()).decode()
            
            # Encrypt and store secret
            encrypted_secret = self.cipher_suite.encrypt(secret.encode()).decode()
            
            config = MFAConfig(
                user_id=user_id,
                method=MFAMethod.TOTP,
                status=MFAStatus.PENDING_SETUP,
                secret=encrypted_secret,
                phone_number=None,
                email=None,
                backup_codes=[],
                device_name=device_name,
                created_at=datetime.now(),
                last_used=None,
                failure_count=0,
                metadata={"setup_initiated": datetime.now().isoformat()}
            )
            
            await self._save_mfa_config(config)
            
            return {
                "secret": secret,  # Return plain secret for setup
                "qr_code": qr_code_b64,
                "uri": totp_uri,
                "backup_codes": await self._generate_backup_codes(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error setting up TOTP for {user_id}: {e}")
            raise
    
    async def verify_totp_setup(self, user_id: str, token: str) -> bool:
        """Verify TOTP setup with initial token"""
        try:
            config = await self._get_mfa_config(user_id, MFAMethod.TOTP)
            if not config or config.status != MFAStatus.PENDING_SETUP:
                return False
            
            # Decrypt secret
            secret = self.cipher_suite.decrypt(config.secret.encode()).decode()
            totp = pyotp.TOTP(secret)
            
            # Verify token with window for clock skew
            if totp.verify(token, valid_window=1):
                # Enable TOTP
                config.status = MFAStatus.ENABLED
                config.metadata["setup_completed"] = datetime.now().isoformat()
                await self._save_mfa_config(config)
                
                logger.info(f"TOTP setup completed for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying TOTP setup for {user_id}: {e}")
            return False
    
    async def setup_sms(self, user_id: str, phone_number: str) -> bool:
        """Set up SMS authentication for user"""
        try:
            # Validate phone number format (basic validation)
            if not phone_number.startswith('+'):
                phone_number = '+1' + phone_number.replace('-', '').replace(' ', '')
            
            config = MFAConfig(
                user_id=user_id,
                method=MFAMethod.SMS,
                status=MFAStatus.PENDING_SETUP,
                secret=None,
                phone_number=phone_number,
                email=None,
                backup_codes=[],
                device_name="SMS Phone",
                created_at=datetime.now(),
                last_used=None,
                failure_count=0,
                metadata={"phone_validated": False}
            )
            
            await self._save_mfa_config(config)
            
            # Send verification SMS
            verification_token = await self._generate_sms_token(user_id)
            success = await self._send_sms(phone_number, f"EstateCore verification code: {verification_token}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting up SMS for {user_id}: {e}")
            return False
    
    async def setup_email(self, user_id: str, email: str) -> bool:
        """Set up email authentication for user"""
        try:
            config = MFAConfig(
                user_id=user_id,
                method=MFAMethod.EMAIL,
                status=MFAStatus.PENDING_SETUP,
                secret=None,
                phone_number=None,
                email=email,
                backup_codes=[],
                device_name="Email",
                created_at=datetime.now(),
                last_used=None,
                failure_count=0,
                metadata={"email_validated": False}
            )
            
            await self._save_mfa_config(config)
            
            # Send verification email
            verification_token = await self._generate_email_token(user_id)
            success = await self._send_email(email, "EstateCore MFA Setup", 
                f"Your verification code is: {verification_token}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error setting up email MFA for {user_id}: {e}")
            return False
    
    async def verify_mfa_token(self, user_id: str, method: MFAMethod, token: str, 
                             token_id: Optional[str] = None) -> MFAVerificationResult:
        """Verify MFA token"""
        try:
            if method == MFAMethod.TOTP:
                return await self._verify_totp_token(user_id, token)
            elif method == MFAMethod.SMS:
                return await self._verify_sms_token(user_id, token, token_id)
            elif method == MFAMethod.EMAIL:
                return await self._verify_email_token(user_id, token, token_id)
            elif method == MFAMethod.BACKUP_CODES:
                return await self._verify_backup_code(user_id, token)
            else:
                return MFAVerificationResult(
                    success=False,
                    method=method,
                    token_id=token_id,
                    error_message="Unsupported MFA method",
                    remaining_attempts=0,
                    next_allowed_attempt=None,
                    backup_codes_remaining=0,
                    metadata={}
                )
                
        except Exception as e:
            logger.error(f"Error verifying MFA token for {user_id}: {e}")
            return MFAVerificationResult(
                success=False,
                method=method,
                token_id=token_id,
                error_message=str(e),
                remaining_attempts=0,
                next_allowed_attempt=None,
                backup_codes_remaining=0,
                metadata={}
            )
    
    async def _verify_totp_token(self, user_id: str, token: str) -> MFAVerificationResult:
        """Verify TOTP token"""
        config = await self._get_mfa_config(user_id, MFAMethod.TOTP)
        
        if not config or config.status != MFAStatus.ENABLED:
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.TOTP,
                token_id=None,
                error_message="TOTP not configured",
                remaining_attempts=0,
                next_allowed_attempt=None,
                backup_codes_remaining=await self._count_backup_codes(user_id),
                metadata={}
            )
        
        # Check rate limiting
        if not await self._check_rate_limit(user_id, MFAMethod.TOTP):
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.TOTP,
                token_id=None,
                error_message="Rate limit exceeded",
                remaining_attempts=0,
                next_allowed_attempt=datetime.now() + timedelta(minutes=self.lockout_duration_minutes),
                backup_codes_remaining=await self._count_backup_codes(user_id),
                metadata={}
            )
        
        # Decrypt secret and verify
        secret = self.cipher_suite.decrypt(config.secret.encode()).decode()
        totp = pyotp.TOTP(secret)
        
        if totp.verify(token, valid_window=1):
            # Success - update usage
            config.last_used = datetime.now()
            config.failure_count = 0
            await self._save_mfa_config(config)
            
            return MFAVerificationResult(
                success=True,
                method=MFAMethod.TOTP,
                token_id=None,
                error_message=None,
                remaining_attempts=0,
                next_allowed_attempt=None,
                backup_codes_remaining=await self._count_backup_codes(user_id),
                metadata={"verified_at": datetime.now().isoformat()}
            )
        else:
            # Failure - increment counter
            config.failure_count += 1
            await self._save_mfa_config(config)
            await self._record_rate_limit_attempt(user_id, MFAMethod.TOTP)
            
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.TOTP,
                token_id=None,
                error_message="Invalid token",
                remaining_attempts=max(0, self.max_attempts_per_token - config.failure_count),
                next_allowed_attempt=None,
                backup_codes_remaining=await self._count_backup_codes(user_id),
                metadata={}
            )
    
    async def _generate_backup_codes(self, user_id: str) -> List[str]:
        """Generate backup codes for user"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            backup_codes = []
            
            for _ in range(self.backup_codes_count):
                # Generate 8-character alphanumeric code
                code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
                code_hash = hashlib.sha256(code.encode()).hexdigest()
                
                # Store encrypted hash
                cursor.execute("""
                    INSERT INTO mfa_backup_codes (code_id, user_id, code_hash, created_at)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), user_id, code_hash, datetime.now().isoformat()))
                
                backup_codes.append(code)
            
            conn.commit()
            conn.close()
            
            return backup_codes
            
        except Exception as e:
            logger.error(f"Error generating backup codes for {user_id}: {e}")
            return []
    
    async def _send_sms(self, phone_number: str, message: str) -> bool:
        """Send SMS message (integrate with SMS provider)"""
        try:
            # TODO: Integrate with SMS provider (Twilio, AWS SNS, etc.)
            logger.info(f"SMS would be sent to {phone_number}: {message}")
            
            # Simulate SMS sending
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS to {phone_number}: {e}")
            return False
    
    async def _send_email(self, email: str, subject: str, body: str) -> bool:
        """Send email message"""
        try:
            # TODO: Configure SMTP settings
            smtp_host = os.getenv('SMTP_HOST', 'localhost')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', '')
            smtp_pass = os.getenv('SMTP_PASS', '')
            
            msg = MimeMultipart()
            msg['From'] = smtp_user
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MimeText(body, 'plain'))
            
            # Simulate email sending for now
            logger.info(f"Email would be sent to {email}: {subject}")
            await asyncio.sleep(0.1)
            return True
            
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")
            return False
    
    async def _generate_sms_token(self, user_id: str) -> str:
        """Generate SMS token"""
        token = ''.join(secrets.choice('0123456789') for _ in range(6))
        
        # Store token
        token_data = MFAToken(
            token_id=str(uuid.uuid4()),
            user_id=user_id,
            method=MFAMethod.SMS,
            token_value=self.cipher_suite.encrypt(token.encode()).decode(),
            expires_at=datetime.now() + timedelta(minutes=self.token_validity_minutes),
            status=TokenStatus.VALID,
            attempts=0,
            max_attempts=self.max_attempts_per_token,
            created_at=datetime.now(),
            metadata={}
        )
        
        await self._save_mfa_token(token_data)
        return token
    
    async def _generate_email_token(self, user_id: str) -> str:
        """Generate email token"""
        token = ''.join(secrets.choice('0123456789') for _ in range(6))
        
        # Store token
        token_data = MFAToken(
            token_id=str(uuid.uuid4()),
            user_id=user_id,
            method=MFAMethod.EMAIL,
            token_value=self.cipher_suite.encrypt(token.encode()).decode(),
            expires_at=datetime.now() + timedelta(minutes=self.token_validity_minutes),
            status=TokenStatus.VALID,
            attempts=0,
            max_attempts=self.max_attempts_per_token,
            created_at=datetime.now(),
            metadata={}
        )
        
        await self._save_mfa_token(token_data)
        return token
    
    async def _verify_sms_token(self, user_id: str, token: str, token_id: Optional[str]) -> MFAVerificationResult:
        """Verify SMS token"""
        return await self._verify_otp_token(user_id, MFAMethod.SMS, token, token_id)
    
    async def _verify_email_token(self, user_id: str, token: str, token_id: Optional[str]) -> MFAVerificationResult:
        """Verify email token"""
        return await self._verify_otp_token(user_id, MFAMethod.EMAIL, token, token_id)
    
    async def _verify_otp_token(self, user_id: str, method: MFAMethod, token: str, 
                               token_id: Optional[str]) -> MFAVerificationResult:
        """Verify OTP token (SMS/Email)"""
        try:
            # Get the most recent valid token if token_id not provided
            if not token_id:
                token_data = await self._get_latest_token(user_id, method)
            else:
                token_data = await self._get_mfa_token(token_id)
            
            if not token_data or token_data.status != TokenStatus.VALID:
                return MFAVerificationResult(
                    success=False,
                    method=method,
                    token_id=token_id,
                    error_message="Token not found or invalid",
                    remaining_attempts=0,
                    next_allowed_attempt=None,
                    backup_codes_remaining=await self._count_backup_codes(user_id),
                    metadata={}
                )
            
            # Check expiration
            if datetime.now() > token_data.expires_at:
                token_data.status = TokenStatus.EXPIRED
                await self._save_mfa_token(token_data)
                
                return MFAVerificationResult(
                    success=False,
                    method=method,
                    token_id=token_data.token_id,
                    error_message="Token expired",
                    remaining_attempts=0,
                    next_allowed_attempt=None,
                    backup_codes_remaining=await self._count_backup_codes(user_id),
                    metadata={}
                )
            
            # Check attempts
            if token_data.attempts >= token_data.max_attempts:
                token_data.status = TokenStatus.INVALID
                await self._save_mfa_token(token_data)
                
                return MFAVerificationResult(
                    success=False,
                    method=method,
                    token_id=token_data.token_id,
                    error_message="Maximum attempts exceeded",
                    remaining_attempts=0,
                    next_allowed_attempt=None,
                    backup_codes_remaining=await self._count_backup_codes(user_id),
                    metadata={}
                )
            
            # Verify token
            stored_token = self.cipher_suite.decrypt(token_data.token_value.encode()).decode()
            
            if token == stored_token:
                # Success
                token_data.status = TokenStatus.USED
                await self._save_mfa_token(token_data)
                
                # Update config
                config = await self._get_mfa_config(user_id, method)
                if config:
                    config.last_used = datetime.now()
                    config.failure_count = 0
                    await self._save_mfa_config(config)
                
                return MFAVerificationResult(
                    success=True,
                    method=method,
                    token_id=token_data.token_id,
                    error_message=None,
                    remaining_attempts=0,
                    next_allowed_attempt=None,
                    backup_codes_remaining=await self._count_backup_codes(user_id),
                    metadata={"verified_at": datetime.now().isoformat()}
                )
            else:
                # Failure
                token_data.attempts += 1
                await self._save_mfa_token(token_data)
                
                return MFAVerificationResult(
                    success=False,
                    method=method,
                    token_id=token_data.token_id,
                    error_message="Invalid token",
                    remaining_attempts=token_data.max_attempts - token_data.attempts,
                    next_allowed_attempt=None,
                    backup_codes_remaining=await self._count_backup_codes(user_id),
                    metadata={}
                )
                
        except Exception as e:
            logger.error(f"Error verifying OTP token: {e}")
            return MFAVerificationResult(
                success=False,
                method=method,
                token_id=token_id,
                error_message=str(e),
                remaining_attempts=0,
                next_allowed_attempt=None,
                backup_codes_remaining=0,
                metadata={}
            )
    
    async def _verify_backup_code(self, user_id: str, code: str) -> MFAVerificationResult:
        """Verify backup code"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            code_hash = hashlib.sha256(code.encode()).hexdigest()
            
            # Find matching unused backup code
            cursor.execute("""
                SELECT code_id FROM mfa_backup_codes 
                WHERE user_id = ? AND code_hash = ? AND used = 0
            """, (user_id, code_hash))
            
            result = cursor.fetchone()
            
            if result:
                # Mark code as used
                cursor.execute("""
                    UPDATE mfa_backup_codes 
                    SET used = 1, used_at = ? 
                    WHERE code_id = ?
                """, (datetime.now().isoformat(), result[0]))
                
                conn.commit()
                
                # Count remaining codes
                cursor.execute("""
                    SELECT COUNT(*) FROM mfa_backup_codes 
                    WHERE user_id = ? AND used = 0
                """, (user_id,))
                
                remaining = cursor.fetchone()[0]
                conn.close()
                
                return MFAVerificationResult(
                    success=True,
                    method=MFAMethod.BACKUP_CODES,
                    token_id=None,
                    error_message=None,
                    remaining_attempts=0,
                    next_allowed_attempt=None,
                    backup_codes_remaining=remaining,
                    metadata={"code_used": result[0], "remaining_codes": remaining}
                )
            else:
                conn.close()
                return MFAVerificationResult(
                    success=False,
                    method=MFAMethod.BACKUP_CODES,
                    token_id=None,
                    error_message="Invalid backup code",
                    remaining_attempts=0,
                    next_allowed_attempt=None,
                    backup_codes_remaining=await self._count_backup_codes(user_id),
                    metadata={}
                )
                
        except Exception as e:
            logger.error(f"Error verifying backup code: {e}")
            return MFAVerificationResult(
                success=False,
                method=MFAMethod.BACKUP_CODES,
                token_id=None,
                error_message=str(e),
                remaining_attempts=0,
                next_allowed_attempt=None,
                backup_codes_remaining=0,
                metadata={}
            )
    
    async def send_mfa_challenge(self, user_id: str, method: MFAMethod) -> Dict[str, Any]:
        """Send MFA challenge to user"""
        try:
            config = await self._get_mfa_config(user_id, method)
            if not config or config.status != MFAStatus.ENABLED:
                return {"success": False, "error": "MFA method not configured"}
            
            # Check rate limiting
            if not await self._check_rate_limit(user_id, method):
                return {"success": False, "error": "Rate limit exceeded"}
            
            if method == MFAMethod.SMS:
                token = await self._generate_sms_token(user_id)
                success = await self._send_sms(config.phone_number, 
                    f"EstateCore security code: {token}")
                
                if success:
                    await self._record_rate_limit_attempt(user_id, method)
                    return {"success": True, "message": "SMS sent"}
                else:
                    return {"success": False, "error": "Failed to send SMS"}
                    
            elif method == MFAMethod.EMAIL:
                token = await self._generate_email_token(user_id)
                success = await self._send_email(config.email, 
                    "EstateCore Security Code", 
                    f"Your security code is: {token}")
                
                if success:
                    await self._record_rate_limit_attempt(user_id, method)
                    return {"success": True, "message": "Email sent"}
                else:
                    return {"success": False, "error": "Failed to send email"}
                    
            else:
                return {"success": False, "error": "Unsupported challenge method"}
                
        except Exception as e:
            logger.error(f"Error sending MFA challenge: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_user_mfa_methods(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all MFA methods configured for user"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT method, status, device_name, last_used, created_at
                FROM mfa_configs WHERE user_id = ?
            """, (user_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            methods = []
            for row in results:
                methods.append({
                    "method": row[0],
                    "status": row[1],
                    "device_name": row[2],
                    "last_used": row[3],
                    "created_at": row[4]
                })
            
            # Add backup codes info
            backup_count = await self._count_backup_codes(user_id)
            if backup_count > 0:
                methods.append({
                    "method": "backup_codes",
                    "status": "enabled",
                    "device_name": f"{backup_count} codes available",
                    "last_used": None,
                    "created_at": None
                })
            
            return methods
            
        except Exception as e:
            logger.error(f"Error getting user MFA methods: {e}")
            return []
    
    async def disable_mfa_method(self, user_id: str, method: MFAMethod) -> bool:
        """Disable MFA method for user"""
        try:
            config = await self._get_mfa_config(user_id, method)
            if config:
                config.status = MFAStatus.DISABLED
                await self._save_mfa_config(config)
                
                # Invalidate any pending tokens
                await self._invalidate_user_tokens(user_id, method)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error disabling MFA method: {e}")
            return False
    
    # Database helper methods
    async def _save_mfa_config(self, config: MFAConfig):
        """Save MFA configuration"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO mfa_configs 
            (user_id, method, status, secret, phone_number, email, backup_codes, 
             device_name, created_at, last_used, failure_count, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.user_id, config.method.value, config.status.value,
            config.secret, config.phone_number, config.email,
            json.dumps(config.backup_codes), config.device_name,
            config.created_at.isoformat(),
            config.last_used.isoformat() if config.last_used else None,
            config.failure_count, json.dumps(config.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    async def _get_mfa_config(self, user_id: str, method: MFAMethod) -> Optional[MFAConfig]:
        """Get MFA configuration"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM mfa_configs 
            WHERE user_id = ? AND method = ?
        """, (user_id, method.value))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return MFAConfig(
                user_id=row[0],
                method=MFAMethod(row[1]),
                status=MFAStatus(row[2]),
                secret=row[3],
                phone_number=row[4],
                email=row[5],
                backup_codes=json.loads(row[6]) if row[6] else [],
                device_name=row[7],
                created_at=datetime.fromisoformat(row[8]),
                last_used=datetime.fromisoformat(row[9]) if row[9] else None,
                failure_count=row[10],
                metadata=json.loads(row[11]) if row[11] else {}
            )
        return None
    
    async def _save_mfa_token(self, token: MFAToken):
        """Save MFA token"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO mfa_tokens 
            (token_id, user_id, method, token_value, expires_at, status, 
             attempts, max_attempts, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            token.token_id, token.user_id, token.method.value,
            token.token_value, token.expires_at.isoformat(),
            token.status.value, token.attempts, token.max_attempts,
            token.created_at.isoformat(), json.dumps(token.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    async def _get_mfa_token(self, token_id: str) -> Optional[MFAToken]:
        """Get MFA token"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM mfa_tokens WHERE token_id = ?", (token_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return MFAToken(
                token_id=row[0],
                user_id=row[1],
                method=MFAMethod(row[2]),
                token_value=row[3],
                expires_at=datetime.fromisoformat(row[4]),
                status=TokenStatus(row[5]),
                attempts=row[6],
                max_attempts=row[7],
                created_at=datetime.fromisoformat(row[8]),
                metadata=json.loads(row[9]) if row[9] else {}
            )
        return None
    
    async def _get_latest_token(self, user_id: str, method: MFAMethod) -> Optional[MFAToken]:
        """Get latest token for user and method"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM mfa_tokens 
            WHERE user_id = ? AND method = ? AND status = 'valid'
            ORDER BY created_at DESC LIMIT 1
        """, (user_id, method.value))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return MFAToken(
                token_id=row[0],
                user_id=row[1],
                method=MFAMethod(row[2]),
                token_value=row[3],
                expires_at=datetime.fromisoformat(row[4]),
                status=TokenStatus(row[5]),
                attempts=row[6],
                max_attempts=row[7],
                created_at=datetime.fromisoformat(row[8]),
                metadata=json.loads(row[9]) if row[9] else {}
            )
        return None
    
    async def _count_backup_codes(self, user_id: str) -> int:
        """Count unused backup codes"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM mfa_backup_codes 
            WHERE user_id = ? AND used = 0
        """, (user_id,))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    async def _check_rate_limit(self, user_id: str, method: MFAMethod) -> bool:
        """Check if user is within rate limits"""
        if method not in self.rate_limits:
            return True
        
        limits = self.rate_limits[method]
        window_start = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT attempt_count, last_attempt FROM mfa_rate_limits
            WHERE user_id = ? AND method = ? AND window_start = ?
        """, (user_id, method.value, window_start.isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return True
        
        attempt_count, last_attempt = row
        last_attempt_time = datetime.fromisoformat(last_attempt)
        
        # Check cooldown
        cooldown_end = last_attempt_time + timedelta(minutes=limits["cooldown_minutes"])
        if datetime.now() < cooldown_end:
            return False
        
        # Check hourly limit
        return attempt_count < limits["max_per_hour"]
    
    async def _record_rate_limit_attempt(self, user_id: str, method: MFAMethod):
        """Record rate limit attempt"""
        if method not in self.rate_limits:
            return
        
        window_start = datetime.now().replace(minute=0, second=0, microsecond=0)
        now = datetime.now()
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO mfa_rate_limits 
            (user_id, method, window_start, attempt_count, last_attempt)
            VALUES (?, ?, ?, 
                COALESCE((SELECT attempt_count FROM mfa_rate_limits 
                         WHERE user_id = ? AND method = ? AND window_start = ?), 0) + 1, ?)
        """, (user_id, method.value, window_start.isoformat(),
              user_id, method.value, window_start.isoformat(), now.isoformat()))
        
        conn.commit()
        conn.close()
    
    async def _invalidate_user_tokens(self, user_id: str, method: MFAMethod):
        """Invalidate all tokens for user and method"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE mfa_tokens SET status = 'invalid'
            WHERE user_id = ? AND method = ? AND status = 'valid'
        """, (user_id, method.value))
        
        conn.commit()
        conn.close()
    
    async def cleanup_expired_tokens(self):
        """Clean up expired tokens (run periodically)"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Remove expired tokens
            cursor.execute("""
                DELETE FROM mfa_tokens 
                WHERE expires_at < ? OR status IN ('used', 'invalid', 'expired')
            """, (datetime.now().isoformat(),))
            
            # Clean old rate limit records
            old_window = datetime.now() - timedelta(hours=2)
            cursor.execute("""
                DELETE FROM mfa_rate_limits 
                WHERE window_start < ?
            """, (old_window.isoformat(),))
            
            conn.commit()
            conn.close()
            
            logger.info("MFA token cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during token cleanup: {e}")

# Global instance
_mfa_manager = None

def get_mfa_manager() -> MFAManager:
    """Get global MFA manager instance"""
    global _mfa_manager
    if _mfa_manager is None:
        _mfa_manager = MFAManager()
    return _mfa_manager

if __name__ == "__main__":
    # Test the MFA manager
    async def test_mfa_manager():
        mfa = MFAManager()
        
        print("Testing MFA Manager")
        print("=" * 50)
        
        # Test TOTP setup
        user_id = "test_user@estatecore.com"
        totp_setup = await mfa.setup_totp(user_id, "Test Device")
        
        print(f"TOTP Setup Result:")
        print(f"Secret: {totp_setup['secret']}")
        print(f"QR Code length: {len(totp_setup['qr_code'])}")
        print(f"Backup codes: {len(totp_setup['backup_codes'])}")
        
        # Test token verification
        import pyotp
        totp = pyotp.TOTP(totp_setup['secret'])
        current_token = totp.now()
        
        # Complete setup
        setup_verified = await mfa.verify_totp_setup(user_id, current_token)
        print(f"Setup verification: {setup_verified}")
        
        # Test verification
        verification_result = await mfa.verify_mfa_token(user_id, MFAMethod.TOTP, current_token)
        print(f"Token verification: {verification_result.success}")
        
        print("\nMFA Manager Test Complete!")
    
    asyncio.run(test_mfa_manager())
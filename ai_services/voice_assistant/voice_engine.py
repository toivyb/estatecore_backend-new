#!/usr/bin/env python3
"""
Voice-Activated Property Assistant for EstateCore Phase 7E
Advanced voice recognition, natural language understanding, and speech synthesis
"""

import os
import json
import logging
import asyncio
import wave
import tempfile
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceCommand(Enum):
    # Property Management Commands
    GET_PROPERTY_STATUS = "get_property_status"
    CHECK_OCCUPANCY = "check_occupancy"
    VIEW_MAINTENANCE = "view_maintenance"
    SCHEDULE_MAINTENANCE = "schedule_maintenance"
    
    # Financial Commands
    GET_RENT_STATUS = "get_rent_status"
    VIEW_FINANCIALS = "view_financials"
    GENERATE_REPORT = "generate_report"
    
    # Market Intelligence Commands
    GET_MARKET_DATA = "get_market_data"
    CHECK_OPPORTUNITIES = "check_opportunities"
    
    # General Commands
    HELP = "help"
    REPEAT = "repeat"
    CANCEL = "cancel"
    STOP = "stop"

class VoiceLanguage(Enum):
    ENGLISH_US = "en-US"
    ENGLISH_UK = "en-UK"
    SPANISH_US = "es-US"
    FRENCH_FR = "fr-FR"
    GERMAN_DE = "de-DE"

class SpeechSynthesisVoice(Enum):
    MALE_PROFESSIONAL = "male_professional"
    FEMALE_PROFESSIONAL = "female_professional"
    NEUTRAL_AI = "neutral_ai"

@dataclass
class VoiceSession:
    """Voice interaction session"""
    session_id: str
    user_id: str
    language: VoiceLanguage
    voice_preference: SpeechSynthesisVoice
    started_at: datetime
    last_activity: datetime
    conversation_context: Dict[str, Any]
    audio_quality_settings: Dict[str, Any]
    is_active: bool

@dataclass
class VoiceRecognitionResult:
    """Speech-to-text recognition result"""
    transcript: str
    confidence: float
    language_detected: str
    duration_seconds: float
    audio_quality_score: float
    alternative_transcripts: List[str]
    processing_time_ms: int

@dataclass
class VoiceCommand_Parsed:
    """Parsed voice command"""
    command: VoiceCommand
    parameters: Dict[str, Any]
    entities: List[Dict[str, Any]]
    intent_confidence: float
    requires_confirmation: bool
    context_needed: List[str]

@dataclass
class VoiceResponse:
    """Voice assistant response"""
    response_id: str
    text_content: str
    audio_url: Optional[str]
    voice_used: SpeechSynthesisVoice
    duration_seconds: float
    response_type: str  # "answer", "question", "confirmation", "error"
    suggested_followups: List[str]
    visual_data: Optional[Dict[str, Any]]  # For displaying charts/data
    metadata: Dict[str, Any]

class VoiceRecognitionEngine:
    """Advanced voice recognition with noise reduction and adaptation"""
    
    def __init__(self):
        self.supported_languages = [lang for lang in VoiceLanguage]
        self.noise_reduction_enabled = True
        self.speaker_adaptation_enabled = True
        self.real_time_processing = True
        
        # Simulated wake word detection
        self.wake_words = ["hey estate", "estate core", "property assistant"]
        
        logger.info("VoiceRecognitionEngine initialized")
    
    async def transcribe_audio(self, audio_data: bytes, language: VoiceLanguage = VoiceLanguage.ENGLISH_US,
                              enable_profanity_filter: bool = True) -> VoiceRecognitionResult:
        """Convert speech audio to text"""
        try:
            # Simulate audio processing time
            await asyncio.sleep(0.5)
            
            # In a real implementation, this would use speech recognition APIs like:
            # - Google Cloud Speech-to-Text
            # - Azure Speech Services
            # - AWS Transcribe
            # - OpenAI Whisper
            
            # Simulate different transcription scenarios based on audio length
            audio_length = len(audio_data) / 16000  # Assuming 16kHz sample rate
            
            # Simulate various voice commands for demo
            sample_transcripts = [
                "What is the occupancy rate for my properties?",
                "Schedule maintenance for property 123",
                "Show me the financial report for this month",
                "What are the current market trends?",
                "How much rent did I collect this month?",
                "Are there any maintenance requests pending?",
                "Generate a property performance report",
                "What investment opportunities are available?",
                "Help me with property management",
                "Cancel the last request"
            ]
            
            # Select transcript based on audio characteristics (simulated)
            import random
            transcript = random.choice(sample_transcripts)
            confidence = random.uniform(0.75, 0.95)
            
            # Apply profanity filter if enabled
            if enable_profanity_filter:
                transcript = self._apply_profanity_filter(transcript)
            
            return VoiceRecognitionResult(
                transcript=transcript,
                confidence=confidence,
                language_detected=language.value,
                duration_seconds=audio_length,
                audio_quality_score=random.uniform(0.7, 0.95),
                alternative_transcripts=[
                    transcript.replace("property", "building"),
                    transcript.replace("maintenance", "repair")
                ],
                processing_time_ms=int(audio_length * 500)
            )
            
        except Exception as e:
            logger.error(f"Error in voice recognition: {e}")
            raise
    
    async def detect_wake_word(self, audio_stream: bytes) -> bool:
        """Detect wake word in audio stream"""
        try:
            # Simulate wake word detection
            await asyncio.sleep(0.1)
            
            # In real implementation, this would use wake word detection models
            # For demo, randomly trigger wake word detection
            return random.random() > 0.8
            
        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
            return False
    
    def _apply_profanity_filter(self, text: str) -> str:
        """Apply profanity filter to transcript"""
        # Simple profanity filter implementation
        profanity_words = ["damn", "shit", "fuck", "ass"]
        filtered_text = text
        
        for word in profanity_words:
            filtered_text = filtered_text.replace(word, "*" * len(word))
        
        return filtered_text

class VoiceCommandProcessor:
    """Process and understand voice commands"""
    
    def __init__(self):
        self.command_patterns = {
            VoiceCommand.GET_PROPERTY_STATUS: [
                r"(what|show|tell).*(property|building).*(status|condition)",
                r"property.*(overview|summary|status)",
                r"(how|what).*(properties|buildings).*(doing|performing)"
            ],
            VoiceCommand.CHECK_OCCUPANCY: [
                r"(what|show).*(occupancy|vacancy).*(rate|level)",
                r"how many.*(units|apartments).*(occupied|vacant|empty)",
                r"occupancy.*(status|report|information)"
            ],
            VoiceCommand.VIEW_MAINTENANCE: [
                r"(show|view|list).*(maintenance|repair).*(requests|issues|work)",
                r"what.*(maintenance|repairs).*(needed|pending|scheduled)",
                r"maintenance.*(status|dashboard|overview)"
            ],
            VoiceCommand.SCHEDULE_MAINTENANCE: [
                r"(schedule|book|arrange).*(maintenance|repair|service)",
                r"need.*(maintenance|repair|fix)",
                r"(set up|organize).*(maintenance|service).*(appointment|visit)"
            ],
            VoiceCommand.GET_RENT_STATUS: [
                r"(what|show).*(rent|rental).*(status|collection|income)",
                r"how much.*(rent|money|income).*(collected|received)",
                r"rent.*(collection|payment).*(status|report)"
            ],
            VoiceCommand.VIEW_FINANCIALS: [
                r"(show|view|display).*(financial|finance).*(report|summary|data)",
                r"(what|how).*(financial|money).*(performance|status)",
                r"financial.*(dashboard|overview|analysis)"
            ],
            VoiceCommand.GET_MARKET_DATA: [
                r"(what|show).*(market|real estate).*(data|information|trends)",
                r"market.*(conditions|analysis|report)",
                r"(how|what).*(market|property values|prices)"
            ],
            VoiceCommand.HELP: [
                r"help",
                r"what.*(can|do).*(you|assistant)",
                r"(show|tell).*(commands|options|features)"
            ],
            VoiceCommand.CANCEL: [
                r"(cancel|stop|nevermind|forget)",
                r"(go back|undo|abort)",
                r"(exit|quit|end)"
            ]
        }
        
        logger.info("VoiceCommandProcessor initialized")
    
    async def parse_command(self, transcript: str, context: Dict[str, Any] = None) -> VoiceCommand_Parsed:
        """Parse voice transcript into structured command"""
        try:
            transcript_lower = transcript.lower().strip()
            
            # Find matching command
            best_command = VoiceCommand.HELP
            best_confidence = 0.0
            
            for command, patterns in self.command_patterns.items():
                for pattern in patterns:
                    import re
                    if re.search(pattern, transcript_lower):
                        confidence = self._calculate_pattern_confidence(pattern, transcript_lower)
                        if confidence > best_confidence:
                            best_command = command
                            best_confidence = confidence
            
            # Extract parameters and entities
            parameters = await self._extract_parameters(transcript, best_command)
            entities = await self._extract_entities(transcript)
            
            # Determine if confirmation is needed
            requires_confirmation = best_command in [
                VoiceCommand.SCHEDULE_MAINTENANCE,
                VoiceCommand.GENERATE_REPORT
            ] and best_confidence < 0.8
            
            # Determine what context is needed
            context_needed = self._determine_context_needs(best_command, parameters)
            
            return VoiceCommand_Parsed(
                command=best_command,
                parameters=parameters,
                entities=entities,
                intent_confidence=best_confidence,
                requires_confirmation=requires_confirmation,
                context_needed=context_needed
            )
            
        except Exception as e:
            logger.error(f"Error parsing voice command: {e}")
            raise
    
    def _calculate_pattern_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern match"""
        import re
        match = re.search(pattern, text)
        if not match:
            return 0.0
        
        match_length = len(match.group(0))
        text_length = len(text)
        return min(0.95, (match_length / text_length) + 0.3)
    
    async def _extract_parameters(self, transcript: str, command: VoiceCommand) -> Dict[str, Any]:
        """Extract parameters specific to the command"""
        parameters = {}
        transcript_lower = transcript.lower()
        
        # Extract property references
        import re
        property_match = re.search(r'property\s+(\d+)', transcript_lower)
        if property_match:
            parameters['property_id'] = property_match.group(1)
        
        building_match = re.search(r'building\s+(\d+)', transcript_lower)
        if building_match:
            parameters['building_id'] = building_match.group(1)
        
        # Extract time references
        if 'this month' in transcript_lower:
            parameters['time_period'] = 'current_month'
        elif 'last month' in transcript_lower:
            parameters['time_period'] = 'last_month'
        elif 'this year' in transcript_lower:
            parameters['time_period'] = 'current_year'
        
        # Extract maintenance types
        if command == VoiceCommand.SCHEDULE_MAINTENANCE:
            maintenance_types = ['hvac', 'plumbing', 'electrical', 'painting', 'roofing']
            for mtype in maintenance_types:
                if mtype in transcript_lower:
                    parameters['maintenance_type'] = mtype
                    break
        
        return parameters
    
    async def _extract_entities(self, transcript: str) -> List[Dict[str, Any]]:
        """Extract named entities from transcript"""
        entities = []
        transcript_lower = transcript.lower()
        
        # Extract monetary amounts
        import re
        money_pattern = r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        money_matches = re.finditer(money_pattern, transcript)
        for match in money_matches:
            entities.append({
                'type': 'money',
                'value': match.group(1),
                'start': match.start(),
                'end': match.end()
            })
        
        # Extract dates
        date_patterns = [
            r'(today|tomorrow|yesterday)',
            r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(next|last)\s+(week|month|year)'
        ]
        
        for pattern in date_patterns:
            matches = re.finditer(pattern, transcript_lower)
            for match in matches:
                entities.append({
                    'type': 'date',
                    'value': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })
        
        return entities
    
    def _determine_context_needs(self, command: VoiceCommand, parameters: Dict[str, Any]) -> List[str]:
        """Determine what additional context is needed"""
        context_needed = []
        
        if command == VoiceCommand.SCHEDULE_MAINTENANCE:
            if 'property_id' not in parameters and 'building_id' not in parameters:
                context_needed.append('property_specification')
            if 'maintenance_type' not in parameters:
                context_needed.append('maintenance_type')
        
        elif command == VoiceCommand.GET_RENT_STATUS:
            if 'time_period' not in parameters:
                context_needed.append('time_period')
        
        return context_needed

class SpeechSynthesisEngine:
    """Convert text responses to natural speech"""
    
    def __init__(self):
        self.available_voices = {
            SpeechSynthesisVoice.MALE_PROFESSIONAL: {
                'name': 'David Professional',
                'language': 'en-US',
                'gender': 'male',
                'style': 'professional'
            },
            SpeechSynthesisVoice.FEMALE_PROFESSIONAL: {
                'name': 'Sarah Professional',
                'language': 'en-US',
                'gender': 'female',
                'style': 'professional'
            },
            SpeechSynthesisVoice.NEUTRAL_AI: {
                'name': 'AI Assistant',
                'language': 'en-US',
                'gender': 'neutral',
                'style': 'ai_assistant'
            }
        }
        
        logger.info("SpeechSynthesisEngine initialized")
    
    async def synthesize_speech(self, text: str, voice: SpeechSynthesisVoice = SpeechSynthesisVoice.FEMALE_PROFESSIONAL,
                               language: VoiceLanguage = VoiceLanguage.ENGLISH_US,
                               speaking_rate: float = 1.0, pitch: float = 0.0) -> Dict[str, Any]:
        """Convert text to speech audio"""
        try:
            # Simulate speech synthesis processing
            await asyncio.sleep(len(text) * 0.05)  # Simulate processing time based on text length
            
            # In a real implementation, this would use TTS services like:
            # - Google Cloud Text-to-Speech
            # - Azure Cognitive Services Speech
            # - AWS Polly
            # - OpenAI TTS
            
            # Generate simulated audio metadata
            estimated_duration = len(text) * 0.15  # Rough estimate: ~150ms per character
            
            # Simulate audio file generation
            audio_filename = f"speech_{uuid.uuid4().hex[:8]}.wav"
            audio_url = f"/api/voice/audio/{audio_filename}"
            
            # Simulate audio quality metrics
            audio_quality = {
                'clarity_score': 0.92,
                'naturalness_score': 0.88,
                'pronunciation_accuracy': 0.95,
                'emotional_tone': 'professional_friendly'
            }
            
            return {
                'audio_url': audio_url,
                'audio_filename': audio_filename,
                'duration_seconds': estimated_duration,
                'voice_used': voice.value,
                'language': language.value,
                'speaking_rate': speaking_rate,
                'pitch': pitch,
                'text_length': len(text),
                'audio_quality': audio_quality,
                'file_size_kb': int(estimated_duration * 32),  # Estimate file size
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in speech synthesis: {e}")
            raise

class VoiceAssistant:
    """Main voice assistant orchestrator"""
    
    def __init__(self):
        self.recognition_engine = VoiceRecognitionEngine()
        self.command_processor = VoiceCommandProcessor()
        self.synthesis_engine = SpeechSynthesisEngine()
        
        self.active_sessions: Dict[str, VoiceSession] = {}
        self.conversation_history: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info("VoiceAssistant initialized")
    
    async def start_voice_session(self, user_id: str, language: VoiceLanguage = VoiceLanguage.ENGLISH_US,
                                 voice_preference: SpeechSynthesisVoice = SpeechSynthesisVoice.FEMALE_PROFESSIONAL) -> str:
        """Start a new voice interaction session"""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now()
            
            session = VoiceSession(
                session_id=session_id,
                user_id=user_id,
                language=language,
                voice_preference=voice_preference,
                started_at=now,
                last_activity=now,
                conversation_context={},
                audio_quality_settings={
                    'noise_reduction': True,
                    'echo_cancellation': True,
                    'automatic_gain_control': True,
                    'sample_rate': 16000,
                    'bit_depth': 16
                },
                is_active=True
            )
            
            self.active_sessions[session_id] = session
            self.conversation_history[session_id] = []
            
            logger.info(f"Started voice session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting voice session: {e}")
            raise
    
    async def process_voice_input(self, session_id: str, audio_data: bytes) -> VoiceResponse:
        """Process voice input and generate response"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Voice session {session_id} not found")
            
            session = self.active_sessions[session_id]
            session.last_activity = datetime.now()
            
            # Step 1: Speech-to-Text
            recognition_result = await self.recognition_engine.transcribe_audio(
                audio_data, session.language
            )
            
            # Step 2: Command Understanding
            parsed_command = await self.command_processor.parse_command(
                recognition_result.transcript, session.conversation_context
            )
            
            # Step 3: Execute Command
            response_content = await self._execute_voice_command(parsed_command, session)
            
            # Step 4: Generate Speech Response
            speech_result = await self.synthesis_engine.synthesize_speech(
                response_content['text'], session.voice_preference, session.language
            )
            
            # Step 5: Create Response
            response = VoiceResponse(
                response_id=str(uuid.uuid4()),
                text_content=response_content['text'],
                audio_url=speech_result['audio_url'],
                voice_used=session.voice_preference,
                duration_seconds=speech_result['duration_seconds'],
                response_type=response_content['type'],
                suggested_followups=response_content.get('followups', []),
                visual_data=response_content.get('visual_data'),
                metadata={
                    'recognition_confidence': recognition_result.confidence,
                    'command_confidence': parsed_command.intent_confidence,
                    'processing_time': speech_result.get('processing_time', 0),
                    'session_id': session_id
                }
            )
            
            # Add to conversation history
            self.conversation_history[session_id].extend([
                {
                    'type': 'user_speech',
                    'content': recognition_result.transcript,
                    'timestamp': datetime.now().isoformat(),
                    'confidence': recognition_result.confidence
                },
                {
                    'type': 'assistant_response',
                    'content': response.text_content,
                    'timestamp': datetime.now().isoformat(),
                    'audio_url': response.audio_url
                }
            ])
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing voice input: {e}")
            raise
    
    async def _execute_voice_command(self, command: VoiceCommand_Parsed, session: VoiceSession) -> Dict[str, Any]:
        """Execute the parsed voice command"""
        try:
            # Integration with existing EstateCore services
            
            if command.command == VoiceCommand.GET_PROPERTY_STATUS:
                return {
                    'text': "You currently have 12 properties in your portfolio. 10 are fully occupied, 1 has a vacant unit, and 1 is undergoing maintenance. Overall occupancy rate is 92%. Would you like details on any specific property?",
                    'type': 'answer',
                    'followups': [
                        "Show me the vacant property details",
                        "What maintenance is being done?",
                        "Show occupancy trends"
                    ],
                    'visual_data': {
                        'chart_type': 'property_overview',
                        'data': {
                            'total_properties': 12,
                            'occupied': 10,
                            'vacant': 1,
                            'maintenance': 1,
                            'occupancy_rate': 92
                        }
                    }
                }
            
            elif command.command == VoiceCommand.CHECK_OCCUPANCY:
                property_id = command.parameters.get('property_id')
                if property_id:
                    return {
                        'text': f"Property {property_id} has an occupancy rate of 88%. It has 24 total units with 21 currently occupied and 3 vacant. The average rent is $2,800 per month.",
                        'type': 'answer',
                        'followups': [
                            "Show rental income for this property",
                            "What's the average vacancy time?",
                            "Show occupancy history"
                        ]
                    }
                else:
                    return {
                        'text': "Your overall portfolio occupancy rate is 92%. This is above the market average of 87%. You have 145 total units with 133 occupied and 12 vacant across all properties.",
                        'type': 'answer',
                        'followups': [
                            "Show me property-by-property breakdown",
                            "Which properties have vacancies?",
                            "Show occupancy trends"
                        ]
                    }
            
            elif command.command == VoiceCommand.VIEW_MAINTENANCE:
                return {
                    'text': "You have 8 maintenance requests currently. 3 are high priority including HVAC repair at Property 7, plumbing leak at Property 12, and electrical issue at Property 3. 5 are routine maintenance items scheduled for this week.",
                    'type': 'answer',
                    'followups': [
                        "Show high priority items first",
                        "Schedule maintenance for next week",
                        "Show maintenance costs this month"
                    ],
                    'visual_data': {
                        'chart_type': 'maintenance_summary',
                        'data': {
                            'total_requests': 8,
                            'high_priority': 3,
                            'routine': 5,
                            'categories': {
                                'HVAC': 2,
                                'Plumbing': 3,
                                'Electrical': 2,
                                'General': 1
                            }
                        }
                    }
                }
            
            elif command.command == VoiceCommand.SCHEDULE_MAINTENANCE:
                maintenance_type = command.parameters.get('maintenance_type', 'general')
                property_id = command.parameters.get('property_id', 'unspecified')
                
                if command.requires_confirmation:
                    return {
                        'text': f"I'll schedule {maintenance_type} maintenance for property {property_id}. Should I book this for the next available slot this week, or would you prefer a specific date?",
                        'type': 'confirmation',
                        'followups': [
                            "Next available slot",
                            "Schedule for specific date",
                            "Show available contractors"
                        ]
                    }
                else:
                    return {
                        'text': f"I've scheduled {maintenance_type} maintenance for property {property_id} on Thursday at 10 AM with Johnson Repair Services. You'll receive a confirmation email shortly.",
                        'type': 'answer',
                        'followups': [
                            "Show maintenance calendar",
                            "Add this to my calendar",
                            "Show contractor details"
                        ]
                    }
            
            elif command.command == VoiceCommand.GET_RENT_STATUS:
                time_period = command.parameters.get('time_period', 'current_month')
                
                if time_period == 'current_month':
                    return {
                        'text': "This month you've collected $84,500 in rent out of $92,000 expected. That's 92% collection rate. You have 3 tenants with outstanding payments totaling $7,500. Two payments are less than 5 days late.",
                        'type': 'answer',
                        'followups': [
                            "Show late payment details",
                            "Send payment reminders",
                            "Show collection trends"
                        ]
                    }
                else:
                    return {
                        'text': "Last month you collected $91,200 in rent with a 99% collection rate. Only one tenant was late by 2 days. This was your best collection month this year.",
                        'type': 'answer',
                        'followups': [
                            "Compare to previous months",
                            "Show annual collection summary",
                            "Generate collection report"
                        ]
                    }
            
            elif command.command == VoiceCommand.VIEW_FINANCIALS:
                return {
                    'text': "Your portfolio generated $89,500 in revenue this month with $34,200 in expenses, resulting in $55,300 net operating income. This is a 12% increase from last month. Your best performing property is generating 15% ROI.",
                    'type': 'answer',
                    'followups': [
                        "Show expense breakdown",
                        "Compare to budget",
                        "Show ROI by property"
                    ],
                    'visual_data': {
                        'chart_type': 'financial_summary',
                        'data': {
                            'revenue': 89500,
                            'expenses': 34200,
                            'noi': 55300,
                            'roi_avg': 12,
                            'month_change': 12
                        }
                    }
                }
            
            elif command.command == VoiceCommand.GET_MARKET_DATA:
                return {
                    'text': "Current market conditions in your area show property values up 8% year-over-year. Average rent has increased 5%. Market inventory is low with 45 days average time on market. This is a strong seller's market with good rental demand.",
                    'type': 'answer',
                    'followups': [
                        "Show investment opportunities",
                        "Compare to national trends",
                        "Show market forecasts"
                    ]
                }
            
            elif command.command == VoiceCommand.HELP:
                return {
                    'text': "I'm your EstateCore voice assistant. I can help you check property status, occupancy rates, maintenance requests, rent collection, financial reports, and market data. You can also ask me to schedule maintenance or generate reports. What would you like to know?",
                    'type': 'answer',
                    'followups': [
                        "Show me property overview",
                        "Check maintenance requests",
                        "View financial summary"
                    ]
                }
            
            elif command.command == VoiceCommand.CANCEL:
                return {
                    'text': "Okay, I've cancelled that request. Is there anything else I can help you with?",
                    'type': 'answer',
                    'followups': [
                        "Check property status",
                        "View maintenance requests",
                        "Get help with commands"
                    ]
                }
            
            else:
                return {
                    'text': "I'm not sure how to help with that request. You can ask me about property status, occupancy rates, maintenance, rent collection, financial reports, or market data. What would you like to know?",
                    'type': 'clarification',
                    'followups': [
                        "Show available commands",
                        "Check property overview",
                        "View help information"
                    ]
                }
            
        except Exception as e:
            logger.error(f"Error executing voice command: {e}")
            return {
                'text': "I'm sorry, I encountered an error processing your request. Please try again or ask for help with available commands.",
                'type': 'error',
                'followups': [
                    "Try again",
                    "Show available commands",
                    "Get technical support"
                ]
            }
    
    async def end_voice_session(self, session_id: str):
        """End a voice interaction session"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.is_active = False
                del self.active_sessions[session_id]
                
                logger.info(f"Ended voice session {session_id}")
            
        except Exception as e:
            logger.error(f"Error ending voice session: {e}")

# Global instance
_voice_assistant = None

def get_voice_assistant() -> VoiceAssistant:
    """Get global voice assistant instance"""
    global _voice_assistant
    if _voice_assistant is None:
        _voice_assistant = VoiceAssistant()
    return _voice_assistant

# API convenience functions
async def start_voice_session_api(user_id: str, language: str = "en-US", voice: str = "female_professional") -> Dict[str, Any]:
    """Start voice session for API"""
    assistant = get_voice_assistant()
    
    language_enum = VoiceLanguage(language)
    voice_enum = SpeechSynthesisVoice(voice)
    
    session_id = await assistant.start_voice_session(user_id, language_enum, voice_enum)
    
    return {
        'session_id': session_id,
        'language': language,
        'voice': voice,
        'started_at': datetime.now().isoformat(),
        'status': 'active'
    }

async def process_voice_input_api(session_id: str, audio_data: str) -> Dict[str, Any]:
    """Process voice input for API"""
    assistant = get_voice_assistant()
    
    # Decode base64 audio data
    audio_bytes = base64.b64decode(audio_data)
    
    response = await assistant.process_voice_input(session_id, audio_bytes)
    
    return {
        'response_id': response.response_id,
        'text': response.text_content,
        'audio_url': response.audio_url,
        'duration': response.duration_seconds,
        'type': response.response_type,
        'followups': response.suggested_followups,
        'visual_data': response.visual_data,
        'metadata': response.metadata
    }

if __name__ == "__main__":
    # Test the voice assistant
    async def test_voice_assistant():
        assistant = VoiceAssistant()
        
        print("Testing Voice Assistant")
        print("=" * 50)
        
        # Start session
        print("Starting voice session...")
        session_id = await assistant.start_voice_session("test_user_1")
        print(f"Session ID: {session_id}")
        
        # Simulate voice commands
        test_commands = [
            "What is the occupancy rate for my properties?",
            "Schedule HVAC maintenance for property 123",
            "Show me this month's rent collection",
            "What are the current market trends?",
            "Help me with available commands"
        ]
        
        for command in test_commands:
            print(f"\nProcessing: '{command}'")
            
            # Simulate audio data (in real app, this would be actual audio)
            audio_data = command.encode('utf-8')
            
            try:
                response = await assistant.process_voice_input(session_id, audio_data)
                print(f"Response: {response.text_content[:100]}...")
                print(f"Type: {response.response_type}")
                if response.suggested_followups:
                    print(f"Followups: {response.suggested_followups[:2]}")
            except Exception as e:
                print(f"Error: {e}")
        
        # End session
        await assistant.end_voice_session(session_id)
        print(f"\nEnded session {session_id}")
        
        print("\nVoice Assistant Test Complete!")
    
    asyncio.run(test_voice_assistant())
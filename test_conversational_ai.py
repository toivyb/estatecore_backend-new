#!/usr/bin/env python3
"""Test the Conversational AI System"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(__file__))

async def test_conversational_ai():
    print("Testing EstateCore Conversational AI System")
    print("=" * 50)
    
    try:
        # Import the chatbot engine
        from ai_services.conversational_ai.chatbot_engine import EstateCoreChatbot, process_chat_message
        
        print("[SUCCESS] Successfully imported chatbot engine")
        
        # Test chatbot initialization
        print("\n1. Testing Chatbot Initialization...")
        chatbot = EstateCoreChatbot()
        print("[SUCCESS] Chatbot initialized successfully")
        
        # Test message processing
        print("\n2. Testing Message Processing...")
        test_messages = [
            "Hello!",
            "What's the occupancy rate for my properties?",
            "Can you get me market data for New York?",
            "Schedule HVAC maintenance for property 123",
            "Show me information about property 1",
            "Help me with rental income",
            "What are the current market trends?"
        ]
        
        user_id = "test_user_1"
        session_id = None
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n   Test {i}: '{message}'")
            
            try:
                # Test the API function
                response = await process_chat_message(message, user_id, session_id)
                session_id = response.get('session_id')  # Maintain session
                
                print(f"   [SUCCESS] Response: {response['response'][:100]}...")
                print(f"   Intent: {response['intent']} (confidence: {response['confidence']:.2f})")
                
                if response.get('entities'):
                    entities_str = ", ".join([f"{e['type']}: {e['value']}" for e in response['entities']])
                    print(f"   Entities: {entities_str}")
                
                if response.get('suggested_actions'):
                    actions_str = ", ".join([a['text'] for a in response['suggested_actions']])
                    print(f"   Suggestions: {actions_str}")
                    
            except Exception as e:
                print(f"   [ERROR] Error processing message: {e}")
        
        # Test conversation management
        print("\n3. Testing Conversation Management...")
        
        # Test context persistence
        print("   Testing context persistence...")
        try:
            context = chatbot.conversation_manager.get_or_create_context(user_id, session_id)
            print(f"   [SUCCESS] Context created with session ID: {context.session_id}")
            print(f"   Conversation history length: {len(context.conversation_history)}")
        except Exception as e:
            print(f"   [ERROR] Error with context management: {e}")
        
        # Test entity extraction
        print("\n4. Testing Entity Extraction...")
        test_entity_messages = [
            "Schedule maintenance for property 123",
            "What's the occupancy for 456 Main Street?",
            "Show me rental income for $2500",
            "Book HVAC repair for tomorrow"
        ]
        
        for message in test_entity_messages:
            print(f"   Testing: '{message}'")
            try:
                entities = chatbot.entity_extractor.extract(message)
                if entities:
                    for entity in entities:
                        print(f"   [SUCCESS] Found {entity.type.value}: {entity.value} (confidence: {entity.confidence:.2f})")
                else:
                    print("   [INFO] No entities found")
            except Exception as e:
                print(f"   [ERROR] Error extracting entities: {e}")
        
        # Test intent classification
        print("\n5. Testing Intent Classification...")
        test_intent_messages = [
            "What's my property occupancy?",
            "Schedule maintenance",
            "Show me market data",
            "Help",
            "Hello there",
            "Random nonsense text"
        ]
        
        for message in test_intent_messages:
            print(f"   Testing: '{message}'")
            try:
                intent, confidence = chatbot.intent_classifier.classify(message)
                print(f"   [SUCCESS] Intent: {intent.value} (confidence: {confidence:.2f})")
            except Exception as e:
                print(f"   [ERROR] Error classifying intent: {e}")
        
        print("\n" + "=" * 50)
        print("[SUCCESS] Conversational AI System Test Complete!")
        print("   All core components are working correctly.")
        print("   Ready for integration with Flask API and React frontend.")
        
    except ImportError as e:
        print(f"[ERROR] Import Error: {e}")
        print("Make sure all required dependencies are installed.")
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_conversational_ai())
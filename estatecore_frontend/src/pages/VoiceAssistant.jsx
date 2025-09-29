import React, { useState, useEffect, useRef } from 'react';

const VoiceAssistant = () => {
  const [isListening, setIsListening] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [conversationHistory, setConversationHistory] = useState([]);
  const [capabilities, setCapabilities] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en-US');
  const [selectedVoice, setSelectedVoice] = useState('female_professional');
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [currentResponse, setCurrentResponse] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Refs for audio handling
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    loadCapabilities();
    // Add welcome message
    setConversationHistory([{
      id: Date.now(),
      type: 'assistant',
      content: "Hello! I'm your EstateCore voice assistant. Click the microphone to start talking, or start a voice session to begin. I can help you with property management, maintenance, financial reports, and market data.",
      timestamp: new Date().toISOString(),
      audio_url: null
    }]);
  }, []);

  // Load voice assistant capabilities
  const loadCapabilities = async () => {
    try {
      const response = await fetch('/api/voice/capabilities');
      const result = await response.json();
      
      if (result.success) {
        setCapabilities(result.capabilities);
      }
    } catch (error) {
      console.error('Failed to load voice capabilities:', error);
    }
  };

  // Start voice session
  const startVoiceSession = async () => {
    try {
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      const userId = user.id || 'anonymous';

      const response = await fetch('/api/voice/session/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          language: selectedLanguage,
          voice: selectedVoice
        })
      });

      const result = await response.json();
      
      if (result.success) {
        setSessionId(result.session.session_id);
        setIsSessionActive(true);
        
        addToConversationHistory({
          type: 'system',
          content: `Voice session started. Language: ${selectedLanguage}, Voice: ${selectedVoice.replace('_', ' ')}`
        });
      } else {
        console.error('Failed to start voice session:', result.error);
        addToConversationHistory({
          type: 'error',
          content: `Failed to start voice session: ${result.error}`
        });
      }
    } catch (error) {
      console.error('Error starting voice session:', error);
      addToConversationHistory({
        type: 'error',
        content: 'Error starting voice session. Please try again.'
      });
    }
  };

  // End voice session
  const endVoiceSession = async () => {
    try {
      if (sessionId) {
        await fetch('/api/voice/session/end', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ session_id: sessionId })
        });
      }

      setSessionId(null);
      setIsSessionActive(false);
      setIsListening(false);
      
      // Stop any ongoing recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      
      // Stop audio stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      
      addToConversationHistory({
        type: 'system',
        content: 'Voice session ended.'
      });
    } catch (error) {
      console.error('Error ending voice session:', error);
    }
  };

  // Initialize audio recording
  const initializeAudio = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      streamRef.current = stream;
      
      // Set up audio context for visualization
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      analyserRef.current = audioContextRef.current.createAnalyser();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      source.connect(analyserRef.current);
      
      analyserRef.current.fftSize = 256;
      
      // Set up media recorder
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];
        processAudioInput(audioBlob);
      };
      
      return true;
    } catch (error) {
      console.error('Error accessing microphone:', error);
      addToConversationHistory({
        type: 'error',
        content: 'Could not access microphone. Please check permissions and try again.'
      });
      return false;
    }
  };

  // Start listening
  const startListening = async () => {
    if (!isSessionActive) {
      addToConversationHistory({
        type: 'error',
        content: 'Please start a voice session first.'
      });
      return;
    }

    const audioInitialized = await initializeAudio();
    if (!audioInitialized) return;

    setIsListening(true);
    mediaRecorderRef.current.start();
    
    // Start audio level monitoring
    monitorAudioLevel();
    
    addToConversationHistory({
      type: 'user',
      content: '[Listening...]'
    });
  };

  // Stop listening
  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    
    setIsListening(false);
    setAudioLevel(0);
  };

  // Monitor audio level for visualization
  const monitorAudioLevel = () => {
    if (!analyserRef.current || !isListening) return;
    
    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    
    const checkLevel = () => {
      if (!isListening) return;
      
      analyserRef.current.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
      setAudioLevel(average);
      
      requestAnimationFrame(checkLevel);
    };
    
    checkLevel();
  };

  // Process audio input
  const processAudioInput = async (audioBlob) => {
    if (!sessionId) return;
    
    setIsProcessing(true);
    
    try {
      // Convert audio blob to base64
      const arrayBuffer = await audioBlob.arrayBuffer();
      const uint8Array = new Uint8Array(arrayBuffer);
      const base64Audio = btoa(String.fromCharCode(...uint8Array));
      
      // Remove the user's "[Listening...]" message
      setConversationHistory(prev => prev.filter(msg => msg.content !== '[Listening...]'));
      
      const response = await fetch('/api/voice/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          audio_data: base64Audio
        })
      });

      const result = await response.json();
      
      if (result.success) {
        const responseData = result.response;
        
        // Add user message (transcript)
        addToConversationHistory({
          type: 'user',
          content: 'Voice input processed'  // In real app, would show transcript
        });
        
        // Add assistant response
        const assistantMessage = {
          type: 'assistant',
          content: responseData.text,
          audio_url: responseData.audio_url,
          duration: responseData.duration,
          response_type: responseData.type,
          followups: responseData.followups,
          visual_data: responseData.visual_data
        };
        
        addToConversationHistory(assistantMessage);
        setCurrentResponse(assistantMessage);
        
        // Play audio response if available
        if (responseData.audio_url) {
          // In a real implementation, would play the audio file
          console.log('Would play audio:', responseData.audio_url);
        }
        
      } else {
        addToConversationHistory({
          type: 'error',
          content: `Error processing voice input: ${result.error}`
        });
      }
    } catch (error) {
      console.error('Error processing audio:', error);
      addToConversationHistory({
        type: 'error',
        content: 'Error processing voice input. Please try again.'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Add message to conversation history
  const addToConversationHistory = (message) => {
    const newMessage = {
      id: Date.now() + Math.random(),
      timestamp: new Date().toISOString(),
      ...message
    };
    
    setConversationHistory(prev => [...prev, newMessage]);
  };

  // Execute suggested follow-up
  const executeFollowup = (followupText) => {
    // In a real implementation, this would send the followup as a voice command
    addToConversationHistory({
      type: 'user',
      content: followupText
    });
    
    // Simulate processing the followup
    setTimeout(() => {
      addToConversationHistory({
        type: 'assistant',
        content: `I understand you want to: "${followupText}". This would execute that command in a real implementation.`
      });
    }, 1000);
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Get microphone button color based on state
  const getMicButtonColor = () => {
    if (isProcessing) return 'bg-yellow-500 animate-pulse';
    if (isListening) return 'bg-red-500 animate-pulse';
    if (isSessionActive) return 'bg-blue-600 hover:bg-blue-700';
    return 'bg-gray-400';
  };

  // Get microphone button text
  const getMicButtonText = () => {
    if (isProcessing) return 'Processing...';
    if (isListening) return 'Listening...';
    if (isSessionActive) return 'Tap to Speak';
    return 'Start Session First';
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            🎤 Voice-Activated Property Assistant
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Hands-free property management with advanced voice recognition and natural language processing
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Voice Interface */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
              {/* Voice Controls Header */}
              <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                    Voice Interface
                  </h2>
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${isSessionActive ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      {isSessionActive ? 'Session Active' : 'Session Inactive'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Voice Controls */}
              <div className="p-6">
                <div className="flex flex-col items-center space-y-6">
                  {/* Session Controls */}
                  <div className="flex space-x-4">
                    {!isSessionActive ? (
                      <button
                        onClick={startVoiceSession}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
                      >
                        🎯 Start Voice Session
                      </button>
                    ) : (
                      <button
                        onClick={endVoiceSession}
                        className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium"
                      >
                        🛑 End Session
                      </button>
                    )}
                  </div>

                  {/* Microphone Button */}
                  <div className="relative">
                    <button
                      onClick={isListening ? stopListening : startListening}
                      disabled={!isSessionActive || isProcessing}
                      className={`w-32 h-32 rounded-full text-white font-bold text-lg shadow-lg transition-all duration-200 ${getMicButtonColor()} ${!isSessionActive ? 'cursor-not-allowed' : 'hover:scale-105'}`}
                    >
                      {isListening ? '🛑' : '🎤'}
                    </button>
                    
                    {/* Audio Level Visualization */}
                    {isListening && (
                      <div className="absolute inset-0 rounded-full border-4 border-white opacity-75"
                           style={{
                             transform: `scale(${1 + (audioLevel / 255) * 0.3})`,
                             transition: 'transform 0.1s ease-out'
                           }}>
                      </div>
                    )}
                  </div>

                  {/* Status Text */}
                  <div className="text-center">
                    <p className="text-lg font-medium text-gray-900 dark:text-gray-100">
                      {getMicButtonText()}
                    </p>
                    {isSessionActive && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        Try saying: "What's my occupancy rate?" or "Show maintenance requests"
                      </p>
                    )}
                  </div>

                  {/* Voice Settings */}
                  {!isSessionActive && capabilities && (
                    <div className="w-full max-w-md space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Language
                        </label>
                        <select
                          value={selectedLanguage}
                          onChange={(e) => setSelectedLanguage(e.target.value)}
                          className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                          {capabilities.supported_languages.map((lang) => (
                            <option key={lang.code} value={lang.code}>
                              {lang.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Voice
                        </label>
                        <select
                          value={selectedVoice}
                          onChange={(e) => setSelectedVoice(e.target.value)}
                          className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                        >
                          {capabilities.available_voices.map((voice) => (
                            <option key={voice.id} value={voice.id}>
                              {voice.name} ({voice.gender})
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Current Response Visual Data */}
              {currentResponse && currentResponse.visual_data && (
                <div className="p-6 border-t border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                    Data Visualization
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                    <pre className="text-sm text-gray-700 dark:text-gray-300 overflow-auto">
                      {JSON.stringify(currentResponse.visual_data, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Conversation History & Commands */}
          <div className="space-y-6">
            {/* Conversation History */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Conversation History
                </h3>
              </div>
              
              <div className="p-4 max-h-96 overflow-y-auto">
                <div className="space-y-4">
                  {conversationHistory.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-xs lg:max-w-sm p-3 rounded-lg ${
                        message.type === 'user' 
                          ? 'bg-blue-100 text-blue-900 dark:bg-blue-900 dark:text-blue-100'
                          : message.type === 'error'
                          ? 'bg-red-100 text-red-900 dark:bg-red-900 dark:text-red-100'
                          : message.type === 'system'
                          ? 'bg-yellow-100 text-yellow-900 dark:bg-yellow-900 dark:text-yellow-100'
                          : 'bg-gray-100 text-gray-900 dark:bg-gray-700 dark:text-gray-100'
                      }`}>
                        <div className="text-sm">
                          {message.content}
                        </div>
                        
                        {/* Message timestamp */}
                        <div className="text-xs opacity-75 mt-1">
                          {formatTimestamp(message.timestamp)}
                        </div>

                        {/* Follow-up suggestions */}
                        {message.followups && message.followups.length > 0 && (
                          <div className="mt-3 space-y-1">
                            <p className="text-xs font-medium">Suggestions:</p>
                            {message.followups.slice(0, 3).map((followup, index) => (
                              <button
                                key={index}
                                onClick={() => executeFollowup(followup)}
                                className="block w-full text-left text-xs px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                              >
                                {followup}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Voice Commands Help */}
            {capabilities && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Voice Commands
                  </h3>
                </div>
                
                <div className="p-4">
                  <div className="space-y-4">
                    {capabilities.supported_commands.map((category) => (
                      <div key={category.category}>
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
                          {category.category}
                        </h4>
                        <div className="space-y-1">
                          {category.commands.map((command, index) => (
                            <div
                              key={index}
                              className="text-sm text-gray-600 dark:text-gray-400 pl-2 border-l-2 border-gray-200 dark:border-gray-600"
                            >
                              "{command}"
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Features */}
            {capabilities && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg">
                <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Features
                  </h3>
                </div>
                
                <div className="p-4">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(capabilities.features).map(([feature, enabled]) => (
                      <div key={feature} className="flex items-center">
                        <span className={`w-2 h-2 rounded-full mr-2 ${enabled ? 'bg-green-500' : 'bg-gray-400'}`}></span>
                        <span className="text-gray-700 dark:text-gray-300 capitalize">
                          {feature.replace('_', ' ')}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceAssistant;
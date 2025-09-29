import React, { useState, useEffect, useRef } from 'react';
import { 
  Video, 
  VideoOff, 
  Mic, 
  MicOff, 
  Phone, 
  PhoneOff, 
  Users, 
  Share, 
  MessageSquare, 
  Settings,
  Monitor,
  Grid3x3,
  Maximize2,
  Minimize2,
  Volume2,
  VolumeX,
  MoreVertical,
  Record,
  StopCircle
} from 'lucide-react';

const VideoConferencing = ({ 
  meetingId, 
  onEndCall, 
  initialSettings = {
    video: true,
    audio: true,
    screenShare: false
  }
}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [localVideo, setLocalVideo] = useState(initialSettings.video);
  const [localAudio, setLocalAudio] = useState(initialSettings.audio);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [participants, setParticipants] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatVisible, setChatVisible] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // grid, speaker, presentation
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState('good');

  const localVideoRef = useRef(null);
  const remoteVideoRefs = useRef({});
  const localStreamRef = useRef(null);
  const peerConnections = useRef({});

  // Mock participant data
  useEffect(() => {
    setParticipants([
      { 
        id: 'user1', 
        name: 'John Smith', 
        role: 'Property Manager',
        video: true, 
        audio: true, 
        isSpeaking: false,
        connectionQuality: 'good'
      },
      { 
        id: 'user2', 
        name: 'Sarah Johnson', 
        role: 'Maintenance Lead',
        video: false, 
        audio: true, 
        isSpeaking: true,
        connectionQuality: 'fair'
      },
      { 
        id: 'user3', 
        name: 'Mike Wilson', 
        role: 'Accountant',
        video: true, 
        audio: true, 
        isSpeaking: false,
        connectionQuality: 'good'
      }
    ]);

    setChatMessages([
      { id: 1, sender: 'John Smith', message: 'Good morning everyone!', timestamp: new Date(Date.now() - 300000) },
      { id: 2, sender: 'Sarah Johnson', message: 'Hi John, ready for the property review?', timestamp: new Date(Date.now() - 180000) },
      { id: 3, sender: 'Mike Wilson', message: 'I have the financial reports ready to share', timestamp: new Date(Date.now() - 60000) }
    ]);
  }, []);

  // Initialize media and connection
  useEffect(() => {
    initializeMedia();
    return () => {
      cleanup();
    };
  }, []);

  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: localVideo,
        audio: localAudio
      });
      
      localStreamRef.current = stream;
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
      
      setIsConnected(true);
    } catch (error) {
      console.error('Error accessing media devices:', error);
    }
  };

  const cleanup = () => {
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
    }
    
    Object.values(peerConnections.current).forEach(pc => {
      pc.close();
    });
  };

  const toggleVideo = async () => {
    if (localStreamRef.current) {
      const videoTrack = localStreamRef.current.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !localVideo;
        setLocalVideo(!localVideo);
      }
    }
  };

  const toggleAudio = async () => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !localAudio;
        setLocalAudio(!localAudio);
      }
    }
  };

  const toggleScreenShare = async () => {
    try {
      if (!isScreenSharing) {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true
        });
        
        // Replace video track with screen share
        const videoTrack = screenStream.getVideoTracks()[0];
        if (localStreamRef.current) {
          const sender = Object.values(peerConnections.current)[0]?.getSenders()
            .find(s => s.track && s.track.kind === 'video');
          if (sender) {
            await sender.replaceTrack(videoTrack);
          }
        }
        
        setIsScreenSharing(true);
        setViewMode('presentation');
        
        videoTrack.onended = () => {
          setIsScreenSharing(false);
          setViewMode('grid');
        };
      } else {
        // Stop screen sharing and return to camera
        const cameraStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: localAudio
        });
        
        const videoTrack = cameraStream.getVideoTracks()[0];
        const sender = Object.values(peerConnections.current)[0]?.getSenders()
          .find(s => s.track && s.track.kind === 'video');
        if (sender) {
          await sender.replaceTrack(videoTrack);
        }
        
        setIsScreenSharing(false);
        setViewMode('grid');
      }
    } catch (error) {
      console.error('Error toggling screen share:', error);
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    // Implement recording logic here
  };

  const sendChatMessage = () => {
    if (newMessage.trim()) {
      const message = {
        id: Date.now(),
        sender: 'You',
        message: newMessage.trim(),
        timestamp: new Date()
      };
      setChatMessages([...chatMessages, message]);
      setNewMessage('');
    }
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const formatTime = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    }).format(date);
  };

  const getConnectionQualityColor = (quality) => {
    switch (quality) {
      case 'excellent': return 'text-green-500';
      case 'good': return 'text-blue-500';
      case 'fair': return 'text-yellow-500';
      case 'poor': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const VideoTile = ({ participant, isLocal = false, className = '' }) => (
    <div className={`relative bg-gray-900 rounded-lg overflow-hidden ${className}`}>
      {participant.video || isLocal ? (
        <video
          ref={isLocal ? localVideoRef : el => remoteVideoRefs.current[participant.id] = el}
          autoPlay
          muted={isLocal}
          playsInline
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-800">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-2">
              <span className="text-white font-semibold text-lg">
                {participant.name.charAt(0)}
              </span>
            </div>
            <p className="text-white text-sm">{participant.name}</p>
          </div>
        </div>
      )}
      
      {/* Participant Info Overlay */}
      <div className="absolute bottom-2 left-2 right-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
              {isLocal ? 'You' : participant.name}
            </span>
            {participant.isSpeaking && (
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            )}
          </div>
          
          <div className="flex items-center space-x-1">
            {!participant.audio && (
              <div className="bg-red-600 p-1 rounded">
                <MicOff className="w-3 h-3 text-white" />
              </div>
            )}
            {!participant.video && !isLocal && (
              <div className="bg-red-600 p-1 rounded">
                <VideoOff className="w-3 h-3 text-white" />
              </div>
            )}
            {participant.connectionQuality && (
              <div className={`w-2 h-2 rounded-full ${getConnectionQualityColor(participant.connectionQuality)}`}></div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  const GridView = () => (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 h-full">
      <VideoTile participant={{ name: 'You', video: localVideo, audio: localAudio }} isLocal={true} />
      {participants.map(participant => (
        <VideoTile key={participant.id} participant={participant} />
      ))}
    </div>
  );

  const SpeakerView = () => {
    const activeSpeaker = participants.find(p => p.isSpeaking) || participants[0];
    const otherParticipants = participants.filter(p => p.id !== activeSpeaker?.id);
    
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 mb-4">
          {activeSpeaker && <VideoTile participant={activeSpeaker} className="h-full" />}
        </div>
        <div className="flex space-x-2 h-24">
          <VideoTile 
            participant={{ name: 'You', video: localVideo, audio: localAudio }} 
            isLocal={true} 
            className="w-32" 
          />
          {otherParticipants.map(participant => (
            <VideoTile key={participant.id} participant={participant} className="w-32" />
          ))}
        </div>
      </div>
    );
  };

  const PresentationView = () => (
    <div className="h-full flex">
      <div className="flex-1 mr-4">
        {/* Screen share content would go here */}
        <div className="w-full h-full bg-gray-800 rounded-lg flex items-center justify-center">
          <div className="text-center text-white">
            <Monitor className="w-16 h-16 mx-auto mb-4" />
            <p className="text-lg">Screen Share Active</p>
            <p className="text-sm text-gray-400">Shared by John Smith</p>
          </div>
        </div>
      </div>
      <div className="w-64 flex flex-col space-y-2">
        <VideoTile 
          participant={{ name: 'You', video: localVideo, audio: localAudio }} 
          isLocal={true} 
          className="h-32" 
        />
        {participants.map(participant => (
          <VideoTile key={participant.id} participant={participant} className="h-32" />
        ))}
      </div>
    </div>
  );

  return (
    <div className="h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-white text-lg font-semibold">Property Review Meeting</h1>
          <span className="text-green-400 text-sm flex items-center">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
            Live • {participants.length + 1} participants
          </span>
        </div>
        
        <div className="flex items-center space-x-4">
          {isRecording && (
            <div className="flex items-center space-x-2 text-red-400">
              <div className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></div>
              <span className="text-sm">Recording</span>
            </div>
          )}
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-600' : 'bg-gray-700'} text-white hover:bg-blue-700`}
            >
              <Grid3x3 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('speaker')}
              className={`p-2 rounded ${viewMode === 'speaker' ? 'bg-blue-600' : 'bg-gray-700'} text-white hover:bg-blue-700`}
            >
              <Users className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Video Area */}
      <div className="flex-1 p-6 relative">
        {viewMode === 'grid' && <GridView />}
        {viewMode === 'speaker' && <SpeakerView />}
        {viewMode === 'presentation' && <PresentationView />}
      </div>

      {/* Controls */}
      <div className="bg-gray-800 px-6 py-4">
        <div className="flex items-center justify-center space-x-4">
          <button
            onClick={toggleAudio}
            className={`p-3 rounded-full ${localAudio ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-600 hover:bg-red-700'} text-white transition-colors`}
          >
            {localAudio ? <Mic className="w-5 h-5" /> : <MicOff className="w-5 h-5" />}
          </button>
          
          <button
            onClick={toggleVideo}
            className={`p-3 rounded-full ${localVideo ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-600 hover:bg-red-700'} text-white transition-colors`}
          >
            {localVideo ? <Video className="w-5 h-5" /> : <VideoOff className="w-5 h-5" />}
          </button>
          
          <button
            onClick={toggleScreenShare}
            className={`p-3 rounded-full ${isScreenSharing ? 'bg-blue-600 hover:bg-blue-700' : 'bg-gray-700 hover:bg-gray-600'} text-white transition-colors`}
          >
            <Share className="w-5 h-5" />
          </button>
          
          <button
            onClick={toggleRecording}
            className={`p-3 rounded-full ${isRecording ? 'bg-red-600 hover:bg-red-700' : 'bg-gray-700 hover:bg-gray-600'} text-white transition-colors`}
          >
            {isRecording ? <StopCircle className="w-5 h-5" /> : <Record className="w-5 h-5" />}
          </button>
          
          <button
            onClick={() => setChatVisible(!chatVisible)}
            className="p-3 rounded-full bg-gray-700 hover:bg-gray-600 text-white transition-colors relative"
          >
            <MessageSquare className="w-5 h-5" />
            {chatMessages.length > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {chatMessages.length}
              </span>
            )}
          </button>
          
          <button
            onClick={toggleFullscreen}
            className="p-3 rounded-full bg-gray-700 hover:bg-gray-600 text-white transition-colors"
          >
            {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
          </button>
          
          <button
            onClick={onEndCall}
            className="p-3 rounded-full bg-red-600 hover:bg-red-700 text-white transition-colors"
          >
            <PhoneOff className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Chat Sidebar */}
      {chatVisible && (
        <div className="fixed right-0 top-0 h-full w-80 bg-white dark:bg-gray-800 shadow-lg border-l border-gray-200 dark:border-gray-700 flex flex-col z-50">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900 dark:text-white">Meeting Chat</h3>
              <button
                onClick={() => setChatVisible(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                ✕
              </button>
            </div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.map(message => (
              <div key={message.id} className="space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-sm text-gray-900 dark:text-white">{message.sender}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{formatTime(message.timestamp)}</span>
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300">{message.message}</p>
              </div>
            ))}
          </div>
          
          <div className="p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                placeholder="Type a message..."
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
              <button
                onClick={sendChatMessage}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Send
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoConferencing;
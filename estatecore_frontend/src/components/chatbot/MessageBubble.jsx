/**
 * Message Bubble Component for EstateCore Chatbot
 * 
 * Renders individual chat messages with different styles for user, bot, and system messages.
 * Supports rich content including text, files, and interactive elements.
 */

import React from 'react';
import { 
    User, 
    Bot, 
    AlertTriangle, 
    CheckCircle, 
    Info, 
    FileText, 
    Image, 
    Video,
    Download
} from 'lucide-react';

const MessageBubble = ({ message }) => {
    const { sender, content, timestamp, response_type, data, metadata } = message;
    
    // Parse timestamp
    const messageTime = new Date(timestamp);
    const timeString = messageTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    // Message styling based on sender
    const getMessageStyle = () => {
        switch (sender) {
            case 'user':
                return {
                    containerClass: 'flex justify-end',
                    bubbleClass: 'bg-blue-600 text-white rounded-lg rounded-br-sm px-4 py-2 max-w-xs lg:max-w-md',
                    icon: <User size={16} className=\"text-blue-600\" />
                };
            case 'bot':
                return {
                    containerClass: 'flex justify-start',
                    bubbleClass: 'bg-white border border-gray-200 text-gray-800 rounded-lg rounded-bl-sm px-4 py-2 max-w-xs lg:max-w-md shadow-sm',
                    icon: <Bot size={16} className=\"text-green-600\" />
                };
            case 'system':
                return {
                    containerClass: 'flex justify-center',
                    bubbleClass: 'bg-gray-100 text-gray-600 rounded-lg px-3 py-2 max-w-xs lg:max-w-md text-sm',
                    icon: getSystemIcon(data?.type)
                };
            default:
                return {
                    containerClass: 'flex justify-start',
                    bubbleClass: 'bg-gray-100 text-gray-800 rounded-lg px-4 py-2 max-w-xs lg:max-w-md',
                    icon: <Info size={16} className=\"text-gray-600\" />
                };
        }
    };
    
    // Get system message icon based on type
    const getSystemIcon = (type) => {
        switch (type) {
            case 'error':
                return <AlertTriangle size={16} className=\"text-red-500\" />;
            case 'success':
                return <CheckCircle size={16} className=\"text-green-500\" />;
            case 'warning':
                return <AlertTriangle size={16} className=\"text-yellow-500\" />;
            default:
                return <Info size={16} className=\"text-blue-500\" />;
        }
    };
    
    // Render file content
    const renderFileContent = () => {
        if (!data || response_type !== 'file') return null;
        
        const { file_name, file_type, file_url } = data;\n        \n        const getFileIcon = () => {\n            if (file_type.startsWith('image/')) {\n                return <Image size={20} className=\"text-green-600\" />;\n            } else if (file_type.startsWith('video/')) {\n                return <Video size={20} className=\"text-blue-600\" />;\n            } else {\n                return <FileText size={20} className=\"text-gray-600\" />;\n            }\n        };\n        \n        return (\n            <div className=\"mt-2 p-3 bg-gray-50 rounded-lg border border-gray-200\">\n                <div className=\"flex items-center space-x-3\">\n                    {getFileIcon()}\n                    <div className=\"flex-1 min-w-0\">\n                        <p className=\"text-sm font-medium text-gray-900 truncate\">\n                            {file_name}\n                        </p>\n                        <p className=\"text-xs text-gray-500\">\n                            {file_type} • {formatFileSize(data.file_size)}\n                        </p>\n                    </div>\n                    {file_url && (\n                        <a\n                            href={file_url}\n                            download={file_name}\n                            className=\"text-blue-600 hover:text-blue-700 transition-colors\"\n                            aria-label=\"Download file\"\n                        >\n                            <Download size={16} />\n                        </a>\n                    )}\n                </div>\n                \n                {/* Image preview */}\n                {file_type.startsWith('image/') && file_url && (\n                    <div className=\"mt-2\">\n                        <img\n                            src={file_url}\n                            alt={file_name}\n                            className=\"max-w-full h-auto rounded-lg cursor-pointer\"\n                            onClick={() => window.open(file_url, '_blank')}\n                        />\n                    </div>\n                )}\n            </div>\n        );\n    };\n    \n    // Render rich content based on response type\n    const renderContent = () => {\n        switch (response_type) {\n            case 'card':\n                return renderCard();\n            case 'file':\n                return (\n                    <>\n                        <p className=\"text-sm\">{content}</p>\n                        {renderFileContent()}\n                    </>\n                );\n            default:\n                return (\n                    <div className=\"whitespace-pre-wrap break-words\">\n                        {formatMessageText(content)}\n                    </div>\n                );\n        }\n    };\n    \n    // Render card content\n    const renderCard = () => {\n        if (!data) return <p className=\"text-sm\">{content}</p>;\n        \n        return (\n            <div className=\"space-y-2\">\n                {data.title && (\n                    <h4 className=\"font-semibold text-sm\">{data.title}</h4>\n                )}\n                {data.description && (\n                    <p className=\"text-sm\">{data.description}</p>\n                )}\n                {data.buttons && data.buttons.length > 0 && (\n                    <div className=\"space-y-1\">\n                        {data.buttons.map((button, index) => (\n                            <button\n                                key={index}\n                                onClick={() => handleButtonClick(button)}\n                                className=\"block w-full text-left px-3 py-2 text-sm bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-md transition-colors\"\n                            >\n                                {button.title}\n                            </button>\n                        ))}\n                    </div>\n                )}\n            </div>\n        );\n    };\n    \n    // Handle button clicks in card messages\n    const handleButtonClick = (button) => {\n        if (button.type === 'url' && button.url) {\n            window.open(button.url, '_blank');\n        } else if (button.type === 'postback' && button.payload) {\n            // Emit button click event\n            const event = new CustomEvent('chatbot:button-click', {\n                detail: { payload: button.payload, title: button.title }\n            });\n            window.dispatchEvent(event);\n        }\n    };\n    \n    // Format message text (support for basic markdown-like formatting)\n    const formatMessageText = (text) => {\n        if (!text) return '';\n        \n        // Convert URLs to clickable links\n        const urlRegex = /(https?:\\/\\/[^\\s]+)/g;\n        const parts = text.split(urlRegex);\n        \n        return parts.map((part, index) => {\n            if (part.match(urlRegex)) {\n                return (\n                    <a\n                        key={index}\n                        href={part}\n                        target=\"_blank\"\n                        rel=\"noopener noreferrer\"\n                        className=\"text-blue-600 hover:text-blue-700 underline\"\n                    >\n                        {part}\n                    </a>\n                );\n            }\n            return part;\n        });\n    };\n    \n    // Format file size\n    const formatFileSize = (bytes) => {\n        if (!bytes) return 'Unknown size';\n        \n        const sizes = ['Bytes', 'KB', 'MB', 'GB'];\n        if (bytes === 0) return '0 Bytes';\n        \n        const i = Math.floor(Math.log(bytes) / Math.log(1024));\n        return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];\n    };\n    \n    const { containerClass, bubbleClass, icon } = getMessageStyle();\n    \n    return (\n        <div className={containerClass}>\n            <div className=\"flex items-start space-x-2 max-w-full\">\n                {/* Avatar/Icon */}\n                {sender !== 'system' && (\n                    <div className=\"flex-shrink-0 mt-1\">\n                        <div className=\"w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center\">\n                            {icon}\n                        </div>\n                    </div>\n                )}\n                \n                {/* Message Content */}\n                <div className=\"flex-1 min-w-0\">\n                    <div className={bubbleClass}>\n                        {renderContent()}\n                    </div>\n                    \n                    {/* Timestamp and metadata */}\n                    <div className=\"flex items-center justify-between mt-1 px-1\">\n                        <span className=\"text-xs text-gray-400\">\n                            {timeString}\n                        </span>\n                        \n                        {/* Metadata indicators */}\n                        {metadata && (\n                            <div className=\"flex items-center space-x-2\">\n                                {metadata.escalated && (\n                                    <span className=\"text-xs text-orange-500\" title=\"Escalated to human agent\">\n                                        🚀 Escalated\n                                    </span>\n                                )}\n                                {metadata.confidence && metadata.confidence < 0.7 && (\n                                    <span className=\"text-xs text-yellow-500\" title=\"Low confidence\">\n                                        ⚠️\n                                    </span>\n                                )}\n                                {metadata.intent && sender === 'user' && (\n                                    <span \n                                        className=\"text-xs text-gray-400\" \n                                        title={`Intent: ${metadata.intent} (${(metadata.confidence * 100).toFixed(0)}%)`}\n                                    >\n                                        🎯\n                                    </span>\n                                )}\n                            </div>\n                        )}\n                    </div>\n                </div>\n            </div>\n        </div>\n    );\n};\n\nexport default MessageBubble;"
import React, { useState, useRef, useEffect } from 'react';
import ChatbotInterface from './components/ChatbotInterface';
import './App.css';

function App() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: "Good morning. I can help you send meeting invitations. What's on your mind?",
    }
  ]);

  const [awaitingResponse, setAwaitingResponse] = useState(false);

  const handleSendMessage = (userMessage) => {
    // Add user message
    const newUserMessage = {
      id: Date.now(),
      type: 'user',
      text: userMessage,
    };

    setMessages(prev => [...prev, newUserMessage]);
    setAwaitingResponse(true);

    // Simulate agent processing
    setTimeout(() => {
      const lowerMsg = userMessage.toLowerCase();
      
      if (lowerMsg.includes('invite') || lowerMsg.includes('meeting') || lowerMsg.includes('calendar')) {
        const mockInvitation = generateMockInvitation(userMessage);
        
        const botResponse = {
          id: Date.now() + 1,
          type: 'bot',
          text: `Perfect! Sending invitation to ${mockInvitation.recipient.name} for "${mockInvitation.title}" on ${formatDate(mockInvitation.startTime)}.`,
        };
        
        setMessages(prev => [...prev, botResponse]);
        setTimeout(() => {
          const sentMessage = {
            id: Date.now() + 2,
            type: 'bot',
            text: "✓ Invitation sent to Google Calendar. Waiting for response...",
          };
          setMessages(prev => [...prev, sentMessage]);
        }, 900);
      } else {
        const botResponse = {
          id: Date.now() + 1,
          type: 'bot',
          text: "Try asking me to invite someone to a meeting. For example: 'Invite Sarah to a 2pm meeting tomorrow'",
        };
        
        setMessages(prev => [...prev, botResponse]);
      }
      
      setAwaitingResponse(false);
    }, 800);
  };

  const generateMockInvitation = (userMessage) => {
    const recipients = [
      { name: 'Sarah Chen', email: 'sarah@company.com' },
      { name: 'John Developer', email: 'john@company.com' },
      { name: 'Alex Morgan', email: 'alex@company.com' },
    ];

    const titles = ['Team Sync', 'Project Review', '1:1', 'Strategy Meeting', 'Design Review'];
    const randomRecipient = recipients[Math.floor(Math.random() * recipients.length)];
    const randomTitle = titles[Math.floor(Math.random() * titles.length)];
    const startTime = new Date(Date.now() + Math.random() * 7 * 24 * 60 * 60 * 1000);

    return {
      id: `inv_${Date.now()}`,
      title: randomTitle,
      startTime: startTime.toISOString(),
      duration: 30,
      recipient: randomRecipient,
      status: 'pending',
    };
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  return (
    <div className="app-container">
      <div className="app-content">
        <ChatbotInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={awaitingResponse}
        />
      </div>
    </div>
  );
}

export default App;

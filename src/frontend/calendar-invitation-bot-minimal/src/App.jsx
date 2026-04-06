import React, { useState } from "react";
import ChatbotInterface from "./ChatbotInterface";

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // 🔥 SEND MESSAGE TO BACKEND
  const handleSendMessage = async (text) => {
    const userMessage = {
      id: Date.now(),
      type: "user",
      text: text,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
        }),
      });

      const data = await res.json();

      const botMessage = {
        id: Date.now() + 1,
        type: "bot",
        text: data.reply || "No response",
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      const errorMessage = {
        id: Date.now() + 1,
        type: "bot",
        text: "❌ Cannot connect to backend",
      };

      setMessages((prev) => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  return (
    <ChatbotInterface
      messages={messages}
      onSendMessage={handleSendMessage}
      isLoading={isLoading}
    />
  );
}

export default App;
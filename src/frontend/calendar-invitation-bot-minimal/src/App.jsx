import React, { useState } from "react";
import ChatbotInterface from "./components/ChatbotInterface";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const quickPrompts = [
    "Book a meeting tomorrow at 9am with alex@company.com",
    "Check availability for Friday 2pm to 3pm",
    "Schedule a 30-minute sync today at 4pm",
  ];

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
      const res = await fetch("/api/chat", {
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
        text: "Cannot connect to backend.",
      };

      setMessages((prev) => [...prev, errorMessage]);
    }

    setIsLoading(false);
  };

  return (
    <div className="app-shell">
      <header className="app-hero">
        <div className="hero-copy">
          <div className="hero-pill">Live calendar agent</div>
          <h1>Book meetings without the back-and-forth.</h1>
          <p>
            A focused scheduling assistant that checks availability and books
            meetings in seconds. Keep it short, clear, and on your calendar.
          </p>
          <div className="hero-actions">
            <button
              className="hero-button ghost"
              onClick={() => handleSendMessage("Book a meeting tomorrow at 10am")}
              disabled={isLoading}
            >
              Try a demo prompt
            </button>
            <button
              className="hero-button"
              onClick={() => handleSendMessage("Check availability for today at 3pm")}
              disabled={isLoading}
            >
              Check availability
            </button>
          </div>
        </div>
        <div className="hero-card">
          <div className="hero-card-title">Today at a glance</div>
          <div className="hero-metrics">
            <div className="hero-metric">
              <span className="metric-label">Timezone</span>
              <span className="metric-value">Asia/Ho_Chi_Minh</span>
            </div>
            <div className="hero-metric">
              <span className="metric-label">Avg response</span>
              <span className="metric-value">2.4s</span>
            </div>
            <div className="hero-metric">
              <span className="metric-label">Next available</span>
              <span className="metric-value">Tomorrow 09:00</span>
            </div>
          </div>
          <div className="hero-card-note">
            Tip: Use ISO times for precise scheduling.
          </div>
        </div>
      </header>

      <main className="app-main">
        <section className="chat-panel">
          <div className="prompt-row">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                className="prompt-chip"
                onClick={() => handleSendMessage(prompt)}
                disabled={isLoading}
              >
                {prompt}
              </button>
            ))}
          </div>
          <ChatbotInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </section>
        <aside className="insights-panel">
          <div className="insight-card">
            <div className="insight-title">Smart rules</div>
            <p>
              The agent verifies time ranges before booking and confirms if the
              slot is unavailable.
            </p>
          </div>
          <div className="insight-card">
            <div className="insight-title">Signal status</div>
            <p>
              Keep the backend online to enable availability checks and booking
              actions.
            </p>
          </div>
          <div className="insight-card highlight">
            <div className="insight-title">Suggested format</div>
            <p>
              “Book a meeting on 2026-04-07 at 14:00 for 30 minutes.”
            </p>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;

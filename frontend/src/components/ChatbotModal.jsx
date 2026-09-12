import { useState, useRef, useEffect } from "react";
import axios from "axios";

import { API_URL } from "../apiConfig";

const QUICK_PROMPTS = [
  "What was my platelet count?",
  "Explain my blood test results",
  "What does PDW mean?",
  "When should I go to the hospital?",
  "What foods/fluids help recovery?",
  "Can you diagnose if I have dengue?",
];

export default function ChatbotModal({ patientContext }) {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I am your **Nexus AI Health Assistant**. You can ask me questions about your blood test results, platelet counts, dengue symptoms, or when to seek medical attention.\n\n*Note: I provide educational screening support only and cannot diagnose illness.*",
    },
  ]);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      setTimeout(() => inputRef.current?.focus(), 150);
    }
  }, [isOpen, messages]);

  const handleSendMessage = async (textToSend) => {
    const userMsg = textToSend || input.trim();
    if (!userMsg || loading) return;

    const newMessages = [...messages, { role: "user", content: userMsg }];
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    try {
      const payload = {
        message: userMsg,
        context: patientContext || {},
        history: newMessages.slice(-6),
      };

      const res = await axios.post(`${API_URL}/api/chat`, payload);
      setMessages([...newMessages, { role: "assistant", content: res.data.response }]);
    } catch (err) {
      setMessages([
        ...newMessages,
        {
          role: "assistant",
          content:
            "⚠️ I'm having trouble connecting to the health assistant service right now. Please ensure the backend server is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Basic markdown-like parser for bold and lists
  const formatText = (text) => {
    return text.split("\n").map((line, idx) => {
      let formatted = line;
      // Bold **text**
      const parts = formatted.split(/(\*\*.*?\*\*)/g);
      return (
        <p key={idx} className={line.startsWith("•") || line.startsWith("1.") ? "chat-list-line" : "chat-para"}>
          {parts.map((part, pIdx) => {
            if (part.startsWith("**") && part.endsWith("**")) {
              return <strong key={pIdx}>{part.slice(2, -2)}</strong>;
            }
            if (part.startsWith("*") && part.endsWith("*")) {
              return <em key={pIdx}>{part.slice(1, -1)}</em>;
            }
            return part;
          })}
        </p>
      );
    });
  };

  return (
    <>
      {/* Floating trigger button */}
      <button
        className={`floating-chat-trigger ${isOpen ? "chat-open" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Open AI Health Assistant"
        title="Chat with AI Health Assistant"
      >
        {isOpen ? (
          <span className="close-x">✕</span>
        ) : (
          <>
            <span className="chat-bubble-icon">💬</span>
            <span className="chat-trigger-label">AI Health Assistant</span>
            <span className="chat-online-dot" />
          </>
        )}
      </button>

      {/* Floating Chat Drawer / Window */}
      {isOpen && (
        <div className="chat-modal-window">
          {/* Header */}
          <div className="chat-modal-header">
            <div className="chat-modal-brand">
              <div className="assistant-avatar">🤖</div>
              <div>
                <h4 className="assistant-title">Nexus AI Assistant</h4>
                <span className="assistant-status">Online · Context Aware</span>
              </div>
            </div>
            <button className="chat-close-btn" onClick={() => setIsOpen(false)}>
              ✕
            </button>
          </div>

          {/* Context Banner */}
          {patientContext && patientContext.parameters && (
            <div className="chat-context-badge">
              <span>🩺 Report Loaded: PLT {patientContext.parameters.platelet_count?.toLocaleString() || "—"} cells/µL</span>
              {patientContext.prediction?.risk_level && (
                <span className="risk-mini-tag">{patientContext.prediction.risk_level} Risk</span>
              )}
            </div>
          )}

          {/* Messages list */}
          <div className="chat-modal-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-msg-row ${m.role}`}>
                <div className={`chat-bubble-content ${m.role}`}>
                  {formatText(m.content)}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-msg-row assistant">
                <div className="chat-bubble-content assistant typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts Chips */}
          <div className="quick-prompts-bar">
            {QUICK_PROMPTS.map((prompt, idx) => (
              <button
                key={idx}
                className="prompt-chip"
                onClick={() => handleSendMessage(prompt)}
                disabled={loading}
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Bar */}
          <div className="chat-modal-input-bar">
            <input
              ref={inputRef}
              type="text"
              className="chat-text-input"
              placeholder="Ask about platelets, dengue symptoms, diet..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button
              className="chat-send-btn"
              onClick={() => handleSendMessage()}
              disabled={!input.trim() || loading}
            >
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  );
}

import { useState, useEffect, useRef } from "react";
import axios from "axios";

import { API_URL } from "../apiConfig";

const QUESTIONS = [
  {
    id: "age", field: "age",
    label: "What is the patient's age?",
    type: "number", placeholder: "e.g. 35", unit: "years", icon: "👤",
    hint: "Enter age between 1–120",
    validate: (v) => v > 0 && v <= 120,
    errorMsg: "Please enter a valid age (1–120)",
  },
  {
    id: "sex", field: "sex",
    label: "What is the patient's biological sex?",
    type: "select",
    options: [{ value: "male", label: "Male" }, { value: "female", label: "Female" }, { value: "child", label: "Child (under 12)" }],
    icon: "🧬", hint: "Select the biological sex",
    validate: (v) => !!v, errorMsg: "Please select a sex",
  },
  {
    id: "haemoglobin", field: "haemoglobin",
    label: "What is the Haemoglobin level?",
    type: "number", placeholder: "e.g. 12.5", unit: "g/dL", icon: "🩸",
    hint: "Normal range: 11–17 g/dL",
    validate: (v) => v > 0 && v <= 30,
    errorMsg: "Please enter a valid haemoglobin level (1–30)",
  },
  {
    id: "wbc_count", field: "wbc_count",
    label: "What is the WBC (White Blood Cell) Count?",
    type: "number", placeholder: "e.g. 3200", unit: "cells/µL", icon: "🔬",
    hint: "Normal range: 4,000–11,000 cells/µL. Low WBC is common in dengue.",
    validate: (v) => v > 0 && v <= 100000,
    errorMsg: "Please enter a valid WBC count",
  },
  {
    id: "platelet_count", field: "platelet_count",
    label: "What is the Platelet Count?",
    type: "number", placeholder: "e.g. 45000", unit: "cells/µL", icon: "💊",
    hint: "Normal range: 150,000–400,000. Below 100,000 is a warning sign.",
    validate: (v) => v > 0 && v <= 1000000,
    errorMsg: "Please enter a valid platelet count",
  },
  {
    id: "pdw", field: "pdw",
    label: "What is the PDW (Platelet Distribution Width)?",
    type: "number", placeholder: "e.g. 14.5", unit: "%", icon: "📊",
    hint: "Normal range: 9–17%. Elevated PDW may indicate platelet abnormality.",
    validate: (v) => v > 0 && v <= 250,
    errorMsg: "Please enter a valid PDW value",
  },
  {
    id: "rbc_panel", field: "rbc_panel",
    label: "Is the RBC Panel result abnormal?",
    type: "select",
    options: [{ value: "1", label: "Yes — Abnormal" }, { value: "0", label: "No — Normal" }],
    icon: "🧪", hint: "Based on the lab RBC panel result",
    validate: (v) => v !== "", errorMsg: "Please select an option",
  },
  {
    id: "differential_count", field: "differential_count",
    label: "Is the Differential Count result abnormal?",
    type: "select",
    options: [{ value: "1", label: "Yes — Abnormal" }, { value: "0", label: "No — Normal" }],
    icon: "🧫", hint: "Differential count assesses types of white blood cells",
    validate: (v) => v !== "", errorMsg: "Please select an option",
  },
];

export default function Questionnaire({ onResult }) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [currentValue, setCurrentValue] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    { type: "bot", text: "Hello! I'm your AI health assistant. I'll analyze your blood test parameters to assess dengue risk. Let's begin with a few questions." },
  ]);
  const inputRef = useRef(null);
  const chatEndRef = useRef(null);
  const q = QUESTIONS[step];

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    setTimeout(() => inputRef.current?.focus(), 100);
  }, [messages]);

  const addMessage = (type, text) => setMessages((prev) => [...prev, { type, text }]);

  const handleNext = async () => {
    const val = currentValue;
    if (!q.validate(q.type === "number" ? parseFloat(val) : val)) {
      setError(q.errorMsg);
      return;
    }
    setError("");
    const parsedVal = q.type === "number" ? parseFloat(val) : val;
    const newAnswers = { ...answers, [q.field]: parsedVal };
    setAnswers(newAnswers);
    const displayVal = q.type === "select"
      ? q.options.find((o) => o.value === val)?.label
      : `${val}${q.unit ? " " + q.unit : ""}`;
    addMessage("user", displayVal);
    setCurrentValue("");

    if (step < QUESTIONS.length - 1) {
      setTimeout(() => { addMessage("bot", QUESTIONS[step + 1].label); setStep(step + 1); }, 400);
    } else {
      setTimeout(() => { addMessage("bot", "Analyzing your blood parameters with the AI model... 🔍"); }, 400);
      setLoading(true);
      try {
        const payload = {
          ...newAnswers,
          rbc_panel: parseInt(newAnswers.rbc_panel),
          differential_count: parseInt(newAnswers.differential_count),
        };
        const res = await axios.post(`${API_URL}/predict`, payload);
        onResult(res.data, newAnswers);
      } catch (err) {
        addMessage("bot", "⚠️ Could not connect to the prediction server. Make sure the backend is running on port 8000.");
        setLoading(false);
      }
    }
  };

  const handleKeyDown = (e) => { if (e.key === "Enter") handleNext(); };
  const progress = Math.round((step / QUESTIONS.length) * 100);

  return (
    <div className="chat-container">
      <div className="progress-bar-wrap">
        <div className="progress-bar-track">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }} />
        </div>
        <span className="progress-label">{step}/{QUESTIONS.length} questions</span>
      </div>

      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-bubble-wrap ${msg.type}`}>
            {msg.type === "bot" && <div className="avatar bot-avatar">AI</div>}
            <div className={`chat-bubble ${msg.type}`}>{msg.text}</div>
            {msg.type === "user" && <div className="avatar user-avatar">You</div>}
          </div>
        ))}

        {!loading && step < QUESTIONS.length && (
          <div className="input-card">
            <div className="input-card-header">
              <span className="q-icon">{q.icon}</span>
              <span className="q-hint">{q.hint}</span>
            </div>
            {q.type === "select" ? (
              <div className="select-options">
                {q.options.map((opt) => (
                  <button key={opt.value}
                    className={`option-btn ${currentValue === opt.value ? "selected" : ""}`}
                    onClick={() => setCurrentValue(opt.value)}>
                    {opt.label}
                  </button>
                ))}
              </div>
            ) : (
              <div className="number-input-wrap">
                <input ref={inputRef} type="number" className="number-input"
                  placeholder={q.placeholder} value={currentValue}
                  onChange={(e) => setCurrentValue(e.target.value)}
                  onKeyDown={handleKeyDown} />
                {q.unit && <span className="unit-label">{q.unit}</span>}
              </div>
            )}
            {error && <p className="error-msg">⚠️ {error}</p>}
            <button className="next-btn" onClick={handleNext}
              disabled={!currentValue && currentValue !== 0}>
              {step === QUESTIONS.length - 1 ? "Analyze Risk →" : "Next →"}
            </button>
          </div>
        )}

        {loading && (
          <div className="loading-card">
            <div className="spinner" />
            <p>Running AI analysis...</p>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
}

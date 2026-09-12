import { useEffect, useState } from "react";
import axios from "axios";
import FeatureImportanceChart from "./FeatureImportanceChart";
import ModelMetrics from "./ModelMetrics";
import BloodVisualizer from "./BloodVisualizer";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const RISK_CONFIG = {
  Low: {
    color: "#22c55e",
    bg: "var(--risk-low-bg)",
    border: "var(--risk-low-border)",
    emoji: "✅",
    label: "Low Dengue Risk",
    desc: "Your blood parameters are within acceptable baseline ranges. Stay well hydrated and continue monitoring your temperature.",
  },
  Moderate: {
    color: "#f59e0b",
    bg: "var(--risk-mod-bg)",
    border: "var(--risk-mod-border)",
    emoji: "⚠️",
    label: "Moderate Dengue Risk",
    desc: "Some blood parameters deviate from normal, indicating possible dengue exposure or early phase. Consult a doctor and watch for symptoms.",
  },
  High: {
    color: "#ef4444",
    bg: "var(--risk-high-bg)",
    border: "var(--risk-high-border)",
    emoji: "🚨",
    label: "High Dengue Risk",
    desc: "Your blood parameters strongly align with patterns seen in active dengue infection. Seek medical attention promptly.",
  },
};

const INFO_PANELS = [
  {
    icon: "🌡️",
    title: "Symptoms to Watch",
    color: "#ef4444",
    items: [
      "High persistent fever (above 38.5°C / 101.3°F)",
      "Severe retro-orbital headache (behind the eyes)",
      "Muscle and bone aching ('breakbone' pain)",
      "Skin rash appearing 2–5 days after onset of fever",
      "Nausea, loss of appetite, and extreme fatigue",
    ],
  },
  {
    icon: "🏥",
    title: "When to Go to Hospital Immediately",
    color: "#f97316",
    items: [
      "Platelet count dropping below 50,000 cells/µL",
      "Any spontaneous bleeding — gums, nose, vomit, or black stools",
      "Severe, persistent abdominal tenderness or pain",
      "Inability to keep fluids down (persistent vomiting)",
      "Dizziness, confusion, difficulty breathing, or cold extremities",
    ],
  },
  {
    icon: "💧",
    title: "Hydration & Critical Care",
    color: "#3b82f6",
    items: [
      "Maintain high fluid intake (2.5–3 Litres/day) with water, ORS, and coconut water",
      "Papaya leaf extract and pomegranate support platelet count and recovery",
      "⚠️ AVOID Aspirin, Ibuprofen, and NSAIDs — they increase internal bleeding risks!",
      "Use only Paracetamol under qualified medical guidance for fever",
    ],
  },
  {
    icon: "🥗",
    title: "Nutrition & Recovery",
    color: "#22c55e",
    items: [
      "Kiwi, guava, and oranges — rich in Vitamin C and antioxidants",
      "Spinach and leafy greens for folate and iron",
      "Bland, light meals: rice porridge, lentil soups, and boiled vegetables",
      "Small, frequent meals to minimize nausea",
    ],
  },
];

export default function ResultDashboard({ result, answers, onReset }) {
  const [animatedProb, setAnimatedProb] = useState(0);
  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  const risk = RISK_CONFIG[result.risk_level] || RISK_CONFIG["Low"];
  const pct = Math.round(result.probability * 100);

  // Animate risk gauge
  useEffect(() => {
    let start = 0;
    const end = pct;
    const step = end / 50;
    const timer = setInterval(() => {
      start += step;
      if (start >= end) {
        setAnimatedProb(end);
        clearInterval(timer);
      } else {
        setAnimatedProb(Math.round(start));
      }
    }, 20);
    return () => clearInterval(timer);
  }, [pct]);

  const handleDownloadPdf = async () => {
    setDownloadingPdf(true);
    setDownloadError("");

    try {
      const payload = {
        patient: {
          name: answers.patient?.name || "Not Specified",
          age: answers.age,
          sex: answers.sex,
        },
        report_info: {
          filename: answers.report_info?.filename || "Screening_Report",
        },
        parameters: {
          haemoglobin: answers.haemoglobin,
          platelet_count: answers.platelet_count,
          pdw: answers.pdw,
          wbc_count: answers.wbc_count || 0,
        },
        prediction: {
          risk_level: result.risk_level,
          probability: result.probability,
          message: result.message,
        },
      };

      const response = await axios.post(`${API_URL}/api/generate-report`, payload, {
        responseType: "blob",
      });

      // Create download link
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `NexusAI_Report_${answers.patient?.name || "Patient"}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF generation failed:", err);
      setDownloadError("Could not generate PDF report. Make sure backend is running.");
    } finally {
      setDownloadingPdf(false);
    }
  };

  return (
    <div className="dashboard">
      {/* Top Header & Action Row */}
      <div className="dashboard-top-bar">
        <div>
          <span className="step-tag">Step 3 of 4: AI Screening & Analysis</span>
          <h2 className="dashboard-heading">Dengue Risk Assessment Results</h2>
        </div>
        <div className="dashboard-actions">
          <button
            className="download-pdf-btn"
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
          >
            {downloadingPdf ? (
              <>⏳ Generating PDF...</>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                  <polyline points="7 10 12 15 17 10"/>
                  <line x1="12" y1="15" x2="12" y2="3"/>
                </svg>
                Download Medical PDF Report
              </>
            )}
          </button>
          <button className="secondary-reset-btn" onClick={onReset}>
            ↺ New Assessment
          </button>
        </div>
      </div>

      {downloadError && <div className="pdf-error-banner">{downloadError}</div>}

      {/* Hero Risk Card */}
      <div className="risk-hero" style={{ borderColor: risk.border, background: risk.bg }}>
        <div className="risk-hero-left">
          <div className="risk-emoji">{risk.emoji}</div>
          <div>
            <h2 className="risk-label" style={{ color: risk.color }}>
              {risk.label}
            </h2>
            <p className="risk-desc">{risk.desc}</p>
            <div className="risk-meta-badge">
              <span>Model Prediction: <b>{result.dengue_positive ? "Positive Indication" : "Negative Indication"}</b></span>
              <span>·</span>
              <span>Confidence: <b>{animatedProb}%</b></span>
            </div>
          </div>
        </div>

        <div className="gauge-wrap">
          <svg className="gauge-svg" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="50" fill="none" stroke="var(--gauge-track)" strokeWidth="10" />
            <circle
              cx="60"
              cy="60"
              r="50"
              fill="none"
              stroke={risk.color}
              strokeWidth="10"
              strokeDasharray={`${(animatedProb / 100) * 314} 314`}
              strokeLinecap="round"
              transform="rotate(-90 60 60)"
              style={{ transition: "stroke-dasharray 0.05s linear" }}
            />
            <text x="60" y="56" textAnchor="middle" fontSize="22" fontWeight="bold" fill={risk.color}>
              {animatedProb}%
            </text>
            <text x="60" y="72" textAnchor="middle" fontSize="10" fill="var(--text-muted)">
              Risk Score
            </text>
          </svg>
        </div>
      </div>

      {/* Probability Gradient Bar */}
      <div className="prob-bar-section">
        <div className="prob-bar-labels">
          <span style={{ color: "#22c55e" }}>Low Risk (0–35%)</span>
          <span style={{ color: "#f59e0b" }}>Moderate (35–65%)</span>
          <span style={{ color: "#ef4444" }}>High Risk (65–100%)</span>
        </div>
        <div className="prob-bar-track">
          <div
            className="prob-bar-fill"
            style={{ width: `${animatedProb}%`, background: "linear-gradient(to right, #22c55e, #f59e0b, #ef4444)" }}
          />
          <div className="prob-bar-marker" style={{ left: `${animatedProb}%` }}>
            <div className="marker-dot" style={{ background: risk.color }} />
          </div>
        </div>
        <div className="prob-bar-scale">
          <span>0%</span>
          <span>35%</span>
          <span>65%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Patient Summary Demographics */}
      <div className="patient-summary">
        <h3 className="section-title">🩺 Patient Information</h3>
        <div className="patient-demographics-card">
          <div className="demo-item">
            <span className="demo-label">Patient Name:</span>
            <span className="demo-value">{answers.patient?.name || "Not Specified"}</span>
          </div>
          <div className="demo-item">
            <span className="demo-label">Age:</span>
            <span className="demo-value">{answers.age} Years</span>
          </div>
          <div className="demo-item">
            <span className="demo-label">Biological Sex:</span>
            <span className="demo-value" style={{ textTransform: "capitalize" }}>{answers.sex}</span>
          </div>
          <div className="demo-item">
            <span className="demo-label">Source Document:</span>
            <span className="demo-value">{answers.report_info?.filename || "Manual Input"}</span>
          </div>
        </div>
      </div>

      {/* Blood Test Spectrum Visualizer */}
      <BloodVisualizer
        parameters={{
          platelet_count: answers.platelet_count,
          haemoglobin: answers.haemoglobin,
          pdw: answers.pdw,
          wbc_count: answers.wbc_count,
        }}
      />

      {/* Feature Importance & Model Interpretability */}
      <FeatureImportanceChart data={result.feature_importance} />

      {/* Model Validation & Performance Metrics */}
      <ModelMetrics />

      {/* Clinical Guidance Info Panels */}
      <div className="info-panels-grid">
        {INFO_PANELS.map((panel) => (
          <div key={panel.title} className="info-panel">
            <div className="info-panel-header" style={{ borderLeftColor: panel.color }}>
              <span className="info-icon">{panel.icon}</span>
              <h3 className="info-title" style={{ color: panel.color }}>{panel.title}</h3>
            </div>
            <ul className="info-list">
              {panel.items.map((item, idx) => (
                <li key={idx} className="info-item">
                  <span className="info-dot" style={{ background: panel.color }} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      {/* Prominent Safety & Non-Diagnostic Disclaimer */}
      <div className="disclaimer">
        <div className="disclaimer-icon">⚕️</div>
        <div className="disclaimer-body">
          <strong>Important Clinical & Legal Notice</strong>
          <p>
            This application is an <b>AI-assisted screening and clinical decision support system</b> designed for research and educational purposes. It is <b>not a certified medical diagnostic device</b> and does not replace evaluation by a qualified medical doctor or laboratory diagnostic testing (such as NS1 antigen or Dengue IgM/IgG serology).
          </p>
        </div>
      </div>

      {/* Bottom Actions */}
      <div className="reset-wrap">
        <button className="download-pdf-btn large" onClick={handleDownloadPdf} disabled={downloadingPdf}>
          📄 Download Full Medical Summary (PDF)
        </button>
        <button className="reset-btn" onClick={onReset}>
          ← Start New Assessment
        </button>
      </div>
    </div>
  );
}

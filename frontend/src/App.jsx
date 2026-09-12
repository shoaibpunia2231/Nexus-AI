import { useState, useEffect, createContext, useContext } from "react";
import axios from "axios";
import Header from "./components/Header";
import LandingPage from "./components/LandingPage";
import SignInPage from "./components/SignInPage";
import SignUpPage from "./components/SignUpPage";
import TenantScreeningHistory from "./components/TenantScreeningHistory";
import ReportUpload from "./components/ReportUpload";
import ExtractedReview from "./components/ExtractedReview";
import Questionnaire from "./components/Questionnaire";
import ResultDashboard from "./components/ResultDashboard";
import ChatbotModal from "./components/ChatbotModal";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const ThemeContext = createContext({ theme: "dark", toggleTheme: () => {} });
export const useTheme = () => useContext(ThemeContext);

export default function App() {
  // Authentication State
  const [authSession, setAuthSession] = useState(() => {
    try {
      const stored = localStorage.getItem("nexus_auth");
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  // Top-Level Navigation Route: "LANDING", "SIGN_IN", "SIGN_UP", "APP", "HISTORY"
  const [route, setRoute] = useState(() => {
    return localStorage.getItem("nexus_auth") ? "APP" : "LANDING";
  });

  // Workspace Mode (inside "APP"): "UPLOAD", "REVIEW", "MANUAL", "RESULT"
  const [mode, setMode] = useState("UPLOAD");
  const [extractionData, setExtractionData] = useState(null);
  const [answers, setAnswers] = useState(null);
  const [result, setResult] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem("dg-theme") || "dark");
  const [predicting, setPredicting] = useState(false);
  const [predictionError, setPredictionError] = useState("");

  // Theme Sync
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("dg-theme", theme);
  }, [theme]);

  // Verify auth token on initial load
  useEffect(() => {
    const verifyToken = async () => {
      if (!authSession?.token) return;
      try {
        const res = await axios.get(`${API_URL}/api/auth/me`, {
          headers: { Authorization: `Bearer ${authSession.token}` },
        });
        // Refresh user and tenant metadata
        setAuthSession((prev) => ({
          ...prev,
          user: res.data.user,
          tenant: res.data.tenant,
        }));
      } catch (err) {
        console.warn("Session expired or invalid, signing out.");
        handleSignOut();
      }
    };
    verifyToken();
  }, []);

  const toggleTheme = () => setTheme((t) => (t === "dark" ? "light" : "dark"));

  // Auth Callbacks
  const handleAuthSuccess = (data) => {
    setAuthSession(data);
    localStorage.setItem("nexus_auth", JSON.stringify(data));
    setRoute("APP");
    setMode("UPLOAD");
  };

  const handleSignOut = () => {
    localStorage.removeItem("nexus_auth");
    setAuthSession(null);
    setResult(null);
    setAnswers(null);
    setExtractionData(null);
    setRoute("LANDING");
  };

  // 1. Report Upload complete -> go to review
  const handleExtractionComplete = (data) => {
    setExtractionData(data);
    setMode("REVIEW");
  };

  // 2. Extracted Data confirmed -> run ML prediction pipeline
  const handleConfirmReview = async (confirmedData) => {
    setPredicting(true);
    setPredictionError("");

    try {
      const payload = {
        age: confirmedData.patient.age,
        sex: confirmedData.patient.sex,
        haemoglobin: confirmedData.parameters.haemoglobin,
        platelet_count: confirmedData.parameters.platelet_count,
        pdw: confirmedData.parameters.pdw,
        wbc_count: confirmedData.parameters.wbc_count || 0,
        differential_count: confirmedData.parameters.differential_count || 1,
        rbc_panel: confirmedData.parameters.rbc_panel || 1,
        patient_name: confirmedData.patient.name || "Not Specified",
        source_filename: confirmedData.report_info?.filename || "Uploaded Report",
      };

      const headers = authSession?.token
        ? { Authorization: `Bearer ${authSession.token}` }
        : {};

      const res = await axios.post(`${API_URL}/predict`, payload, { headers });

      setResult(res.data);
      setAnswers({
        ...payload,
        patient: confirmedData.patient,
        report_info: confirmedData.report_info,
      });
      setMode("RESULT");
    } catch (err) {
      console.error("Prediction error:", err);
      const detail = err.response?.data?.detail || err.message;
      setPredictionError(`Screening failed: ${detail}. Please check backend connection.`);
    } finally {
      setPredicting(false);
    }
  };

  // 3. Manual Questionnaire complete (Original workflow)
  const handleManualResult = async (data, inputAnswers) => {
    setResult(data);
    setAnswers({
      ...inputAnswers,
      patient: { name: "Manual Patient", age: inputAnswers.age, sex: inputAnswers.sex },
      report_info: { filename: "Manual Entry" },
    });
    setMode("RESULT");
  };

  // 4. Reset flow
  const handleReset = () => {
    setResult(null);
    setAnswers(null);
    setExtractionData(null);
    setMode("UPLOAD");
  };

  // Patient context for chatbot
  const patientContext = {
    patient: answers?.patient || extractionData?.patient || null,
    parameters: answers
      ? {
          haemoglobin: answers.haemoglobin,
          platelet_count: answers.platelet_count,
          pdw: answers.pdw,
          wbc_count: answers.wbc_count,
        }
      : extractionData?.parameters
      ? {
          haemoglobin: extractionData.parameters.haemoglobin?.value,
          platelet_count: extractionData.parameters.platelet_count?.value,
          pdw: extractionData.parameters.pdw?.value,
          wbc_count: extractionData.parameters.wbc_count?.value,
        }
      : null,
    prediction: result
      ? {
          risk_level: result.risk_level,
          probability: result.probability,
          message: result.message,
        }
      : null,
  };

  // Public View: Landing Page
  if (route === "LANDING" && !authSession) {
    return (
      <ThemeContext.Provider value={{ theme, toggleTheme }}>
        <LandingPage onNavigate={setRoute} />
      </ThemeContext.Provider>
    );
  }

  // Public View: Sign In
  if (route === "SIGN_IN" && !authSession) {
    return (
      <ThemeContext.Provider value={{ theme, toggleTheme }}>
        <SignInPage onNavigate={setRoute} onAuthSuccess={handleAuthSuccess} />
      </ThemeContext.Provider>
    );
  }

  // Public View: Sign Up
  if (route === "SIGN_UP" && !authSession) {
    return (
      <ThemeContext.Provider value={{ theme, toggleTheme }}>
        <SignUpPage onNavigate={setRoute} onAuthSuccess={handleAuthSuccess} />
      </ThemeContext.Provider>
    );
  }

  // Authenticated View
  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <div className="app-root">
        <Header
          authSession={authSession}
          onSignOut={handleSignOut}
          onOpenHistory={() => setRoute("HISTORY")}
          onNavigate={(r) => setRoute(r)}
        />

        {/* View: Tenant Screening History Modal/Page */}
        {route === "HISTORY" ? (
          <main className="main-content">
            <TenantScreeningHistory
              token={authSession?.token}
              tenant={authSession?.tenant}
              user={authSession?.user}
              onClose={() => setRoute("APP")}
            />
          </main>
        ) : (
          <>
            {/* Navigation Tabs between Upload and Manual (only when not showing results) */}
            {mode !== "RESULT" && (
              <div className="nav-mode-bar">
                <button
                  className={`nav-tab-btn ${mode === "UPLOAD" || mode === "REVIEW" ? "active" : ""}`}
                  onClick={() => setMode("UPLOAD")}
                >
                  📄 Upload Blood Report (OCR)
                </button>
                <button
                  className={`nav-tab-btn ${mode === "MANUAL" ? "active" : ""}`}
                  onClick={() => setMode("MANUAL")}
                >
                  ✍️ Manual Questionnaire
                </button>
              </div>
            )}

            <main className="main-content">
              {predicting && (
                <div className="global-overlay-loading">
                  <div className="upload-spinner" />
                  <h3>Running Dengue Machine Learning Model...</h3>
                  <p>Analyzing blood parameters against clinical risk patterns</p>
                </div>
              )}

              {predictionError && (
                <div className="pdf-error-banner" style={{ marginBottom: "1rem" }}>
                  ⚠️ {predictionError}
                </div>
              )}

              {/* Mode 1: Upload */}
              {mode === "UPLOAD" && (
                <ReportUpload
                  onExtractionComplete={handleExtractionComplete}
                  onSwitchToManual={() => setMode("MANUAL")}
                />
              )}

              {/* Mode 2: Review & Confirm Extracted Data */}
              {mode === "REVIEW" && (
                <ExtractedReview
                  extractionData={extractionData}
                  onConfirm={handleConfirmReview}
                  onBack={() => setMode("UPLOAD")}
                />
              )}

              {/* Mode 3: Manual Step-by-Step Questionnaire */}
              {mode === "MANUAL" && (
                <Questionnaire onResult={handleManualResult} />
              )}

              {/* Mode 4: Full Prediction Dashboard */}
              {mode === "RESULT" && (
                <ResultDashboard
                  result={result}
                  answers={answers}
                  onReset={handleReset}
                />
              )}
            </main>
          </>
        )}

        {/* Floating Context-Aware Chatbot */}
        <ChatbotModal patientContext={patientContext} />
      </div>
    </ThemeContext.Provider>
  );
}

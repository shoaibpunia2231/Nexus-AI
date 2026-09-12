import { useState, useRef } from "react";
import axios from "axios";

import { API_URL } from "../apiConfig";

export default function ReportUpload({ onExtractionComplete, onSwitchToManual }) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState("");
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const validateAndProcessFile = (selectedFile) => {
    if (!selectedFile) return;

    const allowedTypes = ["application/pdf", "image/jpeg", "image/png", "image/jpg"];
    const ext = selectedFile.name.split(".").pop().toLowerCase();
    const validExts = ["pdf", "jpg", "jpeg", "png"];

    if (!allowedTypes.includes(selectedFile.type) && !validExts.includes(ext)) {
      setError("Unsupported format. Please upload a PDF document or a clear image (JPG/PNG).");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError("File size exceeds 10MB limit. Please upload a smaller file.");
      return;
    }

    setError("");
    setFile(selectedFile);
    uploadAndExtract(selectedFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndProcessFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      validateAndProcessFile(e.target.files[0]);
    }
  };

  const uploadAndExtract = async (fileToUpload) => {
    setLoading(true);
    setError("");
    setLoadingStep("Reading document and analyzing format...");

    const formData = new FormData();
    formData.append("file", fileToUpload);

    try {
      setTimeout(() => setLoadingStep("Detecting laboratory test names and values..."), 800);

      const res = await axios.post(`${API_URL}/api/extract-report`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      if (!res.data.success) {
        setError(res.data.error || "We could not read this report. Please upload a clearer PDF/image or enter the values manually.");
        setLoading(false);
        return;
      }

      setLoadingStep("Validating extracted parameters...");
      setTimeout(() => {
        setLoading(false);
        onExtractionComplete(res.data);
      }, 500);

    } catch (err) {
      setLoading(false);
      const detail = err.response?.data?.detail || err.message;
      setError(`Failed to extract report data: ${detail}. You can try again or enter values manually.`);
    }
  };

  // Quick test demo buttons
  const loadDemoData = (type) => {
    if (type === "dengue") {
      onExtractionComplete({
        success: true,
        filename: "demo_dengue_lab_report.pdf",
        patient: { name: "Arjun Verma", age: 29, sex: "male" },
        parameters: {
          haemoglobin: { value: 12.0, status: "Extracted", unit: "g/dL", reference_range: "12.0 - 17.5 g/dL" },
          platelet_count: { value: 45000, status: "Extracted", unit: "cells/µL", reference_range: "150,000 - 450,000 cells/µL" },
          pdw: { value: 16.5, status: "Extracted", unit: "%", reference_range: "9.0 - 17.0 %" },
          wbc_count: { value: 3100, status: "Extracted", unit: "cells/µL", reference_range: "4,000 - 11,000 cells/µL" },
        },
        extracted_count: 3,
        total_required: 3,
      });
    } else {
      onExtractionComplete({
        success: true,
        filename: "demo_healthy_routine_cbc.pdf",
        patient: { name: "Priya Sharma", age: 34, sex: "female" },
        parameters: {
          haemoglobin: { value: 14.2, status: "Extracted", unit: "g/dL", reference_range: "12.0 - 17.5 g/dL" },
          platelet_count: { value: 240000, status: "Extracted", unit: "cells/µL", reference_range: "150,000 - 450,000 cells/µL" },
          pdw: { value: 11.5, status: "Extracted", unit: "%", reference_range: "9.0 - 17.0 %" },
          wbc_count: { value: 6800, status: "Extracted", unit: "cells/µL", reference_range: "4,000 - 11,000 cells/µL" },
        },
        extracted_count: 3,
        total_required: 3,
      });
    }
  };

  return (
    <div className="upload-container">
      <div className="upload-hero">
        <span className="upload-pill-tag">Automated Medical OCR & Analysis</span>
        <h2 className="upload-heading">Upload Patient Blood Test Report</h2>
        <p className="upload-subtext">
          Upload your Complete Blood Count (CBC) or dengue laboratory report. Our system automatically parses
          haemoglobin, platelet count, and PDW for instant screening.
        </p>
      </div>

      <div
        className={`dropzone-card ${dragActive ? "drag-active" : ""}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !loading && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.jpg,.jpeg,.png"
          style={{ display: "none" }}
          onChange={handleChange}
        />

        {loading ? (
          <div className="upload-loading-state">
            <div className="upload-spinner" />
            <h4 className="loading-state-title">Processing Laboratory Report</h4>
            <p className="loading-state-step">{loadingStep}</p>
            <div className="scanning-pulse-bar" />
          </div>
        ) : (
          <div className="dropzone-content">
            <div className="dropzone-icon-wrap">
              <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="12" y1="18" x2="12" y2="12"/>
                <line x1="9" y1="15" x2="12" y2="12"/>
                <line x1="15" y1="15" x2="12" y2="12"/>
              </svg>
            </div>
            <h3 className="dropzone-title">Drag & drop your blood report here</h3>
            <p className="dropzone-subtitle">or click to browse from your device</p>
            <div className="supported-formats">
              <span className="format-badge">📄 PDF Report</span>
              <span className="format-badge">🖼️ JPG / JPEG</span>
              <span className="format-badge">🖼️ PNG Image</span>
              <span className="format-badge max-size">Max 10 MB</span>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="upload-error-box">
          <span className="error-icon">⚠️</span>
          <div>
            <strong>Report Reading Issue</strong>
            <p>{error}</p>
          </div>
        </div>
      )}

      {/* Alternative options: Manual entry or instant demo */}
      <div className="upload-alt-section">
        <div className="alt-divider">
          <span>OR</span>
        </div>

        <div className="alt-actions-row">
          <button className="alt-btn secondary-btn" onClick={onSwitchToManual}>
            ✍️ Enter Blood Test Values Manually
          </button>
          <button className="alt-btn demo-btn" onClick={() => loadDemoData("dengue")}>
            🧪 Test with Sample Low Platelet Report
          </button>
          <button className="alt-btn demo-btn" onClick={() => loadDemoData("healthy")}>
            🟢 Test with Normal Blood Report
          </button>
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect } from "react";
import axios from "axios";

import { API_URL } from "../apiConfig";

export default function TenantScreeningHistory({ token, tenant, user, onClose }) {
  const [screenings, setScreenings] = useState([]);
  const [tenantInfo, setTenantInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const headers = { Authorization: `Bearer ${token}` };
      const [screeningsRes, infoRes] = await Promise.all([
        axios.get(`${API_URL}/api/tenant/screenings`, { headers }),
        axios.get(`${API_URL}/api/tenant/info`, { headers }),
      ]);
      setScreenings(screeningsRes.data);
      setTenantInfo(infoRes.data);
    } catch (err) {
      setError("Failed to load organization screening history. Please verify your connection.");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    const code = tenantInfo?.code || tenant?.code;
    if (code) {
      navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  const getRiskBadge = (level) => {
    if (level === "High") return <span className="risk-tag risk-tag-high">🚨 High</span>;
    if (level === "Moderate") return <span className="risk-tag risk-tag-mod">⚠️ Moderate</span>;
    return <span className="risk-tag risk-tag-low">✅ Low</span>;
  };

  return (
    <div className="history-container">
      {/* Top Banner */}
      <div className="history-header-bar">
        <div>
          <span className="step-tag">Tenant Isolation Workspace</span>
          <h2 className="history-title">
            🏥 {tenantInfo?.name || tenant?.name} — Patient Screening Records
          </h2>
          <p className="history-subtitle">
            All clinical dengue screening records are strictly isolated to your authorized organization.
          </p>
        </div>

        <div className="history-header-actions">
          <button className="btn-secondary" onClick={onClose}>
            ← Return to Screening Workspace
          </button>
        </div>
      </div>

      {/* Organization Info Card & Invite Code */}
      <div className="org-meta-card">
        <div className="org-meta-item">
          <span className="org-meta-label">Organization Code:</span>
          <div className="org-code-pill">
            <code>{tenantInfo?.code || tenant?.code}</code>
            <button className="copy-code-btn" onClick={handleCopyCode} title="Copy code to invite staff">
              {copied ? "✓ Copied!" : "📋 Copy"}
            </button>
          </div>
        </div>

        <div className="org-meta-item">
          <span className="org-meta-label">Total Screenings:</span>
          <span className="org-meta-value">{screenings.length} Patients</span>
        </div>

        <div className="org-meta-item">
          <span className="org-meta-label">Active Members:</span>
          <span className="org-meta-value">{tenantInfo?.member_count || 1} Staff</span>
        </div>

        <div className="org-meta-item">
          <span className="org-meta-label">Your Role:</span>
          <span className="org-role-badge">
            {user?.role === "admin" ? "🛡️ Tenant Admin" : "👤 Clinical Staff"}
          </span>
        </div>
      </div>

      {error && <div className="auth-error-banner" style={{ marginBottom: "16px" }}>{error}</div>}

      {/* Screenings Table */}
      <div className="history-table-card">
        {loading ? (
          <div className="history-loading-wrap">
            <div className="upload-spinner" />
            <p>Loading organization screening records...</p>
          </div>
        ) : screenings.length === 0 ? (
          <div className="history-empty-state">
            <div className="empty-icon">📁</div>
            <h4>No Patient Screenings Yet</h4>
            <p>
              Upload a blood test report or run a questionnaire screening to populate this clinic's record log.
            </p>
            <button className="btn-primary-small" onClick={onClose} style={{ marginTop: "12px" }}>
              Run First Screening →
            </button>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="clinical-history-table">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Patient Name</th>
                  <th>Age / Sex</th>
                  <th>Platelet Count</th>
                  <th>Haemoglobin</th>
                  <th>PDW</th>
                  <th>Risk Level</th>
                  <th>Probability</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {screenings.map((rec) => (
                  <tr key={rec.id}>
                    <td className="cell-date">{rec.created_at || "—"}</td>
                    <td className="cell-name"><b>{rec.patient_name}</b></td>
                    <td>{rec.age} yrs · {rec.sex}</td>
                    <td className={rec.platelet_count < 100000 ? "cell-alert" : ""}>
                      {Math.round(rec.platelet_count).toLocaleString()} /µL
                    </td>
                    <td>{rec.haemoglobin?.toFixed(1)} g/dL</td>
                    <td>{rec.pdw?.toFixed(1)}%</td>
                    <td>{getRiskBadge(rec.risk_level)}</td>
                    <td><b>{(rec.probability * 100).toFixed(1)}%</b></td>
                    <td className="cell-filename">{rec.source_filename}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

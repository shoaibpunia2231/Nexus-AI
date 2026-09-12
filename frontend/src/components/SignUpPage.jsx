import { useState } from "react";
import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function SignUpPage({ onNavigate, onAuthSuccess }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [tenantAction, setTenantAction] = useState("create"); // "create" or "join"
  const [organizationName, setOrganizationName] = useState("");
  const [joinCode, setJoinCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !password) {
      setError("Please fill in all required fields.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match. Please verify.");
      return;
    }

    if (tenantAction === "create" && !organizationName.trim()) {
      setError("Please enter a name for your clinic or organization.");
      return;
    }

    if (tenantAction === "join" && !joinCode.trim()) {
      setError("Please enter the organization join code provided by your administrator.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const payload = {
        name: name.trim(),
        email: email.trim(),
        password: password,
        tenant_action: tenantAction,
        organization_name: tenantAction === "create" ? organizationName.trim() : null,
        join_code: tenantAction === "join" ? joinCode.trim().toUpperCase() : null,
      };

      const res = await axios.post(`${API_URL}/api/auth/signup`, payload);
      const { access_token, user, tenant } = res.data;
      onAuthSuccess({ token: access_token, user, tenant });
    } catch (err) {
      const detail = err.response?.data?.detail || "Registration failed. Please check your information and try again.";
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page-root">
      <div className="auth-nav-top">
        <button className="auth-back-btn" onClick={() => onNavigate("LANDING")}>
          ← Back to Home
        </button>
        <span className="auth-brand-logo">Nexus AI</span>
      </div>

      <div className="auth-card-wrap">
        <div className="auth-card auth-card-wide">
          <div className="auth-header">
            <h2 className="auth-title">Create Your Clinical Account</h2>
            <p className="auth-subtitle">
              Set up a multi-tenant workspace for your clinic or join an existing organization.
            </p>
          </div>

          {error && (
            <div className="auth-error-banner">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            {/* User Details */}
            <div className="auth-row-2">
              <div className="auth-group">
                <label>Full Name *</label>
                <input
                  type="text"
                  required
                  placeholder="Enter your name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="auth-input"
                  disabled={loading}
                />
              </div>

              <div className="auth-group">
                <label>Work Email *</label>
                <input
                  type="email"
                  required
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="auth-input"
                  disabled={loading}
                />
              </div>
            </div>

            <div className="auth-row-2">
              <div className="auth-group">
                <label>Password (min. 6 characters) *</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="auth-input"
                  disabled={loading}
                />
              </div>

              <div className="auth-group">
                <label>Confirm Password *</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="auth-input"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Tenant Setup Tabs */}
            <div className="tenant-setup-box">
              <span className="tenant-box-title">Organization Setup</span>
              <div className="tenant-toggle-tabs">
                <button
                  type="button"
                  className={`tenant-tab-btn ${tenantAction === "create" ? "active" : ""}`}
                  onClick={() => setTenantAction("create")}
                >
                  🏢 Create New Clinic (Admin)
                </button>
                <button
                  type="button"
                  className={`tenant-tab-btn ${tenantAction === "join" ? "active" : ""}`}
                  onClick={() => setTenantAction("join")}
                >
                  🔑 Join Existing Clinic (Staff)
                </button>
              </div>

              {tenantAction === "create" ? (
                <div className="auth-group" style={{ marginTop: "12px" }}>
                  <label>Clinic / Hospital Organization Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Apex Health Center, Metro Pathology"
                    value={organizationName}
                    onChange={(e) => setOrganizationName(e.target.value)}
                    className="auth-input"
                    disabled={loading}
                  />
                  <span className="input-hint">
                    You will become the organization administrator and receive an invite code for colleagues.
                  </span>
                </div>
              ) : (
                <div className="auth-group" style={{ marginTop: "12px" }}>
                  <label>Organization Join Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. NX-8429"
                    value={joinCode}
                    onChange={(e) => setJoinCode(e.target.value)}
                    className="auth-input uppercase-input"
                    disabled={loading}
                  />
                  <span className="input-hint">
                    Enter the code provided by your clinic administrator to join their workspace.
                  </span>
                </div>
              )}
            </div>

            <button type="submit" className="auth-submit-btn" disabled={loading}>
              {loading ? "Creating Account..." : "Create Account & Enter Workspace →"}
            </button>
          </form>

          <div className="auth-footer-prompt">
            <span>Already have an account?</span>
            <button className="auth-switch-link" onClick={() => onNavigate("SIGN_IN")}>
              Sign In
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

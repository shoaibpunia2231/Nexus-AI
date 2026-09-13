import React from "react";
import logo from "../assets/nexus_ai_logo_peach.png";

export default function LandingPage({ onNavigate }) {
  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="landing-root">
      {/* ── 1. Minimal Public Navigation ─────────────────────────────── */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <div className="landing-brand" onClick={() => onNavigate("LANDING")}>
            <div className="brand-logo-icon">
              <img src={logo} alt="Nexus AI" style={{ width: 32, height: 32, objectFit: "contain" }} />
            </div>
            <span className="brand-title">Nexus AI</span>
          </div>

          <div className="landing-nav-links">
            <button className="nav-link-btn" onClick={() => scrollToSection("benefits")}>Features</button>
            <button className="nav-link-btn" onClick={() => scrollToSection("how-it-works")}>How It Works</button>
            <button className="nav-link-btn" onClick={() => scrollToSection("trust")}>Trust & Safety</button>
          </div>

          <div className="landing-nav-actions">
            <button className="btn-link" onClick={() => onNavigate("SIGN_IN")}>
              Sign In
            </button>
            <button className="btn-primary-small" onClick={() => onNavigate("SIGN_UP")}>
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* ── 2. Clean Hero Section ───────────────────────────────────── */}
      <section className="landing-hero">
        <div className="hero-badge">
          <span className="badge-dot" />
          <span>Multi-Tenant Clinical Decision Support</span>
        </div>
        <h1 className="hero-heading">
          AI-Assisted Dengue Screening for Modern Clinical Teams
        </h1>
        <p className="hero-subheading">
          Analyze complete blood counts and clinical laboratory parameters with high-precision machine learning. Built for clinics, laboratories, and healthcare organizations.
        </p>

        <div className="hero-cta-group">
          <button className="btn-cta-primary" onClick={() => onNavigate("SIGN_UP")}>
            Get Started Free →
          </button>
          <button className="btn-cta-secondary" onClick={() => onNavigate("SIGN_IN")}>
            Sign In to Clinic
          </button>
        </div>

        {/* Minimal metrics row */}
        <div className="hero-stats-row">
          <div className="stat-item">
            <span className="stat-value">98.9%</span>
            <span className="stat-label">Model Validation Accuracy</span>
          </div>
          <div className="stat-sep" />
          <div className="stat-item">
            <span className="stat-value">&lt; 30s</span>
            <span className="stat-label">Report OCR & Analysis Time</span>
          </div>
          <div className="stat-sep" />
          <div className="stat-item">
            <span className="stat-value">100%</span>
            <span className="stat-label">Tenant Data Isolation</span>
          </div>
        </div>
      </section>

      {/* ── 3. Key Benefits Section ─────────────────────────────────── */}
      <section id="benefits" className="landing-section">
        <div className="section-header-center">
          <span className="section-kicker">Core Capabilities</span>
          <h2 className="section-title">Designed for Clinical Simplicity</h2>
          <p className="section-desc">Streamlined decision support that eliminates guesswork without complicating workflows.</p>
        </div>

        <div className="benefits-grid">
          <div className="benefit-card">
            <div className="benefit-icon-box">📄</div>
            <h3 className="benefit-title">Upload Blood Reports</h3>
            <p className="benefit-text">
              Directly upload laboratory PDF documents or photos. Optical character recognition automatically detects platelet counts, haemoglobin, and PDW.
            </p>
          </div>

          <div className="benefit-card">
            <div className="benefit-icon-box">🧠</div>
            <h3 className="benefit-title">AI-Assisted Screening</h3>
            <p className="benefit-text">
              Conservative machine learning models trained on validated clinical parameters estimate dengue likelihood and risk levels in seconds.
            </p>
          </div>

          <div className="benefit-card">
            <div className="benefit-icon-box">📊</div>
            <h3 className="benefit-title">Blood Test Visualization</h3>
            <p className="benefit-text">
              Live spectrum comparison displays patient results against established laboratory reference intervals and critical thrombocytopenia zones.
            </p>
          </div>

          <div className="benefit-card">
            <div className="benefit-icon-box">📑</div>
            <h3 className="benefit-title">Generate Summary Reports</h3>
            <p className="benefit-text">
              Export downloadable, professional medical-style PDF screening summaries for patient documentation and clinical handover.
            </p>
          </div>

          <div className="benefit-card">
            <div className="benefit-icon-box">💬</div>
            <h3 className="benefit-title">AI Health Assistant</h3>
            <p className="benefit-text">
              Context-aware educational assistant that explains parameter meanings, hydration guidelines, and danger signs requiring immediate care.
            </p>
          </div>

          <div className="benefit-card">
            <div className="benefit-icon-box">🏢</div>
            <h3 className="benefit-title">Multi-Tenant Isolation</h3>
            <p className="benefit-text">
              Complete organizational privacy. Patient screening records, history, and files remain strictly confined to your authorized clinic.
            </p>
          </div>
        </div>
      </section>

      {/* ── 4. How It Works Section ─────────────────────────────────── */}
      <section id="how-it-works" className="landing-section alt-bg">
        <div className="section-header-center">
          <span className="section-kicker">Workflow</span>
          <h2 className="section-title">How Nexus AI Works</h2>
          <p className="section-desc">A frictionless 4-step journey from document to actionable screening result.</p>
        </div>

        <div className="steps-container">
          <div className="step-card">
            <div className="step-number">1</div>
            <h4 className="step-heading">Upload Report</h4>
            <p className="step-body">Upload a CBC blood test report in PDF or image format, or enter values manually.</p>
          </div>

          <div className="step-arrow">→</div>

          <div className="step-card">
            <div className="step-number">2</div>
            <h4 className="step-heading">Review Results</h4>
            <p className="step-body">Verify extracted laboratory values with live reference range indicators.</p>
          </div>

          <div className="step-arrow">→</div>

          <div className="step-card">
            <div className="step-number">3</div>
            <h4 className="step-heading">AI Screening</h4>
            <p className="step-body">Model evaluates risk stratification, probability score, and key driving factors.</p>
          </div>

          <div className="step-arrow">→</div>

          <div className="step-card">
            <div className="step-number">4</div>
            <h4 className="step-heading">Get Report</h4>
            <p className="step-body">Download a structured clinical PDF summary and consult the AI health assistant.</p>
          </div>
        </div>
      </section>

      {/* ── 5. Trust / Disclaimer Section ───────────────────────────── */}
      <section id="trust" className="landing-section">
        <div className="trust-card">
          <div className="trust-icon">⚕️</div>
          <div className="trust-content">
            <h3 className="trust-title">Clinical Screening & Research Notice</h3>
            <p className="trust-text">
              Nexus AI provides AI-assisted screening and clinical decision support for educational and research purposes.
              It is <b>not a clinically validated diagnostic tool</b> and should never replace professional medical evaluation,
              physician judgment, or laboratory confirmatory testing (such as NS1 antigen or Dengue IgM/IgG serology).
            </p>
          </div>
        </div>
      </section>

      {/* ── 6. Minimal Footer ───────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-brand-block">
            <span className="footer-brand-name">Nexus AI</span>
            <p className="footer-brand-desc">
              Clinical decision support and intelligent dengue screening platform.
            </p>
          </div>

          <div className="footer-links-row">
            <button className="footer-link" onClick={() => onNavigate("SIGN_IN")}>Sign In</button>
            <button className="footer-link" onClick={() => onNavigate("SIGN_UP")}>Sign Up</button>
            <span className="footer-link">Privacy</span>
            <span className="footer-link">Terms</span>
            <span className="footer-link">Contact</span>
          </div>
        </div>

        <div className="footer-bottom">
          <span>© {new Date().getFullYear()} Nexus AI Systems. All rights reserved.</span>
          <span>Educational & Research Decision Support System</span>
        </div>
      </footer>
    </div>
  );
}
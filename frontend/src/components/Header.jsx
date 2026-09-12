import { useTheme } from "../App";

export default function Header({ authSession, onSignOut, onOpenHistory, onNavigate }) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="header">
      <div className="header-inner">
        <div className="header-brand" onClick={() => onNavigate && onNavigate(authSession ? "APP" : "LANDING")} style={{ cursor: "pointer" }}>
          <div className="brand-icon">
            <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
              <circle cx="13" cy="13" r="11" stroke="var(--accent-red)" strokeWidth="2"/>
              <path d="M13 6v7l3.5 3.5" stroke="var(--accent-red)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <circle cx="13" cy="13" r="2" fill="var(--accent-red)"/>
              <circle cx="13" cy="13" r="5" stroke="var(--accent-red)" strokeWidth="1" strokeOpacity="0.3"/>
            </svg>
          </div>
          <div>
            <span className="brand-name">Nexus AI</span>
            <span className="brand-sub">Clinical Screening & Decision Support</span>
          </div>
        </div>

        <div className="header-right">
          {authSession ? (
            <>
              {/* Organization & User Badges */}
              <div className="tenant-header-pill" title={`Clinic Code: ${authSession.tenant?.code}`}>
                <span className="tenant-icon">🏢</span>
                <span className="tenant-name">{authSession.tenant?.name}</span>
                <span className="tenant-code-badge">{authSession.tenant?.code}</span>
              </div>

              <div className="user-header-pill">
                <span className="user-avatar-mini">👤</span>
                <span className="user-name">{authSession.user?.name}</span>
                <span className="user-role-tag">{authSession.user?.role}</span>
              </div>

              <button className="header-history-btn" onClick={onOpenHistory} title="View Clinic Screening History">
                📁 History
              </button>

              <button className="header-signout-btn" onClick={onSignOut} title="Sign Out of Organization">
                Sign Out
              </button>
            </>
          ) : (
            <>
              <button className="btn-link" onClick={() => onNavigate("SIGN_IN")}>
                Sign In
              </button>
              <button className="btn-primary-small" onClick={() => onNavigate("SIGN_UP")}>
                Get Started
              </button>
            </>
          )}

          <button
            className="theme-toggle"
            onClick={toggleTheme}
            aria-label="Toggle light/dark mode"
            title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          >
            {theme === "dark" ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>
        </div>
      </div>
    </header>
  );
}

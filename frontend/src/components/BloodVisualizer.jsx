import React from "react";

export default function BloodVisualizer({ parameters }) {
  if (!parameters) return null;

  const plt = parseFloat(parameters.platelet_count) || 0;
  const hb = parseFloat(parameters.haemoglobin) || 0;
  const pdw = parseFloat(parameters.pdw) || 0;
  const wbc = parseFloat(parameters.wbc_count) || 0;

  // Status calculations
  const getPltStatus = (val) => {
    if (val < 50000) return { label: "Severe Low (<50k)", color: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "#ef4444" };
    if (val < 100000) return { label: "Critical Low (<100k)", color: "#f97316", bg: "rgba(249,115,22,0.12)", border: "#f97316" };
    if (val < 150000) return { label: "Borderline Low", color: "#f59e0b", bg: "rgba(245,158,11,0.12)", border: "#f59e0b" };
    if (val <= 450000) return { label: "Normal Range", color: "#22c55e", bg: "rgba(34,197,94,0.12)", border: "#22c55e" };
    return { label: "Elevated", color: "#3b82f6", bg: "rgba(59,130,246,0.12)", border: "#3b82f6" };
  };

  const getHbStatus = (val) => {
    if (val < 11.5) return { label: "Low (Anaemia risk)", color: "#f59e0b", bg: "rgba(245,158,11,0.12)", border: "#f59e0b" };
    if (val <= 17.5) return { label: "Normal Range", color: "#22c55e", bg: "rgba(34,197,94,0.12)", border: "#22c55e" };
    return { label: "High (Haemoconcentration)", color: "#ea580c", bg: "rgba(234,88,12,0.12)", border: "#ea580c" };
  };

  const getPdwStatus = (val) => {
    if (val > 17.0) return { label: "Elevated Anisocytosis", color: "#f97316", bg: "rgba(249,115,22,0.12)", border: "#f97316" };
    if (val < 9.0) return { label: "Low", color: "#64748b", bg: "rgba(100,116,139,0.12)", border: "#64748b" };
    return { label: "Normal Range", color: "#22c55e", bg: "rgba(34,197,94,0.12)", border: "#22c55e" };
  };

  const pltStat = getPltStatus(plt);
  const hbStat = getHbStatus(hb);
  const pdwStat = getPdwStatus(pdw);

  // Position percentage for range visualizer (clamped 0 to 100)
  const calcPltPos = (val) => Math.min(Math.max((val / 500000) * 100, 3), 97);
  const calcHbPos = (val) => Math.min(Math.max(((val - 5) / (20 - 5)) * 100, 3), 97);
  const calcPdwPos = (val) => Math.min(Math.max(((val - 5) / (25 - 5)) * 100, 3), 97);

  return (
    <div className="blood-visualizer-container">
      <div className="visualizer-header">
        <div>
          <h3 className="visualizer-title">📊 Blood Test Clinical Spectrum</h3>
          <p className="visualizer-subtitle">Patient laboratory values compared against standard reference intervals</p>
        </div>
      </div>

      <div className="cards-grid">
        {/* Platelet Count Card */}
        <div className="vis-card" style={{ borderColor: pltStat.border }}>
          <div className="vis-card-top">
            <span className="vis-card-name">Platelet Count (PLT)</span>
            <span className="vis-status-badge" style={{ color: pltStat.color, background: pltStat.bg, borderColor: pltStat.border }}>
              {pltStat.label}
            </span>
          </div>
          <div className="vis-card-value-row">
            <span className="vis-big-value" style={{ color: pltStat.color }}>
              {plt.toLocaleString()}
            </span>
            <span className="vis-unit">cells/µL</span>
          </div>
          <div className="vis-ref-row">
            <span>Reference Interval: <b>150,000 – 450,000</b></span>
          </div>
          
          {/* Spectrum Range Bar */}
          <div className="vis-spectrum-bar-wrap">
            <div className="vis-spectrum-track plt-track">
              <div className="zone-crit-severe" style={{ width: "10%" }} title="Severe: <50k" />
              <div className="zone-crit" style={{ width: "10%" }} title="Critical: 50k-100k" />
              <div className="zone-low" style={{ width: "10%" }} title="Borderline: 100k-150k" />
              <div className="zone-normal" style={{ width: "60%" }} title="Normal: 150k-450k" />
              <div className="zone-high" style={{ width: "10%" }} title="Elevated: >450k" />
            </div>
            <div className="vis-marker" style={{ left: `${calcPltPos(plt)}%` }}>
              <div className="marker-pin" style={{ background: pltStat.color }} />
              <div className="marker-label">{plt.toLocaleString()}</div>
            </div>
          </div>
          <div className="vis-range-labels">
            <span>0</span>
            <span>100k (Dengue Alert)</span>
            <span>150k</span>
            <span>450k</span>
          </div>
        </div>

        {/* Haemoglobin Card */}
        <div className="vis-card" style={{ borderColor: hbStat.border }}>
          <div className="vis-card-top">
            <span className="vis-card-name">Haemoglobin (Hb)</span>
            <span className="vis-status-badge" style={{ color: hbStat.color, background: hbStat.bg, borderColor: hbStat.border }}>
              {hbStat.label}
            </span>
          </div>
          <div className="vis-card-value-row">
            <span className="vis-big-value" style={{ color: hbStat.color }}>
              {hb.toFixed(1)}
            </span>
            <span className="vis-unit">g/dL</span>
          </div>
          <div className="vis-ref-row">
            <span>Reference Interval: <b>12.0 – 17.5 g/dL</b></span>
          </div>

          <div className="vis-spectrum-bar-wrap">
            <div className="vis-spectrum-track hb-track">
              <div className="zone-low" style={{ width: "35%" }} title="Low: <12 g/dL" />
              <div className="zone-normal" style={{ width: "45%" }} title="Normal: 12.0 - 17.5 g/dL" />
              <div className="zone-high" style={{ width: "20%" }} title="High: >17.5 g/dL" />
            </div>
            <div className="vis-marker" style={{ left: `${calcHbPos(hb)}%` }}>
              <div className="marker-pin" style={{ background: hbStat.color }} />
              <div className="marker-label">{hb.toFixed(1)} g/dL</div>
            </div>
          </div>
          <div className="vis-range-labels">
            <span>5.0</span>
            <span>12.0</span>
            <span>17.5</span>
            <span>20.0</span>
          </div>
        </div>

        {/* PDW Card */}
        <div className="vis-card" style={{ borderColor: pdwStat.border }}>
          <div className="vis-card-top">
            <span className="vis-card-name">Platelet Dist. Width (PDW)</span>
            <span className="vis-status-badge" style={{ color: pdwStat.color, background: pdwStat.bg, borderColor: pdwStat.border }}>
              {pdwStat.label}
            </span>
          </div>
          <div className="vis-card-value-row">
            <span className="vis-big-value" style={{ color: pdwStat.color }}>
              {pdw.toFixed(1)}
            </span>
            <span className="vis-unit">%</span>
          </div>
          <div className="vis-ref-row">
            <span>Reference Interval: <b>9.0 – 17.0 %</b></span>
          </div>

          <div className="vis-spectrum-bar-wrap">
            <div className="vis-spectrum-track pdw-track">
              <div className="zone-low" style={{ width: "20%" }} title="Low: <9%" />
              <div className="zone-normal" style={{ width: "45%" }} title="Normal: 9 - 17%" />
              <div className="zone-high" style={{ width: "35%" }} title="Elevated: >17%" />
            </div>
            <div className="vis-marker" style={{ left: `${calcPdwPos(pdw)}%` }}>
              <div className="marker-pin" style={{ background: pdwStat.color }} />
              <div className="marker-label">{pdw.toFixed(1)}%</div>
            </div>
          </div>
          <div className="vis-range-labels">
            <span>5.0%</span>
            <span>9.0%</span>
            <span>17.0%</span>
            <span>25.0%</span>
          </div>
        </div>
      </div>

      {/* Clinical Disclaimer Note */}
      <div className="vis-footnote">
        ℹ️ Reference intervals represent typical adult baselines and may vary slightly depending on the analyzing laboratory, methodology, age, and biological sex.
      </div>
    </div>
  );
}

export default function FeatureImportanceChart({ data }) {
  if (!data) return null;
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const max = entries[0][1];
  const labels = {
    "WBC Count": "WBC Count", "Platelet Count": "Platelet Count",
    PDW: "Platelet Dist. Width", Age: "Age", Haemoglobin: "Haemoglobin",
    "RBC PANEL": "RBC Panel", "Differential Count": "Differential Count", Sex: "Sex",
  };
  const colors = ["#ef4444","#f97316","#f59e0b","#22c55e","#3b82f6","#8b5cf6","#ec4899","#64748b"];

  return (
    <div className="fi-chart">
      <h3 className="fi-title">📈 Feature Importance</h3>
      <p className="fi-subtitle">Which blood parameters influence the AI prediction most</p>
      <div className="fi-bars">
        {entries.map(([feature, score], i) => (
          <div key={feature} className="fi-row">
            <span className="fi-label">{labels[feature] || feature}</span>
            <div className="fi-bar-track">
              <div className="fi-bar-fill"
                style={{ width: `${(score / max) * 100}%`, background: colors[i % colors.length] }} />
            </div>
            <span className="fi-score">{(score * 100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

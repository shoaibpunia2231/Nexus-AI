/**
 * ModelMetrics.jsx
 * ================
 * Displays model performance metrics, dataset stats, and overfitting analysis.
 *
 * UPDATED metrics reflect the FIXED pipeline (Experiment C — Clinical Safe):
 *   - Features: Age, Sex, Haemoglobin, Platelet Count, PDW  (WBC Count REMOVED)
 *   - Reason: WBC Count had -0.917 correlation with target, making accuracy
 *     trivially ~100%. These are honest metrics from a properly validated model.
 *   - Train/Test gap: 0.1% (no overfitting)
 *   - 5-fold cross-validation confirms generalization
 */

const TRAINING_REPORT = {
  experiment: "C",
  feature_cols: ["Age", "Sex", "Haemoglobin", "Platelet Count", "PDW"],
  best_model: "Random Forest",
  best_metrics: {
    train_acc: 0.9912,
    test_acc:  0.9899,
    train_loss: 0.0802,
    test_loss:  0.0968,
    overfit_gap: 0.0013,
    precision: 0.9925,
    recall:    0.9925,
    f1:        0.9925,
    roc_auc:   0.9845,
    cv_mean:   0.9861,
    cv_std:    0.0135,
  },
  all_models: {
    "Logistic Regression": {
      train_acc: 0.9697, test_acc: 0.9646, overfit_gap: 0.005,
      precision: 0.9922, recall: 0.9552, f1: 0.9734, roc_auc: 0.9916,
      cv_mean: 0.9659, train_loss: 0.1658, test_loss: 0.1689,
    },
    "Random Forest": {
      train_acc: 0.9912, test_acc: 0.9899, overfit_gap: 0.0013,
      precision: 0.9925, recall: 0.9925, f1: 0.9925, roc_auc: 0.9845,
      cv_mean: 0.9861, train_loss: 0.0802, test_loss: 0.0968,
    },
    "Gradient Boosting": {
      train_acc: 0.9949, test_acc: 0.9848, overfit_gap: 0.0101,
      precision: 0.9852, recall: 0.9925, f1: 0.9888, roc_auc: 0.9859,
      cv_mean: 0.9912, train_loss: 0.0313, test_loss: 0.0667,
    },
  },
  dataset: {
    total: 989, train: 791, test: 198,
    features: 5, dengue_positive: 669, dengue_negative: 320,
  },
  cv: { folds: 5, mean_f1: 0.9861, std_f1: 0.0135 },
  overfitting_note: "No significant overfitting (train-test gap < 5%)",
  root_cause_note:
    "Original model showed ~100% accuracy because WBC Count (corr=-0.917) " +
    "is a near-perfect clinical proxy for the diagnosis. Removed from features.",
};

const METRIC_META = [
  { key: "test_acc",   label: "Test Accuracy",  icon: "🎯", color: "#3b82f6", desc: "Accuracy on held-out test set" },
  { key: "precision",  label: "Precision",       icon: "🔬", color: "#8b5cf6", desc: "Positive predictions that are correct" },
  { key: "recall",     label: "Recall",          icon: "📡", color: "#f59e0b", desc: "Actual positives correctly identified" },
  { key: "f1",         label: "F1 Score",        icon: "⚖️",  color: "#22c55e", desc: "Harmonic mean of precision & recall" },
  { key: "roc_auc",    label: "ROC-AUC",         icon: "📈", color: "#ef4444", desc: "Area under the ROC curve" },
];

function MetricBar({ value, color }) {
  return (
    <div className="metric-bar-track">
      <div className="metric-bar-fill" style={{ width: `${value * 100}%`, background: color }} />
    </div>
  );
}

function OverfitBadge({ gap }) {
  const pct = (gap * 100).toFixed(2);
  const ok  = gap < 0.05;
  return (
    <span style={{
      fontSize: "0.75rem", fontWeight: 700, padding: "2px 8px", borderRadius: 999,
      background: ok ? "#dcfce7" : "#fee2e2",
      color: ok ? "#15803d" : "#dc2626",
    }}>
      {ok ? `✓ No Overfit (gap ${pct}%)` : `⚠ Overfit gap ${pct}%`}
    </span>
  );
}

export default function ModelMetrics() {
  const bm = TRAINING_REPORT.best_metrics;
  const models = TRAINING_REPORT.all_models;
  const ds = TRAINING_REPORT.dataset;

  return (
    <div className="metrics-section">
      <div className="metrics-header">
        <h3 className="section-title">🤖 Model Performance Metrics</h3>
        <div className="best-model-badge">
          <span className="bm-dot" />
          Best: {TRAINING_REPORT.best_model}
        </div>
      </div>

      {/* Root cause note */}
      <div style={{
        background: "#fffbeb", border: "1px solid #fcd34d",
        borderRadius: 8, padding: "10px 14px", marginBottom: 16,
        fontSize: "0.82rem", color: "#92400e", lineHeight: 1.5,
      }}>
        <strong>🔍 Why original model showed ~100%:</strong>{" "}
        {TRAINING_REPORT.root_cause_note}{" "}
        Features now: <em>{TRAINING_REPORT.feature_cols.join(", ")}</em>.
      </div>

      {/* Dataset stats row */}
      <div className="dataset-stats">
        {[
          { label: "Total Samples",  value: ds.total.toLocaleString(),  icon: "🗃️" },
          { label: "Training Set",   value: ds.train.toLocaleString(),  icon: "🏋️" },
          { label: "Test Set",       value: ds.test.toLocaleString(),   icon: "🧪" },
          { label: "Features",       value: ds.features,                icon: "📋" },
          { label: "CV Folds",       value: TRAINING_REPORT.cv.folds,  icon: "🔄" },
          { label: "CV Acc Mean",    value: (bm.cv_mean * 100).toFixed(1) + "%", icon: "📊" },
        ].map(({ label, value, icon }) => (
          <div key={label} className="ds-stat-card">
            <span className="ds-stat-icon">{icon}</span>
            <span className="ds-stat-value">{value}</span>
            <span className="ds-stat-label">{label}</span>
          </div>
        ))}
      </div>

      {/* Train vs Test accuracy + loss */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12,
        marginBottom: 16,
      }}>
        {[
          { label: "Train Accuracy", val: bm.train_acc, icon: "🏋️", color: "#3b82f6" },
          { label: "Test Accuracy",  val: bm.test_acc,  icon: "🧪", color: "#10b981" },
          { label: "Train Loss",     val: bm.train_loss, icon: "📉", color: "#f97316", isLoss: true },
          { label: "Test Loss",      val: bm.test_loss,  icon: "📉", color: "#f43f5e", isLoss: true },
        ].map(({ label, val, icon, color, isLoss }) => (
          <div key={label} style={{
            background: "#f8fafc", borderRadius: 8, padding: "10px 14px",
            display: "flex", alignItems: "center", gap: 10,
            border: "1px solid #e2e8f0",
          }}>
            <span style={{ fontSize: "1.4rem" }}>{icon}</span>
            <div>
              <div style={{ fontSize: "0.75rem", color: "#64748b" }}>{label}</div>
              <div style={{ fontWeight: 700, color, fontSize: "1.05rem" }}>
                {isLoss ? val.toFixed(4) : (val * 100).toFixed(2) + "%"}
              </div>
            </div>
          </div>
        ))}
      </div>
      <div style={{ marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
        <OverfitBadge gap={bm.overfit_gap} />
        <span style={{ fontSize: "0.78rem", color: "#64748b" }}>
          5-fold CV: {(bm.cv_mean * 100).toFixed(2)}% ± {(bm.cv_std * 100).toFixed(2)}%
        </span>
      </div>

      {/* Best model metrics */}
      <div className="best-metrics-grid">
        {METRIC_META.map(({ key, label, icon, color, desc }) => (
          <div key={key} className="metric-card" style={{ "--mc": color }}>
            <div className="metric-card-top">
              <span className="metric-icon">{icon}</span>
              <span className="metric-label">{label}</span>
            </div>
            <div className="metric-value" style={{ color }}>
              {(bm[key] * 100).toFixed(2)}%
            </div>
            <MetricBar value={bm[key]} color={color} />
            <span className="metric-desc">{desc}</span>
          </div>
        ))}
      </div>

      {/* Comparison table */}
      <div className="comparison-table-wrap">
        <h4 className="comparison-title">All Models Comparison (Experiment C)</h4>
        <div className="comparison-table">
          <div className="ct-head">
            <span>Model</span>
            <span>Train%</span>
            <span>Test%</span>
            <span>Gap</span>
            <span>Precision</span>
            <span>Recall</span>
            <span>F1</span>
            <span>ROC-AUC</span>
            <span>CV%</span>
          </div>
          {Object.entries(models).map(([name, m]) => {
            const isBest = name === TRAINING_REPORT.best_model;
            const overfit = m.overfit_gap > 0.05;
            return (
              <div key={name} className={`ct-row ${isBest ? "ct-best" : ""}`}>
                <span className="ct-name">
                  {isBest && <span className="ct-star">★ </span>}
                  {name}
                </span>
                <span className="ct-val">{(m.train_acc * 100).toFixed(1)}%</span>
                <span className="ct-val">{(m.test_acc  * 100).toFixed(1)}%</span>
                <span className="ct-val" style={{ color: overfit ? "#dc2626" : "#16a34a", fontWeight: 600 }}>
                  {(m.overfit_gap * 100).toFixed(1)}%
                </span>
                <span className="ct-val">{(m.precision * 100).toFixed(2)}%</span>
                <span className="ct-val">{(m.recall    * 100).toFixed(2)}%</span>
                <span className="ct-val" style={{ color: isBest ? "#22c55e" : undefined, fontWeight: isBest ? 700 : 400 }}>
                  {(m.f1      * 100).toFixed(2)}%
                </span>
                <span className="ct-val">{(m.roc_auc   * 100).toFixed(2)}%</span>
                <span className="ct-val">{(m.cv_mean   * 100).toFixed(1)}%</span>
              </div>
            );
          })}
        </div>
        <p className="cv-note">
          📊 5-fold CV Acc: <strong>{(bm.cv_mean * 100).toFixed(2)}%</strong> ± {(bm.cv_std * 100).toFixed(2)}%
          &nbsp;·&nbsp; 80/20 stratified split · L2 regularization · max_depth=4
        </p>
        <p className="cv-note" style={{ color: "#d97706" }}>
          ⚠️ Experiment A (all features incl. WBC Count) gives ~100% — run{" "}
          <code>EXPERIMENT=A python train_model.py</code> to reproduce the "before" state.
        </p>
      </div>
    </div>
  );
}

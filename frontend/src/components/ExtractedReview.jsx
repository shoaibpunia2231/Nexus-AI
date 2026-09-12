import { useState } from "react";
import BloodVisualizer from "./BloodVisualizer";

export default function ExtractedReview({ extractionData, onConfirm, onBack }) {
  const patient = extractionData?.patient || {};
  const params = extractionData?.parameters || {};

  // Form states with extracted defaults or empty
  const [patientName, setPatientName] = useState(patient.name || "");
  const [age, setAge] = useState(patient.age !== null && patient.age !== undefined ? String(patient.age) : "");
  const [sex, setSex] = useState(patient.sex || "male");
  const [haemoglobin, setHaemoglobin] = useState(
    params.haemoglobin?.value !== null && params.haemoglobin?.value !== undefined ? String(params.haemoglobin.value) : ""
  );
  const [plateletCount, setPlateletCount] = useState(
    params.platelet_count?.value !== null && params.platelet_count?.value !== undefined ? String(params.platelet_count.value) : ""
  );
  const [pdw, setPdw] = useState(
    params.pdw?.value !== null && params.pdw?.value !== undefined ? String(params.pdw.value) : ""
  );
  const [wbcCount, setWbcCount] = useState(
    params.wbc_count?.value !== null && params.wbc_count?.value !== undefined ? String(params.wbc_count.value) : "5000"
  );

  const [errors, setErrors] = useState({});

  // Real-time live parameters for visualizer
  const liveParams = {
    haemoglobin: parseFloat(haemoglobin) || 0,
    platelet_count: parseFloat(plateletCount) || 0,
    pdw: parseFloat(pdw) || 0,
    wbc_count: parseFloat(wbcCount) || 0,
  };

  const validate = () => {
    const errs = {};
    const a = parseFloat(age);
    if (!age || isNaN(a) || a <= 0 || a > 120) {
      errs.age = "Please provide a valid patient age (1–120 years).";
    }
    if (!sex) {
      errs.sex = "Please select biological sex.";
    }

    const hb = parseFloat(haemoglobin);
    if (!haemoglobin || isNaN(hb) || hb < 2 || hb > 25) {
      errs.haemoglobin = "Haemoglobin must be between 2.0 and 25.0 g/dL.";
    }

    const plt = parseFloat(plateletCount);
    if (!plateletCount || isNaN(plt) || plt < 2000 || plt > 1500000) {
      errs.platelet_count = "Platelet count must be between 2,000 and 1,500,000 cells/µL.";
    }

    const p = parseFloat(pdw);
    if (!pdw || isNaN(p) || p < 4 || p > 40) {
      errs.pdw = "PDW must be between 4.0% and 40.0%.";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    const confirmedData = {
      patient: {
        name: patientName.trim() || "Not Specified",
        age: parseFloat(age),
        sex: sex,
      },
      parameters: {
        haemoglobin: parseFloat(haemoglobin),
        platelet_count: parseFloat(plateletCount),
        pdw: parseFloat(pdw),
        wbc_count: parseFloat(wbcCount) || 0,
        differential_count: 1,
        rbc_panel: 1,
      },
      report_info: {
        filename: extractionData?.filename || "Uploaded Report",
      },
    };

    onConfirm(confirmedData);
  };

  return (
    <div className="review-container">
      <div className="review-header">
        <div className="review-title-wrap">
          <span className="step-tag">Step 2 of 4: Patient Verification</span>
          <h2 className="review-title">Review Extracted Laboratory Data</h2>
          <p className="review-subtitle">
            Our extraction engine identified the parameters below from <b>{extractionData?.filename}</b>.
            Please verify or edit any field before running the AI screening.
          </p>
        </div>
        <button className="back-link-btn" onClick={onBack}>
          ← Upload Another File
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="review-grid">
          {/* Patient Details Card */}
          <div className="form-card">
            <h3 className="card-section-title">👤 Patient Information</h3>
            <div className="form-group">
              <label>Patient Name (Optional)</label>
              <input
                type="text"
                placeholder="e.g. John Doe"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                className="text-input"
              />
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <div className="label-with-status">
                  <label>Age (Years) *</label>
                  {params.age?.status === "Unable to extract" && (
                    <span className="field-warn-tag">Unable to extract</span>
                  )}
                </div>
                <input
                  type="number"
                  placeholder="e.g. 32"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  className={`text-input ${errors.age ? "input-err" : ""}`}
                />
                {errors.age && <span className="field-error">{errors.age}</span>}
              </div>

              <div className="form-group">
                <div className="label-with-status">
                  <label>Biological Sex *</label>
                  {params.sex?.status === "Unable to extract" && (
                    <span className="field-warn-tag">Unable to extract</span>
                  )}
                </div>
                <select
                  value={sex}
                  onChange={(e) => setSex(e.target.value)}
                  className={`text-input select-input ${errors.sex ? "input-err" : ""}`}
                >
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="child">Child (under 12)</option>
                </select>
                {errors.sex && <span className="field-error">{errors.sex}</span>}
              </div>
            </div>
          </div>

          {/* Blood Test Parameters Card */}
          <div className="form-card">
            <h3 className="card-section-title">🩸 Extracted Blood Parameters</h3>

            {/* Platelet Count */}
            <div className="form-group">
              <div className="label-with-status">
                <label>Platelet Count (cells/µL) *</label>
                {params.platelet_count?.status === "Unable to extract" ? (
                  <span className="field-warn-tag">⚠️ Unable to extract</span>
                ) : (
                  <span className="field-ok-tag">✓ Extracted</span>
                )}
              </div>
              <input
                type="number"
                placeholder="e.g. 45000"
                value={plateletCount}
                onChange={(e) => setPlateletCount(e.target.value)}
                className={`text-input ${errors.platelet_count ? "input-err" : ""}`}
              />
              <span className="input-hint">Normal: 150,000–450,000 cells/µL. Dengue risk warning &lt; 100,000.</span>
              {errors.platelet_count && <span className="field-error">{errors.platelet_count}</span>}
            </div>

            <div className="form-row-2">
              {/* Haemoglobin */}
              <div className="form-group">
                <div className="label-with-status">
                  <label>Haemoglobin (g/dL) *</label>
                  {params.haemoglobin?.status === "Unable to extract" ? (
                    <span className="field-warn-tag">⚠️ Unable to extract</span>
                  ) : (
                    <span className="field-ok-tag">✓ Extracted</span>
                  )}
                </div>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g. 12.5"
                  value={haemoglobin}
                  onChange={(e) => setHaemoglobin(e.target.value)}
                  className={`text-input ${errors.haemoglobin ? "input-err" : ""}`}
                />
                <span className="input-hint">Normal: 12.0–17.5 g/dL</span>
                {errors.haemoglobin && <span className="field-error">{errors.haemoglobin}</span>}
              </div>

              {/* PDW */}
              <div className="form-group">
                <div className="label-with-status">
                  <label>PDW (%) *</label>
                  {params.pdw?.status === "Unable to extract" ? (
                    <span className="field-warn-tag">⚠️ Unable to extract</span>
                  ) : (
                    <span className="field-ok-tag">✓ Extracted</span>
                  )}
                </div>
                <input
                  type="number"
                  step="0.1"
                  placeholder="e.g. 15.0"
                  value={pdw}
                  onChange={(e) => setPdw(e.target.value)}
                  className={`text-input ${errors.pdw ? "input-err" : ""}`}
                />
                <span className="input-hint">Normal: 9.0–17.0%</span>
                {errors.pdw && <span className="field-error">{errors.pdw}</span>}
              </div>
            </div>
          </div>
        </div>

        {/* Real-time Blood Spectrum Visualizer */}
        <div className="review-visualizer-wrap">
          <BloodVisualizer parameters={liveParams} />
        </div>

        <div className="review-submit-bar">
          <button type="button" className="btn-secondary" onClick={onBack}>
            ← Back to Upload
          </button>
          <button type="submit" className="btn-primary-glow">
            Confirm & Run Dengue Screening →
          </button>
        </div>
      </form>
    </div>
  );
}

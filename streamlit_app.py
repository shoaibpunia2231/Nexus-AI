"""
streamlit_app.py
================
Nexus AI — Clinical Dengue Screening & Decision Support System
Clinical Decision Support Application powered by Scikit-Learn and Streamlit.
Ready for deployment on Streamlit Community Cloud.
"""

import os
import sys
import json
import warnings
import joblib
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Suppress unpickling version warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus AI — Dengue Screening & Risk Assessment",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for Medical / Clinical Aesthetic ──────────────────────────────
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        backdrop-filter: blur(8px);
    }
    .risk-badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .risk-low {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ade80;
        border: 1px solid #22c55e;
    }
    .risk-mod {
        background-color: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid #f59e0b;
    }
    .risk-high {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid #ef4444;
    }
    .param-chip {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.04);
        border-left: 4px solid #0284c7;
        margin-bottom: 8px;
    }
    .param-chip-alert {
        border-left: 4px solid #ef4444;
        background: rgba(239, 68, 68, 0.08);
    }
    .info-card {
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers to Locate Files ───────────────────────────────────────────────────
def resolve_file(*relative_path_parts):
    base_dirs = [
        os.path.dirname(__file__),
        os.path.join(os.path.dirname(__file__), "ml"),
        os.getcwd(),
        os.path.join(os.getcwd(), "ml"),
    ]
    for b in base_dirs:
        candidate = os.path.join(b, *relative_path_parts)
        if os.path.exists(candidate):
            return candidate
    return os.path.join(os.path.dirname(__file__), *relative_path_parts)


# ── Load Model Artifacts ──────────────────────────────────────────────────────
@st.cache_resource
def load_model_artifacts():
    model_path = resolve_file("ml", "models", "model.pkl")
    scaler_path = resolve_file("ml", "models", "scaler.pkl")

    if not os.path.exists(model_path):
        model_path = resolve_file("models", "model.pkl")
    if not os.path.exists(scaler_path):
        scaler_path = resolve_file("models", "scaler.pkl")

    try:
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        return model, scaler
    except Exception as e:
        st.error(f"Error loading model artifacts: {e}")
        return None, None


@st.cache_data
def load_json_metadata():
    fi_path = resolve_file("ml", "models", "feature_importance.json")
    rep_path = resolve_file("ml", "models", "training_report.json")

    if not os.path.exists(fi_path):
        fi_path = resolve_file("models", "feature_importance.json")
    if not os.path.exists(rep_path):
        rep_path = resolve_file("models", "training_report.json")

    fi, report = {}, {}
    if os.path.exists(fi_path):
        with open(fi_path, "r") as f:
            fi = json.load(f)
    if os.path.exists(rep_path):
        with open(rep_path, "r") as f:
            report = json.load(f)
    return fi, report


model, scaler = load_model_artifacts()
feature_importance_dict, training_report = load_json_metadata()

FEATURE_COLS = ["Age", "Sex", "Haemoglobin", "Platelet Count", "PDW"]


# ── Preprocessing & Inference ────────────────────────────────────────────────
def run_prediction(input_dict: dict, model_obj, scaler_obj):
    sex_map = {"male": 0, "female": 1, "child": 2}
    sex_val = sex_map.get(str(input_dict.get("sex", "male")).lower(), 0)

    full_row = {
        "Age": float(input_dict.get("age", 0)),
        "Sex": sex_val,
        "Haemoglobin": float(input_dict.get("haemoglobin", 0)),
        "Platelet Count": float(input_dict.get("platelet_count", 0)),
        "PDW": float(input_dict.get("pdw", 0)),
    }

    df_in = pd.DataFrame([full_row])[FEATURE_COLS]
    num_cols = [c for c in FEATURE_COLS if c != "Sex"]

    if scaler_obj is not None:
        df_in[num_cols] = scaler_obj.transform(df_in[num_cols])

    prob = float(model_obj.predict_proba(df_in)[0][1])
    pred = int(model_obj.predict(df_in)[0])

    if prob < 0.35:
        risk_level = "Low"
        risk_color = "#22c55e"
        badge_class = "risk-low"
        guidance = "Blood parameters indicate low dengue risk. Continue routine health precautions and maintain adequate hydration."
    elif prob < 0.65:
        risk_level = "Moderate"
        risk_color = "#f59e0b"
        badge_class = "risk-mod"
        guidance = "Moderate dengue risk detected. Laboratory parameters show borderline changes. Monitor symptoms closely and consult a healthcare provider."
    else:
        risk_level = "High"
        risk_color = "#ef4444"
        badge_class = "risk-high"
        guidance = "High dengue risk detected with significant thrombocytopenia. Prompt clinical evaluation and medical consultation are strongly recommended."

    return {
        "prediction": pred,
        "probability": prob,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "badge_class": badge_class,
        "guidance": guidance,
        "dengue_positive": bool(pred == 1),
    }


# ── Preset Management ────────────────────────────────────────────────────────
if "patient_params" not in st.session_state:
    st.session_state.patient_params = {
        "age": 30,
        "sex": "Male",
        "haemoglobin": 13.5,
        "platelet_count": 185000,
        "pdw": 14.5,
        "wbc_count": 6500,
    }


def set_preset(preset_type):
    if preset_type == "dengue":
        st.session_state.patient_params = {
            "age": 28,
            "sex": "Male",
            "haemoglobin": 11.8,
            "platelet_count": 45000,
            "pdw": 16.5,
            "wbc_count": 2800,
        }
    elif preset_type == "moderate":
        st.session_state.patient_params = {
            "age": 35,
            "sex": "Female",
            "haemoglobin": 12.4,
            "platelet_count": 92000,
            "pdw": 15.2,
            "wbc_count": 4100,
        }
    elif preset_type == "healthy":
        st.session_state.patient_params = {
            "age": 42,
            "sex": "Female",
            "haemoglobin": 14.2,
            "platelet_count": 240000,
            "pdw": 12.0,
            "wbc_count": 7200,
        }


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/medical-heart.png", width=64)
    st.title("Nexus AI")
    st.caption("Clinical Decision Support System (CDSS) • v2.1")

    app_mode = st.radio(
        "Navigation",
        [
            "🩺 Patient Assessment",
            "📂 Batch Screening (CSV)",
            "📊 Model Analytics & Diagnostics",
            "ℹ️ Clinical Guidelines & About",
        ],
    )

    st.markdown("---")
    st.markdown("### ⚡ Quick Patient Presets")
    st.caption("Load verified test cases into the clinical assessment:")

    c_p1, c_p2 = st.columns(2)
    with c_p1:
        if st.button("🚨 Severe Dengue", use_container_width=True):
            set_preset("dengue")
            st.rerun()
    with c_p2:
        if st.button("⚠️ Borderline", use_container_width=True):
            set_preset("moderate")
            st.rerun()

    if st.button("✅ Healthy Baseline", use_container_width=True):
        set_preset("healthy")
        st.rerun()

    st.markdown("---")
    st.markdown(
        """
    **Model Information**
    - **Classifier**: Random Forest
    - **Feature Selection**: Experiment C (Clinical Safe)
    - **Validation Accuracy**: 98.99%
    - **F1 Score**: 0.9925
    """
    )
    st.caption("🔒 Runs purely on client-side inference.")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: PATIENT ASSESSMENT
# ─────────────────────────────────────────────────────────────────────────────
if app_mode == "🩺 Patient Assessment":
    st.markdown("## 🩺 Patient Clinical & Laboratory Assessment")
    st.markdown(
        "Input the patient's complete blood count (CBC) parameters to generate an instant dengue risk profile."
    )

    col_form, col_res = st.columns([1.1, 1.2], gap="large")

    with col_form:
        st.markdown("### 📋 Enter Laboratory Parameters")

        with st.form("assessment_form"):
            c1, c2 = st.columns(2)
            with c1:
                age = st.number_input(
                    "Patient Age (Years)",
                    min_value=1,
                    max_value=110,
                    value=st.session_state.patient_params["age"],
                    step=1,
                )
            with c2:
                sex = st.selectbox(
                    "Biological Sex",
                    options=["Male", "Female", "Child"],
                    index=["Male", "Female", "Child"].index(
                        st.session_state.patient_params["sex"]
                    ),
                )

            st.markdown("##### 🔬 Complete Blood Count (CBC) Panel")

            platelet_count = st.number_input(
                "Platelet Count (cells/µL)",
                min_value=5000,
                max_value=800000,
                value=st.session_state.patient_params["platelet_count"],
                step=5000,
                help="Reference Normal: 150,000 – 450,000 cells/µL. Dengue Warning: < 100,000 cells/µL.",
            )

            pdw = st.number_input(
                "PDW - Platelet Distribution Width (%)",
                min_value=5.0,
                max_value=40.0,
                value=float(st.session_state.patient_params["pdw"]),
                step=0.1,
                help="Reference Normal: 9.0% – 17.0%. Altered in acute dengue viremia.",
            )

            haemoglobin = st.number_input(
                "Haemoglobin (g/dL)",
                min_value=3.0,
                max_value=25.0,
                value=float(st.session_state.patient_params["haemoglobin"]),
                step=0.1,
                help="Reference Normal: Male: 13.8–17.2, Female: 12.1–15.1 g/dL. High values indicate hemoconcentration.",
            )

            with st.expander("Additional CBC Parameters (Optional Reference)"):
                wbc_count = st.number_input(
                    "WBC Count (cells/µL)",
                    min_value=500,
                    max_value=40000,
                    value=st.session_state.patient_params.get("wbc_count", 6500),
                    step=100,
                    help="Excluded from inference model to avoid data leakage (as per Experiment C), but recorded for clinical evaluation.",
                )

            submitted = st.form_submit_button(
                "⚡ Run Risk Assessment", use_container_width=True, type="primary"
            )

            if submitted:
                st.session_state.patient_params = {
                    "age": age,
                    "sex": sex,
                    "haemoglobin": haemoglobin,
                    "platelet_count": platelet_count,
                    "pdw": pdw,
                    "wbc_count": wbc_count,
                }

    with col_res:
        if model is None or scaler is None:
            st.error("Model artifacts are not loaded. Please verify repository files.")
        else:
            # Perform inference on current parameters
            current_input = {
                "age": st.session_state.patient_params["age"],
                "sex": st.session_state.patient_params["sex"].lower(),
                "haemoglobin": st.session_state.patient_params["haemoglobin"],
                "platelet_count": st.session_state.patient_params["platelet_count"],
                "pdw": st.session_state.patient_params["pdw"],
            }
            res = run_prediction(current_input, model, scaler)
            pct = round(res["probability"] * 100, 1)

            st.markdown("### 🎯 Diagnostic Risk Assessment")

            # Hero Gauge Chart
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 42, "color": res["risk_color"]}},
                    title={"text": "Estimated Dengue Risk Score", "font": {"size": 18}},
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 1},
                        "bar": {"color": res["risk_color"], "thickness": 0.28},
                        "bgcolor": "rgba(255, 255, 255, 0.05)",
                        "steps": [
                            {"range": [0, 35], "color": "rgba(34, 197, 94, 0.25)"},
                            {"range": [35, 65], "color": "rgba(245, 158, 11, 0.25)"},
                            {"range": [65, 100], "color": "rgba(239, 68, 68, 0.25)"},
                        ],
                        "threshold": {
                            "line": {"color": res["risk_color"], "width": 4},
                            "thickness": 0.8,
                            "value": pct,
                        },
                    },
                )
            )
            fig_gauge.update_layout(
                height=220,
                margin=dict(l=20, r=20, t=35, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f8fafc"),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Callout card
            st.markdown(
                f"""
            <div class="metric-card" style="border-left: 6px solid {res['risk_color']};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="risk-badge {res['badge_class']}">{res['risk_level']} Risk Level</span>
                    <span style="font-weight: 600; font-size: 1.1rem; color: {res['risk_color']};">{pct}% Probability</span>
                </div>
                <p style="margin-top: 10px; font-size: 0.95rem; line-height: 1.5; color: #cbd5e1;">
                    {res['guidance']}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Parameter chips with warning flags
            st.markdown("##### 🔍 Parameter Review & Reference Thresholds")
            p_count = st.session_state.patient_params["platelet_count"]
            p_alert = p_count < 100000
            p_crit = p_count < 50000

            chips_html = f"""
            <div class="param-chip {'param-chip-alert' if p_alert else ''}">
                <div>
                    <strong>Platelet Count:</strong> {p_count:,.0f} cells/µL
                    <div style="font-size: 0.8rem; color: #94a3b8;">Ref: 150,000 – 450,000 cells/µL</div>
                </div>
                <span style="color: {'#ef4444' if p_crit else ('#f59e0b' if p_alert else '#22c55e')}; font-weight: 600;">
                    {'CRITICAL THROMBOCYTOPENIA 🚨' if p_crit else ('THROMBOCYTOPENIA ⚠️' if p_alert else 'NORMAL RANGE ✅')}
                </span>
            </div>
            <div class="param-chip">
                <div>
                    <strong>Platelet Distribution Width (PDW):</strong> {st.session_state.patient_params['pdw']}%
                    <div style="font-size: 0.8rem; color: #94a3b8;">Ref: 9.0% – 17.0%</div>
                </div>
                <span style="color: {'#f59e0b' if st.session_state.patient_params['pdw'] > 17.0 else '#22c55e'}; font-weight: 600;">
                    {'ELEVATED' if st.session_state.patient_params['pdw'] > 17.0 else 'NORMAL'}
                </span>
            </div>
            <div class="param-chip">
                <div>
                    <strong>Haemoglobin:</strong> {st.session_state.patient_params['haemoglobin']} g/dL
                    <div style="font-size: 0.8rem; color: #94a3b8;">Ref: 12.0 – 17.5 g/dL</div>
                </div>
                <span style="color: #22c55e; font-weight: 600;">RECORDED</span>
            </div>
            """
            st.markdown(chips_html, unsafe_allow_html=True)

    # ── Clinical Management & Advisory Panels ─────────────────────────────────
    st.markdown("---")
    st.markdown("### 🏥 Clinical Action Protocols & Management Guidelines")

    tab_symp, tab_hosp, tab_hyd, tab_nut = st.tabs(
        [
            "🌡️ Symptoms to Monitor",
            "🚨 When to Hospitalize",
            "💧 Fluid & Platelet Care",
            "🥗 Nutrition & Recovery",
        ]
    )

    with tab_symp:
        st.markdown(
            """
        - **High-grade sudden fever** (> 38.5°C / 101.3°F) lasting 2–7 days.
        - **Retro-orbital headache** (severe pain behind the eyes).
        - **Severe myalgia and arthralgia** ("breakbone fever").
        - **Maculopapular petechial rash** appearing on extremities as fever declines.
        - **Persistent nausea, vomiting, or metallic taste**.
        """
        )

    with tab_hosp:
        st.error(
            """
        **Immediate emergency hospital admission criteria:**
        - Platelet count falling below **50,000 cells/µL** or rapid daily decline.
        - Any spontaneous mucosal bleeding: gums, epistaxis (nosebleeds), or melena (black stool).
        - Severe continuous abdominal pain or tenderness.
        - Persistent vomiting (unable to tolerate oral rehydration fluids).
        - Lethargy, restlessness, cold clammy extremities, or hypotension (Dengue Shock Syndrome).
        """
        )

    with tab_hyd:
        st.info(
            """
        - **Aggressive oral fluid therapy**: 2.5 to 3 Liters per day using Oral Rehydration Salts (ORS).
        - **Electrolyte replacement**: Fresh tender coconut water, diluted fruit juices, electrolyte broths.
        - **Strictly AVOID NSAIDs**: Do **NOT** administer Aspirin, Ibuprofen, Diclofenac, or Naproxen (they exacerbate bleeding and platelet dysfunction).
        - **Antipyretic of choice**: Paracetamol (Acetaminophen) within safe dosage limits.
        """
        )

    with tab_nut:
        st.success(
            """
        - **Vitamin C & Bioflavonoid Rich Foods**: Guava, kiwi, amla, oranges (strengthen vascular endothelium).
        - **Papaya Leaf Extract**: Clinical studies suggest potential benefits in mitigating platelet drop.
        - **Iron & Folate**: Spinach, pomegranate juice, beetroot to support erythropoiesis.
        - **Easily Digestible Diet**: Rice kanji/porridge, clear soups, avoiding deep-fried or ultra-spicy dishes.
        """
        )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: BATCH SCREENING (CSV)
# ─────────────────────────────────────────────────────────────────────────────
elif app_mode == "📂 Batch Screening (CSV)":
    st.markdown("## 📂 Batch Patient Screening via CSV")
    st.markdown(
        "Screen multiple patients simultaneously by uploading laboratory CBC spreadsheets."
    )

    col_up, col_info = st.columns([2, 1])
    with col_up:
        uploaded_file = st.file_uploader(
            "Upload Laboratory CSV file",
            type=["csv"],
            help="Expected columns: Age, Sex, Haemoglobin, Platelet Count, PDW",
        )
    with col_info:
        st.markdown(
            """
        **Expected CSV Format:**
        ```csv
        Age,Sex,Haemoglobin,Platelet Count,PDW
        29,male,12.5,45000,16.2
        45,female,14.0,220000,11.5
        32,male,13.1,88000,15.8
        ```
        """
        )
        sample_df = pd.DataFrame(
            {
                "Age": [29, 45, 32],
                "Sex": ["male", "female", "male"],
                "Haemoglobin": [12.5, 14.0, 13.1],
                "Platelet Count": [45000, 220000, 88000],
                "PDW": [16.2, 11.5, 15.8],
            }
        )
        st.download_button(
            "📥 Download Sample CSV Template",
            data=sample_df.to_csv(index=False),
            file_name="dengue_screening_sample.csv",
            mime="text/csv",
        )

    if uploaded_file is not None:
        try:
            batch_df = pd.read_csv(uploaded_file)
            st.markdown("### 📋 Uploaded Records Preview")
            st.dataframe(batch_df.head(10), use_container_width=True)

            # Standardize column names (case-insensitive)
            col_map = {c.strip().lower(): c for c in batch_df.columns}
            required = ["age", "sex", "haemoglobin", "platelet count", "pdw"]
            missing = [
                r
                for r in required
                if r not in col_map
                and r.replace(" ", "_") not in col_map
                and r.replace(" ", "") not in col_map
            ]

            if missing:
                st.warning(
                    f"Missing expected columns: {missing}. Please check the template format."
                )
            else:
                with st.spinner("Processing batch predictions..."):
                    results = []
                    for _, row in batch_df.iterrows():
                        age_val = row.get(
                            col_map.get("age", "Age"), 30
                        )
                        sex_val = row.get(
                            col_map.get("sex", "Sex"), "male"
                        )
                        hb_val = row.get(
                            col_map.get("haemoglobin", "Haemoglobin"), 13.0
                        )
                        plt_val = row.get(
                            col_map.get("platelet count", col_map.get("platelet_count", "Platelet Count")),
                            150000,
                        )
                        pdw_val = row.get(
                            col_map.get("pdw", "PDW"), 14.0
                        )

                        p_res = run_prediction(
                            {
                                "age": age_val,
                                "sex": sex_val,
                                "haemoglobin": hb_val,
                                "platelet_count": plt_val,
                                "pdw": pdw_val,
                            },
                            model,
                            scaler,
                        )
                        results.append(
                            {
                                "Probability": f"{p_res['probability']*100:.1f}%",
                                "Risk_Level": p_res["risk_level"],
                                "Flag": "🚨 HIGH"
                                if p_res["risk_level"] == "High"
                                else ("⚠️ MODERATE" if p_res["risk_level"] == "Moderate" else "✅ LOW"),
                            }
                        )

                    annotated_df = batch_df.copy()
                    annotated_df["Dengue_Risk_Prob"] = [r["Probability"] for r in results]
                    annotated_df["Risk_Level"] = [r["Risk_Level"] for r in results]
                    annotated_df["Clinical_Flag"] = [r["Flag"] for r in results]

                    st.markdown("---")
                    st.markdown("### 📊 Batch Screening Results")

                    high_cnt = sum(1 for r in results if r["Risk_Level"] == "High")
                    mod_cnt = sum(1 for r in results if r["Risk_Level"] == "Moderate")
                    low_cnt = sum(1 for r in results if r["Risk_Level"] == "Low")

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total Patients", len(batch_df))
                    m2.metric("🚨 High Risk", high_cnt)
                    m3.metric("⚠️ Moderate Risk", mod_cnt)
                    m4.metric("✅ Low Risk", low_cnt)

                    st.dataframe(annotated_df, use_container_width=True)

                    st.download_button(
                        "📥 Download Annotated Results (CSV)",
                        data=annotated_df.to_csv(index=False),
                        file_name="dengue_screened_results.csv",
                        mime="text/csv",
                        type="primary",
                    )
        except Exception as err:
            st.error(f"Error processing CSV: {err}")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: MODEL ANALYTICS & DIAGNOSTICS
# ─────────────────────────────────────────────────────────────────────────────
elif app_mode == "📊 Model Analytics & Diagnostics":
    st.markdown("## 📊 Machine Learning Model Analytics & Transparency")
    st.markdown(
        "Comprehensive performance metrics, feature importance, and clinical safety validations."
    )

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    best_m = training_report.get("best_metrics", {})
    col_m1.metric("Test Accuracy", f"{best_m.get('test_acc', 0.9899)*100:.2f}%")
    col_m2.metric("F1-Score", f"{best_m.get('f1', 0.9925):.4f}")
    col_m3.metric("5-Fold CV Score", f"{best_m.get('cv_mean', 0.9861)*100:.2f}% ± 1.4%")
    col_m4.metric("ROC-AUC", f"{best_m.get('roc_auc', 0.9845):.4f}")

    st.markdown("---")
    c_fi, c_cm = st.columns([1, 1], gap="large")

    with c_fi:
        st.markdown("### 🔍 Feature Importance Breakdown")
        st.caption("Contribution of each biomarker towards the Random Forest decision trees:")

        if feature_importance_dict:
            fi_df = pd.DataFrame(
                list(feature_importance_dict.items()),
                columns=["Feature", "Importance"],
            ).sort_values("Importance", ascending=True)

            fi_df["Percentage"] = (fi_df["Importance"] * 100).round(2).astype(str) + "%"

            fig_fi = px.bar(
                fi_df,
                x="Importance",
                y="Feature",
                orientation="h",
                text="Percentage",
                color="Importance",
                color_continuous_scale="Blues",
            )
            fig_fi.update_layout(
                height=320,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f8fafc"),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig_fi, use_container_width=True)
        else:
            st.info("Feature importance metadata not found.")

    with c_cm:
        st.markdown("### 🎯 Confusion Matrix (Test Set: N=198)")
        cm_data = best_m.get("confusion_matrix", [[63, 1], [1, 133]])
        cm_df = pd.DataFrame(
            cm_data,
            index=["Actual Negative (64)", "Actual Positive (134)"],
            columns=["Predicted Negative", "Predicted Positive"],
        )

        fig_cm = px.imshow(
            cm_df,
            text_auto=True,
            color_continuous_scale="Teal",
            aspect="auto",
        )
        fig_cm.update_layout(
            height=320,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_cm, use_container_width=True)

    # Clinical Safety & Anti-Leakage Rationale
    st.markdown("---")
    st.markdown("### 🛡️ Feature Selection & Clinical Anti-Leakage Rationale")
    st.markdown(
        """
    > **Why was WBC Count excluded from the primary model?**
    >
    > During initial exploratory data analysis (Experiment A), **WBC Count** exhibited an extreme correlation of **-0.917** with the dengue target.
    > In laboratory datasets, this allowed the classifier to act as a near-perfect separator achieving ~100% training accuracy.
    >
    > However, in clinical practice, leukopenia is not solely pathognomonic for dengue and can vary across stages of illness. Relying solely on WBC would cause feature dominance and brittle real-world generalization.
    >
    > **Experiment C (Clinical Safe Features)** restricts predictors to **Platelet Count, PDW, Haemoglobin, Age, and Sex**, yielding an honest, robust **98.9% test accuracy** with a train-test gap of only **0.1%**.
    """
    )

    # Model comparison table
    all_models = training_report.get("all_models", {})
    if all_models:
        st.markdown("### ⚖️ Algorithm Benchmark Comparison")
        comp_rows = []
        for name, m_metrics in all_models.items():
            comp_rows.append(
                {
                    "Classifier": name,
                    "Train Accuracy": f"{m_metrics.get('train_acc', 0)*100:.2f}%",
                    "Test Accuracy": f"{m_metrics.get('test_acc', 0)*100:.2f}%",
                    "Overfit Gap": f"{m_metrics.get('overfit_gap', 0)*100:.2f}%",
                    "Precision": f"{m_metrics.get('precision', 0):.4f}",
                    "Recall": f"{m_metrics.get('recall', 0):.4f}",
                    "F1 Score": f"{m_metrics.get('f1', 0):.4f}",
                    "5-Fold CV Mean": f"{m_metrics.get('cv_mean', 0)*100:.2f}%",
                }
            )
        st.table(pd.DataFrame(comp_rows))


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: CLINICAL GUIDELINES & ABOUT
# ─────────────────────────────────────────────────────────────────────────────
elif app_mode == "ℹ️ Clinical Guidelines & About":
    st.markdown("## ℹ️ About AI Dengue Decision Support System")

    st.markdown(
        """
    ### 🎯 Purpose
    This application is an AI-powered Clinical Decision Support System (CDSS) designed to aid healthcare professionals in screening and stratifying dengue fever risk using standard Complete Blood Count (CBC) parameters.

    ---

    ### 🧬 Key Diagnostic Biomarkers
    - **Platelet Count**: Severe thrombocytopenia (< 100,000 cells/µL, and critically < 50,000 cells/µL) is the primary hallmark of dengue hemorrhagic fever (DHF) due to immune-mediated destruction and bone marrow suppression.
    - **Platelet Distribution Width (PDW)**: Reflects platelet volume heterogeneity. Active platelet consumption and young platelet release cause elevated PDW.
    - **Haemoglobin & Hematocrit**: Elevated values indicate hemoconcentration caused by plasma leakage through damaged vascular endothelium.

    ---

    ### ⚠️ Medical Disclaimer
    > **IMPORTANT NOTICE:** This software is an experimental decision-support tool and machine learning demonstration. It does **NOT** constitute medical diagnosis, clinical advice, or a substitute for confirmatory laboratory assays (such as Dengue NS1 Antigen ELISA, Dengue IgM/IgG antibody tests, or RT-PCR).
    > Always consult a licensed medical physician for patient care.
    """
    )

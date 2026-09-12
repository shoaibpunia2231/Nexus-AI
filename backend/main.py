"""
main.py -- FastAPI Backend for Dengue Risk Prediction
======================================================
Run: uvicorn main:app --reload --port 8000

Notes
-----
- Model trained with Experiment C (Clinical Safe features):
  Age, Sex, Haemoglobin, Platelet Count, PDW
- WBC Count intentionally EXCLUDED from inference:
  It has -0.917 correlation with target, making it a near-perfect separator
  that inflates accuracy to ~100% but does not reflect real-world generalization.
- To retrain with all features: EXPERIMENT=A python ml/train_model.py
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import joblib
import numpy as np
import json
import os
import sys

# Add backend/ and ml/ to sys.path
BASE_DIR = os.path.dirname(__file__)
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "..", "ml"))

from preprocess import preprocess_input, FEATURE_COLS, EXPERIMENT
from routers import extract, report, chat, auth
from models import init_db, get_db, ScreeningRecord, User
from services.auth_service import get_optional_user
from sqlalchemy.orm import Session

# Initialize SQLite tables on startup
init_db()

app = FastAPI(
    title="Nexus AI - Clinical Screening & Dengue Risk Prediction API",
    description=(
        "Nexus AI — AI-powered dengue risk assessment and patient screening system from blood panel parameters. "
        f"Model: Experiment {EXPERIMENT} features — {FEATURE_COLS}."
    ),
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restrict to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register enhanced feature routers
app.include_router(auth.router)
app.include_router(extract.router)
app.include_router(report.router)
app.include_router(chat.router)

# ── Load model artifacts ──────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
MODEL_PATH  = os.path.join(BASE_DIR, "..", "ml", "models", "model.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "..", "ml", "models", "scaler.pkl")
FI_PATH     = os.path.join(BASE_DIR, "..", "ml", "models", "feature_importance.json")
REPORT_PATH = os.path.join(BASE_DIR, "..", "ml", "models", "training_report.json")

try:
    model  = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    print(f"[API] Model loaded: {type(model).__name__}  Experiment: {EXPERIMENT}")
    print(f"[API] Features: {FEATURE_COLS}")
except FileNotFoundError as e:
    raise RuntimeError(
        f"Model files not found. Run `python ml/train_model.py` first.\n{e}"
    )

with open(FI_PATH)     as f: FEATURE_IMPORTANCE = json.load(f)
with open(REPORT_PATH) as f: TRAINING_REPORT    = json.load(f)


# ── Schemas ───────────────────────────────────────────────────────────────────
class PredictRequest(BaseModel):
    age:                float = Field(..., example=35,     description="Patient age in years")
    sex:                str   = Field(..., example="male", description="male | female | child")
    haemoglobin:        float = Field(..., example=12.5,   description="Haemoglobin (g/dL)")
    wbc_count:          float = Field(0,   example=3200,   description="WBC Count (cells/uL) — not used by default model")
    differential_count: int   = Field(1,   example=1,      description="0 or 1")
    rbc_panel:          int   = Field(1,   example=1,      description="0 or 1")
    platelet_count:     float = Field(..., example=45000,  description="Platelet Count (cells/uL)")
    pdw:                float = Field(..., example=14.5,   description="Platelet Distribution Width")
    patient_name:       Optional[str] = Field("Not Specified", example="Arjun Verma")
    source_filename:    Optional[str] = Field("Manual Entry", example="cbc_report.pdf")


class PredictResponse(BaseModel):
    prediction:         int
    probability:        float
    risk_level:         str
    dengue_positive:    bool
    message:            str
    feature_importance: dict
    model_info:         dict


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status":    "Nexus AI API is running",
        "name":      "Nexus AI",
        "version":   "2.1.0",
        "experiment": EXPERIMENT,
        "features":  FEATURE_COLS,
    }


@app.get("/health")
def health():
    return {"status": "ok", "model": type(model).__name__, "experiment": EXPERIMENT}


@app.get("/feature-importance")
def feature_importance():
    return {"feature_importance": FEATURE_IMPORTANCE, "features": FEATURE_COLS}


@app.get("/training-report")
def training_report():
    return TRAINING_REPORT


@app.post("/predict", response_model=PredictResponse)
def predict(
    data: PredictRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    try:
        input_dict = data.dict()
        X = preprocess_input(input_dict, scaler=scaler)

        prob       = float(model.predict_proba(X)[0][1])
        prediction = int(model.predict(X)[0])

        if prob < 0.35:
            risk_level = "Low"
            message = ("Blood parameters suggest low dengue risk. "
                       "Stay hydrated and monitor for symptoms.")
        elif prob < 0.65:
            risk_level = "Moderate"
            message = ("Moderate dengue risk detected. "
                       "Consult a doctor and monitor symptoms closely.")
        else:
            risk_level = "High"
            message = ("High dengue risk detected. "
                       "Please seek immediate medical attention.")

        # Persist screening record to tenant database if authenticated
        if current_user and current_user.tenant_id:
            try:
                record = ScreeningRecord(
                    tenant_id=current_user.tenant_id,
                    user_id=current_user.id,
                    patient_name=data.patient_name or "Not Specified",
                    age=data.age,
                    sex=data.sex,
                    haemoglobin=data.haemoglobin,
                    platelet_count=data.platelet_count,
                    pdw=data.pdw,
                    wbc_count=data.wbc_count,
                    risk_level=risk_level,
                    probability=round(prob, 4),
                    dengue_positive=bool(prediction == 1),
                    source_filename=data.source_filename or "Manual Entry",
                )
                db.add(record)
                db.commit()
            except Exception as db_err:
                print(f"[WARN] Could not persist tenant screening record: {db_err}")

        return PredictResponse(
            prediction=prediction,
            probability=round(prob, 4),
            risk_level=risk_level,
            dengue_positive=bool(prediction == 1),
            message=message,
            feature_importance=FEATURE_IMPORTANCE,
            model_info={
                "model":      type(model).__name__,
                "experiment": EXPERIMENT,
                "features":   FEATURE_COLS,
                "test_acc":   TRAINING_REPORT["best_metrics"].get("test_acc"),
                "f1":         TRAINING_REPORT["best_metrics"].get("f1"),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@app.get("/sample-input")
def sample_input():
    return {
        "dengue_sample": {
            "age": 30, "sex": "male", "haemoglobin": 12.0,
            "wbc_count": 2800, "differential_count": 1,
            "rbc_panel": 1, "platelet_count": 55000, "pdw": 15.5,
        },
        "healthy_sample": {
            "age": 45, "sex": "female", "haemoglobin": 14.0,
            "wbc_count": 7500, "differential_count": 1,
            "rbc_panel": 1, "platelet_count": 210000, "pdw": 32.0,
        },
        "note": f"Active features: {FEATURE_COLS}",
    }

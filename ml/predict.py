"""
predict.py
==========
CLI prediction using the trained model.
Usage: python predict.py
"""

import joblib
from preprocess import preprocess_input


def load_artifacts():
    model  = joblib.load("models/model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    return model, scaler


def predict(input_dict: dict) -> dict:
    model, scaler = load_artifacts()
    X = preprocess_input(input_dict, scaler=scaler)

    prob       = model.predict_proba(X)[0][1]
    prediction = int(model.predict(X)[0])

    if prob < 0.35:
        risk_level = "Low"
    elif prob < 0.65:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    return {
        "prediction":      prediction,
        "probability":     round(float(prob), 4),
        "risk_level":      risk_level,
        "dengue_positive": bool(prediction == 1),
    }


if __name__ == "__main__":
    # Sample: classic dengue presentation (low WBC, low platelets)
    sample_dengue = {
        "age":                30,
        "sex":                "male",
        "haemoglobin":        12.0,
        "wbc_count":          2800,
        "differential_count": 1,
        "rbc_panel":          1,
        "platelet_count":     55000,
        "pdw":                15.5,
    }

    # Sample: healthy presentation
    sample_healthy = {
        "age":                45,
        "sex":                "female",
        "haemoglobin":        14.0,
        "wbc_count":          7500,
        "differential_count": 1,
        "rbc_panel":          1,
        "platelet_count":     210000,
        "pdw":                32.0,
    }

    for label, sample in [("Dengue-like", sample_dengue),
                           ("Healthy-like", sample_healthy)]:
        print(f"\n[PREDICT] {label} Input:")
        for k, v in sample.items():
            print(f"  {k}: {v}")
        result = predict(sample)
        print(f"[PREDICT] Result: {result}")

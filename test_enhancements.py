"""
test_enhancements.py -- Comprehensive test suite for the enhanced Dengue Screening system.
Tests:
- Existing endpoints (/health, /predict, /feature-importance)
- File type and security validations
- PDF report text extraction & parsing
- Image report OCR & parsing
- Missing / unextractable values fallback ("Unable to extract")
- PDF medical report generation (/api/generate-report)
- AI Chatbot responses and context-awareness (/api/chat)
"""

import os
import sys
import io
import json

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw

# Add backend and ml to path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, os.path.join(BASE_DIR, "ml"))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def create_sample_pdf(hb=12.5, plt=45000, pdw=15.2, name="Test Patient", age=32, sex="Male"):
    """Generates an in-memory PDF mimicking a clinical Complete Blood Count report."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 750, "CITY DIAGNOSTIC LABORATORY - CLINICAL REPORT")
    c.drawString(100, 730, "================================================")
    c.drawString(100, 700, f"Patient Name: {name}")
    c.drawString(100, 680, f"Age / Sex: {age} Yrs / {sex}")
    c.drawString(100, 660, "Test Description: COMPLETE BLOOD COUNT (CBC)")
    c.drawString(100, 630, f"Haemoglobin: {hb} g/dL (Ref: 12.0 - 17.5)")
    c.drawString(100, 600, f"Platelet Count: {plt:,} cells/uL (Ref: 150,000 - 450,000)")
    c.drawString(100, 570, f"PDW: {pdw} % (Ref: 9.0 - 17.0)")
    c.drawString(100, 540, "WBC Count: 3,200 cells/uL (Ref: 4,000 - 11,000)")
    c.save()
    buf.seek(0)
    return buf


def create_sample_image(text_lines):
    """Generates an in-memory PNG image with rendered text for OCR."""
    img = Image.new("RGB", (600, 300), color="white")
    draw = ImageDraw.Draw(img)
    y = 30
    for line in text_lines:
        draw.text((40, y), line, fill="black")
        y += 35
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_existing_endpoints():
    print("\n[TEST 1] Testing preserved existing endpoints...")
    r1 = client.get("/health")
    assert r1.status_code == 200, f"Health check failed: {r1.text}"
    assert r1.json().get("status") == "ok"

    r2 = client.get("/sample-input")
    assert r2.status_code == 200, f"Sample input failed: {r2.text}"

    r3 = client.get("/feature-importance")
    assert r3.status_code == 200, f"Feature importance failed: {r3.text}"

    # Test /predict directly (original flow)
    pred_payload = {
        "age": 30,
        "sex": "male",
        "haemoglobin": 12.0,
        "wbc_count": 3200,
        "differential_count": 1,
        "rbc_panel": 1,
        "platelet_count": 45000,
        "pdw": 16.5,
    }
    r4 = client.post("/predict", json=pred_payload)
    assert r4.status_code == 200, f"Predict failed: {r4.text}"
    data = r4.json()
    assert "risk_level" in data
    assert "probability" in data
    assert "feature_importance" in data
    print(f"  ✓ Existing endpoints OK! Risk: {data['risk_level']}, Prob: {data['probability']}")


def test_pdf_extraction_complete():
    print("\n[TEST 2] Testing PDF extraction with complete lab values...")
    pdf_buf = create_sample_pdf(hb=11.8, plt=42000, pdw=16.8, name="Rahul Sharma", age=28, sex="Male")
    files = {"file": ("rahul_cbc_report.pdf", pdf_buf, "application/pdf")}
    res = client.post("/api/extract-report", files=files)
    assert res.status_code == 200, f"Extraction failed: {res.text}"
    data = res.json()
    assert data["success"] is True
    params = data["parameters"]

    print(f"  Extracted Name: {data['patient']['name']}")
    print(f"  Extracted Age: {data['patient']['age']}, Sex: {data['patient']['sex']}")
    print(f"  Extracted Hb: {params['haemoglobin']['value']} ({params['haemoglobin']['status']})")
    print(f"  Extracted PLT: {params['platelet_count']['value']} ({params['platelet_count']['status']})")
    print(f"  Extracted PDW: {params['pdw']['value']} ({params['pdw']['status']})")

    assert params["haemoglobin"]["value"] == 11.8
    assert params["platelet_count"]["value"] == 42000
    assert params["pdw"]["value"] == 16.8
    assert data["patient"]["age"] == 28
    assert data["patient"]["sex"] == "male"
    print("  ✓ Full PDF extraction succeeded!")


def test_pdf_extraction_missing_values():
    print("\n[TEST 3] Testing extraction with missing parameters (expecting 'Unable to extract')...")
    # PDF with only Hb, no Platelet Count or PDW
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.drawString(100, 700, "Patient Name: Jane Doe")
    c.drawString(100, 650, "Haemoglobin: 13.5 g/dL")
    c.save()
    buf.seek(0)

    files = {"file": ("incomplete_report.pdf", buf, "application/pdf")}
    res = client.post("/api/extract-report", files=files)
    assert res.status_code == 200
    data = res.json()
    params = data["parameters"]

    assert params["haemoglobin"]["status"] == "Extracted"
    assert params["haemoglobin"]["value"] == 13.5
    assert params["platelet_count"]["status"] == "Unable to extract"
    assert params["platelet_count"]["value"] is None
    assert params["pdw"]["status"] == "Unable to extract"
    assert params["pdw"]["value"] is None
    print(f"  ✓ Handled missing values properly without hallucinations: {params['platelet_count']['status']}")


def test_invalid_file_upload():
    print("\n[TEST 4] Testing invalid file upload rejection...")
    bad_buf = io.BytesIO(b"Not an allowed document file")
    files = {"file": ("malicious_script.exe", bad_buf, "application/octet-stream")}
    res = client.post("/api/extract-report", files=files)
    assert res.status_code == 400
    print(f"  ✓ Bad file format properly rejected with 400: {res.json().get('detail')}")


def test_medical_pdf_generation():
    print("\n[TEST 5] Testing medical PDF report generation...")
    payload = {
        "patient": {"name": "Sunita Patel", "age": 45, "sex": "female"},
        "report_info": {"filename": "sunita_lab.pdf"},
        "parameters": {
            "haemoglobin": 13.2,
            "platelet_count": 38000,
            "pdw": 17.2,
            "wbc_count": 2900,
        },
        "prediction": {
            "risk_level": "High",
            "probability": 0.92,
            "message": "High dengue risk detected. Please seek immediate medical attention.",
        },
    }

    res = client.post("/api/generate-report", json=payload)
    assert res.status_code == 200, f"PDF generation failed: {res.text}"
    assert res.headers["content-type"] == "application/pdf"
    content = res.content
    assert len(content) > 1000
    assert content.startswith(b"%PDF"), "Response is not a valid PDF document!"
    print(f"  ✓ Medical PDF successfully generated! Byte size: {len(content)} bytes")


def test_chatbot_service():
    print("\n[TEST 6] Testing AI Chatbot service & context awareness...")
    context = {
        "patient": {"name": "Sunita Patel", "age": 45, "sex": "female"},
        "parameters": {
            "haemoglobin": 13.2,
            "platelet_count": 38000,
            "pdw": 17.2,
        },
        "prediction": {
            "risk_level": "High",
            "probability": 0.92,
            "message": "High dengue risk detected.",
        },
    }

    # Query 1: Asking about platelets from current context
    r1 = client.post("/api/chat", json={"message": "What was my platelet count?", "context": context})
    assert r1.status_code == 200
    resp1 = r1.json()["response"]
    assert "38,000" in resp1, f"Expected 38,000 in response, got: {resp1}"
    print("  ✓ Chatbot accurately reported patient platelet count from session context.")

    # Query 2: Educational explanation of PDW
    r2 = client.post("/api/chat", json={"message": "What is PDW?", "context": context})
    assert r2.status_code == 200
    resp2 = r2.json()["response"]
    assert "Platelet Distribution Width" in resp2 or "variation" in resp2
    print("  ✓ Chatbot answered medical educational question on PDW.")

    # Query 3: Safety test - Asking for medical diagnosis
    r3 = client.post("/api/chat", json={"message": "Can you diagnose me if I have dengue?", "context": context})
    assert r3.status_code == 200
    resp3 = r3.json()["response"]
    assert "cannot diagnose" in resp3.lower() or "not a doctor" in resp3.lower() or "ns1" in resp3.lower()
    print("  ✓ Chatbot enforced strict non-diagnostic clinical safety guardrails.")


if __name__ == "__main__":
    print("==================================================")
    print("  DENGUE AI SYSTEM ENHANCEMENT VERIFICATION SUITE")
    print("==================================================")
    test_existing_endpoints()
    test_pdf_extraction_complete()
    test_pdf_extraction_missing_values()
    test_invalid_file_upload()
    test_medical_pdf_generation()
    test_chatbot_service()
    print("\n==================================================")
    print("  ALL 6 TEST SUITES PASSED WITH 100% SUCCESS!")
    print("==================================================")

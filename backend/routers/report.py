"""
report.py -- Router for generating downloadable medical-style summary reports.
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from services.pdf_generator import generate_patient_pdf

router = APIRouter(prefix="/api", tags=["Report Generation"])


class PatientDetails(BaseModel):
    name: Optional[str] = "Not Specified"
    age: Optional[float] = None
    sex: Optional[str] = "Not Specified"


class ReportParameters(BaseModel):
    haemoglobin: Optional[float] = None
    platelet_count: Optional[float] = None
    pdw: Optional[float] = None
    wbc_count: Optional[float] = 0.0


class PredictionSummary(BaseModel):
    risk_level: str = "Low"
    probability: float = 0.0
    message: Optional[str] = "Screening complete."


class GenerateReportRequest(BaseModel):
    patient: Optional[PatientDetails] = None
    report_info: Optional[Dict[str, Any]] = None
    parameters: ReportParameters
    prediction: PredictionSummary


@router.post("/generate-report")
async def generate_report_pdf(payload: GenerateReportRequest):
    """
    Generates and streams a downloadable PDF medical summary report.
    """
    try:
        data = payload.dict()
        pdf_buffer = generate_patient_pdf(data)
        filename_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Dengue_Screening_Report_{filename_ts}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate medical PDF report: {str(e)}",
        )

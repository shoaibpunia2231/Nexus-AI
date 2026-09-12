"""
extract.py -- Router for patient blood test report file upload and laboratory data extraction.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from services.security import validate_upload_file, save_temp_upload
from services.extractor import extract_report_data

router = APIRouter(prefix="/api", tags=["Report Extraction"])


@router.post("/extract-report")
async def extract_report(file: UploadFile = File(...)):
    """
    Receives an uploaded PDF or image (JPG, PNG) medical report,
    extracts laboratory parameters (Haemoglobin, Platelet Count, PDW, Age, Sex),
    validates them, and returns structured data with confidence status.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file was provided.")

    ext = validate_upload_file(file)

    try:
        with save_temp_upload(file, ext) as temp_path:
            result = extract_report_data(temp_path, file.filename)
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the report: {str(e)}",
        )

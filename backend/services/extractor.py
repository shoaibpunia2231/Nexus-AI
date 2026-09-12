"""
extractor.py -- Extraction and normalization of laboratory report parameters.
Supports digital PDFs, scanned PDFs, and image formats (JPG, PNG).
"""

import os
import re
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy singleton for EasyOCR Reader to avoid reinitializing on every request
_OCR_READER = None


def get_ocr_reader():
    global _OCR_READER
    if _OCR_READER is None:
        try:
            import easyocr
            # Disable GPU for lightweight server environments and quiet downloads
            _OCR_READER = easyocr.Reader(["en"], gpu=False, verbose=False)
            logger.info("EasyOCR Reader initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize EasyOCR: {e}")
            _OCR_READER = None
    return _OCR_READER


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file using pdfplumber, falling back to pypdf,
    and then OCR if the document is a scanned image.
    """
    text_content = []

    # 1. Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_content.append(t)
    except Exception as e:
        logger.debug(f"pdfplumber extraction failed or skipped: {e}")

    # 2. Try pypdf fallback if empty
    if not text_content or len("\n".join(text_content).strip()) < 30:
        try:
            import pypdf
            reader = pypdf.PdfReader(pdf_path)
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    text_content.append(t)
        except Exception as e:
            logger.debug(f"pypdf extraction failed or skipped: {e}")

    extracted_text = "\n".join(text_content).strip()

    # 3. If still very sparse, it is likely a scanned document -> OCR pages
    if len(extracted_text) < 40:
        logger.info("PDF appears to be scanned; falling back to OCR on rendered pages.")
        ocr_text = []
        try:
            import fitz  # PyMuPDF
            reader = get_ocr_reader()
            if reader:
                doc = fitz.open(pdf_path)
                for page_num in range(min(len(doc), 3)):  # First 3 pages max
                    page = doc[page_num]
                    pix = page.get_pixmap(dpi=150)
                    img_bytes = pix.tobytes("png")
                    results = reader.readtext(img_bytes, detail=0)
                    ocr_text.extend(results)
                extracted_text = "\n".join(ocr_text).strip()
        except Exception as e:
            logger.warning(f"PyMuPDF + EasyOCR fallback failed: {e}")

    return extracted_text


def extract_text_from_image(image_path: str) -> str:
    """
    Extracts text from an image file using EasyOCR.
    """
    reader = get_ocr_reader()
    if not reader:
        return ""
    try:
        results = reader.readtext(image_path, detail=0)
        return "\n".join(results)
    except Exception as e:
        logger.error(f"Image OCR error on {image_path}: {e}")
        return ""


def clean_line(line: str) -> str:
    """Cleans common OCR noise while keeping delimiters."""
    return re.sub(r"[ \t]+", " ", line).strip()


def parse_patient_name(text: str) -> Optional[str]:
    """Attempts to extract patient name from header fields."""
    patterns = [
        r"(?:Patient\s*Name|Pt\.?\s*Name|Name\s*of\s*Patient|Name)\s*[:\-\—]\s*([A-Za-z\.\s]{3,35})",
        r"(?:Mr\.|Mrs\.|Ms\.|Master|Dr\.)\s+([A-Za-z\s]{3,30})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            # Avoid matching headers like 'Name Age Sex'
            if not any(w in name.lower() for w in ["age", "sex", "gender", "date", "report", "test"]):
                return name.title()
    return None


def parse_age(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Attempts to extract patient age in years."""
    patterns = [
        r"(?:Age|Patient\s*Age)\s*[:\-\—]?\s*(\d{1,3})\s*(?:Yrs?|Years?|Y/O|Y)?\b",
        r"(\d{1,3})\s*(?:Yrs?|Years?|Y/O)\b",
        r"(?:Age\s*/\s*Sex|Age\s*/\s*Gender)\s*[:\-\—]?\s*(\d{1,3})",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = float(m.group(1))
            if 0 < val <= 120:
                return val, m.group(0)
    return None, None


def parse_sex(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Attempts to extract biological sex / gender."""
    patterns = [
        r"(?:Sex|Gender)\s*[:\-\—]?\s*(Male|Female|Child|Boy|Girl|M|F)\b",
        r"\b(?:Age\s*/\s*Sex|Age\s*/\s*Gender)\s*[:\-\—]?\s*\d{1,3}\s*[/,\-\s]\s*(Male|Female|Child|Boy|Girl|M|F)\b",
        r"\b(Male|Female)\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).upper()
            if raw in ("M", "MALE", "BOY"):
                return "male", m.group(0)
            elif raw in ("F", "FEMALE", "GIRL"):
                return "female", m.group(0)
            elif raw in ("CHILD",):
                return "child", m.group(0)
    return None, None


def parse_haemoglobin(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extracts Haemoglobin / Hemoglobin level (g/dL).
    Normal biological range: ~2.0 - 25.0 g/dL.
    """
    patterns = [
        # Example: "Haemoglobin: 12.5 g/dL" or "Hb 12.5"
        r"(?:Ha?emoglobin|Hb|HGB|Total\s*Ha?emoglobin)\b[^\n\d]*?(\d{1,2}(?:\.\d{1,2})?)\s*(?:g/dL|gm/dl|g/l|g%)?",
    ]
    for pat in patterns:
        matches = re.finditer(pat, text, re.IGNORECASE)
        for m in matches:
            try:
                val = float(m.group(1))
                # If lab reported in g/L (e.g. 125 g/L), convert to g/dL
                if 50 <= val <= 220 and "g/l" in m.group(0).lower():
                    val = val / 10.0
                if 2.0 <= val <= 25.0:
                    return val, m.group(0).strip()
            except ValueError:
                continue
    return None, None


def parse_platelet_count(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extracts Platelet Count.
    Handles standard integer counts (e.g. 45,000 or 45000),
    lakhs notation (e.g. 0.45 or 1.5 Lakh/cumm),
    and thousand multiplier notation (e.g. 45 x10^3/uL).
    """
    # 1. Lakhs/cumm notation: e.g. 0.45 Lakhs, 1.80 Lacs
    lakh_pattern = r"(?:Platelet\s*Count|Platelets|PLT|Total\s*Platelet\s*Count|Thrombocytes?)\b[^\n\d]*?(\d{1,2}(?:\.\d{1,3})?)\s*(?:Lakhs?|Lacs?|L|x10\^5)"
    m = re.search(lakh_pattern, text, re.IGNORECASE)
    if m:
        try:
            val = float(m.group(1)) * 100000
            if 5000 <= val <= 1500000:
                return float(round(val)), m.group(0).strip()
        except ValueError:
            pass

    # 2. x10^3/uL or thousand multiplier: e.g. "PLT: 45 x10^3" or "Platelets (10^3/uL) : 45"
    thousand_mult = r"(?:Platelet\s*Count|Platelets|PLT)[^\n\d]*?\(?(?:x\s*10\^?3|10\^?3/uL|thou/uL)\)?[^\n\d]*?(\d{1,3}(?:\.\d{1,2})?)"
    m = re.search(thousand_mult, text, re.IGNORECASE)
    if m:
        try:
            val = float(m.group(1)) * 1000
            if 5000 <= val <= 1500000:
                return float(round(val)), m.group(0).strip()
        except ValueError:
            pass

    # 3. Standard counts: e.g. "Platelet Count: 45,000 /cumm" or "PLT 150000"
    std_pattern = r"(?:Platelet\s*Count|Total\s*Platelet\s*Count|Platelets|PLT|Thrombocytes?)\b[^\n\d]*?(\d{1,3}(?:,\d{3})+|\d{4,7})\b"
    matches = re.finditer(std_pattern, text, re.IGNORECASE)
    for match in matches:
        try:
            raw_str = match.group(1).replace(",", "")
            val = float(raw_str)
            if 5000 <= val <= 1500000:
                return val, match.group(0).strip()
        except ValueError:
            continue

    return None, None


def parse_pdw(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extracts Platelet Distribution Width (PDW).
    Normal biological range: 8.0 - 30.0 (% or fL).
    """
    patterns = [
        r"(?:PDW|Platelet\s*Distribution\s*Width)[\s:\-\—]*?(\d{1,2}(?:\.\d{1,2})?)\s*(?:%|fL|fl)?",
    ]
    for pat in patterns:
        matches = re.finditer(pat, text, re.IGNORECASE)
        for m in matches:
            try:
                val = float(m.group(1))
                if 5.0 <= val <= 40.0:
                    return val, m.group(0).strip()
            except ValueError:
                continue
    return None, None


def parse_wbc_count(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Extracts WBC / Total Leukocyte Count (TLC).
    Normal biological range: ~1,000 - 100,000 cells/µL.
    """
    patterns = [
        r"(?:WBC(?:\s*Count)?|Total\s*Leukocyte\s*Count|TLC|White\s*Blood\s*Cells?)\b[^\n\d]*?(\d{1,3}(?:,\d{3})+|\d{4,6})\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            try:
                val = float(m.group(1).replace(",", ""))
                if 1000 <= val <= 100000:
                    return val, m.group(0).strip()
            except ValueError:
                pass
    return None, None


def extract_report_data(file_path: str, filename: str) -> Dict[str, Any]:
    """
    Main extraction pipeline:
    1. Determines file format (PDF vs Image).
    2. Extracts full text via parser or OCR.
    3. Searches and extracts laboratory parameters.
    4. Validates parameters. If unconfident or absent, explicitly sets "Unable to extract".
    """
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        raw_text = extract_text_from_pdf(file_path)
    elif ext in (".jpg", ".jpeg", ".png"):
        raw_text = extract_text_from_image(file_path)
    else:
        raw_text = ""

    if not raw_text or len(raw_text.strip()) < 10:
        return {
            "success": False,
            "filename": filename,
            "error": "We could not read this report. Please upload a clearer PDF/image or enter the values manually.",
            "raw_text": "",
            "patient": {"name": None, "age": None, "sex": None},
            "parameters": {
                "haemoglobin": {"value": None, "status": "Unable to extract", "unit": "g/dL"},
                "platelet_count": {"value": None, "status": "Unable to extract", "unit": "cells/µL"},
                "pdw": {"value": None, "status": "Unable to extract", "unit": "%"},
                "wbc_count": {"value": None, "status": "Unable to extract", "unit": "cells/µL"},
            },
        }

    # Extract fields
    patient_name = parse_patient_name(raw_text)
    age_val, age_src = parse_age(raw_text)
    sex_val, sex_src = parse_sex(raw_text)
    hb_val, hb_src = parse_haemoglobin(raw_text)
    plt_val, plt_src = parse_platelet_count(raw_text)
    pdw_val, pdw_src = parse_pdw(raw_text)
    wbc_val, wbc_src = parse_wbc_count(raw_text)

    parameters = {
        "haemoglobin": {
            "value": hb_val,
            "status": "Extracted" if hb_val is not None else "Unable to extract",
            "unit": "g/dL",
            "source_snippet": hb_src,
            "reference_range": "12.0 - 17.5 g/dL",
        },
        "platelet_count": {
            "value": plt_val,
            "status": "Extracted" if plt_val is not None else "Unable to extract",
            "unit": "cells/µL",
            "source_snippet": plt_src,
            "reference_range": "150,000 - 450,000 cells/µL",
        },
        "pdw": {
            "value": pdw_val,
            "status": "Extracted" if pdw_val is not None else "Unable to extract",
            "unit": "%",
            "source_snippet": pdw_src,
            "reference_range": "9.0 - 17.0 %",
        },
        "wbc_count": {
            "value": wbc_val,
            "status": "Extracted" if wbc_val is not None else "Unable to extract",
            "unit": "cells/µL",
            "source_snippet": wbc_src,
            "reference_range": "4,000 - 11,000 cells/µL",
        },
    }

    patient = {
        "name": patient_name or "Not Specified",
        "age": age_val,
        "age_status": "Extracted" if age_val is not None else "Unable to extract",
        "sex": sex_val,
        "sex_status": "Extracted" if sex_val is not None else "Unable to extract",
    }

    # Count how many core parameters were successfully extracted
    extracted_count = sum(1 for p in [hb_val, plt_val, pdw_val] if p is not None)

    return {
        "success": True,
        "filename": filename,
        "extracted_count": extracted_count,
        "total_required": 3,
        "patient": patient,
        "parameters": parameters,
        "raw_text_length": len(raw_text),
        "notes": (
            "All parameters extracted."
            if extracted_count == 3
            else f"{3 - extracted_count} core parameter(s) could not be detected and require manual confirmation."
        ),
    }

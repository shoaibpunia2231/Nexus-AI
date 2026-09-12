"""
security.py -- Upload validation, file sanitization, and secure temporary storage.
"""

import os
import shutil
import tempfile
import uuid
from contextlib import contextmanager
from typing import Generator
from fastapi import HTTPException, UploadFile

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
}

# Maximum file size: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def validate_upload_file(file: UploadFile) -> str:
    """
    Validates uploaded file MIME type and extension.
    Returns the normalized extension.
    """
    content_type = (file.content_type or "").lower().strip()
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if content_type not in ALLOWED_MIME_TYPES:
        # Fallback to extension check if content_type is octet-stream
        ext_to_mime = {v: k for k, v in ALLOWED_MIME_TYPES.items()}
        if ext not in ext_to_mime:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file format '{content_type or ext}'. "
                    "Please upload a medical report in PDF, JPEG, or PNG format."
                ),
            )
        return ext

    return ALLOWED_MIME_TYPES[content_type]


@contextmanager
def save_temp_upload(file: UploadFile, extension: str) -> Generator[str, None, None]:
    """
    Saves an uploaded file to a secure temporary location, enforces size limits,
    yields the absolute file path, and guarantees deletion on exit.
    """
    temp_dir = tempfile.mkdtemp(prefix="dengue_report_")
    safe_filename = f"{uuid.uuid4().hex}{extension}"
    temp_path = os.path.join(temp_dir, safe_filename)

    total_bytes = 0
    try:
        with open(temp_path, "wb") as buffer:
            while chunk := file.file.read(1024 * 1024):  # 1MB chunks
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="File is too large. Maximum allowed size is 10 MB.",
                    )
                buffer.write(chunk)

        yield temp_path
    finally:
        # Clean up temporary directory and files immediately
        shutil.rmtree(temp_dir, ignore_errors=True)

# app/upload.py
import os
import uuid
import json
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document
from app.pipeline_runner import run_pipeline

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword"
}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB default

router = APIRouter()

# -------------------- HELPER FUNCTION --------------------
def format_pipeline_result(pipeline_output):
    """
    Converts raw pipeline output into user-friendly format with:
    - original_clause
    - corrected_clause (first suggestion if exists)
    - errors (all errors combined)
    """
    formatted = []
    for item in pipeline_output:
        clause_text = item.get("clause", "")
        suggestions = item.get("suggestions", [])
        corrected = suggestions[0]["suggestion"] if suggestions else clause_text

        errors = []
        for err_type in ["grammatical", "financial", "legal"]:
            for e in item.get("errors", {}).get(err_type, []):
                if "error" in e:
                    errors.append(f"[{err_type}] {e['error']}")
                elif "clause" in e:
                    errors.append(f"[{err_type}] {e['clause']}")
        
        formatted.append({
            "original_clause": clause_text,
            "corrected_clause": corrected,
            "errors": errors
        })
    return formatted
# ----------------------------------------------------------

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    x_user_id: int | None = Header(None),
    db: Session = Depends(get_db)
):
    # Validate MIME type
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Validate file size
    contents = await file.read()
    size = len(contents)
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # Save file with unique name
    unique_name = f"{uuid.uuid4().hex}{Path(file.filename).suffix}"
    file_path = UPLOAD_DIR / unique_name
    with open(file_path, "wb") as f:
        f.write(contents)

    # Save metadata to database
    doc = Document(
        original_filename=file.filename,
        storage_filename=unique_name,
        storage_path=str(file_path.resolve()),
        content_type=file.content_type,
        size=size,
        uploaded_by=x_user_id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    try:
        # Run pipeline synchronously
        raw_pipeline_result = run_pipeline(str(file_path))

        # Format pipeline output
        formatted_result = format_pipeline_result(raw_pipeline_result)

        # Save formatted pipeline result in DB
        doc.pipeline_result = json.dumps(formatted_result)
        db.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

    return {
        "message": "File uploaded and processed successfully.",
        "doc_id": doc.id,
        "file_path": str(file_path),
        "pipeline_result": formatted_result  # <-- formatted, user-friendly output
    }

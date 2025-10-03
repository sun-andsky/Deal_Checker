import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document
from app.pipeline_runner import run_pipeline  # single-file pipeline

# ------------------------
# Config
# ------------------------
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword"
}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB default

router = APIRouter()

# ------------------------
# Upload endpoint
# ------------------------
@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    x_user_id: int | None = Header(None),
    db: Session = Depends(get_db)
):
    # 1️⃣ Validate MIME type
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 2️⃣ Validate file size
    contents = await file.read()
    size = len(contents)
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # 3️⃣ Save file with unique name
    unique_name = f"{uuid.uuid4().hex}{Path(file.filename).suffix}"
    file_path = UPLOAD_DIR / unique_name
    with open(file_path, "wb") as f:
        f.write(contents)

    # 4️⃣ Save metadata to database
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

    # 5️⃣ Run AI pipeline for this single file
    try:
        pipeline_result = run_pipeline(str(file_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

    # 6️⃣ Return full JSON response
    return {
        "message": "uploaded and processed",
        "doc_id": doc.id,
        "path": doc.storage_path,
        "pipeline_result": pipeline_result
    }

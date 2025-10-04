# main.py
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from pathlib import Path
import uuid
import os
import json

# --- Internal imports ---
from app.database import engine, Base, get_db
from app.models import Document
from app.pipeline_runner import run_pipeline
from app.routers.auth_routes import router as auth_router
from app.auth import get_current_active_user
from app.schemas import UserOut

# --- Initialize App ---
app = FastAPI(title="AI Deal Checker + Auth System")

# --- Create DB Tables ---
Base.metadata.create_all(bind=engine)

# --- Include Routers ---
app.include_router(auth_router)

# --- Configurations ---
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_MIMES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword"
}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 20 * 1024 * 1024))  # 20MB default


# --- Protected route example ---
@app.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_active_user)):
    return current_user


# --- File upload + pipeline endpoint ---
@app.post("/upload_and_run_pipeline", response_model=None)
async def upload_and_run_pipeline(
    file: UploadFile = File(...),
    x_user_id: int | None = Header(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user)  # 🔒 Ensure only logged-in users can upload
):
    # Validate MIME type
    if file.content_type not in ALLOWED_MIMES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Read file contents
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    # Save file
    unique_name = f"{uuid.uuid4().hex}{Path(file.filename).suffix}"
    file_path = UPLOAD_DIR / unique_name
    with open(file_path, "wb") as f:
        f.write(contents)

    # Save metadata to DB
    doc = Document(
        original_filename=file.filename,
        storage_filename=unique_name,
        storage_path=str(file_path.resolve()),
        content_type=file.content_type,
        size=len(contents),
        uploaded_by=x_user_id or current_user.id  # ✅ Prefer token user ID
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Run pipeline synchronously
    try:
        pipeline_result = run_pipeline(str(file_path))
        doc.pipeline_result = json.dumps(pipeline_result)
        db.commit()
    except Exception as e:
        return {
            "message": "Pipeline failed",
            "error": str(e),
            "doc_id": doc.id,
            "file_path": str(file_path)
        }

    return {
        "message": "File uploaded and pipeline completed successfully",
        "doc_id": doc.id,
        "file_path": str(file_path),
        "pipeline_result": pipeline_result
    }

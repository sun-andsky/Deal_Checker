# app/main.py
from fastapi import FastAPI
from app.database import Base, engine
from app.routers.files import router as files_router
from pydantic import BaseModel
import os

# Import NLP suggestion logic
from app.suggest import generate_suggestions

# Import OCR + NLP pipeline modules
from extract_text import main as ocr_main
from nlp_clause_extraction import extract_clauses, save_clauses
from hybrid_classification import classify_clause_hybrid

# -----------------------------
# Database setup
# -----------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Deal Checker")
app.include_router(files_router, prefix="/api")

# -----------------------------
# Pydantic Models
# -----------------------------
class ClauseRequest(BaseModel):
    clause: str
    error_type: str = "general"

class SuggestionResponse(BaseModel):
    original: str
    suggestions: list

class ApplyRequest(BaseModel):
    clause_id: int
    suggestion: str

# -----------------------------
# API Endpoints
# -----------------------------
@app.post("/api/get_suggestions", response_model=SuggestionResponse)
def get_suggestions(request: ClauseRequest):
    """
    Dynamic suggestions API.
    Returns grammar or paraphrase suggestions based on error_type.
    """
    suggestions = generate_suggestions(request.clause, request.error_type)
    return {"original": request.clause, "suggestions": suggestions}

@app.post("/api/apply_suggestion")
def apply_suggestion(request: ApplyRequest):
    """
    Apply a suggestion (placeholder, connect to DB later if needed)
    """
    return {"message": "Clause updated successfully", "updated_clause": request.suggestion}

# -----------------------------
# Main Pipeline
# -----------------------------
EXTRACTED_FOLDER = "extracted_text"

def main_pipeline():
    """
    Runs the OCR -> Clause Extraction -> Classification -> Suggestions pipeline.
    Prints results for each clause.
    """
    os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
    extracted_data = ocr_main()

    for data in extracted_data:
        text = data['text']
        document_id = data['document_id']

        clauses = extract_clauses(text)
        clauses_file = os.path.join(EXTRACTED_FOLDER, f"clauses_{document_id}.txt")
        save_clauses(clauses, clauses_file)

        print(f"\nDocument: {data['file_name']} (ID: {document_id})")
        for idx, clause in enumerate(clauses, 1):
            label = classify_clause_hybrid(clause)
            print(f"\nClause {idx}: {clause}")
            print(f"Issue Type: {label}")

            # 🔹 Generate suggestions dynamically
            suggestions = generate_suggestions(clause, label)
            if suggestions:
                print("Suggestions:")
                for s in suggestions:
                    print(f"- {s['suggestion']} (source: {s['source']})")
            else:
                print("No suggestions available.")

            print("-" * 50)

if __name__ == "__main__":
    main_pipeline()

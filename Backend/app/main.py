from fastapi import FastAPI
from app.database import Base, engine
from app.routers.files import router as files_router
from pydantic import BaseModel
import os

# Import your NLP suggestion logic
from app.suggest import generate_suggestions

# Import your OCR + NLP pipeline modules
from extract_text import main as ocr_main
from nlp_clause_extraction import extract_clauses, save_clauses
from hybrid_classification import classify_clause_hybrid

# DB setup
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
    suggestions = generate_suggestions(request.clause, request.error_type)
    return {"original": request.clause, "suggestions": suggestions}

@app.post("/api/apply_suggestion")
def apply_suggestion(request: ApplyRequest):
    # Later: connect with DB update
    return {"message": "Clause updated successfully", "updated_clause": request.suggestion}

# -----------------------------
# Main Pipeline
# -----------------------------
EXTRACTED_FOLDER = "extracted_text"

def main_pipeline():
    extracted_data = ocr_main()
    for data in extracted_data:
        text = data['text']
        document_id = data['document_id']

        clauses = extract_clauses(text)
        clauses_file = os.path.join(EXTRACTED_FOLDER, f"clauses_{document_id}.txt")
        save_clauses(clauses, clauses_file)

        print(f"\nClassification for {data['file_name']}:")
        for clause in clauses:
            label = classify_clause_hybrid(clause)
            print(f"Clause: {clause}")
            print(f"Issue Type: {label}")

            # 🔹 Directly use suggest.py here
            suggestions = generate_suggestions(clause, label)
            if suggestions:
                print("Suggestions:")
                for s in suggestions:
                    print(f"- {s['suggestion']} (source: {s['source']})")

            print("-" * 50)

if __name__ == "__main__":
    main_pipeline()

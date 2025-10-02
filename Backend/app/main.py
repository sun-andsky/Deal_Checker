import os
from extract_text import main as ocr_main
from nlp_clause_extraction import extract_clauses, save_clauses
from hybrid_classification import classify_clause_hybrid

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
            print("-"*50)

if __name__ == "__main__":
    main_pipeline()

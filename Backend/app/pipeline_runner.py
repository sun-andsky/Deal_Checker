import os
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import pytesseract
from rapidfuzz import fuzz  # For fuzzy matching

# Local imports
from app.extract_ocr import ocr_pdf, ocr_image, ocr_docx
from app.nlp_clause_extraction import extract_clauses, save_clauses
from app.hybrid_classification import classify_clause_hybrid
from app.suggest import generate_suggestions
from app.error_detection import (
    detect_grammatical_errors,
    detect_financial_errors,
    detect_legal_errors
)

# ------------------------ Folders ------------------------
EXTRACTED_FOLDER = "extracted_text"
HIGHLIGHTED_FOLDER = "highlighted"

os.makedirs(EXTRACTED_FOLDER, exist_ok=True)
os.makedirs(HIGHLIGHTED_FOLDER, exist_ok=True)

# ------------------------ Highlight Colors ------------------------
COLOR_MAP_PDF = {
    "grammatical": (1, 1, 0),   # yellow
    "financial": (0, 1, 0),     # green
    "legal": (0, 0, 1),         # blue
    "unknown": (0.5, 0.5, 0.5)  # gray
}

COLOR_MAP_IMAGE = {
    "grammatical": "yellow",
    "financial": "green",
    "legal": "blue",
    "unknown": "gray"
}

# ------------------------ Highlighting Functions ------------------------
def highlight_pdf(file_path, clauses, output_file):
    """Highlight extracted clauses inside PDF"""
    doc = fitz.open(file_path)
    for page in doc:
        text = page.get_text()
        for clause in clauses:
            label = classify_clause_hybrid(clause)
            # Fuzzy match clause inside page text
            for inst in text.split("\n"):
                if fuzz.partial_ratio(clause, inst) > 85:
                    areas = page.search_for(inst)
                    for area in areas:
                        annot = page.add_highlight_annot(area)
                        annot.set_colors(stroke=COLOR_MAP_PDF.get(label, (0.5, 0.5, 0.5)))
                        annot.update()
    doc.save(output_file)


def highlight_image(file_path, clauses, output_file):
    """Highlight extracted clauses inside image"""
    image = Image.open(file_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    draw = ImageDraw.Draw(image)

    for clause in clauses:
        label = classify_clause_hybrid(clause)
        words = clause.split()
        for i in range(len(data["text"]) - len(words) + 1):
            text_segment = " ".join(data["text"][i:i+len(words)])
            if fuzz.ratio(clause, text_segment) > 85:
                x0 = min(data["left"][i:i+len(words)])
                y0 = min(data["top"][i:i+len(words)])
                x1 = max([data["left"][i+j] + data["width"][i+j] for j in range(len(words))])
                y1 = max([data["top"][i+j] + data["height"][i+j] for j in range(len(words))])
                draw.rectangle([x0, y0, x1, y1], outline=COLOR_MAP_IMAGE.get(label, "gray"), width=3)
    image.save(output_file)

# ------------------------ Main Pipeline ------------------------
def run_pipeline(file_path: str):
    """Main end-to-end pipeline runner"""
    ext = os.path.splitext(file_path)[1].lower()

    # 1️⃣ OCR
    if ext == ".pdf":
        text = ocr_pdf(file_path)
    elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
        text = ocr_image(file_path)
    elif ext == ".docx":
        text = ocr_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    # 2️⃣ Extract clauses
    clauses = extract_clauses(text)

    # 3️⃣ Save extracted clauses
    clauses_file = os.path.join(EXTRACTED_FOLDER, f"{os.path.basename(file_path)}_clauses.txt")
    save_clauses(clauses, clauses_file)

    # 4️⃣ Classification + Suggestions + Error Detection
    results = []
    for clause in clauses:
        label = classify_clause_hybrid(clause)
        suggestions = generate_suggestions(clause, label)
        errors = {
            "grammatical": detect_grammatical_errors(clause),
            "financial": detect_financial_errors(clause),
            "legal": detect_legal_errors(clause)
        }
        results.append({
            "clause": clause,
            "label": label,
            "suggestions": suggestions,
            "errors": errors
        })

    return results


# ------------------------ Runner ------------------------
if __name__ == "__main__":
    sample_file = "uploads/sample.pdf"  # 👈 Change this to test your own file
    output = run_pipeline(sample_file)

    print("\n📌 Pipeline Results:")
    for r in output:
        print(json.dumps(r, indent=2, ensure_ascii=False))

    # Optional: generate highlighted version
    highlight_out = os.path.join(HIGHLIGHTED_FOLDER, f"highlighted_{os.path.basename(sample_file)}")
    if sample_file.endswith(".pdf"):
        highlight_pdf(sample_file, [r["clause"] for r in output], highlight_out)
    elif sample_file.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff")):
        highlight_image(sample_file, [r["clause"] for r in output], highlight_out)
    print(f"\n✅ Highlighted file saved at: {highlight_out}")


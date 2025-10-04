import os
import json
import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import pytesseract
import docx
from rapidfuzz import fuzz  # For fuzzy matching

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
    "grammatical": (1, 1, 0),
    "financial": (0, 1, 0),
    "legal": (0, 0, 1),
    "unknown": (0.5, 0.5, 0.5)
}

COLOR_MAP_IMAGE = {
    "grammatical": "yellow",
    "financial": "green",
    "legal": "blue",
    "unknown": "gray"
}

# ------------------------ OCR Functions ------------------------
def ocr_pdf(file_path):
    text_pages = []
    doc = fitz.open(file_path)
    for page in doc:
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text_pages.append(pytesseract.image_to_string(img))
    return "\n".join(text_pages)

def ocr_image(file_path):
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)

def ocr_docx(file_path):
    doc = docx.Document(file_path)
    full_text = [p.text for p in doc.paragraphs]
    return "\n".join(full_text)

# ------------------------ Highlighting Functions ------------------------
def highlight_pdf(file_path, clauses, output_file):
    doc = fitz.open(file_path)
    for page in doc:
        text = page.get_text()
        for clause in clauses:
            label = classify_clause_hybrid(clause)
            # Fuzzy search for approximate matches
            for inst in text.split("\n"):
                if fuzz.partial_ratio(clause, inst) > 85:
                    areas = page.search_for(inst)
                    for area in areas:
                        annot = page.add_highlight_annot(area)
                        annot.set_colors(stroke=COLOR_MAP_PDF.get(label, (0.5,0.5,0.5)))
                        annot.update()
    doc.save(output_file)

def highlight_image(file_path, clauses, output_file):
    image = Image.open(file_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    draw = ImageDraw.Draw(image)

    for clause in clauses:
        label = classify_clause_hybrid(clause)
        words = clause.split()
        for i in range(len(data["text"]) - len(words) + 1):
            # Fuzzy matching
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

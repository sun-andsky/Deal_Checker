import os
from extract_text import main as ocr_main  # Your existing OCR module
from hybrid_classification.classify_clauses import classify_clause_hybrid
from nlp_clause_extraction.extract_clauses import extract_clauses, save_clauses  # adjust import as needed

import fitz  # PyMuPDF
from PIL import Image, ImageDraw
import pytesseract

# Folder to save extracted clauses
EXTRACTED_FOLDER = "extracted_text"
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

# -------- Color Mapping --------
COLOR_MAP_PDF = {
    "grammatical": (1, 1, 0),  # yellow
    "financial": (0, 1, 0),    # green
    "legal": (0, 0, 1),        # blue
    "unknown": (0.5, 0.5, 0.5) # gray
}

COLOR_MAP_IMAGE = {
    "grammatical": "yellow",
    "financial": "green",
    "legal": "blue",
    "unknown": "gray"
}

# -------- Highlight PDF --------
def highlight_pdf(file_path, clauses, output_file):
    doc = fitz.open(file_path)
    for page in doc:
        text = page.get_text()
        page_clauses = [clause for clause in clauses if clause in text]

        for clause in page_clauses:
            label = classify_clause_hybrid(clause)
            areas = page.search_for(clause)
            for area in areas:
                annot = page.add_highlight_annot(area)
                annot.set_colors(stroke=COLOR_MAP_PDF.get(label, (0.5, 0.5, 0.5)))
                annot.update()
    doc.save(output_file)
    print(f"Highlighted PDF saved as: {output_file}")

# -------- Highlight Image --------
def highlight_image(file_path, clauses, output_file):
    image = Image.open(file_path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    draw = ImageDraw.Draw(image)

    for clause in clauses:
        label = classify_clause_hybrid(clause)
        clause_words = clause.split()
        for i in range(len(data['text']) - len(clause_words) + 1):
            if data['text'][i:i+len(clause_words)] == clause_words:
                x0 = min(data['left'][i:i+len(clause_words)])
                y0 = min(data['top'][i:i+len(clause_words)])
                x1 = max([data['left'][i+j] + data['width'][i+j] for j in range(len(clause_words))])
                y1 = max([data['top'][i+j] + data['height'][i+j] for j in range(len(clause_words))])
                draw.rectangle([x0, y0, x1, y1], outline=COLOR_MAP_IMAGE.get(label, "gray"), width=3)

    image.save(output_file)
    print(f"Highlighted image saved as: {output_file}")

# -------- Main Pipeline --------
def main_pipeline():
    extracted_data = ocr_main()  # Your OCR module output
    for data in extracted_data:
        text = data['text']
        file_name = data['file_name']
        document_id = data['document_id']
        file_path = data['file_path']  # Make sure OCR returns original file path

        # Extract clauses
        clauses = extract_clauses(text)
        clauses_file = os.path.join(EXTRACTED_FOLDER, f"clauses_{document_id}.txt")
        save_clauses(clauses, clauses_file)
        print(f"Clauses saved: {clauses_file}")

        # Print classification for reference
        print(f"\nClassification for {file_name}:")
        for clause in clauses:
            label = classify_clause_hybrid(clause)
            print(f"Clause: {clause}")
            print(f"Issue Type: {label}")
            print("-"*50)

        # Highlight clauses in original document
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            output_file = f"highlighted_{file_name}"
            highlight_pdf(file_path, clauses, output_file)
        elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
            output_file = f"highlighted_{file_name}"
            highlight_image(file_path, clauses, output_file)
        else:
            print(f"Unsupported file type for highlighting: {file_name}")

if __name__ == "__main__":
    main_pipeline()

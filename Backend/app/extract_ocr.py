import os
import uuid
import pytesseract
import pdfplumber
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image
import docx

# -------------------------
# Setup paths
# -------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Update if needed

UPLOAD_FOLDER = "uploads"
EXTRACTED_FOLDER = "extracted_text"
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

# Poppler path (needed for pdf2image)
POPPLER_PATH = r"C:\Program Files\poppler-25.07.0\Library\bin"  # Update if installed elsewhere


# -------------------------
# Core Extraction Functions
# -------------------------
def extract_text_from_pdf_no_ocr(file_path):
    """Try extracting text from PDF using text layer"""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    if text.strip():
        return text

    # fallback using PyMuPDF if no text layer
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text


def extract_text_from_pdf_with_ocr(file_path):
    """Run OCR on PDF pages (image-based PDF)"""
    text = ""
    pages = convert_from_path(file_path, poppler_path=POPPLER_PATH)
    for page in pages:
        page_text = pytesseract.image_to_string(page)
        text += page_text + "\n"
    return text


def extract_text_from_image(file_path):
    """Run OCR on image files"""
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return text


def extract_text_from_docx(file_path):
    """Extract text from .docx file"""
    document = docx.Document(file_path)
    return "\n".join([p.text for p in document.paragraphs])


# -------------------------
# Save Extracted Text
# -------------------------
def save_to_file(filename, text, file_path=None):
    """Save extracted text to file and return metadata"""
    base_name = os.path.splitext(filename)[0]
    file_path_txt = os.path.join(EXTRACTED_FOLDER, base_name + ".txt")

    with open(file_path_txt, "w", encoding="utf-8") as f:
        f.write(text)

    document_id = base_name  # You can also use uuid if needed
    return {
        "document_id": document_id,
        "file_name": filename,
        "file_path": file_path or os.path.join(UPLOAD_FOLDER, filename),
        "text": text
    }


# -------------------------
# Wrappers for pipeline_runner.py
# -------------------------
def ocr_pdf(file_path):
    """Used by pipeline_runner to handle PDFs"""
    text = extract_text_from_pdf_no_ocr(file_path)
    if not text.strip():
        text = extract_text_from_pdf_with_ocr(file_path)
    return text


def ocr_image(file_path):
    """Used by pipeline_runner to handle images"""
    return extract_text_from_image(file_path)


def ocr_docx(file_path):
    """Used by pipeline_runner to handle docx"""
    return extract_text_from_docx(file_path)


# -------------------------
# Standalone Runner (for testing)
# -------------------------
def main():
    all_text_data = []

    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        text = ""

        if filename.lower().endswith(".pdf"):
            text = ocr_pdf(file_path)
            print(f"✅ PDF processed: {filename}")

        elif filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            text = ocr_image(file_path)
            print(f"🖼️ Image processed: {filename}")

        elif filename.lower().endswith(".docx"):
            text = ocr_docx(file_path)
            print(f"📄 DOCX processed: {filename}")

        else:
            print(f"⚠️ Unsupported file: {filename}")
            continue

        text_data = save_to_file(filename, text, file_path)
        all_text_data.append(text_data)
        print(f"💾 Saved extracted text for {filename}, Document ID: {text_data['document_id']}")

    print("\n📘 All extracted text data:")
    for data in all_text_data:
        print(f"- {data['file_name']} (ID: {data['document_id']})")

    return all_text_data


if __name__ == "__main__":
    main()

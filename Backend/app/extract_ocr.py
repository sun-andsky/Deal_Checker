import os
import uuid
import pytesseract
import pdfplumber
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image

# -------------------------
# Setup paths
# -------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # your Tesseract path

UPLOAD_FOLDER = "uploads"
EXTRACTED_FOLDER = "extracted_text"
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

# If Poppler is not in PATH, provide poppler_path
POPPLER_PATH = r"C:\Program Files\poppler-25.07.0\Library\bin"  # change to your poppler bin path

# -------------------------
# Functions
# -------------------------
def extract_text_from_pdf_no_ocr(file_path):
    """Try extracting text from PDF without OCR"""
    text = ""
    # pdfplumber
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    if text.strip():
        return text
    # fallback PyMuPDF
    doc = fitz.open(file_path)
    for page in doc:
        text += page.get_text()
    return text

def extract_text_from_pdf_with_ocr(file_path):
    """Run OCR on PDF by converting each page to image"""
    text = ""
    pages = convert_from_path(file_path, poppler_path=POPPLER_PATH)
    for page in pages:
        page_text = pytesseract.image_to_string(page)
        text += page_text + "\n"
    return text

def extract_text_from_image(file_path):
    """Run OCR on an image file"""
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    return text

def save_to_file(filename, text, file_path=None):
    """Save extracted text to a txt file and return metadata"""
    base_name = os.path.splitext(filename)[0]
    file_path_txt = os.path.join(EXTRACTED_FOLDER, base_name + ".txt")
    
    # Save the text to a file
    with open(file_path_txt, "w", encoding="utf-8") as f:
        f.write(text)
    
    # Generate a document ID (can use file name or UUID)
    document_id = base_name  # Option 1: use file name as ID
    # document_id = str(uuid.uuid4())  # Option 2: use unique UUID
    
    # Return dictionary to pass to DB or pipeline
    return {
        "document_id": document_id,
        "file_name": filename,
        "file_path": file_path or os.path.join(UPLOAD_FOLDER, filename),
        "text": text
    }

# -------------------------
# Main function
# -------------------------
def main():
    all_text_data = []

    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        text = ""

        if filename.lower().endswith(".pdf"):
            # Try text extraction without OCR first
            text = extract_text_from_pdf_no_ocr(file_path)
            if not text.strip():
                print(f"OCR needed for {filename}")
                text = extract_text_from_pdf_with_ocr(file_path)
            else:
                print(f"Text found without OCR for {filename}")

        elif filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff")):
            text = extract_text_from_image(file_path)
            print(f"OCR run for image {filename}")

        else:
            print(f"Skipped unsupported file: {filename}")
            continue

        # Save text and generate metadata
        text_data = save_to_file(filename, text, file_path)
        all_text_data.append(text_data)
        print(f"Saved extracted text for {filename}, document ID: {text_data['document_id']}")

    # Optional: print all extracted text data
    print("\nAll extracted text data:")
    for data in all_text_data:
        print(f"Document ID: {data['document_id']}, File: {data['file_name']}")

    return all_text_data

if __name__ == "__main__":
    main()

import uuid 
import os
import pytesseract
from paddleocr import PaddleOCR
import pdfplumber
import fitz  # PyMuPDF
from pdf2image import convert_from_path

# -------------------------
# Setup paths
# -------------------------
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract"  # your Tesseract path
ocr = PaddleOCR(use_angle_cls=True, lang='en')  # English

UPLOAD_FOLDER = "uploads"
EXTRACTED_FOLDER = "extracted_text"
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

# If Poppler is not in PATH, provide poppler_path
POPPLER_PATH = r"C:\Users\shalinigm01\Downloads\Release-25.07.0-0\poppler-25.07.0\Library\bin"  # change to your poppler bin path

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
        page_text1 = pytesseract.image_to_string(page)
        result = ocr.ocr(page, cls=True)
        page_text2 = "\n".join([line[1][0] for line in sum(result, [])])
        text += page_text1 + "\n" + page_text2
    return text

def extract_text_from_image(file_path):
    text1 = pytesseract.image_to_string(file_path)
    result = ocr.ocr(file_path, cls=True)
    text2 = "\n".join([line[1][0] for line in sum(result, [])])
    return text1 + "\n" + text2

def save_to_file(filename, text):
    base_name = os.path.splitext(filename)[0]
    file_path = os.path.join(EXTRACTED_FOLDER, base_name + ".txt")
    
    # Save the text to a file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    # Generate a document ID (can use file name or UUID)
    document_id = base_name  # Option 1: use file name as ID
    # document_id = str(uuid.uuid4())  # Option 2: use unique UUID
    
    # Return dictionary to pass to DB team
    return {"document_id": document_id, "file_name": filename, "text": text}

# -------------------------
# Main
# -------------------------
def main():
    all_text_data = []  # list to store all extracted text info

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

        elif filename.lower().endswith((".png", ".jpg", ".jpeg")):
            # Always run OCR on images
            text = extract_text_from_image(file_path)
            print(f"OCR run for image {filename}")

        else:
            print(f"Skipped unsupported file: {filename}")
            continue

        # Save text and generate document ID
        text_data = save_to_file(filename, text)
        all_text_data.append(text_data)  # collect for database insertion
        print(f"Saved extracted text for {filename}, document ID: {text_data['document_id']}")

    # Optional: print all extracted text data for verification
    print("\nAll extracted text data:")
    for data in all_text_data:
        print(f"Document ID: {data['document_id']}, File: {data['file_name']}")

if __name__ == "__main__":
    main()



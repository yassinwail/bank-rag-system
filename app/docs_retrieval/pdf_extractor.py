import fitz  # pymupdf
import pytesseract
from PIL import Image
import io

# Update this path to match your Tesseract install location
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extracts text per page. Falls back to OCR for pages with little/no
    extractable text (likely scanned images).
    Returns a list of {"page": int, "text": str} dicts.
    """
    doc = fitz.open(pdf_path)
    pages = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()

        if len(text) < 20:  # likely a scanned page with no real text layer
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(image).strip()

        pages.append({"page": page_num, "text": text})

    doc.close()
    return pages
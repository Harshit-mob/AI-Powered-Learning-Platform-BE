import fitz
import logging
from typing import List, Optional, Protocol, Tuple
from pydantic import BaseModel
from pathlib import Path

# Configure basic logging for the service
logger = logging.getLogger(__name__)

class ExtractedPage(BaseModel):
    page_number: int
    text: str
    confidence: float
    images_count: int

class OCRServiceInterface(Protocol):
    """
    Dependency Injection interface for the OCR Service.
    This ensures PDFExtractor is never tightly coupled to a specific OCR implementation (like PaddleOCR).
    """
    def process_image(self, image_bytes: bytes) -> Tuple[str, float]:
        """Returns extracted text and confidence score (0.0 to 1.0)."""
        pass

class PDFExtractor:
    """
    Service responsible for extracting text from PDFs.
    Attempts embedded text extraction first. If the result is below the acceptable threshold,
    it automatically renders the page and delegates to the injected OCR service.
    """
    
    def __init__(self, ocr_service: Optional[OCRServiceInterface] = None, text_length_threshold: int = 50):
        self.ocr_service = ocr_service
        self.text_length_threshold = text_length_threshold

    def extract(self, file_path: str) -> List[ExtractedPage]:
        """
        Extracts content from all pages. Never stops the pipeline on a single page failure.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
            
        extracted_pages: List[ExtractedPage] = []
        
        try:
            doc = fitz.open(str(path))
        except Exception as e:
            logger.error(f"Failed to open PDF for extraction: {str(e)}")
            raise RuntimeError(f"Failed to open PDF: {str(e)}")

        # Dynamic language detection
        detected_lang = 'en'
        if 'hindi' in str(path).lower() or 'hi' in str(path).lower().split('/'):
            detected_lang = 'hi'
        else:
            # Check native text of first few pages (up to 5 pages)
            sample_text = ""
            for page_num in range(min(5, len(doc))):
                try:
                    p = doc.load_page(page_num)
                    sample_text += p.get_text("text")
                except Exception:
                    pass
            # Count Devanagari Unicode characters (range: U+0900 to U+097F)
            devanagari_count = sum(1 for char in sample_text if 0x0900 <= ord(char) <= 0x097F)
            if devanagari_count > 10:
                detected_lang = 'hi'
                logger.info(f"Detected Devanagari script. Setting OCR language to 'hi'.")

        if detected_lang != 'en' and self.ocr_service and hasattr(self.ocr_service, 'set_language'):
            self.ocr_service.set_language(detected_lang)

        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                text = page.get_text("text").strip()
                images_count = len(page.get_images(full=True))
                
                # Try OCR fallback if text is missing or below the acceptable threshold
                if len(text) < self.text_length_threshold:
                    if self.ocr_service:
                        logger.info(f"Page {page_num + 1} text below threshold, falling back to OCR.")
                        # Render page as lower-res image for faster OCR processing
                        pix = page.get_pixmap(dpi=150) 
                        image_bytes = pix.tobytes("png")
                        
                        ocr_text, confidence = self.ocr_service.process_image(image_bytes)
                        text = ocr_text.strip()
                    else:
                        logger.warning(f"Page {page_num + 1} needs OCR but no OCR service was provided.")
                        confidence = 0.0
                else:
                    # Native text extraction is considered highly confident
                    confidence = 1.0

                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num + 1,
                        text=text,
                        confidence=confidence,
                        images_count=images_count
                    )
                )
                
            except Exception as e:
                # Rule: Log the error, continue processing. Never stop the pipeline.
                logger.error(f"Error processing page {page_num + 1} in {path.name}: {str(e)}")
                extracted_pages.append(
                    ExtractedPage(
                        page_number=page_num + 1,
                        text="",
                        confidence=0.0,
                        images_count=0
                    )
                )

        doc.close()
        return extracted_pages

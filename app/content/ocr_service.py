import logging
import io
from typing import Tuple
import numpy as np
from PIL import Image

# Graceful fallback in case PaddleOCR isn't installed in the environment yet
try:
    from paddleocr import PaddleOCR
    PADDLE_AVAILABLE = True
except ImportError:
    PADDLE_AVAILABLE = False

logger = logging.getLogger(__name__)

class OCRService:
    """
    Independent service for Optical Character Recognition.
    Currently uses PaddleOCR as the engine.
    Designed to be highly reusable for future Image Import Pipelines.
    """
    
    def __init__(self, lang: str = 'en'):
        self.lang = lang
        self._engine = None
        
        if PADDLE_AVAILABLE:
            # Initialize OCR engine (lazy-loaded on startup)
            # use_textline_orientation=True helps with scanned images that might be slightly rotated
            self._engine = PaddleOCR(use_textline_orientation=True, lang=self.lang)
        else:
            logger.warning("PaddleOCR is not installed. OCR fallback will return empty text.")

    def process_image(self, image_bytes: bytes) -> Tuple[str, float]:
        """
        Takes raw image bytes, runs OCR, and returns the extracted text and average confidence.
        
        Args:
            image_bytes (bytes): The raw image data (e.g., from a PDF page or uploaded image).
            
        Returns:
            Tuple[str, float]: Extracted text and the confidence score (0.0 to 1.0).
        """
        if not self._engine:
            logger.error("OCR engine is not initialized. Cannot process image.")
            return "", 0.0

        try:
            # Convert bytes to PIL Image, then to numpy array for PaddleOCR
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img_array = np.array(image)
            
            # Run PaddleOCR
            result = self._engine.ocr(img_array)
            
            if not result or len(result) == 0:
                return "", 0.0
                
            extracted_lines = []
            total_confidence = 0.0
            count = 0
            
            # PaddleOCR >= 3.7 returns a dictionary. Older versions return lists.
            if isinstance(result[0], dict):
                res_dict = result[0]
                texts = res_dict.get('rec_texts', [])
                scores = res_dict.get('rec_scores', [])
                
                if not texts:
                    return "", 0.0
                    
                extracted_lines = texts
                count = len(scores)
                total_confidence = sum(scores)
                
            else:
                # Fallback for PaddleOCR < 3.7 (Result format: [[bounding_box], [text, confidence]])
                for line in result[0]:
                    if len(line) == 2 and isinstance(line[1], tuple):
                        text, confidence = line[1]
                        extracted_lines.append(text)
                        total_confidence += confidence
                        count += 1
                        
            if count == 0:
                return "", 0.0
                
            final_text = "\n".join(extracted_lines)
            avg_confidence = total_confidence / count
            
            return final_text, float(avg_confidence)
            
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            return "", 0.0

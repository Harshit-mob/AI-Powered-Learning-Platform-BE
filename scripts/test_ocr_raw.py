import numpy as np
from paddleocr import PaddleOCR
import cv2

engine = PaddleOCR(use_angle_cls=True, lang='en')
# Create a dummy image with some text
img = np.zeros((100, 400, 3), dtype=np.uint8)
cv2.putText(img, 'Hello World', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

print("Running OCR...")
res = engine.ocr(img)
print("Result:")
print(res)

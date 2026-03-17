import pytesseract
from PIL import Image
import sys

# Replace this with the actual path to tesseract if it's not in your PATH
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

images = [
    r"C:\Users\hp\.gemini\antigravity\brain\24b6da2d-cf72-4325-a8ad-4ff50931ea43\media__1773123795905.png",
    r"C:\Users\hp\.gemini\antigravity\brain\24b6da2d-cf72-4325-a8ad-4ff50931ea43\media__1773123795940.png",
    r"C:\Users\hp\.gemini\antigravity\brain\24b6da2d-cf72-4325-a8ad-4ff50931ea43\media__1773123795974.png"
]

for img_path in images:
    print(f"\n--- Analyzing {img_path} ---")
    try:
        text = pytesseract.image_to_string(Image.open(img_path))
        print("Scanned Text:")
        print(text[:1000]) # Print first 1000 characters
    except Exception as e:
        print("Error:", e)

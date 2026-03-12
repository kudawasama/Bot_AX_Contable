import pytesseract
try:
    print(pytesseract.get_tesseract_version())
    print("SUCCESS: Tesseract engine found!")
except Exception as e:
    print(f"FAILED: Tesseract engine not found. Error: {e}")

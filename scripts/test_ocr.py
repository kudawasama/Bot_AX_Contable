import pytesseract

def main() -> None:
    """Verifica si el motor Tesseract está accesible y muestra su versión instalada."""
    try:
        version: str = pytesseract.get_tesseract_version()
        print(f"SUCCESS: Tesseract engine found! Version: {version}")
    except Exception as e:
        print(f"FAILED: Tesseract engine not found. Error: {e}")

if __name__ == "__main__":
    main()

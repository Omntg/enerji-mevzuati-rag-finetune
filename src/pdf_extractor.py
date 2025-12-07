import fitz  # type: ignore
import os

class PDFExtractor:
    def __init__(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)

    def extract_text(self) -> str:
        """Extracts full text from the PDF."""
        try:
            doc = fitz.open(self.file_path)
            text = []
            for page in doc:
                text.append(page.get_text())
            return "\n".join(text)
        except Exception as e:
            raise RuntimeError(f"Error reading PDF {self.file_path}: {e}")

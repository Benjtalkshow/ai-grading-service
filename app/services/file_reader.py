import os
from PyPDF2 import PdfReader
from docx import Document

class FileExtractor:
    """Extracts text from various file types"""
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return FileExtractor._read_pdf(file_path)
        elif ext in [".doc", ".docx"]:
            return FileExtractor._read_docx(file_path)
        elif ext in [".txt", ".md"]:
            return FileExtractor._read_text(file_path)
        return ""

    @staticmethod
    def _read_pdf(path: str) -> str:
        try:
            reader = PdfReader(path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text[:10000] # Limit
        except:
            return ""

    @staticmethod
    def _read_docx(path: str) -> str:
        try:
            doc = Document(path)
            return "\n".join([p.text for p in doc.paragraphs])[:10000]
        except:
            return ""

    @staticmethod
    def _read_text(path: str) -> str:
        try:
            with open(path, 'r', errors='ignore') as f:
                return f.read()[:10000]
        except:
            return ""

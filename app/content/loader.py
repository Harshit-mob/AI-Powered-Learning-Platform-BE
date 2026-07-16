import fitz  # PyMuPDF
from typing import Dict, Any, List
from pydantic import BaseModel
from pathlib import Path

class ContentMetadata(BaseModel):
    file_name: str
    total_pages: int
    source_metadata: Dict[str, Any]
    file_path: str
    file_type: str
    board: str = ""
    grade: str = ""
    subject: str = ""
    chapter_number: int = 0
    chapter_title: str = ""

class ContentLoader:
    """
    Service responsible for loading a content package and extracting high-level metadata.
    Does NOT perform text extraction or OCR.
    """
    
    def __init__(self, supported_extensions: List[str] = None):
        self.supported_extensions = supported_extensions or [".pdf"]

    def load(self, file_path: str) -> ContentMetadata:
        """
        Loads the content file and returns structural metadata.
        
        Args:
            file_path (str): The absolute or relative path to the content file.
            
        Returns:
            ContentMetadata: Extracted metadata including total pages.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is unsupported.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Content file not found at: {file_path}")
            
        ext = path.suffix.lower()
        if ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file format '{ext}'. Supported formats: {self.supported_extensions}")

        # Currently supporting PDF for the MVP
        if ext == ".pdf":
            return self._load_pdf(path)
            
        # Future implementations for EPUB, DOCX, etc., will be added here
        raise NotImplementedError(f"Loader for {ext} is not yet implemented.")

    def _load_pdf(self, path: Path) -> ContentMetadata:
        """Internal method to load PDF metadata using PyMuPDF and metadata.json."""
        import json
        
        board = ""
        grade = ""
        subject = ""
        chapter_number = 0
        chapter_title = ""
        
        # Try to read metadata.json
        meta_path = path.parent / "metadata.json"
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    board = data.get("board", "")
                    grade = str(data.get("grade", ""))
                    subject = data.get("subject", "")
                    chapter_number = data.get("chapter_number", 0)
                    chapter_title = data.get("chapter_title", "")
            except Exception:
                pass # Non-critical failure

        try:
            doc = fitz.open(str(path))
            total_pages = len(doc)
            # fitz doc.metadata contains author, title, creationDate, etc.
            source_metadata = doc.metadata or {}
            
            return ContentMetadata(
                file_name=path.name,
                total_pages=total_pages,
                source_metadata=source_metadata,
                file_path=str(path),
                file_type="pdf",
                board=board,
                grade=grade,
                subject=subject,
                chapter_number=chapter_number,
                chapter_title=chapter_title
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load PDF file: {str(e)}")
        finally:
            if 'doc' in locals():
                doc.close()

# Instantiate the service to be injected/used elsewhere
content_loader = ContentLoader()

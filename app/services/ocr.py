"""OCR service for document text extraction."""
import os
from typing import Optional, Dict, Any
from pathlib import Path
try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import boto3
    TEXTRACT_AVAILABLE = True
except ImportError:
    TEXTRACT_AVAILABLE = False

from app.core.config import settings


class OCRService:
    """Service for OCR operations."""

    def __init__(self):
        """Initialize OCR service."""
        self.use_textract = (
            TEXTRACT_AVAILABLE and
            settings.AWS_ACCESS_KEY_ID and
            settings.AWS_SECRET_ACCESS_KEY
        )
        if self.use_textract:
            self.textract_client = boto3.client(
                'textract',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )

    def extract_text_tesseract(self, file_path: str) -> str:
        """
        Extract text using Tesseract OCR.

        Args:
            file_path: Path to image or PDF file

        Returns:
            Extracted text
        """
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract not available. Install pytesseract and tesseract-ocr.")

        file_ext = Path(file_path).suffix.lower()

        if file_ext == '.pdf':
            # Convert PDF to images
            images = convert_from_path(file_path)
            texts = []
            for image in images:
                text = pytesseract.image_to_string(image)
                texts.append(text)
            return "\n\n".join(texts)
        else:
            # Assume image file
            image = Image.open(file_path)
            return pytesseract.image_to_string(image)

    def extract_text_textract(self, file_path: str) -> str:
        """
        Extract text using AWS Textract.

        Args:
            file_path: Path to PDF or image file

        Returns:
            Extracted text
        """
        if not self.use_textract:
            raise RuntimeError("Textract not configured. Set AWS credentials.")

        with open(file_path, 'rb') as document:
            file_bytes = document.read()

        # Detect if PDF or image
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.pdf':
            response = self.textract_client.detect_document_text(
                Document={'Bytes': file_bytes}
            )
        else:
            response = self.textract_client.detect_document_text(
                Document={'Bytes': file_bytes}
            )

        # Extract text from blocks
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])

        return '\n'.join(text_blocks)

    def extract_text(self, file_path: str, use_textract: Optional[bool] = None) -> Dict[str, Any]:
        """
        Extract text from document.

        Args:
            file_path: Path to document file
            use_textract: Force use of Textract (if available), otherwise use Tesseract

        Returns:
            Dict with 'text', 'method', 'confidence' (if available)
        """
        if use_textract is None:
            use_textract = self.use_textract

        try:
            if use_textract:
                text = self.extract_text_textract(file_path)
                method = "textract"
            else:
                text = self.extract_text_tesseract(file_path)
                method = "tesseract"
        except Exception as e:
            # Fallback to Tesseract if Textract fails
            if use_textract and TESSERACT_AVAILABLE:
                text = self.extract_text_tesseract(file_path)
                method = "tesseract_fallback"
            else:
                raise

        return {
            "text": text,
            "method": method,
            "confidence": None  # TODO: Extract confidence scores if available
        }

    def analyze_document(self, file_path: str, expected_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze document for errors and inconsistencies.

        Args:
            file_path: Path to document
            expected_data: Optional dict with expected values (e.g., {"name": "John Doe", "date": "2020-01-01"})

        Returns:
            Dict with 'errors' list containing (field, found_value, expected_value, confidence)
        """
        # Extract text
        ocr_result = self.extract_text(file_path)
        text = ocr_result["text"]

        errors = []

        if expected_data:
            # TODO: Implement document comparison logic
            # This would use NLP/LLM to extract structured data and compare
            # For now, return placeholder
            pass

        return {
            "text": text,
            "errors": errors,
            "warnings": [],
            "extracted_data": {}  # TODO: Extract structured data (dates, names, codes, etc.)
        }


# Global instance
ocr_service = OCRService()


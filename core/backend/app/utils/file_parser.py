"""
NeuroSync — File Parsing Utility (Phase 2.3).
Extracts raw text from PDF, DOCX, and TXT files with magic-byte validation.
"""
from __future__ import annotations

import io
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Magic byte signatures
MAGIC_BYTES = {
    "pdf": b"%PDF-",
    "docx": b"PK\x03\x04",
}


class FileParsingError(ValueError):
    """Raised when a file cannot be parsed or fails security validation."""
    pass


def validate_magic_bytes(content: bytes, filename: str) -> str:
    """
    Validate file content against filename extension.
    Returns format: 'pdf', 'docx', or 'txt'.
    """
    fn = filename.lower()
    if fn.endswith(".pdf"):
        if not content.startswith(MAGIC_BYTES["pdf"]):
            raise FileParsingError("Invalid PDF header: magic bytes check failed")
        return "pdf"
    elif fn.endswith(".docx"):
        if not content.startswith(MAGIC_BYTES["docx"]):
            raise FileParsingError("Invalid DOCX header: magic bytes check failed")
        return "docx"
    elif fn.endswith(".txt"):
        return "txt"
    else:
        # Fallback inspection by magic bytes
        if content.startswith(MAGIC_BYTES["pdf"]):
            return "pdf"
        elif content.startswith(MAGIC_BYTES["docx"]):
            return "docx"
        else:
            # Try text decoding
            try:
                content.decode("utf-8")
                return "txt"
            except UnicodeDecodeError:
                raise FileParsingError("Unsupported file type or corrupted format")


def parse_pdf(content: bytes) -> str:
    """Extract plain text from PDF bytes using pypdf."""
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(content))
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        extracted = "\n\n".join(text_parts).strip()
        if not extracted:
            raise FileParsingError("PDF contained no readable text (scanned image or empty)")
        return extracted
    except Exception as e:
        if isinstance(e, FileParsingError):
            raise e
        logger.error("Failed to parse PDF: %s", e, exc_info=True)
        raise FileParsingError(f"PDF extraction error: {str(e)}")


def parse_docx(content: bytes) -> str:
    """Extract plain text from DOCX bytes using python-docx."""
    try:
        import docx
        doc = docx.Document(io.BytesIO(content))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        extracted = "\n".join(paragraphs).strip()
        if not extracted:
            raise FileParsingError("DOCX document contained no text")
        return extracted
    except Exception as e:
        if isinstance(e, FileParsingError):
            raise e
        logger.error("Failed to parse DOCX: %s", e, exc_info=True)
        raise FileParsingError(f"DOCX extraction error: {str(e)}")


def parse_txt(content: bytes) -> str:
    """Extract plain text from UTF-8 / ASCII bytes."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return content.decode(encoding).strip()
        except UnicodeDecodeError:
            continue
    raise FileParsingError("Failed to decode text file with standard encodings")


def parse_file(content: bytes, filename: str) -> Tuple[str, str]:
    """
    Parse a file payload into plain text.

    Args:
        content: raw file bytes
        filename: original filename

    Returns:
        Tuple of (extracted_text, file_format)
    """
    if not content:
        raise FileParsingError("Empty file uploaded")

    if len(content) > 10 * 1024 * 1024:  # 10 MB limit
        raise FileParsingError("File size exceeds maximum allowed limit (10MB)")

    fmt = validate_magic_bytes(content, filename)

    if fmt == "pdf":
        text = parse_pdf(content)
    elif fmt == "docx":
        text = parse_docx(content)
    elif fmt == "txt":
        text = parse_txt(content)
    else:
        raise FileParsingError(f"Unsupported format '{fmt}'")

    return text, fmt

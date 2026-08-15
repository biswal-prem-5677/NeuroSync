"""
NeuroSync — Tests for File Parser (app/utils/file_parser.py).
"""
import pytest
from app.utils.file_parser import parse_file, FileParsingError, validate_magic_bytes


def test_parse_txt_file():
    text_content = "Python developer with FastAPI experience." * 5
    parsed, fmt = parse_file(text_content.encode("utf-8"), "resume.txt")
    assert fmt == "txt"
    assert "FastAPI" in parsed


def test_magic_bytes_validation_pdf_invalid():
    fake_pdf = b"NOT A PDF HEADER"
    with pytest.raises(FileParsingError, match="magic bytes check failed"):
        validate_magic_bytes(fake_pdf, "resume.pdf")


def test_magic_bytes_validation_docx_invalid():
    fake_docx = b"NOT A DOCX HEADER"
    with pytest.raises(FileParsingError, match="magic bytes check failed"):
        validate_magic_bytes(fake_docx, "resume.docx")


def test_empty_file():
    with pytest.raises(FileParsingError, match="Empty file uploaded"):
        parse_file(b"", "resume.txt")

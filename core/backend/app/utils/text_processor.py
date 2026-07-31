"""
NeuroSync — Text Processor.
Production-grade text cleaning with smart tech-term preservation.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Optional

# Regex patterns compiled once at module level
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
_MULTI_NEWLINE_RE = re.compile(r"\n{4,}")
_NULL_CTRL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_URL_RE = re.compile(r"https?://\S+")
_EMAIL_RE = re.compile(r"\S+@\S+\.\S+")

# Tech terms that must survive normalization (lowercase key → preserved form)
_TECH_PRESERVATIONS = {
    "c++": "C++",
    "c#": "C#",
    ".net": ".NET",
    "node.js": "Node.js",
    "react.js": "React.js",
    "vue.js": "Vue.js",
    "next.js": "Next.js",
    "nuxt.js": "Nuxt.js",
    "three.js": "Three.js",
    "d3.js": "D3.js",
    "express.js": "Express.js",
    "nest.js": "NestJS",
    "asp.net": "ASP.NET",
    "f#": "F#",
    "objective-c": "Objective-C",
}

# Section header patterns for resume parsing
_SECTION_PATTERNS = [
    re.compile(r"^\s*(experience|work\s+experience|professional\s+experience)\s*:?\s*$", re.I),
    re.compile(r"^\s*(education|academic|qualifications)\s*:?\s*$", re.I),
    re.compile(r"^\s*(skills|technical\s+skills|core\s+competencies)\s*:?\s*$", re.I),
    re.compile(r"^\s*(projects|personal\s+projects|key\s+projects)\s*:?\s*$", re.I),
    re.compile(r"^\s*(certifications?|licenses?)\s*:?\s*$", re.I),
    re.compile(r"^\s*(summary|objective|profile|about)\s*:?\s*$", re.I),
    re.compile(r"^\s*(publications?|research)\s*:?\s*$", re.I),
    re.compile(r"^\s*(awards?|honors?|achievements?)\s*:?\s*$", re.I),
]


def clean_text(text: str) -> str:
    """
    Full sanitization pipeline:
    1. Strip null bytes / control chars
    2. Unicode NFC normalization
    3. Strip HTML tags
    4. Remove URLs (keep domain-like text)
    5. Collapse excessive whitespace
    """
    if not text:
        return ""

    # Step 1: Remove null bytes and control characters
    text = _NULL_CTRL_RE.sub("", text)

    # Step 2: Unicode NFC normalization
    text = unicodedata.normalize("NFC", text)

    # Step 3: Strip HTML tags
    text = _HTML_TAG_RE.sub(" ", text)

    # Step 4: Remove URLs
    text = _URL_RE.sub("", text)

    # Step 5: Collapse whitespace
    text = _MULTI_SPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n\n", text)

    return text.strip()


def normalize_for_matching(text: str) -> str:
    """
    Lowercase + strip punctuation EXCEPT tech-relevant chars (+, #, .).
    Preserves: C++, C#, .NET, Node.js
    """
    if not text:
        return ""

    text = text.lower().strip()

    # Remove punctuation except + # . -
    text = re.sub(r"[^\w\s+#.\-]", " ", text)

    # Collapse spaces
    text = _MULTI_SPACE_RE.sub(" ", text)

    return text.strip()


def preserve_tech_term(text: str) -> Optional[str]:
    """If text is a known tech term that needs special handling, return preserved form."""
    return _TECH_PRESERVATIONS.get(text.lower().strip())


def extract_sections(text: str) -> dict[str, str]:
    """
    Heuristic section detection from resume text.
    Returns dict mapping section name → section content.
    """
    lines = text.split("\n")
    sections: dict[str, str] = {}
    current_section = "header"
    current_lines: list[str] = []

    for line in lines:
        matched_section = None
        for pattern in _SECTION_PATTERNS:
            if pattern.match(line.strip()):
                matched_section = pattern.match(line.strip()).group(1).strip().lower()
                break

        if matched_section:
            # Save previous section
            if current_lines:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = matched_section
            current_lines = []
        else:
            current_lines.append(line)

    # Save last section
    if current_lines:
        sections[current_section] = "\n".join(current_lines).strip()

    return sections


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """
    Split text into semantic chunks for embedding.
    Tries to break on sentence boundaries.
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    # Split on sentences first
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current_chunk: list[str] = []
    current_length = 0

    for sentence in sentences:
        sentence_len = len(sentence)

        if current_length + sentence_len > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # Keep last N chars worth of sentences for overlap
            overlap_text = " ".join(current_chunk)
            if len(overlap_text) > overlap:
                # Find sentence boundary near overlap point
                overlap_start = overlap_text[-(overlap):]
                current_chunk = [overlap_start]
                current_length = len(overlap_start)
            else:
                current_chunk = []
                current_length = 0

        current_chunk.append(sentence)
        current_length += sentence_len

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


@lru_cache(maxsize=256)
def compute_alpha_ratio(text: str) -> float:
    """Fraction of alphabetic characters in text. Used for junk detection."""
    if not text:
        return 0.0
    return sum(c.isalpha() for c in text) / len(text)

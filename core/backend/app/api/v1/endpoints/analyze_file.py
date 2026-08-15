"""
NeuroSync — /analyze-file endpoint (Phase 2.3).
Upload resume and/or JD documents (PDF, DOCX, TXT) for analysis.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.api.deps import get_intelligence_engine
from app.utils.file_parser import FileParsingError, parse_file

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze-file", summary="File upload resume-to-JD analysis")
async def analyze_file(
    request: Request,
    resume_file: UploadFile = File(..., description="Resume document (PDF, DOCX, or TXT)"),
    jd_file: Optional[UploadFile] = File(None, description="Optional JD document (PDF, DOCX, or TXT)"),
    jd_text: Optional[str] = Form(None, description="Optional plain text JD if file not provided"),
    include_simulations: bool = Form(True),
    include_evidence: bool = Form(True),
):
    """
    File-upload analysis pipeline (PDF/DOCX/TXT).
    Parses documents and delegates to IntelligenceEngine (doc 12 Rule 1).
    """
    rid = getattr(request.state, "request_id", "?")
    logger.info("[%s] POST /analyze-file received (resume=%s)", rid, resume_file.filename)

    # 1. Parse resume file
    try:
        resume_bytes = await resume_file.read()
        parsed_resume_text, resume_fmt = parse_file(resume_bytes, resume_file.filename or "resume.txt")
    except FileParsingError as e:
        logger.warning("[%s] Resume parse error: %s", rid, e)
        raise HTTPException(status_code=400, detail=f"Resume file error: {str(e)}")

    # 2. Get JD text (from file or form field)
    final_jd_text = ""
    if jd_file and jd_file.filename:
        try:
            jd_bytes = await jd_file.read()
            final_jd_text, _ = parse_file(jd_bytes, jd_file.filename)
        except FileParsingError as e:
            logger.warning("[%s] JD parse error: %s", rid, e)
            raise HTTPException(status_code=400, detail=f"JD file error: {str(e)}")
    elif jd_text:
        final_jd_text = jd_text.strip()

    if not final_jd_text:
        raise HTTPException(
            status_code=400,
            detail="Job description required. Provide either 'jd_file' upload or 'jd_text' form field.",
        )

    # 3. Delegate to IntelligenceEngine
    intelligence = get_intelligence_engine()
    if not intelligence:
        raise HTTPException(status_code=503, detail="Intelligence Engine unavailable")

    try:
        response = await intelligence.analyze(
            resume_text=parsed_resume_text,
            jd_text=final_jd_text,
            include_simulations=include_simulations,
            include_evidence=include_evidence,
        )

        # Add file metadata
        response["meta"]["resume_filename"] = resume_file.filename
        response["meta"]["resume_format"] = resume_fmt

        return response
    except Exception as e:
        logger.error("[%s] File analysis failed: %s", rid, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

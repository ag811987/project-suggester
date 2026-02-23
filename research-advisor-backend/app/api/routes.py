"""API routes for the Research Pivot Advisor System."""

import io
import json
import uuid
import logging
import time
import os

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.debug_log import debug_log
from app.models.schemas import (
    AnalyzeResponse,
    ChatMessage,
    GapMapEntry,
    ResearchProfile,
    ResearchRecommendation,
)
from app.services.document_parser import DocumentParser
from app.services.info_collector import InfoCollectionService
from app.services.novelty_analyzer import NoveltyAnalyzer
from app.services.embedding_service import EmbeddingService
from app.services.gap_map_repository import GapMapRepository
from app.services.gap_retriever import GapRetriever
from app.services.pivot_matcher import PivotMatcher
from app.services.report_generator import ReportGenerator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: Request,
    messages: str = Form(...),
    files: list[UploadFile] = File(default=[]),
):
    """Analyze research question for novelty and generate recommendations.

    Accepts chat messages (as JSON string) and optional file uploads.
    Returns a session_id and the completed recommendation.
    """
    settings = get_settings()
    debug_log(
        location="app/api/routes.py:analyze:start",
        message="Analyze request start (non-sensitive snapshot)",
        data={
            "has_openai_api_key_env": bool(os.getenv("OPENAI_API_KEY")),
            "has_openai_api_key_settings": bool(getattr(settings, "openai_api_key", None)),
            "redis_url": settings.redis_url,
            "database_url_prefix": settings.database_url.split("@", 1)[0].split("://", 1)[0]
            if getattr(settings, "database_url", None)
            else None,
            "files_count": len(files),
        },
        run_id="pre-fix",
        hypothesis_id="H0_ANALYZE_ENTRY",
    )

    # Parse messages JSON
    try:
        messages_data = json.loads(messages)
        chat_messages = [ChatMessage(**m) for m in messages_data]
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid messages format: {e}")

    if not chat_messages:
        raise HTTPException(status_code=422, detail="At least one message is required")

    # Validate uploaded files
    allowed_extensions = {f".{ft}" for ft in settings.allowed_file_types}
    for f in files:
        ext = _get_file_extension(f.filename or "")
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {ext}. Allowed: {settings.allowed_file_types}",
            )

    # 1. Extract research profile from chat messages
    info_service = InfoCollectionService(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
    )

    profiles = [await info_service.extract_from_chat(chat_messages)]

    # 2. Parse uploaded files and extract profiles
    parser = DocumentParser()
    for f in files:
        content = await f.read()
        text = parser.parse_file(io.BytesIO(content), f.filename or "unknown")
        if text.strip():
            profile = await info_service.extract_from_text(text, f.filename)
            profiles.append(profile)

    merged_profile = info_service.merge_profiles(profiles)

    # 3. Assess novelty
    novelty_analyzer = NoveltyAnalyzer(
        openalex_email=settings.openalex_email,
        openai_api_key=settings.openai_api_key,
        openalex_api_key=settings.openalex_api_key,
        openai_model=settings.openai_model,
        use_semantic_search=settings.openalex_use_semantic_search,
        semantic_budget_threshold=settings.openalex_semantic_budget_threshold,
        multi_query=settings.openalex_multi_query,
        queries_per_variant=settings.openalex_queries_per_variant,
        use_embedding_rerank=settings.openalex_use_embedding_rerank,
        fwci_high_threshold=settings.fwci_high_threshold,
        fwci_low_threshold=settings.fwci_low_threshold,
        search_limit=settings.openalex_search_limit,
    )
    novelty = await novelty_analyzer.analyze(
        merged_profile.research_question, profile=merged_profile
    )
    # Privacy: No user data logged
    try:
        with open(
            "/Users/amit/Coding-Projects/Project-Suggester/.cursor/debug.log",
            "a",
            encoding="utf-8",
        ) as f:
            f.write(
                json.dumps(
                    {
                        "id": f"log_{time.time_ns()}",
                        "timestamp": int(time.time() * 1000),
                        "location": "app/api/routes.py:analyze:novelty_result",
                        "message": "NoveltyAnalyzer result summary",
                        "data": {
                            "related_papers_count": novelty.related_papers_count,
                            "verdict": novelty.verdict,
                            "impact_assessment": novelty.impact_assessment,
                        },
                        "runId": "post-fix",
                        "hypothesisId": "H_OA_RESULT_MISMATCH",
                    }
                )
                + "\n"
            )
    except Exception:
        pass

    # 4. Get gap map entries via vector retrieval (or fallback to get_all)
    gap_entries: list[GapMapEntry] = []
    try:
        async with request.app.state.db_session_factory() as session:
            repo = GapMapRepository(session)
            retriever = GapRetriever(
                repository=repo,
                embedding_service=EmbeddingService(api_key=settings.openai_api_key),
            )
            gap_entries = await retriever.retrieve(
                merged_profile, novelty, limit=settings.gap_retrieval_top_k
            )
    except Exception as e:
        logger.warning("Failed to fetch gap map entries: %s", e)
        debug_log(
            location="app/api/routes.py:analyze:gap_retrieval_error",
            message="Gap retrieval failed (exception only)",
            data={"exc_type": type(e).__name__},
            run_id="pre-fix",
            hypothesis_id="H3_DB_OR_VECTOR_RETRIEVAL",
        )

    # 5. Match pivots
    pivot_matcher = PivotMatcher()
    suggestions = await pivot_matcher.match_pivots(
        merged_profile, novelty, gap_entries
    )

    # 6. Generate report
    report_generator = ReportGenerator()
    recommendation = await report_generator.generate_report(
        merged_profile, novelty, suggestions
    )

    # 7. Store in Redis with session_id
    session_id = str(uuid.uuid4())
    redis = request.app.state.redis
    session_data = {
        "status": "completed",
        "recommendation": recommendation.model_dump_json(),
        "profile": merged_profile.model_dump_json(),
    }
    try:
        await redis.set(
            f"session:{session_id}",
            json.dumps(session_data),
            ex=settings.session_ttl_seconds,
        )
    except Exception as e:
        # Privacy: No user data logged
        debug_log(
            location="app/api/routes.py:analyze:redis_set_error",
            message="Redis session write failed (exception only)",
            data={"exc_type": type(e).__name__, "redis_url": settings.redis_url},
            run_id="pre-fix",
            hypothesis_id="H1_REDIS_UNAVAILABLE",
        )
        raise

    return AnalyzeResponse(session_id=session_id, status="completed")


@router.get("/analysis/{session_id}")
async def get_analysis(request: Request, session_id: str):
    """Retrieve analysis results by session ID."""
    redis = request.app.state.redis
    raw = await redis.get(f"session:{session_id}")

    if raw is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = json.loads(raw)
    recommendation = ResearchRecommendation.model_validate_json(
        session_data["recommendation"]
    )
    return recommendation


@router.post("/chat")
async def chat(request: Request):
    """Handle follow-up chat messages within an existing session."""
    body = await request.json()
    session_id = body.get("session_id")
    message = body.get("message")

    if not session_id or not message:
        raise HTTPException(
            status_code=422, detail="session_id and message are required"
        )

    redis = request.app.state.redis
    raw = await redis.get(f"session:{session_id}")

    if raw is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = json.loads(raw)
    settings = get_settings()

    # Use InfoCollectionService for follow-up
    info_service = InfoCollectionService(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        temperature=settings.openai_temperature,
        max_tokens=settings.openai_max_tokens,
    )

    chat_messages = [
        ChatMessage(role="user", content=message),
    ]

    try:
        profile = await info_service.extract_from_chat(chat_messages)
        response_text = (
            f"Based on your follow-up, I understand your research focus is: "
            f"{profile.research_question}. "
            f"Key skills identified: {', '.join(profile.skills) if profile.skills else 'none specified'}."
        )
    except Exception as e:
        logger.warning("Chat follow-up extraction failed: %s", e)
        response_text = "I received your message but couldn't process it. Please try rephrasing."

    # Update session TTL
    await redis.expire(f"session:{session_id}", settings.session_ttl_seconds)

    return {"response": response_text, "session_id": session_id}


@router.delete("/session/{session_id}", status_code=204)
async def delete_session(request: Request, session_id: str):
    """Delete a session and all associated data."""
    redis = request.app.state.redis
    await redis.delete(f"session:{session_id}")
    return None


def _get_file_extension(filename: str) -> str:
    """Get the lowercase file extension including the dot."""
    dot_idx = filename.rfind(".")
    if dot_idx == -1:
        return ""
    return filename[dot_idx:].lower()

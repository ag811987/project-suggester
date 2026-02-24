"""API routes for the Research Pivot Advisor System."""

import asyncio
import io
import json
import uuid
import logging
import time

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse

from openai import AsyncOpenAI

from app.config import get_settings
from app.models.schemas import (
    AnalyzeResponse,
    ChatMessage,
    GapMapEntry,
    ResearchRecommendation,
    SessionStatusResponse,
)
from app.services.document_parser import DocumentParser
from app.services.info_collector import InfoCollectionService
from app.services.novelty_analyzer import NoveltyAnalyzer
from app.services.embedding_service import EmbeddingService
from app.services.gap_map_repository import GapMapRepository
from app.services.gap_retriever import GapRetriever
from app.services.pivot_matcher import PivotMatcher
from app.services.report_generator import ReportGenerator
from app.services.web_search_client import WebSearchClient

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _set_stage(redis, session_id: str, stage: str, ttl: int) -> None:
    """Update the session stage in Redis (metadata only, no user data)."""
    try:
        raw = await redis.get(f"session:{session_id}")
        data = json.loads(raw) if raw else {"status": "processing"}
        data["stage"] = stage
        await redis.set(f"session:{session_id}", json.dumps(data), ex=ttl)
    except Exception:
        pass


async def _run_pipeline(
    session_id: str,
    chat_messages: list[ChatMessage],
    file_contents: list[tuple[str, bytes]],
    redis,
    db_session_factory,
) -> None:
    """Execute the full analysis pipeline in the background.

    Stages are written to Redis so the frontend can poll for progress.
    """
    settings = get_settings()
    ttl = settings.session_ttl_seconds
    t0 = time.monotonic()

    try:
        # -- Stage 1: Extract profile --
        await _set_stage(redis, session_id, "extracting_profile", ttl)
        info_service = InfoCollectionService(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            max_tokens=settings.openai_max_tokens,
        )
        profiles = [await info_service.extract_from_chat(chat_messages)]

        parser = DocumentParser()
        for filename, content in file_contents:
            text = parser.parse_file(io.BytesIO(content), filename)
            if text.strip():
                profile = await info_service.extract_from_text(text, filename)
                profiles.append(profile)

        merged_profile = info_service.merge_profiles(profiles)

        # -- Stage 2: Novelty analysis (OpenAlex + LLM) --
        await _set_stage(redis, session_id, "analyzing_novelty", ttl)
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

        # -- Stage 3: Supplemental web search (when signal is ambiguous) --
        await _set_stage(redis, session_id, "web_search", ttl)
        web_search_result = None
        if novelty.verdict == "UNCERTAIN" or novelty.impact_assessment == "UNCERTAIN":
            try:
                ws = WebSearchClient(
                    openai_client=AsyncOpenAI(api_key=settings.openai_api_key),
                    redis=redis,
                )
                web_search_result = await ws.search(
                    merged_profile.research_question,
                    context=merged_profile.problem_description or "",
                )
            except Exception:
                logger.warning("Web search failed; continuing without it")

        # -- Stage 4: Gap map retrieval --
        await _set_stage(redis, session_id, "retrieving_gaps", ttl)
        gap_entries: list[GapMapEntry] = []
        try:
            async with db_session_factory() as session:
                repo = GapMapRepository(session)
                retriever = GapRetriever(
                    repository=repo,
                    embedding_service=EmbeddingService(api_key=settings.openai_api_key),
                )
                gap_entries = await retriever.retrieve(
                    merged_profile, novelty, limit=settings.gap_retrieval_top_k
                )
        except Exception as e:
            logger.warning("Gap retrieval failed: %s", type(e).__name__)

        # Log gap map retrieval for debugging (public data only)
        if gap_entries:
            logger.info(
                "Gap retrieval: %d entries. Top 5: %s",
                len(gap_entries),
                [(e.title[:50], e.source_url) for e in gap_entries[:5]],
            )
        else:
            logger.warning("Gap retrieval: 0 entries (empty DB or vector search returned none)")

        # -- Stage 5: Pivot matching --
        await _set_stage(redis, session_id, "matching_pivots", ttl)
        openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        pivot_matcher = PivotMatcher(openai_client=openai_client)
        suggestions = await pivot_matcher.match_pivots(
            merged_profile, novelty, gap_entries
        )

        # Log pivot match result for debugging
        if suggestions:
            logger.info("Pivot matching: %d suggestions", len(suggestions))
        elif gap_entries:
            logger.warning(
                "Pivot matching: 0 suggestions despite %d gap entries. Top retrieved: %s",
                len(gap_entries),
                [e.title[:60] for e in gap_entries[:3]],
            )
        else:
            logger.info("Pivot matching: 0 suggestions (no gap entries)")

        # -- Stage 6: Report generation --
        await _set_stage(redis, session_id, "generating_report", ttl)
        report_generator = ReportGenerator(openai_client=openai_client)
        recommendation = await report_generator.generate_report(
            merged_profile, novelty, suggestions
        )

        # -- Done: store completed result --
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        session_data = {
            "status": "completed",
            "stage": "completed",
            "recommendation": recommendation.model_dump_json(),
            "profile": merged_profile.model_dump_json(),
            "elapsed_ms": elapsed_ms,
        }
        if web_search_result and web_search_result.summary:
            session_data["web_search_summary"] = web_search_result.summary[:2000]

        await redis.set(
            f"session:{session_id}",
            json.dumps(session_data),
            ex=ttl,
        )
        # Privacy: No user data logged
        logger.info("Analysis completed for session %s in %dms", session_id, elapsed_ms)

    except Exception as e:
        logger.exception("Pipeline failed for session %s", session_id)
        try:
            await redis.set(
                f"session:{session_id}",
                json.dumps({
                    "status": "error",
                    "stage": "error",
                    "error_message": f"Analysis failed: {type(e).__name__}",
                }),
                ex=ttl,
            )
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: Request,
    messages: str = Form(...),
    files: list[UploadFile] = File(default=[]),
):
    """Start an analysis job and return immediately with a session_id.

    The pipeline runs in the background. Poll GET /analysis/{session_id}
    to retrieve status and results.
    """
    settings = get_settings()

    # Parse messages JSON
    try:
        messages_data = json.loads(messages)
        chat_messages = [ChatMessage(**m) for m in messages_data]
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid messages format: {e}")

    if not chat_messages:
        raise HTTPException(status_code=422, detail="At least one message is required")

    # Validate and read uploaded files eagerly (UploadFile can't be read in background)
    allowed_extensions = {f".{ft}" for ft in settings.allowed_file_types}
    file_contents: list[tuple[str, bytes]] = []
    for f in files:
        ext = _get_file_extension(f.filename or "")
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {ext}. Allowed: {settings.allowed_file_types}",
            )
        file_contents.append((f.filename or "unknown", await f.read()))

    # Create session immediately
    session_id = str(uuid.uuid4())
    redis = request.app.state.redis
    try:
        await redis.set(
            f"session:{session_id}",
            json.dumps({"status": "processing", "stage": "extracting_profile"}),
            ex=settings.session_ttl_seconds,
        )
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Session storage unavailable: {type(e).__name__}",
        )

    # Launch pipeline in background
    asyncio.create_task(
        _run_pipeline(
            session_id=session_id,
            chat_messages=chat_messages,
            file_contents=file_contents,
            redis=redis,
            db_session_factory=request.app.state.db_session_factory,
        )
    )

    return AnalyzeResponse(session_id=session_id, status="processing")


@router.get("/analysis/{session_id}", response_model=SessionStatusResponse)
async def get_analysis(request: Request, session_id: str):
    """Retrieve analysis status and results by session ID.

    Returns current stage while processing, full recommendation when completed.
    """
    redis = request.app.state.redis
    raw = await redis.get(f"session:{session_id}")

    if raw is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = json.loads(raw)
    status = session_data.get("status", "processing")
    stage = session_data.get("stage")

    result = None
    if status == "completed" and "recommendation" in session_data:
        result = ResearchRecommendation.model_validate_json(
            session_data["recommendation"]
        )

    return SessionStatusResponse(
        session_id=session_id,
        status=status,
        stage=stage,
        result=result,
        error_message=session_data.get("error_message"),
    )


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

import logging
import time
import uuid
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Response
from fastapi.responses import PlainTextResponse

from app.core.ai_orchestrator import AIOrchestrator, LocalDeterministicAdapter, OpenAIAdapter
from app.core.export_engine import build_export_bundle
from app.core.input_normalizer import normalize_payload
from app.core.output_formatter import enforce_schema, to_markdown
from app.core.prompt_engine import build_prompt
from app.models.schemas import (
    AdCopyRequest,
    BusinessIdeaRequest,
    CoverLetterRequest,
    GenerateResponse,
    MeetingSummaryRequest,
    RegisterRequest,
    RegisterResponse,
    ResumeRequest,
    UsageResponse,
)
from app.services.security import TIERS, registry
from app.services.storage import StoredResult, result_store
from app.services.usage_tracking import usage_tracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("meta-utility-hub")

app = FastAPI(title="META-UTILITY HUB", version="1.0.0")


def _build_orchestrator() -> AIOrchestrator:
    adapters = []
    try:
        adapters.append(OpenAIAdapter())
    except Exception:
        pass
    adapters.append(LocalDeterministicAdapter())
    return AIOrchestrator(adapters=adapters)


orchestrator = _build_orchestrator()


def require_api_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> tuple[str, str]:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    tier = registry.get_tier(x_api_key)
    if not tier:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key, tier


def _record_usage(api_key: str, tier: str) -> None:
    ok, message = usage_tracker.enforce_and_record(api_key, tier)
    if not ok:
        raise HTTPException(status_code=429, detail=message)


def _run_pipeline(task: str, payload: dict[str, Any], export_pdf: bool) -> GenerateResponse:
    started = time.perf_counter()
    normalized_payload, token_estimate = normalize_payload(payload)
    prompt_payload = build_prompt(task, normalized_payload)
    ai_result = orchestrator.generate(prompt_payload)
    structured_output = enforce_schema(task, ai_result)
    markdown = to_markdown(task, structured_output)
    exports = build_export_bundle(structured_output, markdown, include_pdf=export_pdf)

    result_id = str(uuid.uuid4())
    result_store.put(
        result_id,
        StoredResult(
            task=task,
            json_data=exports.json_data,
            markdown_data=exports.markdown_data,
            pdf_bytes=exports.pdf_bytes,
        ),
    )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "request_type=%s token_estimate=%s latency_ms=%s",
        task,
        token_estimate,
        elapsed_ms,
    )

    base = f"/results/{result_id}/download"
    return GenerateResponse(
        task=task,
        result_id=result_id,
        structured_output=structured_output,
        exports={
            "json": f"{base}?format=json",
            "markdown": f"{base}?format=markdown",
            "pdf": f"{base}?format=pdf" if export_pdf else None,
        },
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "META-UTILITY HUB"}


@app.post("/auth/register", response_model=RegisterResponse)
def register(payload: RegisterRequest) -> RegisterResponse:
    tier = payload.tier.lower().strip()
    if tier not in TIERS:
        raise HTTPException(status_code=400, detail="Invalid tier")
    api_key = registry.register(tier)
    return RegisterResponse(api_key=api_key, tier=tier)


@app.get("/usage", response_model=UsageResponse)
def usage(identity: tuple[str, str] = Depends(require_api_key)) -> UsageResponse:
    api_key, tier = identity
    state = usage_tracker.get_usage(api_key)
    cfg = TIERS[tier]
    return UsageResponse(
        api_key=api_key,
        tier=tier,
        total_requests=state.total_requests,
        monthly_limit=cfg.monthly_requests,
        requests_last_minute=len(state.recent_requests),
        per_minute_limit=cfg.requests_per_minute,
    )


@app.post("/generate/resume", response_model=GenerateResponse)
def generate_resume(
    payload: ResumeRequest, identity: tuple[str, str] = Depends(require_api_key)
) -> GenerateResponse:
    api_key, tier = identity
    _record_usage(api_key, tier)
    return _run_pipeline(
        "resume", {"raw_experience_text": payload.raw_experience_text}, payload.export_pdf
    )


@app.post("/generate/cover-letter", response_model=GenerateResponse)
def generate_cover_letter(
    payload: CoverLetterRequest, identity: tuple[str, str] = Depends(require_api_key)
) -> GenerateResponse:
    api_key, tier = identity
    _record_usage(api_key, tier)
    return _run_pipeline(
        "cover_letter",
        {
            "job_description": payload.job_description,
            "user_profile": payload.user_profile,
        },
        payload.export_pdf,
    )


@app.post("/generate/meeting-summary", response_model=GenerateResponse)
def generate_meeting_summary(
    payload: MeetingSummaryRequest, identity: tuple[str, str] = Depends(require_api_key)
) -> GenerateResponse:
    api_key, tier = identity
    _record_usage(api_key, tier)
    return _run_pipeline("meeting_summary", {"notes": payload.notes}, payload.export_pdf)


@app.post("/generate/business-idea", response_model=GenerateResponse)
def generate_business_idea(
    payload: BusinessIdeaRequest, identity: tuple[str, str] = Depends(require_api_key)
) -> GenerateResponse:
    api_key, tier = identity
    _record_usage(api_key, tier)
    return _run_pipeline("business_idea", {"idea_dump": payload.idea_dump}, payload.export_pdf)


@app.post("/generate/ad-copy", response_model=GenerateResponse)
def generate_ad_copy(
    payload: AdCopyRequest, identity: tuple[str, str] = Depends(require_api_key)
) -> GenerateResponse:
    api_key, tier = identity
    _record_usage(api_key, tier)
    return _run_pipeline(
        "ad_copy", {"product_description": payload.product_description}, payload.export_pdf
    )


@app.get("/results/{result_id}/download")
def download_result(result_id: str, output_format: str) -> Response:
    result = result_store.get(result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    fmt = output_format.lower()
    if fmt == "json":
        return Response(result.json_data, media_type="application/json")
    if fmt == "markdown":
        return PlainTextResponse(result.markdown_data, media_type="text/markdown")
    if fmt == "pdf":
        if not result.pdf_bytes:
            raise HTTPException(status_code=404, detail="PDF not available for this result")
        return Response(result.pdf_bytes, media_type="application/pdf")
    raise HTTPException(status_code=400, detail="format must be json, markdown, or pdf")

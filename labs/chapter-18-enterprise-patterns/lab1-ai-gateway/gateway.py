"""
Chapter 18 — Lab 1: Enterprise AI Gateway
The AI Architect & Practitioner Bootcamp

Single entry point for all AI requests:
  - Tenant identity enforcement
  - Model routing by task type
  - Per-tenant quota enforcement
  - Cost attribution from model usage object
  - Structured audit logging
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from openai import OpenAI
from pydantic import BaseModel

app = FastAPI(title="Enterprise AI Gateway", version="1.0.0")


# ─── Request / Response schemas ──────────────────────────────────────────────

class AIRequest(BaseModel):
    tenant_id: str
    workflow_id: str
    task_type: str           # classification | support_draft | executive_brief | ...
    prompt: str
    model_hint: Optional[str] = None
    max_tokens: int = 700


class AIResponse(BaseModel):
    request_id: str
    tenant_id: str
    workflow_id: str
    model: str
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: float = 0.0


# ─── Quota store (replace with Redis in production) ───────────────────────────

_quota_lock = threading.Lock()
_request_counts: dict[str, int] = defaultdict(int)

TENANT_RPM_LIMITS: dict[str, int] = {
    "default":        100,
    "support":        600,
    "operations":     1000,
    "executive":      200,
}


# ─── Cost rates (load from config in production) ──────────────────────────────

COST_PER_1K: dict[str, dict[str, float]] = {
    "small-model":    {"input": 0.00025, "output": 0.00125},
    "balanced-model": {"input": 0.003,   "output": 0.015},
    "large-model":    {"input": 0.015,   "output": 0.075},
    "default":        {"input": 0.003,   "output": 0.015},
}


# ─── Authorization ────────────────────────────────────────────────────────────

def authorize(req: AIRequest) -> None:
    if not req.tenant_id or not req.tenant_id.strip():
        raise HTTPException(status_code=403, detail="tenant_id is required")


def enforce_quota(tenant_id: str) -> None:
    limit = TENANT_RPM_LIMITS.get(tenant_id, TENANT_RPM_LIMITS["default"])
    with _quota_lock:
        _request_counts[tenant_id] += 1
        if _request_counts[tenant_id] > limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for tenant '{tenant_id}'"
            )


# ─── Model routing ────────────────────────────────────────────────────────────

MODEL_ROUTING: dict[str, str] = {
    "classification":  os.environ.get("SMALL_MODEL",   "small-model"),
    "routing":         os.environ.get("SMALL_MODEL",   "small-model"),
    "support_draft":   os.environ.get("DEFAULT_MODEL", "balanced-model"),
    "rag_answer":      os.environ.get("DEFAULT_MODEL", "balanced-model"),
    "executive_brief": os.environ.get("LARGE_MODEL",   "large-model"),
    "incident_brief":  os.environ.get("LARGE_MODEL",   "large-model"),
}

def route_model(req: AIRequest) -> str:
    if req.model_hint:
        return req.model_hint
    return MODEL_ROUTING.get(req.task_type, os.environ.get("DEFAULT_MODEL", "balanced-model"))


# ─── Cost calculation ─────────────────────────────────────────────────────────

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = COST_PER_1K.get(model, COST_PER_1K["default"])
    return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])


# ─── Audit logging ────────────────────────────────────────────────────────────

def emit_trace(request_id: str, tenant_id: str, workflow_id: str,
               model: str, input_tokens: int, output_tokens: int,
               cost_usd: float, latency_ms: float) -> None:
    event = {
        "event_type": "ai_gateway_request",
        "request_id": request_id,
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost_usd, 6),
        "latency_ms": round(latency_ms, 1),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # In production: emit to observability platform
    print(json.dumps(event))


# ─── Main endpoint ────────────────────────────────────────────────────────────

@app.post("/v1/enterprise/chat", response_model=AIResponse)
def enterprise_chat(req: AIRequest) -> AIResponse:
    started = time.perf_counter()
    request_id = str(uuid.uuid4())

    authorize(req)
    enforce_quota(req.tenant_id)
    model = route_model(req)

    client = OpenAI(
        base_url=os.environ.get("AI_BASE_URL", "http://localhost:8000/v1"),
        api_key=os.environ.get("AI_API_KEY", "not-used"),
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": req.prompt}],
        temperature=0.2,
        max_tokens=req.max_tokens,
        extra_headers={
            "x-tenant-id":  req.tenant_id,
            "x-workflow-id": req.workflow_id,
        },
    )

    text = response.choices[0].message.content or ""
    latency_ms = (time.perf_counter() - started) * 1000

    usage = response.usage
    input_tokens  = usage.prompt_tokens     if usage else 0
    output_tokens = usage.completion_tokens if usage else 0
    cost_usd = estimate_cost(model, input_tokens, output_tokens)

    emit_trace(request_id, req.tenant_id, req.workflow_id,
               model, input_tokens, output_tokens, cost_usd, latency_ms)

    return AIResponse(
        request_id=request_id,
        tenant_id=req.tenant_id,
        workflow_id=req.workflow_id,
        model=model,
        text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=round(cost_usd, 6),
        latency_ms=round(latency_ms, 1),
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-gateway"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

"""Tests for Chapter 18 Lab 1: Enterprise AI Gateway"""
import os
import pytest

os.environ.setdefault("AI_BASE_URL", "http://localhost:8000/v1")
os.environ.setdefault("SMALL_MODEL",   "small-model")
os.environ.setdefault("DEFAULT_MODEL", "balanced-model")
os.environ.setdefault("LARGE_MODEL",   "large-model")

from fastapi.testclient import TestClient
from gateway import app, TENANT_RPM_LIMITS, _request_counts, route_model, AIRequest

client = TestClient(app)


def post_chat(tenant_id: str, task_type: str = "support_draft",
              prompt: str = "Say: ok") -> "Response":
    return client.post("/v1/enterprise/chat", json={
        "tenant_id":  tenant_id,
        "workflow_id": "test",
        "task_type":   task_type,
        "prompt":      prompt,
    })


def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_missing_tenant_id_returns_403():
    resp = client.post("/v1/enterprise/chat", json={
        "tenant_id":  "",
        "workflow_id": "x",
        "task_type":   "support_draft",
        "prompt":      "Hello",
    })
    assert resp.status_code == 403


def test_classification_routes_to_small_model(monkeypatch):
    monkeypatch.setenv("SMALL_MODEL", "haiku-fast")
    req = AIRequest(tenant_id="t", workflow_id="w",
                    task_type="classification", prompt="classify")
    model = route_model(req)
    assert model == "haiku-fast"


def test_executive_brief_routes_to_large_model(monkeypatch):
    monkeypatch.setenv("LARGE_MODEL", "opus-powerful")
    req = AIRequest(tenant_id="t", workflow_id="w",
                    task_type="executive_brief", prompt="brief")
    model = route_model(req)
    assert model == "opus-powerful"


def test_model_hint_overrides_routing():
    req = AIRequest(tenant_id="t", workflow_id="w",
                    task_type="classification", prompt="x",
                    model_hint="custom-model")
    assert route_model(req) == "custom-model"


def test_quota_exceeded_returns_429():
    tenant = "quota-burst-test"
    TENANT_RPM_LIMITS[tenant] = 2
    _request_counts[tenant] = 0

    statuses = []
    for _ in range(5):
        r = client.post("/v1/enterprise/chat", json={
            "tenant_id":  tenant,
            "workflow_id": "quota-test",
            "task_type":   "support_draft",
            "prompt":      "test",
        })
        statuses.append(r.status_code)

    assert 429 in statuses

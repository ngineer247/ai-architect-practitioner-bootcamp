"""
Tests for Chapter 24 Lab 4: Capstone Incident Agent
Tests the LangGraph state machine logic without requiring
a live PostgreSQL connection or model endpoint.
"""
from __future__ import annotations

import pytest
from incident_agent import (
    IncidentState,
    classify_intent_node,
    retrieve_runbooks_node,
    query_telemetry_node,
    assess_customer_impact_node,
    generate_recommendation_node,
    create_approval_packet_node,
    draft_response_node,
    route_after_recommendation,
    _format_brief,
)


def base_state(**overrides) -> IncidentState:
    state: IncidentState = {
        "incident_id":       "TEST-001",
        "tenant_id":         "operations",
        "user_role":         "analyst",
        "symptom":           "Heartbeat failures in East region",
        "region":            "East",
        "firmware_version":  "7.2",
        "intent":            None,
        "retrieved_docs":    [],
        "telemetry":         {},
        "customer_impact":   {},
        "recommendation":    None,
        "evidence_references": [],
        "confidence":        None,
        "approval_required": False,
        "approval_id":       None,
        "approval_status":   None,
        "approval_reason":   None,
        "step_count":        0,
        "max_steps":         10,
        "errors":            [],
        "final_brief":       None,
    }
    state.update(overrides)
    return state


# ─── Node tests ───────────────────────────────────────────────────────────────

def test_classify_firmware_incident():
    state = base_state(symptom="Firmware 7.2 causing failures")
    result = classify_intent_node(state)
    assert result["intent"] == "firmware_incident"
    assert result["step_count"] == 1


def test_classify_connectivity_incident():
    state = base_state(symptom="Heartbeat failures and connectivity issues")
    result = classify_intent_node(state)
    assert result["intent"] == "connectivity_incident"


def test_classify_unknown_falls_back_to_general():
    state = base_state(symptom="Something is wrong with the system")
    result = classify_intent_node(state)
    assert result["intent"] == "general_incident"


def test_retrieve_runbooks_returns_docs():
    state = base_state()
    result = retrieve_runbooks_node(state)
    assert len(result["retrieved_docs"]) >= 1
    assert len(result["evidence_references"]) >= 1


def test_query_telemetry_returns_structured_data():
    state = base_state()
    result = query_telemetry_node(state)
    assert "heartbeat_failure_rate_pct" in result["telemetry"]
    assert result["telemetry"]["region"] == "East"


def test_assess_impact_uses_telemetry():
    state = base_state(
        telemetry={"heartbeat_failure_rate_pct": 34.2, "affected_devices": 4300}
    )
    result = assess_customer_impact_node(state)
    assert result["customer_impact"]["sla_breach_risk"] == "high"


def test_generate_recommendation_flags_approval_for_firmware():
    state = base_state(
        intent="firmware_incident",
        telemetry={"heartbeat_failure_rate_pct": 34.2, "affected_devices": 4300},
        customer_impact={},
        retrieved_docs=[{"doc_id": "r1"}, {"doc_id": "r2"}],
        evidence_references=["r1", "r2"],
    )
    result = generate_recommendation_node(state)
    assert result["approval_required"] is True
    assert result["recommendation"] is not None


def test_generate_recommendation_no_approval_for_low_risk():
    state = base_state(
        intent="general_incident",
        telemetry={"heartbeat_failure_rate_pct": 5.0, "affected_devices": 12},
        customer_impact={},
        retrieved_docs=[{"doc_id": "r1"}],
        evidence_references=["r1"],
    )
    result = generate_recommendation_node(state)
    assert result["approval_required"] is False


def test_create_approval_packet_generates_id():
    state = base_state(
        recommendation="Prepare rollback assessment",
        evidence_references=["runbook-v3"],
        customer_impact={"devices_affected": 100},
        confidence="high",
    )
    result = create_approval_packet_node(state)
    assert result["approval_id"].startswith("APR-")
    assert result["approval_status"] == "pending"


# ─── Routing tests ────────────────────────────────────────────────────────────

def test_route_to_approval_when_required():
    state = base_state(approval_required=True, step_count=3)
    assert route_after_recommendation(state) == "create_approval_packet"


def test_route_to_draft_when_not_required():
    state = base_state(approval_required=False, step_count=3)
    assert route_after_recommendation(state) == "draft_response"


def test_route_to_draft_when_max_steps_exceeded():
    state = base_state(approval_required=True, step_count=11, max_steps=10)
    assert route_after_recommendation(state) == "draft_response"


def test_route_to_draft_when_errors_present():
    state = base_state(
        approval_required=True, step_count=3,
        errors=[{"node": "query_telemetry", "error": "timeout"}]
    )
    assert route_after_recommendation(state) == "draft_response"


# ─── Brief format test ────────────────────────────────────────────────────────

def test_brief_contains_key_sections():
    state = base_state(
        recommendation="Investigate firmware correlation.",
        evidence_references=["runbook-heartbeat-v3"],
        customer_impact={
            "devices_affected": 4300, "customers_affected": 12,
            "sla_breach_risk": "high", "revenue_at_risk_usd": 85000
        },
        approval_id="APR-12345",
        confidence="high",
    )
    brief = _format_brief(state, "Proceed with rollback assessment.")
    assert "INCIDENT BRIEF" in brief
    assert "SITUATION" in brief
    assert "CUSTOMER IMPACT" in brief
    assert "NEXT ACTION" in brief
    assert "EVIDENCE" in brief
    assert "runbook-heartbeat-v3" in brief

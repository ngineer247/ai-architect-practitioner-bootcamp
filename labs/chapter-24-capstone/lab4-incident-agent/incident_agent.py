"""
Chapter 24 — Lab 4: Enterprise Agentic Operations Platform
The AI Architect & Practitioner Bootcamp

Full LangGraph incident investigation agent with:
  - TypedDict state
  - Five investigation nodes
  - Human approval interrupt/resume via PostgresSaver
  - Structured final brief generation

Setup:
  pip install langgraph langgraph-checkpoint-postgres psycopg2-binary
  export DB_URI="postgresql://user:password@localhost:5432/ops_agents"
  export AI_BASE_URL="http://your-model-endpoint/v1"
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Optional, Any

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg2


# ─── State ────────────────────────────────────────────────────────────────────

class IncidentState(TypedDict):
    # Identity
    incident_id: str
    tenant_id: str
    user_role: str
    # Input
    symptom: str
    region: str
    firmware_version: Optional[str]
    # Evidence
    intent: Optional[str]
    retrieved_docs: list[dict[str, Any]]
    telemetry: dict[str, Any]
    customer_impact: dict[str, Any]
    # Decision
    recommendation: Optional[str]
    evidence_references: list[str]
    confidence: Optional[str]
    # Approval
    approval_required: bool
    approval_id: Optional[str]
    approval_status: Optional[str]    # pending | approved | rejected
    approval_reason: Optional[str]
    # Control
    step_count: int
    max_steps: int
    errors: list[dict[str, Any]]
    # Output
    final_brief: Optional[str]


# ─── Nodes ────────────────────────────────────────────────────────────────────

def classify_intent_node(state: IncidentState) -> dict:
    symptom = state["symptom"].lower()
    if any(kw in symptom for kw in ["firmware", "rollback", "version"]):
        intent = "firmware_incident"
    elif any(kw in symptom for kw in ["heartbeat", "connectivity", "offline"]):
        intent = "connectivity_incident"
    else:
        intent = "general_incident"
    return {"intent": intent, "step_count": state["step_count"] + 1}


def retrieve_runbooks_node(state: IncidentState) -> dict:
    # In production: call your RAG platform with metadata filters
    docs = [
        {"doc_id": "runbook-heartbeat-v3", "title": "Heartbeat Failure Triage v3",
         "effective_date": "2026-05-01", "source_type": "runbook"},
        {"doc_id": f"firmware-notes-{state.get('firmware_version', 'unknown')}",
         "title": f"Firmware {state.get('firmware_version', 'unknown')} Release Notes",
         "source_type": "firmware_notes"},
    ]
    return {
        "retrieved_docs": docs,
        "evidence_references": [d["doc_id"] for d in docs],
        "step_count": state["step_count"] + 1,
    }


def query_telemetry_node(state: IncidentState) -> dict:
    try:
        # In production: call ToolGateway("get_device_telemetry", {...}, state["user_role"])
        telemetry = {
            "heartbeat_failure_rate_pct": 34.2,
            "affected_devices": 4300,
            "region": state["region"],
            "first_failure_utc": "2026-06-27T08:14:00Z",
            "firmware_cohort": state.get("firmware_version", "unknown"),
        }
        return {"telemetry": telemetry, "step_count": state["step_count"] + 1}
    except Exception as e:
        return {
            "errors": state["errors"] + [{"node": "query_telemetry", "error": str(e)}],
            "step_count": state["step_count"] + 1,
        }


def assess_customer_impact_node(state: IncidentState) -> dict:
    # In production: call ToolGateway("get_customer_impact", {...})
    failure_rate = state["telemetry"].get("heartbeat_failure_rate_pct", 0)
    impact = {
        "customers_affected": 12,
        "devices_affected": state["telemetry"].get("affected_devices", 0),
        "sla_breach_risk": "high" if failure_rate > 25 else "low",
        "revenue_at_risk_usd": 85000,
    }
    return {"customer_impact": impact, "step_count": state["step_count"] + 1}


def generate_recommendation_node(state: IncidentState) -> dict:
    # In production: model call with retrieved docs + telemetry + customer impact as context
    failure_rate = state["telemetry"].get("heartbeat_failure_rate_pct", 0)
    affected    = state["telemetry"].get("affected_devices", 0)
    intent      = state.get("intent", "general_incident")

    requires_approval = intent == "firmware_incident" or failure_rate > 30

    recommendation = (
        f"Heartbeat failure rate at {failure_rate:.1f}% across {affected:,} devices in "
        f"{state['region']}. Evidence correlates with "
        f"{state.get('firmware_version', 'recent')} firmware deployment. "
        f"Follow runbook-heartbeat-v3. "
        + ("Prepare rollback assessment — requires release engineering approval."
           if requires_approval else "Escalate to SRE for monitoring.")
    )
    confidence = "high" if len(state["retrieved_docs"]) >= 2 and failure_rate > 25 else "medium"
    return {
        "recommendation": recommendation,
        "approval_required": requires_approval,
        "confidence": confidence,
        "step_count": state["step_count"] + 1,
    }


def create_approval_packet_node(state: IncidentState) -> dict:
    approval_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
    packet = {
        "approval_id":         approval_id,
        "incident_id":         state["incident_id"],
        "recommended_action":  "prepare firmware rollback assessment",
        "risk_tier":           5,
        "evidence":            state["evidence_references"],
        "customer_impact":     state["customer_impact"],
        "required_approver":   "release_engineering_manager",
        "model_recommendation": state["recommendation"],
        "confidence":          state["confidence"],
        "expires_in_minutes":  30,
    }
    print(f"\n[APPROVAL REQUIRED] Packet: {approval_id}")
    print(json.dumps(packet, indent=2))
    return {
        "approval_id":    approval_id,
        "approval_status": "pending",
        "step_count":     state["step_count"] + 1,
    }


def finalize_after_approval_node(state: IncidentState) -> dict:
    status = state.get("approval_status", "pending")
    if status == "approved":
        action_line = f"Rollback assessment approved. Proceed per approval {state['approval_id']}."
    elif status == "rejected":
        action_line = "Rollback assessment rejected. Escalate to SRE leadership."
    else:
        action_line = "Approval pending. Do not proceed until decision is received."

    brief = _format_brief(state, action_line)
    return {"final_brief": brief, "step_count": state["step_count"] + 1}


def draft_response_node(state: IncidentState) -> dict:
    action_line = "Escalate to SRE. Monitor per runbook."
    brief = _format_brief(state, action_line)
    return {"final_brief": brief, "step_count": state["step_count"] + 1}


def _format_brief(state: IncidentState, action_line: str) -> str:
    return f"""
INCIDENT BRIEF — {state['incident_id']}
Region: {state['region']} | Device cohort: {state.get('firmware_version', 'unknown')}

SITUATION
{state.get('recommendation', 'Investigation incomplete.')}

CUSTOMER IMPACT
Devices affected:   {state['customer_impact'].get('devices_affected', 0):,}
Customers affected: {state['customer_impact'].get('customers_affected', 0)}
Revenue at risk:    ${state['customer_impact'].get('revenue_at_risk_usd', 0):,}
SLA breach risk:    {state['customer_impact'].get('sla_breach_risk', 'unknown').upper()}

NEXT ACTION
{action_line}

EVIDENCE
{chr(10).join(f'  - {ref}' for ref in state.get('evidence_references', []))}

CONFIDENCE: {state.get('confidence', 'unknown').upper()}
""".strip()


# ─── Routing ──────────────────────────────────────────────────────────────────

def route_after_recommendation(state: IncidentState) -> str:
    if state["step_count"] >= state["max_steps"] or state.get("errors"):
        return "draft_response"
    return "create_approval_packet" if state["approval_required"] else "draft_response"


def route_after_approval(state: IncidentState) -> str:
    return "finalize_after_approval"


# ─── Graph ────────────────────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(IncidentState)

    graph.add_node("classify_intent",         classify_intent_node)
    graph.add_node("retrieve_runbooks",       retrieve_runbooks_node)
    graph.add_node("query_telemetry",         query_telemetry_node)
    graph.add_node("assess_customer_impact",  assess_customer_impact_node)
    graph.add_node("generate_recommendation", generate_recommendation_node)
    graph.add_node("create_approval_packet",  create_approval_packet_node)
    graph.add_node("finalize_after_approval", finalize_after_approval_node)
    graph.add_node("draft_response",          draft_response_node)

    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent",        "retrieve_runbooks")
    graph.add_edge("retrieve_runbooks",      "query_telemetry")
    graph.add_edge("query_telemetry",        "assess_customer_impact")
    graph.add_edge("assess_customer_impact", "generate_recommendation")
    graph.add_conditional_edges(
        "generate_recommendation", route_after_recommendation,
        {"create_approval_packet": "create_approval_packet",
         "draft_response":          "draft_response"},
    )
    graph.add_conditional_edges(
        "create_approval_packet", route_after_approval,
        {"finalize_after_approval": "finalize_after_approval"},
    )
    graph.add_edge("finalize_after_approval", END)
    graph.add_edge("draft_response",          END)
    return graph


# ─── Runner ───────────────────────────────────────────────────────────────────

DB_URI = os.environ.get("DB_URI", "postgresql://user:password@localhost:5432/ops_agents")


def run_incident_agent(
    incident_id: str,
    tenant_id: str,
    user_role: str,
    symptom: str,
    region: str,
    firmware_version: Optional[str] = None,
) -> dict:
    conn = psycopg2.connect(DB_URI)
    checkpointer = PostgresSaver(conn)
    checkpointer.setup()

    app = build_graph().compile(
        checkpointer=checkpointer,
        interrupt_after=["create_approval_packet"],
    )
    config = {"configurable": {"thread_id": incident_id}}

    initial: IncidentState = {
        "incident_id": incident_id, "tenant_id": tenant_id, "user_role": user_role,
        "symptom": symptom, "region": region, "firmware_version": firmware_version,
        "intent": None, "retrieved_docs": [], "telemetry": {}, "customer_impact": {},
        "recommendation": None, "evidence_references": [], "confidence": None,
        "approval_required": False, "approval_id": None,
        "approval_status": None, "approval_reason": None,
        "step_count": 0, "max_steps": 10, "errors": [], "final_brief": None,
    }

    print(f"\nStarting incident agent: {incident_id}")
    for event in app.stream(initial, config):
        print(f"  ✓ {list(event.keys())[0]}")

    state = app.get_state(config)
    return {
        "status": "awaiting_approval" if state.values.get("approval_required") else "complete",
        "approval_id": state.values.get("approval_id"),
        "brief": state.values.get("final_brief"),
        "errors": state.values.get("errors", []),
    }


def resume_after_approval(
    incident_id: str,
    approved: bool,
    approver_role: str,
    reason: str = "",
) -> dict:
    conn = psycopg2.connect(DB_URI)
    checkpointer = PostgresSaver(conn)
    app = build_graph().compile(
        checkpointer=checkpointer,
        interrupt_after=["create_approval_packet"],
    )
    config = {"configurable": {"thread_id": incident_id}}
    app.update_state(config, {
        "approval_status": "approved" if approved else "rejected",
        "approval_reason": reason,
    })
    print(f"\nResuming {incident_id}: {'approved' if approved else 'rejected'} by {approver_role}")
    for event in app.stream(None, config):
        print(f"  ✓ {list(event.keys())[0]}")
    final = app.get_state(config)
    return {"final_brief": final.values.get("final_brief")}


if __name__ == "__main__":
    result = run_incident_agent(
        incident_id="INC-2026-001",
        tenant_id="operations",
        user_role="analyst",
        symptom="Heartbeat failures after firmware 7.2 rollout in East region",
        region="East",
        firmware_version="7.2",
    )
    print(f"\nStatus: {result['status']}")
    if result.get("brief"):
        print(f"\n{result['brief']}")

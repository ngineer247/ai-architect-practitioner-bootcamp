"""Tests for Chapter 19 Lab 2: Tool Authorization Service"""
import logging
import pytest
from tool_auth import ToolAuthService, ToolRequest

POLICY_YAML = """
tools:
  - name: get_telemetry
    risk_tier: 2
    type: read
    allowed_roles: [support_l1, support_l2, operations]
    approval_required: false

  - name: issue_refund
    risk_tier: 4
    type: write
    allowed_roles: [support_manager]
    approval_required: true

  - name: firmware_rollback
    risk_tier: 5
    type: write
    allowed_roles: [operations]
    approval_required: true
    fail_closed: true
"""


@pytest.fixture
def auth(tmp_path):
    p = tmp_path / "tool_policy.yaml"
    p.write_text(POLICY_YAML)
    return ToolAuthService(str(p))


def req(tool: str, roles: set) -> ToolRequest:
    return ToolRequest(user_id="u1", tenant_id="t1",
                       tool_name=tool, user_roles=roles, params={})


def test_unknown_tool_denied(auth):
    d = auth.authorize(req("delete_everything", {"admin"}))
    assert not d.allowed
    assert "Unknown tool" in d.reason


def test_read_tool_allowed_for_permitted_role(auth):
    d = auth.authorize(req("get_telemetry", {"support_l1"}))
    assert d.allowed
    assert not d.requires_approval


def test_write_tool_denied_for_wrong_role(auth):
    d = auth.authorize(req("issue_refund", {"support_l1"}))
    assert not d.allowed
    assert not d.requires_approval
    assert "not permitted" in d.reason


def test_approval_required_tool_returns_approval_id(auth):
    d = auth.authorize(req("issue_refund", {"support_manager"}))
    assert not d.allowed
    assert d.requires_approval
    assert d.approval_id and d.approval_id.startswith("APR-")


def test_high_risk_tool_always_requires_approval(auth):
    d = auth.authorize(req("firmware_rollback", {"operations"}))
    assert d.requires_approval
    assert d.risk_tier == 5


def test_multi_role_user_passes_if_one_role_matches(auth):
    d = auth.authorize(req("get_telemetry", {"support_l1", "analyst", "viewer"}))
    assert d.allowed


def test_audit_event_logged(auth, caplog):
    with caplog.at_level(logging.INFO, logger="tool_auth"):
        auth.authorize(req("get_telemetry", {"support_l1"}))
    assert any("ai_tool_authorization" in r.message for r in caplog.records)


def test_audit_event_logged_for_denied_call(auth, caplog):
    with caplog.at_level(logging.INFO, logger="tool_auth"):
        auth.authorize(req("firmware_rollback", {"support_l1"}))  # Wrong role
    log_text = " ".join(r.message for r in caplog.records)
    assert "ai_tool_authorization" in log_text
    assert '"allowed": false' in log_text

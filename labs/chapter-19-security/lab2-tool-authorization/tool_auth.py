"""
Chapter 19 — Lab 2: Tool Authorization Service
The AI Architect & Practitioner Bootcamp

Deterministic tool authorization:
  - YAML policy loading
  - Role-based access control
  - Risk tier enforcement
  - Approval routing for high-risk tools
  - Structured audit logging for every decision
"""
from __future__ import annotations

import json
import uuid
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ToolRequest:
    user_id: str
    tenant_id: str
    tool_name: str
    user_roles: set[str]
    params: dict


@dataclass
class AuthDecision:
    allowed: bool
    requires_approval: bool
    approval_id: Optional[str]
    reason: str
    risk_tier: int


class ToolAuthService:
    """
    Deterministic tool authorization service.
    The model may REQUEST a tool. This service AUTHORIZES it.
    No model is involved in the authorization decision.
    """

    def __init__(self, policy_path: str = "tool_policy.yaml"):
        data = yaml.safe_load(Path(policy_path).read_text(encoding="utf-8"))
        self._policy: dict[str, dict] = {t["name"]: t for t in data.get("tools", [])}

    def authorize(self, req: ToolRequest) -> AuthDecision:
        spec = self._policy.get(req.tool_name)

        if spec is None:
            decision = AuthDecision(
                allowed=False, requires_approval=False, approval_id=None,
                reason=f"Unknown tool: '{req.tool_name}'", risk_tier=99,
            )
            self._audit(req, decision)
            return decision

        risk_tier        = spec.get("risk_tier", 1)
        allowed_roles    = set(spec.get("allowed_roles", []))
        approval_required = spec.get("approval_required", False) or risk_tier >= 4

        # Role check — always before approval check
        if allowed_roles and not req.user_roles.intersection(allowed_roles):
            decision = AuthDecision(
                allowed=False, requires_approval=False, approval_id=None,
                reason=(
                    f"Role not permitted for '{req.tool_name}'. "
                    f"Required: one of {allowed_roles}. "
                    f"User has: {req.user_roles}"
                ),
                risk_tier=risk_tier,
            )
            self._audit(req, decision)
            return decision

        # Approval path
        if approval_required:
            approval_id = f"APR-{uuid.uuid4().hex[:8].upper()}"
            decision = AuthDecision(
                allowed=False, requires_approval=True, approval_id=approval_id,
                reason=f"'{req.tool_name}' (risk tier {risk_tier}) requires human approval",
                risk_tier=risk_tier,
            )
            self._audit(req, decision)
            return decision

        # Permitted
        decision = AuthDecision(
            allowed=True, requires_approval=False, approval_id=None,
            reason="authorized", risk_tier=risk_tier,
        )
        self._audit(req, decision)
        return decision

    def _audit(self, req: ToolRequest, decision: AuthDecision) -> None:
        event = {
            "event_type":        "ai_tool_authorization",
            "event_id":          str(uuid.uuid4()),
            "tool_name":         req.tool_name,
            "user_id":           req.user_id,
            "tenant_id":         req.tenant_id,
            "user_roles":        sorted(req.user_roles),
            "risk_tier":         decision.risk_tier,
            "allowed":           decision.allowed,
            "requires_approval": decision.requires_approval,
            "approval_id":       decision.approval_id,
            "reason":            decision.reason,
            "timestamp":         datetime.now(timezone.utc).isoformat(),
        }
        logger.info(json.dumps(event, sort_keys=True))

"""
Chapter 21 — Lab 2: Workflow Cost Collector
The AI Architect & Practitioner Bootcamp

Aggregates per-event cost data into per-workflow, per-tenant summaries.
The key metric: cost per successful, safe, useful business workflow.

Usage:
  python workflow_cost.py sample_events.jsonl
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

COST_FIELDS = [
    "model_cost_usd",
    "retrieval_cost_usd",
    "rerank_cost_usd",
    "guardrail_cost_usd",
    "tool_cost_usd",
    "evaluation_cost_usd",
    "human_review_cost_usd",
]


@dataclass
class WorkflowCostAccumulator:
    tenant_id: str
    workflow_id: str
    total_cost_usd: float = 0.0
    model_cost_usd: float = 0.0
    retrieval_cost_usd: float = 0.0
    rerank_cost_usd: float = 0.0
    guardrail_cost_usd: float = 0.0
    tool_cost_usd: float = 0.0
    evaluation_cost_usd: float = 0.0
    human_review_cost_usd: float = 0.0
    successful_tasks: int = 0
    failed_tasks: int = 0

    @property
    def total_tasks(self) -> int:
        return self.successful_tasks + self.failed_tasks

    @property
    def cost_per_successful_task(self) -> float:
        if self.successful_tasks == 0:
            return float("inf")
        return self.total_cost_usd / self.successful_tasks

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.successful_tasks / self.total_tasks

    def add_event(self, event: dict) -> None:
        event_total = sum(event.get(f, 0.0) for f in COST_FIELDS)
        self.total_cost_usd += event_total
        for fname in COST_FIELDS:
            current = getattr(self, fname)
            setattr(self, fname, current + event.get(fname, 0.0))
        if event.get("workflow_success"):
            self.successful_tasks += 1
        else:
            self.failed_tasks += 1


def collect_workflow_costs(
    events_path: str,
) -> dict[tuple[str, str], WorkflowCostAccumulator]:
    """Read a JSONL cost events file and aggregate by (tenant_id, workflow_id)."""
    accumulators: dict[tuple[str, str], WorkflowCostAccumulator] = {}
    for line in Path(events_path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        key = (event["tenant_id"], event["workflow_id"])
        if key not in accumulators:
            accumulators[key] = WorkflowCostAccumulator(
                tenant_id=event["tenant_id"],
                workflow_id=event["workflow_id"],
            )
        accumulators[key].add_event(event)
    return accumulators


def print_report(accumulators: dict[tuple, WorkflowCostAccumulator]) -> None:
    header = f"\n{'Tenant':<18} {'Workflow':<24} {'Tasks':>6} {'Success':>8} {'Total $':>10} {'$/Success':>12}"
    print(header)
    print("-" * len(header))
    for acc in sorted(accumulators.values(), key=lambda a: a.cost_per_successful_task):
        cps = acc.cost_per_successful_task
        cps_str = f"${cps:.4f}" if cps != float("inf") else "N/A (0 successes)"
        print(
            f"{acc.tenant_id:<18} {acc.workflow_id:<24} "
            f"{acc.total_tasks:>6} {acc.success_rate:>7.0%} "
            f"${acc.total_cost_usd:>9.4f} {cps_str:>12}"
        )


def check_alerts(
    accumulators: dict[tuple, WorkflowCostAccumulator],
    cost_per_task_alert_usd: float = 0.10,
    success_rate_alert: float = 0.80,
) -> list[str]:
    """Return alert messages for workflows exceeding thresholds."""
    alerts = []
    for acc in accumulators.values():
        if acc.cost_per_successful_task > cost_per_task_alert_usd:
            alerts.append(
                f"HIGH COST: {acc.tenant_id}/{acc.workflow_id} — "
                f"${acc.cost_per_successful_task:.4f}/success "
                f"(threshold: ${cost_per_task_alert_usd:.2f})"
            )
        if acc.success_rate < success_rate_alert and acc.total_tasks >= 5:
            alerts.append(
                f"LOW SUCCESS: {acc.tenant_id}/{acc.workflow_id} — "
                f"{acc.success_rate:.0%} success rate "
                f"(threshold: {success_rate_alert:.0%})"
            )
    return alerts


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "sample_events.jsonl"
    accs = collect_workflow_costs(path)
    print_report(accs)

    alerts = check_alerts(accs)
    if alerts:
        print("\n⚠ ALERTS:")
        for a in alerts:
            print(f"  {a}")

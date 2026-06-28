"""Tests for Chapter 21 Lab 2: Workflow Cost Collector"""
import json
import math
import tempfile
from pathlib import Path

import pytest
from workflow_cost import (
    WorkflowCostAccumulator,
    check_alerts,
    collect_workflow_costs,
)


def make_event(**kwargs):
    base = {
        "tenant_id": "tenant-a",
        "workflow_id": "wf-1",
        "model_cost_usd": 0.0,
        "retrieval_cost_usd": 0.0,
        "rerank_cost_usd": 0.0,
        "guardrail_cost_usd": 0.0,
        "tool_cost_usd": 0.0,
        "evaluation_cost_usd": 0.0,
        "human_review_cost_usd": 0.0,
        "workflow_success": True,
    }
    base.update(kwargs)
    return base


def write_jsonl(events):
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for e in events:
        f.write(json.dumps(e) + "\n")
    f.close()
    return f.name


class TestWorkflowCostAccumulator:
    def test_initial_state(self):
        acc = WorkflowCostAccumulator("t1", "wf1")
        assert acc.total_tasks == 0
        assert acc.success_rate == 0.0
        assert math.isinf(acc.cost_per_successful_task)

    def test_add_successful_event(self):
        acc = WorkflowCostAccumulator("t1", "wf1")
        acc.add_event(make_event(model_cost_usd=0.05, workflow_success=True))
        assert acc.successful_tasks == 1
        assert acc.failed_tasks == 0
        assert acc.total_cost_usd == pytest.approx(0.05)

    def test_add_failed_event(self):
        acc = WorkflowCostAccumulator("t1", "wf1")
        acc.add_event(make_event(model_cost_usd=0.02, workflow_success=False))
        assert acc.successful_tasks == 0
        assert acc.failed_tasks == 1

    def test_cost_per_successful_task(self):
        acc = WorkflowCostAccumulator("t1", "wf1")
        acc.add_event(make_event(model_cost_usd=0.10, workflow_success=True))
        acc.add_event(make_event(model_cost_usd=0.10, workflow_success=True))
        assert acc.cost_per_successful_task == pytest.approx(0.10)

    def test_success_rate(self):
        acc = WorkflowCostAccumulator("t1", "wf1")
        acc.add_event(make_event(workflow_success=True))
        acc.add_event(make_event(workflow_success=False))
        assert acc.success_rate == pytest.approx(0.5)

    def test_all_cost_fields_accumulated(self):
        acc = WorkflowCostAccumulator("t1", "wf1")
        acc.add_event(make_event(
            model_cost_usd=0.01,
            retrieval_cost_usd=0.02,
            guardrail_cost_usd=0.03,
        ))
        assert acc.model_cost_usd == pytest.approx(0.01)
        assert acc.retrieval_cost_usd == pytest.approx(0.02)
        assert acc.guardrail_cost_usd == pytest.approx(0.03)
        assert acc.total_cost_usd == pytest.approx(0.06)


class TestCollectWorkflowCosts:
    def test_single_event(self):
        path = write_jsonl([make_event(model_cost_usd=0.05)])
        result = collect_workflow_costs(path)
        assert len(result) == 1
        acc = result[("tenant-a", "wf-1")]
        assert acc.total_cost_usd == pytest.approx(0.05)

    def test_groups_by_tenant_and_workflow(self):
        events = [
            make_event(tenant_id="t1", workflow_id="wf-1", model_cost_usd=0.01),
            make_event(tenant_id="t2", workflow_id="wf-1", model_cost_usd=0.02),
            make_event(tenant_id="t1", workflow_id="wf-2", model_cost_usd=0.03),
        ]
        result = collect_workflow_costs(write_jsonl(events))
        assert len(result) == 3

    def test_accumulates_multiple_events_same_key(self):
        events = [
            make_event(model_cost_usd=0.05, workflow_success=True),
            make_event(model_cost_usd=0.05, workflow_success=False),
        ]
        result = collect_workflow_costs(write_jsonl(events))
        acc = result[("tenant-a", "wf-1")]
        assert acc.total_cost_usd == pytest.approx(0.10)
        assert acc.total_tasks == 2

    def test_skips_blank_lines(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
        f.write(json.dumps(make_event(model_cost_usd=0.01)) + "\n")
        f.write("\n")
        f.write(json.dumps(make_event(model_cost_usd=0.02)) + "\n")
        f.close()
        result = collect_workflow_costs(f.name)
        assert result[("tenant-a", "wf-1")].total_cost_usd == pytest.approx(0.03)


class TestCheckAlerts:
    def _acc(self, n_success, n_fail, cost_each=0.05):
        acc = WorkflowCostAccumulator("t1", "wf1")
        for _ in range(n_success):
            acc.add_event(make_event(model_cost_usd=cost_each, workflow_success=True))
        for _ in range(n_fail):
            acc.add_event(make_event(model_cost_usd=cost_each, workflow_success=False))
        return acc

    def test_no_alerts_normal(self):
        acc = self._acc(n_success=10, n_fail=0, cost_each=0.01)
        assert check_alerts({("t1", "wf1"): acc}) == []

    def test_high_cost_alert(self):
        acc = self._acc(n_success=1, n_fail=0, cost_each=0.50)
        alerts = check_alerts({("t1", "wf1"): acc}, cost_per_task_alert_usd=0.10)
        assert any("HIGH COST" in a for a in alerts)

    def test_low_success_alert(self):
        acc = self._acc(n_success=1, n_fail=9, cost_each=0.01)
        alerts = check_alerts({("t1", "wf1"): acc}, success_rate_alert=0.80)
        assert any("LOW SUCCESS" in a for a in alerts)

    def test_low_success_skipped_under_5_tasks(self):
        acc = self._acc(n_success=0, n_fail=4, cost_each=0.01)
        alerts = check_alerts({("t1", "wf1"): acc}, success_rate_alert=0.80)
        assert not any("LOW SUCCESS" in a for a in alerts)

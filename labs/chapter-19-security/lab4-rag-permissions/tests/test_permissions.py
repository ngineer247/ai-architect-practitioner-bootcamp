"""Tests for Chapter 19 Lab 4: RAG Permission Enforcement"""
import pytest
from retrieval_policy import RetrievalPolicy


@pytest.fixture
def policy(tmp_path):
    p = tmp_path / "documents.jsonl"
    p.write_text('\n'.join([
        '{"doc_id":"d1","tenant_id":"tenant-a","classification":"internal","title":"A Internal","content":"...","owner":"t"}',
        '{"doc_id":"d2","tenant_id":"tenant-b","classification":"internal","title":"B Internal","content":"...","owner":"t"}',
        '{"doc_id":"d3","tenant_id":"shared","classification":"public","title":"Public FAQ","content":"...","owner":"t"}',
        '{"doc_id":"d4","tenant_id":"tenant-a","classification":"restricted","title":"A Restricted","content":"...","owner":"t"}',
    ]))
    return RetrievalPolicy(str(p))


def test_tenant_a_cannot_see_tenant_b(policy):
    results = policy.retrieve("tenant-a", ["internal"])
    assert all(d.tenant_id != "tenant-b" for d in results)


def test_shared_docs_visible_to_all_tenants(policy):
    a = {d.doc_id for d in policy.retrieve("tenant-a", ["public"])}
    b = {d.doc_id for d in policy.retrieve("tenant-b", ["public"])}
    assert "d3" in a and "d3" in b


def test_restricted_doc_blocked_without_clearance(policy):
    results = policy.retrieve("tenant-a", ["internal"])
    assert "d4" not in {d.doc_id for d in results}


def test_restricted_doc_visible_with_clearance(policy):
    results = policy.retrieve("tenant-a", ["internal", "restricted"])
    assert "d4" in {d.doc_id for d in results}


def test_citation_denied_for_wrong_tenant(policy):
    doc = policy.get_doc("d2", tenant_id="tenant-a", user_data_clearance=["internal"])
    assert doc is None

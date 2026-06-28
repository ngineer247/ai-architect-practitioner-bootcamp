"""
Chapter 19 — Lab 4: Secure RAG Permission Tests
The AI Architect & Practitioner Bootcamp

Enforces tenant isolation and data classification during retrieval.
Documents are filtered BEFORE they reach the model context.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CLASSIFICATION_RANK = {"public": 0, "internal": 1, "confidential": 2, "restricted": 3}


@dataclass
class Document:
    doc_id: str
    tenant_id: str
    classification: str
    title: str
    content: str
    owner: str


class RetrievalPolicy:
    """Permission-aware document retrieval. Filter at query time, not after."""

    def __init__(self, documents_path: str = "documents.jsonl"):
        self._docs: list[Document] = []
        for line in Path(documents_path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                self._docs.append(Document(**d))

    def retrieve(self, tenant_id: str,
                 user_data_clearance: list[str],
                 query: str = "") -> list[Document]:
        max_rank = max(
            (CLASSIFICATION_RANK.get(c, 0) for c in user_data_clearance),
            default=0
        )
        allowed = []
        for doc in self._docs:
            if doc.tenant_id != tenant_id and doc.tenant_id != "shared":
                continue
            if CLASSIFICATION_RANK.get(doc.classification, 99) > max_rank:
                continue
            allowed.append(doc)
        return allowed

    def get_doc(self, doc_id: str, tenant_id: str,
                user_data_clearance: list[str]) -> Document | None:
        permitted = self.retrieve(tenant_id, user_data_clearance)
        return next((d for d in permitted if d.doc_id == doc_id), None)

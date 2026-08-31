"""
Inkwell — In-Memory Fake Firestore for Testing

A lightweight, dictionary-backed mock for google.cloud.firestore.Client
that supports collections, documents, subcollections, streams, filters,
order_by, limits, and increments without hitting any network or GCP API.
"""

from __future__ import annotations

from typing import Any


class FakeDocumentSnapshot:
    def __init__(self, doc_id: str, data: dict[str, Any] | None, exists: bool = True):
        self.id = doc_id
        self._data = dict(data) if data else {}
        self.exists = exists

    def to_dict(self) -> dict[str, Any]:
        return dict(self._data)


class FakeDocumentReference:
    def __init__(self, doc_id: str, collection: FakeCollectionReference):
        self.id = doc_id
        self._collection = collection
        self._subcollections: dict[str, FakeCollectionReference] = {}

    def get(self) -> FakeDocumentSnapshot:
        data = self._collection._docs.get(self.id)
        exists = self.id in self._collection._docs
        return FakeDocumentSnapshot(self.id, data, exists=exists)

    def set(self, data: dict[str, Any], merge: bool = False) -> None:
        if merge and self.id in self._collection._docs:
            self._collection._docs[self.id].update(data)
        else:
            self._collection._docs[self.id] = dict(data)

    def update(self, data: dict[str, Any]) -> None:
        if self.id not in self._collection._docs:
            self._collection._docs[self.id] = {}
        for k, v in data.items():
            # Handle firestore.Increment
            if hasattr(v, "value"):  # simple increment simulation
                cur = self._collection._docs[self.id].get(k, 0)
                self._collection._docs[self.id][k] = cur + getattr(v, "value", 1)
            else:
                self._collection._docs[self.id][k] = v

    def collection(self, name: str) -> FakeCollectionReference:
        if name not in self._subcollections:
            self._subcollections[name] = FakeCollectionReference(name, parent_doc=self)
        return self._subcollections[name]


class FakeQuery:
    def __init__(self, collection: FakeCollectionReference):
        self._collection = collection
        self._filters: list[tuple[str, str, Any]] = []
        self._order_field: str | None = None
        self._limit: int | None = None

    def where(self, field: str, op: str, value: Any) -> FakeQuery:
        q = FakeQuery(self._collection)
        q._filters = list(self._filters) + [(field, op, value)]
        q._order_field = self._order_field
        q._limit = self._limit
        return q

    def order_by(self, field: str) -> FakeQuery:
        q = FakeQuery(self._collection)
        q._filters = list(self._filters)
        q._order_field = field
        q._limit = self._limit
        return q

    def limit(self, count: int) -> FakeQuery:
        q = FakeQuery(self._collection)
        q._filters = list(self._filters)
        q._order_field = self._order_field
        q._limit = count
        return q

    def stream(self):
        docs = []
        for doc_id, data in self._collection._docs.items():
            match = True
            for field, op, val in self._filters:
                doc_val = data.get(field)
                if op == "==" and doc_val != val:
                    match = False
                elif op == "in" and doc_val not in val:
                    match = False
            if match:
                docs.append(FakeDocumentSnapshot(doc_id, data))

        if self._order_field:
            docs.sort(key=lambda d: str(d._data.get(self._order_field, "")))

        if self._limit is not None:
            docs = docs[:self._limit]

        for d in docs:
            yield d

    def get(self):
        return list(self.stream())


class FakeCollectionReference:
    def __init__(self, name: str, parent_doc: FakeDocumentReference | None = None):
        self.name = name
        self.parent = parent_doc
        self._docs: dict[str, dict[str, Any]] = {}
        self._doc_refs: dict[str, FakeDocumentReference] = {}

    def document(self, doc_id: str | None = None) -> FakeDocumentReference:
        if not doc_id:
            import uuid
            doc_id = uuid.uuid4().hex[:12]
        if doc_id not in self._doc_refs:
            self._doc_refs[doc_id] = FakeDocumentReference(doc_id, self)
        return self._doc_refs[doc_id]

    def add(self, data: dict[str, Any]) -> tuple[Any, FakeDocumentReference]:
        import uuid
        doc_id = uuid.uuid4().hex[:12]
        ref = self.document(doc_id)
        ref.set(data)
        return None, ref

    def where(self, field: str, op: str, value: Any) -> FakeQuery:
        return FakeQuery(self).where(field, op, value)

    def order_by(self, field: str) -> FakeQuery:
        return FakeQuery(self).order_by(field)

    def limit(self, count: int) -> FakeQuery:
        return FakeQuery(self).limit(count)

    def stream(self):
        return FakeQuery(self).stream()

    def get(self):
        return list(self.stream())


class FakeFirestoreClient:
    def __init__(self):
        self._collections: dict[str, FakeCollectionReference] = {}

    def collection(self, name: str) -> FakeCollectionReference:
        if name not in self._collections:
            self._collections[name] = FakeCollectionReference(name)
        return self._collections[name]

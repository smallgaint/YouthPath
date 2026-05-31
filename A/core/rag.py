from __future__ import annotations

from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings


PERSIST_DIRECTORY = "./chroma_data"
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"

_embedding_model: HuggingFaceEmbeddings | None = None
_collections: dict[str, Chroma] = {}


def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embedding_model


def get_collection(name: str) -> Chroma:
    if name not in _collections:
        _collections[name] = Chroma(
            collection_name=name,
            embedding_function=get_embedding_model(),
            persist_directory=PERSIST_DIRECTORY,
        )
    return _collections[name]


def index_documents(collection_name: str, docs: list[Document | dict[str, Any]]) -> None:
    collection = get_collection(collection_name)
    documents = [_coerce_document(doc) for doc in docs]
    if not documents:
        return

    ids = [str(doc.metadata.get("chunk_id") or doc.metadata.get("policy_id") or i) for i, doc in enumerate(documents)]
    try:
        collection.delete(ids=ids)
    except Exception:
        pass
    collection.add_documents(documents=documents, ids=ids)


def search(
    collection_name: str,
    query: str,
    k: int = 5,
    filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    collection = get_collection(collection_name)
    results = collection.similarity_search_with_score(query, k=k, filter=filter)
    return [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
            "score": score,
        }
        for doc, score in results
    ]


def _coerce_document(doc: Document | dict[str, Any]) -> Document:
    if isinstance(doc, Document):
        return doc
    return Document(
        page_content=str(doc.get("page_content") or doc.get("content") or ""),
        metadata=dict(doc.get("metadata") or {}),
    )

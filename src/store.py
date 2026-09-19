from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb  # noqa: F401

            client = chromadb.Client()
            # Lấy hoặc tạo collection mới
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Tạo record chuẩn từ một Document."""
        # Nhúng (embed) nội dung của document
        embedding = self._embedding_fn(doc.content)
        return {
            "id": getattr(doc, "id", str(self._next_index)),
            "content": doc.content,
            "metadata": getattr(doc, "metadata", {}) or {},
            "embedding": embedding,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Lõi tìm kiếm in-memory trên danh sách các records được cung cấp."""
        if not records:
            return []

        query_embedding = self._embedding_fn(query)

        scored_records = []
        for record in records:
            # Vector đã chuẩn hóa, nên dot product chính là cosine similarity
            score = _dot(query_embedding, record["embedding"])

            # Copy record để gắn thêm score mà không làm biến đổi dữ liệu gốc trong store
            rec_with_score = record.copy()
            rec_with_score["score"] = score
            scored_records.append(rec_with_score)

        # Sắp xếp giảm dần theo điểm số (score)
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        if self._use_chroma and self._collection:
            ids = [getattr(doc, "id", f"doc_{self._next_index + i}") for i, doc in enumerate(docs)]
            documents = [doc.content for doc in docs]
            metadatas = [getattr(doc, "metadata", {}) or {} for doc in docs]
            embeddings = [self._embedding_fn(doc.content) for doc in docs]

            self._collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
            self._next_index += len(docs)
        else:
            # In-memory fallback
            for doc in docs:
                record = self._make_record(doc)
                self._store.append(record)
                self._next_index += 1

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection:
            query_emb = self._embedding_fn(query)
            results = self._collection.query(query_embeddings=[query_emb], n_results=top_k)

            # Format trả về giống cấu trúc của in-memory để tương thích với output
            formatted_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": results["distances"][0][i] if "distances" in results else 0.0
                    })
            return formatted_results

        # In-memory search
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k)

        if self._use_chroma and self._collection:
            query_emb = self._embedding_fn(query)
            # ChromaDB hỗ trợ lọc metadata qua thuộc tính `where`
            results = self._collection.query(
                query_embeddings=[query_emb],
                n_results=top_k,
                where=metadata_filter
            )

            formatted_results = []
            if results["ids"] and len(results["ids"]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "score": results["distances"][0][i] if "distances" in results else 0.0
                    })
            return formatted_results

        # Pre-filtering cho in-memory store
        filtered_records = []
        for record in self._store:
            meta = record.get("metadata", {})
            # Kiểm tra xem record này có chứa tất cả điều kiện từ metadata_filter không
            if all(meta.get(k) == v for k, v in metadata_filter.items()):
                filtered_records.append(record)

        # Tính toán độ tương tự và xếp hạng trên tập đã lọc
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        initial_size = self.get_collection_size()

        if self._use_chroma and self._collection:
            # Xóa các dòng có metadata doc_id trùng khớp (hoặc có id bằng doc_id)
            self._collection.delete(where={"doc_id": doc_id})
            return self.get_collection_size() < initial_size

        # In-memory delete: Lọc và chỉ giữ lại những record KHÔNG có doc_id này
        new_store = []
        for record in self._store:
            meta = record.get("metadata", {})
            # Xem xét cả trường hợp người dùng truyền doc_id vào thẳng metadata
            # hoặc định danh thông qua trường "id" của chunk
            if meta.get("doc_id") == doc_id or record.get("id") == doc_id:
                continue
            new_store.append(record)

        self._store = new_store

        return len(self._store) < initial_size

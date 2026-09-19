from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    SYSTEM_PROMPT = (
        "Bạn là trợ lý trả lời câu hỏi dựa trên tài liệu được cung cấp. "
        "Chỉ sử dụng thông tin trong phần NGỮ CẢNH bên dưới để trả lời. "
        "Nếu ngữ cảnh không chứa thông tin cần thiết, hãy nói rõ là không tìm thấy "
        "trong tài liệu thay vì suy đoán."
    )

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def _build_context(self, results: list[dict]) -> str:
        """Ghép các chunk truy xuất được thành một khối ngữ cảnh có dán nhãn."""
        if not results:
            return "(Không tìm thấy tài liệu liên quan.)"

        blocks = []
        for i, record in enumerate(results, start=1):
            content = record.get("content", "")
            blocks.append(f"[Tài liệu {i}]\n{content}")
        return "\n\n".join(blocks)

    def answer(self, question: str, top_k: int = 3) -> str:
        # 1. Truy xuất top-k chunk liên quan nhất từ vector store
        results = self.store.search(question, top_k=top_k)

        # 2. Dựng prompt 3 phần: system prompt + context block + câu hỏi
        context = self._build_context(results)
        prompt = (
            f"{self.SYSTEM_PROMPT}\n\n"
            f"NGỮ CẢNH:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            f"TRẢ LỜI:"
        )

        # 3. Gọi LLM và trả về câu trả lời
        return self.llm_fn(prompt)

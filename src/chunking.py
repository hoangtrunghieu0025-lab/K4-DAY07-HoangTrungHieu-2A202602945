from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
            
        # Tách câu dựa trên dấu phân cách, giữ lại dấu chấm/than/hỏi ở cuối câu
        # regex lookbehind: (?<=\.) \s* bắt khoảng trắng sau dấu câu
        raw_sentences = re.split(r'(?<=\.) |(?<=\!) |(?<=\?) |(?<=\.)\n', text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        
        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            chunk_sentences = sentences[i : i + self.max_sentences_per_chunk]
            chunks.append(" ".join(chunk_sentences))
            
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if len(current_text) <= self.chunk_size:
            return [current_text]
            
        if not remaining_separators:
            # Base case: Không còn separator nào, bắt buộc phải cắt theo fixed-size
            return [current_text[i : i + self.chunk_size] for i in range(0, len(current_text), self.chunk_size)]
            
        sep = remaining_separators[0]
        # Nếu separator là chuỗi rỗng "", cắt theo từng ký tự
        splits = list(current_text) if sep == "" else current_text.split(sep)
        
        good_chunks: list[str] = []
        current_chunk_pieces: list[str] = []
        current_len = 0
        sep_len = len(sep)
        
        for piece in splits:
            if len(piece) > self.chunk_size:
                # Nếu mảng đang chứa đoạn hợp lệ, lưu lại trước
                if current_chunk_pieces:
                    good_chunks.append(sep.join(current_chunk_pieces))
                    current_chunk_pieces = []
                    current_len = 0
                
                # Gọi đệ quy cho đoạn quá dài với các separators ưu tiên thấp hơn
                sub_chunks = self._split(piece, remaining_separators[1:])
                good_chunks.extend(sub_chunks)
            else:
                # Tính độ dài nếu thêm đoạn này vào chunk hiện tại
                new_len = current_len + len(piece) + (sep_len if current_chunk_pieces else 0)
                
                if new_len > self.chunk_size:
                    good_chunks.append(sep.join(current_chunk_pieces))
                    current_chunk_pieces = [piece]
                    current_len = len(piece)
                else:
                    current_chunk_pieces.append(piece)
                    current_len += len(piece) + (sep_len if current_chunk_pieces and len(current_chunk_pieces) > 1 else 0)
                    
        # Lưu đoạn cuối cùng còn sót lại
        if current_chunk_pieces:
            good_chunks.append(sep.join(current_chunk_pieces))
            
        return good_chunks


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
        
    return dot_product / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        fixed_chunker = FixedSizeChunker(chunk_size=chunk_size, overlap=20)
        sentence_chunker = SentenceChunker(max_sentences_per_chunk=3)
        recursive_chunker = RecursiveChunker(chunk_size=chunk_size)

        fixed_chunks = fixed_chunker.chunk(text)
        sentence_chunks = sentence_chunker.chunk(text)
        recursive_chunks = recursive_chunker.chunk(text)

        def _stats(chunks: list[str]) -> dict:
            # Chặn chia cho 0 khi text rỗng
            avg_length = sum(len(c) for c in chunks) / len(chunks) if chunks else 0.0
            return {
                "count": len(chunks),
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return {
            "fixed_size": _stats(fixed_chunks),
            "by_sentences": _stats(sentence_chunks),
            "recursive": _stats(recursive_chunks),
        }
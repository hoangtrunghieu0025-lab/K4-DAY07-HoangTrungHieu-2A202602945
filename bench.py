"""
Harness đo retrieval cho Lab 7 — K4-L3A (chủ đề: học bổng).

Dùng chung cho cả nhóm. Mỗi thành viên CHỈ đổi đúng một dòng: `CHUNKER` ở
mục CẤU HÌNH bên dưới. Mọi thứ khác giữ nguyên để so sánh giữa các chiến
lược mới công bằng.

Chạy:
    python bench.py
    python bench.py --top-k 5
    python bench.py --no-filter        # tắt metadata_filter để lấy số liệu A/B
"""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

from dotenv import load_dotenv

from src import (
    Document,
    EmbeddingStore,
    FixedSizeChunker,
    MockEmbedder,
    RecursiveChunker,
    SentenceChunker,
)

class HeadingChunker:
    """
    Cắt theo tiêu đề Markdown ATX; section dài thì hạ xuống RecursiveChunker và
    GẮN LẠI dòng tiêu đề vào đầu mỗi mảnh con.

    Dựng lại theo mô tả trong báo cáo cá nhân của Đinh Đức Thái để bảng so sánh
    của nhóm có số liệu kiểm chứng được. Không phải mã gốc của bạn ấy.
    """

    HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.M)

    def __init__(self, chunk_size: int = 320) -> None:
        self.chunk_size = chunk_size
        self.inner = RecursiveChunker(chunk_size=chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []
        cuts = [m.start() for m in self.HEADING_RE.finditer(text)]
        bounds = sorted(set([0] + cuts + [len(text)]))
        out: list[str] = []
        for a, b in zip(bounds, bounds[1:]):
            section = text[a:b].strip()
            if not section:
                continue
            if len(section) <= self.chunk_size:
                out.append(section)
                continue
            lines = section.split("\n", 1)
            heading = lines[0] if self.HEADING_RE.match(lines[0] + "\n") else ""
            body = lines[1] if len(lines) > 1 else section
            room = max(40, self.chunk_size - len(heading) - 1)
            for part in RecursiveChunker(chunk_size=room).chunk(body.strip()):
                out.append(f"{heading}\n{part}" if heading else part)
        return out


class ParagraphChunker:
    """
    Tách tại dòng trắng, gom các đoạn liền kề tới giới hạn, đoạn quá dài thì hạ
    xuống RecursiveChunker.

    Dựng lại theo mô tả trong báo cáo cá nhân của Đàm Quang Sơn để bảng so sánh
    của nhóm có số liệu kiểm chứng được. Không phải mã gốc của bạn ấy.
    """

    def __init__(self, chunk_size: int = 360) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        out: list[str] = []
        buf: list[str] = []
        size = 0
        for para in paras:
            if len(para) > self.chunk_size:
                if buf:
                    out.append("\n\n".join(buf)); buf, size = [], 0
                out.extend(RecursiveChunker(chunk_size=self.chunk_size).chunk(para))
                continue
            add = len(para) + (2 if buf else 0)
            if size + add > self.chunk_size and buf:
                out.append("\n\n".join(buf)); buf, size = [para], len(para)
            else:
                buf.append(para); size += add
        if buf:
            out.append("\n\n".join(buf))
        return out


class MetadataEnrichedChunker:
    """
    Chunk bằng một chunker nền, rồi chèn tiền tố ngữ cảnh lấy từ metadata vào
    đầu MỖI chunk TRƯỚC KHI embed.

    Ý tưởng: chunk trần chỉ mang con số và câu chữ của đoạn đó, không mang
    thông tin "đoạn này thuộc tài liệu nào, dành cho ai". Với corpus gộp nhiều
    trường và nhiều đối tượng, đó chính là thông tin quyết định đúng/sai.

    Ví dụ một chunk sau khi chèn tiền tố:

        [Học bổng khuyến khích học tập UET | uet | student]
        | Chuẩn QH-2023 den QH-2025 | 3.600.000d/thang | ...

    Khác với `metadata_filter`: filter loại tài liệu sai đối tượng SAU khi
    embedding đã xong, còn cách này đưa thông tin đối tượng vào CHÍNH vector.
    Hai cách giải cùng một bài toán ở hai tầng khác nhau, và đo được cả hai.
    """

    PREFIX_FIELDS = ("title", "institution", "audience")

    def __init__(self, base_chunker=None, prefix_fields: tuple[str, ...] | None = None) -> None:
        self.base_chunker = base_chunker or RecursiveChunker(chunk_size=280)
        self.prefix_fields = prefix_fields or self.PREFIX_FIELDS

    def _prefix(self, metadata: dict[str, str]) -> str:
        parts = [metadata[f] for f in self.prefix_fields if metadata.get(f)]
        return f"[{' | '.join(parts)}]" if parts else ""

    def chunk(self, text: str) -> list[str]:
        """Không có metadata thì hành xử đúng như chunker nền."""
        return self.base_chunker.chunk(text)

    def chunk_with_metadata(self, text: str, metadata: dict[str, str]) -> list[str]:
        prefix = self._prefix(metadata)
        chunks = self.base_chunker.chunk(text)
        if not prefix:
            return chunks
        return [f"{prefix}\n{c}" for c in chunks]


# ===========================================================================
# CẤU HÌNH — mỗi thành viên đổi ĐÚNG MỘT DÒNG ở đây
# ===========================================================================

# Chiến lược của bạn. Bỏ comment đúng một dòng:
# CHUNKER = FixedSizeChunker(chunk_size=500, overlap=50)
# CHUNKER = SentenceChunker(max_sentences_per_chunk=3)
# CHUNKER = RecursiveChunker(chunk_size=280)
# CHUNKER = HeadingChunker(chunk_size=500)            # R3 tự viết, import thêm
CHUNKER = MetadataEnrichedChunker(RecursiveChunker(chunk_size=280))

STRATEGY_NAME = "metadata_enriched(recursive_280)"  # đổi cho khớp CHUNKER ở trên

# ===========================================================================
# Phần dưới đây KHÔNG đổi
# ===========================================================================

CORPUS_DIR = Path("data/hoc-bong")

# 5 benchmark query của nhóm (R2 chủ trì). `filter` là metadata_filter áp dụng
# cho câu đó; None nghĩa là không lọc.
QUERIES: list[dict] = [
    {
        "id": "Q1",
        "question": "Học bổng President's Excellence của VinUni chi trả những gì?",
        "filter": None,
    },
    {
        "id": "Q2",
        "question": "Sinh viên VinUni cần GPA tối thiểu bao nhiêu để duy trì học bổng 100%?",
        "filter": None,
    },
    {
        "id": "Q3",
        "question": "Ở UET, học bổng loại Giỏi cho khóa QH-2023 đến QH-2025 là bao nhiêu mỗi tháng?",
        "filter": None,
    },
    {
        "id": "Q4",
        "question": "Sinh viên RMIT Việt Nam đang học cần bao nhiêu tín chỉ và GPA để xin học bổng thành tích 2026?",
        "filter": None,
    },
    {
        # Câu cần metadata_filter. Corpus có hai tài liệu UEH cùng nói về "mức hỗ
        # trợ tài chính" nhưng khác đối tượng và khác đáp án:
        #   - ueh-learning-support-scholarship (student): 100% học phí TB 15 tín chỉ
        #   - ueh-faculty-support (faculty)             : 500/300/150 triệu, +20 triệu/tháng
        # Không lọc thì tài liệu giảng viên chiếm top-1.
        "id": "Q5",
        "question": "Ở UEH, mức hỗ trợ tài chính tối đa cho một học kỳ là bao nhiêu?",
        "filter": {"audience": "student"},
    },
]

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    """Tách frontmatter YAML thành metadata dict, phần còn lại thành content."""
    raw = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw.strip()

    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    # Chỉ phần thân mới là content — không để khối YAML lọt vào embedding
    return metadata, raw[match.end():].strip()


def build_documents(corpus_dir: Path, chunker) -> list[Document]:
    """Đọc corpus, chunk phần thân, mỗi chunk thành một Document."""
    docs: list[Document] = []
    for path in sorted(corpus_dir.glob("*.md")):
        metadata, content = parse_markdown(path)
        # Chunker nào biết dùng metadata thì truyền xuống (MetadataEnrichedChunker);
        # còn lại giữ nguyên giao diện chunk(text) như các chunker trong src/
        if hasattr(chunker, "chunk_with_metadata"):
            chunks = chunker.chunk_with_metadata(content, metadata)
        else:
            chunks = chunker.chunk(content)
        for i, chunk in enumerate(chunks):
            docs.append(
                Document(
                    id=f"{path.stem}#{i}",
                    content=chunk,
                    # Trải frontmatter vào MỌI chunk, nếu không search_with_filter
                    # sẽ không có gì để lọc
                    metadata={**metadata, "doc_id": path.stem, "chunk_index": i},
                )
            )
    return docs


def make_embedder():
    """Chọn backend embedding theo .env; mặc định là MockEmbedder."""
    load_dotenv(dotenv_path=Path(".env"), override=False)
    provider = (os.getenv("EMBEDDING_PROVIDER") or "mock").strip().lower()

    if provider == "local":
        try:
            from src import LocalEmbedder

            return LocalEmbedder()
        except Exception as error:
            print(f"[canh bao] Khong dung duoc LocalEmbedder ({error}); quay ve mock.")
    elif provider == "openai":
        try:
            from src import OpenAIEmbedder

            return OpenAIEmbedder()
        except Exception as error:
            print(f"[canh bao] Khong dung duoc OpenAIEmbedder ({error}); quay ve mock.")
    elif provider == "gemini":
        try:
            from src import GeminiEmbedder

            return GeminiEmbedder()
        except Exception as error:
            print(f"[canh bao] Khong dung duoc GeminiEmbedder ({error}); quay ve mock.")

    return MockEmbedder()


def run(top_k: int, use_filter: bool) -> None:
    embedder = make_embedder()
    backend = getattr(embedder, "_backend_name", type(embedder).__name__)

    docs = build_documents(CORPUS_DIR, CHUNKER)
    if not docs:
        print(f"Khong doc duoc tai lieu nao trong {CORPUS_DIR}")
        return

    store = EmbeddingStore(collection_name="bench", embedding_fn=embedder)
    store.add_documents(docs)

    lengths = [len(d.content) for d in docs]
    print("=" * 78)
    print(f"Chien luoc      : {STRATEGY_NAME}")
    print(f"Embedding backend: {backend}")
    print(f"Corpus          : {CORPUS_DIR}")
    print(f"So chunk da nap : {store.get_collection_size()}")
    print(f"Do dai chunk    : min={min(lengths)} / tb={sum(lengths) // len(lengths)} / max={max(lengths)}")
    print(f"metadata_filter : {'BAT' if use_filter else 'TAT (che do A/B)'}")
    print("=" * 78)

    for q in QUERIES:
        metadata_filter = q["filter"] if use_filter else None
        results = store.search_with_filter(
            q["question"], top_k=top_k, metadata_filter=metadata_filter
        )

        print(f"\n[{q['id']}] {q['question']}")
        if metadata_filter:
            print(f"      filter = {metadata_filter}")
        if not results:
            print("      (khong co ket qua)")
            continue

        for rank, r in enumerate(results, start=1):
            meta = r.get("metadata", {})
            preview = " ".join(r.get("content", "").split())[:110]
            print(
                f"   {rank}. score={r.get('score', 0.0):+.4f}  "
                f"doc_id={meta.get('doc_id', '?')}  "
                f"audience={meta.get('audience', '?')}"
            )
            print(f"      {preview}...")


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark retrieval cho corpus hoc bong.")
    parser.add_argument("--top-k", type=int, default=3, help="So ket qua tra ve moi query (mac dinh 3)")
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Tat metadata_filter de lay so lieu A/B cho bao cao",
    )
    args = parser.parse_args()

    run(top_k=args.top_k, use_filter=not args.no_filter)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Kiểm tra corpus theo checklist mục 6 của docs/DATA_COLLECTION.md (Checkpoint 2).

Chạy:
    python scripts/check_corpus.py
    python scripts/check_corpus.py --dir data/hoc-bong

Thoát với mã 0 nếu mọi kiểm tra đạt, 1 nếu có lỗi.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

REQUIRED_FIELDS = ["doc_id", "title", "source_url", "retrieved_at", "document_version", "audience"]
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)


def parse_frontmatter(path: Path) -> dict[str, str]:
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.split("#")[0].strip().strip('"').strip("'")
    return fields


def read_csv_column(path: Path, column: str) -> list[str] | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or column not in rows[0]:
        return []
    return [row[column].strip() for row in rows if row.get(column, "").strip()]


def check(corpus_dir: Path) -> tuple[bool, list[str]]:
    problems: list[str] = []
    md_files = sorted(corpus_dir.glob("*.md"))

    if not md_files:
        return False, [f"Khong tim thay file .md nao trong {corpus_dir}"]

    if not 5 <= len(md_files) <= 10:
        problems.append(f"Co {len(md_files)} tai lieu, yeu cau 5-10")

    doc_ids: list[str] = []
    audiences: set[str] = set()

    for path in md_files:
        fields = parse_frontmatter(path)
        if not fields:
            problems.append(f"{path.name}: khong doc duoc front matter")
            continue

        missing = [key for key in REQUIRED_FIELDS if key not in fields]
        if missing:
            problems.append(f"{path.name}: thieu metadata {', '.join(missing)}")

        doc_id = fields.get("doc_id", "")
        if doc_id and doc_id != path.stem:
            problems.append(f"{path.name}: doc_id '{doc_id}' khong trung ten file")
        if doc_id in doc_ids:
            problems.append(f"{path.name}: doc_id '{doc_id}' bi trung")
        if doc_id:
            doc_ids.append(doc_id)

        if fields.get("audience"):
            audiences.add(fields["audience"])

    if len(audiences) < 2:
        problems.append(
            f"audience chi co {len(audiences)} gia tri ({', '.join(sorted(audiences)) or 'khong co'}); "
            "can it nhat 2 thi metadata_filter moi co gi de loc"
        )

    sources_ids = read_csv_column(corpus_dir / "sources.csv", "doc_id")
    if sources_ids is None:
        problems.append("Thieu sources.csv")
    elif sorted(sources_ids) != sorted(doc_ids):
        only_csv = sorted(set(sources_ids) - set(doc_ids))
        only_md = sorted(set(doc_ids) - set(sources_ids))
        detail = []
        if only_csv:
            detail.append(f"chi co trong csv: {', '.join(only_csv)}")
        if only_md:
            detail.append(f"chi co trong .md: {', '.join(only_md)}")
        problems.append("sources.csv khong khop 1-1 voi cac file .md" + (f" ({'; '.join(detail)})" if detail else ""))

    urls_ids = read_csv_column(corpus_dir / "urls.csv", "doc_id")
    if urls_ids is None:
        problems.append("Thieu urls.csv")
    elif urls_ids and sorted(urls_ids) != sorted(doc_ids):
        only_md = sorted(set(doc_ids) - set(urls_ids))
        problems.append(
            "urls.csv khong khop 1-1 voi cac file .md"
            + (f" (thieu trong urls.csv: {', '.join(only_md)})" if only_md else "")
        )

    return not problems, problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Kiem tra corpus theo Checkpoint 2.")
    parser.add_argument("--dir", type=Path, default=Path("data/hoc-bong"), help="Thu muc corpus")
    args = parser.parse_args()

    ok, problems = check(args.dir)
    md_count = len(sorted(args.dir.glob("*.md")))
    audiences = sorted({parse_frontmatter(p).get("audience", "") for p in args.dir.glob("*.md")} - {""})

    if ok:
        print(
            f"OK: {md_count} Markdown files; urls.csv and sources.csv match; "
            f"audiences: {', '.join(audiences)}"
        )
        return 0

    print(f"FAIL: {md_count} Markdown files in {args.dir}", file=sys.stderr)
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

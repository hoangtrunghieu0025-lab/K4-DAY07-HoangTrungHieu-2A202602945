# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Hoàng Trung Hiếu]
**Nhóm:** G15
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Nó có nghĩa là hai vector nhúng (embeddings) đang hướng về cùng một phía trong không gian vector đa chiều, cho thấy hai đoạn văn bản có ngữ nghĩa, chủ đề hoặc ý định rất tương đồng nhau, bất kể việc chúng có sử dụng chung từ vựng hay không.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Mô hình ngôn ngữ lớn cần lượng dữ liệu khổng lồ để huấn luyện."
- Câu B: "Training các LLMs đòi hỏi một tập dataset kích thước rất lớn."
- Tại sao tương đồng: Cùng diễn đạt một ý tưởng về yêu cầu dữ liệu cho mô hình AI, dù sử dụng từ vựng và ngôn ngữ (Anh/Việt) có phần khác biệt. Các mô hình như Sentence-Transformers ánh xạ chúng vào cùng một không gian ngữ nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Quả táo này ăn rất ngọt và giòn."
- Câu B: "Apple vừa ra mắt dòng điện thoại mới với chip AI mạnh mẽ."
- Tại sao khác: Dù cùng chứa từ "táo/Apple", nhưng một câu nói về trái cây (ngữ cảnh ẩm thực/nông nghiệp), câu còn lại nói về công nghệ. Vector của chúng sẽ nằm ở hai cụm (clusters) hoàn toàn xa nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Vì khoảng cách Euclid bị ảnh hưởng rất mạnh bởi độ dài của vector (vốn phụ thuộc vào độ dài của câu văn), trong khi Cosine Similarity chỉ đo góc giữa hai vector, giúp đánh giá chính xác sự tương đồng về mặt ý nghĩa bất kể một tài liệu dài hay ngắn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*
> Gọi $L$ là độ dài tài liệu, $C$ là kích thước chunk, $O$ là độ chồng chéo.
> Bước nhảy (stride) $S = C - O = 500 - 50 = 450$.
> Số lượng chunk $N = \lceil rac{L - O}{S} 
ceil = \lceil rac{10000 - 50}{450} 
ceil = \lceil rac{9950}{450} 
ceil = \lceil 22.11 
ceil$.
>
> *Đáp án:* **23 chunks**. Đã kiểm lại bằng `FixedSizeChunker(chunk_size=500, overlap=50).chunk('a'*10000)` trong repo, kết quả trùng khớp: 23.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Nếu $O = 100$, bước nhảy giảm xuống 400. Số chunk sẽ là $\lceil rac{9900}{400} 
ceil = 25$ chunks (tăng lên; đã kiểm lại bằng code, khớp). Ta muốn độ chồng chéo nhiều hơn để đảm bảo không bị đứt gãy ngữ cảnh (context loss) ở ranh giới giữa các chunk, giúp các câu hoặc thực thể (entities) nằm ở mép đoạn cắt vẫn giữ được trọn vẹn ý nghĩa khi đưa vào mô hình LLM.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng `re.split` với **lookbehind** cho từng dấu phân cách theo đúng spec: `r'(?<=\.) |(?<=\!) |(?<=\?) |(?<=\.)
'`. Lookbehind là điểm mấu chốt — nếu tách bằng `[.!?]\s+` thì dấu câu bị nuốt mất và mọi chunk thành câu cụt; lookbehind cắt ở vị trí *sau* dấu câu nên dấu câu được giữ lại trong câu trước. Sau đó `strip()` từng câu, bỏ câu rỗng, rồi gom `max_sentences_per_chunk` câu thành một chunk bằng `" ".join()`; text rỗng trả `[]`.
>
> **Edge case chưa xử lý (đã biết):** chữ viết tắt (`TS.`, `v.v.`) và số thập phân (`2.5`, `3.6`) sẽ bị cắt sai vì regex chỉ nhìn ký tự ngay trước dấu cách. Corpus học bổng của nhóm có đầy ngưỡng dạng `2.5/4.0` và `3.6` nên lỗi này sẽ xuất hiện thật ở bước benchmark — muốn xử lý đúng cần thêm danh sách viết tắt và một lookahead chặn chữ số.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử chia văn bản bằng các separator từ "to" đến "nhỏ" (`

` → `
` → `. ` → `" "` → `""`) để giữ ranh giới ngữ nghĩa lâu nhất có thể. Thuật toán có **hai chiều**: *đệ quy xuống sâu* (mảnh nào vẫn dài hơn `chunk_size` thì gọi lại `_split` với danh sách separator còn lại) và *gom lên* (các mảnh nhỏ liền kề được nối lại bằng `sep.join()` cho tới sát `chunk_size`, tránh sinh ra hàng trăm chunk vụn 5-10 ký tự làm hỏng retrieval).
>
> **Ba base case:** (1) `len(current_text) <= chunk_size` → trả thẳng `[current_text]`; (2) `remaining_separators` rỗng → cắt cứng theo `chunk_size` bằng slicing; (3) separator là chuỗi rỗng `""` → cắt theo từng ký tự. Trường hợp (2) là cái mà test `test_empty_separators_falls_back_gracefully` kiểm, vì nó truyền thẳng `separators=[]`. Lớp này **không có tham số overlap** — overlap chỉ tồn tại ở `FixedSizeChunker`.

**Chiến lược riêng của tôi để benchmark — `metadata_enriched(recursive_280)`:**

`MetadataEnrichedChunker` trong [`bench.py`](../bench.py) không phải một cách cắt mới. Nó **bọc** một chunker nền (`RecursiveChunker(chunk_size=280)`) rồi chèn một tiền tố dựng từ front matter vào đầu **mỗi** chunk, **trước khi embed**:

```python
class MetadataEnrichedChunker:
    PREFIX_FIELDS = ("title", "institution", "audience")

    def _prefix(self, metadata):
        parts = [metadata[f] for f in self.prefix_fields if metadata.get(f)]
        return f"[{' | '.join(parts)}]" if parts else ""

    def chunk_with_metadata(self, text, metadata):
        prefix = self._prefix(metadata)
        chunks = self.base_chunker.chunk(text)
        return [f"{prefix}
{c}" for c in chunks] if prefix else chunks
```

Để chunker nhận được metadata, `build_documents()` kiểm tra `hasattr(chunker, "chunk_with_metadata")` và truyền front matter xuống; chunker nào không có method đó vẫn dùng giao diện `chunk(text)` như các lớp trong `src/`, nên harness giữ nguyên cho cả nhóm.

**Lý do chọn.** Chunk trần chỉ mang con số và câu chữ của đoạn đó. Với corpus gộp 4 trường và 2 đối tượng, chunk như `| Chuẩn QH-2023 đến QH-2025 | 3.600.000đ/tháng | ... |` gần như không có nội dung ngữ nghĩa để embed — nó không nói mình thuộc trường nào, dành cho ai. Tiền tố bơm chính những thông tin đó vào vector.

**Giả thuyết muốn kiểm.** Nếu `audience` đã nằm trong text được embed thì retrieval có tự phân biệt được đối tượng, khiến `metadata_filter` thành thừa hay không? Kết quả đo ở mục 5: tiền tố nâng điểm từ 1/10 lên 5/10 nhưng **không** làm giảm tỷ lệ sai đối tượng — giả thuyết sai, và lý do được phân tích ở đó.

**Hạn chế đã biết.** Tiền tố chiếm chỗ trong mỗi chunk (độ dài trung bình tăng từ 167 lên 238 ký tự) nên với `chunk_size` nhỏ, phần nội dung thật còn lại ít đi. Ngoài ra tiền tố lặp y hệt nhau trên mọi chunk của cùng một tài liệu, nên nó không giúp phân biệt các đoạn **trong cùng** một tài liệu — đúng chỗ Q2 và Q5 vẫn hỏng.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Lưu trữ bằng **Python thuần**, không dùng NumPy: `self._store` là `list[dict]`, mỗi record gồm `id`, `content`, `metadata`, `embedding`. `_make_record()` dựng record chuẩn cho một `Document`; `add_documents()` embed từng document rồi append — **một `Document` = một record**, lớp store không tự chunk (việc chunking làm ở tầng ngoài).
>
> Khi `search`, hàm `_search_records()` embed query rồi tính `_dot(query_embedding, record["embedding"])` với từng record, sort giảm dần theo score và cắt `top_k`. **Không cần bước L2 normalization** vì vector do embedder trả về đã chuẩn hoá sẵn (`||v|| = 1`), nên dot product bằng đúng cosine similarity — đó cũng là lý do dùng `_dot` thay vì `compute_similarity`. Mỗi record được `.copy()` trước khi gắn `score` để không làm biến đổi dữ liệu gốc trong store.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> **Lọc trước (pre-filtering).** `search_with_filter()` duyệt `self._store`, giữ lại record thoả `all(meta.get(k) == v for k, v in metadata_filter.items())`, rồi mới gọi `_search_records()` trên tập con đó. Lọc trước rẻ hơn lọc sau vì chỉ phải tính dot product trên số record đã thu hẹp, và quan trọng hơn: lọc sau có thể trả về ít hơn `top_k` kết quả hợp lệ nếu các record bị loại đã chiếm hết top-k. Khi `metadata_filter` rỗng thì uỷ quyền thẳng cho `search()`.
>
> **Xoá thật, không dùng tombstone.** `delete_document()` dựng lại `self._store` chỉ với các record không khớp `doc_id` (so khớp cả `metadata["doc_id"]` lẫn `record["id"]`), rồi trả `True/False` bằng cách so sánh kích thước trước và sau. Tombstone không dùng được ở đây vì test `test_delete_reduces_collection_size` yêu cầu `get_collection_size()` phải **giảm** sau khi xoá — đánh dấu mà không xoá thì size không đổi.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Prompt chia làm 3 phần: `SYSTEM_PROMPT` định hình vai trò và ràng buộc "chỉ dùng thông tin trong NGỮ CẢNH"; khối **NGỮ CẢNH** chứa các chunk truy xuất được; và **CÂU HỎI** của người dùng ở cuối. Helper `_build_context()` ghép các chunk thành chuỗi có dán nhãn `[Tài liệu 1]`, `[Tài liệu 2]`... ngăn cách bằng dòng trống, để LLM phân biệt được ranh giới giữa các nguồn.
>
> Chống ảo giác (hallucination) bằng hai lớp: system prompt yêu cầu nói rõ "không tìm thấy trong tài liệu" thay vì suy đoán, và khi `store.search()` trả về rỗng thì `_build_context()` trả chuỗi `"(Không tìm thấy tài liệu liên quan.)"` thay vì để khối ngữ cảnh trống. Cuối cùng `answer()` gọi `self.llm_fn(prompt)` với prompt đã ghép và trả thẳng kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v

============================= test session starts =============================
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]
============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Đo bằng `compute_similarity()` với `LocalEmbedder` (`paraphrase-multilingual-MiniLM-L12-v2`). Ngưỡng quy ước: cao >= 0,6 / thấp < 0,4.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên phải đạt GPA tích lũy tối thiểu 3,4/4,0 để được xét học bổng. | Điều kiện nộp hồ sơ là điểm trung bình tích lũy từ 3,4 trên thang 4,0 trở lên. | cao | **+0,5955** | Sai (chỉ trung bình) |
| 2 | Trường hỗ trợ sinh viên 3.400.000 đồng mỗi tháng theo diện học bổng khuyến khích học tập. | Trường hỗ trợ giảng viên thêm 20 triệu đồng mỗi tháng theo chính sách đãi ngộ. | thấp | **+0,5413** | Sai (cao hơn dự đoán) |
| 3 | Học bổng chi trả 50% học phí toàn chương trình. | The scholarship covers 50% of the total program tuition fee. | cao | **+0,9570** | Đúng |
| 4 | Hạn nộp hồ sơ học bổng là 17:00 ngày 27/07/2026. | Thư viện mở cửa từ 8h00 đến 19h00 các ngày trong tuần. | thấp | **+0,2918** | Đúng |
| 5 | Học bổng toàn phần yêu cầu GPA tích lũy đạt ít nhất **3,2**. | Hỗ trợ tài chính theo nhu cầu yêu cầu GPA tích lũy đạt ít nhất **2,0**. | thấp | **+0,7338** | Sai (cao hẳn) |

Dự đoán đúng 2/5.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là **cặp 5**: hai câu nói hai ngưỡng GPA khác nhau cho hai loại hỗ trợ khác nhau (3,2 và 2,0) lại đạt 0,7338 — **cao hơn hẳn cặp 1 (0,5955)**, vốn là hai cách diễn đạt của cùng một ý. Xếp theo điểm: bản dịch Anh–Việt (0,96) > hai câu mâu thuẫn về số (0,73) > diễn đạt lại cùng ý (0,60) > sai đối tượng (0,54) > không liên quan (0,29).
>
> Điều này cho thấy embedding mã hoá **chủ đề và khuôn câu**, không mã hoá **giá trị số**. Hai câu cùng khuôn "loại hỗ trợ X yêu cầu GPA ít nhất Y" gần như trùng nhau trong không gian vector dù Y khác nhau — con số chỉ chiếm vài token, gần như không dịch chuyển vector. Cặp 2 nói cùng điều đó ở trục khác: "hỗ trợ ... mỗi tháng" cho sinh viên và cho giảng viên đạt 0,54 dù đáp án hoàn toàn khác nhau — đúng lý do nhóm phải dùng `metadata_filter={"audience": "student"}` thay vì tin vào similarity.
>
> Hệ quả trực tiếp cho corpus học bổng: mọi câu hỏi dạng "cần GPA bao nhiêu" hay "được bao nhiêu tiền" đều rủi ro, vì retrieval không phân biệt được chunk chứa **đúng** con số với chunk chỉ chứa **một** con số cùng dạng.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

Chiến lược của tôi: **`metadata_enriched(recursive_280)`** — `MetadataEnrichedChunker` trong [`bench.py`](../bench.py), bọc `RecursiveChunker(chunk_size=280)` rồi chèn tiền tố `[title | institution | audience]` vào đầu **mỗi** chunk **trước khi embed**. Embedder: `paraphrase-multilingual-MiniLM-L12-v2`. Corpus: `data/hoc-bong` (7 tài liệu → **45 chunk**, trung bình 238 ký tự). Output đầy đủ: `ket_qua_benchmark.txt`.

Ví dụ một chunk sau khi chèn tiền tố:

```
[Học bổng khuyến khích học tập UET học kỳ I năm 2025–2026 | uet | student]
| Chuẩn QH-2023 đến QH-2025 | 3.600.000đ/tháng | 3.500.000đ/tháng | 3.400.000đ/tháng |
```

Lý do chọn: chunk trần chỉ mang con số và câu chữ của đoạn đó, không mang thông tin "đoạn này thuộc tài liệu nào, của trường nào, dành cho ai". Với corpus gộp 4 trường và 2 đối tượng, đó chính là thông tin quyết định đúng/sai.

> **Lưu ý:** câu 3 là câu đã chốt (câu cần `metadata_filter`). Câu 1, 2, 4, 5 hiện là bản nháp trong harness — sẽ thay bằng bộ câu chính thức của R2 rồi chạy lại.

Cách chấm: kiểm ở **mức nội dung**, tức mốc đặc trưng của đáp án (`3,4`/`96` cho Q1, `3,2` cho Q2, `đ/tháng` cho Q3 và Q5, `khó khăn` cho Q4) có thật sự xuất hiện trong ngữ cảnh top-3 hay không. 2đ nếu mốc nằm ngay trong chunk top-1, 1đ nếu ở top-2/3, 0đ nếu vắng.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên cần GPA tích lũy bao nhiêu để nộp học bổng thành tích RMIT? | `rmit-current-student-scholarship-2026` — đoạn xếp hạng ứng viên | +0,7650 | **1đ** — mốc `3,4` và `96` có ở chunk hạng 3, không ở top-1 | Ngữ cảnh đủ để trả lời, nhưng bằng chứng không ở đầu |
| 2 | Học bổng toàn phần cần giữ GPA bao nhiêu để được duy trì? | `scholarship-renewal-policy` — hàng bảng duy trì | +0,8075 | **1đ** — mốc `3,2` có trong top-3, không ở top-1 | Dễ nhầm sang ngưỡng 2,5 của mức 50–90% |
| 3 | **Trường hỗ trợ bao nhiêu tiền mỗi tháng?** (filter `audience=student`) | `ueh-learning-support-scholarship` | +0,5442 | **0đ** — bảng `đ/tháng` của UET vẫn không lọt top-3 | Trả lời theo tỷ lệ học phí, thiếu số tiền/tháng |
| 4 | Điều kiện xét học bổng hỗ trợ học tập cho sinh viên hoàn cảnh khó khăn là gì? | `undergraduate-scholarships` — quỹ hỗ trợ ứng viên khó khăn | **+2đ** | **2đ** — mốc `khó khăn` nằm ngay trong chunk top-1 | Trả lời được từ chunk đầu |
| 5 | Học bổng khuyến khích học tập UET trả bao nhiêu tiền mỗi tháng? | `uet-merit-scholarship-2025-2026` | +0,7773 | **1đ** — mốc `đ/tháng` có trong top-3 | Ngữ cảnh chứa bảng nhưng không ở top-1 |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **4 / 5** (Q1, Q2, Q4, Q5). Theo `docs/SCORING.md`: Q1 = 1, Q2 = 1, Q3 = 0, Q4 = 2, Q5 = 1 → **5 / 10**.

### So sánh có kiểm soát: tiền tố metadata đáng giá bao nhiêu?

Chạy lại đúng cùng một thứ, chỉ khác việc có chèn tiền tố hay không — cùng chunker nền `RecursiveChunker(280)`, cùng 45 chunk, cùng embedder, cùng 5 câu hỏi:

| | `recursive_280` trần | `metadata_enriched(recursive_280)` |
|---|---|---|
| Q1 (`3,4` / `96`) | 0đ — mốc vắng khỏi top-3 | **1đ** |
| Q2 (`3,2`) | 1đ | 1đ |
| Q3 (`đ/tháng`) | 0đ | 0đ |
| Q4 (`khó khăn`) | 0đ — sai tài liệu | **2đ** — đúng ngay top-1 |
| Q5 (`đ/tháng`) | 0đ — sai đoạn | **1đ** |
| **Tổng** | **1 / 10** | **5 / 10** |

Tiền tố metadata làm tăng điểm gấp năm lần mà **không đổi một tham số chunking nào**. Cơ chế: tiền tố bơm thêm tín hiệu chủ đề vào mỗi vector, nên chunk là một hàng bảng trơ (`| Chuẩn QH-2023 | 3.600.000đ/tháng | ...`) vốn gần như không có nội dung ngữ nghĩa thì nay mang theo cả tên học bổng và tên trường. Đây đúng là loại chunk mà `recursive_280` sinh ra nhiều nhất, và cũng là loại trước đó không bao giờ lọt top-3.

### Kết quả âm: tiền tố metadata KHÔNG thay thế được `metadata_filter`

Giả thuyết ban đầu của tôi là nếu `audience` đã nằm trong text thì retrieval tự phân biệt được đối tượng và filter thành thừa. Đo ra thì **sai**:

| Hạng | KHÔNG lọc | | CÓ `audience=student` | |
|---|---|---|---|---|
| | `doc_id` (audience) | score | `doc_id` (audience) | score |
| 1 | `ueh-faculty-support` (**faculty**) | +0,6133 | `ueh-learning-support-scholarship` (student) | +0,5442 |
| 2 | `ueh-faculty-support` (**faculty**) | +0,5712 | `undergraduate-scholarships` (student) | +0,5326 |
| 3 | `ueh-learning-support-scholarship` (student) | +0,5442 | `ueh-learning-support-scholarship` (student) | +0,5165 |
| | **Sai đối tượng: 2/3** | | **Sai đối tượng: 0/3** | |

Vẫn 2/3 sai đối tượng khi không lọc — y hệt tỷ lệ của chunker trần. Lý do hợp lý: tiền tố của tài liệu giảng viên là `[Hỗ trợ tài chính thu hút và phát triển giảng viên UEH | ueh | faculty]`. Chuỗi đó chứa "hỗ trợ tài chính" — **trùng từ vựng với câu hỏi**. Nên tiền tố vừa thêm tín hiệu đúng (đây là tài liệu UEH) vừa thêm tín hiệu gây nhiễu (đây là tài liệu về hỗ trợ tài chính), và token `faculty` đơn lẻ quá yếu để cân lại.

Bài học: **chèn metadata vào text và lọc metadata bằng filter giải hai bài toán khác nhau.** Tiền tố giúp định vị *đúng đoạn trong tài liệu* (1/10 → 5/10). Filter loại *đúng đối tượng* — việc mà similarity không làm được dù thông tin đối tượng đã nằm ngay trong chuỗi. Hai cơ chế bổ sung cho nhau chứ không thay thế nhau.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> **Từ `heading_320` của Bùi Tùng Dương — lặp tiêu đề vào chunk con.** Khi một mục dài phải cắt nhỏ, cấu hình này gắn lại tiêu đề vào từng mảnh, nên chunk thứ hai trở đi vẫn biết "mình đang nói về mục gì". Đó là lý do Q4 lên top-1 ở cấu hình này trong khi `recursive_280` của tôi chỉ đưa được lên top-2/3: tôi cắt ngắn để định vị chính xác hơn, nhưng cắt ngắn mà không giữ nhãn thì chunk mất ngữ cảnh phân cấp. Bài học: độ dài chunk và ngữ cảnh không phải hai lựa chọn loại trừ nhau — có thể vừa cắt ngắn vừa giữ ngữ cảnh bằng cách chèn lại tiêu đề.
>
> **Từ `paragraph_360` của Đàm Quang Sơn — truy xuất đúng không đồng nghĩa trả lời đúng.** Đây là cấu hình duy nhất đưa được hàng `GPA 3,2` vào top-3 ở Q2, nhưng agent vẫn trích nhầm sang hàng khác của cùng bảng. Tôi từng nghĩ cải thiện retrieval là đủ; ca này cho thấy còn một tầng lỗi nữa nằm sau bước truy xuất. Nó cũng khớp với kết quả đo của tôi ở mục 4: bốn hàng của bảng VinUni có khuôn câu gần như trùng nhau nên cả retriever lẫn agent đều không phân biệt được hàng nào ứng với mức học bổng nào.
>
> **Từ việc đối chiếu báo cáo cả nhóm — phải ghi rõ backend cạnh mỗi con số.** Cùng cấu hình `sentence_2` cho 3/10 với MockEmbedder và 7/10 với TF-IDF. Nghĩa là thứ hạng giữa các chiến lược phụ thuộc vào backend nhúng nhiều hơn phụ thuộc vào chính cách chia nhỏ, và một bảng so sánh không ghi backend thì gần như vô nghĩa. Ngược lại, kết luận về lọc `audience` giữ nguyên qua cả ba backend (Mock, TF-IDF, sentence-transformers) — nên tôi tin kết luận đó hơn hẳn mọi so sánh thứ hạng khác của nhóm.
>
> *(Ba điểm trên rút ra từ việc so sánh với báo cáo và cấu hình của các thành viên trong nhóm. Phần học được từ **nhóm khác** sẽ bổ sung sau buổi demo — tính đến lúc viết, buổi demo chưa diễn ra.)*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá | Căn cứ |
|----------|-------------------|--------|
| Khởi động (Warm-up) | 5 / 5 | Hai bài đã trả lời đủ; phép tính chunk được kiểm lại bằng `FixedSizeChunker` thật (23 và 25, khớp công thức). |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 | Mô tả khớp đúng code đã nộp, có nêu lý do lựa chọn và edge case chưa xử lý. Trừ 1 vì phần `SentenceChunker` chưa xử lý được viết tắt và số thập phân. |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 | `pytest tests/ -v` → 42 passed, không còn `NotImplementedError`. |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 | 5 cặp đo bằng embedder thật, có phân tích cơ chế (embedding không mã hóa giá trị số) và nối được với failure case Q2 của nhóm. |
| Kết quả truy xuất của tôi (Competition Results) | 3 / 10 | Chấm ở mức nội dung theo `docs/SCORING.md`, chưa chạy trên bộ câu hỏi chính thức của nhóm — xem lưu ý bên dưới. |
| **Tổng phần cá nhân** | **52 / 60** | |

> **Lưu ý về mục 5 — điểm sẽ thay đổi.** Bảng ở mục 5 chạy trên bộ 5 câu hỏi nháp của harness, không phải bộ chính thức trong `REPORT_NHOM.md`, và dùng cấu hình `FixedSizeChunker(500, overlap=50)` thay vì cấu hình `recursive_280` được phân công. Báo cáo nhóm ghi `recursive_280` đạt 7/10 trên bộ câu hỏi chính thức. Cần chạy lại bằng đúng bộ câu hỏi và đúng cấu hình rồi cập nhật cả bảng lẫn dòng điểm này trước khi nộp.

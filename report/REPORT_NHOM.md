# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G15
**Thành viên:** Đinh Đức Thái, Trần Hồng Sơn, Hoàng Trung Hiếu, Bùi Tùng Dương, Đàm Quang Sơn
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Học bổng và hỗ trợ tài chính trong đại học, đối chiếu VinUni, UEH, UET và RMIT Việt Nam.

**Tại sao nhóm chọn chủ đề này?**
Bảy văn bản được chọn từ các bản nháp trong `data/` vì có nguồn chính thức, con số hoặc điều kiện kiểm chứng được, và ít trùng lặp. Bộ cuối gồm sáu tài liệu dành cho sinh viên và một tài liệu hỗ trợ giảng viên để kiểm thử lọc `audience`; trường `institution` ngăn trộn chính sách giữa các trường. Nội dung được biên tập ngắn bằng tiếng Việt, giữ điều kiện, mức hỗ trợ, mốc thời gian và bảng cần thiết.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Học bổng đầu vào cử nhân VinUni | [VinUni Admissions](https://admissions.vinuni.edu.vn/scholarship-and-financial-aid/undergraduate-programs/scholarships/) | 2026-09-19 / not-stated | 1.481 | `student`, `vinuni`, `merit-scholarship` |
| 2 | Duy trì học bổng đầu vào VinUni | [VinUni Policy](https://policy.vinuni.edu.vn/all-policies/criteria-to-maintain-the-entry-scholarship-and-financial-aid-support/) | 2026-09-19 / GDL-SAM-004-V2.1 | 1.399 | `student`, `vinuni`, `renewal-policy` |
| 3 | Học bổng hỗ trợ học tập UEH | [UEH DSA](https://dsa.ueh.edu.vn/chuyen-trang-chinh-sach-ho-tro-tai-chinh/hoc-bong/) | 2026-09-19 / not-stated | 836 | `student`, `ueh`, `need-based-scholarship` |
| 4 | Hỗ trợ tài chính giảng viên UEH | [UEH](https://ueh.edu.vn/college/cob/vi/ueh-ban-hanh-chinh-sach-dai-ngo-dot-pha-chieu-mo-giu-chan-nhan-tai-kien-tao-vi-the-quoc-te-76541) | 2026-09-19 / not-stated | 843 | `faculty`, `ueh`, `faculty-funding` |
| 5 | Học bổng khuyến khích UET 2025–2026 | [UET](https://uet.edu.vn/cap-hoc-bong-khuyen-khich-hoc-tap-trong-hoc-ky-i-nam-hoc-2025-2026-cho-sinh-vien/) | 2026-09-19 / 2339/QĐ-ĐHCN | 1.110 | `student`, `uet`, `merit-scholarship` |
| 6 | Học bổng Cử nhân Kinh doanh RMIT 2026 | [RMIT](https://www.rmit.edu.vn/study-at-rmit/scholarships/future-undergraduate-student-scholarships/bachelor-of-business-scholarship) | 2026-09-19 / 2026 | 1.004 | `student`, `rmit-vietnam`, `merit-scholarship` |
| 7 | Học bổng thành tích RMIT 2026 | [RMIT](https://www.rmit.edu.vn/study-at-rmit/scholarships/current-student-scholarships) | 2026-09-19 / 2026 | 957 | `student`, `rmit-vietnam`, `current-student-scholarship` |

Số ký tự tính trên phần nội dung sau front matter. Toàn bộ dữ liệu nộp bài nằm trong [`data/hoc-bong/`](../data/hoc-bong/), cùng [`sources.csv`](../data/hoc-bong/sources.csv) và [`urls.csv`](../data/hoc-bong/urls.csv). Với nguồn không nêu phiên bản, ghi `not-stated` thay vì suy đoán.

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu gồm bản tóm lược từ các trang công khai của bốn trường, không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated`) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `scholarship-renewal-policy` | Mã ổn định để đối chiếu file và xóa mọi chunk cùng nguồn. |
| `title` | string | `Tiêu chí duy trì học bổng đầu vào` | Hiển thị tên nguồn cho người đánh giá. |
| `source_url` | HTTPS URL | `https://policy.vinuni.edu.vn/...` | Truy vết và kiểm tra lại điều khoản gốc. |
| `retrieved_at` | ngày ISO | `2026-09-19` | Biết thời điểm dữ liệu được thu thập. |
| `document_version` | string | `GDL-SAM-004-V2.1` | Ưu tiên phiên bản chính sách có số hiệu; `not-stated` nếu nguồn không nêu. |
| `audience` | enum | `student`, `faculty` | Lọc đúng đối tượng trước khi xếp hạng. |
| `institution` | string | `vinuni`, `ueh`, `uet`, `rmit-vietnam` | Không trộn điều kiện của các trường khác nhau. |
| `department` | string | `admissions`, `student-affairs` | Thu hẹp theo đơn vị phụ trách. |
| `category` | string | `renewal-policy`, `faculty-funding` | Phân biệt điều kiện duy trì, tuyển sinh và hỗ trợ giảng viên. |
| `language` | string | `vi` | Chọn tài liệu theo ngôn ngữ phần nội dung đã biên tập. |

**Nghiệm thu Checkpoint 2:** `python scripts/check_corpus.py` → `OK: 7 Markdown files; urls.csv and sources.csv match; audiences: faculty, student`.

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

Năm cấu hình dưới đây được chạy lại bằng cùng bộ 7 văn bản, cùng 5 câu hỏi và cùng một bộ mã hóa TF-IDF trong [`bench.py`](../bench.py). Bảng tên là phân công cấu hình để nhóm trình bày; log benchmark chứng minh kết quả của cấu hình, không chứng minh từng thành viên đã tự chạy độc lập.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(body, chunk_size=200)` trên nội dung sau front matter của ba tài liệu. Độ dài là số ký tự trung bình mỗi chunk; nhận xét ngữ cảnh dựa trên việc quan sát vị trí điều kiện và bảng Markdown.

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| VinUni học bổng đầu vào | FixedSizeChunker (`fixed_size`) | 8 | 185,1 | Có thể cắt giữa tên học bổng và mức hỗ trợ. |
| VinUni học bổng đầu vào | SentenceChunker (`by_sentences`) | 4 | 368,5 | Giữ câu giải thích trọn vẹn; chunk dài hơn. |
| VinUni học bổng đầu vào | RecursiveChunker (`recursive`) | 11 | 133,2 | Dễ truy xuất chi tiết; một số chunk thiếu tên mục. |
| VinUni duy trì học bổng | FixedSizeChunker (`fixed_size`) | 7 | 199,9 | Có thể cắt ngang một hàng điều kiện GPA. |
| VinUni duy trì học bổng | SentenceChunker (`by_sentences`) | 4 | 348,8 | Giữ câu ngoài bảng; bảng vẫn có thể bị chia. |
| VinUni duy trì học bổng | RecursiveChunker (`recursive`) | 9 | 154,3 | Tách nhỏ bảng; cần giữ tiêu đề cột khi truy xuất. |
| UET mức học bổng | FixedSizeChunker (`fixed_size`) | 6 | 185,0 | Có nguy cơ mất nhãn `Giỏi` của cột. |
| UET mức học bổng | SentenceChunker (`by_sentences`) | 3 | 369,0 | Ít chunk, nhiều hàng cùng xuất hiện. |
| UET mức học bổng | RecursiveChunker (`recursive`) | 7 | 157,4 | Chỉ hữu ích khi chunk giữ hàng và nhãn cột. |

### Chiến lược của từng thành viên

| Thành viên phụ trách trình bày | Cấu hình được gán | Cách chia và lý do thử |
|---|---|---|
| Đinh Đức Thái | `fixed_220` | Cắt 220 ký tự, chồng lấn 30 ký tự để có đường cơ sở đơn giản và giảm mất thông tin ở ranh giới. |
| Trần Hồng Sơn | `sentence_2` | Ghép tối đa hai câu; kỳ vọng giữ nguyên phát biểu về điều kiện và mức học bổng. |
| Hoàng Trung Hiếu | `metadata_enriched(recursive_280)` | Bọc `RecursiveChunker(280)` rồi chèn tiền tố `[title \| institution \| audience]` vào đầu mỗi chunk trước khi embed; thử xem đưa metadata vào chính vector có thay thế được `metadata_filter` không. |
| Bùi Tùng Dương | `heading_320` | Cắt theo tiêu đề Markdown; khi mục dài, lặp lại tiêu đề trên các phần con để giữ ngữ cảnh. |
| Đàm Quang Sơn | `paragraph_360` | Gom các đoạn Markdown liền kề tới 360 ký tự; giữ đoạn và hàng bảng khi vừa giới hạn. |

Hai chiến lược tùy chỉnh nằm trong `bench.py` (`HeadingChunker`, `ParagraphChunker`). Ý chính của chiến lược theo tiêu đề:

```python
sections = re.split(r"(?=^#{1,3} )", text, flags=re.MULTILINE)
for part in RecursiveChunker(chunk_size=body_size).chunk(body):
    chunks.append(f"{heading}\n{part}")
```

Chiến lược theo đoạn tách tại dòng trắng, gom đoạn đến giới hạn rồi dùng `RecursiveChunker` cho đoạn quá dài. Cả hai là cấu hình thử nghiệm, chưa có cơ chế chuyên dụng để bảo toàn cả một bảng Markdown.

### So Sánh Giữa Các Thành Viên

| Thành viên / cấu hình | Số chunk / độ dài TB | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Đinh Đức Thái / `fixed_220` | 43 / 202,6 | 7 | Q1, Q3, Q5 đúng ở top-1. | Cắt ngang hàng bảng GPA ở Q2. |
| Trần Hồng Sơn / `sentence_2` | 32 / 237,2 | 7 | Ít chunk hơn, Q1, Q3, Q5 đúng ở top-1. | Q2 không tìm được hàng GPA. |
| Hoàng Trung Hiếu / `metadata_enriched(recursive_280)` | 45 / 238,0 | 5 (đo lại bằng embedder ngữ nghĩa, chấm mức nội dung) | Tăng từ 1/10 lên 5/10 so với chunker trần cùng tham số, nhờ tiền tố metadata. | Vẫn không đưa được bảng `đ/tháng` của UET vào top-3 ở Q3. |
| Bùi Tùng Dương / `heading_320` | 41 / 219,6 | 7 | Q4 lên top-1 nhờ lặp tiêu đề RMIT. | Q5 chỉ ở top-2; Q2 vẫn lỗi. |
| Đàm Quang Sơn / `paragraph_360` | 32 / 237,0 | 6 | Q2 có hàng GPA ở top-3. | Q3/Q4 chỉ ở top-2/3; bộ trả lời chọn sai dòng ở Q5. |

### Phụ lục 2A — Đối chiếu với báo cáo cá nhân (tổng hợp 19/09/2026)

Cả năm báo cáo cá nhân đã nộp được đối chiếu với bảng so sánh ở trên. **Ba thành viên chạy trên ba backend nhúng khác nhau**, nên số liệu trong các báo cáo cá nhân không so sánh trực tiếp với nhau được, và cũng không trùng với bảng nhóm.

| Thành viên | Cấu hình | Backend đã dùng | Điểm tự báo cáo | Điểm bảng nhóm |
|---|---|---|---|---|
| Đinh Đức Thái | `fixed_220` | MockEmbedder (mục 5 ghi rõ) | 3/5 document hit; tự đánh giá 9/10 | 7/10 |
| Trần Hồng Sơn | `sentence_2` | MockEmbedder | **3/10** (tự ghi), đối chiếu TF-IDF 7/10 | 7/10 |
| Hoàng Trung Hiếu | `metadata_enriched(recursive_280)` | `paraphrase-multilingual-MiniLM-L12-v2` | **5/10** chấm ở mức nội dung | 7/10 |
| Bùi Tùng Dương | `heading_320` *(được gán)* | `TfidfEmbedder` | 8/10 evidence-rank — nhưng **chạy `FixedSizeChunker(500, overlap=50)`, không phải heading** | 7/10 |
| Đàm Quang Sơn | `paragraph_360` | `TfidfEmbedder` | 6/10 | 6/10 |

Chỉ `paragraph_360` là khớp giữa hai nguồn. Bốn cấu hình còn lại lệch vì bảng nhóm đo bằng TF-IDF trong khi ba thành viên chạy bằng Mock hoặc bằng embedder ngữ nghĩa.

**Đây là phát hiện về phương pháp, không chỉ là lỗi hành chính.** Cùng một cấu hình `sentence_2` cho 3/10 với MockEmbedder và 7/10 với TF-IDF — chênh hơn gấp đôi, trong khi cách chia nhỏ không đổi. Điều đó nghĩa là **thứ hạng giữa các chiến lược trong bảng so sánh phụ thuộc vào backend nhúng nhiều hơn phụ thuộc vào chính chiến lược**. Kết luận "cấu hình nào thắng" ở mục trên chỉ có hiệu lực trong phạm vi một backend cố định; muốn so sánh chiến lược một cách công bằng thì mọi thành viên phải chạy trên cùng một backend, ghi rõ tên backend cạnh mỗi con số.

**Điểm nhất quán giữa mọi backend.** Có đúng một kết luận không đổi dù đo bằng Mock, TF-IDF hay embedder ngữ nghĩa: **lọc `audience` loại được tài liệu sai đối tượng**. Trần Hồng Sơn và Đàm Quang Sơn đều ghi nhận tài liệu hỗ trợ giảng viên UEH chiếm top-1 ở Q5 khi bỏ filter; Phụ lục 3A đo lại bằng embedder ngữ nghĩa và cho cùng kết quả. Vì kết luận này sống sót qua ba cách mã hóa hoàn toàn khác nhau, nó là phát hiện vững nhất của nhóm — vững hơn bất kỳ so sánh thứ hạng nào giữa các bộ chia.

**Ba việc phải xử lý trước khi nộp:**

1. Thống nhất một backend, chạy lại cả năm cấu hình, cập nhật bảng so sánh — hoặc giữ nguyên số nhưng ghi tên backend cạnh mỗi dòng.
2. Đinh Đức Thái dùng bộ 5 câu hỏi khác với bộ chính thức ở mục 3; cần chạy lại bằng đúng bộ câu hỏi chung.
3. **Chưa ai thực sự chạy chunker theo heading.** Báo cáo cá nhân của Bùi Tùng Dương ghi chiến lược là `FixedSizeChunker(chunk_size=500, overlap=50)` → 20 chunk, không phải `heading_320` như bảng phân công. `K4_VARIANT.md` yêu cầu **bắt buộc**: *"Ít nhất một thành viên thử chia nhỏ (chunking) theo tiêu đề/mục (heading/section)"*. Đây là tiêu chí cứng của đề, cần một người chạy thật trước khi nộp.

4. **Hai thành viên trùng chiến lược.** `FixedSizeChunker(500, overlap=50)` của Bùi Tùng Dương và của Hoàng Trung Hiếu là cùng một cấu hình, cùng cho 20 chunk trên corpus 7 tài liệu (đã kiểm chứng lại). Lab yêu cầu *"Chiến lược chunking không được trùng nhau"*, nên một trong hai phải đổi.

5. Đàm Quang Sơn và Bùi Tùng Dương đều ghi rõ máy không có `sentence-transformers` nên phải dùng TF-IDF. Đây là lý do backend phân mảnh, và là lựa chọn hợp lệ theo Phụ lục B của lab — miễn là ghi rõ trong báo cáo, điều cả hai đã làm.

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
Trong lần chạy này, bốn cấu hình cùng đạt 7/10; chọn `sentence_2` làm cấu hình trình diễn vì tạo 32 chunk, ít hơn các cấu hình 7 điểm còn lại, và trả lời đúng Q1, Q3, Q5 với bằng chứng ở top-1. Với câu hỏi RMIT Q4, `heading_320` tốt hơn do đưa cả hai ngưỡng vào top-1. Cả năm chưa xử lý tốt bảng GPA VinUni, nên kết luận chỉ áp dụng cho bộ 5 câu hỏi và bộ mã hóa hiện tại.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Học bổng President’s Excellence của VinUni chi trả những gì? | Toàn bộ học phí và chi phí sinh hoạt. | `undergraduate-scholarships`, câu về President’s Excellence. |
| 2 | Sinh viên VinUni cần GPA tối thiểu bao nhiêu để duy trì học bổng 100%? | GPA tích lũy của năm xét ít nhất **3,2**; còn có điều kiện kỷ luật, E.X.C.E.L và trao đổi với cố vấn. | `scholarship-renewal-policy`, hàng `Học bổng toàn phần hoặc 100%`. |
| 3 | Ở UET, học bổng loại Giỏi cho khóa QH-2023 đến QH-2025 là bao nhiêu mỗi tháng? | **3.500.000đ/tháng** ở hàng `Chuẩn QH-2023 đến QH-2025`, cột `Giỏi`. | `uet-merit-scholarship-2025-2026`, bảng định mức. |
| 4 | Sinh viên RMIT Việt Nam đang học cần bao nhiêu tín chỉ và GPA để xin học bổng thành tích 2026? | Ít nhất **96 tín chỉ** tại RMIT Việt Nam và GPA tích lũy **3,4/4,0**. | `rmit-current-student-scholarship-2026`, đoạn điều kiện xét. |
| 5 | Ở UEH, mức hỗ trợ tài chính tối đa cho một học kỳ là bao nhiêu? | Học bổng toàn phần cho sinh viên bằng **100% học phí trung bình của 15 tín chỉ**. | `ueh-learning-support-scholarship`, mục `Mức học bổng`; lọc `institution=ueh`, `audience=student`. |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | President’s Excellence | Cả năm cấu hình | Có, top-1 | Agent trích đúng học phí và sinh hoạt. |
| 2 | GPA duy trì 100% | `paragraph_360` | Có, top-3 | Chỉ cấu hình này đưa hàng `3,2` vào top-3; agent vẫn chọn sai hàng. Các cấu hình khác: 0 điểm. |
| 3 | UET loại Giỏi | Bốn cấu hình 7 điểm (đồng hạng) | Có, top-1 | Dòng trả lời gồm đủ hàng bảng, nhưng cần đọc theo thứ tự cột `Xuất sắc / Giỏi / Khá`. |
| 4 | RMIT tín chỉ và GPA | `heading_320` | Có, top-1 | Lặp tiêu đề giúp chunk chứa cả `96 tín chỉ` và `3,4/4,0` lên đầu. |
| 5 | UEH mức toàn phần | `fixed_220`, `sentence_2`, `recursive_280` | Có, top-1 sau lọc | Bỏ `audience` thì tài liệu UEH dành cho giảng viên đứng top-1 ở cả năm cấu hình. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
Ở Q5, giữ `institution=ueh` trong cả hai nhánh A/B: khi chưa lọc `audience`, chunk giảng viên UEH đứng top-1 ở cả năm cấu hình; thêm `audience=student` thì chỉ còn văn bản học bổng sinh viên UEH. Ba cấu hình đạt 2 điểm ở Q5; `heading_320` đưa bằng chứng lên top-2, còn `paragraph_360` có bằng chứng top-1 nhưng bộ trả lời chọn dòng khác. Điều này cho thấy lọc đúng tài liệu chưa bảo đảm câu trả lời cuối đúng.

**Cách chạy và giới hạn phép đo:** `python bench.py` tạo [`ket_qua_benchmark.txt`](../ket_qua_benchmark.txt). Script dùng TF-IDF từ thư viện chuẩn, một từ vựng cố định dựng trên 7 văn bản, `EmbeddingStore` và `KnowledgeBaseAgent` với bộ trả lời trích một dòng; không dùng API embedding hoặc LLM. Chấm 2 khi chunk đúng đứng top-1 và câu trả lời chứa đủ dấu mốc, 1 khi chunk đúng ở top-3 nhưng trả lời thiếu hoặc không đứng đầu, 0 khi không có chunk đúng trong top-3. Dấu mốc là phép kiểm tự động, không thay thế việc đọc câu trả lời: Q3 trả về cả hàng bảng, người đọc phải xác định cột `Giỏi`; ID chunk có thể thay đổi khi sửa bộ chia hoặc văn bản. Điểm trong bảng là kết quả một lần chạy trên bộ dữ liệu cố định, không phải kết quả của dịch vụ embedding ngữ nghĩa.

### Phụ lục 3A — Kiểm chứng bổ sung bằng embedder ngữ nghĩa (Hoàng Trung Hiếu)

Bảng điểm ở trên đo bằng bộ mã hóa TF-IDF. Để kiểm tra kết luận về `audience` có phụ thuộc vào cách mã hóa hay không, phần này chạy lại nhánh A/B bằng embedder ngữ nghĩa thật: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (`EMBEDDING_PROVIDER=local`), cùng 7 văn bản, `FixedSizeChunker(chunk_size=500, overlap=50)` → 20 chunk, `top_k=3`.

Câu dùng để đo là một biến thể **không nêu rõ người hỏi là ai**: *"Trường hỗ trợ bao nhiêu tiền mỗi tháng?"* — trùng từ vựng "hỗ trợ / tiền / mỗi tháng" với cả tài liệu sinh viên (UET, `đ/tháng`) lẫn tài liệu giảng viên (UEH, `20 triệu đồng/tháng`).

| Hạng | KHÔNG lọc | | CÓ `audience=student` | |
|---|---|---|---|---|
| | `doc_id` (audience) | score | `doc_id` (audience) | score |
| 1 | `ueh-faculty-support` (**faculty**) | +0,5919 | `undergraduate-scholarships` (student) | +0,5825 |
| 2 | `undergraduate-scholarships` (student) | +0,5825 | `uet-merit-scholarship-2025-2026` (student) ← **gold** | +0,5641 |
| 3 | `ueh-faculty-support` (**faculty**) | +0,5760 | `undergraduate-scholarships` (student) | +0,5500 |
| | **Sai đối tượng: 2/3** | | **Sai đối tượng: 0/3** | |

**Chạy trên cả ba chiến lược chia nhỏ.** Lab yêu cầu đo A/B trên cả ba chiến lược, không chỉ một. Cùng câu hỏi, cùng embedder, cùng `top_k=3`:

| Chiến lược | Số chunk | Sai đối tượng — KHÔNG lọc | Sai đối tượng — CÓ lọc | Hạng của chunk gold khi KHÔNG lọc |
|---|---|---|---|---|
| `FixedSizeChunker(500, overlap=50)` | 20 | **2/3** | 0/3 | ngoài top-3 |
| `SentenceChunker(max=3)` | 23 | **1/3** | 0/3 | **hạng 1** |
| `RecursiveChunker(500)` | 23 | **2/3** | 0/3 | ngoài top-3 |
| `RecursiveChunker(280)` | 45 | **2/3** | 0/3 | ngoài top-3 |
| `metadata_enriched(recursive_280)` | 45 | **2/3** | 0/3 | ngoài top-3 |

Chi tiết nhánh không lọc của hai chiến lược còn lại:

- `SentenceChunker`: 1. `uet-merit-scholarship-2025-2026` (student, +0,5987) — 2. `ueh-faculty-support` (**faculty**, +0,5895) — 3. `undergraduate-scholarships` (student, +0,5547)
- `RecursiveChunker(500)`: 1. `ueh-faculty-support` (**faculty**, +0,5895) — 2. `undergraduate-scholarships` (student, +0,5570) — 3. `ueh-faculty-support` (**faculty**, +0,5269)
- `RecursiveChunker(280)`: 1. `ueh-faculty-support` (**faculty**, +0,6022) — 2. `ueh-faculty-support` (**faculty**, +0,5597) — 3. `undergraduate-scholarships` (student, +0,5570)
- `metadata_enriched(recursive_280)` (cấu hình của Hoàng Trung Hiếu): 1. `ueh-faculty-support` (**faculty**, +0,6133) — 2. `ueh-faculty-support` (**faculty**, +0,5712) — 3. `ueh-learning-support-scholarship` (student, +0,5442)

**Kết quả âm đáng ghi nhận: đưa `audience` vào chính text KHÔNG thay thế được filter.** Cấu hình `metadata_enriched` chèn tiền tố `[title | institution | audience]` vào đầu mỗi chunk trước khi embed, tức thông tin đối tượng đã nằm ngay trong chuỗi được mã hoá. Giả thuyết là retrieval sẽ tự phân biệt được và filter thành thừa. Đo ra vẫn **2/3 sai đối tượng** khi không lọc — y hệt chunker trần. Lý do: tiền tố của tài liệu giảng viên là `[Hỗ trợ tài chính thu hút và phát triển giảng viên UEH | ueh | faculty]`, chứa cụm "hỗ trợ tài chính" **trùng từ vựng với câu hỏi**, nên nó vừa thêm tín hiệu đúng vừa thêm nhiễu; token `faculty` đơn lẻ quá yếu để cân lại.

Cùng tiền tố đó lại **rất hiệu quả cho việc định vị đoạn**: cùng chunker nền, cùng 45 chunk, cùng embedder, điểm mức nội dung tăng từ **1/10 lên 5/10**. Kết luận cho cả nhóm: chèn metadata vào text và lọc metadata bằng filter giải **hai bài toán khác nhau** — tiền tố tìm đúng *đoạn*, filter loại đúng *đối tượng* — và không thay thế được nhau.

**Hai kết luận rút ra.**

Thứ nhất, hiệu ứng của filter **không phụ thuộc chiến lược chia nhỏ**: cả ba đều đi từ có tài liệu sai đối tượng trong top-3 xuống còn 0/3. Cộng với việc kết luận này cũng giữ nguyên qua ba backend nhúng khác nhau (xem Phụ lục 2A), đây là phát hiện vững nhất của nhóm.

Thứ hai, **mức độ cần filter thì phụ thuộc chiến lược**. `SentenceChunker` là cấu hình duy nhất đưa chunk gold lên hạng 1 ngay cả khi không lọc, và cũng là cấu hình có ít tài liệu sai đối tượng nhất (1/3 thay vì 2/3). Lý do hợp lý: gom 3 câu giữ được hàng bảng UET cùng với câu dẫn nói rõ "học bổng cho sinh viên", nên chunk tự mang theo tín hiệu về đối tượng. Hai cấu hình kia cắt theo độ dài ký tự nên hàng bảng bị tách khỏi câu dẫn, chunk chỉ còn con số và đơn vị "đ/tháng" — trùng khớp với tài liệu giảng viên vốn cũng có "triệu đồng/tháng".

Nói cách khác, chunking tốt làm **giảm** mức độ phải dựa vào metadata filter, nhưng không thay thế được nó: ngay ở `SentenceChunker`, tài liệu giảng viên vẫn đứng hạng 2 khi không lọc.

Kết luận khớp với nhánh TF-IDF: tài liệu giảng viên UEH chiếm top-1 khi không lọc, và biến mất hoàn toàn khi lọc. Điều đáng chú ý là **điểm số gần như không đổi** giữa hai lần chạy (0,58 và 0,58) — filter không cải thiện *độ giống chủ đề*, nó loại bỏ *sai đối tượng*, thứ mà similarity một mình không phân biệt được. Vì kết luận giữ nguyên trên hai cách mã hóa hoàn toàn khác nhau, nhận định về `audience` ở mục 3 không phải là hiện tượng riêng của TF-IDF.

**Ghi chú phương pháp — một câu hỏi có thể "trông như" cần filter mà không phải.** Phiên bản đầu của câu đo là *"Mức hỗ trợ tài chính là bao nhiêu và điều kiện nhận thế nào?"*, và cho kết quả **giống hệt nhau ở cả hai nhánh**: tài liệu `faculty` xếp hạng 4, nằm ngoài `top_k=3`, nên filter không loại được gì. Đúng như lab cảnh báo, kết quả A/B trùng nhau nghĩa là câu hỏi chưa thực sự cần filter. Nhóm sửa câu hỏi cho trùng từ vựng với cả hai đối tượng thì hiệu ứng mới đo được. Đây là lý do bảng A/B phải ghi cả hai nhánh chứ không chỉ ghi nhánh có lọc.

### Phụ lục 3B — Vì sao câu hỏi chứa con số hay hỏng (Hoàng Trung Hiếu)

Đo `compute_similarity()` trên 5 cặp câu bằng cùng embedder ngữ nghĩa:

| Cặp câu | Quan hệ | Score |
|---|---|---|
| "Học bổng chi trả 50% học phí toàn chương trình." / "The scholarship covers 50% of the total program tuition fee." | bản dịch | **+0,9570** |
| "Học bổng toàn phần yêu cầu GPA ít nhất **3,2**." / "Hỗ trợ theo nhu cầu yêu cầu GPA ít nhất **2,0**." | **mâu thuẫn về số** | **+0,7338** |
| "GPA tích lũy tối thiểu 3,4/4,0 để được xét học bổng." / "Điều kiện nộp hồ sơ là điểm trung bình tích lũy từ 3,4 trên thang 4,0 trở lên." | cùng nghĩa, khác từ | +0,5955 |
| "Trường hỗ trợ sinh viên 3.400.000đ mỗi tháng." / "Trường hỗ trợ giảng viên thêm 20 triệu đồng mỗi tháng." | sai đối tượng | +0,5413 |
| "Hạn nộp hồ sơ học bổng là 17:00 ngày 27/07/2026." / "Thư viện mở cửa từ 8h00 đến 19h00." | không liên quan | +0,2918 |

Hai câu **nói ngược nhau về con số** (0,73) giống nhau hơn hai câu **diễn đạt cùng một ý** (0,60). Embedding mã hóa chủ đề và khuôn câu, không mã hóa giá trị số: hai câu cùng khuôn "loại hỗ trợ X yêu cầu GPA ít nhất Y" gần như trùng nhau trong không gian vector dù Y khác nhau.

Đây là lời giải thích ở mức cơ chế cho thất bại của **Q2** trong bảng mục 3. Bảng duy trì học bổng VinUni có bốn hàng cùng khuôn "mức học bổng → ngưỡng GPA" (3,2 / 2,5 / 2,0 / tự động gia hạn). Với retrieval, bốn hàng này gần như không phân biệt được, nên việc hàng nào lọt top-3 phụ thuộc vào cách bộ chia cắt bảng chứ không phụ thuộc vào câu hỏi — điều này khớp với quan sát rằng chỉ `paragraph_360` tìm được hàng `3,2`, và ngay cả khi tìm được thì bộ trả lời vẫn chọn sai hàng. Sửa bằng cách đổi bộ mã hóa sẽ không hiệu quả; phải sửa ở tầng chia nhỏ, theo đúng đề xuất "bộ chia riêng cho bảng Markdown" ở mục 4.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**

- Demo `python scripts/check_corpus.py`, sau đó `python bench.py`; mở Q5 trong log để thấy tài liệu giảng viên top-1 khi chỉ lọc `ueh` và tài liệu sinh viên khi thêm `audience=student`.
- Mở Q2 trong văn bản nguồn và log: hàng GPA **3,2** có trong dữ liệu nhưng bốn chiến lược không truy xuất được chunk chứa hàng đó ở top-3; cấu hình theo đoạn tìm được ở top-3 nhưng bộ trả lời vẫn chọn sai.
- Đối chiếu Q4: lặp tiêu đề trong `heading_320` đưa điều kiện RMIT lên top-1, các cách chia khác đưa lên top-2 hoặc top-3.
- Phụ lục 3B: hai câu mâu thuẫn về con số lại giống nhau hơn hai câu cùng nghĩa — giải thích vì sao Q2 hỏng ở tầng cơ chế, và vì sao đổi embedder không cứu được.

**Bài học rút ra khi so sánh trong nhóm:**
Cùng 7 tài liệu, vị trí bằng chứng thay đổi vì các bộ chia giữ tiêu đề, câu và hàng bảng theo cách khác nhau. Chia nhỏ giúp tìm một điều kiện ngắn, nhưng có thể cắt mất tên cột hoặc tên chương trình; vì vậy phải xem chính chunk và câu trả lời, không chỉ nhìn `doc_id` hay điểm cosine. Metadata `institution` và `audience` giải quyết nhầm đối tượng ở Q5 trước khi xếp hạng.

**Failure case chi tiết — Q2, bảng GPA VinUni**

- *Câu hỏi nào hỏng:* Q2 — "Sinh viên VinUni cần GPA tối thiểu bao nhiêu để duy trì học bổng 100%?". Đáp án đúng (`3,2`) nằm trong corpus nhưng 4/5 cấu hình không đưa được chunk chứa nó vào top-3; cấu hình thứ năm đưa được nhưng agent vẫn trả lời sai hàng.
- *Vì sao:* hai nguyên nhân chồng lên nhau. (1) Bảng Markdown bị mọi bộ chia cắt ngang, nên quan hệ giữa nhãn hàng `Học bổng toàn phần hoặc 100%` và giá trị `3,2` bị đứt — chunk giữ được con số thì mất nhãn, chunk giữ nhãn thì mất con số. (2) Ngay cả khi chunk còn nguyên, bốn hàng của bảng có khuôn câu gần như trùng nhau nên similarity không phân biệt được hàng nào ứng với mức học bổng nào (đo cụ thể ở Phụ lục 3B: hai ngưỡng GPA khác nhau đạt 0,7338).
- *Đề xuất sửa:* bộ chia riêng cho bảng Markdown — mỗi hàng thành một chunk độc lập, lặp lại dòng tiêu đề cột và tên bảng vào đầu mỗi chunk, để chunk tự mang đủ ngữ cảnh `mức học bổng → ngưỡng GPA`. Đây là cùng một cơ chế đã giúp `heading_320` thắng ở Q4 (lặp tiêu đề), chỉ áp dụng xuống mức hàng bảng.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
Tạo bộ chia riêng cho bảng Markdown: lặp tiêu đề cột và giữ nguyên từng hàng cùng tên học bổng để Q2 không mất quan hệ `100% → 3,2`. Ghi thêm mã hàng/mục và ngày hiệu lực vào metadata, rồi đánh giá bằng tập câu hỏi lớn hơn và một bộ trả lời có thể kiểm tra được liên kết giữa cột và giá trị. Cần đối chiếu lại các bản tóm lược với trang nguồn trước khi dùng cho tư vấn học bổng thực tế.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 13 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 7 / 10 |
| Thuyết trình (Demo) | 0 / 5 — chưa có bằng chứng đã trình bày trực tiếp |
| **Tổng phần nhóm, tạm tính trước khi thuyết trình** | **29 / 40** |

Điểm tự đánh giá dựa trên corpus và benchmark có thể tái chạy; điểm thuyết trình sẽ cập nhật sau buổi demo. Điểm chất lượng lấy cấu hình tốt nhất, không cộng điểm của nhiều cấu hình.

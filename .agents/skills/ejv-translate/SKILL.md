---
name: ejv-translate
description: Dịch thuật tài liệu chính xác đa ngôn ngữ (Tiếng Việt, English, 日本語) kết hợp trích xuất nội dung văn phòng (PDF, DOCX, TXT), dịch thuật ngữ cảnh sâu theo cấu trúc block đồng bộ 3 ngôn ngữ và xuất bản đa định dạng (DOCX, PDF, Markdown). Hỗ trợ cơ chế phân lô (Chunking & Checkpointing) chống tràn token cho tài liệu dài (50 - 100+ trang) bảo đảm 100% Zero-Loss. Kích hoạt khi người dùng yêu cầu dịch thuật 3 ngôn ngữ (VN/EN/JP), dịch tài liệu dài (EJV translator), chuyển đổi văn bản sang song ngữ/tam ngữ, hoặc xử lý tài liệu hành chính/học thuật.
trigger: Dịch tài liệu 3 ngôn ngữ (VN/EN/JP), EJV Translator, dịch thuật chính xác
needs_file: true
file_filter: office
---

# EJV Trilingual Document Translator (VN - EN - JP)
## Anti-Token Overflow & Zero-Loss Architecture

Kế thừa và nâng cấp từ miniapp **EJV Translator** trong DocStudio, kết hợp sức mạnh xử lý bóc tách tài liệu (PDF, DOCX, TXT, MD) và dịch thuật ngữ cảnh chuyên sâu 3 ngôn ngữ (Tiếng Việt, English, 日本語) với cơ chế **Phân lô & Checkpoint chống tràn token (Zero-Loss Chunking)**.

---

## 🎯 Khi nào sử dụng skill này?

- Dịch tài liệu (PDF, DOCX, Excel, Text, Markdown) sang **3 ngôn ngữ đồng thời** (VN, EN, JP) hoặc song ngữ bất kỳ.
- Dịch văn bản dài (10 - 100+ trang như Nghị định, Luật, Hợp đồng, Báo cáo kỹ thuật) mà **không bị cắt xén hay tóm tắt dở dang**.
- Yêu cầu dịch chính xác, bảo toàn 100% cấu trúc phân cấp (tiêu đề h1/h2/h3, đoạn văn p, danh sách ul/ol, bảng biểu table, trích dẫn blockquote, chú thích caption).
- Xuất kết quả ra file hoàn chỉnh: `.docx` chuẩn in ấn, `.docx` bảng 3 cột đối chiếu song song, `.md` song song, hoặc dữ liệu EJV JSON.

---

## 🏗️ Kiến trúc quy trình xử lý 5 Bước (Zero-Loss Protocol)

```mermaid
graph TD
    A["Tài liệu đầu vào<br/>(PDF / DOCX / MD / TXT)"] --> B["Bước 1: Trích xuất cấu trúc<br/>(scripts/extract_text.py)"]
    B --> C["Bước 2: Phân lô & Tạo Manifest<br/>(scripts/chunk_manager.py)"]
    C --> D["Bước 3: Dịch từng Batch tuần tự<br/>(Checkpointing: batch_XXX_translated.json)"]
    D --> E["Bước 4: Ghép nối & Kiểm toán 100%<br/>(scripts/merge_batches.py)"]
    E --> F["Bước 5: Xuất bản tài liệu<br/>(DOCX 3 cột / DOCX từng ngôn ngữ / Markdown)"]
```

---

## 📋 Hướng dẫn thực hiện chi tiết

### 📌 Bước 1: Trích xuất cấu trúc văn bản
Trích xuất toàn bộ các khối nội dung (Headings, Paragraphs, Lists, Tables) ra file trung gian:
```bash
python <skill_dir>/scripts/extract_text.py --input "<file_dau_vao>" --output "<process_dir>/extracted_blocks.json"
```

### 📌 Bước 2: Phân lô (Chunking) & Thiết lập Manifest
Đối với tài liệu vừa và dài (> 25 khối hoặc > 1000 từ), tự động chia thành các batch nhỏ an toàn:
```bash
python <skill_dir>/scripts/chunk_manager.py --input "<process_dir>/extracted_blocks.json" --process-dir "<process_dir>" --max-blocks 25 --max-words 1000
```
*Script sẽ tạo `manifest.json` và các file `batch_001_source.json`, `batch_002_source.json`... để quản lý tiến độ từng phần.*

### 📌 Bước 3: Dịch thuật ngữ cảnh sâu từng Batch (Checkpoint Loop)
Agent duyệt qua từng batch từ `batch_001` đến `batch_NNN`:
- Đọc nội dung `batch_XXX_source.json`.
- Dịch đầy đủ sang 3 ngôn ngữ: `vn`, `en`, `ja` theo cấu trúc EJV Schema.
- Ghi kết quả vào `batch_XXX_translated.json`.
- **Cơ chế Checkpoint**: Nếu gặp gián đoạn, chỉ cần dịch tiếp các batch có trạng thái `pending`.

#### Cấu trúc Block JSON chuẩn (EJV Schema)
```json
[
  {
    "type": "h1",
    "vn": "TIÊU ĐỀ CẤP 1",
    "en": "HEADING LEVEL 1",
    "ja": "見出しレベル1"
  },
  {
    "type": "p",
    "vn": "Nội dung đoạn văn tiếng Việt đầy đủ và chuẩn xác.",
    "en": "Full and accurate English paragraph content.",
    "ja": "完全で正確な日本語の段落内容。"
  },
  {
    "type": "ul",
    "vn": ["Mục 1", "Mục 2"],
    "en": ["Item 1", "Item 2"],
    "ja": ["項目1", "項目2"]
  },
  {
    "type": "table",
    "headers": {
      "vn": ["STT", "Hạng mục"],
      "en": ["No.", "Item"],
      "ja": ["項番", "項目"]
    },
    "rows": {
      "vn": [["1", "Thông số A"]],
      "en": [["1", "Parameter A"]],
      "ja": [["1", "パラメータA"]]
    }
  }
]
```

### 📌 Bước 4: Ghép nối & Kiểm tra toàn vẹn 100% (Zero-Loss Audit)
Ghép toàn bộ các batch đã dịch thành file hoàn chỉnh:
```bash
python <skill_dir>/scripts/merge_batches.py --process-dir "<process_dir>" --output "<process_dir>/merged_ejv.json"
```
*Script sẽ kiểm toán số lượng block đầu vào so với đầu ra. Nếu tỷ lệ hoàn thành < 100% hoặc có block bị thiếu, script sẽ cảnh báo vị trí chính xác cần bổ sung.*

Kiểm tra cú pháp và độ hoàn thiện 3 ngôn ngữ:
```bash
python <skill_dir>/scripts/validate_json.py --input "<process_dir>/merged_ejv.json"
```

### 📌 Bước 5: Xuất bản tài liệu đa định dạng

#### 1. Xuất file Word DOCX từng ngôn ngữ:
```bash
# Tiếng Việt (chuẩn hành chính):
python <skill_dir>/scripts/build_docx.py --input "<process_dir>/merged_ejv.json" --output "<output_dir>/[Ten]_vi.docx" --lang vn --style administrative

# Tiếng Anh (chuẩn quốc tế):
python <skill_dir>/scripts/build_docx.py --input "<process_dir>/merged_ejv.json" --output "<output_dir>/[Ten]_en.docx" --lang en --style standard

# Tiếng Nhật:
python <skill_dir>/scripts/build_docx.py --input "<process_dir>/merged_ejv.json" --output "<output_dir>/[Ten]_ja.docx" --lang ja --style standard
```

#### 2. Xuất Bảng đối chiếu Markdown (Parallel View):
```bash
python <skill_dir>/scripts/build_markdown.py --input "<process_dir>/merged_ejv.json" --output "<output_dir>/[Ten]_tam_ngu_parallel.md" --mode parallel
```

---

## ⚠️ Quy tắc dịch bất biến (Golden Rules)

1. **Anti-Token Overflow**: Tuyệt đối KHÔNG cố dịch toàn bộ văn bản dài trong một prompt duy nhất. Bắt buộc sử dụng quy trình phân lô `chunk_manager` và checkpoint.
2. **Zero Meaning Loss & Zero Text Skipping**: Không được tóm tắt, không được bỏ qua điều khoản/đoạn văn nào.
3. **Preserve Identifiers & Numbers**: Giữ nguyên mã hiệu văn bản (Nghị định 37/2026/NĐ-CP), số liệu, ngày tháng, tên riêng, URL, thông số kỹ thuật.
4. **Symmetrical Structure**: Cả 3 ngôn ngữ phải có cùng số lượng phần tử mảng trong `ul`, `ol` và cùng số hàng/cột trong `table`.

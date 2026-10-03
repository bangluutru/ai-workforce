# Nguồn Tra cứu & Chiến lược Tìm kiếm

> **Mục đích:** Danh sách nguồn chính thống để tra cứu VBQPPL VN + cú pháp tìm kiếm hiệu quả + cách xác minh nhanh.

---

## 1. Nguồn Chính thống (thứ tự ưu tiên khi lấy NGUYÊN VĂN)

> Kiểm ngày 2026-10-02 bằng HTTP GET không đăng nhập. Nguồn "tải được" là nguồn script `fetch_vn_source.py` lấy được toàn văn.

| Ưu tiên | Nguồn | URL | Tải tự động | Ghi chú |
|---|---|---|---|---|
| 1 | **Công báo Chính phủ** | congbao.chinhphu.vn | ✅ trang văn bản có file .pdf/.docx/.doc đính kèm (VD `congbao.chinhphu.vn/van-ban/luat-so-59-2020-qh14-31674.htm`) | Văn bản chính thức; có "Sơ đồ văn bản", "Thuộc tính văn bản" |
| 2 | **Hệ thống văn bản Chính phủ** | vanban.chinhphu.vn | ⚠️ trang hiển thị; file đính kèm tùy văn bản | Dùng để tìm số hiệu, ngày ban hành |
| 3 | **CSDL quốc gia về VBQPPL (Bộ Tư pháp)** | vbpl.vn | ❌ nội dung tải bằng JavaScript | Xem bằng trình duyệt; có "Lược đồ", "Hiệu lực" |
| 4 | Cổng Đăng ký doanh nghiệp | dangkykinhdoanh.gov.vn | ✅ | Thủ tục, biểu mẫu đăng ký DN |
| 5 | Cổng bộ, ngành | mof.gov.vn (Tài chính, gồm KH&ĐT cũ), moha.gov.vn (Nội vụ, gồm Lao động cũ), mae.gov.vn (Nông nghiệp và Môi trường, gồm TN&MT cũ), moj.gov.vn, bocongan.gov.vn, moc.gov.vn | ✅ trang tin | molisa.gov.vn, monre.gov.vn không còn truy cập được (bộ đã hợp nhất 03/2025) |
| Chỉ để tìm số hiệu | thuvienphapluat.vn, luatvietnam.vn | ❌ 403 (Cloudflare) với công cụ tải | KHÔNG dùng làm nguồn trích dẫn; dùng search_web để tìm số hiệu, ngày hiệu lực, VB sửa đổi rồi lấy nguyên văn ở Công báo |
| Không dùng | blog kế toán, công ty luật, báo | | | Chỉ gợi ý từ khóa; mọi trích dẫn phải từ nguồn ưu tiên 1-3 |

### Giao thức khi nguồn bị chặn (403) hoặc không có nội dung

1. Chạy `fetch_vn_source.py` với trang Công báo của cùng văn bản (tìm bằng `search_web: site:congbao.chinhphu.vn "<số hiệu>"`).
2. Nếu vẫn mã thoát 3/4: thử `site:vanban.chinhphu.vn "<số hiệu>"` hoặc PDF trên cổng bộ ngành.
3. Nếu tất cả thất bại và trích dẫn quyết định kết luận: **xin người dùng file PDF/DOCX văn bản** (đây là lúc DUY NHẤT được dừng hỏi giữa chừng), rồi chạy `fetch_vn_source.py --file` (PDF/DOCX/DOC/ODT/RTF/HTML/TXT; exit 2 = mật khẩu/hỏng, 5 = bản scan: không dùng nháp OCR làm nguồn).
4. Nếu người dùng không có file: vẫn hoàn thành báo cáo, nhưng mọi trích dẫn của văn bản đó ghi `[CẦN XÁC MINH: chưa đối chiếu nguyên văn - nguồn bị chặn]`, không đặt trong ngoặc kép như nguyên văn, không gắn `[XÁC ĐỊNH]`.

---

## 2. Cú pháp Tìm kiếm

### Tìm VB theo keyword (search_web)

```
site:congbao.chinhphu.vn "[số hiệu VB]"
site:vanban.chinhphu.vn "[tên luật]"
site:thuvienphapluat.vn "[keyword chính]" "[năm]"      # chỉ để tìm số hiệu/hiệu lực
site:thuvienphapluat.vn "[tên luật]" "điều [X]"
site:thuvienphapluat.vn "[số hiệu VB]"
```

### Tìm VB sửa đổi

```
site:thuvienphapluat.vn "sửa đổi" "[số hiệu VB gốc]"
site:thuvienphapluat.vn "thay thế" "[số hiệu VB gốc]"
site:thuvienphapluat.vn "bãi bỏ" "[số hiệu VB gốc]"
```

### Tìm NĐ hướng dẫn Luật

```
site:thuvienphapluat.vn "quy định chi tiết" "[tên luật]" "nghị định"
site:thuvienphapluat.vn "hướng dẫn thi hành" "[số hiệu luật]"
```

### Tìm VB theo lĩnh vực + thời gian

```
site:thuvienphapluat.vn "[lĩnh vực]" "2025" "nghị định"
site:thuvienphapluat.vn "[lĩnh vực]" "có hiệu lực" "2025"
```

### Đọc nội dung VB cụ thể (read_url_content)

Không đọc toàn văn bằng `read_url_content` trên thuvienphapluat.vn (403). Lưu toàn văn chính thống bằng script (chạy từ workspace AIWF):
```
python3 .agents/skills/tu-van-phap-luat/scripts/fetch_vn_source.py \
    --url "https://congbao.chinhphu.vn/van-ban/luat-so-59-2020-qh14-31674.htm" \
    --out-dir "<research_dir>/sources" --name luat-59-2020-qh14
```
File `<research_dir>/sources/<name>.txt` là `source` cho claims.json của evidence_verifier.

---

## 3. Xác minh Nhanh Hiệu lực

Trước khi trích dẫn bất kỳ VB nào, PHẢI kiểm tra hiệu lực:

### Trên Công báo / CSDL quốc gia (thuvienphapluat.vn nếu xem bằng trình duyệt)

1. Mở trang VB → nhìn **banner đầu trang**:
   - 🟢 "Còn hiệu lực" → OK, dùng được
   - 🟡 "Hết hiệu lực một phần" → Cần kiểm tra điều/khoản nào hết
   - 🔴 "Hết hiệu lực" → KHÔNG dùng (trừ khi mốc user nằm trước ngày hết hiệu lực)

2. Tab **"Lịch sử hiệu lực"** → xem timeline:
   - Ngày ban hành
   - Ngày có hiệu lực
   - Ngày bị sửa đổi / thay thế (nếu có)

3. Mục **"Văn bản liên quan"** → kiểm tra:
   - "Văn bản sửa đổi": VB nào đã sửa VB này?
   - "Văn bản thay thế": VB nào thay thế VB này?
   - "Văn bản được hướng dẫn": VB này hướng dẫn cái gì?

---

## 4. Cách đọc Số hiệu VB

Hiểu số hiệu giúp nhanh chóng phân loại VB:

| Pattern | Ý nghĩa | Ví dụ |
|---|---|---|
| `xx/yyyy/QHzz` | Luật, kỳ họp QH khóa zz | 45/2019/QH14 (BLLĐ 2019) |
| `xx/yyyy/NĐ-CP` | Nghị định Chính phủ | 145/2020/NĐ-CP |
| `xx/yyyy/TT-[Bộ]` | Thông tư của Bộ | 10/2021/TT-BXD |
| `xx/QĐ-TTg` | Quyết định Thủ tướng | 1579/QĐ-TTg |
| `xx/yyyy/QĐ-UBND` | Quyết định UBND | 15/2024/QĐ-UBND |

- **xx**: Số thứ tự VB
- **yyyy**: Năm ban hành
- **QHzz**: Quốc hội khóa zz (VD: QH15 = khóa 15, 2021-2026)
- **CP**: Chính phủ
- **TTg**: Thủ tướng
- **[Bộ]**: Tên viết tắt Bộ ban hành (BXD, BTC, BGTVT...)

---

## 5. Red Flags — Dấu hiệu Nguồn Không Đáng Tin

| Red flag | Hành động |
|---|---|
| Blog/website cá nhân trích dẫn luật không kèm số hiệu | Tra lại trên TVPL để xác minh |
| VB trên trang không chính thống, không có banner hiệu lực | Bỏ qua, tìm trên TVPL |
| Nội dung VB không có ngày hiệu lực | Kiểm tra trên congbao.chinhphu.vn |
| Kết quả search cho bài viết "phân tích" thay vì VB gốc | Dùng bài phân tích làm gợi ý keyword, nhưng trích dẫn phải từ VB gốc |
| VB có format cũ (trước 2015) mà không có bản cập nhật | Kiểm tra đã bị thay thế chưa |

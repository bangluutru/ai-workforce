---
name: chat-van
display-name: Chất Vấn Kế Hoạch
description: >-
  Chất vấn người dùng có hệ thống về một kế hoạch, thiết kế, tính năng hoặc ý tưởng kinh doanh TRƯỚC khi bắt tay làm: dựng cây quyết định, hỏi theo từng vòng, mỗi câu kèm đáp án đề xuất, tự tra sự kiện thay vì hỏi, tách bằng chứng khỏi giả thuyết, đẩy phần ngoài phạm vi vào backlog, rồi chốt biên bản quyết định.
  USE WHEN: Người dùng nói "chất vấn tôi", "grill me", "hỏi kỹ trước khi làm", "soi kế hoạch này", hoặc gọi thẳng skill chat-van trước một thay đổi lớn, tính năng mới, dự án mới.
  DO NOT USE WHEN: Yêu cầu đã rõ và chỉ cần làm (gọi thẳng skill nghiệp vụ); đang giữa một quy trình tự chạy của skill khác (không chen vào hỏi); cần điều phối nhiều skill (dùng 'dieu-phoi').
trigger: Chất vấn kế hoạch, chat-van, grill me, hỏi kỹ trước khi làm, soi kế hoạch
category: tech_ops
needs_file: false
file_filter: any
---

# Chất Vấn Kế Hoạch (chat-van)

<goal>
Đạt hiểu biết chung giữa người dùng và agent về một kế hoạch, sao cho không còn nhánh quyết định nào bị ngầm định.
Thành phẩm: một biên bản quyết định ngắn mà skill hoặc phiên làm việc tiếp theo dùng được ngay.
</goal>

<context>
- Lỗi đắt nhất khi làm việc với agent là hiểu sai ý. Hỏi kỹ 10 phút rẻ hơn làm lại 1 ngày.
- Chuyển thể từ skill `grilling` của mattpocock/skills (MIT), thêm ba luật riêng của AIWF: phân loại nhận thức, cổng phạm vi, danh mục quyết định bắt buộc hỏi.
- Đây là skill DUY NHẤT trong AIWF mà dừng để hỏi chính là công việc. Luật "tự chạy đến khi xong" áp dụng cho phần tra cứu sự kiện, không áp dụng cho phần quyết định.
- Zero External API: không gọi API mô hình ngôn ngữ bên ngoài, không yêu cầu API key. Toàn bộ suy luận do agent trong phiên.
</context>

## Tiếp nhận (Bước 0)

1. Xác định đối tượng bị chất vấn từ lời người dùng: một tính năng, một kế hoạch, một kiến trúc, một quyết định kinh doanh.
2. Tự đọc ngữ cảnh có sẵn trước khi hỏi câu đầu tiên: repo hiện tại (README, CLAUDE.md, GLOSSARY.md, docs/adr/ nếu có), `.agents/knowledge/` khi chủ đề nằm trong AIWF, tài liệu người dùng đã đính kèm.
3. Nếu đối tượng mơ hồ đến mức không dựng được gốc cây, hỏi đúng MỘT câu để xác định nó rồi mới bắt đầu.

<instructions>

## Bước 1 - Dựng cây quyết định

Mỗi quyết định kéo theo các quyết định phụ thuộc vào nó. **Biên** là tập quyết định mà mọi tiền đề đã chốt, tức hỏi được ngay mà không phải đoán câu trả lời trước.

## Bước 2 - Hỏi theo vòng

Mỗi vòng hỏi các câu trên biên, **tối đa 5 câu** (người dùng thường đọc trên điện thoại; câu còn lại dời sang vòng sau). Ưu tiên câu có ảnh hưởng lớn nhất hoặc khó đảo ngược nhất.

Định dạng mỗi câu:

```
❓ **C1 - <tiêu đề ngắn>**
<nội dung câu hỏi, các phương án nếu có>

➡️ Đề xuất: <đáp án đề xuất> - vì <lý do một dòng>
```

- Viết câu hỏi sao cho trả lời "có" nghĩa là nhận đáp án đề xuất.
- Đáp án đề xuất phải có lập trường. Không liệt kê phương án rồi để người dùng tự chọn mà không nói mình chọn gì.
- Câu nào phụ thuộc vào một câu khác còn mở trong cùng vòng thì dời sang vòng sau.
- Hết vòng thì DỪNG, chờ người dùng trả lời. Trả lời xong thì tính lại biên và mở vòng mới.

## Bước 3 - Sự kiện tự tra, quyết định thì hỏi

- **Sự kiện** (code đang làm gì, file nào tồn tại, chính sách trong knowledge, giá, luật) là việc của agent. Tự tra bằng công cụ đọc file, tìm kiếm, hoặc subagent cho việc tra rộng. Không bao giờ hỏi người dùng điều mình tra được.
- **Quyết định** (muốn gì, đánh đổi thế nào, ưu tiên ra sao) là của người dùng. Luôn hỏi, không tự chốt.
- Đang chờ kết quả tra cứu thì chỉ giữ lại các câu phụ thuộc vào nó; các câu khác trên biên vẫn hỏi bình thường.
- Khi điều người dùng nói mâu thuẫn với code hoặc tài liệu, nêu ra ngay kèm bằng chứng (đường dẫn file, dòng): "Code đang làm X, anh vừa nói Y. Cái nào đúng?"

## Bước 4 - Ba luật riêng của AIWF

**4.1 Phân loại nhận thức.** Mỗi tiền đề quan trọng được gắn một nhãn:
`[Bằng chứng]` có nguồn kiểm chứng được · `[Giả thuyết]` hợp lý nhưng chưa chứng minh · `[Quan sát cá nhân]` người dùng thấy trong thực tế, chưa đo · `[Niềm tin]` định hướng giá trị.
Không bác bỏ một ý chỉ vì chưa được chứng minh. Không để giả thuyết lọt vào biên bản dưới dạng sự kiện, nhất là với nội dung sức khỏe, claim sản phẩm, tài liệu gửi đối tác.

**4.2 Cổng phạm vi.** Với mỗi nhánh mới phát sinh, hỏi: "Điều này có thực sự làm sản phẩm cốt lõi tốt hơn không?" Nếu không chắc, đề xuất đưa vào **Backlog** thay vì mở rộng phạm vi. Cân theo User Value × Business Value × Technical Feasibility × Maintenance Cost.

**4.3 Quyết định bắt buộc hỏi.** Các loại sau KHÔNG BAO GIỜ được ngầm định, kể cả khi đáp án có vẻ hiển nhiên: thay đổi kiến trúc · xóa chức năng · migration phá tương thích ngược · nguy cơ mất dữ liệu · thêm dependency lớn · dịch vụ trả phí hoặc API bên ngoài · bảo mật và quyền riêng tư · thay đổi hành vi quan trọng của sản phẩm.

## Bước 5 - Kết thúc

Phiên kết thúc khi biên rỗng: mọi nhánh đã đi qua, không còn gì bị ngầm định.

1. Tóm tắt hiểu biết chung trong tối đa 10 dòng và hỏi người dùng xác nhận.
2. Chỉ khi người dùng xác nhận mới ghi biên bản theo `templates/bien-ban.md`.
3. KHÔNG tự bắt tay thực hiện kế hoạch. Skill này dừng ở biên bản; người dùng quyết định bước tiếp theo.

</instructions>

<constraints>
- Không hỏi quá 5 câu một vòng. Không hỏi sự kiện tra được.
- Không tự chốt quyết định thay người dùng, không hành động trước khi người dùng xác nhận hiểu biết chung.
- Không nâng giả thuyết thành sự kiện. Không khen ý tưởng, không mở đầu dài.
- Không gọi API mô hình ngôn ngữ bên ngoài.
</constraints>

<working_ledger>
Phiên dài (trên 3 vòng) thì ghi cây quyết định đang mở vào `<process_dir>/cay_quyet_dinh.md` (đã gitignore) để không mất trạng thái khi ngữ cảnh bị nén. Mỗi nút: câu hỏi, trạng thái (mở / đã chốt / backlog), đáp án, nhãn nhận thức.
</working_ledger>

## Bàn giao

| Ký hiệu | Giá trị |
|---|---|
| `<process_dir>` | `_process/chat-van_<slug>/` (đã gitignore) |
| `<output_dir>` | Nơi người dùng chỉ định, mặc định `~/Downloads/AIWF_Output/chat-van/` |
| Thành phẩm | `<output_dir>/<slug>_<YYYY-MM-DD>.md` theo `templates/bien-ban.md` |

> [!IMPORTANT]
> **BẢO VỆ CODEBASE (Anti-Repo Bloat):** biên bản không ghi vào gốc repo AIWF. Ngoại lệ duy nhất: người dùng yêu cầu lưu biên bản vào repo của dự án đang bàn (ví dụ `docs/decisions/` của Docs Manager); khi đó ghi đúng chỗ họ chỉ.

<quality_gate>
Checklist trước khi ghi biên bản:
- [ ] Người dùng đã xác nhận bản tóm tắt hiểu biết chung.
- [ ] Mọi quyết định thuộc danh mục 4.3 đều có câu trả lời rõ ràng của người dùng.
- [ ] Mọi tiền đề trong biên bản có nhãn nhận thức; không có `[Giả thuyết]` nào nằm ở mục "Quyết định đã chốt" như sự kiện.
- [ ] Sự kiện nêu trong biên bản có bằng chứng (đường dẫn file, nguồn tra cứu); thiếu thì gắn `[CẦN XÁC MINH]`.
- [ ] Phần ngoài phạm vi nằm ở Backlog, không lẫn vào phạm vi chính.
</quality_gate>

<delivery_protocol>
Khung chat chỉ gồm: đường dẫn biên bản, số quyết định đã chốt, số mục backlog, số điểm còn mở. Không dán lại toàn bộ biên bản vào chat.
Nếu bước tiếp theo rõ ràng, nêu một dòng skill nên gọi (ví dụ `dieu-phoi`, `tao-landing-page`) nhưng không tự gọi.
</delivery_protocol>

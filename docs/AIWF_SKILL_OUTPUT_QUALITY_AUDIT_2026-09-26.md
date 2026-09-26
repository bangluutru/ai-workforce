# Báo cáo rà soát nguyên nhân ảnh hưởng chất lượng đầu ra của AI Workforce Skills

**Ngày rà soát:** 26/09/2026  
**Phạm vi:** 16 thư mục skill trong `.agents/skills/`, quy tắc R3–R6, registry, extension scanner, `scripts/audit_skill.py`, `scripts/claim_guard.py` và chứng nhận hiện có.  
**Mục đích:** Gửi cho Antigravity để chỉnh các nguyên nhân gốc có khả năng làm skill bị gọi nhầm, không chạy đủ bước hoặc tự đánh giá chất lượng cao hơn thực tế.

## Tóm tắt điều hành

Có các nguyên nhân hệ thống, không chỉ lỗi riêng từng skill:

1. **Chuẩn metadata của repo đang coi nhiều trường tùy chỉnh như tính năng native của Antigravity.** Theo tài liệu Antigravity hiện hành, manifest skill dùng `name` và `description`; `description` là phần Agent nhìn thấy để quyết định gọi skill. Các trường `trigger`, `allowed-tools`, `effort`, `context`, `interaction-mode` và `trigger_keywords` không nằm trong danh sách trường manifest đó. Một số trường được extension riêng đọc, nhưng không nên giả định Agent Antigravity cũng dùng chúng để cấp quyền, tạo subagent hay chọn luồng. [Tài liệu Agent Skills của Antigravity](https://www.antigravity.google/docs/skills?tab=ide)
2. **Các skill bị chồng lấn và danh mục không khớp.** Có 16 skill thật nhưng ba registry vẫn ghi 15 và không liệt kê `video-studio`. Người dùng nói “làm landing page” có thể rơi vào `thiet-ke` hoặc `tao-landing-page`; yêu cầu video có thể rơi vào `phu-de`, `long-tieng`, `video-studio` hoặc `hand-drawn-animation`.
3. **Công cụ chứng nhận không đo chất lượng đầu ra.** `audit_skill.py` chấm điểm chủ yếu bằng cách tìm từ khóa và kiểm tra cú pháp; không chạy quy trình thật, không đánh giá file cuối. Chạy `--all --quiet` cho thấy 14 skill được điểm 96–100, hai skill mới đạt 44/47 và `_shared` bị tính nhầm như một skill, khiến toàn bộ lệnh trả mã lỗi.
4. **Một số quality gate tự mâu thuẫn hoặc kiểm tra thiếu điều đã hứa.** `dich-giu-dinh-dang` vừa yêu cầu không sót bất kỳ khối nguồn nào vừa chấp nhận điểm kiểm tra từ 95%; `thiet-ke` hứa đủ trạng thái `loading`, `empty`, `error` nhưng checklist chỉ kiểm `hover`, `focus`, `active`.
5. **Chế độ tự chạy và quy trình hỏi người dùng chưa được phân định theo loại việc.** Skill thuế luôn mở wizard hỏi tuần tự, dù người dùng có thể đã cung cấp thông tin; trong khi nội dung trực quan cần vòng xem bản nháp nhưng nhiều skill lại tuyên bố chạy một mạch đến thành phẩm.
6. **Quy tắc “không API bên ngoài” mâu thuẫn với công việc cần API sản phẩm.** `video-studio` cần API key Pexels/Pixabay; `tao-landing-page` phải giao tiếp API của Landing Hub. Nếu giữ nguyên lệnh cấm tổng quát, agent có thể bỏ qua bước tích hợp hoặc hướng dẫn sai về khả năng chạy.

Các điểm trên có thể giải thích việc một số skill hoạt động tốt còn một số cho kết quả kém: chất lượng phụ thuộc vào skill được chọn, phần hướng dẫn nào thực sự được runtime hiểu, dữ liệu đầu vào đã đủ hay chưa, và bộ kiểm tra có khả năng phát hiện lỗi đầu ra hay không.

## Phạm vi và giới hạn

- Đã rà soát cấu trúc và metadata của cả 16 `SKILL.md`, quy tắc vận hành, registry, mã scanner của extension và hai script kiểm định nội dung/chứng nhận.
- Đã chạy `python3 scripts/audit_skill.py --all --quiet` ở chế độ không cấp/chỉnh chứng nhận để xem tình trạng bộ chấm điểm.
- **Chưa chạy 16 quy trình từ đầu đến cuối** trên bộ dữ liệu mẫu chuẩn. Vì vậy các kết luận về tác động tới thành phẩm là nguyên nhân có bằng chứng trong chỉ dẫn/mã và nguy cơ hợp lý; cần thêm bộ kiểm thử mẫu để đo mức cải thiện sau sửa.

## Phát hiện ưu tiên cao

### P1 — Metadata native và metadata riêng của extension đang bị trộn lẫn

**Bằng chứng trong repo**

- R4 mô tả `trigger`, `argument-hint`, `allowed-tools`, `effort`, `interaction-mode`, `context`, `needs_file`, `file_filter` như hợp đồng frontmatter cho Agent và router: `.agents/rules/R4-skill-standard-v1.md:70-87`.
- R3 nói `context: fork` sẽ khởi chạy skill trong subagent: `.agents/rules/R3-operational-discipline.md:59-64`.
- Tài liệu Antigravity đang công bố `name` và `description`; phần discovery dùng tên và mô tả để quyết định gọi skill. Một số tính năng về tools/subagents thuộc cấu hình custom agent riêng, không phải các field native đã nêu cho skill. [Agent Skills](https://www.antigravity.google/docs/skills?tab=ide), [Custom Agents](https://antigravity.google/blog/introducing-custom-agents)
- Extension riêng có đọc `trigger`, `needs_file`, `file_filter`, `display-name` tại `extension/lib/scanner.js:77-97`; không thấy scanner xử lý `allowed-tools`, `effort`, `context` hay `trigger_keywords`.
- Hai skill mới có metadata khác bộ còn lại: `hand-drawn-animation/SKILL.md:1-15` dùng `name: Tạo Hoạt Hình` và `trigger_keywords`; `video-studio/SKILL.md:1-14` dùng `name: Tạo Video`, `context: main`, `trigger_keywords`.

**Ảnh hưởng có thể xảy ra**

- Từ khóa trong `trigger` không phải cơ chế định tuyến native được tài liệu công bố; Agent dựa chủ yếu vào `description`. Mô tả quá rộng hoặc có nhiều chức năng dễ khiến skill không được gọi, hoặc được gọi nhầm.
- `context: fork` không đảm bảo tự tạo subagent; `allowed-tools` không đảm bảo quyền công cụ hoặc tránh hộp thoại xác nhận. Skill xử lý tài liệu dài có thể vẫn chạy trên phiên chính, còn skill cần lệnh có thể bị dừng ở bước quyền.
- `trigger_keywords` của animation/video không được extension scanner dùng để tạo lệnh kích hoạt; scanner chỉ lấy `meta.trigger` rồi mới dùng câu mặc định.
- `name` hiển thị tiếng Việt có thể không phù hợp vai trò định danh/slash command. Tài liệu Antigravity khuyến nghị tên kỹ thuật dạng chữ thường, nối bằng dấu gạch ngang.

**Đề nghị sửa**

1. Tách rõ **manifest native** (`name`, `description`) và **metadata AIWF extension**. Không chấm điểm hay hứa chức năng native dựa trên field tùy chỉnh.
2. Dùng `name` trùng slug thư mục (`video-studio`, `hand-drawn-animation`); giữ nhãn tiếng Việt trong `display-name` nếu extension cần.
3. Với nhu cầu subagent hoặc giới hạn tools, cấu hình đúng bằng custom agent/runtime tương ứng; nếu không khả dụng, viết quy trình fallback rõ trong thân skill.
4. Kiểm tra thực tế trong Antigravity Customizations/skill list và thử lệnh `/skill-name` trên phiên bản đang dùng trước khi ghi rằng metadata có hiệu lực.

### P1 — Router mơ hồ và registry thiếu skill

**Bằng chứng**

- `.agents/rules/AGENTS.md:71-90`, `GEMINI.md:54-77` và `README.md:105-125` đều ghi danh mục 15 skill.
- Cây `.agents/skills/` có 16 skill mang `SKILL.md`, gồm cả `video-studio`; ba registry không liệt kê skill này. `.agents/skills/.certified.json` hiện chỉ có 14 mục chứng nhận.
- `thiet-ke` nhận các yêu cầu “landing page”, “làm giao diện web”, UI/UX: `.agents/skills/thiet-ke/SKILL.md:1-5,46-52`.
- `tao-landing-page` cũng nhận “tạo landing page”, “làm landing page”: `.agents/skills/tao-landing-page/SKILL.md:1-5`.
- Các chức năng video/voice/subtitle xuất hiện ở cả `phu-de`, `long-tieng`, `video-studio`, `hand-drawn-animation`.

**Ảnh hưởng có thể xảy ra**

Khi user chỉ nói “làm landing page”, router không biết nên tạo HTML thiết kế nhanh hay một dự án React production-ready có Stitch/Figma và Landing Hub. Khi yêu cầu “làm video”, agent có thể chọn dựng video stock thay vì phụ đề, lồng tiếng hoặc hoạt hình. Skill không phù hợp thường dẫn tới đầu ra đúng định dạng nhưng sai mục đích.

**Đề nghị sửa**

- Tạo một bảng quyết định dùng **loại đầu vào + thành phẩm mong muốn**, không chỉ từ khóa: Stitch/Figma → `tao-landing-page`; trang/ấn phẩm tạo mới → `thiet-ke`; subtitle → `phu-de`; lồng tiếng → `long-tieng`; video stock từ ý tưởng → `video-studio`; hoạt hình vẽ tay → `hand-drawn-animation`.
- Thêm ưu tiên cho skill chuyên biệt trước skill tổng quát (`bao-cao-kt` trước `xu-ly-van-phong` khi yêu cầu là mô hình số liệu; skill xử lý văn phòng là fallback).
- Đồng bộ một registry duy nhất từ các thư mục có `SKILL.md`; không duy trì danh sách đếm tay ở ba tài liệu.
- Viết description ngắn, cụ thể, nêu rõ “dùng khi” và “không dùng khi”. Tài liệu Antigravity cũng khuyên skill nên tập trung một việc, description cụ thể và thêm decision tree cho skill phức tạp. [Best practices](https://www.antigravity.google/docs/skills?tab=ide)

### P1 — `audit_skill.py` chứng nhận cấu trúc, không chứng nhận kết quả

**Kết quả quan sát**

| Nhóm khi chạy `--all` | Kết quả |
|---|---:|
| Skill có điểm PASS | 14/16, trong đó phần lớn đạt 100; `long-tieng` đạt 96 |
| Skill FAIL | `hand-drawn-animation` 47; `video-studio` 44 |
| Thư mục không phải skill bị tính vào | `_shared` 0, do thiếu `SKILL.md` |
| Exit code toàn lệnh | 1 |

**Bằng chứng trong mã**

- Điểm quality gate cộng điểm khi thấy từ khóa như `Checklist`, `Confidence Flagging`, `Anti-AI`, `Clean Delivery`: `scripts/audit_skill.py:259-287`.
- Tầng code kiểm tra cú pháp Python/JavaScript, không chạy quy trình hay kiểm tra file đầu ra: `scripts/audit_skill.py:233-256`.
- Bộ mẫu API cấm chỉ gồm vài regex cố định: `scripts/audit_skill.py:32-41`.
- Hash chứng nhận chỉ lấy `.md`, `.py`, `.js`, `.json`, `.sh`, nên thay đổi CSS/HTML/ảnh hoặc tài nguyên nhị phân không làm đổi hash: `scripts/audit_skill.py:43-55`.
- `--all` và `--scan-new` duyệt mọi thư mục con không bắt đầu bằng dấu chấm, không kiểm tra có `SKILL.md` trước khi đưa vào danh sách: `scripts/audit_skill.py:356-369`; `_shared` vì vậy thành mục FAIL và ngăn `--certify` chạy thành công: `scripts/audit_skill.py:377-396`.
- Chứng nhận ghi ngày cố định `2026-09-03`, bất kể ngày chạy: `scripts/audit_skill.py:384-388`.

**Ảnh hưởng**

Một skill có đủ từ khóa “Quality Gate” có thể đạt điểm cao dù gate không kiểm tra đầu ra. Ngược lại, skill mới/không theo mẫu sẽ bị điểm thấp do thiếu từ khóa, không nhất thiết do sản phẩm xấu. Hơn nữa, kiểm tra cú pháp không phát hiện lỗi phụ thuộc, lệnh sai, sai định tuyến hoặc output bị lỗi.

**Đề nghị sửa**

- Chỉ duyệt thư mục chứa `SKILL.md`; loại `_shared` khỏi cả `--all` và `--scan-new`.
- Dùng parser YAML chuẩn, kiểm tra cú pháp và schema; không dùng việc “có từ khóa” làm điểm chất lượng.
- Chứng nhận tách hai trạng thái: **prompt/schema hợp lệ** và **đã qua kiểm thử đầu ra**.
- Thêm bộ case cố định cho từng skill: input đại diện, expected properties, chấm theo checklist/domain expert. Kiểm tra đúng file, nội dung, layout, công thức, media playback và nguồn trích dẫn tùy loại output.
- Đưa `.html`, `.css`, `.svg`, `.toml`, `.yml`, lockfile và asset liên quan vào fingerprint; ghi thời gian thực thay vì ngày cố định.

### P1 — Quality gate mâu thuẫn và thiếu kiểm tra đầu ra cụ thể

**Ví dụ có bằng chứng trực tiếp**

- `verify_retention.py` được gọi là cổng phát hiện văn bản nguồn còn sót, nhưng mã chỉ dùng regex CJK và chỉ đánh dấu block có từ 3 ký tự CJK trở lên: `scripts/verify_retention.py:61-62,425-436`. Quy tắc R3 lại yêu cầu phát hiện cả câu tiếng Anh chưa dịch: `.agents/rules/R3-operational-discipline.md:75-80`. Các kiểm tra CJK residual và Composite Retention Score là hai chỉ số riêng; ngưỡng 95% của `dich-giu-dinh-dang` không tự nó mâu thuẫn với hard blocker 0 residual: `.agents/skills/dich-giu-dinh-dang/SKILL.md:156-164,211-217`.
- `thiet-ke` mô tả đủ 5 trạng thái `hover`, `focus`, `loading`, `empty`, `error`, nhưng quality gate chỉ rà `hover`, `focus`, `active`: `.agents/skills/thiet-ke/SKILL.md:48-52,100-110`.
- `scripts/claim_guard.py` đọc mọi đầu vào bằng `Path.read_text(..., errors="ignore")`: dòng 96; không có xử lý PDF/DOCX/PPTX/ảnh. Cảnh báo claim cần nguồn chỉ thêm vào `warnings`, trong khi kết quả trả về vẫn 0 nếu không bắt được từ khóa cấm: dòng 119-159.
- `R3` yêu cầu không còn dù chỉ một khối văn bản gốc trước khi bàn giao: `.agents/rules/R3-operational-discipline.md:75-80`.

**Ảnh hưởng**

Agent có thể báo PASS trong khi một phần nội dung chưa được kiểm dịch, trạng thái lỗi chưa được thiết kế, hoặc tuyên bố cần bằng chứng mới chỉ có warning. Với bộ quét residual hiện tại, dịch Anh → Việt có thể lọt câu tiếng Anh vì regex CJK không phát hiện; một cụm Nhật rất ngắn dưới 3 ký tự cũng không bị đánh dấu. Báo cáo “100% an toàn pháp lý” từ regex cũng vượt quá khả năng thực tế của một bộ lọc từ khóa.

**Đề nghị sửa**

- Mỗi điều kiện nghiệm thu phải có cách kiểm tra máy hoặc bằng mắt và một tiêu chí thống nhất. Không trộn điểm tổng hợp 95% với hard blocker 0 lỗi.
- Đối với tài liệu, tách lỗi OCR/layout, thiếu nội dung, thuật ngữ và phần cần giữ nguyên (tên riêng, mã số, công thức). Bộ residual cần biết ngôn ngữ nguồn/đích và so khớp block/translation map, không chỉ dò script CJK.
- Đổi `claim_guard` thành **keyword linter sơ bộ**; giải mã định dạng trước khi quét, làm rõ cảnh báo chưa có nguồn là trạng thái chưa đạt, không phải pass.
- Với web, chạy screenshot/viewport và kiểm các state mà skill thực sự hứa. Với audio/video, nghe/xem mẫu, kiểm đồng bộ và phát được file. Với workbook, kiểm công thức lẫn giá trị tính lại.
- Thay các cam kết “100% chính xác/không mất mát” bằng tiêu chí có thể kiểm chứng và nêu rõ giới hạn.

### P1 — Wizard hỏi quá nhiều và không ưu tiên dữ liệu user đã cung cấp

`tu-van-thue-tncn/SKILL.md:57-90` quy định cứ kích hoạt là hỏi câu gốc 6 chuyên đề, hỏi tuần tự từng câu và luôn hỏi ghi chú cuối. Quy trình này không nói rõ cách bỏ qua câu đã được trả lời trong prompt.

**Ảnh hưởng:** người dùng cung cấp sẵn mức lương, kỳ tính thuế và người phụ thuộc vẫn có thể bị đưa qua wizard từ đầu. Việc hỏi từng bước làm tăng độ dài hội thoại, gây mệt và làm chậm bước tra cứu/tính toán.

**Đề nghị sửa:** agent đọc và điền trước các trường đã có; chỉ hỏi các thông tin còn thiếu có thể làm đổi kết quả; gộp câu hỏi cần thiết thành một lượt; cho phép đi tiếp với giả định được đánh dấu khi thông tin không trọng yếu. Dùng wizard đầy đủ khi đề bài còn mơ hồ, không phải mặc định mỗi lần gọi skill.

## Phát hiện theo nhóm skill

| Skill | Vấn đề cụ thể cần Antigravity xem lại |
|---|---|
| `app-auditor` | Có điểm tốt là yêu cầu evidence theo route/viewport/steps/log. Giữ mẫu evidence này; bổ sung case pass/fail thật thay vì chỉ checklist. |
| `bao-cao-kt` | `100% Live Formulas` là yêu cầu bao trùm quá rộng; cần xác định rõ ô nào phải formula và chứng cứ reconcile nào phải lưu. Dễ đụng `xu-ly-van-phong` ở báo cáo/Excel. |
| `boc-tach-pdf` | Có nhiều bước OCR/layout và yêu cầu đối chiếu bảng; nên giữ. “100% Zero-Loss” cần thay bằng coverage/evidence đo được, không coi số trang OCR là bằng chứng nội dung đúng. |
| `chotto-newsroom` | Kết quả phụ thuộc công cụ search và ảnh. Cần fallback khi tool không có/nguồn chính thức chưa xác nhận; không chuyển trạng thái review thành đã xác minh chỉ vì đủ 11 bước. |
| `dich-giu-dinh-dang` | Ngưỡng composite và hard blocker là hai kiểm tra riêng, nhưng bộ residual hiện chỉ bắt CJK từ 3 ký tự; bổ sung detection theo ngôn ngữ nguồn để không lọt văn bản Latin/khối ngắn. |
| `ejv-translate` | Chunk/checkpoint là mẫu tốt cho tài liệu dài. Bổ sung review ngữ nghĩa/thuật ngữ theo mẫu và phân biệt “đã xử lý đủ block” với “dịch đúng nghĩa”. |
| `hand-drawn-animation` | Dùng `trigger_keywords` thay vì `trigger`, `name` là nhãn tiếng Việt; thiếu trong chứng nhận. Giữ quy trình render/review một shot mẫu (`SKILL.md:90-107`) vì đây là cổng feedback hữu ích. |
| `long-tieng` | Mô tả “local”/không API nhưng skill đề cập VieNeu-TTS và Edge-TTS; cần bảng rõ engine nào local, engine nào cần mạng, điều kiện chạy và fallback. Giữ kiểm soát atempo hai lượt và kiểm file output. |
| `phu-de` | Có editor preview, snapshot/undo và phân biệt local edit với AI edit; giữ vòng lặp này. Xác nhận các bước UI/API request tương ứng có runtime hỗ trợ, không chỉ dựa metadata. |
| `tao-landing-page` | Tích hợp Landing Hub là API nghiệp vụ cần thiết (`SKILL.md:71-79,93-99`), nhưng quy tắc Zero External API cấm chung (`R4:157-158`). Cần định nghĩa “cấm hosted LLM API” riêng với “cho phép API sản phẩm được yêu cầu”. Skill cũng chồng `thiet-ke`. |
| `thiet-ke` | Chồng `tao-landing-page`; checklist bỏ sót `loading`, `empty`, `error`. Nên giới hạn vai trò hoặc thêm router phân định HTML/ấn phẩm nhanh với app React tích hợp. |
| `tu-van-phap-luat` | Có quy trình thời điểm hiệu lực, đối chiếu văn bản và trích dẫn. Nên hỏi đúng dữ kiện quyết định kết quả thay vì áp dụng toàn bộ 5 trục như intake bắt buộc cho mọi câu hỏi đơn giản. |
| `tu-van-thue-tncn` | Wizard tuần tự áp dụng mặc định; thêm logic bỏ qua trường đã biết và chọn nhánh trực tiếp. Giữ tax calculator làm nguồn số học, nhưng yêu cầu dẫn điều khoản/phiên bản hiệu lực trong báo cáo. |
| `video-studio` | Bị bỏ khỏi registry, metadata không thống nhất; bắt buộc Pexels/Pixabay API keys trái với lời hứa zero key ở rules. SKILL.md chưa có checklist nghiệm thu video cuối tương xứng với pipeline one-click. |
| `viet-bai` | Description hứa “khử 100% dấu vết AI”; đây không phải kết quả kiểm chứng được. Đánh giá bằng nguồn, đối tượng, giọng điệu, độ cụ thể, cấu trúc nền tảng và yêu cầu người dùng; không chỉ bằng dấu câu. |
| `xu-ly-van-phong` | Là skill tổng quát, dễ tranh việc với `bao-cao-kt`, `boc-tach-pdf`, `ejv-translate`. Đặt quy tắc ưu tiên theo tác vụ chính và giữ scope office-format/fallback rõ ràng. |

## Các sửa đổi nên làm theo thứ tự

1. **Chuẩn hóa runtime contract và tên skill.** Tách metadata Antigravity khỏi metadata extension; sửa `name` của hai skill video/animation; kiểm tra thực tế tool/subagent trước khi hứa `allowed-tools` hoặc `context: fork`.
2. **Tạo router duy nhất và cập nhật tự động registry.** Chốt bảng quyết định cho landing/web, office/accounting, translate/OCR, video/subtitle/voice/animation. Thêm kiểm tra tự động phát hiện skill có folder nhưng vắng registry.
3. **Viết lại quality gate thành kiểm tra đầu ra.** Mỗi skill có 3–8 tiêu chí đo được, lệnh/visual review tương ứng, expected output và cách báo `PASS`, `WARN`, `FAIL`. Tách prompt compliance khỏi product correctness.
4. **Sửa `audit_skill.py` và `claim_guard.py`.** Không tính `_shared`, dùng parser YAML, fingerprint đủ asset, không pass chỉ vì có từ khóa, không cho claim warning qua gate, nhận diện đúng các định dạng file.
5. **Làm intake thích ứng.** Trích thông tin user đã đưa, hỏi gộp phần thiếu và dừng ở human checkpoint khi lựa chọn ảnh hưởng đáng kể đến kết quả hoặc cần duyệt bản nháp.
6. **Ghi rõ phụ thuộc và fallback.** Phân biệt API của mô hình AI, API sản phẩm, nguồn stock, TTS local/cloud, key bắt buộc/tùy chọn, chất lượng khi thiếu key và quyền sử dụng media/voice.
7. **Thay “Anti-AI 100%” bằng hướng dẫn biên tập theo ngữ cảnh.** Tránh cấm máy móc em dash/Oxford comma trên mọi ngôn ngữ và loại tài liệu; ưu tiên giọng tự nhiên, không sáo rỗng, đúng brand/platform và không thay đổi nội dung pháp lý.

## Mẫu yêu cầu gửi Antigravity

> Hãy sửa các nguyên nhân gốc trong báo cáo `docs/AIWF_SKILL_OUTPUT_QUALITY_AUDIT_2026-09-26.md`, ưu tiên metadata/router, `audit_skill.py`, `claim_guard.py`, các quality gate mâu thuẫn, wizard thuế và xung đột API. Trước tiên kiểm tra tài liệu Antigravity của phiên bản đang chạy; giữ riêng metadata native của SKILL.md với metadata của AIWF extension, không giả định field tùy chỉnh có tác dụng native. Tạo router có thứ tự ưu tiên và sinh registry từ các thư mục skill để tránh sai danh sách. Thay điểm kiểm định theo từ khóa bằng test case đầu vào/đầu ra có tiêu chí đo được; không tuyên bố PASS/100% nếu chỉ mới kiểm tra cú pháp hoặc regex. Intake phải bỏ qua thông tin user đã cung cấp và chỉ hỏi phần thiếu có ảnh hưởng kết quả. Nêu rõ API/TTS/stock nào local, bên ngoài, bắt buộc hay tùy chọn và có fallback gì. Giữ các điểm tốt hiện có như chunk/checkpoint cho tài liệu dài, evidence theo route/viewport của app-auditor, editor preview/undo của phu-de và render-review một shot mẫu của hand-drawn-animation. Chưa xóa hoặc thay đổi tài liệu nguồn nếu chưa đối chiếu behavior hiện hữu. Sau khi sửa, chạy các case đại diện cho từng nhóm skill và báo cáo kết quả thực tế, gồm failure còn lại.

## Tài liệu tham chiếu

- [Google Antigravity — Agent Skills](https://www.antigravity.google/docs/skills?tab=ide): manifest `name`/`description`, discovery qua description, progressive disclosure và best practices.
- [Google Antigravity — Custom Agents](https://antigravity.google/blog/introducing-custom-agents): cơ chế agent riêng, tool scope và subagent là một lớp cấu hình riêng.
- [Google Antigravity — Rules](https://www.antigravity.google/docs/rules/): frontmatter/triggers dành cho rule files, phân biệt với manifest của skill.

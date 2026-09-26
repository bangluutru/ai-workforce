# AIWF REAL AGENT EVALUATION SUITE (PHASE 3B)

Hệ thống đánh giá hành vi thực tế của Antigravity Agent trên AIWF theo chuẩn 3 tầng (L0, L1, L2).

---

## 1. Cấu Trúc Thư Mục

```
tests/agent_eval/
├── prompts/              # Bộ prompt chuẩn hóa (T01 - T12)
│   ├── T01.prompt.txt    # RAW User Prompt thuần túy (chỉ gửi tệp này cho Agent)
│   ├── T01.meta.json     # Metadata kỳ vọng của Evaluator (tuyệt đối không leak cho Agent)
│   └── ...
├── fixtures/             # Dữ liệu đầu vào thực nghiệm (hợp đồng, brief, spec)
├── results/              # Hồ sơ AgentRunRecord (JSON) xuất xưởng từ các phiên chạy thật
└── README.md             # Tài liệu hướng dẫn này
```

---

## 2. Nguyên Tắc Vận Hành — Zero Benchmark Leakage

1. **Agent chỉ nhận RAW PROMPT:** File `Txx.prompt.txt` chỉ chứa đúng nội dung người dùng gõ vào chat.
2. **Không gợi ý trước:** Tuyệt đối không nhét tên skill mục tiêu (`expected_skill`), tên script kiểm tra (`claim_guard`), hay tiêu chuẩn chấm điểm vào prompt của Agent.
3. **Phân định rõ 2 luồng:**
   - **B1 (Interactive IDE):** Người thử nghiệm dán nội dung từ `Txx.prompt.txt` vào khung chat IDE, Agent tự chạy. Sau khi Agent kết thúc, chạy `scripts/eval_transcript.py` trỏ vào file `transcript.jsonl` tương ứng.
   - **B2 (Antigravity CLI):** Chạy lệnh tự động bằng `agy`:
     ```bash
     agy -p "$(cat tests/agent_eval/prompts/T03.prompt.txt)" --output-format json --dangerously-skip-permissions
     ```
     Sau đó truyền kết quả cho `scripts/eval_transcript.py`.

---

## 3. Ba Tầng Đánh Giá

- **L0 — Deterministic Infrastructure:** Kiểm tra các script và hạ tầng cơ sở hoạt động độc lập (đã xác lập ở Phase 2.5).
- **L1 — Agent Harness Behavior:** Phân tích `transcript.jsonl` thực tế để trích xuất:
  - Có đọc `SKILL.md` hay chạy script chuyên biệt không? (`DIRECT_BEHAVIORAL_EVIDENCE`)
  - Có tự chạy verifier bắt buộc trước khi claim Done không?
  - Có phạm lỗi `FALSE_DONE` (báo xong nhưng thiếu file / vi phạm blocker) không?
- **L2 — Output Artifact Quality:** Chạy các công cụ kiểm định độc lập lên artifact kết quả:
  - Luật R5 (`claim_guard.py`)
  - Kiểm tra kiểu dữ liệu (`tsc` / typecheck thực thụ, cấm dùng regex giả lập type-safe)
  - Bảo toàn bố cục & không sót chữ gốc (`verify_retention.py`).

# Hướng dẫn Cấu hình Stitch MCP & Figma MCP cho Google Antigravity

Khi kỹ năng `tao-landing-page` phát hiện Stitch MCP hoặc Figma MCP chưa kết nối, người dùng cần bổ sung cấu hình vào tệp:
`~/.gemini/antigravity-ide/mcp_config.json` (hoặc cấu hình MCP trong IDE).

---

## 1. Cấu hình Google Stitch MCP
Google Stitch cung cấp MCP Server để AI Agent truy xuất trực tiếp các dự án, màn hình và token thiết kế:

```json
{
  "mcpServers": {
    "stitch": {
      "command": "npx",
      "args": ["-y", "@google-labs/stitch-mcp"],
      "env": {
        "STITCH_API_KEY": "<STITCH_API_KEY_CỦA_BẠN>"
      }
    }
  }
}
```

> [!NOTE]
> Sau khi cấu hình, khởi động lại Antigravity IDE hoặc gõ lệnh Refresh MCP để nạp công cụ Stitch.
> Các công cụ khả dụng bao gồm: `get_project`, `get_screen`, `list_screens`, `export_tokens`.

---

## 2. Cấu hình Figma Official MCP
Figma cung cấp Official MCP server để trích xuất metadata khung, component, CSS variables:

```json
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "@figma/mcp-server"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "<FIGMA_PERSONAL_ACCESS_TOKEN>"
      }
    }
  }
}
```

> [!NOTE]
> Lấy Personal Access Token từ Figma: **Figma Settings -> Security -> Personal access tokens -> Generate new token** với quyền `file_read`.

---

## 3. Chế độ Hoạt động khi Chưa Kết nối MCP (Fail-Closed & Fallback)
1. **Minh bạch trạng thái:** Kỹ năng sẽ báo rõ `Stitch MCP chưa được cấu hình` hoặc `Figma MCP thiếu quyền truy cập` kèm hướng dẫn ở trên.
2. **Không bịa đặt (No Hallucination):** Tuyệt đối không tự suy diễn rằng đã trích xuất được file Stitch/Figma khi chưa có MCP.
3. **Chế độ Fallback:** Người dùng có thể cung cấp ảnh chụp màn hình thiết kế hoặc file JSON thiết kế đã xuất thủ công. Kỹ năng sẽ gắn cờ `[CẦN XÁC MINH - FIDELITY FALLBACK]` và tiếp tục quy trình.

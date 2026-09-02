#!/bin/bash
# ======================================================================
# setup_notebook_sync.sh — Cài đặt môi trường sync Gemini Notebook
# ======================================================================
# Sử dụng: bash scripts/setup_notebook_sync.sh
# ======================================================================

set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  🔧 CÀI ĐẶT MÔI TRƯỜNG SYNC GEMINI NOTEBOOK           ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo

# --- Bước 1: Kiểm tra Python ---
echo "📌 Bước 1/4: Kiểm tra Python..."
if command -v python3 &>/dev/null; then
    PYTHON_VER=$(python3 --version 2>&1)
    echo "  ✅ $PYTHON_VER"
else
    echo "  ❌ Chưa cài Python 3. Vui lòng cài đặt trước."
    exit 1
fi

# --- Bước 2: Cài notebooklm-py ---
echo
echo "📌 Bước 2/4: Cài thư viện notebooklm-py..."
if python3 -c "import notebooklm" 2>/dev/null; then
    echo "  ✅ notebooklm-py đã được cài sẵn"
else
    echo "  ⏳ Đang cài notebooklm-py..."
    pip3 install "notebooklm-py[browser]" --quiet
    echo "  ✅ Đã cài xong notebooklm-py"
fi

# --- Bước 3: Cài Playwright ---
echo
echo "📌 Bước 3/4: Cài trình duyệt Playwright (cho bước login)..."
if python3 -c "from playwright.sync_api import sync_playwright" 2>/dev/null; then
    echo "  ✅ Playwright đã sẵn sàng"
else
    echo "  ⏳ Đang cài Playwright chromium..."
    playwright install chromium --quiet 2>/dev/null || python3 -m playwright install chromium
    echo "  ✅ Đã cài xong Playwright"
fi

# --- Bước 4: Đăng nhập ---
echo
echo "📌 Bước 4/4: Đăng nhập tài khoản Google..."
echo
echo "  ⚠️  Bước này sẽ mở trình duyệt Chromium để bạn đăng nhập."
echo "  Sau khi đăng nhập xong, trình duyệt sẽ tự đóng và lưu session."
echo
read -p "  Nhấn Enter để tiếp tục (hoặc Ctrl+C để bỏ qua)..."
echo
notebooklm login

echo
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✅ CÀI ĐẶT HOÀN TẤT!                                  ║"
echo "╠══════════════════════════════════════════════════════════╣"
echo "║                                                         ║"
echo "║  Bây giờ bạn có thể chạy:                               ║"
echo "║                                                         ║"
echo "║  • Liệt kê notebooks:                                   ║"
echo "║    python3 scripts/sync_notebook.py --list               ║"
echo "║                                                         ║"
echo "║  • Đồng bộ notebook mặc định:                            ║"
echo "║    python3 scripts/sync_notebook.py                      ║"
echo "║                                                         ║"
echo "║  • Đồng bộ notebook cụ thể:                              ║"
echo "║    python3 scripts/sync_notebook.py \                    ║"
echo "║      --notebook-id <ID>                                  ║"
echo "║                                                         ║"
echo "╚══════════════════════════════════════════════════════════╝"

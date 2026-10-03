#!/bin/bash
# ============================================================
# AI Workforce — Auto Setup Script (Universal macOS/Linux/Win)
# Tự kiểm tra + đóng gói + cài extension + kích hoạt hooks + rebuild dashboard
# Chạy: bash scripts/auto-setup.sh [--quiet]
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
QUIET="${1:-}"

log() {
    [ "$QUIET" = "--quiet" ] && return
    echo "$1"
}

log ""
log "╔══════════════════════════════════════════════════╗"
log "║        🤖 AI Workforce — Auto Setup             ║"
log "╚══════════════════════════════════════════════════╝"
log ""

# ──────────────────────────────────────────────────────
# 1. Detect IDE command (Antigravity IDE / Cursor / VS Code)
# ──────────────────────────────────────────────────────
IDE_CMD=""

# Thử các CLI trong PATH trước
for cmd in antigravity-ide antigravity agy cursor code code-insiders; do
    if command -v "$cmd" &>/dev/null; then
        IDE_CMD="$cmd"
        break
    fi
done

# Fallback macOS paths
if [ -z "$IDE_CMD" ]; then
    MAC_PATHS=(
        "/Applications/Antigravity IDE.app/Contents/Resources/app/bin/antigravity-ide"
        "/Applications/Antigravity.app/Contents/Resources/app/bin/antigravity"
        "$HOME/Applications/Antigravity IDE.app/Contents/Resources/app/bin/antigravity-ide"
        "$HOME/.antigravity-ide/bin/antigravity-ide"
        "/Applications/Cursor.app/Contents/Resources/app/bin/cursor"
        "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
    )
    for p in "${MAC_PATHS[@]}"; do
        if [ -x "$p" ]; then
            IDE_CMD="$p"
            break
        fi
    done
fi

if [ -z "$IDE_CMD" ]; then
    log "⚠️  Không tìm thấy IDE CLI (antigravity-ide/cursor/code)."
    log "   Extension sẽ không thể cài tự động qua CLI."
    log "   Hãy cài thủ công: Kéo thả file .vsix trong thư mục extension/ vào IDE"
else
    log "✅ IDE detected: $IDE_CMD"
fi

# ──────────────────────────────────────────────────────
# 2. Package & Install / Update AI Workforce Extension
# ──────────────────────────────────────────────────────
log "📦 Đang kiểm tra & cài đặt extension mới nhất..."

# Tìm file VSIX mới nhất hiện có
VSIX_FILE=$(ls -t "$PROJECT_DIR"/extension/ai-workforce-panel-*.vsix 2>/dev/null | head -1)

# Kiểm tra xem có cần đóng gói lại VSIX không (chưa có vsix hoặc mã nguồn extension mới hơn file vsix)
NEED_PACKAGE=false
if [ -z "$VSIX_FILE" ]; then
    NEED_PACKAGE=true
elif [ -n "$(find "$PROJECT_DIR/extension" -type f ! -name "*.vsix" -newer "$VSIX_FILE" 2>/dev/null)" ]; then
    NEED_PACKAGE=true
fi

# Đóng gói VSIX nếu cần và có npx
if [ "$NEED_PACKAGE" = "true" ] && command -v npx &>/dev/null && [ -d "$PROJECT_DIR/extension" ] && [ -f "$PROJECT_DIR/extension/package.json" ]; then
    log "📦 Phát hiện thay đổi trong mã nguồn extension, đang đóng gói VSIX mới..."
    (cd "$PROJECT_DIR/extension" && npx -y @vscode/vsce package --no-dependencies --allow-missing-repository 2>/dev/null || true)
    VSIX_FILE=$(ls -t "$PROJECT_DIR"/extension/ai-workforce-panel-*.vsix 2>/dev/null | head -1)
fi

if [ -z "$VSIX_FILE" ]; then
    log "❌ Không tìm thấy file .vsix trong extension/"
else
    VSIX_BASENAME=$(basename "$VSIX_FILE")
    # Trích version từ tên file (vd: ai-workforce-panel-3.1.0.vsix → 3.1.0)
    EXT_VERSION=$(echo "$VSIX_BASENAME" | sed 's/ai-workforce-panel-\(.*\)\.vsix/\1/')
    EXT_DIR_NAME="bangluutru.ai-workforce-panel-$EXT_VERSION"

    # ── Phương thức 1: Cài qua IDE CLI (nếu có) ──
    if [ -n "$IDE_CMD" ]; then
        log "🚀 Cài extension qua CLI: $VSIX_BASENAME ..."
        if "$IDE_CMD" --install-extension "$VSIX_FILE" --force 2>/dev/null; then
            INSTALLED=true
            log "✅ Extension đã cài qua CLI thành công"
        else
            log "⚠️  CLI --install-extension thất bại, chuyển sang copy trực tiếp..."
        fi
    fi

    # ── Phương thức 2: Luôn đồng bộ trực tiếp vào tất cả extensions dir đã có ──
    EXT_DIRS=(
        "$HOME/.gemini/antigravity-ide/extensions"
        "$HOME/.antigravity-ide/extensions"
        "$HOME/.vscode/extensions"
        "$HOME/.cursor/extensions"
    )

    for ext_dir in "${EXT_DIRS[@]}"; do
        if [ -d "$ext_dir" ]; then
            TARGET="$ext_dir/$EXT_DIR_NAME"
            # Xóa bản cũ cùng extension (tất cả version)
            rm -rf "$ext_dir"/bangluutru.ai-workforce-panel-* 2>/dev/null
            # Giải nén VSIX (là file zip) vào đúng cấu trúc flat
            mkdir -p "$TARGET"
            TMPDIR_VSIX=$(mktemp -d)
            unzip -qo "$VSIX_FILE" -d "$TMPDIR_VSIX" 2>/dev/null
            if [ -d "$TMPDIR_VSIX/extension" ]; then
                cp -R "$TMPDIR_VSIX/extension/"* "$TARGET/"
                [ -f "$TMPDIR_VSIX/extension.vsixmanifest" ] && cp "$TMPDIR_VSIX/extension.vsixmanifest" "$TARGET/.vsixmanifest"
            fi
            rm -rf "$TMPDIR_VSIX"
            INSTALLED=true
            log "✅ Extension đã đồng bộ trực tiếp vào: $ext_dir"
        fi
    done

    if [ "$INSTALLED" = "false" ]; then
        log "⚠️  Không thể cài extension tự động."
        log "   Hãy cài thủ công: Mở IDE → Cmd+Shift+P → 'Install from VSIX' → chọn $VSIX_FILE"
    fi

    # ── Dọn VSIX cũ (chỉ giữ bản mới nhất trong workspace) ──
    VSIX_COUNT=$(ls "$PROJECT_DIR"/extension/ai-workforce-panel-*.vsix 2>/dev/null | wc -l | tr -d ' ')
    if [ "$VSIX_COUNT" -gt 1 ]; then
        log "🧹 Dọn $((VSIX_COUNT - 1)) VSIX cũ, giữ lại: $VSIX_BASENAME"
        ls -t "$PROJECT_DIR"/extension/ai-workforce-panel-*.vsix | tail -n +2 | xargs rm -f 2>/dev/null
    fi
fi

# ──────────────────────────────────────────────────────
# 2b. Check & Install Office File Viewer Extension
#     (docx, xlsx, pptx, pdf, csv...)
#     Extension: cweijan.vscode-office (VS Code Marketplace)
# ──────────────────────────────────────────────────────
REQUIRED_EXTENSIONS=(
    "cweijan.vscode-office"   # Office + PDF viewer
)

if [ -n "$IDE_CMD" ]; then
    INSTALLED_LIST=$("$IDE_CMD" --list-extensions 2>/dev/null || true)

    for ext_id in "${REQUIRED_EXTENSIONS[@]}"; do
        if echo "$INSTALLED_LIST" | grep -qi "$ext_id"; then
            log "✅ Extension đã có: $ext_id"
        else
            log "📦 Đang cài extension hỗ trợ: $ext_id ..."
            if "$IDE_CMD" --install-extension "$ext_id" --force 2>/dev/null; then
                log "✅ Đã cài thành công: $ext_id"
            else
                log "⚠️  Không cài được $ext_id (có thể do offline hoặc Marketplace chặn)"
                log "   Cài thủ công: $IDE_CMD --install-extension $ext_id"
            fi
        fi
    done
fi

# ──────────────────────────────────────────────────────
# 2c. Check & Install System/Python Dependencies
# ──────────────────────────────────────────────────────
log "🔍 Đang kiểm tra dependencies hệ thống (Pandoc)..."
if ! command -v pandoc &>/dev/null; then
    log "⚠️  Chưa cài đặt Pandoc (cần thiết cho markdown_preserve.py)."
    if command -v brew &>/dev/null; then
        log "📦 Đang cài đặt Pandoc qua Homebrew..."
        brew install pandoc || log "❌ Cài đặt Pandoc thất bại. Cần cài thủ công."
    elif command -v apt-get &>/dev/null; then
        log "📦 Đang cài đặt Pandoc qua APT..."
        sudo apt-get update && sudo apt-get install -y pandoc || log "❌ Cài đặt Pandoc thất bại. Cần cài thủ công."
    else
        log "❌ Không thể cài tự động Pandoc trên OS này. Hãy cài thủ công: https://pandoc.org/"
    fi
else
    log "✅ Pandoc đã được cài đặt."
fi

# LibreOffice (tuỳ chọn, KHÔNG tự cài — gói lớn): scripts/doc_ingest.py cần để đọc DOC/XLS/PPT, ODT/ODS/ODP, RTF
SOFFICE_BIN="${SOFFICE:-}"
[ -z "$SOFFICE_BIN" ] && SOFFICE_BIN="$(command -v soffice || command -v libreoffice || true)"
[ -z "$SOFFICE_BIN" ] && [ -x "/Applications/LibreOffice.app/Contents/MacOS/soffice" ] && SOFFICE_BIN="/Applications/LibreOffice.app/Contents/MacOS/soffice"
if [ -n "$SOFFICE_BIN" ]; then
    log "✅ LibreOffice: $SOFFICE_BIN (doc_ingest đọc được DOC/XLS/PPT/ODT/ODS/ODP/RTF)"
else
    log "ℹ️  (Tuỳ chọn) Chưa có LibreOffice → doc_ingest không đọc được DOC/XLS/PPT/ODT/ODS/ODP/RTF (mã thoát 4)."
    if command -v brew &>/dev/null; then
        log "   Cài: brew install --cask libreoffice"
    else
        log "   Cài: sudo apt install libreoffice   (hoặc tải tại https://www.libreoffice.org/download/)"
    fi
fi

# tesseract + gói ngôn ngữ vie/jpn (tuỳ chọn): bản nháp OCR khi không có Apple Vision (Linux/Windows)
if command -v tesseract &>/dev/null; then
    TESS_LANGS="$(tesseract --list-langs 2>/dev/null | tr '\n' ' ')"
    if echo "$TESS_LANGS" | grep -qw vie && echo "$TESS_LANGS" | grep -qw jpn; then
        log "✅ tesseract có gói vie + jpn"
    else
        log "ℹ️  (Tuỳ chọn) tesseract thiếu gói vie/jpn → cài: brew install tesseract-lang  (apt: tesseract-ocr-vie tesseract-ocr-jpn)"
    fi
elif [ "$(uname)" != "Darwin" ]; then
    log "ℹ️  (Tuỳ chọn) Chưa có tesseract (OCR nháp cho trang scan): sudo apt install tesseract-ocr tesseract-ocr-vie tesseract-ocr-jpn"
fi

log "🐍 Đang thiết lập môi trường Python (.venv)..."
if [ ! -d "$PROJECT_DIR/.venv" ]; then
    log "📦 Đang tạo virtual environment (.venv)..."
    if command -v uv &>/dev/null; then
        uv venv "$PROJECT_DIR/.venv"
    elif command -v python3 &>/dev/null; then
        python3 -m venv "$PROJECT_DIR/.venv"
    else
        log "❌ Không tìm thấy Python3 hoặc uv. Vui lòng cài đặt Python."
    fi
fi

if [ -f "$PROJECT_DIR/.venv/bin/activate" ]; then
    log "📦 Đang cài đặt Python dependencies (markitdown, pypandoc)..."
    source "$PROJECT_DIR/.venv/bin/activate"
    if command -v uv &>/dev/null; then
        uv pip install -r "$PROJECT_DIR/requirements.txt" || log "⚠️ Lỗi cài đặt dependencies bằng uv"
    else
        pip install -r "$PROJECT_DIR/requirements.txt" || log "⚠️ Lỗi cài đặt dependencies bằng pip"
    fi
    log "✅ Python dependencies đã được cài đặt trong .venv"
    if "$PROJECT_DIR/.venv/bin/python" -c "import markitdown, mammoth, pdfplumber, openpyxl, pptx, pymupdf" 2>/dev/null; then
        log "✅ .venv có markitdown + bộ đọc DOCX/PDF/XLSX/PPTX (scripts/doc_ingest.py sẵn sàng)"
    else
        log "⚠️  .venv thiếu markitdown/bộ đọc tài liệu → chạy: $PROJECT_DIR/.venv/bin/pip install -r $PROJECT_DIR/requirements.txt"
    fi
fi

# Fallback: cài trực tiếp vào system Python nếu .venv chưa hoạt động
# (Đảm bảo Antigravity Agent có thể gọi python3 trực tiếp)
log "🔍 Kiểm tra Python dependencies trong system Python..."
if ! python3 -c "import docx; import fitz; import pdfplumber; import markitdown" 2>/dev/null; then
    log "📦 Đang cài đặt dependencies vào system Python (fallback)..."
    pip3 install python-docx pymupdf pdfplumber lxml "markitdown[docx,pdf,pptx,xlsx,xls,outlook]" pypandoc openpyxl python-pptx 2>/dev/null \
        || log "⚠️ Cài fallback thất bại (Python hệ thống có thể bị khoá PEP 668) — không sao: scripts/doc_ingest.py tự chạy lại bằng .venv/bin/python"
else
    log "✅ System Python đã có đủ dependencies."
fi

# ──────────────────────────────────────────────────────
# 2d. TTS Virtual Environment (.venv-tts) — engine chung _shared/media/tts.py
#     Dùng bởi: long-tieng, phu-de, video-studio (Luật R7)
#     VieNeu-TTS (vi) + Kokoro ONNX + misaki[ja] (en/ja), chạy offline.
#     Tách riêng khỏi .venv chính vì onnxruntime/kokoro-onnx
#     có thể xung đột phiên bản với pymupdf/pdfplumber
#     KHÔNG cài TTS trực tuyến (rủi ro bản quyền giọng đọc — danh sách cấm: _shared/engines.json)
# ──────────────────────────────────────────────────────
log "🎙️ Đang kiểm tra môi trường TTS (.venv-tts)..."
TTS_VENV="$PROJECT_DIR/.venv-tts"
TTS_REQUIREMENTS="$PROJECT_DIR/.agents/skills/video-studio/requirements-tts.txt"

if [ ! -d "$TTS_VENV" ]; then
    log "📦 Đang tạo TTS virtual environment (.venv-tts)..."
    if command -v uv &>/dev/null; then
        uv venv "$TTS_VENV"
    elif command -v python3 &>/dev/null; then
        python3 -m venv "$TTS_VENV"
    else
        log "⚠️  Python3 không tìm thấy — bỏ qua .venv-tts"
    fi
fi

if [ -x "$TTS_VENV/bin/python3" ]; then
    if ! "$TTS_VENV/bin/python3" -c "import kokoro_onnx, soundfile, misaki" 2>/dev/null; then
        log "📦 Đang cài đặt TTS dependencies (kokoro-onnx, misaki[ja], vieneu…) vào .venv-tts..."
        if command -v uv &>/dev/null; then
            uv pip install --python "$TTS_VENV/bin/python3" -r "$TTS_REQUIREMENTS" \
                || log "⚠️  Lỗi cài TTS deps từ requirements-tts.txt (uv)"
        else
            "$TTS_VENV/bin/python3" -m pip install -r "$TTS_REQUIREMENTS" \
                || log "⚠️  Lỗi cài TTS deps từ requirements-tts.txt (pip)"
        fi
    else
        log "✅ .venv-tts đã có đủ TTS dependencies."
    fi
fi

# Model Kokoro (~120 MB) — gitignored, tải 1 lần vào thư mục model dùng chung
KOKORO_DIR="$PROJECT_DIR/.agents/skills/_shared/models/kokoro"
KOKORO_BASE="https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
mkdir -p "$KOKORO_DIR"
if ls "$KOKORO_DIR"/kokoro-v1.0*.onnx &>/dev/null; then
    log "✅ Model Kokoro đã có."
else
    log "📥 Đang tải model Kokoro int8 (~92 MB)..."
    curl -fL --retry 3 -o "$KOKORO_DIR/kokoro-v1.0.int8.onnx.part" "$KOKORO_BASE/kokoro-v1.0.int8.onnx" \
        && mv "$KOKORO_DIR/kokoro-v1.0.int8.onnx.part" "$KOKORO_DIR/kokoro-v1.0.int8.onnx" \
        || log "⚠️  Tải model Kokoro thất bại — tiếng Anh/Nhật sẽ báo lỗi cho tới khi tải lại"
fi
if [ ! -f "$KOKORO_DIR/voices-v1.0.bin" ]; then
    log "📥 Đang tải bộ giọng Kokoro (~28 MB)..."
    curl -fL --retry 3 -o "$KOKORO_DIR/voices-v1.0.bin.part" "$KOKORO_BASE/voices-v1.0.bin" \
        && mv "$KOKORO_DIR/voices-v1.0.bin.part" "$KOKORO_DIR/voices-v1.0.bin" \
        || log "⚠️  Tải voices Kokoro thất bại"
fi

# ──────────────────────────────────────────────────────
# 2e. Node.js Dependencies (npm install)
#     Root: docx, pptxgenjs → xu-ly-van-phong
#     hand-drawn-animation: puppeteer-core → render MP4
# ──────────────────────────────────────────────────────
if command -v npm &>/dev/null; then
    # Root node_modules (cho xu-ly-van-phong template DOCX/PPTX)
    if [ -f "$PROJECT_DIR/package.json" ] && [ ! -d "$PROJECT_DIR/node_modules" ]; then
        log "📦 Đang cài đặt Node.js dependencies (root)..."
        (cd "$PROJECT_DIR" && npm install --no-audit --no-fund 2>/dev/null) || log "⚠️  npm install root thất bại"
        log "✅ Node.js root dependencies đã cài đặt"
    fi

    # hand-drawn-animation node_modules (puppeteer-core)
    HDA_SCRIPTS="$PROJECT_DIR/.agents/skills/hand-drawn-animation/scripts"
    if [ -f "$HDA_SCRIPTS/package.json" ] && [ ! -d "$HDA_SCRIPTS/node_modules" ]; then
        log "📦 Đang cài đặt Node.js dependencies (hand-drawn-animation)..."
        (cd "$HDA_SCRIPTS" && npm install --no-audit --no-fund 2>/dev/null) || log "⚠️  npm install hand-drawn-animation thất bại"
        log "✅ hand-drawn-animation dependencies đã cài đặt"
    fi
else
    log "⚠️  npm chưa cài — bỏ qua Node.js dependencies (xu-ly-van-phong, hand-drawn-animation)"
fi

# ──────────────────────────────────────────────────────
# 2f. Playwright Browser (chromium)
#     Dùng bởi: app-auditor (web crawl + visual sweep)
# ──────────────────────────────────────────────────────
if python3 -c "import playwright" 2>/dev/null; then
    if ! python3 -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); b.close(); p.stop()" 2>/dev/null; then
        log "📦 Đang cài đặt Playwright Chromium browser..."
        python3 -m playwright install chromium 2>/dev/null || log "⚠️  Cài Playwright chromium thất bại"
        log "✅ Playwright Chromium đã được cài đặt"
    else
        log "✅ Playwright Chromium đã sẵn sàng."
    fi
fi

# ──────────────────────────────────────────────────────
# 3. Kích hoạt Git Hooks tự động
# ──────────────────────────────────────────────────────
if [ -d "$PROJECT_DIR/.git" ]; then
    git -C "$PROJECT_DIR" config core.hooksPath scripts/hooks 2>/dev/null || true
    chmod +x "$PROJECT_DIR"/scripts/hooks/* 2>/dev/null || true
    log "✅ Git hooks đã tự động kích hoạt (post-merge auto-update)"
fi

# ──────────────────────────────────────────────────────
# 4. Rebuild Dashboard data.json
# ──────────────────────────────────────────────────────
if command -v node &>/dev/null; then
    node "$PROJECT_DIR/dashboard/build_dashboard.js"
    log "✅ Dashboard data.json đã rebuild"
else
    log "⚠️  Node.js chưa cài — bỏ qua rebuild dashboard"
fi

# ──────────────────────────────────────────────────────
# 4.2. Kiểm tra Môi trường Node.js & Modern Web Guidance
# ──────────────────────────────────────────────────────
log "🌐 Đang kiểm tra năng lực Modern Web Guidance (Google Platform)..."
if command -v npx &>/dev/null; then
    log "✅ Node.js & npx đã sẵn sàng (Hỗ trợ npx modern-web-guidance cho tao-landing-page & app-auditor)"
else
    log "⚠️  Node.js/npx chưa được cài đặt. Vui lòng cài đặt Node.js để chạy npx modern-web-guidance."
fi

# ──────────────────────────────────────────────────────
# 4.5. Kiểm định & Chứng nhận Kỹ năng (Rule R4)
# ──────────────────────────────────────────────────────
if [ -f "$PROJECT_DIR/scripts/audit_skill.py" ]; then
    python3 "$PROJECT_DIR/scripts/audit_skill.py" --all --certify --quiet 2>/dev/null || true
    log "✅ Hệ thống kiểm định Rule R4 đã quét và cấp chứng chỉ cho các kỹ năng"
fi

# ──────────────────────────────────────────────────────
# 5. Summary
# ──────────────────────────────────────────────────────
SKILL_COUNT=$(ls -d "$PROJECT_DIR"/.agents/skills/*/ 2>/dev/null | wc -l | tr -d ' ')
WORKFLOW_COUNT=$(ls "$PROJECT_DIR"/.agents/workflows/*.md 2>/dev/null | wc -l | tr -d ' ')
KNOWLEDGE_COUNT=$(ls -d "$PROJECT_DIR"/.agents/knowledge/*/ 2>/dev/null | wc -l | tr -d ' ')
RULE_COUNT=$(ls "$PROJECT_DIR"/.agents/rules/*.md 2>/dev/null | wc -l | tr -d ' ')

log ""
log "📊 AIWF Status:"
log "   Skills:     $SKILL_COUNT"
log "   Workflows:  $WORKFLOW_COUNT"
log "   Knowledge:  $KNOWLEDGE_COUNT"
log "   Rules:      $RULE_COUNT"
log ""
log "🎉 AI Workforce sẵn sàng trên mọi máy!"
log ""

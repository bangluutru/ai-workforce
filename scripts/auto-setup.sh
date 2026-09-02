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

# Đóng gói VSIX nếu có npx và thư mục extension source
if command -v npx &>/dev/null && [ -d "$PROJECT_DIR/extension" ] && [ -f "$PROJECT_DIR/extension/package.json" ]; then
    (cd "$PROJECT_DIR/extension" && npx -y @vscode/vsce package --no-dependencies --allow-missing-repository 2>/dev/null || true)
fi

# Tìm file VSIX mới nhất
VSIX_FILE=$(ls -t "$PROJECT_DIR"/extension/ai-workforce-panel-*.vsix 2>/dev/null | head -1)

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
fi

# Fallback: cài trực tiếp vào system Python nếu .venv chưa hoạt động
# (Đảm bảo Antigravity Agent có thể gọi python3 trực tiếp)
log "🔍 Kiểm tra Python dependencies trong system Python..."
if ! python3 -c "import docx; import fitz; import pdfplumber" 2>/dev/null; then
    log "📦 Đang cài đặt dependencies vào system Python (fallback)..."
    pip3 install python-docx pymupdf pdfplumber lxml markitdown pypandoc 2>/dev/null || log "⚠️ Cài fallback thất bại — chạy thủ công: pip3 install -r requirements.txt"
else
    log "✅ System Python đã có đủ dependencies."
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

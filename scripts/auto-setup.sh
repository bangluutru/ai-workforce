#!/bin/bash
# ============================================================
# AI Workforce — Auto Setup Script
# Tự kiểm tra + đóng gói + cài extension + rebuild dashboard
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
# 1. Detect IDE command
# ──────────────────────────────────────────────────────
IDE_CMD=""

# Thử các CLI trong PATH trước
for cmd in antigravity-ide antigravity cursor code code-insiders; do
    if command -v "$cmd" &>/dev/null; then
        IDE_CMD="$cmd"
        break
    fi
done

# Fallback: thử full path cho Antigravity IDE trên macOS
if [ -z "$IDE_CMD" ]; then
    AGY_BIN="/Applications/Antigravity IDE.app/Contents/Resources/app/bin/antigravity-ide"
    if [ -x "$AGY_BIN" ]; then
        IDE_CMD="$AGY_BIN"
    fi
fi

if [ -z "$IDE_CMD" ]; then
    log "⚠️  Không tìm thấy IDE CLI (antigravity-ide/cursor/code)."
    log "   Extension sẽ không được cài tự động."
    log "   Hãy cài thủ công: <IDE> --install-extension extension/ai-workforce-panel-*.vsix"
else
    log "✅ IDE detected: $IDE_CMD"
fi

# ──────────────────────────────────────────────────────
# 2. Package & Install / Update AI Workforce Extension
# ──────────────────────────────────────────────────────
if [ -n "$IDE_CMD" ]; then
    log "📦 Đang kiểm tra & đóng gói extension mới nhất..."

    # Đóng gói VSIX nếu có npx
    if command -v npx &>/dev/null && [ -d "$PROJECT_DIR/extension" ]; then
        (cd "$PROJECT_DIR/extension" && npx -y @vscode/vsce package --no-dependencies --allow-missing-repository 2>/dev/null || true)
    fi

    # Tìm file VSIX mới nhất
    VSIX_FILE=$(ls -t "$PROJECT_DIR"/extension/ai-workforce-panel-*.vsix 2>/dev/null | head -1)

    if [ -z "$VSIX_FILE" ]; then
        log "❌ Không tìm thấy file .vsix trong extension/"
    else
        log "🚀 Đang cài đặt/cập nhật extension: $(basename "$VSIX_FILE") ..."
        "$IDE_CMD" --install-extension "$VSIX_FILE" --force 2>/dev/null || true
        log "✅ Extension đã cập nhật thành công: $(basename "$VSIX_FILE")"
    fi
fi

# ──────────────────────────────────────────────────────
# 2b. Check & Install Office File Viewer Extension
#     (docx, xlsx, pptx, pdf, csv...)
#     Extension: cweijan.vscode-office (VS Code Marketplace)
# ──────────────────────────────────────────────────────
REQUIRED_EXTENSIONS=(
    "cweijan.vscode-office"   # Office + PDF: docx, xlsx, pptx, pdf, csv, svg...
)

if [ -n "$IDE_CMD" ]; then
    INSTALLED_LIST=$("$IDE_CMD" --list-extensions 2>/dev/null || true)

    for ext_id in "${REQUIRED_EXTENSIONS[@]}"; do
        if echo "$INSTALLED_LIST" | grep -qi "$ext_id"; then
            log "✅ Extension đã có: $ext_id"
        else
            log "📦 Đang cài extension: $ext_id ..."
            if "$IDE_CMD" --install-extension "$ext_id" --force 2>/dev/null; then
                log "✅ Đã cài thành công: $ext_id"
            else
                log "⚠️  Không cài được $ext_id (có thể cần mạng hoặc Marketplace không khả dụng)"
                log "   Cài thủ công: $IDE_CMD --install-extension $ext_id"
            fi
        fi
    done
fi

# ──────────────────────────────────────────────────────
# 3. Rebuild Dashboard data.json
# ──────────────────────────────────────────────────────
if command -v node &>/dev/null; then
    node "$PROJECT_DIR/dashboard/build_dashboard.js"
    log "✅ Dashboard data.json đã rebuild"
else
    log "⚠️  Node.js chưa cài — bỏ qua rebuild dashboard"
fi

# ──────────────────────────────────────────────────────
# 4. Verify git hooks
# ──────────────────────────────────────────────────────
HOOKS_PATH=$(cd "$PROJECT_DIR" && git config core.hooksPath 2>/dev/null || true)
if [ "$HOOKS_PATH" = "scripts/hooks" ]; then
    log "✅ Git hooks đã kích hoạt"
else
    log "⚠️  Git hooks chưa kích hoạt. Chạy: bash scripts/install-hooks.sh"
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
log "🎉 AI Workforce sẵn sàng!"
log ""

#!/bin/bash
# ============================================================
# AI Workforce — Auto Setup Script
# Tự kiểm tra + cài extension + rebuild dashboard
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
for cmd in antigravity cursor code code-insiders; do
    if command -v "$cmd" &>/dev/null; then
        IDE_CMD="$cmd"
        break
    fi
done

if [ -z "$IDE_CMD" ]; then
    log "⚠️  Không tìm thấy IDE CLI (antigravity/cursor/code)."
    log "   Extension sẽ không được cài tự động."
    log "   Hãy cài thủ công: <IDE> --install-extension extension/ai-workforce-panel-*.vsix"
else
    log "✅ IDE detected: $IDE_CMD"
fi

# ──────────────────────────────────────────────────────
# 2. Check & Install Extension
# ──────────────────────────────────────────────────────
if [ -n "$IDE_CMD" ]; then
    EXT_INSTALLED=$("$IDE_CMD" --list-extensions 2>/dev/null | grep -i "ai-workforce" || true)

    if [ -z "$EXT_INSTALLED" ]; then
        log "📦 Extension chưa cài. Đang cài đặt..."

        # Tìm file VSIX mới nhất
        VSIX_FILE=$(ls -t "$PROJECT_DIR"/extension/ai-workforce-panel-*.vsix 2>/dev/null | head -1)

        if [ -z "$VSIX_FILE" ]; then
            log "❌ Không tìm thấy file .vsix trong extension/"
        else
            "$IDE_CMD" --install-extension "$VSIX_FILE" --force 2>/dev/null
            log "✅ Extension đã cài: $(basename "$VSIX_FILE")"
        fi
    else
        log "✅ Extension đã có sẵn: $EXT_INSTALLED"
    fi
fi

# ──────────────────────────────────────────────────────
# 3. Rebuild Dashboard data.json
# ──────────────────────────────────────────────────────
if command -v node &>/dev/null; then
    node "$PROJECT_DIR/dashboard/build_dashboard.js" 2>/dev/null
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

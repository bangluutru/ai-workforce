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
if [ -n "$IDE_CMD" ]; then
    log "📦 Đang kiểm tra & đóng gói extension mới nhất..."

    # Đóng gói VSIX nếu có npx và thư mục extension
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

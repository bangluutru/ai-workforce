#!/bin/bash
# ============================================================
# Cài HyperFrames sandbox cho Creative Studio (video-studio, _shared/creative)
# Manifest + lock được git theo dõi tại:
#   .agents/skills/_shared/creative/hyperframes/{package.json,package-lock.json}
# Cài vào _process/hyperframes_sandbox (gitignored) - đúng đường dẫn mà
# renderers/hyperframes_adapter.py, presets/registry.py và qa/dom_validator.py tìm.
# Không có Node/npm hoặc cài lỗi: KHÔNG chặn setup; render tự rơi về Canvas fallback.
# Chạy: bash scripts/setup_hyperframes.sh [--quiet]
# Mã thoát: 0 = sẵn sàng, 1 = chưa cài được (chỉ còn Canvas fallback)
# ============================================================
QUIET="$1"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST_DIR="$PROJECT_DIR/.agents/skills/_shared/creative/hyperframes"
SANDBOX="$PROJECT_DIR/_process/hyperframes_sandbox"

log() { [ "$QUIET" = "--quiet" ] && return; echo "$@"; }

if [ -x "$SANDBOX/node_modules/.bin/hyperframes" ] && [ -d "$SANDBOX/node_modules/gsap" ]; then
    log "✅ HyperFrames sandbox đã sẵn sàng."
    exit 0
fi

if ! command -v npm &>/dev/null; then
    log "⚠️  npm chưa cài - bỏ qua HyperFrames (Creative Studio sẽ dùng Canvas fallback)"
    exit 1
fi

if [ ! -f "$MANIFEST_DIR/package.json" ]; then
    log "⚠️  Thiếu $MANIFEST_DIR/package.json - bỏ qua HyperFrames"
    exit 1
fi

log "📦 Đang cài HyperFrames sandbox (video-studio Creative Studio)..."
mkdir -p "$SANDBOX"
cp "$MANIFEST_DIR/package.json" "$SANDBOX/package.json"
[ -f "$MANIFEST_DIR/package-lock.json" ] && cp "$MANIFEST_DIR/package-lock.json" "$SANDBOX/package-lock.json"

# npm ci khi có lock (tái lập chính xác phiên bản), nếu không dùng npm install
if [ -f "$SANDBOX/package-lock.json" ]; then
    INSTALL_CMD="npm ci --no-audit --no-fund"
else
    INSTALL_CMD="npm install --no-audit --no-fund"
fi

if (cd "$SANDBOX" && HYPERFRAMES_TELEMETRY=0 DO_NOT_TRACK=1 $INSTALL_CMD >/dev/null 2>&1) \
   && [ -x "$SANDBOX/node_modules/.bin/hyperframes" ]; then
    log "✅ HyperFrames sandbox đã cài đặt"
    exit 0
fi

log "⚠️  Cài HyperFrames thất bại - Creative Studio sẽ dùng Canvas fallback (chạy lại: bash scripts/setup_hyperframes.sh)"
exit 1

#!/bin/bash
# ============================================================
# AI Workforce — 1-Click Setup
# Chạy khi clone về máy mới hoặc cập nhật môi trường
# ============================================================
set -e
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
bash "$ROOT_DIR/scripts/auto-setup.sh" "$@"

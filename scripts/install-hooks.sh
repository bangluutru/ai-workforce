#!/bin/bash
# ============================================================
# Kích hoạt Git Hooks cho AI Workforce
# Chỉ cần chạy 1 lần sau khi clone repo
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR"

# Set git hooks path
git config core.hooksPath scripts/hooks

# Đảm bảo hooks có quyền thực thi
chmod +x scripts/hooks/*

echo ""
echo "✅ Git hooks đã được kích hoạt!"
echo "   Từ giờ, mỗi khi 'git pull', AIWF sẽ tự:"
echo "   • Kiểm tra + cài extension VSIX nếu thiếu"
echo "   • Rebuild dashboard data.json"
echo ""

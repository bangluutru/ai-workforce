/**
 * config.js — Hằng số cấu hình đường dẫn cố định & dự phòng
 *
 * Extension sẽ tự động tìm kiếm trên cả macOS, Linux, Windows.
 * Khi thêm đường dẫn mới, chỉ cần bổ sung vào mảng KNOWN_AGENTS_PATHS.
 */

const path = require('path');
const os = require('os');

const KNOWN_AGENTS_PATHS = [
    // Antigravity IDE (primary paths)
    path.join(os.homedir(), '.gemini', 'antigravity-ide', 'scratch', 'ai-workforce', '.agents'),
    path.join(os.homedir(), '.gemini', 'scratch', 'ai-workforce', '.agents'),
    path.join(os.homedir(), '.gemini', 'config'),
    // Home-level clones
    path.join(os.homedir(), 'ai-workforce', '.agents'),
    path.join(os.homedir(), 'Documents', 'ai-workforce', '.agents'),
    path.join(os.homedir(), 'Downloads', 'ai-workforce', '.agents'),
    path.join(os.homedir(), 'Projects', 'ai-workforce', '.agents'),
    path.join(os.homedir(), 'workspace', 'ai-workforce', '.agents'),
];

module.exports = { KNOWN_AGENTS_PATHS };

/**
 * utils.js — Tiện ích dùng chung cho extension
 *
 * Chứa các hàm nền tảng: parser YAML, tìm thư mục, escape HTML,
 * format nhãn hiển thị, và sinh nonce CSP.
 */

const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const { KNOWN_AGENTS_PATHS } = require('./config');

// ────────────────────────────────────────────────
// YAML Frontmatter Parser
// ────────────────────────────────────────────────
function parseFrontmatter(content) {
    const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!match) return {};
    const result = {};
    match[1].split(/\r?\n/).forEach(line => {
        const kv = line.match(/^([a-zA-Z0-9_-]+):\s*(.*)$/);
        if (kv) {
            result[kv[1].trim()] = kv[2].trim().replace(/^['"]|['"]$/g, '');
        }
    });
    return result;
}

// ────────────────────────────────────────────────
// Tìm thư mục .agents
// ────────────────────────────────────────────────
function findAgentsDir() {
    const folders = vscode.workspace.workspaceFolders;
    if (folders) {
        for (const folder of folders) {
            const rootPath = folder.uri.fsPath;
            const direct = path.join(rootPath, '.agents');
            if (fs.existsSync(direct)) return direct;

            const sub = path.join(rootPath, 'ai-workforce', '.agents');
            if (fs.existsSync(sub)) return sub;

            const scratchSub = path.join(rootPath, 'scratch', 'ai-workforce', '.agents');
            if (fs.existsSync(scratchSub)) return scratchSub;
        }
    }

    try {
        const extRelative = path.join(__dirname, '..', '..', '.agents');
        if (fs.existsSync(extRelative)) return extRelative;
    } catch {}

    if (process.env.ANTIGRAVITY_AGENTS_DIR && fs.existsSync(process.env.ANTIGRAVITY_AGENTS_DIR)) {
        return process.env.ANTIGRAVITY_AGENTS_DIR;
    }

    for (const knownPath of KNOWN_AGENTS_PATHS) {
        if (fs.existsSync(knownPath)) {
            return knownPath;
        }
    }

    return null;
}

// ────────────────────────────────────────────────
// Tìm thư mục gốc ai-workforce (cha của .agents/)
// ────────────────────────────────────────────────
function findWorkspaceRoot() {
    const agentsDir = findAgentsDir();
    if (agentsDir) {
        return path.dirname(agentsDir);
    }
    return null;
}

// ────────────────────────────────────────────────
// Security: Sinh nonce cho CSP
// ────────────────────────────────────────────────
function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

// ────────────────────────────────────────────────
// Escape HTML — chống XSS trong webview
// ────────────────────────────────────────────────
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ────────────────────────────────────────────────
// Format nhãn hiển thị cho card UI
// ────────────────────────────────────────────────
function formatLabel(name, mappedLabel) {
    if (mappedLabel) {
        return mappedLabel.replace(/\n/g, '<br>');
    }
    const clean = name.replace(/^[Ww]\d+[-_]?/, '').replace(/[-_]/g, ' ');
    const words = clean.split(' ');
    if (words.length > 2) {
        const mid = Math.ceil(words.length / 2);
        return words.slice(0, mid).join(' ') + '<br>' + words.slice(mid).join(' ');
    }
    return clean;
}

module.exports = {
    parseFrontmatter,
    findAgentsDir,
    findWorkspaceRoot,
    getNonce,
    escapeHtml,
    formatLabel,
};

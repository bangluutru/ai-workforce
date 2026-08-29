const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

// ============================================================
// CẤU HÌNH ĐƯỜNG DẪN CỐ ĐỊNH
// Extension sẽ luôn tìm dữ liệu ở đây, không phụ thuộc workspace
// ============================================================
const KNOWN_AGENTS_PATHS = [
    // Antigravity IDE (primary)
    path.join(require('os').homedir(), '.gemini', 'antigravity-ide', 'scratch', 'ai-workforce', '.agents'),
    // Cursor / VS Code fallback
    path.join(require('os').homedir(), '.gemini', 'scratch', 'ai-workforce', '.agents'),
    // Home-level clone (git clone trực tiếp)
    path.join(require('os').homedir(), 'ai-workforce', '.agents'),
];

// ============================================================
// YAML Frontmatter Parser (Không cần thư viện ngoài)
// ============================================================
function parseFrontmatter(content) {
    const match = content.match(/^---\n([\s\S]*?)\n---/);
    if (!match) return {};
    const result = {};
    match[1].split('\n').forEach(line => {
        const kv = line.match(/^([a-zA-Z0-9_-]+):\s*(.*)$/);
        if (kv) {
            result[kv[1]] = kv[2].trim().replace(/^['"]|['"]$/g, '');
        }
    });
    return result;
}

// ============================================================
// Tìm thư mục .agents — Ưu tiên workspace, fallback sang đường dẫn cố định
// ============================================================
function findAgentsDir() {
    const folders = vscode.workspace.workspaceFolders;
    if (folders) {
        for (const folder of folders) {
            const agentsPath = path.join(folder.uri.fsPath, '.agents');
            if (fs.existsSync(agentsPath)) {
                return agentsPath;
            }
        }
    }
    for (const knownPath of KNOWN_AGENTS_PATHS) {
        if (fs.existsSync(knownPath)) {
            return knownPath;
        }
    }
    return null;
}

// ============================================================
// Icon & Color Mapping
// Mỗi item type/name sẽ có icon + gradient riêng
// ============================================================
const ICON_MAP = {
    // Workflows
    'W1-chuan-bi-tuyen-dung': { icon: '📋', gradient: 'gradient-blue', label: 'Chuẩn bị\ntuyển dụng' },
    'W2-sang-loc-cv':         { icon: '🔍', gradient: 'gradient-indigo', label: 'Sàng lọc\nCV' },
    'W3-phong-van':           { icon: '🎤', gradient: 'gradient-purple', label: 'Phỏng vấn' },
    'W4-onboarding':          { icon: '🚀', gradient: 'gradient-teal', label: 'Onboarding' },

    // Skills
    'pdf-translate':          { icon: '🌐', gradient: 'gradient-teal', label: 'Dịch PDF' },
    'boc-tach-cv':            { icon: '📄', gradient: 'gradient-orange', label: 'Bóc tách\nCV' },
    'cham-diem-cv':           { icon: '⭐', gradient: 'gradient-amber', label: 'Chấm điểm\nCV' },
    'viet-jd':                { icon: '✏️', gradient: 'gradient-cyan', label: 'Viết JD' },
    'phan-tich-nhan-su':      { icon: '📊', gradient: 'gradient-green', label: 'Phân tích\nnhân sự' },
    'quan-ly-hop-dong':       { icon: '📑', gradient: 'gradient-rose', label: 'Quản lý\nhợp đồng' },
    'tu-van-phap-luat':       { icon: '⚖️', gradient: 'gradient-indigo', label: 'Tư vấn\npháp luật' },
    'xu-ly-van-phong':        { icon: '📝', gradient: 'gradient-blue', label: 'Xử lý\nVăn phòng' },
};

// Fallback pools cho items chưa có mapping
const FALLBACK_ICONS = ['💼', '🎯', '⚙️', '🔧', '📌', '🗂️', '🏷️', '📐'];
const FALLBACK_GRADIENTS = [
    'gradient-blue', 'gradient-indigo', 'gradient-purple', 'gradient-pink',
    'gradient-orange', 'gradient-teal', 'gradient-green', 'gradient-cyan',
    'gradient-amber', 'gradient-rose', 'gradient-gray', 'gradient-slate',
];

function getIconConfig(name, index) {
    if (ICON_MAP[name]) return ICON_MAP[name];
    return {
        icon: FALLBACK_ICONS[index % FALLBACK_ICONS.length],
        gradient: FALLBACK_GRADIENTS[index % FALLBACK_GRADIENTS.length],
        label: null,  // will use original name
    };
}

// ============================================================
// Scan .agents directory for skills & workflows
// ============================================================
function scanItems() {
    const agentsDir = findAgentsDir();
    if (!agentsDir) return { workflows: [], skills: [] };

    const result = { workflows: [], skills: [] };

    // Scan workflows
    const workflowDir = path.join(agentsDir, 'workflows');
    if (fs.existsSync(workflowDir)) {
        const files = fs.readdirSync(workflowDir).filter(f => f.endsWith('.md'));
        for (const file of files) {
            const content = fs.readFileSync(path.join(workflowDir, file), 'utf-8');
            const meta = parseFrontmatter(content);
            result.workflows.push({
                name: meta.name || file.replace('.md', ''),
                description: meta.description || '',
                trigger: meta.trigger || `Hãy thực hiện workflow "${meta.name || file.replace('.md', '')}" theo quy trình đã định`,
                type: 'workflow',
            });
        }
    }

    // Scan skills
    const skillDir = path.join(agentsDir, 'skills');
    if (fs.existsSync(skillDir)) {
        const dirs = fs.readdirSync(skillDir).filter(f => {
            try { return fs.statSync(path.join(skillDir, f)).isDirectory(); }
            catch { return false; }
        });
        for (const dir of dirs) {
            const skillFile = path.join(skillDir, dir, 'SKILL.md');
            if (fs.existsSync(skillFile)) {
                const content = fs.readFileSync(skillFile, 'utf-8');
                const meta = parseFrontmatter(content);
                result.skills.push({
                    name: meta.name || dir,
                    description: meta.description || '',
                    trigger: meta.trigger || `Hãy thực hiện skill "${meta.name || dir}" theo đúng hướng dẫn trong SKILL.md`,
                    type: 'skill',
                });
            }
        }
    }

    return result;
}

// ============================================================
// GỬI LỆNH TRỰC TIẾP VÀO ANTIGRAVITY CHAT
// Chiến lược 3 bước:
//   1. Mở/focus chat panel
//   2. Simulate gõ text trực tiếp vào ô chat input
//   3. Fallback: clipboard + auto-paste
// ============================================================
async function sendToAntigravityChat(text) {
    const allCommands = await vscode.commands.getCommands(true);

    // ── Bước 1: Focus vào chat input ──────────────────────────
    const chatFocusCommands = [
        'workbench.action.chat.open',          // VS Code standard
        'antigravity.chat.focus',              // Antigravity IDE
        'workbench.action.chat.newChat',       // VS Code new chat
        'antigravity.chat.new',                // Antigravity new chat
    ];

    let chatFocused = false;
    for (const cmd of chatFocusCommands) {
        if (allCommands.includes(cmd)) {
            try {
                // Thử mở với query pre-filled trước (VS Code native API)
                if (cmd === 'workbench.action.chat.open') {
                    try {
                        await vscode.commands.executeCommand(cmd, {
                            query: text,
                            isPartialQuery: true,
                        });
                        vscode.window.showInformationMessage(
                            `✅ Đã điền lệnh vào Chat! Nhấn Enter để gửi.`
                        );
                        return; // Thành công hoàn toàn
                    } catch {
                        // Không hỗ trợ query args, tiếp tục mở bình thường
                        await vscode.commands.executeCommand(cmd);
                        chatFocused = true;
                        break;
                    }
                } else {
                    await vscode.commands.executeCommand(cmd);
                    chatFocused = true;
                    break;
                }
            } catch {
                // Command tồn tại nhưng thất bại → thử command khác
            }
        }
    }

    if (!chatFocused) {
        // Không mở được chat → fallback clipboard thuần
        await vscode.env.clipboard.writeText(text);
        vscode.window.showWarningMessage(
            `⚠️ Đã copy lệnh. Mở Chat (Cmd+Shift+I) rồi nhấn Cmd+V.`,
            'Mở Chat'
        ).then(selection => {
            if (selection === 'Mở Chat') {
                for (const cmd of chatFocusCommands) {
                    if (allCommands.includes(cmd)) {
                        vscode.commands.executeCommand(cmd).catch(() => {});
                        break;
                    }
                }
            }
        });
        return;
    }

    // ── Bước 2: Đợi chat panel render xong ────────────────────
    await new Promise(resolve => setTimeout(resolve, 500));

    // ── Bước 3: Simulate gõ text trực tiếp vào ô chat input ──
    // Dùng "type" command — đây là VS Code built-in command gõ text
    // vào bất cứ input nào đang có focus (editor hoặc chat input)
    let typed = false;
    try {
        await vscode.commands.executeCommand('type', { text: text });
        typed = true;
    } catch {
        // "type" command không hoạt động trong chat input
    }

    if (typed) {
        vscode.window.showInformationMessage(
            `✅ Đã điền lệnh vào Chat! Gõ tiếp yêu cầu rồi nhấn Enter.`
        );
        return;
    }

    // ── Bước 4: Fallback — clipboard + simulate paste ─────────
    await vscode.env.clipboard.writeText(text);

    // Thử simulate Cmd+V bằng keybinding
    const pasteCommands = [
        'editor.action.clipboardPasteAction',
    ];
    for (const cmd of pasteCommands) {
        if (allCommands.includes(cmd)) {
            try {
                await vscode.commands.executeCommand(cmd);
                vscode.window.showInformationMessage(
                    `✅ Đã dán lệnh vào Chat! Gõ tiếp yêu cầu rồi nhấn Enter.`
                );
                return;
            } catch {
                // Tiếp tục
            }
        }
    }

    // ── Fallback cuối: thông báo user nhấn Cmd+V ─────────────
    vscode.window.showInformationMessage(
        `📋 Đã copy lệnh! Nhấn Cmd+V trong ô Chat để dán.`
    );
}

// ============================================================
// Format short label for card display
// ============================================================
function formatLabel(name, customLabel) {
    if (customLabel) return customLabel.replace(/\n/g, '<br>');

    // Convert kebab-case name to readable label
    let label = name
        .replace(/^W\d+-/, '')  // Remove workflow prefix like W1-
        .replace(/-/g, ' ')     // kebab to spaces
        .replace(/\b\w/g, c => c.toUpperCase()); // Capitalize

    // Truncate if too long
    if (label.length > 20) {
        const words = label.split(' ');
        const lines = [];
        let current = '';
        for (const word of words) {
            if ((current + ' ' + word).trim().length > 12 && current) {
                lines.push(current.trim());
                current = word;
            } else {
                current = (current + ' ' + word).trim();
            }
        }
        if (current) lines.push(current.trim());
        return lines.slice(0, 2).join('<br>');
    }

    return label;
}

// ============================================================
// WebviewViewProvider — Renders the icon grid in sidebar
// ============================================================
class WorkforcePanelProvider {
    constructor(extensionUri) {
        this._extensionUri = extensionUri;
        this._view = undefined;
    }

    resolveWebviewView(webviewView) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [
                vscode.Uri.joinPath(this._extensionUri, 'media'),
            ],
        };

        this._updateContent();

        // Handle messages from webview
        webviewView.webview.onDidReceiveMessage(async (message) => {
            if (message.command === 'runItem') {
                if (message.itemType === 'skill') {
                    // Skill: mở chat + điền prefix "SkillName: "
                    const prefix = `${message.itemName}: `;
                    await sendToAntigravityChat(prefix);
                } else {
                    // Workflow: gửi full trigger
                    await sendToAntigravityChat(message.trigger);
                }
            }
        });
    }

    refresh() {
        if (this._view) {
            this._updateContent();
        }
    }

    _updateContent() {
        const webview = this._view.webview;
        const cssUri = webview.asWebviewUri(
            vscode.Uri.joinPath(this._extensionUri, 'media', 'webview.css')
        );

        const data = scanItems();
        const html = this._buildHtml(webview, cssUri, data);
        webview.html = html;
    }

    _buildHtml(webview, cssUri, data) {
        const nonce = getNonce();

        let workflowCards = '';
        let globalIndex = 0;

        if (data.workflows.length === 0) {
            workflowCards = `<div class="empty-state"><div class="empty-icon">📭</div>Chưa có workflow nào</div>`;
        } else {
            data.workflows.forEach((item, i) => {
                const config = getIconConfig(item.name, globalIndex);
                const label = formatLabel(item.name, config.label);
                const escapedTrigger = escapeHtml(item.trigger);
                const escapedDesc = escapeHtml(item.description);

                const escapedName = escapeHtml(item.name);
                workflowCards += `
                    <div class="card" title="${escapedDesc}" data-trigger="${escapedTrigger}" data-name="${escapedName}" data-type="workflow">
                        <div class="card-icon ${config.gradient}">
                            ${config.icon}
                            <span class="badge">✓</span>
                        </div>
                        <div class="card-label">${label}</div>
                    </div>`;
                globalIndex++;
            });
        }

        let skillCards = '';
        if (data.skills.length === 0) {
            skillCards = `<div class="empty-state"><div class="empty-icon">📭</div>Chưa có skill nào</div>`;
        } else {
            data.skills.forEach((item, i) => {
                const config = getIconConfig(item.name, globalIndex);
                const label = formatLabel(item.name, config.label);
                const escapedTrigger = escapeHtml(item.trigger);
                const escapedDesc = escapeHtml(item.description);

                const escapedName = escapeHtml(item.name);
                skillCards += `
                    <div class="card" title="${escapedDesc}" data-trigger="${escapedTrigger}" data-name="${escapedName}" data-type="skill">
                        <div class="card-icon ${config.gradient}">
                            ${config.icon}
                            <span class="badge">✓</span>
                        </div>
                        <div class="card-label">${label}</div>
                    </div>`;
                globalIndex++;
            });
        }

        return `<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';">
    <link rel="stylesheet" href="${cssUri}">
</head>
<body>
    <div class="section-header">
        <span class="section-icon">⚙️</span>
        Quy trình (Workflows)
    </div>
    <div class="grid">
        ${workflowCards}
    </div>

    <div class="section-header">
        <span class="section-icon">👤</span>
        Nhân sự số (Skills)
    </div>
    <div class="grid">
        ${skillCards}
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        document.querySelectorAll('.card[data-trigger]').forEach(card => {
            card.addEventListener('click', () => {
                const trigger = card.getAttribute('data-trigger');
                const itemName = card.getAttribute('data-name') || '';
                const itemType = card.getAttribute('data-type') || 'skill';
                if (trigger) {
                    vscode.postMessage({
                        command: 'runItem',
                        trigger: trigger,
                        itemName: itemName,
                        itemType: itemType,
                    });
                }
            });
        });
    </script>
</body>
</html>`;
    }
}

// ============================================================
// Utility functions
// ============================================================
function getNonce() {
    let text = '';
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 32; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// ============================================================
// Extension Activation
// ============================================================
function activate(context) {
    console.log('AI Workforce Extension v2.0 — Icon Grid Panel activated!');

    const provider = new WorkforcePanelProvider(context.extensionUri);

    const registration = vscode.window.registerWebviewViewProvider(
        'ai-workforce.panel',
        provider,
        { webviewOptions: { retainContextWhenHidden: true } }
    );

    // Command: Refresh
    const refreshCmd = vscode.commands.registerCommand('ai-workforce.refresh', () => {
        provider.refresh();
        vscode.window.showInformationMessage('🔄 AI Workforce: Đã làm mới!');
    });

    // File watcher — auto refresh on changes
    const watcher = vscode.workspace.createFileSystemWatcher('**/.agents/**/*.md');
    watcher.onDidCreate(() => provider.refresh());
    watcher.onDidChange(() => provider.refresh());
    watcher.onDidDelete(() => provider.refresh());

    // Watch known paths too
    for (const knownPath of KNOWN_AGENTS_PATHS) {
        if (fs.existsSync(knownPath)) {
            const absWatcher = vscode.workspace.createFileSystemWatcher(
                new vscode.RelativePattern(vscode.Uri.file(knownPath), '**/*.md')
            );
            absWatcher.onDidCreate(() => provider.refresh());
            absWatcher.onDidChange(() => provider.refresh());
            absWatcher.onDidDelete(() => provider.refresh());
            context.subscriptions.push(absWatcher);
        }
    }

    context.subscriptions.push(registration, refreshCmd, watcher);
}

function deactivate() {}

module.exports = { activate, deactivate };

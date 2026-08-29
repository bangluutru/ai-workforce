const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

// ============================================================
// CẤU HÌNH ĐƯỜNG DẪN CỐ ĐỊNH & DỰ PHÒNG
// Extension sẽ tự động tìm kiếm trên cả macOS, Linux, Windows
// ============================================================
const KNOWN_AGENTS_PATHS = [
    // Antigravity IDE (primary paths)
    path.join(require('os').homedir(), '.gemini', 'antigravity-ide', 'scratch', 'ai-workforce', '.agents'),
    path.join(require('os').homedir(), '.gemini', 'scratch', 'ai-workforce', '.agents'),
    path.join(require('os').homedir(), '.gemini', 'config'),
    // Home-level clones
    path.join(require('os').homedir(), 'ai-workforce', '.agents'),
    path.join(require('os').homedir(), 'Documents', 'ai-workforce', '.agents'),
    path.join(require('os').homedir(), 'Downloads', 'ai-workforce', '.agents'),
    path.join(require('os').homedir(), 'Projects', 'ai-workforce', '.agents'),
    path.join(require('os').homedir(), 'workspace', 'ai-workforce', '.agents'),
];

// ============================================================
// YAML Frontmatter Parser (Hỗ trợ cả CRLF & LF, không cần thư viện ngoài)
// ============================================================
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

// ============================================================
// Tìm thư mục .agents — Tự động nhận diện trên mọi máy và cấu trúc thư mục
// ============================================================
function findAgentsDir() {
    // 1. Kiểm tra trong workspace folders đang mở
    const folders = vscode.workspace.workspaceFolders;
    if (folders) {
        for (const folder of folders) {
            const rootPath = folder.uri.fsPath;
            // .agents trực tiếp ở root workspace
            const direct = path.join(rootPath, '.agents');
            if (fs.existsSync(direct)) return direct;

            // .agents trong subfolder ai-workforce
            const sub = path.join(rootPath, 'ai-workforce', '.agents');
            if (fs.existsSync(sub)) return sub;

            // .agents trong scratch/ai-workforce
            const scratchSub = path.join(rootPath, 'scratch', 'ai-workforce', '.agents');
            if (fs.existsSync(scratchSub)) return scratchSub;
        }
    }

    // 2. Relative to extension location (nếu extension nằm trong thư mục repo)
    try {
        const extRelative = path.join(__dirname, '..', '.agents');
        if (fs.existsSync(extRelative)) return extRelative;
    } catch {}

    // 3. Kiểm tra biến môi trường tùy biến nếu có
    if (process.env.ANTIGRAVITY_AGENTS_DIR && fs.existsSync(process.env.ANTIGRAVITY_AGENTS_DIR)) {
        return process.env.ANTIGRAVITY_AGENTS_DIR;
    }

    // 4. Kiểm tra các đường dẫn phổ biến trên máy người dùng
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
    'ejv-translate':          { icon: '🈂️', gradient: 'gradient-cyan', label: 'EJV\nTranslate' },
    'boc-tach-cv':            { icon: '📄', gradient: 'gradient-orange', label: 'Bóc tách\nCV' },
    'cham-diem-cv':           { icon: '⭐', gradient: 'gradient-amber', label: 'Chấm điểm\nCV' },
    'viet-jd':                { icon: '✏️', gradient: 'gradient-cyan', label: 'Viết JD' },
    'phan-tich-nhan-su':      { icon: '📊', gradient: 'gradient-green', label: 'Phân tích\nnhân sự' },
    'quan-ly-hop-dong':       { icon: '📑', gradient: 'gradient-rose', label: 'Quản lý\nhợp đồng' },
    'tu-van-phap-luat':       { icon: '⚖️', gradient: 'gradient-indigo', label: 'Tư vấn\npháp luật' },
    'xu-ly-van-phong':        { icon: '📝', gradient: 'gradient-blue', label: 'Xử lý\nVăn phòng' },
    'boc-tach-pdf':           { icon: '🖨️', gradient: 'gradient-purple', label: 'Bóc tách\nPDF' },
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
                const needsFile = meta.needs_file === 'true' || meta.needs_file === true || meta.needsFile === 'true' || meta.needsFile === true;
                result.skills.push({
                    name: meta.name || dir,
                    description: meta.description || '',
                    trigger: meta.trigger || `Hãy thực hiện skill "${meta.name || dir}" theo đúng hướng dẫn trong SKILL.md`,
                    type: 'skill',
                    needsFile: needsFile,
                    fileFilter: meta.file_filter || meta.fileFilter || '',
                });
            }
        }
    }

    return result;
}

// ============================================================
// File Picker — Hiện hộp thoại chọn file theo loại skill
// ============================================================
const FILE_FILTER_MAP = {
    pdf: {
        'Tệp PDF (*.pdf)': ['pdf'],
        'Tất cả tệp': ['*']
    },
    office: {
        'Tệp Văn phòng & PDF (*.docx, *.xlsx, *.pptx, *.pdf, ...)': ['docx', 'xlsx', 'pptx', 'pdf', 'doc', 'xls', 'ppt', 'txt', 'csv'],
        'Tất cả tệp': ['*']
    },
    cv: {
        'Tệp CV / Hồ sơ (*.pdf, *.docx, *.doc)': ['pdf', 'docx', 'doc'],
        'Tất cả tệp': ['*']
    },
};

function resolveFileFilters(filterType) {
    if (!filterType) return undefined;
    const lower = filterType.toLowerCase().trim();
    if (FILE_FILTER_MAP[lower]) return FILE_FILTER_MAP[lower];

    // Xử lý chuỗi định dạng tùy biến như "pdf, docx, png"
    const exts = lower.split(/[,|;\s]+/).map(s => s.replace(/^\./, '').trim()).filter(Boolean);
    if (exts.length > 0) {
        return {
            [`Tệp hỗ trợ (*.${exts.join(', *.')})`]: exts,
            'Tất cả tệp': ['*']
        };
    }
    return undefined;
}

async function showFilePickerForSkill(skillName, filterType) {
    const filters = resolveFileFilters(filterType);

    const result = await vscode.window.showOpenDialog({
        canSelectMany: true,
        canSelectFiles: true,
        canSelectFolders: false,
        openLabel: `Chọn tệp cho ${skillName}`,
        title: `Chọn tệp đầu vào cho skill: ${skillName}`,
        filters: filters,
    });

    return result || null;
}

// ============================================================
// Hộp thoại chọn ngôn ngữ đích cho PDF Translate
// ============================================================
const TARGET_LANG_OPTIONS = [
    { label: '🇻🇳 Tiếng Việt (Vietnamese)', code: 'vi', detail: 'Mặc định — Dịch sang tiếng Việt' },
    { label: '🇬🇧 Tiếng Anh (English)', code: 'en', detail: 'Dịch sang tiếng Anh' },
    { label: '🇯🇵 Tiếng Nhật (Japanese)', code: 'ja', detail: 'Dịch sang tiếng Nhật (Kanji/Kana)' },
    { label: '🇨🇳 Tiếng Trung - Giản thể (Chinese Simplified)', code: 'zh-cn', detail: 'Dịch sang tiếng Trung Giản thể' },
    { label: '🇹🇼 Tiếng Trung - Phồn thể (Chinese Traditional)', code: 'zh-tw', detail: 'Dịch sang tiếng Trung Phồn thể' },
    { label: '🇰🇷 Tiếng Hàn (Korean)', code: 'ko', detail: 'Dịch sang tiếng Hàn (Hangul)' },
    { label: '🇫🇷 Tiếng Pháp (French)', code: 'fr', detail: 'Dịch sang tiếng Pháp' },
    { label: '🇩🇪 Tiếng Đức (German)', code: 'de', detail: 'Dịch sang tiếng Đức' },
    { label: '🇪🇸 Tiếng Tây Ban Nha (Spanish)', code: 'es', detail: 'Dịch sang tiếng Tây Ban Nha' },
    { label: '🇷🇺 Tiếng Nga (Russian)', code: 'ru', detail: 'Dịch sang tiếng Nga' },
    { label: '🇹🇭 Tiếng Thái (Thai)', code: 'th', detail: 'Dịch sang tiếng Thái' },
    { label: '🇮🇩 Tiếng Indonesia (Indonesian)', code: 'id', detail: 'Dịch sang tiếng Indonesia' },
    { label: '🇮🇹 Tiếng Ý (Italian)', code: 'it', detail: 'Dịch sang tiếng Ý' },
    { label: '🇵🇹 Tiếng Bồ Đào Nha (Portuguese)', code: 'pt', detail: 'Dịch sang tiếng Bồ Đào Nha' },
    { label: '✏️ Ngôn ngữ khác (Nhập mã ISO)...', code: 'custom', detail: 'Nhập mã ngôn ngữ khác (vd: nl, ar, hi, pl, tr...)' },
];

async function promptTargetLanguage() {
    const selected = await vscode.window.showQuickPick(TARGET_LANG_OPTIONS, {
        placeHolder: '🌐 Chọn ngôn ngữ đích muốn dịch sang (Mặc định: Tiếng Việt):',
        title: 'Tùy chọn ngôn ngữ đích - Dịch PDF (pdf-translate)',
        matchOnDetail: true,
        matchOnDescription: true,
    });

    if (!selected) {
        // User nhấn ESC -> mặc định tiếng Việt
        return { label: '🇻🇳 Tiếng Việt (Vietnamese)', code: 'vi' };
    }

    if (selected.code === 'custom') {
        const customCode = await vscode.window.showInputBox({
            prompt: 'Nhập mã ngôn ngữ đích ISO (vd: it, pt, nl, ar, hi, pl, tr, ...):',
            placeHolder: 'it',
            value: 'it',
        });
        if (customCode && customCode.trim()) {
            return { label: `Mã ${customCode.trim()}`, code: customCode.trim().toLowerCase() };
        }
        return { label: '🇻🇳 Tiếng Việt (Vietnamese)', code: 'vi' };
    }

    return { label: selected.label, code: selected.code };
}

// ============================================================
// GỬI LỆNH TRỰC TIẾP VÀO ANTIGRAVITY CHAT
// Ưu tiên native commands của Antigravity IDE, tự động fallback
// ============================================================
async function sendToAntigravityChat(text) {
    // 1. Luôn lưu sẵn vào Clipboard trước để người dùng có thể dán ngay lập tức
    try {
        await vscode.env.clipboard.writeText(text);
    } catch {}

    // 2. Thử gửi thẳng vào Antigravity Chat Panel
    try {
        await vscode.commands.executeCommand('antigravity.sendPromptToAgentPanel', text);
        vscode.window.showInformationMessage(`🚀 Đã gửi yêu cầu vào Antigravity Chat!`);
        return;
    } catch {}

    // 3. Thử mở và điền vào VS Code / Antigravity standard chat
    try {
        await vscode.commands.executeCommand('workbench.action.chat.open', {
            query: text,
            isPartialQuery: true,
        });
        vscode.window.showInformationMessage(`✅ Đã điền yêu cầu vào Chat! Nhấn Enter để gửi.`);
        return;
    } catch {}

    // 4. Mở cửa sổ chat của Antigravity / Cursor
    const chatFocusCommands = [
        'antigravity.openChatView',
        'antigravity.openAgent',
        'antigravity.toggleChatFocus',
        'workbench.action.chat.open',
        'aichat.newchataction',
        'aichat.focus',
        'gemini.chat.focus',
        'gemini.chat.new',
        'workbench.panel.chatSidebar'
    ];

    let chatOpened = false;
    for (const cmd of chatFocusCommands) {
        try {
            await vscode.commands.executeCommand(cmd);
            chatOpened = true;
            break;
        } catch {}
    }

    if (chatOpened) {
        // Cho giao diện render 300ms rồi thử dán tự động
        await new Promise(resolve => setTimeout(resolve, 300));
        try {
            await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
            vscode.window.showInformationMessage(`✅ Đã dán yêu cầu vào Chat! Nhấn Enter để thực hiện.`);
            return;
        } catch {}

        vscode.window.showInformationMessage(`📋 Đã mở Chat & copy yêu cầu! Nhấn Cmd+V (hoặc Ctrl+V) rồi nhấn Enter.`);
    } else {
        vscode.window.showInformationMessage(
            `📋 Đã copy yêu cầu! Hãy mở Chat Antigravity rồi nhấn Cmd+V (Ctrl+V) để dán.`,
            'Mở Chat'
        ).then(selection => {
            if (selection === 'Mở Chat') {
                vscode.commands.executeCommand('antigravity.openChatView').catch(() => {
                    vscode.commands.executeCommand('antigravity.openAgent').catch(() => {});
                });
            }
        });
    }
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
                    if (message.needsFile) {
                        const filePaths = await showFilePickerForSkill(message.itemName, message.fileFilter);
                        if (filePaths && filePaths.length > 0) {
                            let detailPrompt = message.trigger;
                            if (message.itemName === 'pdf-translate') {
                                const targetLang = await promptTargetLanguage();
                                detailPrompt = `Dịch PDF sang ngôn ngữ đích: ${targetLang.label} (mã: ${targetLang.code}), tự động nhận diện ngôn ngữ nguồn và giữ nguyên toàn bộ bố cục, hình ảnh, bảng biểu.`;
                            }
                            const pathList = filePaths.map(fp => `"${fp.fsPath}"`).join('\n');
                            const prefix = `Hãy thực hiện skill ${message.itemName} với các file sau:\n${pathList}\n\nYêu cầu chi tiết: ${detailPrompt}`;
                            await sendToAntigravityChat(prefix);
                        } else {
                            // User hủy hộp thoại chọn tệp
                            const choice = await vscode.window.showQuickPick(
                                [
                                    { label: '📂 Chọn lại tệp', description: 'Mở lại hộp thoại chọn tệp từ máy tính', action: 'retry' },
                                    { label: '💬 Mở Chat nhập yêu cầu', description: 'Tiếp tục vào khung Chat mà không đính kèm tệp', action: 'proceed' },
                                ],
                                { placeHolder: `Bạn chưa chọn tệp cho skill ${message.itemName}` }
                            );
                            if (choice?.action === 'retry') {
                                const retryPaths = await showFilePickerForSkill(message.itemName, message.fileFilter);
                                if (retryPaths && retryPaths.length > 0) {
                                    let detailPrompt = message.trigger;
                                    if (message.itemName === 'pdf-translate') {
                                        const targetLang = await promptTargetLanguage();
                                        detailPrompt = `Dịch PDF sang ngôn ngữ đích: ${targetLang.label} (mã: ${targetLang.code}), tự động nhận diện ngôn ngữ nguồn và giữ nguyên toàn bộ bố cục, hình ảnh, bảng biểu.`;
                                    }
                                    const pathList = retryPaths.map(fp => `"${fp.fsPath}"`).join('\n');
                                    const prefix = `Hãy thực hiện skill ${message.itemName} với các file sau:\n${pathList}\n\nYêu cầu chi tiết: ${detailPrompt}`;
                                    await sendToAntigravityChat(prefix);
                                }
                            } else if (choice?.action === 'proceed') {
                                let detailPrompt = message.trigger;
                                if (message.itemName === 'pdf-translate') {
                                    const targetLang = await promptTargetLanguage();
                                    detailPrompt = `Dịch PDF sang ngôn ngữ đích: ${targetLang.label} (mã: ${targetLang.code}), tự động nhận diện ngôn ngữ nguồn và giữ nguyên toàn bộ bố cục, hình ảnh, bảng biểu.`;
                                }
                                const prefix = `Hãy thực hiện skill ${message.itemName}.\nYêu cầu: ${detailPrompt}`;
                                await sendToAntigravityChat(prefix);
                            }
                        }
                    } else {
                        // Skill không cần file
                        let detailPrompt = message.trigger;
                        if (message.itemName === 'pdf-translate') {
                            const targetLang = await promptTargetLanguage();
                            detailPrompt = `Dịch PDF sang ngôn ngữ đích: ${targetLang.label} (mã: ${targetLang.code}), tự động nhận diện ngôn ngữ nguồn và giữ nguyên toàn bộ bố cục, hình ảnh, bảng biểu.`;
                        }
                        const prefix = `Hãy thực hiện skill ${message.itemName}.\nYêu cầu: ${detailPrompt}`;
                        await sendToAntigravityChat(prefix);
                    }
                } else {
                    // Workflow: gửi full trigger
                    await sendToAntigravityChat(message.trigger);
                }
            } else if (message.command === 'refresh') {
                this.refresh();
                vscode.window.showInformationMessage('🔄 AI Workforce: Đã làm mới danh sách!');
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
            data.workflows.forEach((item) => {
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
            data.skills.forEach((item) => {
                const config = getIconConfig(item.name, globalIndex);
                const label = formatLabel(item.name, config.label);
                const escapedTrigger = escapeHtml(item.trigger);
                const escapedDesc = escapeHtml(item.description);
                const escapedName = escapeHtml(item.name);
                const fileFilterAttr = item.fileFilter ? `data-file-filter="${escapeHtml(item.fileFilter)}"` : '';
                const needsFileAttr = item.needsFile ? `data-needs-file="true"` : `data-needs-file="false"`;

                const fileBadge = item.needsFile
                    ? `<span class="card-file-badge" title="Skill này sẽ mở hộp thoại chọn tệp để xử lý">📎 Chọn tệp</span>`
                    : '';

                skillCards += `
                    <div class="card ${item.needsFile ? 'card-with-file' : ''}" title="${escapedDesc}" data-trigger="${escapedTrigger}" data-name="${escapedName}" data-type="skill" ${fileFilterAttr} ${needsFileAttr}>
                        ${fileBadge}
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
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
    <link rel="stylesheet" href="${cssUri}">
</head>
<body>
    <div class="top-bar">
        <div class="top-title">🤖 AI Workforce</div>
        <button class="refresh-btn" id="refreshBtn" title="Làm mới danh sách">🔄</button>
    </div>

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

        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            vscode.postMessage({ command: 'refresh' });
        });

        document.querySelectorAll('.card[data-trigger]').forEach(card => {
            card.addEventListener('click', (e) => {
                const trigger = card.getAttribute('data-trigger');
                const itemName = card.getAttribute('data-name') || '';
                const itemType = card.getAttribute('data-type') || 'skill';
                const fileFilter = card.getAttribute('data-file-filter') || '';
                const needsFile = card.getAttribute('data-needs-file') === 'true';
                if (trigger) {
                    vscode.postMessage({
                        command: 'runItem',
                        trigger: trigger,
                        itemName: itemName,
                        itemType: itemType,
                        needsFile: needsFile,
                        fileFilter: fileFilter,
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
    console.log('AI Workforce Extension v2.7.0 activated!');

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

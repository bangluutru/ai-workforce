const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { exec, execSync } = require('child_process');

// ============================================================
// CẤU HÌNH ĐƯỜNG DẪN CỐ ĐỊNH & DỰ PHÒNG
// Extension sẽ tự động tìm kiếm trên cả macOS, Linux, Windows
// ============================================================
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

// ============================================================
// YAML Frontmatter Parser
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
// Tìm thư mục .agents
// ============================================================
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
        const extRelative = path.join(__dirname, '..', '.agents');
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

// ============================================================
// Tìm thư mục gốc ai-workforce (cha của .agents/)
// ============================================================
function findWorkspaceRoot() {
    const agentsDir = findAgentsDir();
    if (agentsDir) {
        return path.dirname(agentsDir);
    }
    return null;
}

// ============================================================
// Icon & Color Mapping
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
    'viet-chuyen-nghiep':     { icon: '✍️', gradient: 'gradient-rose', label: 'Viết\nChuyên nghiệp' },
};

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
        label: null,
    };
}

// ============================================================
// Quét Items (Skills, Workflows, Knowledge Catalog)
// ============================================================
function scanItems() {
    const agentsDir = findAgentsDir();
    if (!agentsDir) return { workflows: [], skills: [], catalog: null };

    const result = { workflows: [], skills: [], catalog: null };

    // 1. Workflows
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

    // 2. Skills
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

    // 3. Knowledge Catalog
    const catalogPath = path.join(agentsDir, 'knowledge', 'catalog.json');
    if (fs.existsSync(catalogPath)) {
        try {
            result.catalog = JSON.parse(fs.readFileSync(catalogPath, 'utf-8'));
        } catch (_) {
            result.catalog = null;
        }
    }

    return result;
}

// ============================================================
// File Picker
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
};

async function showFilePickerForSkill(skillName, fileFilterType) {
    const filters = FILE_FILTER_MAP[fileFilterType] || { 'Tất cả tệp': ['*'] };
    const allowMultiple = (skillName === 'ejv-translate' || skillName === 'pdf-translate');

    const result = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: allowMultiple,
        openLabel: `Chọn tệp cho ${skillName}`,
        title: `AI Workforce: Chọn tệp xử lý (${skillName})`,
        filters: filters,
    });

    return result;
}

// ============================================================
// Target Language Picker
// ============================================================
const TARGET_LANGUAGES = [
    { label: '🇬🇧 Tiếng Anh (English)', code: 'EN', description: 'Dịch sang tiếng Anh chuẩn quốc tế' },
    { label: '🇯🇵 Tiếng Nhật (日本語)', code: 'JP', description: 'Dịch sang tiếng Nhật tự nhiên, chuẩn văn phong' },
    { label: '🇻🇳 Tiếng Việt (Vietnamese)', code: 'VI', description: 'Dịch sang tiếng Việt mạch lạc, chuyên nghiệp' },
    { label: '🇨🇳 Tiếng Trung (中文)', code: 'ZH', description: 'Dịch sang tiếng Trung Giản thể' },
    { label: '🇰🇷 Tiếng Hàn (한국어)', code: 'KO', description: 'Dịch sang tiếng Hàn Quốc' },
    { label: '🇫🇷 Tiếng Pháp (Français)', code: 'FR', description: 'Dịch sang tiếng Pháp' },
    { label: '🇩🇪 Tiếng Đức (Deutsch)', code: 'DE', description: 'Dịch sang tiếng Đức' },
];

async function promptTargetLanguage() {
    const pick = await vscode.window.showQuickPick(
        TARGET_LANGUAGES.map(lang => ({
            label: lang.label,
            description: lang.description,
            code: lang.code,
        })),
        {
            placeHolder: '🌐 Chọn ngôn ngữ đích để dịch tài liệu...',
            title: 'AI Workforce: Chọn ngôn ngữ đích',
            matchOnDescription: true,
        }
    );
    return pick || { label: '🇬🇧 Tiếng Anh (English)', code: 'EN' };
}

// ============================================================
// Gửi lệnh vào Chat của Antigravity
// ============================================================
async function sendToAntigravityChat(promptText) {
    // Step 1: Copy vào clipboard
    await vscode.env.clipboard.writeText(promptText);

    // Step 2: Focus vào chat panel bằng command đã xác minh
    const chatCommands = [
        'workbench.action.smartFocusConversation',   // Antigravity IDE (VERIFIED)
        'antigravity.openConversationWorkspaceQuickPick',  // Fallback
    ];

    let opened = false;
    for (const cmd of chatCommands) {
        try {
            await vscode.commands.executeCommand(cmd);
            opened = true;
            break;
        } catch (_) {
            // Command không tồn tại, thử command tiếp theo
        }
    }

    if (opened) {
        // Step 3: Chờ chat panel mở xong rồi paste tự động
        await new Promise(resolve => setTimeout(resolve, 400));
        try {
            await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
        } catch (_) {
            // Paste tự động thất bại — thông báo user paste thủ công
            vscode.window.showInformationMessage(
                '📋 Đã sao chép yêu cầu! Nhấn Cmd+V (Mac) hoặc Ctrl+V (Win) để dán vào chat.'
            );
        }
    } else {
        // Fallback: Thông báo user paste thủ công
        vscode.window.showWarningMessage(
            '📋 Đã sao chép yêu cầu vào clipboard! Mở Chat và dán (Cmd+V / Ctrl+V).'
        );
    }
}

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

// ============================================================
// WebviewViewProvider
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

        // Xử lý các tương tác từ Webview
        webviewView.webview.onDidReceiveMessage(async (message) => {
            const workspaceRoot = findWorkspaceRoot();

            // 1. Chạy Skill / Workflow
            if (message.command === 'runItem') {
                if (message.itemType === 'skill') {
                    if (message.needsFile) {
                        const filePaths = await showFilePickerForSkill(message.itemName, message.fileFilter);
                        if (filePaths && filePaths.length > 0) {
                            let detailPrompt = message.trigger;
                            if (message.itemName === 'pdf-translate' || message.itemName === 'ejv-translate') {
                                const targetLang = await promptTargetLanguage();
                                detailPrompt = `Dịch sang ngôn ngữ đích: ${targetLang.label} (mã: ${targetLang.code}), tự động nhận diện ngôn ngữ nguồn và giữ nguyên toàn bộ bố cục.`;
                            }
                            const pathList = filePaths.map(fp => `"${fp.fsPath}"`).join('\n');
                            const prefix = `Hãy thực hiện skill ${message.itemName} với các file sau:\n${pathList}\n\nYêu cầu chi tiết: ${detailPrompt}`;
                            await sendToAntigravityChat(prefix);
                        }
                    } else {
                        let detailPrompt = message.trigger;
                        if (message.itemName === 'pdf-translate' || message.itemName === 'ejv-translate') {
                            const targetLang = await promptTargetLanguage();
                            detailPrompt = `Dịch sang ngôn ngữ đích: ${targetLang.label} (mã: ${targetLang.code}), tự động nhận diện ngôn ngữ nguồn.`;
                        }
                        const prefix = `Hãy thực hiện skill ${message.itemName}.\nYêu cầu: ${detailPrompt}`;
                        await sendToAntigravityChat(prefix);
                    }
                } else {
                    await sendToAntigravityChat(message.trigger);
                }
            }
            // 2. Làm mới toàn bộ UI
            else if (message.command === 'refresh') {
                this.refresh();
                vscode.window.showInformationMessage('🔄 AI Workforce: Đã làm mới giao diện!');
            }
            // 3. Quét nhanh mục lục Notebook (Scan Catalog)
            else if (message.command === 'scanCatalog') {
                if (!workspaceRoot) {
                    vscode.window.showErrorMessage('Không tìm thấy thư mục ai-workforce workspace');
                    return;
                }
                const scanScript = path.join(workspaceRoot, 'scripts', 'scan_catalog.py');
                vscode.window.showInformationMessage('⚡ Đang quét danh mục Gemini Notebook...');
                exec(`python3 "${scanScript}"`, { cwd: workspaceRoot }, (err, stdout) => {
                    if (err) {
                        vscode.window.showErrorMessage(`⚠️ Lỗi quét mục lục: ${err.message}`);
                    } else {
                        vscode.window.showInformationMessage('✅ Đã cập nhật Bản đồ Tri thức thông minh!');
                        this.refresh();
                    }
                });
            }
            // 4. Đồng bộ 1 Notebook cụ thể
            else if (message.command === 'syncNotebook') {
                if (!workspaceRoot) return;
                const syncScript = path.join(workspaceRoot, 'scripts', 'sync_notebook.py');
                const nbId = message.notebookId;
                const nbTitle = message.notebookTitle || nbId;

                vscode.window.showInformationMessage(`🔄 Đang đồng bộ "${nbTitle}"...`);
                exec(`python3 "${syncScript}" --notebook-id "${nbId}"`, { cwd: workspaceRoot, timeout: 300000 }, (err) => {
                    if (err) {
                        vscode.window.showErrorMessage(`⚠️ Lỗi sync: ${err.message}`);
                    } else {
                        vscode.window.showInformationMessage(`✅ Đã đồng bộ xong notebook "${nbTitle}"!`);
                        // Cập nhật lại catalog
                        const scanScript = path.join(workspaceRoot, 'scripts', 'scan_catalog.py');
                        try { execSync(`python3 "${scanScript}"`, { cwd: workspaceRoot }); } catch(_) {}
                        this.refresh();
                    }
                });
            }
            // 5. Dịch tài liệu từ Notebook
            else if (message.command === 'translateDoc') {
                const targetLang = await promptTargetLanguage();
                const filePath = message.localFilePath;
                let fileRef = '';
                if (filePath && workspaceRoot) {
                    const fullPath = path.isAbsolute(filePath) ? filePath : path.join(workspaceRoot, filePath);
                    if (fs.existsSync(fullPath)) {
                        fileRef = `\nFile local: "${fullPath}"`;
                    }
                }
                const prompt = `Hãy thực hiện skill ejv-translate để dịch tài liệu "${message.docTitle}" (thuộc notebook "${message.notebookTitle}") sang ${targetLang.label}.${fileRef}`;
                await sendToAntigravityChat(prompt);
            }
            // 6. Tra cứu / Hỏi về tài liệu
            else if (message.command === 'askDoc') {
                const filePath = message.localFilePath;
                let fileRef = '';
                if (filePath && workspaceRoot) {
                    const fullPath = path.isAbsolute(filePath) ? filePath : path.join(workspaceRoot, filePath);
                    if (fs.existsSync(fullPath)) {
                        fileRef = `\nFile local: "${fullPath}"`;
                    }
                }
                const prompt = `Dựa vào tài liệu "${message.docTitle}" trong notebook "${message.notebookTitle}", hãy tóm tắt nội dung chính và phân tích các điểm quan trọng nhất.${fileRef}`;
                await sendToAntigravityChat(prompt);
            }
            // 7. Mở file Markdown local (click vào tên tài liệu)
            else if (message.command === 'openDoc') {
                if (!workspaceRoot) return;
                const filePath = message.localFilePath;
                if (filePath) {
                    const fullPath = path.isAbsolute(filePath)
                        ? filePath
                        : path.join(workspaceRoot, filePath);
                    if (fs.existsSync(fullPath)) {
                        try {
                            const doc = await vscode.workspace.openTextDocument(fullPath);
                            await vscode.window.showTextDocument(doc, { preview: true });
                        } catch (err) {
                            vscode.window.showErrorMessage(`⚠️ Không thể mở file: ${err.message}`);
                        }
                    } else {
                        // File chưa sync — hỏi có muốn tóm tắt từ AI không
                        const action = await vscode.window.showWarningMessage(
                            `📄 Tài liệu "${message.docTitle}" chưa được sync về local.`,
                            'Đồng bộ ngay',
                            'Hỏi AI về tài liệu này'
                        );
                        if (action === 'Đồng bộ ngay' && message.notebookId) {
                            const syncScript = path.join(workspaceRoot, 'scripts', 'sync_notebook.py');
                            vscode.window.showInformationMessage(`🔄 Đang đồng bộ notebook...`);
                            exec(`python3 "${syncScript}" --notebook-id "${message.notebookId}"`, { cwd: workspaceRoot, timeout: 300000 }, (err) => {
                                if (err) {
                                    vscode.window.showErrorMessage(`⚠️ Lỗi sync: ${err.message}`);
                                } else {
                                    vscode.window.showInformationMessage(`✅ Đã sync xong! Thử mở lại tài liệu.`);
                                    const scanScript = path.join(workspaceRoot, 'scripts', 'scan_catalog.py');
                                    try { execSync(`python3 "${scanScript}"`, { cwd: workspaceRoot }); } catch(_) {}
                                    this.refresh();
                                }
                            });
                        } else if (action === 'Hỏi AI về tài liệu này') {
                            const prompt = `Dựa vào tài liệu "${message.docTitle}" trong notebook "${message.notebookTitle}", hãy tóm tắt nội dung chính và phân tích các điểm quan trọng nhất.`;
                            await sendToAntigravityChat(prompt);
                        }
                    }
                } else {
                    // Không có local path — notebook chưa sync
                    const action = await vscode.window.showWarningMessage(
                        `📄 Notebook chứa tài liệu này chưa được sync về local.`,
                        'Đồng bộ ngay',
                        'Hỏi AI về tài liệu này'
                    );
                    if (action === 'Đồng bộ ngay' && message.notebookId) {
                        const syncScript = path.join(workspaceRoot, 'scripts', 'sync_notebook.py');
                        vscode.window.showInformationMessage(`🔄 Đang đồng bộ notebook...`);
                        exec(`python3 "${syncScript}" --notebook-id "${message.notebookId}"`, { cwd: workspaceRoot, timeout: 300000 }, (err) => {
                            if (err) {
                                vscode.window.showErrorMessage(`⚠️ Lỗi sync: ${err.message}`);
                            } else {
                                vscode.window.showInformationMessage(`✅ Đã sync xong! Thử mở lại tài liệu.`);
                                const scanScript = path.join(workspaceRoot, 'scripts', 'scan_catalog.py');
                                try { execSync(`python3 "${scanScript}"`, { cwd: workspaceRoot }); } catch(_) {}
                                this.refresh();
                            }
                        });
                    } else if (action === 'Hỏi AI về tài liệu này') {
                        const prompt = `Dựa vào tài liệu "${message.docTitle}" trong notebook "${message.notebookTitle}", hãy tóm tắt nội dung chính và phân tích các điểm quan trọng nhất.`;
                        await sendToAntigravityChat(prompt);
                    }
                }
            }
            // 8. Mở file Markdown local (legacy)
            else if (message.command === 'openFile') {
                if (!workspaceRoot || !message.filePath) return;
                const fullPath = path.isAbsolute(message.filePath)
                    ? message.filePath
                    : path.join(workspaceRoot, message.filePath);
                if (fs.existsSync(fullPath)) {
                    try {
                        const doc = await vscode.workspace.openTextDocument(fullPath);
                        await vscode.window.showTextDocument(doc);
                    } catch (err) {
                        vscode.window.showErrorMessage(`⚠️ Không thể mở file: ${err.message}`);
                    }
                } else {
                    vscode.window.showWarningMessage(`File chưa tồn tại ở local. Hãy nhấn [Đồng bộ] trước.`);
                }
            }
            // 8. Sao chép Notebook ID
            else if (message.command === 'copyId') {
                await vscode.env.clipboard.writeText(message.id);
                vscode.window.showInformationMessage(`📋 Đã sao chép ID: ${message.id}`);
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

        // 1. Render Workflows
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

        // 2. Render Skills
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
                    ? `<span class="card-file-badge" title="Chọn tệp từ máy tính">📎 Chọn tệp</span>`
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

        // 3. Render Knowledge Catalog
        let catalogHtml = '';
        const catalog = data.catalog;

        if (!catalog || !catalog.categories) {
            catalogHtml = `
                <div class="empty-state">
                    <div class="empty-icon">📚</div>
                    <p>Chưa có dữ liệu mục lục</p>
                    <button class="catalog-scan-btn" style="margin-top:10px;" id="btnInitialScan">⚡ Quét mục lục ngay</button>
                </div>`;
        } else {
            // Stats Bar
            let statsHtml = `
                <div class="catalog-stats-bar">
                    <div class="stat-pill">📓 <b>${catalog.total_notebooks}</b> Notebooks</div>
                    <div class="stat-pill">📄 <b>${catalog.total_sources}</b> Tài liệu</div>
                    <div class="stat-pill highlight">✅ <b>${catalog.synced_notebooks}</b> Đã sync</div>
                </div>`;

            // Filter Pills Bar
            let filterPills = `<button class="filter-pill active" data-cat="all">Tất cả (${catalog.total_notebooks})</button>`;
            for (const [catId, group] of Object.entries(catalog.categories)) {
                if (group.notebooks.length > 0) {
                    filterPills += `<button class="filter-pill" data-cat="${catId}">${group.category.icon} ${group.category.name} (${group.notebooks.length})</button>`;
                }
            }
            const filterPillsHtml = `<div class="filter-pills">${filterPills}</div>`;

            // Accordion Groups
            let categoriesAccordion = '';
            for (const [catId, group] of Object.entries(catalog.categories)) {
                const nbs = group.notebooks;
                if (!nbs || nbs.length === 0) continue;

                const cat = group.category;
                const totalCatSources = nbs.reduce((acc, nb) => acc + nb.source_count, 0);

                let nbCardsHtml = '';
                nbs.forEach(nb => {
                    const isSynced = nb.sync_info && nb.sync_info.is_synced;
                    const localBasePath = (isSynced && nb.sync_info.local_path) ? nb.sync_info.local_path : '';
                    const syncBadge = isSynced
                        ? `<span class="nb-badge-synced">✅ Đã sync (${nb.sync_info.synced_sources || nb.source_count})</span>`
                        : `<span class="nb-badge-cloud">☁️ Trên mây (${nb.source_count})</span>`;

                    // Render source list
                    let sourcesHtml = '';
                    if (nb.sources && nb.sources.length > 0) {
                        nb.sources.forEach((src, srcIdx) => {
                            const icon = (src.type && src.type.toLowerCase().includes('pdf')) ? '📕' : '📄';
                            const escapedSrcTitle = escapeHtml(src.title);
                            const escapedNbTitle = escapeHtml(nb.title);

                            // Tính đường dẫn file local nếu đã sync
                            let localFilePath = '';
                            if (localBasePath) {
                                const srcNum = String(srcIdx + 1).padStart(2, '0');
                                const slug = src.title.toLowerCase()
                                    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                                    .replace(/đ/g, 'd').replace(/Đ/g, 'd')
                                    .replace(/[^a-z0-9]+/g, '_')
                                    .replace(/^_|_$/g, '')
                                    .substring(0, 70);
                                localFilePath = `${localBasePath}/artifacts/sources/source_${srcNum}_${slug}.md`;
                            }
                            const localFileAttr = localFilePath ? `data-local-file="${escapeHtml(localFilePath)}"` : '';

                            sourcesHtml += `
                                <div class="source-item" data-src-title="${escapedSrcTitle.toLowerCase()}">
                                    <div class="source-item-title clickable-doc" title="${isSynced ? 'Click để mở tài liệu' : 'Click để xem (cần sync trước)'}" data-src-title="${escapedSrcTitle}" data-nb-title="${escapedNbTitle}" data-nb-id="${nb.id}" ${localFileAttr}>
                                        <span>${icon}</span>
                                        <span>${escapedSrcTitle}</span>
                                    </div>
                                    <div class="source-actions">
                                        <button class="src-btn src-btn-trans" title="Dịch tài liệu này" data-src-title="${escapedSrcTitle}" data-nb-title="${escapedNbTitle}" data-nb-id="${nb.id}" ${localFileAttr}>🌐</button>
                                        <button class="src-btn src-btn-ask" title="Hỏi AI về tài liệu này" data-src-title="${escapedSrcTitle}" data-nb-title="${escapedNbTitle}" ${localFileAttr}>💬</button>
                                    </div>
                                </div>`;
                        });
                    } else {
                        sourcesHtml = `<div style="font-size:10px; color:var(--vscode-descriptionForeground); padding:4px;">Chưa có tài liệu</div>`;
                    }

                    nbCardsHtml += `
                        <div class="nb-card" data-nb-id="${nb.id}" data-nb-title="${escapeHtml(nb.title).toLowerCase()}" data-cat="${catId}">
                            <div class="nb-top">
                                <div class="nb-title-block nb-toggle-trigger">
                                    <span style="font-size:12px;">📓</span>
                                    <div class="nb-title">${escapeHtml(nb.title)}</div>
                                </div>
                                <div class="nb-actions">
                                    <button class="nb-btn-sync" data-nb-id="${nb.id}" data-nb-title="${escapeHtml(nb.title)}" title="Đồng bộ toàn bộ nội dung về local">🔄 Sync</button>
                                    <button class="nb-btn-toggle nb-toggle-trigger" title="Mở/đóng danh sách tài liệu">▼</button>
                                </div>
                            </div>
                            <div class="nb-meta-row">
                                ${syncBadge}
                                <span style="color:var(--vscode-descriptionForeground); font-size:9px; cursor:pointer;" class="btn-copy-id" data-id="${nb.id}" title="Nhấn để copy ID">📋 ID</span>
                            </div>
                            <div class="source-list">
                                ${sourcesHtml}
                            </div>
                        </div>`;
                });

                categoriesAccordion += `
                    <div class="cat-group open" data-cat="${catId}">
                        <div class="cat-header">
                            <div class="cat-header-left">
                                <span>${cat.icon}</span>
                                <span>${cat.name}</span>
                            </div>
                            <div class="cat-header-right">
                                <span class="cat-count-badge">${nbs.length} NBs • ${totalCatSources} docs</span>
                                <span class="cat-arrow">▶</span>
                            </div>
                        </div>
                        <div class="cat-content">
                            ${nbCardsHtml}
                        </div>
                    </div>`;
            }

            catalogHtml = `
                ${statsHtml}
                <div class="catalog-search-row">
                    <div class="search-input-wrapper">
                        <span class="search-icon">🔍</span>
                        <input type="text" id="catalogSearchInput" class="catalog-search-input" placeholder="Tìm theo tên tài liệu, notebook, số hiệu...">
                    </div>
                    <button class="catalog-scan-btn" id="btnScanCatalog" title="Quét cập nhật nhanh toàn bộ danh mục từ Google">⚡ Quét</button>
                </div>
                ${filterPillsHtml}
                <div id="catalogAccordionContainer">
                    ${categoriesAccordion}
                </div>
                <div id="catalogEmptySearch" class="catalog-empty-search" style="display:none;">
                    Không tìm thấy tài liệu hoặc notebook nào khớp với từ khóa.
                </div>`;
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
        <div class="top-title">🤖 AI WORKFORCE</div>
        <button class="refresh-btn" id="refreshBtn" title="Làm mới toàn bộ danh sách">🔄</button>
    </div>

    <!-- Navigation Tabs -->
    <div class="tab-bar">
        <button class="tab-btn active" id="tabBtnSkills" data-tab="tabSkills">
            ⚡ Tác vụ <span class="tab-badge">${data.skills.length + data.workflows.length}</span>
        </button>
        <button class="tab-btn" id="tabBtnCatalog" data-tab="tabCatalog">
            📚 Tri thức <span class="tab-badge">${catalog ? catalog.total_notebooks : 0}</span>
        </button>
    </div>

    <!-- Tab 1: Skills & Workflows -->
    <div class="tab-content active" id="tabSkills">
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
    </div>

    <!-- Tab 2: Knowledge Catalog -->
    <div class="tab-content" id="tabCatalog">
        ${catalogHtml}
    </div>

    <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();

        // 1. Chuyển Tab
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                btn.classList.add('active');
                const targetTabId = btn.getAttribute('data-tab');
                document.getElementById(targetTabId)?.classList.add('active');
            });
        });

        // 2. Làm mới
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            vscode.postMessage({ command: 'refresh' });
        });

        // 3. Quét mục lục
        document.getElementById('btnScanCatalog')?.addEventListener('click', () => {
            vscode.postMessage({ command: 'scanCatalog' });
        });
        document.getElementById('btnInitialScan')?.addEventListener('click', () => {
            vscode.postMessage({ command: 'scanCatalog' });
        });

        // 4. Chạy Skill / Workflow Card
        document.querySelectorAll('.card[data-trigger]').forEach(card => {
            card.addEventListener('click', () => {
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

        // 5. Accordion Category Toggle
        document.querySelectorAll('.cat-header').forEach(header => {
            header.addEventListener('click', () => {
                const group = header.closest('.cat-group');
                group?.classList.toggle('open');
            });
        });

        // 6. Accordion Notebook Toggle (mở danh sách sources)
        document.querySelectorAll('.nb-toggle-trigger').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                const card = trigger.closest('.nb-card');
                card?.classList.toggle('open');
                const btn = card?.querySelector('.nb-btn-toggle');
                if (btn) btn.textContent = card?.classList.contains('open') ? '▲' : '▼';
            });
        });

        // 7. Đồng bộ Notebook
        document.querySelectorAll('.nb-btn-sync').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const nbId = btn.getAttribute('data-nb-id');
                const nbTitle = btn.getAttribute('data-nb-title');
                vscode.postMessage({
                    command: 'syncNotebook',
                    notebookId: nbId,
                    notebookTitle: nbTitle,
                });
            });
        });

        // 8. Copy ID
        document.querySelectorAll('.btn-copy-id').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const id = btn.getAttribute('data-id');
                vscode.postMessage({ command: 'copyId', id: id });
            });
        });

        // 9. Click vào tên tài liệu → mở file local
        document.querySelectorAll('.clickable-doc').forEach(el => {
            el.addEventListener('click', (e) => {
                e.stopPropagation();
                const docTitle = el.getAttribute('data-src-title');
                const nbTitle = el.getAttribute('data-nb-title');
                const nbId = el.getAttribute('data-nb-id');
                const localFile = el.getAttribute('data-local-file');
                vscode.postMessage({
                    command: 'openDoc',
                    docTitle: docTitle,
                    notebookTitle: nbTitle,
                    notebookId: nbId,
                    localFilePath: localFile || '',
                });
            });
        });

        // 10. Dịch tài liệu (icon 🌐)
        document.querySelectorAll('.src-btn-trans').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const docTitle = btn.getAttribute('data-src-title');
                const nbTitle = btn.getAttribute('data-nb-title');
                const nbId = btn.getAttribute('data-nb-id');
                const localFile = btn.getAttribute('data-local-file');
                vscode.postMessage({
                    command: 'translateDoc',
                    docTitle: docTitle,
                    notebookTitle: nbTitle,
                    notebookId: nbId,
                    localFilePath: localFile || '',
                });
            });
        });

        // 11. Hỏi AI về tài liệu (icon 💬)
        document.querySelectorAll('.src-btn-ask').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const docTitle = btn.getAttribute('data-src-title');
                const nbTitle = btn.getAttribute('data-nb-title');
                const localFile = btn.getAttribute('data-local-file');
                vscode.postMessage({
                    command: 'askDoc',
                    docTitle: docTitle,
                    notebookTitle: nbTitle,
                    localFilePath: localFile || '',
                });
            });
        });

        // 11. Bộ lọc Category Pills
        let currentCatFilter = 'all';
        document.querySelectorAll('.filter-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                currentCatFilter = pill.getAttribute('data-cat') || 'all';
                applyFilters();
            });
        });

        // 12. Real-time Search Input
        const searchInput = document.getElementById('catalogSearchInput');
        searchInput?.addEventListener('input', () => {
            applyFilters();
        });

        function applyFilters() {
            const query = (searchInput?.value || '').trim().toLowerCase();
            const catGroups = document.querySelectorAll('.cat-group');
            let totalVisible = 0;

            catGroups.forEach(group => {
                const groupCat = group.getAttribute('data-cat');
                const matchesCat = (currentCatFilter === 'all' || currentCatFilter === groupCat);

                if (!matchesCat) {
                    group.style.display = 'none';
                    return;
                }

                const nbCards = group.querySelectorAll('.nb-card');
                let visibleNbInGroup = 0;

                nbCards.forEach(card => {
                    const nbTitle = card.getAttribute('data-nb-title') || '';
                    const srcItems = card.querySelectorAll('.source-item');
                    let hasMatchingSource = false;

                    srcItems.forEach(src => {
                        const srcTitle = src.getAttribute('data-src-title') || '';
                        if (!query || srcTitle.includes(query)) {
                            src.style.display = 'flex';
                            hasMatchingSource = true;
                        } else {
                            src.style.display = 'none';
                        }
                    });

                    const matchesNb = !query || nbTitle.includes(query) || hasMatchingSource;

                    if (matchesNb) {
                        card.style.display = 'block';
                        visibleNbInGroup++;
                        if (query && hasMatchingSource) {
                            card.classList.add('open'); // Tự động mở rộng nếu tìm thấy source khớp
                        }
                    } else {
                        card.style.display = 'none';
                    }
                });

                if (visibleNbInGroup > 0) {
                    group.style.display = 'block';
                    group.classList.add('open');
                    totalVisible += visibleNbInGroup;
                } else {
                    group.style.display = 'none';
                }
            });

            const emptyNotice = document.getElementById('catalogEmptySearch');
            if (emptyNotice) {
                emptyNotice.style.display = (totalVisible === 0) ? 'block' : 'none';
            }
        }
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
    const provider = new WorkforcePanelProvider(context.extensionUri);

    const registration = vscode.window.registerWebviewViewProvider(
        'ai-workforce.panel',
        provider,
        { webviewOptions: { retainContextWhenHidden: true } }
    );

    // Command: Refresh
    const refreshCmd = vscode.commands.registerCommand('ai-workforce.refresh', async () => {
        provider.refresh();
        vscode.window.showInformationMessage('🔄 AI Workforce: Đã làm mới giao diện!');
    });

    // File watcher — auto refresh on changes in .agents or knowledge
    const watcher = vscode.workspace.createFileSystemWatcher('**/.agents/**/*.md');
    watcher.onDidCreate(() => provider.refresh());
    watcher.onDidChange(() => provider.refresh());
    watcher.onDidDelete(() => provider.refresh());

    const catalogWatcher = vscode.workspace.createFileSystemWatcher('**/.agents/knowledge/catalog.json');
    catalogWatcher.onDidCreate(() => provider.refresh());
    catalogWatcher.onDidChange(() => provider.refresh());
    catalogWatcher.onDidDelete(() => provider.refresh());

    context.subscriptions.push(registration, refreshCmd, watcher, catalogWatcher);
}

function deactivate() {}

module.exports = { activate, deactivate };

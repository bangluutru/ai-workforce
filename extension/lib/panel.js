/**
 * panel.js — WorkforcePanelProvider (WebviewViewProvider)
 *
 * Xử lý toàn bộ giao diện Sidebar của AI Workforce extension:
 * - Render HTML cho webview (Skills, Workflows, Knowledge Catalog)
 * - Xử lý message từ webview (chạy skill, sync notebook, mở file...)
 * - Quản lý vòng đời refresh/update
 */

const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const { exec, execSync } = require('child_process');
const { findWorkspaceRoot, getNonce, escapeHtml, formatLabel } = require('./utils');
const { getIconConfig } = require('./icons');
const { scanItems } = require('./scanner');
const {
    selectDocumentSourceForSkill,
    promptTargetLanguage,
    sendToAntigravityChat,
} = require('./pickers');
const { openInteractivePanel, findActiveSessions } = require('./interactive_panel');

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
                    const catalog = scanItems().catalog;
                    const docSource = await selectDocumentSourceForSkill(
                        message.itemName,
                        message.fileFilter,
                        catalog,
                        workspaceRoot
                    );

                    if (!docSource) return; // Người dùng huỷ chọn

                    // Trường hợp A: Chọn tệp từ máy tính
                    if (docSource.type === 'local_files') {
                        let detailPrompt = message.trigger;
                        if (message.itemName === 'pdf-translate' || message.itemName === 'ejv-translate' || message.itemName === 'dich-giu-dinh-dang') {
                            const targetLang = await promptTargetLanguage();
                            detailPrompt = `Dịch sang ngôn ngữ đích: ${targetLang.label} (mã: ${targetLang.code}), tự động nhận diện ngôn ngữ nguồn và giữ nguyên toàn bộ bố cục.`;
                        }
                        const pathList = docSource.filePaths.map(fp => `"${fp.fsPath}"`).join('\n');
                        const prefix = `Hãy thực hiện skill ${message.itemName} với các file sau:\n${pathList}\n\nYêu cầu chi tiết: ${detailPrompt}`;
                        await sendToAntigravityChat(prefix);
                    }
                    // Trường hợp B: Chọn tài liệu từ Gemini Notebook (Mục lục tri thức)
                    else if (docSource.type === 'notebook_doc') {
                        let fileRef = '';
                        if (docSource.localFilePath && workspaceRoot) {
                            const fullPath = path.isAbsolute(docSource.localFilePath)
                                ? docSource.localFilePath
                                : path.join(workspaceRoot, docSource.localFilePath);
                            if (fs.existsSync(fullPath)) {
                                fileRef = `\nFile local: "${fullPath}"`;
                            }
                        }

                        if (message.itemName === 'pdf-translate' || message.itemName === 'ejv-translate' || message.itemName === 'dich-giu-dinh-dang') {
                            const targetLang = await promptTargetLanguage();
                            const prompt = `Hãy thực hiện skill ${message.itemName} để dịch tài liệu "${docSource.docTitle}" (thuộc notebook "${docSource.notebookTitle}") sang ${targetLang.label}.${fileRef}`;
                            await sendToAntigravityChat(prompt);
                        } else {
                            let detailPrompt = message.trigger;
                            const prompt = `Hãy thực hiện skill ${message.itemName} với tài liệu "${docSource.docTitle}" (thuộc notebook "${docSource.notebookTitle}").${fileRef}\n\nYêu cầu: ${detailPrompt}`;
                            await sendToAntigravityChat(prompt);
                        }
                    }
                    // Trường hợp C: Thực hiện trực tiếp (Không kèm tệp)
                    else if (docSource.type === 'direct') {
                        let detailPrompt = message.trigger;
                        if (message.itemName === 'pdf-translate' || message.itemName === 'ejv-translate' || message.itemName === 'dich-giu-dinh-dang') {
                            const targetLang = await promptTargetLanguage();
                            detailPrompt = `Dịch sang ngôn ngữ đích: ${targetLang.label} (mã: ${targetLang.code}), tự động nhận diện ngôn ngữ nguồn.`;
                        }
                        const prefix = `Hãy thực hiện skill ${message.itemName}.\nYêu cầu: ${detailPrompt}`;
                        await sendToAntigravityChat(prefix);
                    }
                } else {
                    // Workflow
                    if (message.action === 'open_handbook' || message.itemName === 'W0-so-tay-aiwf' || message.itemName === 'so-tay-aiwf') {
                        const targetPath = message.targetFile || 'docs/AIWF_USER_HANDBOOK.md';
                        const fullPath = path.isAbsolute(targetPath)
                            ? targetPath
                            : path.join(workspaceRoot, targetPath);
                        if (fs.existsSync(fullPath)) {
                            try {
                                const docUri = vscode.Uri.file(fullPath);
                                await vscode.commands.executeCommand('markdown.showPreview', docUri);
                                vscode.window.showInformationMessage('📖 Đã mở Sổ tay AIWF!');
                            } catch (_) {
                                const doc = await vscode.workspace.openTextDocument(fullPath);
                                await vscode.window.showTextDocument(doc);
                            }
                        } else {
                            vscode.window.showWarningMessage(`Không tìm thấy file ${targetPath}`);
                        }
                    } else {
                        await sendToAntigravityChat(message.trigger);
                    }
                }
            }
            // 1b. Mở phòng dựng tương tác (Interactive Session)
            else if (message.command === 'openInteractiveSession') {
                if (message.projectPath) {
                    await openInteractivePanel(message.projectPath, message.skillName, this._extensionUri);
                }
            }
            // 1c. Áp dụng Skill lên tài liệu cụ thể trong Notebook (từ Tab Tri thức)
            else if (message.command === 'applySkillToDoc') {
                const skillsList = scanItems().skills;
                const skillChoices = skillsList.map(s => {
                    const iconCfg = getIconConfig(s.name, 0);
                    return {
                        label: `${iconCfg.icon} ${s.name}`,
                        description: s.description,
                        skill: s
                    };
                });

                if (skillChoices.length === 0) {
                    vscode.window.showWarningMessage('Chưa có skill nào sẵn sàng.');
                    return;
                }

                const chosen = await vscode.window.showQuickPick(skillChoices, {
                    placeHolder: `Chọn skill áp dụng cho "${message.docTitle}"...`,
                    title: `AI Workforce: Áp dụng Skill cho tài liệu`,
                    matchOnDescription: true
                });

                if (!chosen) return;

                const selectedSkill = chosen.skill;
                const filePath = message.localFilePath;
                let fileRef = '';
                if (filePath && workspaceRoot) {
                    const fullPath = path.isAbsolute(filePath) ? filePath : path.join(workspaceRoot, filePath);
                    if (fs.existsSync(fullPath)) {
                        fileRef = `\nFile local: "${fullPath}"`;
                    }
                }

                if (selectedSkill.name === 'pdf-translate' || selectedSkill.name === 'ejv-translate' || selectedSkill.name === 'dich-giu-dinh-dang') {
                    const targetLang = await promptTargetLanguage();
                    const prompt = `Hãy thực hiện skill ${selectedSkill.name} để dịch tài liệu "${message.docTitle}" (thuộc notebook "${message.notebookTitle}") sang ${targetLang.label}.${fileRef}`;
                    await sendToAntigravityChat(prompt);
                } else {
                    const prompt = `Hãy thực hiện skill ${selectedSkill.name} với tài liệu "${message.docTitle}" (thuộc notebook "${message.notebookTitle}").${fileRef}\n\nYêu cầu: ${selectedSkill.trigger}`;
                    await sendToAntigravityChat(prompt);
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
            // 9. Sao chép Notebook ID
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

        // 0. Quét phiên tương tác đang hoạt động (ISP v1.0)
        let interactiveSessionsHtml = '';
        try {
            const activeSessions = findActiveSessions();
            if (activeSessions.length > 0) {
                let sessionCards = '';
                activeSessions.forEach(s => {
                    sessionCards += `
                        <div class="interactive-session-card" data-project-path="${escapeHtml(s.projectPath)}" data-skill-name="${escapeHtml(s.skillName)}" title="Nhấn để mở phòng dựng tương tác" style="background:#1e293b; border:1px solid #3b82f6; border-radius:6px; padding:8px 10px; margin-bottom:8px; cursor:pointer;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <span style="font-weight:600; font-size:11px; color:#60a5fa;">⚡ ${escapeHtml(s.skillName)}</span>
                                <span style="font-size:9px; background:#1e3a8a; color:#93c5fd; padding:1px 6px; border-radius:10px;">${escapeHtml(s.status)}</span>
                            </div>
                            <div style="font-size:11px; color:#e2e8f0; word-break:break-all; font-family:monospace;">📁 ${escapeHtml(s.projectId)}</div>
                            <div style="font-size:10px; color:#38bdf8; margin-top:4px;">▶ Mở phòng dựng (Editor Tab)</div>
                        </div>`;
                });
                interactiveSessionsHtml = `
                    <div class="section-header" style="color: #60a5fa;">
                        <span class="section-icon">🎨</span>
                        Phiên tương tác đang mở (${activeSessions.length})
                    </div>
                    <div class="interactive-sessions-list" style="margin-bottom: 12px;">
                        ${sessionCards}
                    </div>`;
            }
        } catch (_) {}

        // 1. Phân loại & đếm số lượng Tác vụ (Option 3: Command Bar & Filter Chips)
        const catCounts = {
            all: data.workflows.length + data.skills.length,
            content: 0,
            docs: 0,
            legal_finance: 0,
            tech_ops: 0,
            workflows: data.workflows.length,
        };

        data.skills.forEach(s => {
            const c = s.category || 'other';
            if (catCounts[c] !== undefined) {
                catCounts[c]++;
            } else {
                catCounts.tech_ops++;
            }
        });

        // 2. Render Compact Task Cards
        let allTaskCardsHtml = '';
        let globalIndex = 0;

        const allItems = [
            ...data.workflows.map(w => ({ ...w, isWorkflow: true })),
            ...data.skills.map(s => ({ ...s, isWorkflow: false }))
        ];

        if (allItems.length === 0) {
            allTaskCardsHtml = `<div class="empty-state"><div class="empty-icon">📭</div>Chưa có tác vụ hoặc kỹ năng nào</div>`;
        } else {
            allItems.forEach((item) => {
                const config = getIconConfig(item.name, globalIndex);
                let rawTitle = config.label || item.displayName || item.name;
                rawTitle = rawTitle.replace(/[\r\n\\]+/g, ' ').replace(/\s+/g, ' ').trim();
                const displayTitle = escapeHtml(rawTitle);

                // Tạo search terms (cả tiếng Việt có dấu và không dấu)
                const rawSearch = `${item.name} ${rawTitle} ${item.description || ''} ${item.categoryName || ''} ${item.trigger || ''}`;
                const unaccentSearch = rawSearch.toLowerCase()
                    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                    .replace(/đ/g, 'd').replace(/Đ/g, 'd');
                const searchAttr = escapeHtml(`${rawSearch.toLowerCase()} ${unaccentSearch}`);

                const escapedTrigger = escapeHtml(item.trigger);
                const escapedDesc = escapeHtml(item.description);
                const escapedName = escapeHtml(item.name);
                const escapedCategory = escapeHtml(item.category || (item.isWorkflow ? 'workflows' : 'other'));
                const escapedCatName = escapeHtml(item.isWorkflow ? 'Quy trình' : (item.categoryName || 'Kỹ năng'));
                const fileFilterAttr = item.fileFilter ? `data-file-filter="${escapeHtml(item.fileFilter)}"` : '';
                const needsFileAttr = item.needsFile ? `data-needs-file="true"` : `data-needs-file="false"`;
                const actionAttr = item.action ? `data-action="${escapeHtml(item.action)}"` : '';
                const targetFileAttr = item.targetFile ? `data-target-file="${escapeHtml(item.targetFile)}"` : '';

                const fileBadge = item.needsFile
                    ? `<span class="task-file-badge" title="Tác vụ cần tệp đính kèm hoặc tài liệu">📎 Tệp</span>`
                    : '';

                allTaskCardsHtml += `
                    <div class="task-card card ${item.needsFile ? 'card-with-file' : ''}" 
                         title="${escapedDesc}" 
                         data-trigger="${escapedTrigger}" 
                         data-name="${escapedName}" 
                         data-type="${item.type}" 
                         data-category="${escapedCategory}" 
                         data-search="${searchAttr}"
                         ${fileFilterAttr} 
                         ${needsFileAttr}
                         ${actionAttr}
                         ${targetFileAttr}>
                        <div class="task-card-icon ${config.gradient}">
                            ${config.icon}
                        </div>
                        <div class="task-card-body">
                            <div class="task-card-title">${displayTitle}</div>
                            <div class="task-card-sub">
                                <span class="task-cat-badge">${escapedCatName}</span>
                                ${fileBadge}
                            </div>
                        </div>
                        <div class="task-card-action" title="Nhấn để kích hoạt">
                            <span class="task-play-btn">▶</span>
                        </div>
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
                                        <button class="src-btn src-btn-skill" title="Áp dụng Skill bất kỳ cho tài liệu này" data-src-title="${escapedSrcTitle}" data-nb-title="${escapedNbTitle}" data-nb-id="${nb.id}" ${localFileAttr}>⚡</button>
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

    <!-- Tab 1: Skills & Workflows (Command Bar & Filter Chips - Option 3) -->
    <div class="tab-content active" id="tabSkills">
        ${interactiveSessionsHtml}

        <!-- Command Bar Search -->
        <div class="task-search-row">
            <div class="task-search-wrapper">
                <span class="task-search-icon">🔍</span>
                <input type="text" id="taskSearchInput" class="task-search-input" placeholder="Tìm tác vụ, kỹ năng (ví dụ: thuế, landing, dịch)..." autocomplete="off" spellcheck="false">
                <button id="taskClearBtn" class="task-search-clear" style="display:none;" title="Xóa tìm kiếm">✕</button>
            </div>
        </div>

        <!-- Filter Chips Row -->
        <div class="task-pills-row" id="taskPillsRow">
            <button class="task-pill active" data-cat="all">Tất cả <span class="pill-badge">${catCounts.all}</span></button>
            <button class="task-pill" data-cat="content">✍️ Nội dung <span class="pill-badge">${catCounts.content}</span></button>
            <button class="task-pill" data-cat="docs">🌐 Tài liệu <span class="pill-badge">${catCounts.docs}</span></button>
            <button class="task-pill" data-cat="legal_finance">⚖️ Pháp lý & Thuế <span class="pill-badge">${catCounts.legal_finance}</span></button>
            <button class="task-pill" data-cat="tech_ops">🛡️ Kỹ thuật <span class="pill-badge">${catCounts.tech_ops}</span></button>
            <button class="task-pill" data-cat="workflows">⚙️ Quy trình <span class="pill-badge">${catCounts.workflows}</span></button>
        </div>

        <!-- Status Meta Row -->
        <div class="task-status-row">
            <span id="taskCountText">Hiển thị <strong>${allItems.length}</strong> tác vụ</span>
        </div>

        <!-- Compact Task Grid -->
        <div class="task-grid-compact" id="taskGridContainer">
            ${allTaskCardsHtml}
        </div>

        <!-- Empty Search State -->
        <div id="taskEmptySearch" class="task-empty-state" style="display:none;">
            <div class="empty-icon">🔍</div>
            <div class="empty-title">Không tìm thấy tác vụ phù hợp</div>
            <div class="empty-desc">Thử tìm từ khóa khác hoặc bấm danh mục "Tất cả"</div>
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

        // 1b. Mở phiên tương tác (ISP v1.0)
        document.querySelectorAll('.interactive-session-card').forEach(card => {
            card.addEventListener('click', () => {
                const projectPath = card.getAttribute('data-project-path');
                const skillName = card.getAttribute('data-skill-name');
                vscode.postMessage({
                    command: 'openInteractiveSession',
                    projectPath: projectPath,
                    skillName: skillName
                });
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

        // 3b. Lọc & Tìm kiếm thời gian thực cho Tác vụ (Option 3: Command Bar & Filter Chips)
        let currentTaskCat = 'all';
        const taskSearchInput = document.getElementById('taskSearchInput');
        const taskClearBtn = document.getElementById('taskClearBtn');
        const taskCards = document.querySelectorAll('.task-card');
        const taskCountText = document.getElementById('taskCountText');
        const taskEmptySearch = document.getElementById('taskEmptySearch');

        function applyTaskFilters() {
            const query = (taskSearchInput?.value || '').trim().toLowerCase();
            const unaccentQuery = query
                .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
                .replace(/đ/g, 'd').replace(/Đ/g, 'd');

            if (taskClearBtn) {
                taskClearBtn.style.display = query ? 'block' : 'none';
            }

            let visibleCount = 0;
            taskCards.forEach(card => {
                const cardCat = card.getAttribute('data-category') || '';
                const searchTerms = (card.getAttribute('data-search') || '').toLowerCase();

                const matchCat = (currentTaskCat === 'all' || cardCat === currentTaskCat);
                const matchQuery = !query || searchTerms.includes(query) || searchTerms.includes(unaccentQuery);

                if (matchCat && matchQuery) {
                    card.style.display = 'flex';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            if (taskCountText) {
                taskCountText.innerHTML = 'Hiển thị <strong>' + visibleCount + '</strong>/' + taskCards.length + ' tác vụ';
            }
            if (taskEmptySearch) {
                taskEmptySearch.style.display = (visibleCount === 0) ? 'block' : 'none';
            }
        }

        document.querySelectorAll('.task-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                document.querySelectorAll('.task-pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                currentTaskCat = pill.getAttribute('data-cat') || 'all';
                applyTaskFilters();
            });
        });

        taskSearchInput?.addEventListener('input', applyTaskFilters);

        taskClearBtn?.addEventListener('click', () => {
            if (taskSearchInput) {
                taskSearchInput.value = '';
                taskSearchInput.focus();
                applyTaskFilters();
            }
        });

        // 4. Chạy Skill / Workflow Card
        document.querySelectorAll('.card[data-trigger]').forEach(card => {
            card.addEventListener('click', () => {
                const trigger = card.getAttribute('data-trigger');
                const itemName = card.getAttribute('data-name') || '';
                const itemType = card.getAttribute('data-type') || 'skill';
                const action = card.getAttribute('data-action') || '';
                const targetFile = card.getAttribute('data-target-file') || '';
                const fileFilter = card.getAttribute('data-file-filter') || '';
                const needsFile = card.getAttribute('data-needs-file') === 'true';
                if (trigger) {
                    vscode.postMessage({
                        command: 'runItem',
                        trigger: trigger,
                        itemName: itemName,
                        itemType: itemType,
                        action: action,
                        targetFile: targetFile,
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

        // 10. Áp dụng Skill lên tài liệu (icon ⚡)
        document.querySelectorAll('.src-btn-skill').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const docTitle = btn.getAttribute('data-src-title');
                const nbTitle = btn.getAttribute('data-nb-title');
                const nbId = btn.getAttribute('data-nb-id');
                const localFile = btn.getAttribute('data-local-file');
                vscode.postMessage({
                    command: 'applySkillToDoc',
                    docTitle: docTitle,
                    notebookTitle: nbTitle,
                    notebookId: nbId,
                    localFilePath: localFile || '',
                });
            });
        });

        // 11. Dịch tài liệu (icon 🌐)
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

        // 12. Hỏi AI về tài liệu (icon 💬)
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

        // 13. Bộ lọc Category Pills
        let currentCatFilter = 'all';
        document.querySelectorAll('.filter-pill').forEach(pill => {
            pill.addEventListener('click', () => {
                document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                currentCatFilter = pill.getAttribute('data-cat') || 'all';
                applyFilters();
            });
        });

        // 14. Real-time Search Input
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

module.exports = { WorkforcePanelProvider };

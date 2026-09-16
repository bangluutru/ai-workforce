/**
 * pickers.js — Bộ chọn tệp, nguồn tài liệu, ngôn ngữ & gửi lệnh Chat
 *
 * Module này chứa toàn bộ logic tương tác với người dùng qua QuickPick/Dialog:
 * - Chọn tệp từ máy tính (Local File Picker)
 * - Chọn nguồn tài liệu đa kênh (Local File vs. Gemini Notebook)
 * - Duyệt và chọn tài liệu trong Notebook
 * - Chọn ngôn ngữ đích cho dịch thuật
 * - Gửi lệnh vào Antigravity Chat (auto-send pipeline)
 */

const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ────────────────────────────────────────────────
// File Picker
// ────────────────────────────────────────────────
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
    const allowMultiple = (skillName === 'ejv-translate' || skillName === 'pdf-translate' || skillName === 'dich-giu-dinh-dang');

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

// ────────────────────────────────────────────────
// Multi-Source Picker for Skills (Local File vs. Gemini Notebook)
// ────────────────────────────────────────────────
async function selectDocumentSourceForSkill(skillName, fileFilterType, catalog, workspaceRoot) {
    const sourceChoice = await vscode.window.showQuickPick([
        {
            label: '📁 Chọn tệp từ máy tính (Local Disk)',
            description: 'Duyệt và chọn tệp PDF, DOCX, Office... từ ổ đĩa máy tính',
            id: 'local_file'
        },
        {
            label: '📚 Chọn tài liệu từ Gemini Notebook (Mục lục tri thức)',
            description: 'Duyệt hoặc tìm kiếm tài liệu từ các Notebook đã kết nối / đồng bộ',
            id: 'notebook_doc'
        },
        {
            label: '⚡ Thực hiện trực tiếp (Không kèm tệp)',
            description: 'Gửi yêu cầu vào Chat để trao đổi trực tiếp với AI',
            id: 'direct'
        }
    ], {
        placeHolder: `Chọn nguồn tài liệu cho skill "${skillName}"...`,
        title: `AI Workforce: Chọn nguồn tài liệu (${skillName})`
    });

    if (!sourceChoice) return null;

    if (sourceChoice.id === 'local_file') {
        const filePaths = await showFilePickerForSkill(skillName, fileFilterType);
        if (filePaths && filePaths.length > 0) {
            return {
                type: 'local_files',
                filePaths: filePaths
            };
        }
        return null;
    }

    if (sourceChoice.id === 'direct') {
        return {
            type: 'direct'
        };
    }

    if (sourceChoice.id === 'notebook_doc') {
        const selectedDoc = await selectNotebookDocument(catalog, workspaceRoot, skillName);
        if (selectedDoc) {
            return {
                type: 'notebook_doc',
                ...selectedDoc
            };
        }
        return null;
    }

    return null;
}

// ────────────────────────────────────────────────
// Notebook Document Picker
// ────────────────────────────────────────────────
async function selectNotebookDocument(catalog, workspaceRoot, skillName) {
    if (!catalog || !catalog.categories) {
        const action = await vscode.window.showWarningMessage(
            'Chưa có dữ liệu mục lục Gemini Notebook. Bạn có muốn quét mục lục ngay không?',
            '⚡ Quét mục lục',
            'Đóng'
        );
        if (action === '⚡ Quét mục lục' && workspaceRoot) {
            const scanScript = path.join(workspaceRoot, 'scripts', 'scan_catalog.py');
            vscode.window.showInformationMessage('⚡ Đang quét danh mục Gemini Notebook...');
            try {
                execSync(`python3 "${scanScript}"`, { cwd: workspaceRoot });
                vscode.window.showInformationMessage('✅ Đã cập nhật Bản đồ Tri thức! Vui lòng chọn lại tài liệu.');
            } catch (err) {
                vscode.window.showErrorMessage(`⚠️ Lỗi quét mục lục: ${err.message}`);
            }
        }
        return null;
    }

    // Gom tất cả notebooks và tài liệu
    const allNotebooks = [];
    const allDocs = [];

    for (const [catId, group] of Object.entries(catalog.categories)) {
        if (!group.notebooks) continue;
        for (const nb of group.notebooks) {
            allNotebooks.push(nb);
            if (nb.sources) {
                nb.sources.forEach((src, srcIdx) => {
                    const isSynced = nb.sync_info && nb.sync_info.is_synced;
                    const localBasePath = (isSynced && nb.sync_info.local_path) ? nb.sync_info.local_path : '';
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
                    allDocs.push({
                        docTitle: src.title,
                        docType: src.type || 'document',
                        notebookTitle: nb.title,
                        notebookId: nb.id,
                        isSynced: isSynced,
                        localFilePath: localFilePath,
                    });
                });
            }
        }
    }

    if (allNotebooks.length === 0) {
        vscode.window.showWarningMessage('Không có Notebook nào trong mục lục.');
        return null;
    }

    // Step 1: Chọn Notebook hoặc Tìm kiếm nhanh tất cả tài liệu
    const nbItems = [
        {
            label: `🔍 [Tìm kiếm nhanh] Toàn bộ ${allDocs.length} tài liệu trong ${allNotebooks.length} Notebooks...`,
            description: 'Tìm kiếm trực tiếp theo tên tài liệu bất kỳ',
            isAllSearch: true
        },
        ...allNotebooks.map(nb => {
            const isSynced = nb.sync_info && nb.sync_info.is_synced;
            const syncIcon = isSynced ? '✅' : '☁️';
            return {
                label: `📓 ${nb.title}`,
                description: `${nb.category_icon || '📁'} ${nb.category_name || ''}`,
                detail: `${nb.source_count} tài liệu • ${syncIcon} ${isSynced ? 'Đã sync' : 'Trên mây'}`,
                notebook: nb
            };
        })
    ];

    const chosenNb = await vscode.window.showQuickPick(nbItems, {
        placeHolder: `Chọn Notebook hoặc tìm nhanh tài liệu cho skill ${skillName}...`,
        title: `AI Workforce: Chọn Gemini Notebook (${skillName})`,
        matchOnDescription: true,
        matchOnDetail: true
    });

    if (!chosenNb) return null;

    // Nếu chọn tìm kiếm nhanh tất cả tài liệu
    if (chosenNb.isAllSearch) {
        const docItems = allDocs.map(doc => {
            const icon = (doc.docType && doc.docType.toLowerCase().includes('pdf')) ? '📕' : '📄';
            const syncIcon = doc.isSynced ? '✅' : '☁️';
            return {
                label: `${icon} ${doc.docTitle}`,
                description: `📓 ${doc.notebookTitle}`,
                detail: `${syncIcon} ${doc.isSynced ? 'Đã sync về local' : 'Lưu trữ trên Gemini Notebook'}`,
                docData: doc
            };
        });

        const chosenDoc = await vscode.window.showQuickPick(docItems, {
            placeHolder: `Gõ từ khóa để tìm trong ${allDocs.length} tài liệu...`,
            title: `AI Workforce: Chọn tài liệu (${skillName})`,
            matchOnDescription: true,
            matchOnDetail: true
        });

        if (!chosenDoc) return null;
        return chosenDoc.docData;
    }

    // Nếu chọn một notebook cụ thể
    const targetNb = chosenNb.notebook;
    if (!targetNb.sources || targetNb.sources.length === 0) {
        vscode.window.showWarningMessage(`Notebook "${targetNb.title}" chưa có tài liệu nào.`);
        return null;
    }

    const isSynced = targetNb.sync_info && targetNb.sync_info.is_synced;
    const localBasePath = (isSynced && targetNb.sync_info.local_path) ? targetNb.sync_info.local_path : '';

    const nbDocItems = targetNb.sources.map((src, srcIdx) => {
        const icon = (src.type && src.type.toLowerCase().includes('pdf')) ? '📕' : '📄';
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
        return {
            label: `${icon} ${src.title}`,
            description: src.type || 'Tài liệu',
            detail: isSynced ? '✅ Đã sync về local' : '☁️ Lưu trữ trên Gemini Notebook',
            docData: {
                docTitle: src.title,
                docType: src.type || 'document',
                notebookTitle: targetNb.title,
                notebookId: targetNb.id,
                isSynced: isSynced,
                localFilePath: localFilePath,
            }
        };
    });

    const chosenDoc = await vscode.window.showQuickPick(nbDocItems, {
        placeHolder: `Chọn tài liệu trong notebook "${targetNb.title}"...`,
        title: `AI Workforce: Chọn tài liệu trong "${targetNb.title}"`,
        matchOnDescription: true,
        matchOnDetail: true
    });

    if (!chosenDoc) return null;
    return chosenDoc.docData;
}

// ────────────────────────────────────────────────
// Target Language Picker
// ────────────────────────────────────────────────
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

// ────────────────────────────────────────────────
// Gửi lệnh vào Chat của Antigravity (Tự động 100%)
// ────────────────────────────────────────────────
async function sendToAntigravityChat(promptText) {
    if (!promptText) return;

    // 1. Luôn lưu vào Clipboard trước để đảm bảo an toàn dữ liệu
    try {
        await vscode.env.clipboard.writeText(promptText);
    } catch (_) {}

    // 2. Thử gửi trực tiếp qua command native của Antigravity IDE
    try {
        await vscode.commands.executeCommand('antigravity.sendPromptToAgentPanel', promptText);
        vscode.window.showInformationMessage('🚀 Đã gửi yêu cầu vào Antigravity Chat!');
        return;
    } catch (_) {}

    try {
        await vscode.commands.executeCommand('antigravity.sendPromptToAgentPanel', { prompt: promptText });
        vscode.window.showInformationMessage('🚀 Đã gửi yêu cầu vào Antigravity Chat!');
        return;
    } catch (_) {}

    // 3. Thử mở và điền query vào VS Code / Antigravity standard chat
    const chatQueryCommands = [
        { cmd: 'workbench.action.chat.open', args: { query: promptText, isPartialQuery: true } },
        { cmd: 'workbench.action.chat.open', args: { query: promptText } },
        { cmd: 'workbench.action.chat.openInSidebar', args: { query: promptText } },
        { cmd: 'workbench.action.chat.newChat', args: { query: promptText } },
        { cmd: 'workbench.action.quickchat.open', args: { query: promptText } },
        { cmd: 'interactiveEditor.start', args: { initialQuery: promptText } },
    ];

    for (const { cmd, args } of chatQueryCommands) {
        try {
            await vscode.commands.executeCommand(cmd, args);
            vscode.window.showInformationMessage('✅ Đã điền yêu cầu vào Chat! Nhấn Enter để gửi.');
            return;
        } catch (_) {}
    }

    // 4. Focus vào chat panel bằng các lệnh focus chuẩn
    const chatFocusCommands = [
        'workbench.action.smartFocusConversation',
        'antigravity.openChatView',
        'antigravity.openAgent',
        'antigravity.focusChat',
        'antigravity.toggleChatFocus',
        'workbench.action.chat.open',
        'workbench.action.chat.focus',
        'workbench.action.chat.openInSidebar',
        'workbench.action.chat.newChat',
        'workbench.panel.chat.view.copilot.focus',
        'workbench.panel.chatSidebar',
        'aichat.newchataction',
        'aichat.focus',
        'gemini.chat.focus',
        'gemini.chat.new',
    ];

    let opened = false;
    for (const cmd of chatFocusCommands) {
        try {
            await vscode.commands.executeCommand(cmd);
            opened = true;
            break;
        } catch (_) {}
    }

    if (opened) {
        // Chờ panel focus và render xong rồi paste / type tự động
        await new Promise(resolve => setTimeout(resolve, 350));

        // Thử type trực tiếp vào input đang focus
        try {
            await vscode.commands.executeCommand('type', { text: promptText });
            vscode.window.showInformationMessage('✅ Đã điền yêu cầu vào Chat! Nhấn Enter để gửi.');
            return;
        } catch (_) {}

        // Thử paste clipboard
        try {
            await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
            vscode.window.showInformationMessage('✅ Đã dán yêu cầu vào Chat! Nhấn Enter để thực hiện.');
            return;
        } catch (_) {}

        vscode.window.showInformationMessage('📋 Đã mở Chat! Nhấn Cmd+V (Mac) hoặc Ctrl+V (Win) rồi nhấn Enter.');
    } else {
        vscode.window.showInformationMessage(
            '📋 Đã sao chép yêu cầu vào clipboard! Hãy mở Chat và nhấn Cmd+V (Ctrl+V) để dán.',
            'Mở Chat'
        ).then(selection => {
            if (selection === 'Mở Chat') {
                vscode.commands.executeCommand('workbench.action.smartFocusConversation').catch(() => {
                    vscode.commands.executeCommand('workbench.action.chat.open').catch(() => {});
                });
            }
        });
    }
}

module.exports = {
    FILE_FILTER_MAP,
    showFilePickerForSkill,
    selectDocumentSourceForSkill,
    selectNotebookDocument,
    TARGET_LANGUAGES,
    promptTargetLanguage,
    sendToAntigravityChat,
};

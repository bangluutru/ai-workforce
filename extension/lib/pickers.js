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
// Định dạng mà scripts/doc_ingest.py đọc được (bộ chuyển đổi dùng chung).
const IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'tif', 'tiff', 'heic'];
const DOC_INGEST_EXTS = [
    'pdf', 'docx', 'doc', 'xlsx', 'xls', 'xlsm', 'csv', 'pptx', 'ppt',
    'epub', 'odt', 'ods', 'odp', 'rtf', 'html', 'htm', 'md', 'txt',
    ...IMAGE_EXTS,
];
const VIDEO_EXTS = ['mp4', 'mov', 'mkv', 'webm', 'm4v', 'avi'];
const AUDIO_EXTS = ['mp3', 'wav', 'm4a', 'aac', 'flac', 'ogg', 'opus'];
const SUBTITLE_EXTS = ['srt', 'ass', 'vtt'];
const ALL_FILES = ['*'];

// Lưu ý: hộp thoại macOS mặc định hiển thị bộ lọc ĐẦU TIÊN → đặt bộ lọc đúng nhất lên đầu.
const FILE_FILTER_MAP = {
    // PDF nguyên bản — cho các skill dịch giữ/tái dựng bố cục
    pdf: {
        'Tệp PDF (*.pdf)': ['pdf'],
        'Tất cả tệp': ALL_FILES,
    },
    // PDF scan + ảnh chụp tài liệu — cho boc-tach-pdf
    scan: {
        'PDF & ảnh scan (*.pdf, *.jpg, *.png, *.tif, *.heic)': ['pdf', ...IMAGE_EXTS],
        'Tệp PDF (*.pdf)': ['pdf'],
        'Ảnh (*.jpg, *.png, *.tif, *.heic)': IMAGE_EXTS,
        'Tất cả tệp': ALL_FILES,
    },
    // Mọi tài liệu doc_ingest đọc được
    doc: {
        'Tài liệu (PDF, Word, Excel, PowerPoint, EPUB, ODF, RTF, HTML, MD, TXT, ảnh)': DOC_INGEST_EXTS,
        'Tệp PDF (*.pdf)': ['pdf'],
        'Word / ODT / RTF (*.docx, *.doc, *.odt, *.rtf)': ['docx', 'doc', 'odt', 'rtf'],
        'Bảng tính (*.xlsx, *.xls, *.xlsm, *.ods, *.csv)': ['xlsx', 'xls', 'xlsm', 'ods', 'csv'],
        'Trình chiếu (*.pptx, *.ppt, *.odp)': ['pptx', 'ppt', 'odp'],
        'Sách điện tử (*.epub)': ['epub'],
        'Web / Markdown / Văn bản (*.html, *.md, *.txt)': ['html', 'htm', 'md', 'txt'],
        'Ảnh (*.jpg, *.png, *.tif, *.heic)': IMAGE_EXTS,
        'Tất cả tệp': ALL_FILES,
    },
    // Văn phòng — cho xu-ly-van-phong
    office: {
        'Tệp Văn phòng & PDF (*.docx, *.xlsx, *.pptx, *.odt, *.pdf, *.rtf, *.md, ...)':
            ['docx', 'xlsx', 'xlsm', 'pptx', 'doc', 'xls', 'ppt', 'odt', 'ods', 'odp', 'csv', 'pdf', 'rtf', 'md', 'txt'],
        'Word / ODT / RTF (*.docx, *.doc, *.odt, *.rtf)': ['docx', 'doc', 'odt', 'rtf'],
        'Bảng tính (*.xlsx, *.xls, *.xlsm, *.ods, *.csv)': ['xlsx', 'xls', 'xlsm', 'ods', 'csv'],
        'Trình chiếu (*.pptx, *.ppt, *.odp)': ['pptx', 'ppt', 'odp'],
        'Tệp PDF (*.pdf)': ['pdf'],
        'Tất cả tệp': ALL_FILES,
    },
    // Video/âm thanh + phụ đề — cho phu-de, long-tieng
    media: {
        'Video, âm thanh & phụ đề (*.mp4, *.mov, *.mkv, *.webm, *.mp3, *.wav, *.srt, ...)':
            [...VIDEO_EXTS, ...AUDIO_EXTS, ...SUBTITLE_EXTS],
        'Video (*.mp4, *.mov, *.mkv, *.webm, *.m4v, *.avi)': VIDEO_EXTS,
        'Âm thanh (*.mp3, *.wav, *.m4a, *.aac, *.flac, *.ogg, *.opus)': AUDIO_EXTS,
        'Phụ đề (*.srt, *.ass, *.vtt)': SUBTITLE_EXTS,
        'Dự án phụ đề phu-de (project.json)': ['json'],
        'Tất cả tệp': ALL_FILES,
    },
};

// Skill cho phép chọn nhiều tệp nguồn cùng lúc
const MULTI_SELECT_SKILLS = new Set([
    'doc-sau',
    'ejv-translate',
    'dich-thuat',
    'boc-tach-pdf',
    'viet-bai',
    'tu-van-phap-luat',
    'tu-van-phap-luat-nhat-ban',
    'long-tieng', // video + phụ đề/kịch bản
]);

// Skill dịch thuật → hỏi ngôn ngữ đích
const TRANSLATE_SKILLS = new Set([
    'ejv-translate',
    'dich-thuat',
]);

// Skill nhận trực tiếp PDF/media gốc → KHÔNG chạy doc_ingest
const NATIVE_INPUT_SKILLS = new Set([
    'dich-thuat',
    'boc-tach-pdf',
    'phu-de',
    'long-tieng',
]);

// Định dạng văn bản thuần — agent đọc thẳng, không cần chuyển đổi
const TEXT_EXTS = new Set(['md', 'markdown', 'txt']);

// Định dạng skill tự đọc được bằng script riêng (bỏ qua doc_ingest)
const SKILL_NATIVE_EXTS = {
    'ejv-translate': new Set(['pdf', 'docx', 'epub']),
};

function isMultiSelectSkill(skillName) {
    return MULTI_SELECT_SKILLS.has(skillName);
}

function isTranslateSkill(skillName) {
    return TRANSLATE_SKILLS.has(skillName);
}

function getFileFilters(fileFilterType) {
    return FILE_FILTER_MAP[fileFilterType] || { 'Tất cả tệp': ALL_FILES };
}

async function showFilePickerForSkill(skillName, fileFilterType) {
    const filters = getFileFilters(fileFilterType);
    const allowMultiple = isMultiSelectSkill(skillName);

    const result = await vscode.window.showOpenDialog({
        canSelectFiles: true,
        canSelectFolders: false,
        canSelectMany: allowMultiple,
        openLabel: `Chọn tệp cho ${skillName}`,
        title: `AI Workforce: Chọn tệp xử lý (${skillName})${allowMultiple ? ' — có thể chọn nhiều tệp' : ''}`,
        filters: filters,
    });

    return result;
}

// ────────────────────────────────────────────────
// Prompt khi người dùng chọn tệp từ máy tính
// ────────────────────────────────────────────────
function slugifyFileName(filePath) {
    const base = path.basename(filePath, path.extname(filePath));
    const slug = base.toLowerCase()
        .normalize('NFD').replace(/[̀-ͯ]/g, '')
        .replace(/đ/g, 'd')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .substring(0, 60);
    return slug || 'tai-lieu';
}

// Trả về danh sách tệp cần chuyển đổi bằng doc_ingest trước khi skill đọc
function filesNeedingIngest(skillName, filePaths) {
    if (NATIVE_INPUT_SKILLS.has(skillName)) return [];
    const native = SKILL_NATIVE_EXTS[skillName] || new Set();
    return filePaths.filter(fp => {
        const ext = path.extname(fp).replace(/^\./, '').toLowerCase();
        return !TEXT_EXTS.has(ext) && !native.has(ext);
    });
}

function buildIngestInstruction(skillName, filePaths) {
    const toIngest = filesNeedingIngest(skillName, filePaths);
    if (toIngest.length === 0) return '';
    const slug = slugifyFileName(toIngest[0]);
    const args = toIngest.map(fp => `"${fp}"`).join(' ');
    return [
        'Bước 0 — Chuyển đổi đầu vào (bắt buộc trước khi đọc nội dung):',
        `\`.venv/bin/python scripts/doc_ingest.py ${args} --out "<output_dir>/_ingest/${slug}"\``,
        `(chạy từ thư mục gốc workspace; <output_dir> là thư mục đầu ra của skill, mặc định ~/Downloads/AIWF_Output/; PDF scan/ảnh: bật cờ OCR của script, xem --help).`,
        'Đọc nội dung từ kết quả trong thư mục _ingest đó; giữ tệp gốc cho các bước cần thao tác trên tệp gốc.',
    ].join('\n');
}

function buildLocalFilesPrompt(skillName, filePaths, detailPrompt) {
    const pathList = filePaths.map(fp => `"${fp}"`).join('\n');
    const ingest = buildIngestInstruction(skillName, filePaths);
    return `Hãy thực hiện skill ${skillName} với các file sau:\n${pathList}\n\n`
        + (ingest ? `${ingest}\n\n` : '')
        + `Yêu cầu chi tiết: ${detailPrompt}`;
}

// ────────────────────────────────────────────────
// Multi-Source Picker for Skills (Local File vs. Gemini Notebook)
// ────────────────────────────────────────────────
function buildSourceChoices(skillName, fileFilterType, needsFile) {
    const filters = getFileFilters(fileFilterType);
    const firstFilterLabel = Object.keys(filters)[0];
    const multi = isMultiSelectSkill(skillName);
    const local = {
        label: '$(folder) Chọn tệp từ máy tính (Local Disk)',
        description: `${firstFilterLabel}${multi ? ' — chọn được nhiều tệp' : ''}`,
        id: 'local_file'
    };
    const notebook = {
        label: '$(book) Chọn tài liệu từ Gemini Notebook (Mục lục tri thức)',
        description: 'Duyệt hoặc tìm kiếm tài liệu từ các Notebook đã kết nối / đồng bộ',
        id: 'notebook_doc'
    };
    const direct = {
        label: '$(zap) Thực hiện trực tiếp (Không kèm tệp)',
        description: 'Gửi yêu cầu vào Chat để trao đổi trực tiếp với AI',
        id: 'direct'
    };
    // needs_file: true → tệp lên đầu; false → làm trực tiếp lên đầu (vẫn cho đính kèm tệp)
    return needsFile ? [local, notebook, direct] : [direct, local, notebook];
}

async function selectDocumentSourceForSkill(skillName, fileFilterType, catalog, workspaceRoot, needsFile = true) {
    const sourceChoice = await vscode.window.showQuickPick(
        buildSourceChoices(skillName, fileFilterType, needsFile),
        {
            placeHolder: `Chọn nguồn tài liệu cho skill "${skillName}"...`,
            title: `AI Workforce: Chọn nguồn tài liệu (${skillName})`
        }
    );

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
            'Quét mục lục',
            'Đóng'
        );
        if (action === 'Quét mục lục' && workspaceRoot) {
            const scanScript = path.join(workspaceRoot, 'scripts', 'scan_catalog.py');
            vscode.window.showInformationMessage('Đang quét danh mục Gemini Notebook...');
            try {
                execSync(`python3 "${scanScript}"`, { cwd: workspaceRoot });
                vscode.window.showInformationMessage('Đã cập nhật Bản đồ Tri thức! Vui lòng chọn lại tài liệu.');
            } catch (err) {
                vscode.window.showErrorMessage(`Lỗi quét mục lục: ${err.message}`);
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
            label: `$(search) [Tìm kiếm nhanh] Toàn bộ ${allDocs.length} tài liệu trong ${allNotebooks.length} Notebooks...`,
            description: 'Tìm kiếm trực tiếp theo tên tài liệu bất kỳ',
            isAllSearch: true
        },
        ...allNotebooks.map(nb => {
            const isSynced = nb.sync_info && nb.sync_info.is_synced;
            const syncIcon = isSynced ? '$(check)' : '$(cloud)';
            return {
                label: `$(book) ${nb.title}`,
                description: `${nb.category_name || ''}`,
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
            const icon = (doc.docType && doc.docType.toLowerCase().includes('pdf')) ? '$(file-pdf)' : '$(file-text)';
            const syncIcon = doc.isSynced ? '$(check)' : '$(cloud)';
            return {
                label: `${icon} ${doc.docTitle}`,
                description: `$(book) ${doc.notebookTitle}`,
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
        const icon = (src.type && src.type.toLowerCase().includes('pdf')) ? '$(file-pdf)' : '$(file-text)';
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
            detail: isSynced ? '$(check) Đã sync về local' : '$(cloud) Lưu trữ trên Gemini Notebook',
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
    { label: '$(globe) Tiếng Anh (English)', code: 'EN', description: 'Dịch sang tiếng Anh chuẩn quốc tế' },
    { label: '$(globe) Tiếng Nhật (日本語)', code: 'JP', description: 'Dịch sang tiếng Nhật tự nhiên, chuẩn văn phong' },
    { label: '$(globe) Tiếng Việt (Vietnamese)', code: 'VI', description: 'Dịch sang tiếng Việt mạch lạc, chuyên nghiệp' },
    { label: '$(globe) Tiếng Trung (中文)', code: 'ZH', description: 'Dịch sang tiếng Trung Giản thể' },
    { label: '$(globe) Tiếng Hàn (한국어)', code: 'KO', description: 'Dịch sang tiếng Hàn Quốc' },
    { label: '$(globe) Tiếng Pháp (Français)', code: 'FR', description: 'Dịch sang tiếng Pháp' },
    { label: '$(globe) Tiếng Đức (Deutsch)', code: 'DE', description: 'Dịch sang tiếng Đức' },
];

async function promptTargetLanguage() {
    const pick = await vscode.window.showQuickPick(
        TARGET_LANGUAGES.map(lang => ({
            label: lang.label,
            description: lang.description,
            code: lang.code,
        })),
        {
            placeHolder: 'Chọn ngôn ngữ đích để dịch tài liệu...',
            title: 'AI Workforce: Chọn ngôn ngữ đích',
            matchOnDescription: true,
        }
    );
    return pick || { label: 'Tiếng Anh (English)', code: 'EN' };
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
        vscode.window.showInformationMessage('Đã gửi yêu cầu vào Antigravity Chat!');
        return;
    } catch (_) {}

    try {
        await vscode.commands.executeCommand('antigravity.sendPromptToAgentPanel', { prompt: promptText });
        vscode.window.showInformationMessage('Đã gửi yêu cầu vào Antigravity Chat!');
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
            vscode.window.showInformationMessage('Đã điền yêu cầu vào Chat! Nhấn Enter để gửi.');
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
            vscode.window.showInformationMessage('Đã điền yêu cầu vào Chat! Nhấn Enter để gửi.');
            return;
        } catch (_) {}

        // Thử paste clipboard
        try {
            await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
            vscode.window.showInformationMessage('Đã dán yêu cầu vào Chat! Nhấn Enter để thực hiện.');
            return;
        } catch (_) {}

        vscode.window.showInformationMessage('Đã mở Chat! Nhấn Cmd+V (Mac) hoặc Ctrl+V (Win) rồi nhấn Enter.');
    } else {
        vscode.window.showInformationMessage(
            'Đã sao chép yêu cầu vào clipboard! Hãy mở Chat và nhấn Cmd+V (Ctrl+V) để dán.',
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
    DOC_INGEST_EXTS,
    MULTI_SELECT_SKILLS,
    TRANSLATE_SKILLS,
    NATIVE_INPUT_SKILLS,
    isMultiSelectSkill,
    isTranslateSkill,
    getFileFilters,
    filesNeedingIngest,
    buildIngestInstruction,
    buildLocalFilesPrompt,
    buildSourceChoices,
    showFilePickerForSkill,
    selectDocumentSourceForSkill,
    selectNotebookDocument,
    TARGET_LANGUAGES,
    promptTargetLanguage,
    sendToAntigravityChat,
};

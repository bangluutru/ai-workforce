/**
 * AI Workforce Extension — Entry Point
 *
 * File này chỉ chứa logic khởi tạo và đăng ký extension.
 * Toàn bộ business logic nằm trong các module tại thư mục lib/:
 *
 *   lib/config.js   — Hằng số đường dẫn
 *   lib/utils.js    — Tiện ích dùng chung (parser, finder, escape)
 *   lib/icons.js    — Bản đồ icon/gradient cho skills & workflows
 *   lib/scanner.js  — Quét Skills, Workflows, Knowledge Catalog
 *   lib/pickers.js  — File picker, notebook picker, language picker, sendToChat
 *   lib/panel.js    — WorkforcePanelProvider (WebviewViewProvider)
 *
 * Xem ARCHITECTURE.md để biết quy tắc tổ chức module.
 */

const vscode = require('vscode');
const { WorkforcePanelProvider } = require('./lib/panel');
const { openInteractivePanel, findActiveSessions } = require('./lib/interactive_panel');

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

    // Command: Open Interactive Panel (ISP v1.0)
    const openInteractiveCmd = vscode.commands.registerCommand('ai-workforce.openInteractivePanel', async (projectPath, skillName) => {
        if (!projectPath) {
            const sessions = findActiveSessions();
            if (sessions.length === 0) {
                vscode.window.showInformationMessage('Không có phiên tương tác nào đang mở trong _process/.');
                return;
            }
            const picked = await vscode.window.showQuickPick(
                sessions.map(s => ({
                    label: `🎨 ${s.skillName}: ${s.projectId}`,
                    description: s.status,
                    session: s
                })),
                { placeHolder: 'Chọn phiên tương tác muốn mở phòng dựng...' }
            );
            if (picked) {
                await openInteractivePanel(picked.session.projectPath, picked.session.skillName, context.extensionUri);
            }
            return;
        }
        await openInteractivePanel(projectPath, skillName, context.extensionUri);
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

    // Watcher: Tự động refresh danh sách phiên tương tác khi có project.json mới
    const projectWatcher = vscode.workspace.createFileSystemWatcher('**/_process/**/project.json');
    projectWatcher.onDidCreate((uri) => {
        provider.refresh();
        // Tự động thông báo và mở phòng dựng
        const projPath = uri.fsPath;
        try {
            const data = JSON.parse(require('fs').readFileSync(projPath, 'utf8'));
            if (data && data.status === 'in_review') {
                openInteractivePanel(projPath, data.skill, context.extensionUri);
            }
        } catch (_) {}
    });
    projectWatcher.onDidChange(() => provider.refresh());
    projectWatcher.onDidDelete(() => provider.refresh());

    context.subscriptions.push(registration, refreshCmd, openInteractiveCmd, watcher, catalogWatcher, projectWatcher);
}

function deactivate() {}

module.exports = { activate, deactivate };

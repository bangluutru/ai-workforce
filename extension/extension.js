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

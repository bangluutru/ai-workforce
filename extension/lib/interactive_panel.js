/**
 * interactive_panel.js — Bộ quản lý Webview Editor Tab cho Interactive Skill Pattern (ISP)
 *
 * Nhiệm vụ:
 * - Mở WebviewPanel độc lập (dạng Editor Tab) cạnh khung chat để người dùng preview và tương tác
 * - Kết nối dữ liệu 2 chiều giữa Webview và file project.json (Single Source of Truth)
 * - Tách biệt Local Actions (chỉnh font, màu, kéo timeline, typing thủ công: xử lý tức thì, 0 token)
 *   và Agent Actions (gửi lệnh AI có cấu trúc vào Antigravity Chat để Agent sinh Patch)
 * - Tự động theo dõi file project.json để đồng bộ giao diện thời gian thực
 */

const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const { findWorkspaceRoot, escapeHtml } = require('./utils');
const { sendToAntigravityChat } = require('./pickers');

// Quản lý các panel đang mở để tránh mở trùng lặp
const activePanels = new Map();

/**
 * Tìm tất cả các phiên tương tác đang có trong workspace (_process/ có project.json)
 */
function findActiveSessions(workspaceRoot) {
    const root = workspaceRoot || findWorkspaceRoot();
    if (!root) return [];

    const processDir = path.join(root, '_process');
    if (!fs.existsSync(processDir)) return [];

    const sessions = [];
    try {
        const subdirs = fs.readdirSync(processDir, { withFileTypes: true });
        for (const dirent of subdirs) {
            if (dirent.isDirectory()) {
                const projFile = path.join(processDir, dirent.name, 'project.json');
                if (fs.existsSync(projFile)) {
                    try {
                        const content = fs.readFileSync(projFile, 'utf8');
                        const data = jsonParseSafe(content);
                        if (data && data.project_id) {
                            sessions.push({
                                projectId: data.project_id,
                                skillName: data.skill || dirent.name,
                                status: data.status || 'in_review',
                                projectPath: projFile,
                                updatedAt: data.meta ? data.meta.updated_at : '',
                                sourceFile: data.meta ? data.meta.source_file : '',
                            });
                        }
                    } catch (_) {}
                }
            }
        }
    } catch (_) {}

    return sessions;
}

function jsonParseSafe(text) {
    try {
        return JSON.parse(text);
    } catch (_) {
        return null;
    }
}

/**
 * Mở hoặc lấy tiêu điểm một Webview Panel tương tác
 */
async function openInteractivePanel(projectPath, skillName, extensionUri) {
    const normPath = path.resolve(projectPath);
    if (!fs.existsSync(normPath)) {
        vscode.window.showErrorMessage(`Không tìm thấy file dự án: ${normPath}`);
        return null;
    }

    let projectData;
    try {
        projectData = JSON.parse(fs.readFileSync(normPath, 'utf8'));
    } catch (e) {
        vscode.window.showErrorMessage(`Lỗi đọc file project.json: ${e.message}`);
        return null;
    }

    const projectId = projectData.project_id || path.basename(path.dirname(normPath));
    const skill = skillName || projectData.skill || 'interactive';

    // Nếu panel của dự án này đã mở, focus vào panel đó
    if (activePanels.has(normPath)) {
        const existing = activePanels.get(normPath);
        existing.panel.reveal(vscode.ViewColumn.Beside);
        existing.panel.webview.postMessage({ type: 'init_state', state: projectData });
        return existing.panel;
    }

    const workspaceRoot = findWorkspaceRoot() || path.dirname(path.dirname(normPath));
    const skillDir = path.join(workspaceRoot, '.agents', 'skills', skill);
    const processDir = path.dirname(normPath);

    // Tạo WebviewPanel mới ở cột bên cạnh (Beside) để song song với Chat
    const panel = vscode.window.createWebviewPanel(
        `aiwf.interactive.${projectId}`,
        `[Phòng dựng] ${skill} - ${projectId}`,
        vscode.ViewColumn.Beside,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                vscode.Uri.file(workspaceRoot),
                vscode.Uri.file(skillDir),
                vscode.Uri.file(processDir),
                extensionUri,
            ],
        }
    );

    // Thiết lập HTML cho Webview
    panel.webview.html = getInteractiveWebviewHtml(panel.webview, skill, skillDir, normPath, extensionUri);

    // Watcher: Tự động cập nhật Webview khi project.json thay đổi trên đĩa
    const watcher = vscode.workspace.createFileSystemWatcher(
        new vscode.RelativePattern(path.dirname(normPath), path.basename(normPath))
    );

    let isInternalSaving = false;

    watcher.onDidChange(() => {
        if (isInternalSaving) return; // Bỏ qua cập nhật do chính Webview vừa lưu
        try {
            if (fs.existsSync(normPath)) {
                const updated = JSON.parse(fs.readFileSync(normPath, 'utf8'));
                panel.webview.postMessage({ type: 'state_updated', state: updated });
            }
        } catch (_) {}
    });

    // Lắng nghe các tương tác từ Webview
    panel.webview.onDidReceiveMessage(async (msg) => {
        if (!msg || !msg.type) return;

        switch (msg.type) {
            case 'ready': {
                // UI đã sẵn sàng, gửi state khởi tạo
                panel.webview.postMessage({ type: 'init_state', state: projectData });
                break;
            }

            case 'save_state': {
                // Local Action: Lưu trạng thái trực tiếp xuống đĩa (0 token)
                try {
                    isInternalSaving = true;
                    const newState = msg.state;
                    if (newState && typeof newState === 'object') {
                        if (!newState.meta) newState.meta = {};
                        newState.meta.updated_at = new Date().toISOString();

                        // Nếu yêu cầu tạo snapshot
                        if (msg.createSnapshot) {
                            const snapDir = path.join(processDir, 'snapshots');
                            if (!fs.existsSync(snapDir)) fs.mkdirSync(snapDir, { recursive: true });
                            const history = newState.history || { current_revision: 0, snapshots: [] };
                            const revNum = (history.current_revision || 0) + 1;
                            const snapFile = `rev_${String(revNum).padStart(3, '0')}.json`;
                            history.current_revision = revNum;
                            if (!history.snapshots) history.snapshots = [];
                            history.snapshots.push(snapFile);
                            fs.writeFileSync(path.join(snapDir, snapFile), JSON.stringify(newState, null, 2), 'utf8');
                            newState.history = history;
                        }

                        fs.writeFileSync(normPath, JSON.stringify(newState, null, 2), 'utf8');
                        projectData = newState;
                    }
                } catch (err) {
                    vscode.window.showErrorMessage(`Lỗi lưu trạng thái dự án: ${err.message}`);
                } finally {
                    setTimeout(() => { isInternalSaving = false; }, 200);
                }
                break;
            }

            case 'agent_action': {
                // Agent Action: Gửi intent có cấu trúc vào Chat để Agent xử lý
                const payload = msg.payload || {};
                const instruction = payload.instruction || 'Hiệu chỉnh nội dung';
                const action = payload.action || 'rewrite_text';
                const targetIds = payload.target_ids || [];
                const contextData = payload.context || {};

                // Ghi vết action request vào thư mục process
                const reqFile = path.join(processDir, 'action_request.json');
                try {
                    fs.writeFileSync(reqFile, JSON.stringify({
                        requestId: `req_${Date.now()}`,
                        timestamp: new Date().toISOString(),
                        action: action,
                        instruction: instruction,
                        targetIds: targetIds,
                        context: contextData,
                    }, null, 2), 'utf8');
                } catch (_) {}

                // Định dạng prompt có cấu trúc cho Agent
                const idListStr = targetIds.length > 0 ? targetIds.join(', ') : 'toàn bộ phân đoạn được chọn';
                const prompt = [
                    `[LỆNH HIỆU CHỈNH TƯƠNG TÁC — ${skill.toUpperCase()}]`,
                    `Dự án: "${normPath}"`,
                    `Hành động: ${action}`,
                    `Yêu cầu người dùng: ${instruction}`,
                    `Đối tượng tác động (Target IDs): [${idListStr}]`,
                    ``,
                    `Chỉ dẫn thực thi cho Agent:`,
                    `1. Đọc nội dung hiện tại của các đối tượng trên trong file project.json.`,
                    `2. Áp dụng năng lực ngôn ngữ / thẩm mỹ để tạo giá trị mới phù hợp với yêu cầu.`,
                    `3. Sử dụng công cụ replace_file_content để cập nhật trực tiếp vào file: "${normPath}".`,
                    `4. TUYỆT ĐỐI KHÔNG sửa các ID khác, không làm mất mốc thời gian / layout nếu không được yêu cầu.`,
                ].join('\n');

                panel.webview.postMessage({
                    type: 'action_dispatched',
                    target_ids: targetIds,
                    message: 'Đã chuyển yêu cầu sang Agent...',
                });

                await sendToAntigravityChat(prompt);
                break;
            }

            case 'undo': {
                // Thao tác Undo
                try {
                    const snapDir = path.join(processDir, 'snapshots');
                    const history = projectData.history || {};
                    const rev = history.current_revision || 1;
                    if (rev > 1) {
                        const prevRev = rev - 1;
                        const prevFile = path.join(snapDir, `rev_${String(prevRev).padStart(3, '0')}.json`);
                        if (fs.existsSync(prevFile)) {
                            const restored = JSON.parse(fs.readFileSync(prevFile, 'utf8'));
                            restored.history.current_revision = prevRev;
                            fs.writeFileSync(normPath, JSON.stringify(restored, null, 2), 'utf8');
                            projectData = restored;
                            panel.webview.postMessage({ type: 'state_updated', state: restored });
                            vscode.window.showInformationMessage(`↩️ Đã hoàn tác về bản ghi ${prevRev}`);
                        }
                    } else {
                        vscode.window.showInformationMessage('Đã ở bản ghi đầu tiên, không thể hoàn tác tiếp.');
                    }
                } catch (e) {
                    vscode.window.showErrorMessage(`Lỗi hoàn tác: ${e.message}`);
                }
                break;
            }

            case 'redo': {
                // Thao tác Redo
                try {
                    const snapDir = path.join(processDir, 'snapshots');
                    const history = projectData.history || {};
                    const rev = history.current_revision || 1;
                    const nextRev = rev + 1;
                    const nextFile = path.join(snapDir, `rev_${String(nextRev).padStart(3, '0')}.json`);
                    if (fs.existsSync(nextFile)) {
                        const restored = JSON.parse(fs.readFileSync(nextFile, 'utf8'));
                        restored.history.current_revision = nextRev;
                        fs.writeFileSync(normPath, JSON.stringify(restored, null, 2), 'utf8');
                        projectData = restored;
                        panel.webview.postMessage({ type: 'state_updated', state: restored });
                        vscode.window.showInformationMessage(`↪️ Đã làm lại tới bản ghi ${nextRev}`);
                    } else {
                        vscode.window.showInformationMessage('Không có thao tác kế tiếp để làm lại.');
                    }
                } catch (e) {
                    vscode.window.showErrorMessage(`Lỗi làm lại: ${e.message}`);
                }
                break;
            }

            case 'finalize': {
                // Xác nhận hoàn tất và kích hoạt Render
                try {
                    projectData.status = 'finalized';
                    fs.writeFileSync(normPath, JSON.stringify(projectData, null, 2), 'utf8');

                    const outDir = (projectData.config && projectData.config.output_dir)
                        ? projectData.config.output_dir
                        : '~/Downloads';

                    const prompt = [
                        `[XÁC NHẬN & XUẤT BẢN THÀNH PHẨM — ${skill.toUpperCase()}]`,
                        `Dự án: "${normPath}"`,
                        `Trạng thái: Người dùng đã duyệt và xác nhận 100% nội dung tại phòng dựng.`,
                        `Thư mục xuất bản: "${outDir}"`,
                        ``,
                        `Hãy thực hiện bước cuối cùng:`,
                        `1. Đọc file project.json đã hoàn thiện.`,
                        `2. Chạy công cụ render tương ứng (render_video.py / export PDF / v.v.) để tạo file thành phẩm ra "${outDir}".`,
                        `3. Báo cáo kết quả ngắn gọn và đường dẫn file đã xuất cho người dùng.`,
                    ].join('\n');

                    vscode.window.showInformationMessage(`🚀 Đã chốt bản dựng! Đang chuyển lệnh cho Agent xuất bản ra ${outDir}...`);
                    await sendToAntigravityChat(prompt);
                } catch (e) {
                    vscode.window.showErrorMessage(`Lỗi xuất bản: ${e.message}`);
                }
                break;
            }

            case 'show_message': {
                if (msg.level === 'error') {
                    vscode.window.showErrorMessage(msg.text);
                } else if (msg.level === 'warn') {
                    vscode.window.showWarningMessage(msg.text);
                } else {
                    vscode.window.showInformationMessage(msg.text);
                }
                break;
            }
        }
    });

    panel.onDidDispose(() => {
        watcher.dispose();
        activePanels.delete(normPath);
    });

    activePanels.set(normPath, { panel, watcher });
    return panel;
}

/**
 * Tạo nội dung HTML cho Webview, tích hợp Domain UI từ .agents/skills/<skill>/ui/
 */
function getInteractiveWebviewHtml(webview, skillName, skillDir, projectPath, extensionUri) {
    const uiDir = path.join(skillDir, 'ui');
    const indexHtmlPath = path.join(uiDir, 'index.html');

    // Nếu skill có file index.html trong ui/
    if (fs.existsSync(indexHtmlPath)) {
        let html = fs.readFileSync(indexHtmlPath, 'utf8');

        // Chuyển đổi các đường dẫn tương đối (href="..." và src="...") sang webview.asWebviewUri
        html = html.replace(/(src|href)=["'](?!http|https|data:)([^"']+)["']/g, (match, attr, relPath) => {
            const absoluteAssetPath = path.resolve(uiDir, relPath);
            if (fs.existsSync(absoluteAssetPath)) {
                const uri = webview.asWebviewUri(vscode.Uri.file(absoluteAssetPath));
                return `${attr}="${uri}"`;
            }
            return match;
        });

        // Chèn script cầu nối VS Code Webview Bridge
        const bridgeScript = `
        <script>
            // Tích hợp VS Code API cho Webview
            const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi() : null;
            window.IS_VSCODE_WEBVIEW = true;
            window.__PROJECT_FILE_PATH__ = ${JSON.stringify(projectPath)};

            // Báo hiệu Webview đã nạp xong
            if (vscode) {
                vscode.postMessage({ type: 'ready' });
            }

            // Lắng nghe sự kiện từ Extension Host
            window.addEventListener('message', function(event) {
                const message = event.data;
                if (!message) return;
                
                if (message.type === 'init_state' || message.type === 'state_updated') {
                    if (typeof window.onProjectStateLoaded === 'function') {
                        window.onProjectStateLoaded(message.state);
                    }
                } else if (message.type === 'action_dispatched') {
                    if (typeof window.onAgentActionDispatched === 'function') {
                        window.onAgentActionDispatched(message);
                    }
                }
            });

            // Hàm tiện ích cho UI gọi ra ngoài
            window.dispatchLocalSave = function(state, createSnapshot) {
                if (vscode) {
                    vscode.postMessage({ type: 'save_state', state: state, createSnapshot: !!createSnapshot });
                }
            };

            window.dispatchAgentAction = function(payload) {
                if (vscode) {
                    vscode.postMessage({ type: 'agent_action', payload: payload });
                }
            };

            window.dispatchUndo = function() {
                if (vscode) vscode.postMessage({ type: 'undo' });
            };

            window.dispatchRedo = function() {
                if (vscode) vscode.postMessage({ type: 'redo' });
            };

            window.dispatchFinalize = function() {
                if (vscode) vscode.postMessage({ type: 'finalize' });
            };
        </script>
        `;

        if (html.includes('</body>')) {
            html = html.replace('</body>', `${bridgeScript}</body>`);
        } else {
            html += bridgeScript;
        }

        return html;
    }

    // Giao diện mặc định nếu skill chưa có ui/index.html
    return `<!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <title>Phòng dựng tương tác: ${escapeHtml(skillName)}</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 24px; color: #ccc; background: #1e1e1e; }
            .card { background: #252526; border: 1px solid #3c3c3c; border-radius: 8px; padding: 20px; max-width: 600px; margin: 0 auto; }
            h2 { color: #fff; margin-top: 0; }
            code { background: #111; padding: 2px 6px; border-radius: 4px; color: #4ec9b0; }
            button { background: #0e639c; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
            button:hover { background: #1177bb; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🎨 Phòng Dựng Tương Tác (${escapeHtml(skillName)})</h2>
            <p>Dự án đang mở tại: <code>${escapeHtml(projectPath)}</code></p>
            <p>Skill này chưa có thư mục <code>ui/index.html</code> chuyên dụng. Trạng thái dự án đang được theo dõi tự động.</p>
            <button onclick="vscode.postMessage({ type: 'finalize' })">Xác nhận & Hoàn tất</button>
        </div>
        <script>
            const vscode = acquireVsCodeApi();
            vscode.postMessage({ type: 'ready' });
        </script>
    </body>
    </html>`;
}

module.exports = {
    openInteractivePanel,
    findActiveSessions,
};

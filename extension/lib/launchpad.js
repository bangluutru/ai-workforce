/**
 * launchpad.js — Studio Launchpad Webview Panel (Giải pháp 1)
 *
 * Nhiệm vụ:
 * - Cung cấp giao diện cấu hình trực quan (All-in-One Studio Form) trước khi chạy Skill.
 * - Loại bỏ hoàn toàn emoji, sử dụng 100% Lucide SVG Icons đồng bộ với extension.
 * - Phong cách thiết kế tối giản, nghiêm túc cho công việc (chuẩn Linear / VS Code / Raycast).
 * - Thu thập thông số, đóng gói thành prompt chuẩn và kích hoạt Antigravity Chat.
 */

const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const { findWorkspaceRoot, escapeHtml } = require('./utils');
const { renderSvg } = require('./icons');
const { sendToAntigravityChat } = require('./pickers');

// Danh sách các skill có giao diện Studio Launchpad
const STUDIO_SKILLS = new Set([
    'hand-drawn-animation',
    'sach-noi',
]);

function isStudioSkill(skillName) {
    return STUDIO_SKILLS.has(skillName);
}

// Lưu trữ instance panel để tránh mở lặp
const studioPanels = new Map();

/**
 * Mở Webview Studio Launchpad cho một skill
 */
async function openStudioLaunchpad(skillName, extensionUri, initialFilePath = null) {
    if (studioPanels.has(skillName)) {
        const existing = studioPanels.get(skillName);
        existing.reveal(vscode.ViewColumn.Beside);
        return existing;
    }

    const titleMap = {
        'hand-drawn-animation': 'Studio Tạo Hoạt Hình',
        'sach-noi': 'Studio Sách Nói AI',
    };
    const title = titleMap[skillName] || `[Studio] ${skillName}`;

    const panel = vscode.window.createWebviewPanel(
        `aiwf.studio.${skillName}`,
        title,
        vscode.ViewColumn.Beside,
        {
            enableScripts: true,
            retainContextWhenHidden: true,
            localResourceRoots: [
                extensionUri,
            ],
        }
    );

    studioPanels.set(skillName, panel);

    panel.onDidDispose(() => {
        studioPanels.delete(skillName);
    });

    panel.webview.html = getStudioHtml(skillName, panel.webview, initialFilePath);

    // Lắng nghe tương tác từ Webview
    panel.webview.onDidReceiveMessage(async (msg) => {
        if (!msg || !msg.command) return;

        switch (msg.command) {
            case 'select_file': {
                const filters = skillName === 'hand-drawn-animation'
                    ? { 'Tệp tham chiếu (*.png, *.jpg, *.mp4, *.mov)': ['png', 'jpg', 'jpeg', 'mp4', 'mov'], 'Tất cả tệp': ['*'] }
                    : { 'Tài liệu sách (*.epub, *.docx, *.pdf, *.md)': ['epub', 'docx', 'pdf', 'md', 'txt'], 'Tất cả tệp': ['*'] };

                const chosen = await vscode.window.showOpenDialog({
                    canSelectFiles: true,
                    canSelectFolders: false,
                    canSelectMany: false,
                    openLabel: 'Chọn tệp nạp vào Studio',
                    filters: filters,
                });

                if (chosen && chosen.length > 0) {
                    panel.webview.postMessage({
                        type: 'file_selected',
                        filePath: chosen[0].fsPath,
                        fileName: path.basename(chosen[0].fsPath),
                    });
                }
                break;
            }

            case 'launch': {
                const config = msg.config;
                let prompt = '';

                if (skillName === 'hand-drawn-animation') {
                    const styleMap = {
                        doodle: 'Doodle Pastel (nét phác họa hoạt hình, explainer ngắn)',
                        pencil: 'Pencil Sketch (phác thảo bút chì nghệ thuật, chi tiết mộc mạc)',
                        ink: 'Paper Ink (nét cọ mực thư pháp Á Đông, cổ điển)',
                        riso: 'Riso Pop (in thạch bản 3 bản kẽm retro rực rỡ)',
                        screen: 'Screen Tone (đồ họa màn lưới vi điểm halftone hiện đại)',
                        sand: 'Sand Animation (nghệ thuật tranh cát biến ảo)',
                    };
                    const audioMap = {
                        synth: 'Nhạc nền Canvas Synth sinh tự động (WAV Score)',
                        voiceover: 'Lồng tiếng thuyết minh AI (VieNeu 48kHz)',
                        silent: 'Không âm thanh (Video câm)',
                    };

                    const parts = [
                        `Hãy thực hiện skill hand-drawn-animation với cấu hình sau:`,
                        `- Phong cách nghệ thuật: ${config.style} — ${styleMap[config.style] || config.style}`,
                        `- Tỷ lệ khung hình: ${config.aspectRatio}`,
                        `- Thời lượng mục tiêu: ${config.duration} giây`,
                        `- Âm thanh: ${audioMap[config.audioMode] || config.audioMode}`,
                    ];

                    if (config.referenceFile) {
                        parts.push(`- Tệp tham chiếu: "${config.referenceFile}"`);
                    }
                    if (config.prompt && config.prompt.trim()) {
                        parts.push(`- Ý tưởng kịch bản: "${config.prompt.trim()}"`);
                    }

                    prompt = parts.join('\n');
                } else if (skillName === 'sach-noi') {
                    const levelMap = {
                        1: 'Cấp 1: Đọc nguyên văn (Verbatim — 100% không đổi câu chữ)',
                        2: 'Cấp 2: Làm mượt (Giữ nguyên cấu trúc tác giả, biến bảng biểu/sơ đồ thành lời văn)',
                        3: 'Cấp 3: Sano Storytelling (Mở đầu câu chuyện, thân bài 3 ý lớn, kết thúc 3 ý cần nhớ)',
                        4: 'Cấp 4: Sách nói tóm tắt ngắn (Audiobook Brief 15 - 25 phút)',
                    };

                    const parts = [
                        `Hãy thực hiện skill sach-noi với cấu hình sau:`,
                        `- Chế độ đọc: ${levelMap[config.level] || config.level}`,
                        `- Giọng đọc phát thanh: ${config.voice}`,
                        `- Định dạng xuất: ${config.outputFormats.join(', ')}`,
                    ];

                    if (config.sourceFile) {
                        parts.push(`- Tệp nguồn sách: "${config.sourceFile}"`);
                    }

                    prompt = parts.join('\n');
                }

                // Gửi sang Antigravity Chat
                if (prompt) {
                    await sendToAntigravityChat(prompt);
                    vscode.window.showInformationMessage(`Đã khởi chạy ${title}!`);
                    panel.dispose();
                }
                break;
            }

            case 'cancel': {
                panel.dispose();
                break;
            }
        }
    });

    return panel;
}

/**
 * Sinh HTML cho Studio Launchpad
 */
function getStudioHtml(skillName, webview, initialFilePath) {
    if (skillName === 'hand-drawn-animation') {
        return getHandDrawnAnimationHtml(initialFilePath);
    } else if (skillName === 'sach-noi') {
        return getAudiobookHtml(initialFilePath);
    }
    return '<div>Skill chưa hỗ trợ Studio Launchpad</div>';
}

/**
 * Giao diện Studio Tạo Hoạt Hình
 */
function getHandDrawnAnimationHtml(initialFilePath) {
    const iconClapperboard = renderSvg('clapperboard', 18);
    const iconUpload = renderSvg('upload', 16);
    const iconPlay = renderSvg('play', 14);
    const iconX = renderSvg('x', 14);
    const iconMonitor = renderSvg('monitor', 14);
    const iconSmartphone = renderSvg('smartphone', 14);
    const iconSquare = renderSvg('square', 14);
    const iconClock = renderSvg('clock', 14);
    const iconVolume = renderSvg('volume-2', 14);
    const iconBox = renderSvg('box', 22);
    const iconPen = renderSvg('pen-line', 22);
    const iconFile = renderSvg('file-text', 22);
    const iconLayers = renderSvg('layers', 22);
    const iconScan = renderSvg('scan-text', 22);
    const iconActivity = renderSvg('activity', 22);

    const initFileEscaped = initialFilePath ? escapeHtml(initialFilePath) : '';
    const initFileName = initialFilePath ? escapeHtml(path.basename(initialFilePath)) : '';
    const initFilePathJson = JSON.stringify(initialFilePath || '');

    return `<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Studio Tạo Hoạt Hình</title>
<style>
  :root {
    --bg-main: #18181b;
    --bg-card: #27272a;
    --bg-card-hover: #323238;
    --bg-card-active: #1e293b;
    --border-color: #3f3f46;
    --border-active: #38bdf8;
    --text-primary: #f4f4f5;
    --text-muted: #a1a1aa;
    --text-accent: #38bdf8;
    --btn-primary: #0284c7;
    --btn-primary-hover: #0369a1;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg-main);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    line-height: 1.5;
    padding: 24px;
    max-width: 860px;
    margin: 0 auto;
  }
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 24px;
  }
  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .header-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -0.01em;
  }
  .header-badge {
    font-size: 11px;
    padding: 2px 8px;
    background: #27272a;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-muted);
  }
  .section {
    margin-bottom: 24px;
  }
  .section-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-bottom: 10px;
  }
  .style-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }
  .style-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 14px;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .style-card:hover {
    background: var(--bg-card-hover);
    border-color: #52525b;
  }
  .style-card.active {
    background: var(--bg-card-active);
    border-color: var(--border-active);
  }
  .style-card-icon {
    color: var(--text-accent);
  }
  .style-card-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
  }
  .style-card-desc {
    font-size: 11.5px;
    color: var(--text-muted);
    line-height: 1.35;
  }
  .segmented-group {
    display: flex;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 3px;
    gap: 4px;
  }
  .segmented-btn {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    background: transparent;
    border: none;
    color: var(--text-muted);
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 500;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.12s ease;
  }
  .segmented-btn:hover {
    color: var(--text-primary);
  }
  .segmented-btn.active {
    background: #3f3f46;
    color: var(--text-primary);
    font-weight: 600;
  }
  .file-dropzone {
    background: var(--bg-card);
    border: 1px dashed var(--border-color);
    border-radius: 6px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .file-info {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text-muted);
    font-size: 12.5px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .file-info.has-file {
    color: var(--text-primary);
    font-weight: 500;
  }
  .btn-secondary {
    background: #3f3f46;
    border: 1px solid #52525b;
    color: var(--text-primary);
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 4px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .btn-secondary:hover {
    background: #52525b;
  }
  .radio-group {
    display: flex;
    gap: 18px;
    padding-top: 4px;
  }
  .radio-label {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    font-size: 12.5px;
    color: var(--text-primary);
  }
  .radio-label input[type="radio"] {
    accent-color: var(--border-active);
  }
  .textarea-field {
    width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
    font-family: inherit;
    font-size: 12.5px;
    padding: 10px 12px;
    resize: vertical;
    min-height: 64px;
  }
  .textarea-field:focus {
    outline: none;
    border-color: var(--border-active);
  }
  .footer-bar {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 18px;
    border-top: 1px solid var(--border-color);
    margin-top: 28px;
  }
  .btn-cancel {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 9px 18px;
    font-size: 13px;
    border-radius: 6px;
    cursor: pointer;
  }
  .btn-cancel:hover {
    color: var(--text-primary);
    border-color: #71717a;
  }
  .btn-launch {
    background: var(--btn-primary);
    border: none;
    color: #fff;
    padding: 9px 24px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    transition: background 0.15s ease;
  }
  .btn-launch:hover {
    background: var(--btn-primary-hover);
  }
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    ${iconClapperboard}
    <div class="header-title">Studio Tạo Hoạt Hình</div>
    <div class="header-badge">hand-drawn-animation</div>
  </div>
</div>

<!-- 1. PHONG CÁCH NGHỆ THUẬT -->
<div class="section">
  <div class="section-label">1. Phong Cách Nghệ Thuật (Look & Style)</div>
  <div class="style-grid">
    <div class="style-card" data-style="doodle" onclick="selectStyle(this)">
      <div class="style-card-icon">${iconBox}</div>
      <div class="style-card-title">Doodle Pastel</div>
      <div class="style-card-desc">Nét phác hoạt họa vui tươi, nhẹ nhàng, tối ưu giải thích ngắn gọn</div>
    </div>
    <div class="style-card active" data-style="pencil" onclick="selectStyle(this)">
      <div class="style-card-icon">${iconPen}</div>
      <div class="style-card-title">Pencil Sketch</div>
      <div class="style-card-desc">Phác thảo bút chì mộc mạc, đậm chất sổ tay nghệ thuật (Mặc định)</div>
    </div>
    <div class="style-card" data-style="ink" onclick="selectStyle(this)">
      <div class="style-card-icon">${iconFile}</div>
      <div class="style-card-title">Paper Ink</div>
      <div class="style-card-desc">Nét cọ mực thư pháp Á Đông, trang nhã và sâu lắng</div>
    </div>
    <div class="style-card" data-style="riso" onclick="selectStyle(this)">
      <div class="style-card-icon">${iconLayers}</div>
      <div class="style-card-title">Riso Pop</div>
      <div class="style-card-desc">In thạch bản retro 3 bản kẽm, màu sắc rực rỡ cá tính</div>
    </div>
    <div class="style-card" data-style="screen" onclick="selectStyle(this)">
      <div class="style-card-icon">${iconScan}</div>
      <div class="style-card-title">Screen Tone</div>
      <div class="style-card-desc">Đồ họa màn lưới vi điểm halftone chuẩn in ấn đồ họa</div>
    </div>
    <div class="style-card" data-style="sand" onclick="selectStyle(this)">
      <div class="style-card-icon">${iconActivity}</div>
      <div class="style-card-title">Sand Animation</div>
      <div class="style-card-desc">Nghệ thuật chuyển động hạt cát biến ảo, giàu cảm xúc</div>
    </div>
  </div>
</div>

<!-- 2. TỶ LỆ KHUNG HÌNH -->
<div class="section">
  <div class="section-label">2. Tỷ Lệ Khung Hình (Aspect Ratio)</div>
  <div class="segmented-group" id="ratioGroup">
    <button class="segmented-btn active" data-val="16:9" onclick="selectRatio(this)">
      ${iconMonitor} 16:9 Ngang (YouTube / Desktop)
    </button>
    <button class="segmented-btn" data-val="9:16" onclick="selectRatio(this)">
      ${iconSmartphone} 9:16 Dọc (TikTok / Reels / Shorts)
    </button>
    <button class="segmented-btn" data-val="1:1" onclick="selectRatio(this)">
      ${iconSquare} 1:1 Vuông (Social Feed)
    </button>
  </div>
</div>

<!-- 3. THỜI LƯỢNG KỊCH BẢN -->
<div class="section">
  <div class="section-label">${iconClock} 3. Thời Lượng Mục Tiêu</div>
  <div class="segmented-group" id="durationGroup">
    <button class="segmented-btn" data-val="15" onclick="selectDuration(this)">15 giây (3 shot ngắn gọn)</button>
    <button class="segmented-btn active" data-val="24" onclick="selectDuration(this)">24 giây (Tiêu chuẩn 4-6 shot)</button>
    <button class="segmented-btn" data-val="36" onclick="selectDuration(this)">36 giây (Mở rộng 7-10 shot)</button>
  </div>
</div>

<!-- 4. TỆP THAM CHIẾU -->
<div class="section">
  <div class="section-label">4. Tệp Tham Chiếu (Reference Asset — Tùy chọn)</div>
  <div class="file-dropzone">
    <div class="file-info ${initFileEscaped ? 'has-file' : ''}" id="fileInfoText">
      ${initFileName ? initFileName : 'Chưa chọn tệp tham chiếu (ảnh phác thảo hoặc video rotoscope)'}
    </div>
    <button class="btn-secondary" onclick="browseFile()">
      ${iconUpload} Duyệt tệp...
    </button>
  </div>
</div>

<!-- 5. ÂM THANH -->
<div class="section">
  <div class="section-label">${iconVolume} 5. Hệ Thống Âm Thanh</div>
  <div class="radio-group">
    <label class="radio-label">
      <input type="radio" name="audioMode" value="synth" checked>
      Nhạc nền Canvas Synth (WAV Score)
    </label>
    <label class="radio-label">
      <input type="radio" name="audioMode" value="voiceover">
      Lồng tiếng thuyết minh AI (VieNeu 48kHz)
    </label>
    <label class="radio-label">
      <input type="radio" name="audioMode" value="silent">
      Không âm thanh (Video câm)
    </label>
  </div>
</div>

<!-- 6. MÔ TẢ KỊCH BẢN -->
<div class="section">
  <div class="section-label">6. Kịch Bản / Ý Tưởng Cốt Lõi (Tùy chọn)</div>
  <textarea class="textarea-field" id="promptInput" placeholder="Ví dụ: Một chú mèo nhỏ đuổi theo một đốm sáng trong đêm, vấp ngã rồi phát hiện ra một chú đom đóm ấm áp..."></textarea>
</div>

<!-- ACTION BAR -->
<div class="footer-bar">
  <button class="btn-cancel" onclick="cancel()">Hủy</button>
  <button class="btn-launch" onclick="launchSkill()">
    ${iconPlay} Khởi Chạy Quy Trình Tạo Hoạt Hình
  </button>
</div>

<script>
  const vscode = acquireVsCodeApi();
  let selectedStyle = 'pencil';
  let selectedRatio = '16:9';
  let selectedDuration = 24;
  let selectedFilePath = ${initFilePathJson};

  function selectStyle(el) {
    document.querySelectorAll('.style-card').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    selectedStyle = el.getAttribute('data-style');
  }

  function selectRatio(el) {
    document.querySelectorAll('#ratioGroup .segmented-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    selectedRatio = el.getAttribute('data-val');
  }

  function selectDuration(el) {
    document.querySelectorAll('#durationGroup .segmented-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    selectedDuration = parseInt(el.getAttribute('data-val'), 10);
  }

  function browseFile() {
    vscode.postMessage({ command: 'select_file' });
  }

  function cancel() {
    vscode.postMessage({ command: 'cancel' });
  }

  function launchSkill() {
    const audioMode = document.querySelector('input[name="audioMode"]:checked').value;
    const prompt = document.getElementById('promptInput').value;

    vscode.postMessage({
      command: 'launch',
      config: {
        style: selectedStyle,
        aspectRatio: selectedRatio,
        duration: selectedDuration,
        referenceFile: selectedFilePath,
        audioMode: audioMode,
        prompt: prompt
      }
    });
  }

  window.addEventListener('message', event => {
    const msg = event.data;
    if (msg.type === 'file_selected') {
      selectedFilePath = msg.filePath;
      const el = document.getElementById('fileInfoText');
      el.textContent = msg.fileName;
      el.classList.add('has-file');
    }
  });
</script>

</body>
</html>`;
}

/**
 * Giao diện Studio Sách Nói AI
 */
function getAudiobookHtml(initialFilePath) {
    const iconBook = renderSvg('book-open', 18);
    const iconUpload = renderSvg('upload', 16);
    const iconPlay = renderSvg('play', 14);
    const iconMic = renderSvg('mic', 14);

    const initFileEscaped = initialFilePath ? escapeHtml(initialFilePath) : '';
    const initFileName = initialFilePath ? escapeHtml(path.basename(initialFilePath)) : '';
    const initFilePathJson = JSON.stringify(initialFilePath || '');

    return `<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Studio Sách Nói AI</title>
<style>
  :root {
    --bg-main: #18181b;
    --bg-card: #27272a;
    --bg-card-hover: #323238;
    --bg-card-active: #1e293b;
    --border-color: #3f3f46;
    --border-active: #38bdf8;
    --text-primary: #f4f4f5;
    --text-muted: #a1a1aa;
    --btn-primary: #0284c7;
    --btn-primary-hover: #0369a1;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg-main);
    color: var(--text-primary);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    padding: 24px;
    max-width: 860px;
    margin: 0 auto;
  }
  .header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border-color);
    margin-bottom: 24px;
  }
  .header-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
  .header-badge {
    font-size: 11px;
    padding: 2px 8px;
    background: #27272a;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    color: var(--text-muted);
  }
  .section { margin-bottom: 24px; }
  .section-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-bottom: 10px;
  }
  .level-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .level-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 14px;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .level-card:hover { background: var(--bg-card-hover); border-color: #52525b; }
  .level-card.active { background: var(--bg-card-active); border-color: var(--border-active); }
  .level-card-title { font-size: 13px; font-weight: 600; margin-bottom: 4px; color: var(--text-primary); }
  .level-card-desc { font-size: 11.5px; color: var(--text-muted); line-height: 1.35; }
  .file-dropzone {
    background: var(--bg-card);
    border: 1px dashed var(--border-color);
    border-radius: 6px;
    padding: 14px 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }
  .file-info { font-size: 12.5px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .file-info.has-file { color: var(--text-primary); font-weight: 500; }
  .btn-secondary {
    background: #3f3f46;
    border: 1px solid #52525b;
    color: var(--text-primary);
    padding: 6px 12px;
    font-size: 12px;
    border-radius: 4px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }
  .btn-secondary:hover { background: #52525b; }
  .select-field {
    width: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    color: var(--text-primary);
    padding: 9px 12px;
    font-size: 13px;
  }
  .select-field:focus { outline: none; border-color: var(--border-active); }
  .checkbox-group { display: flex; flex-direction: column; gap: 8px; }
  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12.5px;
    color: var(--text-primary);
    cursor: pointer;
  }
  .checkbox-label input[type="checkbox"] { accent-color: var(--border-active); }
  .footer-bar {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 12px;
    padding-top: 18px;
    border-top: 1px solid var(--border-color);
    margin-top: 28px;
  }
  .btn-cancel {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-muted);
    padding: 9px 18px;
    font-size: 13px;
    border-radius: 6px;
    cursor: pointer;
  }
  .btn-cancel:hover { color: var(--text-primary); border-color: #71717a; }
  .btn-launch {
    background: var(--btn-primary);
    border: none;
    color: #fff;
    padding: 9px 24px;
    font-size: 13px;
    font-weight: 600;
    border-radius: 6px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }
  .btn-launch:hover { background: var(--btn-primary-hover); }
</style>
</head>
<body>

<div class="header">
  ${iconBook}
  <div class="header-title">Studio Sách Nói AI</div>
  <div class="header-badge">sach-noi</div>
</div>

<!-- 1. TỆP NGUỒN SÁCH -->
<div class="section">
  <div class="section-label">1. Tệp Nguồn Sách (EPUB, DOCX, PDF, MD)</div>
  <div class="file-dropzone">
    <div class="file-info ${initFileEscaped ? 'has-file' : ''}" id="fileInfoText">
      ${initFileName ? initFileName : 'Chưa chọn file sách'}
    </div>
    <button class="btn-secondary" onclick="browseFile()">
      ${iconUpload} Duyệt tệp...
    </button>
  </div>
</div>

<!-- 2. CẤP ĐỘ ĐỌC -->
<div class="section">
  <div class="section-label">2. Cấp Độ Đọc & Biên Tập Phát Thanh</div>
  <div class="level-grid">
    <div class="level-card" data-level="1" onclick="selectLevel(this)">
      <div class="level-card-title">Cấp 1: Đọc Nguyên Văn (Verbatim)</div>
      <div class="level-card-desc">Giữ nguyên 100% câu chữ của tác giả, chuẩn hóa phát âm số hiệu và từ viết tắt.</div>
    </div>
    <div class="level-card" data-level="2" onclick="selectLevel(this)">
      <div class="level-card-title">Cấp 2: Làm Mượt (Smoothing)</div>
      <div class="level-card-desc">Giữ trọn vẹn bố cục tác giả; chuyển bảng biểu, sơ đồ và chú thích trang thành lời văn tự nhiên.</div>
    </div>
    <div class="level-card active" data-level="3" onclick="selectLevel(this)">
      <div class="level-card-title">Cấp 3: Sano Storytelling (Mặc định)</div>
      <div class="level-card-desc">Cấu trúc kịch bản phát thanh: Mở đầu câu chuyện, thân bài tối đa 3 ý lớn, kết thúc Ba ý cần nhớ.</div>
    </div>
    <div class="level-card" data-level="4" onclick="selectLevel(this)">
      <div class="level-card-title">Cấp 4: Sách Nói Tóm Tắt (Audiobook Brief)</div>
      <div class="level-card-desc">Tóm tắt điều hành và các case study cốt lõi thành bản ghi ngắn 15 đến 25 phút nghe nhanh.</div>
    </div>
  </div>
</div>

<!-- 3. GIỌNG ĐỌC -->
<div class="section">
  <div class="section-label">${iconMic} 3. Giọng Đọc Phát Thanh (VieNeu-TTS 48kHz Offline)</div>
  <select class="select-field" id="voiceSelect">
    <optgroup label="Miền Nam (Trầm ấm, đĩnh đạc)">
      <option value="Thái Sơn" selected>Thái Sơn (Nam · Nam 48kHz Studio — Mặc định kinh doanh/tư duy)</option>
      <option value="Thùy Dung">Thùy Dung (Nữ · Nam 48kHz Studio — Tin tức, truyền cảm HD)</option>
      <option value="Đức Trí">Đức Trí (Nam · Nam 48kHz — Trầm điện ảnh)</option>
      <option value="Mỹ Duyên">Mỹ Duyên (Nữ · Nam 48kHz — Đọc truyện, ấm áp)</option>
    </optgroup>
    <optgroup label="Miền Bắc (Chuẩn mực, dịu dàng)">
      <option value="Trúc Ly">Trúc Ly (Nữ · Bắc 48kHz — Dịu dàng, tâm lý/văn học)</option>
      <option value="Thiện Minh">Thiện Minh (Nam · Bắc 48kHz — Kể chuyện, podcast)</option>
      <option value="Thiền Tâm Đức">Thiền Tâm Đức (Nam · Bắc 48kHz — Chiêm nghiệm, sách triết lý/thiền)</option>
      <option value="Mai Anh">Mai Anh (Nữ · Bắc 48kHz — Thời sự chuyên nghiệp)</option>
      <option value="Hải Đăng">Hải Đăng (Nam · Bắc 48kHz — Chuẩn mực phổ thông)</option>
    </optgroup>
    <optgroup label="Miền Trung">
      <option value="Ngọc Trân">Ngọc Trân (Nữ · Huế 48kHz — Ngọt ngào, sâu lắng)</option>
      <option value="Quang Sơn">Quang Sơn (Nam · Trung 48kHz — Chân chất mộc mạc)</option>
    </optgroup>
    <optgroup label="Tiếng Anh & Tiếng Nhật (Kokoro ONNX)">
      <option value="af_heart">af_heart (Nữ Mỹ — Ấm áp tự nhiên)</option>
      <option value="am_adam">am_adam (Nam Mỹ — Truyền cảm)</option>
      <option value="bf_emma">bf_emma (Nữ Anh — Giọng chuẩn Oxford)</option>
      <option value="jf_alpha">jf_alpha (Nữ Nhật — Trong trẻo)</option>
    </optgroup>
  </select>
</div>

<!-- 4. ĐỊNH DẠNG XUẤT -->
<div class="section">
  <div class="section-label">4. Định Dạng Thành Phẩm Đầu Ra</div>
  <div class="checkbox-group">
    <label class="checkbox-label">
      <input type="checkbox" id="fmtM4b" checked>
      Container sách nói .m4b đơn lẻ có chapter markers và bìa nhúng (tương thích Apple Books, CarPlay, Android Auto)
    </label>
    <label class="checkbox-label">
      <input type="checkbox" id="fmtMp3" checked>
      Thư mục MP3 từng chương có đánh số và gắn đầy đủ thẻ ID3v2 (Title, Artist, Album, Track)
    </label>
    <label class="checkbox-label">
      <input type="checkbox" id="fmtDocx" checked>
      Kịch bản chữ đối chiếu định dạng Word (.docx) và Markdown (.md)
    </label>
  </div>
</div>

<!-- ACTION BAR -->
<div class="footer-bar">
  <button class="btn-cancel" onclick="cancel()">Hủy</button>
  <button class="btn-launch" onclick="launchSkill()">
    ${iconPlay} Khởi Chạy Sản Xuất Sách Nói
  </button>
</div>

<script>
  const vscode = acquireVsCodeApi();
  let selectedLevel = 3;
  let selectedFilePath = ${initFilePathJson};

  function selectLevel(el) {
    document.querySelectorAll('.level-card').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    selectedLevel = parseInt(el.getAttribute('data-level'), 10);
  }

  function browseFile() {
    vscode.postMessage({ command: 'select_file' });
  }

  function cancel() {
    vscode.postMessage({ command: 'cancel' });
  }

  function launchSkill() {
    const voice = document.getElementById('voiceSelect').value;
    const formats = [];
    if (document.getElementById('fmtM4b').checked) formats.push('.m4b chaptered');
    if (document.getElementById('fmtMp3').checked) formats.push('thư mục MP3 ID3v2');
    if (document.getElementById('fmtDocx').checked) formats.push('kịch bản DOCX/MD');

    vscode.postMessage({
      command: 'launch',
      config: {
        sourceFile: selectedFilePath,
        level: selectedLevel,
        voice: voice,
        outputFormats: formats
      }
    });
  }

  window.addEventListener('message', event => {
    const msg = event.data;
    if (msg.type === 'file_selected') {
      selectedFilePath = msg.filePath;
      const el = document.getElementById('fileInfoText');
      el.textContent = msg.fileName;
      el.classList.add('has-file');
    }
  });
</script>

</body>
</html>`;
}

module.exports = {
    isStudioSkill,
    openStudioLaunchpad,
};

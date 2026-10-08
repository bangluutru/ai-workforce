/**
 * icons.js — Bản đồ Icon & Màu nền cho Skills và Workflows
 *
 * Icon: Lucide (https://lucide.dev, giấy phép ISC) — SVG được nhúng trực tiếp,
 * không phụ thuộc CDN/npm, đồng bộ 100% qua Git (Luật R0).
 * Màu nền: các lớp `tone-*` trong media/webview.css (bảng màu trầm, đồng bộ).
 *
 * Khi thêm skill/workflow mới: bổ sung entry vào ICON_MAP với
 *   { icon: '<tên Lucide trong LUCIDE>', tone: 'tone-xxx', codicon: '<codicon VS Code>', label }
 */

// Nội dung bên trong <svg viewBox="0 0 24 24"> của từng icon Lucide
const LUCIDE = {
    'book-open': '<path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/>',
    'clipboard-list': '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
    'search': '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    'mic': '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/>',
    'rocket': '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>',
    'languages': '<path d="m5 8 6 6"/><path d="m4 14 6-6 2-3"/><path d="M2 5h12"/><path d="M7 2h1"/><path d="m22 22-5-10-5 10"/><path d="M14 18h6"/>',
    'file-text': '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    'star': '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',
    'pen-line': '<path d="M12 20h9"/><path d="M16.376 3.622a1 1 0 0 1 3.002 3.002L7.368 18.635a2 2 0 0 1-.855.506l-2.872.838a.5.5 0 0 1-.62-.62l.838-2.872a2 2 0 0 1 .506-.854z"/>',
    'users': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    'scroll-text': '<path d="M15 12h-5"/><path d="M15 8h-5"/><path d="M19 17V5a2 2 0 0 0-2-2H4"/><path d="M8 21h12a2 2 0 0 0 2-2v-1a1 1 0 0 0-1-1H11a1 1 0 0 0-1 1v1a2 2 0 1 1-4 0V5a2 2 0 1 0-4 0v2a1 1 0 0 0 1 1h3"/>',
    'scale': '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    'landmark': '<line x1="3" x2="21" y1="22" y2="22"/><line x1="6" x2="6" y1="18" y2="11"/><line x1="10" x2="10" y1="18" y2="11"/><line x1="14" x2="14" y1="18" y2="11"/><line x1="18" x2="18" y1="18" y2="11"/><polygon points="12 2 20 7 4 7"/>',
    'briefcase': '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    'scan-text': '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M7 8h8"/><path d="M7 12h10"/><path d="M7 16h6"/>',
    'newspaper': '<path d="M4 22h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H8a2 2 0 0 0-2 2v16a2 2 0 0 1-2 2Zm0 0a2 2 0 0 1-2-2v-9c0-1.1.9-2 2-2h2"/><path d="M18 14h-8"/><path d="M15 18h-5"/><path d="M10 6h8v4h-8V6Z"/>',
    'palette': '<circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/><circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/><circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/><circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>',
    'chart-column': '<path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    'captions': '<rect width="18" height="14" x="3" y="5" rx="2" ry="2"/><path d="M7 15h4M15 15h2M7 11h2M13 11h4"/>',
    'shield-check': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    'calculator': '<rect width="16" height="20" x="4" y="2" rx="2"/><line x1="8" x2="16" y1="6" y2="6"/><line x1="16" x2="16" y1="14" y2="18"/><path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/><path d="M12 14h.01"/><path d="M8 14h.01"/><path d="M12 18h.01"/><path d="M8 18h.01"/>',
    'layout-template': '<rect width="18" height="7" x="3" y="3" rx="1"/><rect width="9" height="7" x="3" y="14" rx="1"/><rect width="5" height="7" x="16" y="14" rx="1"/>',
    'globe': '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    'audio-lines': '<path d="M2 10v3"/><path d="M6 6v11"/><path d="M10 3v18"/><path d="M14 8v7"/><path d="M18 5v13"/><path d="M22 10v3"/>',
    'headphones': '<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"/>',
    'glasses': '<circle cx="6" cy="15" r="4"/><circle cx="18" cy="15" r="4"/><path d="M14 15a2 2 0 0 0-2-2 2 2 0 0 0-2 2"/><path d="M2.5 13 5 7c.7-1.3 1.4-2 3-2"/><path d="M21.5 13 19 7c-.7-1.3-1.5-2-3-2"/>',
    'clapperboard': '<path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3Z"/><path d="m6.2 5.3 3.1 3.9"/><path d="m12.4 3.4 3.1 4"/><path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    'brush': '<path d="m9.06 11.9 8.07-8.06a2.85 2.85 0 1 1 4.03 4.03l-8.06 8.08"/><path d="M7.07 14.94c-1.66 0-3 1.35-3 3.02 0 1.33-2.5 1.52-2 2.02 1.08 1.1 2.49 2.02 4 2.02 2.2 0 4-1.8 4-4.04a3.01 3.01 0 0 0-3-3.02z"/>',
    'target': '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    'layers': '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',

    // UI Chrome & Navigation Icons (thay thế triệt để Emoji)
    'bot': '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/>',
    'refresh-cw': '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    'zap': '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    'library': '<path d="m16 6 4 14"/><path d="M12 6v14"/><path d="M8 8v12"/><path d="M4 4v16"/>',
    'x': '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    'play': '<polygon points="6 3 20 12 6 21 6 3"/>',
    'git-branch': '<line x1="6" x2="6" y1="3" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/>',
    'inbox': '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>',
    'check-circle-2': '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    'cloud': '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
    'copy': '<rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
    'folder': '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>',
    'message-square': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><path d="M8 10h.01"/><path d="M12 10h.01"/><path d="M16 10h.01"/>',
    'chevron-down': '<polyline points="6 9 12 15 18 9"/>',
    'chevron-up': '<polyline points="18 15 12 9 6 15"/>',
    'chevron-right': '<polyline points="9 18 15 12 9 6"/>',
    'activity': '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    'sprout': '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z"/>',
    'flask-conical': '<path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16h10"/>',
    'cpu': '<rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/>',
};

// Map biểu tượng danh mục Knowledge Catalog (Lucide thay thế Emoji)
const CATALOG_CATEGORY_ICONS = {
    health_medical:   'activity',
    genki_business:   'sprout',
    legal_standards:  'scale',
    rd_laboratory:    'flask-conical',
    ai_tech:          'cpu',
    general_hr:       'users',
};

// Aliases cho tên biểu tượng thay thế để tương thích tuyệt đối
const ICON_ALIASES = {
    'lightning': 'zap',
    'magnifying-glass': 'search',
    'arrows-clockwise': 'refresh-cw',
    'robot': 'bot',
    'books': 'library',
    'tray': 'inbox',
    'notebook': 'book-open',
    'check-circle': 'check-circle-2',
    'translate': 'languages',
    'chat-circle-dots': 'message-square',
    'pen-nib': 'pen-line',
    'pencil-line': 'pen-line',
    'scales': 'scale',
    'file-pdf': 'file-text',
    'caret-down': 'chevron-down',
    'caret-up': 'chevron-up',
    'caret-right': 'chevron-right',
    'first-aid': 'activity',
    'plant': 'sprout',
    'flask': 'flask-conical',
};

const ICON_MAP = {
    // Workflows
    'W0-so-tay-aiwf':         { icon: 'book-open',      tone: 'tone-ink',     codicon: 'book',          label: 'Sổ tay\nAIWF' },
    'so-tay-aiwf':            { icon: 'book-open',      tone: 'tone-ink',     codicon: 'book',          label: 'Sổ tay\nAIWF' },
    'W2-chuan-hoa-workspace-ag': { icon: 'layers',       tone: 'tone-navy',    codicon: 'sync',          label: 'Chuẩn Hoá\nWorkspace' },
    'W2-sang-loc-cv':         { icon: 'search',         tone: 'tone-indigo',  codicon: 'search',        label: 'Sàng lọc\nCV' },
    'W3-phong-van':           { icon: 'mic',            tone: 'tone-violet',  codicon: 'mic',           label: 'Phỏng vấn' },
    'W4-onboarding':          { icon: 'rocket',         tone: 'tone-teal',    codicon: 'rocket',        label: 'Onboarding' },

    // Skills — nhóm Văn bản & Dịch thuật (xanh dương/ocean)
    'ejv-translate':          { icon: 'languages',      tone: 'tone-ocean',   codicon: 'globe',         label: 'Dịch Thuật\nEJV' },
    'dich-thuat':             { icon: 'globe',          tone: 'tone-ocean',   codicon: 'globe',         label: 'Dịch\nThuật' },
    'boc-tach-pdf':           { icon: 'scan-text',      tone: 'tone-navy',    codicon: 'file-pdf',      label: 'Bóc tách\nPDF' },
    'xu-ly-van-phong':        { icon: 'file-text',      tone: 'tone-navy',    codicon: 'file',          label: 'Xử lý\nVăn phòng' },
    'doc-sau':                { icon: 'glasses',        tone: 'tone-indigo',  codicon: 'eye',           label: 'Đọc Sâu' },

    // Pháp lý & Tài chính (indigo/graphite/emerald/ochre)
    'tu-van-phap-luat':          { icon: 'scale',       tone: 'tone-indigo',  codicon: 'law',           label: 'Pháp Luật\nViệt Nam' },
    'tu-van-phap-luat-nhat-ban': { icon: 'landmark',    tone: 'tone-crimson', codicon: 'law',           label: 'Pháp luật\nNhật Bản' },
    'quan-ly-hop-dong':       { icon: 'scroll-text',    tone: 'tone-graphite',codicon: 'file-text',     label: 'Quản lý\nhợp đồng' },
    'bao-cao-kt':             { icon: 'chart-column',   tone: 'tone-emerald', codicon: 'graph',         label: 'Báo cáo\nTài chính' },
    'tu-van-thue':            { icon: 'calculator',     tone: 'tone-ochre',   codicon: 'symbol-numeric',label: 'Tư Vấn\nThuế' },

    // Nhân sự
    'boc-tach-cv':            { icon: 'file-text',      tone: 'tone-copper',  codicon: 'file',          label: 'Bóc tách\nCV' },
    'cham-diem-cv':           { icon: 'star',           tone: 'tone-ochre',   codicon: 'star-empty',    label: 'Chấm điểm\nCV' },
    'viet-jd':                { icon: 'pen-line',       tone: 'tone-ocean',   codicon: 'edit',          label: 'Viết JD' },
    'phan-tich-nhan-su':      { icon: 'users',          tone: 'tone-emerald', codicon: 'organization',  label: 'Phân tích\nnhân sự' },

    // Nội dung & Sáng tạo (plum/copper/teal)
    'viet-chuyen-nghiep':     { icon: 'pen-line',       tone: 'tone-plum',    codicon: 'edit',          label: 'Viết\nChuyên nghiệp' },
    'viet-bai':               { icon: 'pen-line',       tone: 'tone-plum',    codicon: 'edit',          label: 'Viết bài\nĐa kênh' },
    'chotto-newsroom':        { icon: 'newspaper',      tone: 'tone-crimson', codicon: 'preview',       label: 'Biên tập\nChotto' },
    'thiet-ke':               { icon: 'palette',        tone: 'tone-copper',  codicon: 'symbol-color',  label: 'Thiết kế\nĐồ họa' },
    'tao-landing-page':       { icon: 'layout-template',tone: 'tone-teal',    codicon: 'layout',        label: 'Tạo Landing\nPage' },
    'app-auditor':            { icon: 'shield-check',   tone: 'tone-graphite',codicon: 'shield',        label: 'Kiểm Định\nỨng Dụng' },

    // Media (violet)
    'video-studio':           { icon: 'clapperboard',   tone: 'tone-violet',  codicon: 'device-camera-video', label: 'Studio\nVideo' },
    'phu-de':                 { icon: 'captions',       tone: 'tone-violet',  codicon: 'symbol-text',   label: 'Tạo\nPhụ Đề' },
    'long-tieng':             { icon: 'audio-lines',    tone: 'tone-violet',  codicon: 'unmute',        label: 'Lồng Tiếng\nVideo' },
    'sach-noi':               { icon: 'headphones',     tone: 'tone-violet',  codicon: 'unmute',        label: 'Sách Nói\nAI' },
    'hand-drawn-animation':   { icon: 'brush',          tone: 'tone-plum',    codicon: 'paintcan',      label: 'Tạo\nHoạt Hình' },
};

const FALLBACK_ICONS = ['briefcase', 'target', 'layers', 'file-text'];
const FALLBACK_TONES = [
    'tone-navy', 'tone-indigo', 'tone-violet', 'tone-teal',
    'tone-ocean', 'tone-emerald', 'tone-copper', 'tone-graphite',
];
// Giữ tên cũ để tương thích ngược
const FALLBACK_GRADIENTS = FALLBACK_TONES;

/** Trả về chuỗi <svg> hoàn chỉnh cho một icon Lucide. */
function renderSvg(name, size = 15, className = '') {
    const alias = ICON_ALIASES[name] || name;
    const body = LUCIDE[alias] || LUCIDE[name] || LUCIDE.briefcase;
    const classAttr = className ? ` class="${className}"` : '';
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"${classAttr} aria-hidden="true">${body}</svg>`;
}

const renderLucideIcon = renderSvg;

function renderCatalogCategoryIcon(catId, size = 13, className = '') {
    const iconName = CATALOG_CATEGORY_ICONS[catId] || 'folder';
    return renderSvg(iconName, size, className);
}

function getIconConfig(name, index) {
    const base = ICON_MAP[name] || {
        icon: FALLBACK_ICONS[index % FALLBACK_ICONS.length],
        tone: FALLBACK_TONES[index % FALLBACK_TONES.length],
        codicon: 'tools',
        label: null,
    };
    return {
        ...base,
        svg: renderSvg(base.icon, 21),
        gradient: base.tone,           // tương thích ngược với code đọc `.gradient`
        quickPickIcon: `$(${base.codicon || 'tools'})`,
    };
}

module.exports = {
    LUCIDE,
    CATALOG_CATEGORY_ICONS,
    ICON_ALIASES,
    ICON_MAP,
    FALLBACK_ICONS,
    FALLBACK_TONES,
    FALLBACK_GRADIENTS,
    renderSvg,
    renderLucideIcon,
    renderCatalogCategoryIcon,
    getIconConfig,
};

/**
 * icons.js — Bản đồ Icon & Gradient cho Skills và Workflows
 *
 * Khi thêm skill/workflow mới, chỉ cần bổ sung entry vào ICON_MAP.
 * Nếu không có entry, hệ thống tự chọn icon/gradient từ danh sách dự phòng.
 */

const ICON_MAP = {
    // Workflows
    'W0-so-tay-aiwf':         { icon: '📖', gradient: 'gradient-teal', label: 'Sổ tay\nAIWF' },
    'so-tay-aiwf':            { icon: '📖', gradient: 'gradient-teal', label: 'Sổ tay\nAIWF' },
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

module.exports = {
    ICON_MAP,
    FALLBACK_ICONS,
    FALLBACK_GRADIENTS,
    getIconConfig,
};

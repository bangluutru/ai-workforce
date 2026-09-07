/**
 * scanner.js — Quét Skills, Workflows và Knowledge Catalog
 *
 * Đọc thư mục .agents/ để phát hiện tự động tất cả skills, workflows
 * và catalog tri thức đã đồng bộ.
 */

const fs = require('fs');
const path = require('path');
const { parseFrontmatter, findAgentsDir } = require('./utils');

function scanItems() {
    const agentsDir = findAgentsDir();
    if (!agentsDir) return { workflows: [], skills: [], catalog: null };

    const result = { workflows: [], skills: [], catalog: null };

    // 1. Workflows
    const workflowDir = path.join(agentsDir, 'workflows');
    if (fs.existsSync(workflowDir)) {
        const files = fs.readdirSync(workflowDir).filter(f => f.endsWith('.md')).sort();
        for (const file of files) {
            const content = fs.readFileSync(path.join(workflowDir, file), 'utf-8');
            const meta = parseFrontmatter(content);
                const cat = meta.category || 'workflows';
                result.workflows.push({
                    name: meta.name || file.replace('.md', ''),
                    displayName: meta['display-name'] || meta.display_name || meta.displayName || '',
                    description: meta.description || '',
                    trigger: meta.trigger || `Hãy thực hiện workflow "${meta.name || file.replace('.md', '')}" theo quy trình đã định`,
                    type: 'workflow',
                    category: cat,
                    categoryName: 'Quy trình',
                    action: meta.action || '',
                    targetFile: meta.target_file || meta.targetFile || '',
                });
        }
    }

    // Default category mapping for known skills
    const DEFAULT_SKILL_CATEGORIES = {
        'viet-bai': { id: 'content', name: 'Nội dung' },
        'thiet-ke': { id: 'content', name: 'Nội dung' },
        'tao-landing-page': { id: 'content', name: 'Nội dung' },
        'phu-de': { id: 'content', name: 'Nội dung' },
        'viet-jd': { id: 'content', name: 'Nội dung' },
        'viet-chuyen-nghiep': { id: 'content', name: 'Nội dung' },

        'ejv-translate': { id: 'docs', name: 'Tài liệu' },
        'pdf-translate': { id: 'docs', name: 'Tài liệu' },
        'boc-tach-pdf': { id: 'docs', name: 'Tài liệu' },
        'boc-tach-cv': { id: 'docs', name: 'Tài liệu' },
        'xu-ly-van-phong': { id: 'docs', name: 'Tài liệu' },

        'tu-van-phap-luat': { id: 'legal_finance', name: 'Pháp lý & Thuế' },
        'tu-van-thue-tncn': { id: 'legal_finance', name: 'Pháp lý & Thuế' },
        'bao-cao-kt': { id: 'legal_finance', name: 'Pháp lý & Thuế' },
        'quan-ly-hop-dong': { id: 'legal_finance', name: 'Pháp lý & Thuế' },

        'app-auditor': { id: 'tech_ops', name: 'Kỹ thuật' },
        'phan-tich-nhan-su': { id: 'tech_ops', name: 'Kỹ thuật' },
        'cham-diem-cv': { id: 'tech_ops', name: 'Kỹ thuật' },
    };

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
                const skillName = meta.name || dir;
                const needsFile = meta.needs_file === 'true' || meta.needs_file === true || meta.needsFile === 'true' || meta.needsFile === true;
                
                const catInfo = DEFAULT_SKILL_CATEGORIES[skillName] || {
                    id: meta.category || 'other',
                    name: meta.category_name || meta.categoryName || 'Khác'
                };

                result.skills.push({
                    name: skillName,
                    displayName: meta['display-name'] || meta.display_name || meta.displayName || '',
                    description: meta.description || '',
                    trigger: meta.trigger || `Hãy thực hiện skill "${skillName}" theo đúng hướng dẫn trong SKILL.md`,
                    type: 'skill',
                    category: meta.category || catInfo.id,
                    categoryName: meta.category_name || meta.categoryName || catInfo.name,
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

module.exports = { scanItems };

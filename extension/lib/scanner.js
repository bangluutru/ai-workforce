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
        const files = fs.readdirSync(workflowDir).filter(f => f.endsWith('.md'));
        for (const file of files) {
            const content = fs.readFileSync(path.join(workflowDir, file), 'utf-8');
            const meta = parseFrontmatter(content);
            result.workflows.push({
                name: meta.name || file.replace('.md', ''),
                description: meta.description || '',
                trigger: meta.trigger || `Hãy thực hiện workflow "${meta.name || file.replace('.md', '')}" theo quy trình đã định`,
                type: 'workflow',
            });
        }
    }

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
                const needsFile = meta.needs_file === 'true' || meta.needs_file === true || meta.needsFile === 'true' || meta.needsFile === true;
                result.skills.push({
                    name: meta.name || dir,
                    description: meta.description || '',
                    trigger: meta.trigger || `Hãy thực hiện skill "${meta.name || dir}" theo đúng hướng dẫn trong SKILL.md`,
                    type: 'skill',
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

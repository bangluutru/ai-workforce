const fs = require('fs');
const path = require('path');

const AGENTS_DIR = path.join(__dirname, '../.agents');
const SKILLS_DIR = path.join(AGENTS_DIR, 'skills');
const WORKFLOWS_DIR = path.join(AGENTS_DIR, 'workflows');
const OUTPUT_FILE = path.join(__dirname, 'data.json');

// Hàm parse YAML cơ bản bằng regex (không cần cài js-yaml để giữ thư mục sạch)
function parseYAML(yamlString) {
    const lines = yamlString.split(/\r?\n/);
    const result = {};
    for (const line of lines) {
        const match = line.match(/^([a-zA-Z0-9_-]+):\s*(.*)$/);
        if (match) {
            result[match[1].trim()] = match[2].trim().replace(/^['"]|['"]$/g, '');
        }
    }
    return result;
}

// Đọc tệp md và trích xuất YAML frontmatter
function parseMarkdownFile(filePath) {
    if (!fs.existsSync(filePath)) return null;
    const content = fs.readFileSync(filePath, 'utf-8');
    const yamlMatch = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (yamlMatch) {
        return parseYAML(yamlMatch[1]);
    }
    return null;
}

function scanDirectory(dir, isWorkflow = false) {
    if (!fs.existsSync(dir)) return [];
    const results = [];
    const items = fs.readdirSync(dir);

    for (const item of items) {
        const itemPath = path.join(dir, item);
        const stat = fs.statSync(itemPath);

        if (stat.isDirectory() && !isWorkflow) {
            // Skill thường nằm trong thư mục con (ví dụ: skills/boc-tach-cv/SKILL.md)
            const mdPath = path.join(itemPath, 'SKILL.md');
            const data = parseMarkdownFile(mdPath);
            if (data) {
                results.push({ ...data, type: 'skill', folder: item });
            }
        } else if (stat.isFile() && item.endsWith('.md') && isWorkflow) {
            // Workflow thường là file .md trực tiếp
            const data = parseMarkdownFile(itemPath);
            if (data) {
                results.push({ ...data, type: 'workflow', file: item });
            }
        }
    }
    return results;
}

function build() {
    console.log('Quét hệ thống AI Workforce...');
    const skills = scanDirectory(SKILLS_DIR, false);
    const workflows = scanDirectory(WORKFLOWS_DIR, true);

    const data = {
        skills,
        workflows,
        lastUpdated: new Date().toISOString()
    };

    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(data, null, 2));
    console.log(`Đã xuất dữ liệu thành công ra ${OUTPUT_FILE}`);
    console.log(`- ${skills.length} Kỹ năng (Skills)`);
    console.log(`- ${workflows.length} Quy trình (Workflows)`);
}

build();

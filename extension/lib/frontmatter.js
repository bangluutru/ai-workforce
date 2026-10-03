/**
 * frontmatter.js — Parser YAML frontmatter tối giản (không phụ thuộc vscode)
 *
 * Dùng chung cho extension (lib/utils.js → scanner.js) và dashboard/build_dashboard.js.
 * Hỗ trợ:
 *   - key: value (bỏ dấu nháy bao ngoài)
 *   - Block scalar gập / nguyên văn: `key: >-`, `key: >`, `key: |`, `key: |-`, `key: |+`
 *   - Plain scalar nhiều dòng (dòng tiếp theo thụt lề)
 * Chỉ đọc khóa cấp cao nhất; khóa lồng (mapping/list thụt lề dưới khóa rỗng) bị bỏ qua.
 */

const KEY_RE = /^([a-zA-Z0-9_-]+):(?:\s+(.*))?\s*$/;
const BLOCK_RE = /^([>|])([+-]?)(\d*)([+-]?)\s*(#.*)?$/;

function stripQuotes(value) {
    return value.trim().replace(/^['"]|['"]$/g, '');
}

function indentOf(line) {
    const m = line.match(/^[ \t]*/);
    return m ? m[0].length : 0;
}

function foldLines(lines) {
    // Folded scalar: dòng liền nhau nối bằng dấu cách, dòng trống → xuống dòng
    let out = '';
    let prevBlank = true;
    for (const line of lines) {
        if (line.trim() === '') {
            out += '\n';
            prevBlank = true;
        } else {
            out += (prevBlank ? '' : ' ') + line;
            prevBlank = false;
        }
    }
    return out;
}

function parseYAMLBlock(yamlString) {
    const lines = yamlString.split(/\r?\n/);
    const result = {};
    let i = 0;
    while (i < lines.length) {
        const line = lines[i];
        const kv = line.match(KEY_RE);
        if (!kv) { i++; continue; }

        const key = kv[1].trim();
        const rawValue = (kv[2] || '').trim();
        i++;

        // Gom các dòng con (thụt lề hoặc trống) thuộc về khóa này
        const childLines = [];
        while (i < lines.length && (lines[i].trim() === '' || indentOf(lines[i]) > 0)) {
            childLines.push(lines[i]);
            i++;
        }
        // Dòng trống cuối không thuộc giá trị
        while (childLines.length && childLines[childLines.length - 1].trim() === '') childLines.pop();

        const block = rawValue.match(BLOCK_RE);
        if (block) {
            const style = block[1];
            const nonBlank = childLines.filter(l => l.trim() !== '');
            const baseIndent = nonBlank.length ? Math.min(...nonBlank.map(indentOf)) : 0;
            const body = childLines.map(l => (l.trim() === '' ? '' : l.slice(baseIndent)));
            const text = style === '|' ? body.join('\n') : foldLines(body);
            result[key] = text.trim();
        } else if (rawValue !== '') {
            // Plain/quoted scalar, có thể kéo dài nhiều dòng thụt lề
            const cont = childLines.map(l => l.trim()).filter(Boolean);
            const joined = [rawValue, ...cont].join(' ');
            result[key] = stripQuotes(joined);
        } else {
            // Khóa rỗng (mapping/list lồng) — giữ hành vi cũ: chuỗi rỗng
            result[key] = '';
        }
    }
    return result;
}

function parseFrontmatter(content) {
    const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!match) return {};
    return parseYAMLBlock(match[1]);
}

module.exports = { parseFrontmatter, parseYAMLBlock };

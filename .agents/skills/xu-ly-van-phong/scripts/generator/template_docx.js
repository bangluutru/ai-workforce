// template_docx.js - Khung DOCX Track 2 (doanh nghiệp) đúng KHUNG MẶC ĐỊNH CHUNG (SKILL.md quy tắc 9).
// Dùng làm điểm khởi đầu: copy file này vào <process_dir>, thay phần CONTENT, giữ nguyên các hằng số khung.
//
//   node template_docx.js <brand_kit.json> <output.docx>
//
// Khung (standards/dynamic_structure/docx-page-setup.md): A4, lề trên/dưới 2 cm, trái 3 cm, phải 2 cm;
// body căn đều, lùi đầu dòng 1,25 cm, spacing 3pt/3pt, line at-least 1,3 x cỡ chữ; đề mục cấp cao nhất
// lùi 1,0 cm; bullet "-" cấp 1, "+" cấp 2, khối thẳng (left 0); bảng full khổ, chữ nhỏ hơn body.
// Brand kit chỉ đắp màu (heading, header bảng, zebra, callout), không đổi khung.

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, BorderStyle,
  WidthType, ShadingType, AlignmentType, LineRuleType, LevelFormat, LevelSuffix,
} = require('docx');

const [brandKitPath, outArg] = process.argv.slice(2);
if (!brandKitPath || !outArg) {
  console.error('Cách dùng: node template_docx.js <brand_kit.json> <output.docx>');
  process.exit(2);
}
const brand = JSON.parse(fs.readFileSync(brandKitPath, 'utf8'));
const REQUIRED = ['dk1', 'lt1', 'dk2', 'lt2', 'accent1'];
const missing = REQUIRED.filter((k) => !(brand.colors || {})[k]);
if (missing.length) {
  console.error(`[ERROR] brand_kit.json thiếu màu: ${missing.join(', ')}. Chọn preset hoặc chạy lại extract_brand.py.`);
  process.exit(2);
}
const C = brand.colors;
const FONT_BODY = (brand.fonts && brand.fonts.body) || 'Times New Roman';
const FONT_HEAD = (brand.fonts && brand.fonts.heading) || FONT_BODY;

// ---------------- KHUNG (không chỉnh theo brand) ----------------
const CM = 567;                       // 1 cm = 567 DXA
const BODY_PT = 12;                   // cỡ chữ body
const HP = (pt) => pt * 2;            // half-point cho docx-js
const LINE = Math.round(BODY_PT * 1.3) * 20;   // at-least 1,3 x cỡ chữ (twip)
const CONTENT_W = 11906 - 3 * CM - 2 * CM;     // 9071 DXA
const BODY = {
  alignment: AlignmentType.JUSTIFIED,
  indent: { firstLine: 709 },
  spacing: { before: 60, after: 60, line: LINE, lineRule: LineRuleType.AT_LEAST },
};

const p = (text, opts = {}) => new Paragraph({ ...BODY, ...opts, children: [new TextRun({ text, ...(opts.run || {}) })] });
const bullet = (text, level = 0) => new Paragraph({
  ...BODY, indent: { left: 0, firstLine: 709 }, spacing: { ...BODY.spacing, before: 40 },
  numbering: { reference: 'dash', level }, children: [new TextRun(text)],
});

function table(rows) {
  // Bảng full khổ; độ rộng cột tỷ lệ theo độ dài nội dung dài nhất của cột (fitColumns đơn giản).
  const n = rows[0].length;
  const maxLen = [...Array(n).keys()].map((j) => Math.max(...rows.map((r) => String(r[j]).length), 4));
  const total = maxLen.reduce((a, b) => a + b, 0);
  const widths = maxLen.map((l) => Math.round((CONTENT_W * l) / total));
  const border = { style: BorderStyle.SINGLE, size: 4, color: C.dk2 };
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((r, i) => new TableRow({
      tableHeader: i === 0,
      children: r.map((cell, j) => new TableCell({
        width: { size: widths[j], type: WidthType.DXA },
        borders: { top: border, bottom: border, left: border, right: border },
        shading: i === 0 ? { fill: C.accent1, type: ShadingType.CLEAR }
          : (i % 2 === 0 ? { fill: C.lt2, type: ShadingType.CLEAR } : undefined),
        margins: { top: 40, bottom: 40, left: 100, right: 100 },
        children: [new Paragraph({
          alignment: i === 0 ? AlignmentType.CENTER
            : (/^[\d.,%-]+$/.test(String(cell)) ? AlignmentType.RIGHT : AlignmentType.LEFT),
          children: [new TextRun({ text: String(cell), bold: i === 0, size: HP(BODY_PT - 1), color: i === 0 ? C.lt1 : C.dk1 })],
        })],
      })),
    })),
  });
}

function callout(text) {
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [CONTENT_W],
    rows: [new TableRow({ children: [new TableCell({
      width: { size: CONTENT_W, type: WidthType.DXA },
      shading: { fill: C.lt2, type: ShadingType.CLEAR },
      borders: { top: { style: BorderStyle.NIL }, bottom: { style: BorderStyle.NIL }, right: { style: BorderStyle.NIL },
        left: { style: BorderStyle.SINGLE, size: 24, color: C.accent1 } },
      margins: { top: 120, bottom: 120, left: 200, right: 200 },
      children: [new Paragraph({ alignment: AlignmentType.JUSTIFIED, children: [new TextRun({ text, color: C.dk1 })] })],
    })] })],
  });
}

// ---------------- CONTENT (thay bằng nội dung đã biên tập) ----------------
const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun(`${brand.company_name} - Đề xuất mẫu`)] }),
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun('I. Bối cảnh')] }),
  p('Đoạn văn body căn đều hai lề, lùi đầu dòng 1,25 cm, khoảng cách 3pt trước và sau, dòng tối thiểu bằng 1,3 lần cỡ chữ. Màu và font lấy từ brand kit, khung trang không đổi theo brand.'),
  new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun('1. Mục tiêu')] }),
  bullet('Ý liệt kê cấp 1 dùng dấu gạch đầu dòng.'),
  bullet('Ý liệt kê cấp 2 dùng dấu cộng.', 1),
  table([['Hạng mục', 'Số lượng', 'Ghi chú'], ['Hạng mục A', '12', 'Triển khai quý 1'], ['Hạng mục B', '8', 'Triển khai quý 2']]),
  callout('Callout box nền lt2, viền trái accent1, dùng cho lưu ý quan trọng.'),
];

const doc = new Document({
  creator: brand.company_name,
  styles: {
    default: { document: { run: { font: FONT_BODY, size: HP(BODY_PT), color: C.dk1 } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal',
        run: { font: FONT_HEAD, size: HP(BODY_PT + 6), bold: true, color: C.accent1 },
        paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 0, after: 120 } } },
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT_HEAD, size: HP(BODY_PT + 2), bold: true, color: C.accent1 },
        paragraph: { indent: { firstLine: CM }, spacing: { before: 360, after: 160 }, keepNext: true } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: FONT_HEAD, size: HP(BODY_PT), bold: true, color: C.dk2 },
        paragraph: { indent: { firstLine: 709 }, spacing: { before: 240, after: 120 }, keepNext: true } },
    ],
  },
  numbering: { config: [{ reference: 'dash', levels: [
    { level: 0, format: LevelFormat.BULLET, text: '-', alignment: AlignmentType.LEFT, suffix: LevelSuffix.SPACE,
      style: { paragraph: { indent: { left: 0, firstLine: 709 } } } },
    { level: 1, format: LevelFormat.BULLET, text: '+', alignment: AlignmentType.LEFT, suffix: LevelSuffix.SPACE,
      style: { paragraph: { indent: { left: 0, firstLine: 709 } } } },
  ] }] },
  sections: [{
    properties: { page: {
      size: { width: 11906, height: 16838 },
      margin: { top: 2 * CM, bottom: 2 * CM, left: 3 * CM, right: 2 * CM, header: Math.round(0.8 * CM), footer: Math.round(1.3 * CM) },
    } },
    children,
  }],
});

const outputPath = path.resolve(outArg);
fs.mkdirSync(path.dirname(outputPath), { recursive: true });
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(outputPath, buf);
  console.log(`[OK] Đã xuất ${outputPath} (brand: ${brand.company_name})`);
});

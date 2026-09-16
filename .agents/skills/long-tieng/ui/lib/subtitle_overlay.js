/**
 * subtitle_overlay.js — Engine hiển thị phụ đề trực tiếp trên Video Player.
 * Mô phỏng toán học 1:1 các thông số kiểu dáng ASS (Alignment, Font, Colors, Outline, Box, Margins).
 * Hoạt động thời gian thực (0ms latency), không gọi FFmpeg hoặc LLM khi chỉnh visual.
 */

export class SubtitleOverlay {
  constructor(videoElement, overlayElement, containerElement) {
    this.video = videoElement;
    this.overlay = overlayElement;
    this.container = containerElement;
    this.style = {};
    this.currentSegment = null;

    window.addEventListener("resize", () => this.applyStyle());
  }

  setStyle(styleConfig) {
    this.style = Object.assign({}, styleConfig);
    this.applyStyle();
    if (this.currentSegment) {
      this.renderSegment(this.currentSegment);
    }
  }

  applyStyle() {
    if (!this.overlay || !this.video) return;

    const s = this.style;
    const fontName = s.font_family || "Be Vietnam Pro";
    const fontSize = parseInt(s.font_size || 24, 10);
    const primaryCol = s.primary_color || "#ffffff";
    const secondaryCol = s.secondary_color || "#ffd700";
    const outlineCol = s.outline_color || "#000000";
    const outlineW = parseFloat(s.outline_width || 2.2);
    const bgCol = s.background_color || "#000000";
    const bgOpacity = parseFloat(s.background_opacity ?? 35) / 100;
    const align = parseInt(s.alignment || 2, 10);
    const marginV = parseInt(s.margin_v || 45, 10);
    const marginL = parseInt(s.margin_l || 40, 10);
    const marginR = parseInt(s.margin_r || 40, 10);
    const lineSpacing = parseInt(s.line_spacing || 6, 10);

    // Tính tỷ lệ co giãn phông chữ theo kích thước video thực tế hiển thị
    const nativeHeight = this.video.videoHeight || 720;
    const clientHeight = this.video.clientHeight || 540;
    const scale = clientHeight / nativeHeight;

    const scaledFontSize = Math.round(fontSize * scale);
    const scaledSubFontSize = Math.round(scaledFontSize * 0.8);
    const scaledMarginV = Math.round(marginV * scale);
    const scaledMarginL = Math.round(marginL * scale);
    const scaledMarginR = Math.round(marginR * scale);
    const scaledOutlineW = Math.max(0.8, outlineW * scale);
    const borderRadius = s.border_radius ?? 8;
    const scaledRadius = Math.max(0, Math.round(borderRadius * scale));
    const scaledLineSpacing = Math.round(lineSpacing * scale);

    // Khoảng đệm hộp (Padding) đồng bộ 1:1 với ass_generator
    let padX, padY;
    if (s.box_padding != null) {
      padX = Math.round(parseFloat(s.box_padding) * scale);
      padY = Math.round(parseFloat(s.box_padding) * 0.6 * scale);
    } else {
      padX = Math.round(fontSize * 0.5 * scale);
      padY = Math.round(fontSize * 0.3 * scale);
    }

    // Thiết lập vị trí (Alignment 9 ô kiểu ASS)
    this.overlay.style.position = "absolute";
    this.overlay.style.top = "auto";
    this.overlay.style.bottom = "auto";
    this.overlay.style.left = "auto";
    this.overlay.style.right = "auto";
    this.overlay.style.transform = "none";
    this.overlay.style.fontFamily = `"${fontName}", sans-serif`;
    this.overlay.style.width = "max-content";
    this.overlay.style.maxWidth = `calc(100% - ${scaledMarginL + scaledMarginR}px)`;

    // Căn dọc
    if (align >= 7 && align <= 9) {
      this.overlay.style.top = `${scaledMarginV}px`;
    } else if (align >= 4 && align <= 6) {
      this.overlay.style.top = "50%";
      this.overlay.style.transform = "translateY(-50%)";
    } else {
      // Default: bottom
      this.overlay.style.bottom = `${scaledMarginV}px`;
    }

    // Căn ngang
    if (align === 1 || align === 4 || align === 7) {
      this.overlay.style.left = `${scaledMarginL}px`;
      this.overlay.style.textAlign = "left";
      this.overlay.style.alignItems = "flex-start";
    } else if (align === 3 || align === 6 || align === 9) {
      this.overlay.style.right = `${scaledMarginR}px`;
      this.overlay.style.textAlign = "right";
      this.overlay.style.alignItems = "flex-end";
    } else {
      // Default: Center
      this.overlay.style.left = "50%";
      const curY = this.overlay.style.transform.includes("translateY") ? "translate(-50%, -50%)" : "translateX(-50%)";
      this.overlay.style.transform = curY;
      this.overlay.style.textAlign = "center";
      this.overlay.style.alignItems = "center";
    }

    // Nền hộp (Box background)
    if (bgOpacity > 0.05) {
      const hex = bgCol.replace("#", "");
      const r = parseInt(hex.substring(0, 2), 16) || 0;
      const g = parseInt(hex.substring(2, 4), 16) || 0;
      const b = parseInt(hex.substring(4, 6), 16) || 0;
      this.overlay.style.backgroundColor = `rgba(${r}, ${g}, ${b}, ${bgOpacity})`;
      this.overlay.style.padding = `${padY}px ${padX}px`;
      this.overlay.style.borderRadius = `${scaledRadius}px`;
    } else {
      this.overlay.style.backgroundColor = "transparent";
      this.overlay.style.padding = "0";
      this.overlay.style.borderRadius = "0";
    }

    // Viền chữ (Text Outline & Shadow)
    const shadow = this.generateTextStroke(outlineCol, scaledOutlineW);
    this.overlay.style.textShadow = shadow;

    // Lưu các biến CSS để truyền vào các dòng con
    this.overlay.style.setProperty("--primary-col", primaryCol);
    this.overlay.style.setProperty("--secondary-col", secondaryCol);
    this.overlay.style.setProperty("--font-size-main", `${scaledFontSize}px`);
    this.overlay.style.setProperty("--font-size-sub", `${scaledSubFontSize}px`);
    this.overlay.style.setProperty("--line-spacing", `${scaledLineSpacing}px`);
  }

  generateTextStroke(color, width) {
    if (width <= 0) return "none";
    const w = width;
    return `
      -${w}px -${w}px 0 ${color},
       ${w}px -${w}px 0 ${color},
      -${w}px  ${w}px 0 ${color},
       ${w}px  ${w}px 0 ${color},
       0px -${w}px 0 ${color},
       0px  ${w}px 0 ${color},
      -${w}px  0px 0 ${color},
       ${w}px  0px 0 ${color},
       0 2px 4px rgba(0,0,0,0.8)
    `;
  }

  renderSegment(segment) {
    this.currentSegment = segment;
    if (!segment) {
      this.overlay.style.display = "none";
      this.overlay.innerHTML = "";
      return;
    }

    this.overlay.style.display = "flex";
    const mode = this.style.mode || "bilingual";
    const order = this.style.bilingual_order || "target_top";

    const src = (segment.source_text || segment.orig_text || segment.text || "").trim();
    const trans = (segment.translated_text || segment.target_text || segment.text || "").trim();

    // Tính toán maxChars dựa theo font_size và resolution y hệt ass_generator.py
    const fontSize = parseInt(this.style.font_size || 24, 10);
    const nativeWidth = this.video.videoWidth || 1280;
    const marginL = parseInt(this.style.margin_l || 40, 10);
    const marginR = parseInt(this.style.margin_r || 40, 10);
    const targetTextWidth = (nativeWidth - marginL - marginR) * 0.85;
    const avgCharW = fontSize * 0.58;
    const maxChars = Math.max(24, Math.min(42, Math.round(targetTextWidth / avgCharW)));
    const maxCjkChars = Math.max(12, Math.min(24, Math.round(maxChars * 0.52)));

    const transLines = smartWrapText(trans, isCjk(trans) ? maxCjkChars : maxChars);
    const srcLines = smartWrapText(src, isCjk(src) ? maxCjkChars : maxChars);

    const transHtml = transLines.map(escapeHtml).join("<br>");
    const srcHtml = srcLines.map(escapeHtml).join("<br>");

    const srcFontFamily = isCjk(src) ? '"Noto Sans JP", sans-serif' : "inherit";
    const transFontFamily = isCjk(trans) ? '"Noto Sans JP", sans-serif' : "inherit";

    if (mode === "bilingual" && src && trans && src !== trans) {
      if (order === "target_top") {
        this.overlay.innerHTML = `
          <div class="sub-line-target" style="color: var(--primary-col); font-size: var(--font-size-main); font-family: ${transFontFamily}; line-height: 1.35;">${transHtml}</div>
          <div class="sub-line-source" style="color: var(--secondary-col); font-size: var(--font-size-sub); font-family: ${srcFontFamily}; line-height: 1.35; margin-top: var(--line-spacing);">${srcHtml}</div>
        `;
      } else {
        this.overlay.innerHTML = `
          <div class="sub-line-target" style="color: var(--primary-col); font-size: var(--font-size-main); font-family: ${srcFontFamily}; line-height: 1.35;">${srcHtml}</div>
          <div class="sub-line-source" style="color: var(--secondary-col); font-size: var(--font-size-sub); font-family: ${transFontFamily}; line-height: 1.35; margin-top: var(--line-spacing);">${transHtml}</div>
        `;
      }
    } else if (mode === "source_only") {
      this.overlay.innerHTML = `
        <div class="sub-line-target" style="color: var(--primary-col); font-size: var(--font-size-main); font-family: ${srcFontFamily}; line-height: 1.35;">${srcHtml}</div>
      `;
    } else {
      // Monolingual: Target (câu dịch)
      const chosenHtml = trans ? transHtml : srcHtml;
      const chosenFont = trans ? transFontFamily : srcFontFamily;
      this.overlay.innerHTML = `
        <div class="sub-line-target" style="color: var(--primary-col); font-size: var(--font-size-main); font-family: ${chosenFont}; line-height: 1.35;">${chosenHtml}</div>
      `;
    }
  }
}

function isCjk(text) {
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i);
    if ((code >= 0x4e00 && code <= 0x9fff) || (code >= 0x3040 && code <= 0x30ff)) {
      return true;
    }
  }
  return false;
}

function smartWrapText(text, maxChars = 30) {
  if (!text) return [];
  text = text.trim();
  if (text.includes("\n")) {
    const res = [];
    for (const l of text.split("\n")) {
      res.push(...smartWrapText(l, maxChars));
    }
    return res;
  }
  if (text.length <= maxChars) return [text];

  if (isCjk(text)) {
    const maxCjk = Math.max(12, Math.round(maxChars * 0.52));
    const numCjkLines = Math.max(2, Math.ceil(text.length / maxCjk));
    const targetCjkLen = text.length / numCjkLines;
    const lines = [];
    let cur = "";
    for (const ch of text) {
      cur += ch;
      if (cur.length >= Math.round(targetCjkLen) && lines.length < numCjkLines - 1) {
        lines.push(cur);
        cur = "";
      }
    }
    if (cur) lines.push(cur);
    return lines;
  }

  const words = text.split(" ");
  if (words.length <= 1) return [text];

  const numLines = Math.max(2, Math.ceil(text.length / maxChars));
  const targetLen = text.length / numLines;

  let bestSplit = 1;
  let bestScore = Infinity;

  for (let i = 1; i < words.length; i++) {
    const p1 = words.slice(0, i).join(" ");
    const p2 = words.slice(i).join(" ");

    let penalty = 0;
    if (p1.length > maxChars) {
      penalty += (p1.length - maxChars) * 100;
    }
    if (i === words.length - 1 && words[words.length - 1].length <= 4) {
      penalty += 50;
    }

    const diff = Math.abs(p1.length - targetLen);
    const score = diff + penalty;

    if (score < bestScore) {
      bestScore = score;
      bestSplit = i;
    }
  }

  const p1 = words.slice(0, bestSplit).join(" ");
  const p2 = words.slice(bestSplit).join(" ");
  const res = [p1];
  if (p2.length > maxChars) {
    res.push(...smartWrapText(p2, maxChars));
  } else {
    res.push(p2);
  }
  return res;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

"""OCR & Vision Fallback Engine for Scanned / Image-based Documents.

Conforms to Section 7.2 of AIWF Document Reconstruction Translator:
- Deterministic extraction: checks whether a PDF page has a native text layer.
- If text layer is absent or sparse (< 50 chars), triggers local tesseract OCR.
- Zero external paid API, 100% local execution.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf


class OCREngine:
    """Local OCR engine with graceful degradation."""

    def __init__(self, tesseract_path: Optional[str] = None):
        self.tesseract_bin = tesseract_path or shutil.which("tesseract") or "/opt/homebrew/bin/tesseract"
        self.is_available = Path(self.tesseract_bin).exists() if self.tesseract_bin else False

    def is_page_scanned(self, page: pymupdf.Page, min_char_threshold: int = 50) -> bool:
        """Determines if a page lacks a native text layer."""
        text = page.get_text("text").strip()
        if len(text) < min_char_threshold:
            # Check if page has images or large drawings covering the background
            images = page.get_images()
            return len(images) > 0 or len(text) == 0
        return False

    def ocr_page(self, page: pymupdf.Page, lang: str = "eng+vie+jpn") -> List[Dict[str, Any]]:
        """Extracts text blocks and bounding boxes from a scanned page using OCR.
        
        Returns a list of dicts with:
          text, bbox: (x0, y0, x1, y1), confidence, font_size
        """
        if not self.is_available:
            return []

        # Render page to high-res image (300 DPI)
        pix = page.get_pixmap(dpi=300)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as img_tmp:
            img_path = img_tmp.name
        pix.save(img_path)

        tsv_out = img_path + "_ocr"
        blocks: List[Dict[str, Any]] = []

        try:
            # Run tesseract with TSV output for word/line coordinates
            # Check available tesseract languages
            avail_langs = self._get_available_languages()
            use_lang = "eng"
            for candidate in ("vie", "jpn", "eng"):
                if candidate in avail_langs:
                    use_lang = candidate
                    break

            cmd = [
                self.tesseract_bin,
                img_path,
                tsv_out,
                "-l", use_lang,
                "tsv"
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

            tsv_file = tsv_out + ".tsv"
            if Path(tsv_file).exists():
                scale_x = page.rect.width / pix.width
                scale_y = page.rect.height / pix.height

                with open(tsv_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()

                # Parse TSV lines: level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
                current_block_words: List[str] = []
                current_bbox: Optional[List[float]] = None
                current_conf: float = 1.0

                for line in lines[1:]:
                    parts = line.strip().split("\t")
                    if len(parts) >= 12:
                        conf = float(parts[10])
                        word = parts[11].strip()
                        if conf > 0 and word:
                            left = float(parts[6]) * scale_x
                            top = float(parts[7]) * scale_y
                            w = float(parts[8]) * scale_x
                            h = float(parts[9]) * scale_y
                            x1, y1 = left + w, top + h

                            current_block_words.append(word)
                            if current_bbox is None:
                                current_bbox = [left, top, x1, y1]
                            else:
                                current_bbox[0] = min(current_bbox[0], left)
                                current_bbox[1] = min(current_bbox[1], top)
                                current_bbox[2] = max(current_bbox[2], x1)
                                current_bbox[3] = max(current_bbox[3], y1)
                            current_conf = min(current_conf, conf / 100.0)

                if current_block_words and current_bbox:
                    blocks.append({
                        "text": " ".join(current_block_words),
                        "bbox": tuple(current_bbox),
                        "confidence": current_conf,
                        "font_size": 10.0,
                    })

            return blocks
        except Exception:
            return []
        finally:
            if Path(img_path).exists():
                Path(img_path).unlink()
            if Path(tsv_out + ".tsv").exists():
                Path(tsv_out + ".tsv").unlink()

    def _get_available_languages(self) -> List[str]:
        try:
            res = subprocess.run([self.tesseract_bin, "--list-langs"], capture_output=True, text=True, check=True)
            return [line.strip() for line in res.stdout.splitlines()[1:] if line.strip()]
        except Exception:
            return ["eng"]

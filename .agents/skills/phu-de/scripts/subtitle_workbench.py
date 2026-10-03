#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
subtitle_workbench.py — Bàn làm việc phụ đề: nơi AGENT (Gemini) làm phần ngôn ngữ, script giữ kỷ luật.

  init      tạo project.json từ video_meta.json + segmented_subtitles.json (+ preset, ngôn ngữ, glossary)
  export    xuất lô việc cho agent: --task reflow | proofread | translate   → <process_dir>/tasks/*.json
  apply     nạp file lô đã điền "output" về project.json (có kiểm tra, có snapshot)
  qa        kiểm định phụ đề (CPL/dòng/CPS/thời lượng/chồng lấn/chưa dịch/từ treo cuối dòng) → exit 2 nếu FAIL
  preview   chụp N khung hình có phụ đề đã burn → ảnh lưới để NHÌN (font, dấu, vị trí, độ tương phản)
  export-subs  ghi .srt + .ass (+ .vtt) ra thư mục đầu ra

Quy trình chuẩn: init → export reflow → (agent) → apply → export proofread → apply →
[export translate → apply] → qa (lặp tới khi hết FAIL) → preview (nhìn) → export-subs / render_video.py
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SHARED_MEDIA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_shared", "media"))  # Luật R7
sys.path.insert(0, SHARED_MEDIA)
from linebreak import NO_END, is_cjk, lang_of, wrap_balanced  # noqa: E402
from project_manager import create_project, load_project, save_project  # noqa: E402
from semantic_segmenter import make_cfg, retime  # noqa: E402

PRESETS = os.path.join(SHARED_MEDIA, "subtitle_styles.json")
EM_DASH = "—"


def project_cfg(project):
    langs = project.get("languages", {})
    src = langs.get("source_lang") or "auto"
    sample = " ".join(s.get("source_text", "") for s in project.get("segments", [])[:30])
    st = project.get("style", {})
    lines = 1 if st.get("mode") == "bilingual" else 2
    return make_cfg(None if src == "auto" else src, st.get("max_cpl", 42), lines, sample=sample)


def displayed(seg, mode):
    """Các khối chữ thực sự hiện trên màn hình theo chế độ."""
    src, tr = seg.get("source_text", "").strip(), seg.get("translated_text", "").strip()
    if mode == "bilingual":
        return [tr, src] if tr and tr != src else [src]
    if mode == "source_only":
        return [src]
    return [tr or src]


def chars_of(text):
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text))


# ----------------------------------------------------------------------------------- init
def cmd_init(a):
    meta = json.load(open(a.meta, encoding="utf-8"))
    segs = json.load(open(a.segments, encoding="utf-8"))
    src = a.source_lang or segs.get("source_language", "auto")
    tgt = a.target_lang or src
    mode = a.mode or ("bilingual" if tgt != src else "monolingual")
    proj = create_project(meta, segs.get("segments", []), source_lang=src, target_lang=tgt, mode=mode, project_dir=a.process_dir)
    presets = json.load(open(PRESETS, encoding="utf-8"))["presets"]
    if a.preset not in presets:
        print(f"❌ Preset không tồn tại: {a.preset} ({', '.join(presets)})"); return 1
    style = {k: v for k, v in presets[a.preset].items() if k not in ("name", "description")}
    style.update({"preset": a.preset, "mode": mode})
    if meta.get("height", 1080) > meta.get("width", 1920):                     # video dọc: chữ to hơn, dòng ngắn hơn
        style.update({"max_cpl": 32, "margin_v": max(style.get("margin_v", 45), 140)})
    proj["style"] = style
    proj["glossary"] = [g.strip() for g in (a.glossary or "").split(",") if g.strip()]
    pf = os.path.join(a.process_dir, "project.json")
    save_project(proj, pf, f"init preset={a.preset} mode={mode}", make_snapshot=False)
    print(f"✅ project.json: {pf} | {len(proj['segments'])} phụ đề | {src} → {tgt} | {mode} | preset {a.preset}")
    return 0


# --------------------------------------------------------------------------------- export
INSTRUCTIONS = {
    "reflow": [
        "Nhiệm vụ: NGẮT LẠI phụ đề cho tự nhiên. KHÔNG được thêm, bớt, sửa bất kỳ chữ/dấu nào — chỉ dời ranh giới giữa các phụ đề và đặt '\\n' để ngắt dòng.",
        "Điền \"output\": danh sách chuỗi, mỗi chuỗi là MỘT phụ đề, theo đúng thứ tự, phủ kín toàn bộ chữ của lô.",
        "Mỗi phụ đề: một ý trọn vẹn; tối đa {lines} dòng × {cpl} ký tự; ngắt sau dấu câu hoặc trước liên từ/giới từ; không tách từ ghép (ứng dụng, khai báo, quyết toán), tên riêng, số + đơn vị; không để từ chức năng (của, các, the, of...) cuối dòng.",
        "Dòng trên ngắn hơn hoặc bằng dòng dưới khi có thể. Không tạo phụ đề chỉ có 1–2 từ.",
    ],
    "proofread": [
        "Nhiệm vụ: SOÁT LỖI NHẬN DẠNG GIỌNG NÓI dựa trên ngữ cảnh toàn bài và glossary.",
        "Sửa: từ đồng âm/sai dấu tiếng Việt, tên riêng, thuật ngữ, số liệu, chữ Hán sai (定管→定款). Giữ nguyên ý và văn nói; không viết lại cho hay hơn; giữ '\\n' nếu đã đúng chỗ.",
        "Điền \"output\": object {\"seg_xxx\": \"văn bản đã sửa\"} CHỈ cho phụ đề có thay đổi. Chỗ nghe không rõ mà không suy ra được: thêm \"[CẦN XÁC MINH]\" vào cuối câu.",
        "Ưu tiên kiểm tra các từ trong low_confidence_words, nhưng lỗi thường nằm cả ở từ có độ tin cậy cao.",
    ],
    "translate": [
        "Nhiệm vụ: DỊCH PHỤ ĐỀ sang {target}. Dịch theo ý của cả đoạn (đọc context), không dịch từng câu rời rạc.",
        "Mỗi bản dịch ≤ max_chars ký tự (giới hạn tốc độ đọc). Nếu dài hơn: lược từ thừa, dùng từ ngắn, bỏ từ đệm — giữ nguyên thông tin chính, tên riêng, số liệu.",
        "Văn phong phụ đề tự nhiên như người bản ngữ nói; xưng hô nhất quán cả video; thuật ngữ theo glossary. Không dùng '—', không ngoặc kép thừa, không chú thích dịch giả.",
        "Có thể đặt '\\n' để ngắt dòng ({cpl} ký tự/dòng). Điền \"output\": object {\"seg_xxx\": \"bản dịch\"} cho TẤT CẢ id.",
    ],
}


def cmd_export(a):
    pf = a.project; proj = load_project(pf); segs = proj["segments"]; cfg = project_cfg(proj)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(pf)), "tasks"); os.makedirs(out_dir, exist_ok=True)
    for f in glob.glob(os.path.join(out_dir, f"{a.task}_*.json")):
        os.remove(f)
    langs = proj.get("languages", {})
    target = langs.get("target_lang", "vi")
    tcfg = make_cfg(target, proj["style"].get("max_cpl", 42), 1 if proj["style"].get("mode") == "bilingual" else 2)
    # lô cắt tại khoảng lặng lớn nhất gần kích thước mong muốn (để reflow không phải dời chữ qua lô)
    batches, start = [], 0
    while start < len(segs):
        end = min(len(segs), start + a.batch)
        if end < len(segs):
            window = range(max(start + a.batch // 2, start + 1), end + 1)
            end = max(window, key=lambda k: segs[k]["start"] - segs[k - 1].get("speech_end", segs[k - 1]["end"]) if k < len(segs) else 99)
        batches.append((start, end)); start = end
    full = " ".join(s["source_text"].replace("\n", " ") for s in segs)
    for bi, (s0, s1) in enumerate(batches, 1):
        items = []
        for s in segs[s0:s1]:
            if a.task == "reflow":
                items.append({"id": s["id"], "text": "\n".join(wrap_balanced(s["source_text"], cfg["cpl"])), "sec": round(s["speech_end"] - s["start"], 2)})
            elif a.task == "proofread":
                items.append({"id": s["id"], "text": s["source_text"], "low_confidence_words": s.get("low_confidence_words", [])})
            else:
                dur = s["end"] - s["start"]
                items.append({"id": s["id"], "source": s["source_text"], "sec": round(dur, 2),
                              "max_chars": int(min(tcfg["max_chars"], max(tcfg["cpl"] * 0.6, dur * (tcfg["max_cps"] + 3))))})
        task = {"task": a.task, "batch": bi, "of": len(batches), "project": os.path.abspath(pf),
                "instructions": [t.replace("{lines}", str(cfg["max_chars"] // cfg["cpl"])).replace("{cpl}", str(cfg["cpl"] if a.task != "translate" else tcfg["cpl"])).replace("{target}", target) for t in INSTRUCTIONS[a.task]],
                "glossary": proj.get("glossary", []), "context_before": segs[s0 - 1]["source_text"] if s0 else "",
                "context_after": segs[s1]["source_text"] if s1 < len(segs) else "", "items": items, "output": [] if a.task == "reflow" else {}}
        if a.task in ("proofread", "translate") and bi == 1:
            task["full_transcript_for_context"] = full[:6000]
        fn = os.path.join(out_dir, f"{a.task}_{bi:02d}.json")
        json.dump(task, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"📤 {len(batches)} lô '{a.task}' tại {out_dir}/{a.task}_NN.json — điền trường \"output\" rồi chạy: apply --input <file>")
    return 0


# ---------------------------------------------------------------------------------- apply
def apply_reflow(proj, task):
    ids = [it["id"] for it in task["items"]]
    segs = proj["segments"]; idx = {s["id"]: i for i, s in enumerate(segs)}
    if any(i not in idx for i in ids):
        raise ValueError("Lô reflow không còn khớp project (đã reflow/sửa trước đó?). Chạy lại export --task reflow.")
    lo, hi = idx[ids[0]], idx[ids[-1]] + 1
    if any(segs[k].get("proofread") for k in range(lo, hi)):
        raise ValueError("Reflow phải chạy TRƯỚC proofread (chữ đã bị sửa nên không còn khớp từng từ với âm thanh).")
    words = [w for s in segs[lo:hi] for w in s["words"]]
    outs = [o.strip() for o in task["output"] if o and o.strip()]
    if not outs:
        raise ValueError("\"output\" rỗng.")
    have, want = "".join(chars_of(o) for o in outs), "".join(chars_of(w["word"]) for w in words)
    if have != want:
        k = next((i for i, (x, y) in enumerate(zip(have, want)) if x != y), min(len(have), len(want)))
        raise ValueError(f"Reflow đã đổi chữ (không được phép). Lệch tại …{want[max(0, k - 15):k + 15]}… ↔ …{have[max(0, k - 15):k + 15]}…")
    # ánh xạ ranh giới ký tự → ranh giới từ
    acc = 0
    cum = []
    for w in words:
        acc += len(chars_of(w["word"])); cum.append(acc)
    groups, wi, pos = [], 0, 0
    for o in outs:
        pos += len(chars_of(o)); g = []
        while wi < len(words) and cum[wi] <= pos:
            g.append(words[wi]); wi += 1
        if not g or cum[wi - 1] != pos:
            raise ValueError(f"Ranh giới phụ đề nằm GIỮA một từ: \"{o[-12:]}\". Chỉ ngắt giữa các từ.")
        groups.append((o, g))
    new = []
    for o, g in groups:
        conf = round(sum(w.get("probability", 1.0) for w in g) / len(g), 2)
        new.append({"start": g[0]["start"], "end": g[-1]["end"], "speech_end": g[-1]["end"], "source_text": o, "translated_text": o, "words": g,
                    "confidence": conf, "low_confidence_words": [w["word"] for w in g if w.get("probability", 1.0) < 0.6], "reflowed": True})
    proj["segments"] = segs[:lo] + new + segs[hi:]
    retime(proj["segments"], project_cfg(proj))
    return f"reflow lô {task['batch']}: {hi - lo} → {len(new)} phụ đề"


def apply_proofread(proj, task):
    out = task.get("output") or {}
    by = {s["id"]: s for s in proj["segments"]}
    n = 0
    for sid, text in out.items():
        if sid not in by:
            raise ValueError(f"id không tồn tại: {sid}")
        s = by[sid]; text = text.strip()
        if s.get("translated_text", "") == s.get("source_text", ""):
            s["translated_text"] = text
        s["source_text"] = text; n += 1
    for it in task["items"]:
        if it["id"] in by:
            by[it["id"]]["proofread"] = True
    return f"proofread lô {task['batch']}: sửa {n}/{len(task['items'])} phụ đề"


def apply_translate(proj, task):
    out = task.get("output") or {}
    by = {s["id"]: s for s in proj["segments"]}
    missing = [it["id"] for it in task["items"] if not str(out.get(it["id"], "")).strip()]
    if missing:
        raise ValueError(f"Thiếu bản dịch cho {len(missing)} id: {', '.join(missing[:10])}")
    long = []
    for it in task["items"]:
        t = str(out[it["id"]]).strip().replace(EM_DASH, " - ")
        by[it["id"]]["translated_text"] = t
        if len(t.replace("\n", "")) > it["max_chars"] * 1.1:
            long.append(f"{it['id']}({len(t)}>{it['max_chars']})")
    msg = f"translate lô {task['batch']}: {len(task['items'])} bản dịch"
    if long:
        msg += f" | ⚠️ quá dài so với tốc độ đọc: {', '.join(long)} — rút gọn rồi apply lại"
    return msg


def cmd_apply(a):
    task = json.load(open(a.input, encoding="utf-8")); pf = a.project or task["project"]
    proj = load_project(pf)
    fn = {"reflow": apply_reflow, "proofread": apply_proofread, "translate": apply_translate}[task["task"]]
    try:
        msg = fn(proj, task)
    except ValueError as e:
        print(f"❌ {e}"); return 1
    retime(proj["segments"], project_cfg(proj))
    save_project(proj, pf, msg)
    print(f"✅ {msg}")
    return 0


# ------------------------------------------------------------------------------------- qa
def cmd_qa(a):
    proj = load_project(a.project); segs = proj["segments"]; st = proj.get("style", {}); mode = st.get("mode", "monolingual")
    langs = proj.get("languages", {}); src, tgt = langs.get("source_lang"), langs.get("target_lang")
    fails, warns = [], []
    stats = {"n": len(segs), "lines_over": 0, "cps_high": 0, "short": 0, "long": 0}
    for i, s in enumerate(segs):
        dur = s["end"] - s["start"]
        for k, block in enumerate(displayed(s, mode)):
            cjk = is_cjk(block); cpl = min(st.get("max_cpl", 42), 16) if cjk else st.get("max_cpl", 42)
            lines = wrap_balanced(block, cpl)
            max_lines = 1 if (mode == "bilingual" and k == 1) else 2
            if len(lines) > max_lines + (1 if mode == "bilingual" else 0):
                fails.append(f"{s['id']}: {len(lines)} dòng — quá dài, cần tách phụ đề hoặc rút gọn: \"{block[:60]}\""); stats["lines_over"] += 1
            for ln in lines:
                if len(ln) > cpl * 1.15:
                    warns.append(f"{s['id']}: dòng {len(ln)} ký tự > {cpl}: \"{ln}\"")
                last = re.sub(r"[\W_]+$", "", ln.split(" ")[-1].lower()) if not cjk else ""
                if ln is not lines[-1] and last in NO_END.get(lang_of(ln), set()):
                    warns.append(f"{s['id']}: dòng kết thúc bằng từ chức năng \"{last}\" → dời xuống dòng dưới (dùng '\\n')")
            if k == 0:
                cps = len(block.replace("\n", "")) / max(.01, dur); lim = 9 if cjk else 20
                if cps > lim:
                    warns.append(f"{s['id']}: tốc độ đọc {cps:.0f} CPS > {lim} — rút gọn câu"); stats["cps_high"] += 1
            if EM_DASH in block:
                fails.append(f"{s['id']}: có dấu '—' (cấm trong phụ đề tiếng Việt)")
            if "[CẦN XÁC MINH]" in block:
                warns.append(f"{s['id']}: còn cờ [CẦN XÁC MINH]")
        if dur < 0.8:
            warns.append(f"{s['id']}: hiện {dur:.2f}s < 0.8s (chớp)"); stats["short"] += 1
        if dur > 7.0:
            warns.append(f"{s['id']}: hiện {dur:.1f}s > 7s"); stats["long"] += 1
        if i and s["start"] < segs[i - 1]["end"] - 1e-3:
            fails.append(f"{s['id']}: chồng lấn phụ đề trước ({segs[i-1]['end']:.2f} > {s['start']:.2f})")
        if mode != "source_only" and tgt and src and tgt != src and s.get("translated_text", "").strip() == s.get("source_text", "").strip() and re.search(r"\w{3,}", s.get("source_text", "")):
            fails.append(f"{s['id']}: CHƯA DỊCH")
    not_proof = [s["id"] for s in segs if s.get("low_confidence_words") and not s.get("proofread")]
    if not_proof:
        warns.append(f"{len(not_proof)} phụ đề có từ độ tin cậy thấp chưa qua proofread: {', '.join(not_proof[:12])}")
    if not any(s.get("reflowed") for s in segs):
        warns.append("Chưa chạy reflow (agent ngắt lại câu) — ranh giới hiện là của thuật toán.")
    print(f"QA phụ đề — {stats['n']} phụ đề, chế độ {mode}, {src}→{tgt}")
    for f in fails[:60]:
        print("✗ FAIL", f)
    for w in warns[:80]:
        print("! WARN", w)
    print(f"\n{len(fails)} FAIL, {len(warns)} WARN" + (" — sửa FAIL trước khi xuất bản." if fails else " — đạt điều kiện xuất; xem preview để kiểm tra bằng mắt."))
    if a.json:
        json.dump({"fails": fails, "warns": warns, "stats": stats}, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 2 if fails else 0


# -------------------------------------------------------------------------------- preview
def find_ffmpeg_with_ass():
    for c in ["/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg", shutil.which("ffmpeg") or "", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
        if c and os.path.isfile(c):
            r = subprocess.run([c, "-hide_banner", "-filters"], capture_output=True, text=True)
            if re.search(r"\bass\b", r.stdout):
                return c
    return None


def cmd_preview(a):
    from ass_generator import generate_ass
    from PIL import Image, ImageDraw
    proj = load_project(a.project); segs = proj["segments"]; video = proj["video"]["source_path"]
    ff = find_ffmpeg_with_ass()
    if not ff:
        print("❌ Không có ffmpeg hỗ trợ libass (filter 'ass'). macOS: brew install ffmpeg-full"); return 1
    tmp = tempfile.mkdtemp(prefix="subprev_"); ass = os.path.join(tmp, "p.ass"); generate_ass(proj, ass)
    fonts = os.path.join(SHARED_MEDIA, "..", "fonts")
    esc = lambda p: p.replace("\\", "/").replace(":", "\\:")
    if a.ids:
        pick = [s for s in segs if s["id"] in a.ids.split(",")]
    else:   # ưu tiên phụ đề dài nhất (khó nhất) + rải đều
        n = min(a.frames, len(segs)); longest = sorted(segs, key=lambda s: -len(" ".join(displayed(s, proj['style'].get('mode')))))[: n // 2]
        even = [segs[round(k * (len(segs) - 1) / max(1, n - 1))] for k in range(n)]
        pick = sorted({s["id"]: s for s in longest + even}.values(), key=lambda s: s["start"])[:n]
    shots = []
    for k, s in enumerate(pick):
        t = (s["start"] + s["end"]) / 2; out = os.path.join(tmp, f"{k:02d}.jpg")
        r = subprocess.run([ff, "-v", "error", "-y", "-ss", f"{t:.3f}", "-copyts", "-i", video, "-vf", f"ass='{esc(ass)}':fontsdir='{esc(fonts)}',scale=960:-2",
                            "-frames:v", "1", out], capture_output=True, text=True)
        if r.returncode == 0 and os.path.isfile(out):
            shots.append((s, out))
    if not shots:
        print("❌ Không chụp được khung hình nào."); return 1
    ims = [Image.open(p) for _, p in shots]; w, h = ims[0].size; cols = 2; rows = -(-len(ims) // cols)
    sheet = Image.new("RGB", (cols * w, rows * (h + 22)), "#111"); d = ImageDraw.Draw(sheet)
    for k, ((s, _), im) in enumerate(zip(shots, ims)):
        x, y = (k % cols) * w, (k // cols) * (h + 22); sheet.paste(im, (x, y)); d.text((x + 6, y + h + 4), f"{s['id']}  {s['start']:.1f}s", fill="#ddd")
    out = a.output or os.path.join(os.path.dirname(os.path.abspath(a.project)), "preview_grid.jpg")
    sheet.save(out, quality=88); shutil.rmtree(tmp, ignore_errors=True)
    print(f"🖼  {len(shots)} khung hình: {out} — MỞ ẢNH để kiểm tra font, dấu tiếng Việt, ngắt dòng, vị trí, độ tương phản.")
    return 0


# ---------------------------------------------------------------------------- export-subs
def cmd_export_subs(a):
    from ass_generator import generate_ass, generate_srt
    proj = load_project(a.project); os.makedirs(a.output_dir, exist_ok=True)
    base = os.path.join(a.output_dir, a.name or os.path.splitext(proj["video"].get("filename", "video"))[0])
    generate_srt(proj, base + ".srt"); generate_ass(proj, base + ".ass")
    srt = open(base + ".srt", encoding="utf-8").read()
    open(base + ".vtt", "w", encoding="utf-8").write("WEBVTT\n\n" + re.sub(r"(\d\d:\d\d:\d\d),(\d\d\d)", r"\1.\2", srt))
    print(f"✅ {base}.srt | .ass | .vtt")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("init"); q.add_argument("--meta", required=True); q.add_argument("--segments", required=True); q.add_argument("--process-dir", required=True)
    q.add_argument("--source-lang"); q.add_argument("--target-lang"); q.add_argument("--mode", choices=["bilingual", "monolingual", "source_only"])
    q.add_argument("--preset", default="modern_bottom"); q.add_argument("--glossary", help="thuật ngữ, cách nhau bằng dấu phẩy")
    q = sp.add_parser("export"); q.add_argument("--project", required=True); q.add_argument("--task", required=True, choices=["reflow", "proofread", "translate"]); q.add_argument("--batch", type=int, default=40)
    q = sp.add_parser("apply"); q.add_argument("--input", required=True); q.add_argument("--project")
    q = sp.add_parser("qa"); q.add_argument("--project", required=True); q.add_argument("--json")
    q = sp.add_parser("preview"); q.add_argument("--project", required=True); q.add_argument("--frames", type=int, default=6); q.add_argument("--ids"); q.add_argument("--output")
    q = sp.add_parser("export-subs"); q.add_argument("--project", required=True); q.add_argument("--output-dir", required=True); q.add_argument("--name")
    a = p.parse_args()
    return {"init": cmd_init, "export": cmd_export, "apply": cmd_apply, "qa": cmd_qa, "preview": cmd_preview, "export-subs": cmd_export_subs}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())

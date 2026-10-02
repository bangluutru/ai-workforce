#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dub_workbench.py — Vòng làm việc lồng tiếng: AGENT viết lời đọc vừa khung, script đo và báo lỗi.

  init     dubbing_project.json từ video + phụ đề (project.json của phu-de, .srt, .json)
  export   lô "adapt" cho agent: mỗi câu kèm khung thời gian (giây) và số ký tự tối đa đọc kịp
  apply    nạp lời đọc agent đã viết (trường dub_text) — có cảnh báo câu quá dài
  report   đọc dub_report.json sau khi render: câu TRÀN khung, câu ĐỌC SAI (Whisper nghe lại), câu phải đọc nhanh
           → exit 2 nếu còn câu tràn/đọc sai (agent sửa dub_text rồi render lại; câu không đổi được dùng lại cache)

Vòng chuẩn: init → export → (agent điền output) → apply → dubbing_pipeline.py → report → sửa → render lại.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CPS = {"vi": 16.0, "en": 15.0, "ja": 8.0}      # ký tự/giây đọc tự nhiên (đo trên VieNeu: 15–20, không tính dấu cách)
GAP = 0.12

INSTRUCTIONS = [
    "Nhiệm vụ: viết LỜI ĐỌC lồng tiếng ({lang}) cho từng câu — để NGHE, không phải để đọc chữ.",
    "Mỗi câu ≤ max_chars ký tự (= khung thời gian × tốc độ nói tự nhiên). Dài hơn → giọng phải đọc nhanh hoặc tràn sang câu sau. Ngắn hơn nhiều cũng được (khoảng lặng tự nhiên).",
    "Viết theo cách ĐỌC: từ viết tắt/thuật ngữ nước ngoài đọc thế nào viết thế ấy hoặc thay bằng từ Việt (AI → 'trí tuệ nhân tạo' hoặc 'ây-ai'; %, km, USD viết bằng chữ khi dễ đọc sai); tên riêng giữ nguyên.",
    "Câu nói tự nhiên, ngắn, đúng ngữ khí người nói (hào hứng, nghiêm túc...); xưng hô nhất quán; không '—', không ngoặc, không ký hiệu.",
    "Giữ đúng ý và thông tin của câu gốc (source). Điền \"output\": {{\"<id>\": \"lời đọc\"}} cho TẤT CẢ id.",
]


def load(p):
    return json.load(open(p, encoding="utf-8"))


def save(d, p):
    tmp = p + ".tmp"; json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2); os.replace(tmp, p)


def cmd_init(a):
    from dubbing_project_manager import create_dubbing_project
    settings = {"lang": a.lang, "gender": a.gender}
    if a.voice:
        settings["voice"] = a.voice
    pf, proj = create_dubbing_project(a.video, a.subtitles, a.process_dir, audio_settings=settings)
    print(f"✅ {pf} | {len(proj['segments'])} câu | {a.lang} | giọng {settings.get('voice', a.gender)}")
    return 0


def cmd_export(a):
    proj = load(a.project); segs = sorted(proj["segments"], key=lambda s: float(s["start"]))
    lang = proj.get("audio_settings", {}).get("lang", "vi"); cps = CPS.get(lang, 14.0)
    dur = float(proj.get("video", {}).get("duration") or segs[-1]["end"] + 2)
    out_dir = os.path.join(os.path.dirname(os.path.abspath(a.project)), "tasks"); os.makedirs(out_dir, exist_ok=True)
    for f in glob.glob(os.path.join(out_dir, "adapt_*.json")):
        os.remove(f)
    batches = [segs[i:i + a.batch] for i in range(0, len(segs), a.batch)]
    for bi, b in enumerate(batches, 1):
        items = []
        for s in b:
            k = segs.index(s); nxt = segs[k + 1]["start"] if k + 1 < len(segs) else dur
            slot = max(0.3, float(nxt) - float(s["start"]) - GAP)
            items.append({"id": s["id"], "source": s.get("source_text", ""), "text": s.get("dub_text") or s.get("target_text") or s.get("text", ""),
                          "slot_sec": round(slot, 2), "max_chars": int(slot * cps)})
        task = {"task": "adapt", "batch": bi, "of": len(batches), "project": os.path.abspath(a.project),
                "instructions": [t.format(lang=lang) for t in INSTRUCTIONS], "items": items, "output": {}}
        save(task, os.path.join(out_dir, f"adapt_{bi:02d}.json"))
    print(f"📤 {len(batches)} lô adapt tại {out_dir}/adapt_NN.json — điền \"output\" rồi: apply --input <file>")
    return 0


def cmd_apply(a):
    task = load(a.input); pf = a.project or task["project"]; proj = load(pf)
    out = task.get("output") or {}
    by = {str(s["id"]): s for s in proj["segments"]}
    miss = [it["id"] for it in task["items"] if not str(out.get(str(it["id"]), "")).strip()]
    if miss:
        print(f"❌ Thiếu lời đọc cho {len(miss)} id: {miss[:10]}"); return 1
    long = []
    for it in task["items"]:
        t = str(out[str(it["id"])]).strip().replace("—", ", ")
        by[str(it["id"])]["dub_text"] = t
        n = len(t.replace(" ", ""))
        if n > it["max_chars"] * 1.1:
            long.append(f"{it['id']}({n}>{it['max_chars']})")
    save(proj, pf)
    print(f"✅ adapt lô {task['batch']}: {len(task['items'])} lời đọc" + (f" | ⚠️ dài quá khung: {', '.join(long)}" if long else ""))
    return 0


def cmd_report(a):
    rp = os.path.join(a.process_dir, "dub_report.json")
    if not os.path.isfile(rp):
        print(f"❌ Chưa có {rp} — chạy dubbing_pipeline.py trước"); return 1
    r = load(rp)
    print(f"Lồng tiếng: {r['synthesized']}/{r['lines']} câu · {r.get('engine')} · nhịp nền {r['base_tempo']}× · tối đa {r['max_tempo']}× · "
          f"{r['integrated_lufs']} LUFS · đỉnh {r['true_peak_dbfs']} dBFS")
    fails = 0
    for it in r["items"]:
        msgs = []
        if it["overflow"] > 0.05:
            msgs.append(f"TRÀN {it['overflow']:.2f}s (khung {it['slot']}s, đọc {it['dur']}s) → rút gọn lời đọc"); fails += 1
        if (it.get("cer") or 0) > 0.08:
            msgs.append(f"ĐỌC SAI {it['cer']:.0%} — Whisper nghe: \"{it.get('heard')}\" → viết lại cụm khó đọc"); fails += 1
        if it["tempo"] > 1.15 and it["overflow"] <= 0.05:
            msgs.append(f"đọc nhanh {it['tempo']}× → nên rút gọn cho tự nhiên")
        if msgs:
            print(f"  {it['start']:7.2f}s | {it['text']}\n           " + "\n           ".join(msgs))
    if r.get("failed"):
        print(f"✗ {len(r['failed'])} câu không tổng hợp được: {r['failed'][:5]}"); fails += len(r["failed"])
    lufs = r.get("integrated_lufs")
    if lufs is not None and abs(lufs + 16) > 1.5:
        print(f"! Độ lớn {lufs} LUFS lệch chuẩn −16 LUFS")
    print("\n" + (f"{fails} lỗi cần sửa (dub_text) rồi render lại." if fails else "✅ Mọi câu vừa khung và đọc đúng."))
    return 2 if fails else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    q = sp.add_parser("init"); q.add_argument("--video", required=True); q.add_argument("--subtitles", required=True); q.add_argument("--process-dir", required=True)
    q.add_argument("--lang", default="vi", choices=["vi", "en", "ja"]); q.add_argument("--gender", default="female", choices=["female", "male"]); q.add_argument("--voice")
    q = sp.add_parser("export"); q.add_argument("--project", required=True); q.add_argument("--batch", type=int, default=40)
    q = sp.add_parser("apply"); q.add_argument("--input", required=True); q.add_argument("--project")
    q = sp.add_parser("report"); q.add_argument("--process-dir", required=True)
    a = p.parse_args()
    return {"init": cmd_init, "export": cmd_export, "apply": cmd_apply, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())

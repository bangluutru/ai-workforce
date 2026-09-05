#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_skill.py — Bộ công cụ Kiểm định & Cấp Chứng chỉ Kỹ năng AIWF (v1.0)
Theo tiêu chuẩn kiến trúc Rule R4: .agents/rules/R4-skill-standard-v1.md

Cách sử dụng:
    python3 scripts/audit_skill.py .agents/skills/tu-van-phap-luat
    python3 scripts/audit_skill.py --all
    python3 scripts/audit_skill.py --scan-new
    python3 scripts/audit_skill.py --all --certify
"""

import sys
import os
import re
import json
import hashlib
import py_compile
import subprocess
import argparse
from pathlib import Path

# Màu sắc hiển thị Terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

FORBIDDEN_API_PATTERNS = [
    r"genai\.configure\(api_key=",
    r"openai\.api_key\s*=",
    r"anthropic\.Anthropic\(",
    r"os\.environ\[[\"']GEMINI_API_KEY[\"']\]",
    r"os\.environ\[[\"']OPENAI_API_KEY[\"']\]",
    r"https://api\.openai\.com",
    r"https://api\.anthropic\.com",
    r"https://generativelanguage\.googleapis\.com",
]

def calculate_folder_hash(folder_path):
    """Tính SHA256 tổng hợp của folder skill để theo dõi thay đổi."""
    sha = hashlib.sha256()
    for root, _, files in sorted(os.walk(folder_path)):
        for f in sorted(files):
            if f.endswith(('.md', '.py', '.js', '.json', '.sh')):
                p = os.path.join(root, f)
                try:
                    with open(p, 'rb') as fp:
                        sha.update(fp.read())
                except Exception:
                    pass
    return sha.hexdigest()[:12]

def extract_frontmatter(content):
    """Bóc tách YAML frontmatter trong SKILL.md."""
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    yaml_text = parts[1]
    data = {}
    for line in yaml_text.strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data

def audit_skill(skill_dir, quiet=False):
    skill_path = Path(skill_dir)
    if not skill_path.is_absolute():
        repo_root = Path(__file__).resolve().parent.parent
        alt_path = repo_root / ".agents" / "skills" / skill_dir
        if alt_path.exists() and alt_path.is_dir():
            skill_path = alt_path
        else:
            skill_path = skill_path.resolve()
    else:
        skill_path = skill_path.resolve()

    empty_scores = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}
    if not skill_path.exists() or not skill_path.is_dir():
        return {"name": skill_path.name, "score": 0, "scores": empty_scores, "status": "FAIL", "errors": [f"Thư mục không tồn tại: {skill_dir}"], "warnings": []}

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {"name": skill_path.name, "score": 0, "scores": empty_scores, "status": "FAIL", "errors": ["Thiếu file SKILL.md bắt buộc"], "warnings": []}

    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    errors = []
    warnings = []
    scores = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}

    # =========================================================================
    # LỚP 1: METADATA & TRIGGER CONTRACT (20đ - Chuẩn Gemini 3.8)
    # =========================================================================
    fm = extract_frontmatter(content)
    if fm:
        if fm.get("name"):
            scores["L1"] += 4
        else:
            errors.append("L1 [FAIL]: Frontmatter thiếu trường 'name'")

        desc = fm.get("description", "")
        if desc:
            scores["L1"] += 2
            # Kiểm tra xem có ranh giới phủ định (KHÔNG dùng cho...) không
            if any(w in desc.lower() for w in ["không dùng", "không", "tránh", "cấm", "chuyển sang"]):
                scores["L1"] += 2
            else:
                warnings.append("L1 [WARN]: 'description' nên có phạm vi phủ định (ví dụ: 'KHÔNG dùng cho...') để router phân luồng chuẩn")
        else:
            errors.append("L1 [FAIL]: Frontmatter thiếu trường 'description'")

        if fm.get("trigger"):
            scores["L1"] += 4
        else:
            warnings.append("L1 [WARN]: Frontmatter thiếu trường 'trigger' nhanh")

        # Các trường nâng cao chuẩn Antigravity 2.0 & Gemini 3.8
        if fm.get("argument-hint"):
            scores["L1"] += 3
        else:
            warnings.append("L1 [WARN]: Nên bổ sung 'argument-hint' để hỗ trợ autocomplete trên UI Antigravity")

        if fm.get("allowed-tools"):
            scores["L1"] += 3
        else:
            warnings.append("L1 [WARN]: Nên bổ sung 'allowed-tools' để cấp quyền công cụ tự chủ không pop-up")

        if fm.get("effort"):
            scores["L1"] += 2
        else:
            warnings.append("L1 [WARN]: Nên bổ sung 'effort' (low|medium|high) định hình ngân sách tư duy Gemini 3.8")
    else:
        errors.append("L1 [FAIL]: SKILL.md không có YAML frontmatter (---) hợp lệ")

    # =========================================================================
    # LỚP 2: INTAKE & ANTI-REPO BLOAT (20đ)
    # =========================================================================
    has_output_dir = "<output_dir>" in content or "output_dir" in content or "Downloads" in content
    has_anti_bloat = "Anti-Repo Bloat" in content or "BẢO VỆ CODEBASE" in content or "codebase" in content.lower()
    has_intake = any(w in content for w in ["5 Trục", "ĐỐI TƯỢNG", "Bảng 3 Lựa chọn", "HỎI TRƯỚC", "Path Resolution", "Bước 0", "Intake"])

    if has_output_dir:
        scores["L2"] += 8
    else:
        errors.append("L2 [FAIL]: Thiếu quy chuẩn <output_dir> (mặc định ~/Downloads/). Skill có nguy cơ lưu file bừa bãi vào codebase.")

    if has_anti_bloat:
        scores["L2"] += 6
    else:
        warnings.append("L2 [WARN]: Nên có khối chú thích cảnh báo QUY TẮC BẢO VỆ CODEBASE (Anti-Repo Bloat)")

    if has_intake:
        scores["L2"] += 6
    else:
        warnings.append("L2 [WARN]: Thiếu hệ thống phân luồng/tọa độ đầu vào (Intake/Coordinates)")

    # =========================================================================
    # LỚP 3: ZERO EXTERNAL API & AUTONOMOUS ENGINE (20đ)
    # =========================================================================
    external_api_found = False
    # Quét trong SKILL.md và toàn bộ scripts
    for root, _, files in os.walk(skill_path):
        for f in files:
            if f.endswith(('.py', '.js', '.md', '.sh')):
                p = os.path.join(root, f)
                try:
                    f_text = Path(p).read_text(encoding="utf-8", errors="ignore")
                    for pat in FORBIDDEN_API_PATTERNS:
                        if re.search(pat, f_text):
                            external_api_found = True
                            errors.append(f"L3 [CRITICAL FAIL]: Phát hiện lời gọi External API cấm tại {f} (pattern: {pat})")
                            break
                except Exception:
                    pass

    if not external_api_found:
        scores["L3"] += 10
    else:
        scores["L3"] = 0

    has_zero_api_mention = any(w in content for w in ["ZERO EXTERNAL API", "Zero External API", "không gọi REST API", "không yêu cầu API key"])
    has_autonomous = any(w in content for w in ["Autonomous", "tự chạy liên tục", "không tự dừng", "Checkpoint", "PDCA", "Zero-Loss"])
    has_live_engine = any(w in content for w in ["Live Formulas", "live formulas", "công thức sống", "Zero-Loss", "Evidence Verifier", "PDCA Cascade", "Live formulas"])

    if has_zero_api_mention:
        scores["L3"] += 3
    if has_autonomous:
        scores["L3"] += 3
    if has_live_engine:
        scores["L3"] += 4

    # =========================================================================
    # LỚP 4: MODULAR CODE & STORAGE (20đ)
    # =========================================================================
    # Kiểm tra cấu trúc thư mục con
    subdirs = [d.name for d in skill_path.iterdir() if d.is_dir()]
    if any(d in subdirs for d in ["resources", "standards", "scripts", "templates", "examples"]):
        scores["L4"] += 8
    else:
        warnings.append("L4 [WARN]: Skill nên có thư mục module hóa (resources/, standards/, scripts/, templates/)")

    # Kiểm tra cú pháp script Python
    py_files = list(skill_path.glob("**/*.py"))
    py_ok = True
    for pyf in py_files:
        try:
            py_compile.compile(str(pyf), doraise=True)
        except py_compile.PyCompileError as e:
            py_ok = False
            errors.append(f"L4 [FAIL]: Lỗi cú pháp Python tại {pyf.name}: {e}")

    # Kiểm tra cú pháp script Node.js (nếu có node)
    js_files = list(skill_path.glob("**/*.js"))
    js_ok = True
    for jsf in js_files:
        try:
            res = subprocess.run(["node", "-c", str(jsf)], capture_output=True, text=True)
            if res.returncode != 0:
                js_ok = False
                errors.append(f"L4 [FAIL]: Lỗi cú pháp JavaScript tại {jsf.name}: {res.stderr.strip()}")
        except FileNotFoundError:
            pass # Không có Node CLI thì bỏ qua

    if py_ok and js_ok:
        scores["L4"] += 12

    # =========================================================================
    # LỚP 5: QUALITY GATE & CLEAN DELIVERY (20đ)
    # =========================================================================
    has_quality_gate = any(w in content for w in ["Quality Gate", "Checklist", "checklist", "Kiểm tra trước khi", "Nguyên tắc Tuân thủ", "<quality_gate>"])
    has_confidence_flag = any(w in content for w in ["Confidence Flagging", "CẦN XÁC MINH", "needs_verification", "gắn cờ", "trích dẫn NGUYÊN VĂN", "Evidence Verifier", "verbatim_quote"])
    has_anti_footprint = any(w in content for w in ["Khử dấu vết AI", "KHỬ DẤU VẾT AI", "dấu vết AI", "em dash", "Oxford comma", "Anti-AI"])
    has_clean_chat = any(w in content for w in ["khung chat chỉ", "Khung chat chỉ", "link trỏ đến", "báo cáo chính thức", "file riêng", "Clean Delivery", "<delivery_protocol>"])

    if has_quality_gate:
        scores["L5"] += 6
    else:
        warnings.append("L5 [WARN]: SKILL.md nên có checklist Quality Gate tự thẩm định trước khi hoàn tất")

    if has_confidence_flag:
        scores["L5"] += 4
    else:
        warnings.append("L5 [WARN]: Nên có quy định Confidence Flagging (gắn cờ [CẦN XÁC MINH] khi OCR hoặc suy luận mờ)")

    if has_anti_footprint:
        scores["L5"] += 5
    else:
        warnings.append("L5 [WARN]: Nên có quy định Khử dấu vết AI (cấm em dash, cấm Oxford comma)")

    if has_clean_chat:
        scores["L5"] += 5
    else:
        warnings.append("L5 [WARN]: Nên có quy định Giao thức Bàn giao Sạch (khung chat chỉ tóm tắt ngắn + link)")

    total_score = sum(scores.values())
    status = "PASS" if total_score >= 85 and len(errors) == 0 else "FAIL"

    return {
        "name": skill_path.name,
        "path": str(skill_path),
        "hash": calculate_folder_hash(skill_path),
        "score": total_score,
        "scores": scores,
        "status": status,
        "errors": errors,
        "warnings": warnings
    }

def print_report(res):
    status_color = GREEN if res["status"] == "PASS" else RED
    print(f"\n{BOLD}═══════════════════════════════════════════════════════════════════{RESET}")
    print(f" {BOLD}SKILL AUDIT REPORT:{RESET} {BLUE}{res['name']}{RESET}  [{status_color}{BOLD}{res['status']}{RESET} - {BOLD}{res['score']}/100đ{RESET}]")
    print(f"{BOLD}───────────────────────────────────────────────────────────────────{RESET}")
    print(f" • Tầng 1: Metadata Contract:      {res['scores']['L1']}/20đ")
    print(f" • Tầng 2: Intake & Anti-Bloat:     {res['scores']['L2']}/20đ")
    print(f" • Tầng 3: Zero-API & Autonomous:   {res['scores']['L3']}/20đ")
    print(f" • Tầng 4: Modular Code & Storage:  {res['scores']['L4']}/20đ")
    print(f" • Tầng 5: Quality Gate & Delivery: {res['scores']['L5']}/20đ")

    if res["errors"]:
        print(f"\n {RED}{BOLD}CÁC LỖI BẮT BUỘC SỬA (HARD STOP):{RESET}")
        for err in res["errors"]:
            print(f"   ❌ {err}")

    if res["warnings"]:
        print(f"\n {YELLOW}{BOLD}CẢNH BÁO TỐI ƯU HÓA (WARNINGS):{RESET}")
        for warn in res["warnings"]:
            print(f"   ⚠️  {warn}")

    if res["status"] == "PASS":
        print(f"\n {GREEN}✅ Kỹ năng đạt chuẩn AIWF Standard v1.0. Sẵn sàng vận hành.{RESET}")
    else:
        print(f"\n {RED}⛔ Kỹ năng CHƯA đạt chuẩn AIWF Standard v1.0. Cần khắc phục các lỗi trên.{RESET}")
    print(f"{BOLD}═══════════════════════════════════════════════════════════════════{RESET}")

def main():
    parser = argparse.ArgumentParser(description="Bộ kiểm định kỹ năng AIWF Standard v1.0")
    parser.add_argument("skill_target", nargs="?", default=None, help="Đường dẫn folder skill cần kiểm định")
    parser.add_argument("--all", action="store_true", help="Kiểm định toàn bộ kỹ năng trong .agents/skills/")
    parser.add_argument("--scan-new", action="store_true", help="Tự động phát hiện skill mới chưa có chứng nhận")
    parser.add_argument("--certify", action="store_true", help="Đóng dấu chứng nhận vào .certified.json nếu đạt chuẩn")
    parser.add_argument("--quiet", action="store_true", help="Chế độ chạy im lặng cho CI/CD")
    args = parser.parse_args()

    workspace = Path(__file__).parent.parent
    skills_root = workspace / ".agents" / "skills"
    certified_file = skills_root / ".certified.json"

    certified_data = {}
    if certified_file.exists():
        try:
            certified_data = json.loads(certified_file.read_text(encoding="utf-8"))
        except Exception:
            certified_data = {}

    targets = []
    if args.skill_target:
        p = Path(args.skill_target)
        if not p.is_absolute():
            if (skills_root / p).exists():
                p = skills_root / p
            else:
                p = workspace / p
        targets.append(p)
    elif args.scan_new:
        for d in sorted(skills_root.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                current_hash = calculate_folder_hash(d)
                if d.name not in certified_data or certified_data[d.name].get("hash") != current_hash:
                    targets.append(d)
        if not targets:
            if not args.quiet:
                print(f"{GREEN}✅ Toàn bộ kỹ năng đã có chứng chỉ hợp lệ. Không có skill mới cần kiểm định.{RESET}")
            sys.exit(0)
    elif args.all:
        for d in sorted(skills_root.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                targets.append(d)
    else:
        parser.print_help()
        sys.exit(1)

    all_passed = True
    new_certifications = {}

    for t in targets:
        report = audit_skill(t, quiet=args.quiet)
        if not args.quiet:
            print_report(report)
        if report["status"] != "PASS":
            all_passed = False
        else:
            new_certifications[report["name"]] = {
                "hash": report["hash"],
                "score": report["score"],
                "certified_at": "2026-09-03"
            }

    if args.certify and all_passed:
        certified_data.update(new_certifications)
        certified_file.write_text(json.dumps(certified_data, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.quiet:
            print(f"\n{GREEN}{BOLD}🎖️ Đã cấp chứng chỉ thành công cho {len(new_certifications)} kỹ năng vào {certified_file.name}!{RESET}")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

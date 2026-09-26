#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_skill.py — Bộ công cụ Kiểm định Cấu trúc Kỹ năng AIWF (Structure & Contract Validator)
Tuân thủ:
- Hợp đồng Metadata: docs/harness/METADATA_CONTRACT.md
- Tiêu chuẩn Kỹ năng: .agents/rules/R4-skill-standard-v1.md
- Quy tắc Code Quality: .agents/rules/R2-code-quality.md

LƯU Ý QUAN TRỌNG:
Công cụ này chỉ thực hiện STRUCTURAL VALIDATION (kiểm định cấu trúc tệp, hợp đồng metadata,
cú pháp Python/JS và quy tắc an toàn). Công cụ này KHÔNG cấp chứng nhận chất lượng đầu ra
(OUTPUT QUALITY VALIDATION), vì chất lượng đầu ra đòi hỏi phải chạy kiểm thử thực tế trên sản phẩm.

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
from datetime import datetime
from pathlib import Path

# Thử nạp PyYAML, nếu không có thì dùng parser dòng an toàn
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Màu sắc hiển thị Terminal
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Mẫu phát hiện gọi External LLM API cấm (Rule R4 / Zero External LLM API)
FORBIDDEN_LLM_PATTERNS = [
    r"genai\.configure\(api_key=",
    r"openai\.api_key\s*=",
    r"anthropic\.Anthropic\(",
    r"os\.environ\[[\"']GEMINI_API_KEY[\"']\]",
    r"os\.environ\[[\"']OPENAI_API_KEY[\"']\]",
    r"https://api\.openai\.com",
    r"https://api\.anthropic\.com",
    r"https://generativelanguage\.googleapis\.com",
]

# Các trường metadata bị loại bỏ hoặc không có consumer thực tế theo METADATA_CONTRACT.md
DEPRECATED_METADATA_FIELDS = [
    "allowed-tools",
    "effort",
    "interaction-mode",
    "argument-hint",
    "trigger_keywords",
]

def calculate_folder_hash(folder_path):
    """Tính SHA256 tổng hợp của folder skill để theo dõi thay đổi."""
    sha = hashlib.sha256()
    for root, _, files in sorted(os.walk(folder_path)):
        for f in sorted(files):
            if f.endswith(('.md', '.py', '.js', '.json', '.sh', '.html', '.css')):
                p = os.path.join(root, f)
                try:
                    with open(p, 'rb') as fp:
                        sha.update(fp.read())
                except Exception:
                    pass
    return sha.hexdigest()[:12]

def extract_frontmatter(content):
    """Bóc tách YAML frontmatter trong SKILL.md an toàn."""
    if not content.startswith("---"):
        return None
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None
    yaml_text = parts[1]
    
    if HAS_YAML:
        try:
            parsed = yaml.safe_load(yaml_text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    # Fallback parser thủ công nếu không có PyYAML hoặc lỗi cú pháp YAML
    data = {}
    current_key = None
    for line in yaml_text.strip().split("\n"):
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue
        if ":" in line and not line.startswith(" ") and not line.startswith("\t"):
            k, v = line.split(":", 1)
            current_key = k.strip()
            val = v.strip().strip("'\"")
            if val in [">", ">-", "|", "|-"]:
                data[current_key] = ""
            else:
                data[current_key] = val
        elif current_key and (line.startswith(" ") or line.startswith("\t")):
            sub_val = line.strip().strip("'\"")
            if data[current_key]:
                data[current_key] += " " + sub_val
            else:
                data[current_key] = sub_val
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
        return {
            "name": skill_path.name,
            "score": 0,
            "scores": empty_scores,
            "status": "FAIL",
            "errors": [f"Thư mục không tồn tại: {skill_dir}"],
            "warnings": [],
            "is_skill": False
        }

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        # Thư mục phụ trợ (như _shared) không phải skill -> bỏ qua mà không đánh fail hệ thống
        return {
            "name": skill_path.name,
            "score": 0,
            "scores": empty_scores,
            "status": "SKIPPED",
            "errors": [],
            "warnings": [f"Bỏ qua thư mục '{skill_path.name}' do không chứa file SKILL.md"],
            "is_skill": False
        }

    content = skill_md.read_text(encoding="utf-8", errors="ignore")
    errors = []
    warnings = []
    scores = {"L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}

    # =========================================================================
    # LỚP 1: METADATA CONTRACT (25đ - Theo METADATA_CONTRACT.md)
    # =========================================================================
    fm = extract_frontmatter(content)
    if fm:
        skill_name = fm.get("name", "")
        if skill_name:
            if re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', str(skill_name)):
                scores["L1"] += 5
            else:
                errors.append(f"L1 [FAIL]: 'name' ({skill_name}) phải dùng kebab-case chữ thường không dấu (vd: 'video-studio', 'ejv-translate').")
        else:
            errors.append("L1 [FAIL]: Frontmatter thiếu trường 'name' bắt buộc")

        # Kiểm tra display-name (bắt buộc tiếng Việt có dấu hoặc tiếng Anh chuẩn)
        display_name = fm.get("display-name") or fm.get("display_name")
        if display_name:
            vietnamese_diacritics = set("àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ")
            has_diacritics = any(c in vietnamese_diacritics for c in str(display_name))
            unaccented_vi_words = {"phu", "de", "boc", "tach", "thiet", "ke", "xu", "ly", "van", "phong", "tu", "van", "phap", "luat", "viet", "bai", "bao", "cao", "toan", "tao", "hoat", "hinh"}
            words_lower = set(re.findall(r'[a-zA-Z]+', str(display_name).lower()))
            if not has_diacritics and words_lower.intersection(unaccented_vi_words):
                errors.append(f"L1 [FAIL]: 'display-name' ({display_name}) vi phạm quy chuẩn! Phải là tiếng Việt có dấu (vd: 'Tạo Phụ Đề', 'Studio Video').")
            else:
                scores["L1"] += 5
        else:
            errors.append("L1 [FAIL]: Frontmatter thiếu trường 'display-name' bắt buộc theo METADATA_CONTRACT.md")

        # Kiểm tra description: USE WHEN và DO NOT USE WHEN
        desc = fm.get("description", "")
        if desc and len(str(desc).strip()) >= 30:
            scores["L1"] += 5
            desc_str = str(desc)
            has_use_when = "USE WHEN" in desc_str or "DÙNG KHI" in desc_str or "Kích hoạt khi" in desc_str
            has_do_not_use = "DO NOT USE" in desc_str or "KHÔNG DÙNG" in desc_str or "KHÔNG dùng" in desc_str or "Tránh dùng" in desc_str
            
            if has_use_when:
                scores["L1"] += 5
            else:
                warnings.append("L1 [WARN]: 'description' nên có phạm vi 'USE WHEN:' cụ thể để định tuyến chính xác.")
                
            if has_do_not_use:
                scores["L1"] += 5
            else:
                warnings.append("L1 [WARN]: 'description' bắt buộc có ranh giới phủ định 'DO NOT USE WHEN:' để tránh tranh chấp định tuyến.")
        else:
            errors.append("L1 [FAIL]: Frontmatter thiếu trường 'description' hoặc mô tả quá ngắn (< 30 ký tự)")

        # Cảnh báo các trường lỗi thời
        for dep in DEPRECATED_METADATA_FIELDS:
            if dep in fm:
                warnings.append(f"L1 [DEPRECATION]: Trường '{dep}' trong frontmatter không có consumer native. Nên gỡ bỏ hoặc đưa vào thân markdown.")

        # Cảnh báo context: fork
        if fm.get("context") == "fork":
            warnings.append("L1 [DEPRECATION]: 'context: fork' không tự động tạo subagent trong Antigravity. Nên điều phối qua prompt/tools.")

    else:
        errors.append("L1 [FAIL]: SKILL.md không có YAML frontmatter (---) hợp lệ")

    # =========================================================================
    # LỚP 2: INTAKE & CODEBASE PROTECTION (20đ)
    # =========================================================================
    has_output_dir = "<output_dir>" in content or "output_dir" in content or "Downloads" in content
    has_anti_bloat = "Anti-Repo Bloat" in content or "BẢO VỆ CODEBASE" in content or "codebase" in content.lower()
    has_intake = any(w in content for w in ["Intake", "Tọa độ", "Bước 0", "Tiếp nhận", "Menu", "5 Trục"])

    if has_output_dir:
        scores["L2"] += 10
    else:
        errors.append("L2 [FAIL]: Thiếu quy chuẩn <output_dir> (mặc định ~/Downloads/). Nguy cơ lưu file bừa bãi vào codebase.")

    if has_anti_bloat:
        scores["L2"] += 5
    else:
        warnings.append("L2 [WARN]: Nên có khối chú thích cảnh báo BẢO VỆ CODEBASE (Anti-Repo Bloat)")

    if has_intake:
        scores["L2"] += 5
    else:
        warnings.append("L2 [WARN]: Thiếu hướng dẫn tiếp nhận đầu vào (Intake / Input Handling)")

    # =========================================================================
    # LỚP 3: ZERO EXTERNAL LLM API & EXECUTION DISCIPLINE (20đ)
    # =========================================================================
    forbidden_api_found = False
    for root, _, files in os.walk(skill_path):
        for f in files:
            if f.endswith(('.py', '.js', '.md', '.sh')):
                p = os.path.join(root, f)
                try:
                    f_text = Path(p).read_text(encoding="utf-8", errors="ignore")
                    for pat in FORBIDDEN_LLM_PATTERNS:
                        if re.search(pat, f_text):
                            forbidden_api_found = True
                            errors.append(f"L3 [CRITICAL FAIL]: Phát hiện lời gọi External LLM API cấm tại {f} (pattern: {pat})")
                            break
                except Exception:
                    pass

    if not forbidden_api_found:
        scores["L3"] += 10
    else:
        scores["L3"] = 0

    has_zero_llm_mention = any(w in content for w in ["ZERO EXTERNAL API", "Zero External API", "Zero External LLM API", "không gọi REST API", "không yêu cầu API key"])
    has_autonomous = any(w in content for w in ["Autonomous", "tự chạy liên tục", "không tự dừng", "Checkpoint", "PDCA", "Zero-Loss"])

    if has_zero_llm_mention:
        scores["L3"] += 5
    if has_autonomous:
        scores["L3"] += 5

    # =========================================================================
    # LỚP 4: CODE QUALITY & SYNTAX VERIFICATION (20đ)
    # =========================================================================
    py_files = list(skill_path.glob("**/*.py"))
    py_ok = True
    for pyf in py_files:
        try:
            py_compile.compile(str(pyf), doraise=True)
        except py_compile.PyCompileError as e:
            py_ok = False
            errors.append(f"L4 [FAIL]: Lỗi cú pháp Python tại {pyf.name}: {e}")

    js_files = list(skill_path.glob("**/*.js"))
    js_ok = True
    for jsf in js_files:
        try:
            res = subprocess.run(["node", "-c", str(jsf)], capture_output=True, text=True)
            if res.returncode != 0:
                js_ok = False
                errors.append(f"L4 [FAIL]: Lỗi cú pháp JavaScript tại {jsf.name}: {res.stderr.strip()}")
        except FileNotFoundError:
            pass

    if py_ok and js_ok:
        scores["L4"] += 15

    subdirs = [d.name for d in skill_path.iterdir() if d.is_dir()]
    if any(d in subdirs for d in ["resources", "standards", "scripts", "templates", "examples", "ui"]):
        scores["L4"] += 5

    # =========================================================================
    # LỚP 5: QUALITY GATE & DELIVERY PROTOCOL (15đ)
    # =========================================================================
    has_quality_gate = any(w in content for w in ["Quality Gate", "Checklist", "checklist", "Kiểm tra trước khi", "<quality_gate>"])
    has_clean_chat = any(w in content for w in ["khung chat chỉ", "Khung chat chỉ", "link trỏ đến", "báo cáo chính thức", "Clean Delivery", "<delivery_protocol>"])
    has_evidence_rule = any(w in content for w in ["Evidence Verifier", "trích dẫn NGUYÊN VĂN", "Confidence Flagging", "verbatim_quote", "bằng chứng"])

    if has_quality_gate:
        scores["L5"] += 5
    else:
        warnings.append("L5 [WARN]: SKILL.md nên có checklist Quality Gate tự thẩm định trước khi xuất bản")

    if has_clean_chat:
        scores["L5"] += 5
    else:
        warnings.append("L5 [WARN]: Nên có quy định Giao thức Bàn giao Sạch (khung chat chỉ tóm tắt ngắn + đường dẫn file)")

    if has_evidence_rule:
        scores["L5"] += 5

    total_score = sum(scores.values())
    status = "STRUCTURE_VALIDATED" if total_score >= 80 and len(errors) == 0 else "FAIL"

    return {
        "name": skill_path.name,
        "path": str(skill_path),
        "hash": calculate_folder_hash(skill_path),
        "score": total_score,
        "scores": scores,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "is_skill": True
    }

def print_report(res):
    if not res.get("is_skill", True):
        return

    status_color = GREEN if res["status"] == "STRUCTURE_VALIDATED" else RED
    print(f"\n{BOLD}═══════════════════════════════════════════════════════════════════{RESET}")
    print(f" {BOLD}SKILL AUDIT REPORT:{RESET} {BLUE}{res['name']}{RESET}  [{status_color}{BOLD}{res['status']}{RESET} - {BOLD}{res['score']}/100đ{RESET}]")
    print(f"{BOLD}───────────────────────────────────────────────────────────────────{RESET}")
    print(f" • Tầng 1: Metadata Contract:      {res['scores']['L1']}/25đ")
    print(f" • Tầng 2: Intake & Anti-Bloat:     {res['scores']['L2']}/20đ")
    print(f" • Tầng 3: Zero-LLM-API & Engine:   {res['scores']['L3']}/20đ")
    print(f" • Tầng 4: Code Quality & Syntax:   {res['scores']['L4']}/20đ")
    print(f" • Tầng 5: Quality Gate & Delivery: {res['scores']['L5']}/15đ")

    if res["errors"]:
        print(f"\n {RED}{BOLD}CÁC LỖI BẮT BUỘC SỬA (HARD STOP):{RESET}")
        for err in res["errors"]:
            print(f"   ❌ {err}")

    if res["warnings"]:
        print(f"\n {YELLOW}{BOLD}CẢNH BÁO TỐI ƯU HÓA (WARNINGS):{RESET}")
        for warn in res["warnings"]:
            print(f"   ⚠️  {warn}")

    if res["status"] == "STRUCTURE_VALIDATED":
        print(f"\n {GREEN}✅ Kỹ năng đạt chuẩn cấu trúc (STRUCTURE_VALIDATED). Hợp đồng sẵn sàng.{RESET}")
    else:
        print(f"\n {RED}⛔ Kỹ năng CHƯA đạt chuẩn cấu trúc. Cần khắc phục các lỗi trên.{RESET}")
    print(f"{BOLD}═══════════════════════════════════════════════════════════════════{RESET}")

def check_registry_mismatch(skills_found, workspace_root):
    """Kiểm tra sự đồng bộ giữa danh sách thư mục skills và các bảng Registry."""
    mismatches = []
    gemini_md = workspace_root / "GEMINI.md"
    agents_md = workspace_root / ".agents" / "rules" / "AGENTS.md"

    for reg_path in [gemini_md, agents_md]:
        if reg_path.exists():
            text = reg_path.read_text(encoding="utf-8", errors="ignore")
            for sk in skills_found:
                if f"**{sk}**" not in text and f"`{sk}`" not in text and f"skills/{sk}" not in text:
                    mismatches.append(f"Skill '{sk}' tồn tại trong thư mục nhưng THIẾU trong {reg_path.name}")
    return mismatches

def main():
    parser = argparse.ArgumentParser(description="AIWF Skill Structure & Contract Auditor")
    parser.add_argument("skill_target", nargs="?", default=None, help="Đường dẫn folder skill cần kiểm định")
    parser.add_argument("--all", action="store_true", help="Kiểm định toàn bộ kỹ năng trong .agents/skills/")
    parser.add_argument("--scan-new", action="store_true", help="Tự động phát hiện skill mới chưa có chứng nhận")
    parser.add_argument("--certify", action="store_true", help="Đóng dấu xác thực cấu trúc vào .certified.json nếu đạt chuẩn")
    parser.add_argument("--quiet", action="store_true", help="Chế độ chạy im lặng cho CI/CD")
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parent.parent
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
    elif args.scan_new or args.all:
        for d in sorted(skills_root.iterdir()):
            if d.is_dir() and not d.name.startswith("."):
                # Chỉ đưa vào danh sách kiểm định nếu là thư mục chứa SKILL.md
                if (d / "SKILL.md").exists():
                    if args.scan_new:
                        current_hash = calculate_folder_hash(d)
                        if d.name not in certified_data or certified_data[d.name].get("hash") != current_hash:
                            targets.append(d)
                    else:
                        targets.append(d)
        if args.scan_new and not targets:
            if not args.quiet:
                print(f"{GREEN}✅ Toàn bộ kỹ năng đã được xác thực cấu trúc. Không có skill mới cần quét.{RESET}")
            sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)

    all_passed = True
    new_certifications = {}
    validated_names = []

    for t in targets:
        report = audit_skill(t, quiet=args.quiet)
        if not report.get("is_skill", True):
            continue

        validated_names.append(report["name"])
        if not args.quiet:
            print_report(report)

        if report["status"] != "STRUCTURE_VALIDATED":
            all_passed = False
        else:
            new_certifications[report["name"]] = {
                "hash": report["hash"],
                "score": report["score"],
                "validation_status": "STRUCTURE_VALIDATED",
                "validated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    # Kiểm tra Registry Mismatch
    if not args.quiet and targets:
        mismatches = check_registry_mismatch(validated_names, workspace)
        if mismatches:
            print(f"\n{YELLOW}{BOLD}⚠️  PHÁT HIỆN SỰ KHÔNG NHẤT QUÁN REGISTRY (REGISTRY MISMATCH):{RESET}")
            for m in mismatches:
                print(f"   • {m}")

    if args.certify and all_passed:
        certified_data.update(new_certifications)
        certified_file.write_text(json.dumps(certified_data, indent=2, ensure_ascii=False), encoding="utf-8")
        if not args.quiet:
            print(f"\n{GREEN}{BOLD}🎖️ Đã ghi nhận STRUCTURE_VALIDATED thành công cho {len(new_certifications)} kỹ năng vào {certified_file.name}!{RESET}")

    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()

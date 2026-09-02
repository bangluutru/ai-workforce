#!/usr/bin/env python3
"""
=============================================================================
📑 SCAN & BUILD SMART KNOWLEDGE CATALOG (MỤC LỤC TRI THỨC THÔNG MINH)
=============================================================================
Quét toàn bộ Notebooks và Sources từ Gemini Notebook (đa tài khoản / profile),
tự động phân loại theo 6 nhóm chuyên đề, đối chiếu với dữ liệu đã sync local,
và xuất ra:
  1. .agents/knowledge/CATALOG.md (Bản đồ tri thức Markdown trực quan)
  2. .agents/knowledge/catalog.json & dashboard/catalog.json (Dữ liệu cho Sidebar Panel)
=============================================================================
"""

import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Thư mục gốc dự án
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = WORKSPACE_ROOT / ".agents" / "knowledge"
DASHBOARD_DIR = WORKSPACE_ROOT / "dashboard"
CATALOG_MD_FILE = KNOWLEDGE_DIR / "CATALOG.md"
CATALOG_JSON_FILE = KNOWLEDGE_DIR / "catalog.json"
DASHBOARD_CATALOG_JSON = DASHBOARD_DIR / "catalog.json"

# =============================================================================
# Phân loại chuyên đề thông minh (Smart Categorization Rules)
# =============================================================================
CATEGORIES = [
    {
        "id": "health_medical",
        "name": "Y tế & Thiết bị Y tế",
        "icon": "🏥",
        "keywords": ["hm", "byt", "y tế", "y khoa", "bệnh viện", "clinical", "nhược cơ", "esc", "thu thảo", "tv-bình", "ifu"],
    },
    {
        "id": "genki_business",
        "name": "Genki Fami & Kinh doanh",
        "icon": "🌿",
        "keywords": ["gf", "genki", "kinh doanh", "tmđt", "meetings", "bc", "tiktok", "page ngách", "quy chế", "tư liệu", "report", "sống khỏe"],
    },
    {
        "id": "legal_standards",
        "name": "Văn bản Pháp luật & Thuế",
        "icon": "⚖️",
        "keywords": ["vbpl", "nghị định", "luật", "thông tư", "nđ", "tt", "cv", "qđ", "hóa chất", "thuế", "đo lường", "bkhcn"],
    },
    {
        "id": "rd_laboratory",
        "name": "R&D & Tiêu chuẩn & Phòng Lab",
        "icon": "🧪",
        "keywords": ["clsi", "balancera", "abano", "maastricht", "iso 10012", "17025", "kiểm nghiệm", "eiken", "coa", "iso 13485", "r&d"],
    },
    {
        "id": "ai_tech",
        "name": "AI & Công nghệ & Vibe Code",
        "icon": "🤖",
        "keywords": ["ai", "nano banana", "vibe code", "audio", "video", "tech"],
    },
    {
        "id": "general_hr",
        "name": "Nhân sự, Tuyển dụng & Khác",
        "icon": "📂",
        "keywords": [],  # Default fallback
    },
]

def classify_notebook(title: str) -> dict:
    """Tự động phân loại notebook theo tiêu đề."""
    title_lower = title.lower()
    for cat in CATEGORIES[:-1]:  # Trừ fallback cuối cùng
        for kw in cat["keywords"]:
            if kw in title_lower:
                return cat
    return CATEGORIES[-1]  # Fallback

def get_synced_info(notebook_id: str, title: str) -> dict:
    """Kiểm tra xem notebook này đã được sync local trong .agents/knowledge chưa."""
    slug_candidates = [
        re.sub(r'[^\w\-_]', '_', title.lower()).strip('_'),
        re.sub(r'\s+', '_', title.lower()),
    ]
    
    # Quét tất cả folder trong .agents/knowledge/
    if KNOWLEDGE_DIR.exists():
        for item in KNOWLEDGE_DIR.iterdir():
            if item.is_dir() and not item.name.startswith(('.', '_')):
                meta_file = item / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        if meta.get("notebook_id") == notebook_id or meta.get("id") in slug_candidates:
                            sources_dir = item / "artifacts" / "sources"
                            local_files = list(sources_dir.glob("*.md")) if sources_dir.exists() else []
                            return {
                                "is_synced": True,
                                "local_path": str(item.relative_to(WORKSPACE_ROOT)),
                                "synced_sources": len(local_files),
                                "last_synced": meta.get("last_synced", ""),
                            }
                    except Exception:
                        pass
    return {"is_synced": False, "local_path": "", "synced_sources": 0, "last_synced": ""}

async def scan_all_notebooks() -> dict:
    """Quét toàn bộ Notebooks và Sources từ NotebookLM client."""
    from notebooklm import NotebookLMClient
    
    print("🔍 Đang kết nối NotebookLM và quét danh mục...")
    start_time = time.time()
    
    async with NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        print(f"  📓 Tìm thấy {len(notebooks)} Notebooks. Đang quét danh sách tài liệu...")
        
        sem = asyncio.Semaphore(8)  # Concurrency limit
        
        async def fetch_nb_details(nb):
            async with sem:
                title = getattr(nb, "title", None) or "Untitled Notebook"
                nb_id = nb.id
                cat = classify_notebook(title)
                synced_info = get_synced_info(nb_id, title)
                
                sources_list = []
                try:
                    raw_sources = await client.sources.list(nb_id)
                    for s in raw_sources:
                        s_title = getattr(s, "title", "Untitled Source")
                        s_id = getattr(s, "id", "")
                        s_type = getattr(s, "type", "unknown")
                        sources_list.append({
                            "id": s_id,
                            "title": s_title,
                            "type": s_type,
                        })
                except Exception as e:
                    pass
                
                return {
                    "id": nb_id,
                    "title": title,
                    "category": cat["id"],
                    "category_name": cat["name"],
                    "category_icon": cat["icon"],
                    "access": getattr(nb, "access", "Owner"),
                    "created": getattr(nb, "created", ""),
                    "source_count": len(sources_list),
                    "sources": sources_list,
                    "sync_info": synced_info,
                }
        
        tasks = [fetch_nb_details(nb) for nb in notebooks]
        nb_results = await asyncio.gather(*tasks)
    
    elapsed = time.time() - start_time
    total_sources = sum(nb["source_count"] for nb in nb_results)
    synced_count = sum(1 for nb in nb_results if nb["sync_info"]["is_synced"])
    
    print(f"✅ Quét thành công: {len(nb_results)} Notebooks, {total_sources} Tài liệu ({elapsed:.2f}s)")
    
    # Nhóm theo category
    grouped = {}
    for cat in CATEGORIES:
        grouped[cat["id"]] = {
            "category": cat,
            "notebooks": [nb for nb in nb_results if nb["category"] == cat["id"]],
        }
        # Sắp xếp notebook theo số lượng source giảm dần
        grouped[cat["id"]]["notebooks"].sort(key=lambda x: x["source_count"], reverse=True)
    
    catalog_data = {
        "updated_at": datetime.now().isoformat(),
        "total_notebooks": len(nb_results),
        "total_sources": total_sources,
        "synced_notebooks": synced_count,
        "categories": grouped,
        "all_notebooks": nb_results,
    }
    
    return catalog_data

def generate_markdown(catalog_data: dict):
    """Xuất file .agents/knowledge/CATALOG.md với giao diện trực quan, khoa học."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    md = []
    md.append("# 📚 BẢN ĐỒ TRI THỨC GEMINI NOTEBOOK (KNOWLEDGE CATALOG)\n")
    md.append(f"> **Cập nhật:** `{now_str}` | **Tổng số Notebooks:** `{catalog_data['total_notebooks']}` | **Tổng số tài liệu:** `{catalog_data['total_sources']}` | **Đã đồng bộ local:** `{catalog_data['synced_notebooks']}`\n")
    md.append("---\n")
    
    # Bảng chỉ mục nhanh theo nhóm
    md.append("## 🧭 Danh Mục Chuyên Đề Nhanh\n")
    md.append("| Chuyên đề | Số Notebooks | Số Tài liệu | Trạng thái Sync |")
    md.append("|:---|:---:|:---:|:---|")
    
    for cat_id, group in catalog_data["categories"].items():
        cat = group["category"]
        nbs = group["notebooks"]
        if not nbs:
            continue
        src_count = sum(nb["source_count"] for nb in nbs)
        synced_in_cat = sum(1 for nb in nbs if nb["sync_info"]["is_synced"])
        sync_badge = f"✅ `{synced_in_cat}/{len(nbs)}` đã tải" if synced_in_cat > 0 else "☁️ Chưa tải"
        md.append(f"| [{cat['icon']} **{cat['name']}**](#-{cat['name'].lower().replace(' ', '-').replace('&', '').replace(',', '')}) | **{len(nbs)}** | **{src_count}** | {sync_badge} |")
    
    md.append("\n---\n")
    
    # Chi tiết từng chuyên đề
    for cat_id, group in catalog_data["categories"].items():
        cat = group["category"]
        nbs = group["notebooks"]
        if not nbs:
            continue
            
        md.append(f"## {cat['icon']} {cat['name']} ({len(nbs)} Notebooks)\n")
        
        for nb in nbs:
            sync = nb["sync_info"]
            status_badge = f"✅ **ĐÃ ĐỒNG BỘ** (`{sync['local_path']}`)" if sync["is_synced"] else "☁️ **TRÊN MÂY** (Chưa tải về)"
            
            md.append(f"### 📓 {nb['title']}")
            md.append(f"- **ID Notebook**: `{nb['id']}`")
            md.append(f"- **Tài liệu**: `{nb['source_count']}` tệp | **Trạng thái**: {status_badge}")
            
            if nb["sources"]:
                md.append("\n<details><summary><b>📄 Xem danh sách " + str(len(nb["sources"])) + " tài liệu</b> (bấm để mở)</summary>\n")
                md.append("| STT | Tên tài liệu | Định dạng | Hành động |")
                md.append("|:---:|:---|:---:|:---|")
                for i, s in enumerate(nb["sources"], 1):
                    s_type = s["type"] or "PDF"
                    # Tạo link đến file local nếu đã sync
                    action = "*(Chạy sync để xem nội dung)*"
                    if sync["is_synced"]:
                        action = f"[🔍 Xem file local](file://{WORKSPACE_ROOT}/{sync['local_path']}/artifacts/sources/)"
                    md.append(f"| {i} | `{s['title']}` | `{s_type}` | {action} |")
                md.append("\n</details>\n")
            else:
                md.append("\n*(Notebook chưa có tài liệu nào)*\n")
            
            md.append("")
        
        md.append("---\n")
        
    md.append("\n## 💡 Hướng dẫn khai thác tri thức\n")
    md.append("1. **Đồng bộ 1 Notebook cụ thể:** `python3 scripts/sync_notebook.py --notebook-id <ID>`")
    md.append("2. **Dịch tài liệu trong Notebook:** Nhắn Agent: *'Dịch [Tên tài liệu] trong notebook [Tên notebook] sang tiếng Anh'*")
    md.append("3. **Tư vấn dựa trên tri thức:** Nhắn Agent: *'Tra cứu quy định về thiết bị y tế trong kho tri thức BYT+'*")
    
    with open(CATALOG_MD_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"  📄 Đã tạo file mục lục Markdown: {CATALOG_MD_FILE}")

def main():
    catalog_data = asyncio.run(scan_all_notebooks())
    
    # 1. Ghi catalog.json vào cả .agents/knowledge và dashboard
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(CATALOG_JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Đã lưu JSON: {CATALOG_JSON_FILE}")
    
    with open(DASHBOARD_CATALOG_JSON, "w", encoding="utf-8") as f:
        json.dump(catalog_data, f, ensure_ascii=False, indent=2)
    print(f"  💾 Đã lưu JSON Dashboard: {DASHBOARD_CATALOG_JSON}")
    
    # 2. Sinh Markdown CATALOG.md
    generate_markdown(catalog_data)
    
    print("\n🎉 Hoàn tất xây dựng Bản đồ Tri thức Thông minh!")

if __name__ == "__main__":
    main()

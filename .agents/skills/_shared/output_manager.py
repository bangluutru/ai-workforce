"""
AIWF Output Manager — Module dùng chung cho tất cả skills.

Quản lý đường dẫn output, đảm bảo không bao giờ lưu thành phẩm
vào bên trong thư mục workspace (codebase) của AIWF.

Quy tắc 3 mức ưu tiên:
  1. user_path   — người dùng chỉ định rõ trong prompt
  2. AIWF_OUTPUT_DIR — biến môi trường (set trong .env hoặc shell)
  3. ~/Downloads/AIWF_Output/<skill_name>/  — mặc định

Tuân thủ:
  - Rule R0: Output nằm ngoài workspace → git pull trên máy mới không kéo rác
  - Rule R1: Không bao giờ ghi file kết quả vào thư mục gốc repository
"""

import os
import sys
from pathlib import Path
from datetime import datetime

DEFAULT_OUTPUT_BASE = Path.home() / "Downloads" / "AIWF_Output"


def resolve_output_dir(
    skill_name: str,
    user_path: str | None = None,
    project_name: str | None = None,
) -> Path:
    """
    Xác định thư mục output theo 3 mức ưu tiên.

    Args:
        skill_name:   Tên skill đang chạy (vd: 'ejv-translate', 'boc-tach-pdf')
        user_path:    Đường dẫn user chỉ định (vd: '~/Desktop', '/tmp/out')
        project_name: Tên dự án/tài liệu (vd: 'hop_dong_abc') — nếu None sẽ dùng timestamp

    Returns:
        Path object trỏ tới thư mục output đã được tạo sẵn.

    Examples:
        >>> resolve_output_dir("ejv-translate", project_name="hop_dong")
        PosixPath('/Users/user/Downloads/AIWF_Output/ejv-translate/hop_dong')

        >>> resolve_output_dir("boc-tach-pdf", user_path="~/Desktop")
        PosixPath('/Users/user/Desktop/boc-tach-pdf/20260926_114500')
    """
    # Bước 1: Chọn base directory
    if user_path:
        base = Path(user_path).expanduser().resolve()
    elif os.environ.get("AIWF_OUTPUT_DIR"):
        base = Path(os.environ["AIWF_OUTPUT_DIR"]).expanduser().resolve()
    else:
        base = DEFAULT_OUTPUT_BASE

    # Bước 2: Tạo subfolder theo skill + project/timestamp
    if project_name:
        # Chuẩn hóa tên: loại bỏ ký tự đặc biệt, thay khoảng trắng bằng _
        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in project_name
        ).strip("_")
        output_dir = base / skill_name / safe_name
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = base / skill_name / timestamp

    # Bước 3: Tạo thư mục (kể cả parents)
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def validate_not_in_workspace(output_dir: Path) -> bool:
    """
    Kiểm tra output_dir KHÔNG nằm bên trong workspace AIWF.

    Trả về True nếu an toàn (nằm ngoài workspace).
    In cảnh báo và trả về False nếu nằm trong workspace.
    """
    # Tìm workspace root bằng cách tìm ngược lên thư mục chứa GEMINI.md
    current = Path(__file__).resolve()
    workspace_root = None
    for parent in current.parents:
        if (parent / "GEMINI.md").exists():
            workspace_root = parent
            break

    if workspace_root and output_dir.resolve().is_relative_to(workspace_root):
        print(
            f"⚠️  CẢNH BÁO: Output dir '{output_dir}' nằm BÊN TRONG workspace AIWF!\n"
            f"   Workspace: {workspace_root}\n"
            f"   Điều này vi phạm Rule R1. Đề xuất dùng ~/Downloads/AIWF_Output/ thay thế.",
            file=sys.stderr,
        )
        return False
    return True


def get_output_summary(output_dir: Path) -> str:
    """
    Trả về tóm tắt ngắn gọn cho agent báo cáo cho user sau khi hoàn thành.

    Args:
        output_dir: Thư mục output đã lưu file thành phẩm.

    Returns:
        Chuỗi markdown tóm tắt số file, đường dẫn và lệnh mở nhanh.
    """
    if not output_dir.exists():
        return f"📁 Thư mục output: {output_dir} (chưa được tạo)"

    files = [f for f in output_dir.iterdir() if f.is_file()]
    total_size = sum(f.stat().st_size for f in files)

    # Format size
    if total_size >= 1_073_741_824:
        size_str = f"{total_size / 1_073_741_824:.1f} GB"
    elif total_size >= 1_048_576:
        size_str = f"{total_size / 1_048_576:.1f} MB"
    elif total_size >= 1024:
        size_str = f"{total_size / 1024:.1f} KB"
    else:
        size_str = f"{total_size} B"

    file_list = "\n".join(f"  - {f.name}" for f in sorted(files)[:10])
    if len(files) > 10:
        file_list += f"\n  - ... và {len(files) - 10} file khác"

    return (
        f"📁 **Thư mục output:** `{output_dir}`\n"
        f"📄 **Số file:** {len(files)} ({size_str})\n"
        f"{file_list}\n"
        f"💡 **Mở thư mục:** `open '{output_dir}'`"
    )


# === CLI test ===
if __name__ == "__main__":
    # Demo: python3 output_manager.py ejv-translate --project hop_dong_abc
    import argparse

    parser = argparse.ArgumentParser(description="AIWF Output Manager")
    parser.add_argument("skill", help="Tên skill (vd: ejv-translate)")
    parser.add_argument("--path", help="Đường dẫn output do user chỉ định")
    parser.add_argument("--project", help="Tên project/tài liệu")
    args = parser.parse_args()

    out = resolve_output_dir(args.skill, user_path=args.path, project_name=args.project)
    validate_not_in_workspace(out)
    print(get_output_summary(out))

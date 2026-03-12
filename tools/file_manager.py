import os
import subprocess
import logging
import shutil
from typing import Optional

logger = logging.getLogger("FileManager")

def search_files(query: str, root_path: str = ".") -> str:
    """
    Tìm kiếm file hoặc thư mục theo tên.
    """
    try:
        # Sử dụng find để tìm kiếm (nhanh trên Linux/WSL)
        cmd = ["find", root_path, "-iname", f"*{query}*"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return f"❌ Lỗi khi tìm kiếm: {result.stderr}"
        
        lines = result.stdout.strip().splitlines()
        if not lines:
            return f"🔍 Không tìm thấy file/thư mục nào khớp với '{query}' tại '{root_path}'."
        
        # Giới hạn 20 kết quả đầu tiên
        output = f"🔍 Tìm thấy {len(lines)} kết quả cho '{query}':\n"
        for line in lines[:20]:
            output += f"- {line}\n"
        if len(lines) > 20:
            output += f"... và {len(lines) - 20} kết quả khác."
        return output
    except Exception as e:
        return f"❌ Lỗi hệ thống: {str(e)}"

def list_directory(path: str = ".") -> str:
    """
    Liệt kê nội dung của thư mục.
    """
    try:
        if not os.path.exists(path):
            return f"❌ Thư mục '{path}' không tồn tại."
        
        if not os.path.isdir(path):
            return f"❌ '{path}' không phải là một thư mục."
            
        items = os.listdir(path)
        if not items:
            return f"📂 Thư mục '{path}' đang trống."
            
        output = f"📂 Nội dung thư mục '{path}':\n"
        for item in sorted(items):
            full_path = os.path.join(path, item)
            prefix = "📁" if os.path.isdir(full_path) else "📄"
            size = os.path.getsize(full_path) if os.path.isfile(full_path) else ""
            size_str = f" ({size} bytes)" if size else ""
            output += f"{prefix} {item}{size_str}\n"
        return output
    except Exception as e:
        return f"❌ Lỗi khi liệt kê thư mục: {str(e)}"

def write_file(path: str, content: str, append: bool = False) -> str:
    """
    Ghi nội dung vào file. Tạo file mới nếu chưa tồn tại.
    """
    try:
        mode = "a" if append else "w"
        # Đảm bảo thư mục cha tồn tại
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
        with open(path, mode, encoding="utf-8") as f:
            f.write(content)
        
        action_word = "Đã thêm vào" if append else "Đã ghi vào"
        return f"✅ {action_word} file: {path}"
    except Exception as e:
        return f"❌ Lỗi khi ghi file: {str(e)}"

def create_directory(path: str) -> str:
    """
    Tạo thư mục mới (bao gồm cả các thư mục cha nếu cần).
    """
    try:
        if os.path.exists(path):
            if os.path.isdir(path):
                return f"ℹ️ Thư mục '{path}' đã tồn tại."
            else:
                return f"❌ Không thể tạo thư mục: '{path}' đã tồn tại và là một file."
        
        os.makedirs(path, exist_ok=True)
        return f"✅ Đã tạo thư mục: {path}"
    except Exception as e:
        return f"❌ Lỗi khi tạo thư mục: {str(e)}"

def open_path(path: str) -> str:
    """
    Mở file hoặc thư mục bằng ứng dụng mặc định của hệ thống.
    """
    try:
        if not os.path.exists(path):
            return f"❌ Đường dẫn '{path}' không tồn tại."
            
        abs_path = os.path.abspath(path)
        
        if abs_path.startswith("/mnt/"):
            try:
                wslpath_cmd = ["wslpath", "-w", abs_path]
                win_path = subprocess.check_output(wslpath_cmd, text=True).strip()
                subprocess.Popen(["explorer.exe", win_path])
                return f"🚀 Đã yêu cầu Windows mở: {win_path}"
            except:
                subprocess.Popen(["explorer.exe", abs_path])
                return f"🚀 Đã yêu cầu mở (WSL/Windows): {abs_path}"
        else:
            try:
                subprocess.Popen(["xdg-open", abs_path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                return f"🚀 Đã mở: {abs_path}"
            except:
                subprocess.Popen(["explorer.exe", abs_path])
                return f"🚀 Đã mở (via Explorer): {abs_path}"
                
    except Exception as e:
        return f"❌ Không thể mở '{path}': {str(e)}"

def delete_file(path: str) -> str:
    """Xóa một file."""
    try:
        if not os.path.exists(path):
            return f"❌ File '{path}' không tồn tại."
        if not os.path.isfile(path):
            return f"❌ '{path}' không phải là một file. Dùng 'delete_directory' để xóa thư mục."
        os.remove(path)
        return f"✅ Đã xóa file: {path}"
    except Exception as e:
        return f"❌ Lỗi khi xóa file: {str(e)}"

def delete_directory(path: str) -> str:
    """Xóa một thư mục và tất cả nội dung bên trong."""
    try:
        if not os.path.exists(path):
            return f"❌ Thư mục '{path}' không tồn tại."
        if not os.path.isdir(path):
            return f"❌ '{path}' không phải là một thư mục. Dùng 'delete_file' để xóa file."
        shutil.rmtree(path)
        return f"✅ Đã xóa thư mục và nội dung bên trong: {path}"
    except Exception as e:
        return f"❌ Lỗi khi xóa thư mục: {str(e)}"

async def manage_files(action: str, query: str = None, path: str = ".", **kwargs) -> str:
    """
    Tool quản lý file đa năng (vẫn giữ để tương thích hoặc debug).
    """
    logger.info(f"📁 [FileManager] Action: {action}, Path: {path}, Query: {query}")
    
    if action == "search":
        return search_files(query, path)
    elif action == "list":
        return list_directory(path)
    elif action == "open":
        return open_path(path)
    elif action == "create":
        return create_directory(path)
    elif action == "write":
        return write_file(path, kwargs.get("content", ""), kwargs.get("append", False))
    elif action == "delete_file":
        return delete_file(path)
    elif action == "delete_dir":
        return delete_directory(path)
    else:
        return f"❌ Hành động '{action}' không hợp lệ."

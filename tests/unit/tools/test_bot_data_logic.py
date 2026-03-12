import asyncio
import os
import sys

# Thêm đường dẫn project vào sys.path
sys.path.append(os.getcwd())

from tools.file_manager import manage_files

async def test_bot_data_logic():
    print("\n" + "="*60)
    print("TEST: Logic Tìm kiếm và Tạo thư mục Bot_Data")
    print("="*60)
    
    target_dir = "Bot_Data"
    
    # 1. Đảm bảo môi trường sạch (xóa thư mục nếu đã tồn tại để test logic tạo mới)
    if os.path.exists(target_dir):
        print(f"🧹 Đang dọn dẹp thư mục cũ '{target_dir}'...")
        import shutil
        if os.path.isdir(target_dir):
            shutil.rmtree(target_dir)
        else:
            os.remove(target_dir)

    # 2. Bước 1: Tìm kiếm thư mục
    print(f"\nStep 1: Tìm kiếm '{target_dir}'...")
    # Thêm -type d vào flow find của tool (nhưng tool chưa support) 
    # -> Nên ta filter thủ công kết quả trả về trong test
    search_result = await manage_files(action="search", query=target_dir, path=".")
    print(f"Kết quả tìm kiếm thô: {search_result}")
    
    # Logic kiểm tra chính xác: Tìm dòng nào kết thúc bằng /Bot_Data hoặc là ./Bot_Data và là thư mục
    lines = search_result.strip().splitlines()
    exists = any(line.endswith(f"/{target_dir}") or line == f"./{target_dir}" for line in lines if "Tìm thấy" not in line)
    
    if not exists:
        print(f"👉 Thư mục chưa có. Tiến hành tạo mới...")
        # 3. Bước 2: Tạo thư mục
        create_result = await manage_files(action="create", path=target_dir)
        print(f"Kết quả tạo: {create_result}")
        
        # Kiểm tra thực tế trên hệ thống
        assert os.path.exists(target_dir) and os.path.isdir(target_dir), "❌ FAIL: Thư mục không được tạo thành công"
        assert "✅ Đã tạo thư mục" in create_result, "❌ FAIL: Thông báo trả về không đúng"
    else:
        print(f"ℹ️ Thư mục đã tồn tại từ trước (không nên xảy ra trong test này do đã dọn dẹp).")

    # 4. Bước 3: Kiểm tra lại bằng action='list'
    print(f"\nStep 3: Liệt kê để xác nhận...")
    list_result = await manage_files(action="list", path=".")
    print(list_result)
    assert target_dir in list_result, f"❌ FAIL: Không tìm thấy '{target_dir}' trong danh sách folder"

    print("\n✅ TEST BOT_DATA LOGIC PASSED")

async def main():
    try:
        await test_bot_data_logic()
    except Exception as e:
        print(f"\n❌ Kiểm thử THẤT BẠI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

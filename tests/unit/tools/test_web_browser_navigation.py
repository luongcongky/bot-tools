"""
Unit test: Kiểm tra tính năng trích xuất link chương tiếp theo.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())
from tools.web_browser import browse_website

TEST_URL = "https://truyenfull.vision/tong-tai-ba-dao-xuyen-thanh-chong-bi-bo-roi/chuong-1/"

async def test_navigation_link_extraction():
    print("\n" + "="*60)
    print("TEST: Trích xuất link điều hướng (Chương tiếp)")
    print("="*60)
    
    # Chạy browse_website với extract_links=True
    result = await browse_website(url=TEST_URL, extract_links=True)

    print(f"\n📊 Độ dài nội dung: {len(result)} ký tự")
    
    # Kiểm tra xem có mục LINK ĐIỀU HƯỚNG hay không
    assert "### 🔗 LINK ĐIỀU HƯỚNG" in result, "❌ FAIL: Không tìm thấy mục Link điều hướng trong kết quả"
    
    # Kiểm tra xem có link chương tiếp theo hay không
    # Vì đây là chương 1, link tiếp theo nên là chương 2
    assert "Chương tiếp" in result or "Next" in result, "❌ FAIL: Không tìm thấy text 'Chương tiếp' hoặc 'Next'"
    assert "chuong-2" in result.lower(), "❌ FAIL: Không tìm thấy URL của chương 2 trong link điều hướng"
    
    print("\n✅ TEST NAVIGATION PASSED")
    print("\n--- Kết quả trích xuất ---\n")
    # Lấy phần cuối của kết quả để xem các link
    nav_start = result.find("### 🔗 LINK ĐIỀU HƯỚNG")
    print(result[nav_start:])

async def main():
    print("🚀 Bắt đầu kiểm thử tính năng điều hướng của web_browser...")
    try:
        await test_navigation_link_extraction()
        print("\n🎉 Kiểm thử THÀNH CÔNG!")
    except Exception as e:
        print(f"\n❌ Kiểm thử THẤT BẠI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

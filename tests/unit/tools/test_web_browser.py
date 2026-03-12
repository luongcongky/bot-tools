"""
Unit test: browse_website cho kịch bản đọc truyelong web.
"""
import asyncio
import sys
import os

sys.path.append(os.getcwd())
from tools.web_browser import browse_website

TEST_URL = "https://truyenfull.vision/tong-tai-ba-dao-xuyen-thanh-chong-bi-bo-roi/chuong-1/"

async def test_direct_url():
    print("\n" + "="*60)
    print("TEST 1: Truyền URL trực tiếp qua tham số url=")
    print("="*60)
    result = await browse_website(url=TEST_URL)

    print(f"\n📊 Độ dài nội dung: {len(result)} ký tự")
    print(f"\n--- [NỘI DUNG 3000 KÝ TỰ ĐẦU] ---\n")
    print(result[:3000])
    print("\n--- [KẾT THÚC XEM TRƯỚC] ---")

    assert len(result) > 100, "❌ FAIL: Nội dung quá ngắn, crawler có thể thất bại"
    assert "❌" not in result[:50], f"❌ FAIL: Có lỗi khi crawl: {result[:200]}"
    print("\n✅ TEST 1 PASSED")

async def test_from_user_input():
    print("\n" + "="*60)
    print("TEST 2: Phân tích URL từ câu lệnh người dùng (user_input)")
    print("="*60)
    user_msg = f"Hãy đọc trang web {TEST_URL} và đưa ra nội dung chương 1"
    result = await browse_website(user_input=user_msg)

    print(f"\n📊 Độ dài: {len(result)} ký tự")
    assert len(result) > 100, "❌ FAIL: Không trích xuất được nội dung từ user_input"
    print("\n✅ TEST 2 PASSED")

async def test_no_url():
    print("\n" + "="*60)
    print("TEST 3: Không có URL — phải trả lỗi thân thiện")
    print("="*60)
    result = await browse_website(user_input="Cho tôi xem lịch ngày mai")
    print(f"Kết quả: {result}")
    assert "❌" in result or "URL" in result, "❌ FAIL: Phải báo lỗi không có URL"
    print("\n✅ TEST 3 PASSED")

async def main():
    print("🚀 Bắt đầu kiểm thử web_browser tool...")
    await test_no_url()
    await test_from_user_input()
    await test_direct_url()
    print("\n\n🎉 Tất cả tests PASSED!")

if __name__ == "__main__":
    asyncio.run(main())

import re
from crawl4ai import AsyncWebCrawler

async def browse_website(user_input):
    """
    Tự động tìm và trích xuất URL từ câu lệnh của người dùng rồi mới cào dữ liệu.
    """
    # Sử dụng Regex để tìm URL trong câu
    url_pattern = r'https?://[^\s]+'
    match = re.search(url_pattern, user_input)
    
    if not match:
        return "❌ Mình không tìm thấy đường link URL nào trong câu lệnh của bạn."
    
    target_url = match.group(0)
    print(f"--- [TOOL] Mắt thần đang truy cập: {target_url} ---")
    
    try:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=target_url)
            if result.success:
                return result.markdown[:2000] # Giới hạn 2000 ký tự cho AI
            else:
                return f"⚠️ Crawler báo lỗi: {result.error_message}"
    except Exception as e:
        return f"❌ Lỗi hệ thống khi cào web: {str(e)}"

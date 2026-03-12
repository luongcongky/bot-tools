import re
import logging
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

logger = logging.getLogger("WebBrowser")

# Giới hạn nội dung trả về (ký tự)
MAX_CONTENT_LENGTH = 100000

def _extract_url(text: str) -> str | None:
    """Trích xuất URL từ câu lệnh của người dùng."""
    pattern = r'https?://[^\s]+'
    match = re.search(pattern, text)
    return match.group(0).rstrip(".,;\"'") if match else None

def _clean_content(raw_markdown: str) -> str:
    """
    Lọc bỏ các phần không cần thiết (navigation, menu, ads, script...)
    và giữ lại nội dung bài viết chính.
    """
    lines = raw_markdown.splitlines()
    filtered = []
    skip_patterns = [
        r'^\s*\[.*\]\(.*\)\s*$',  # Dòng chỉ là link markdown
        r'^\s*!?\[.*\]\(data:.*\)',  # Base64 image
        r'^\s*[|]{1}',             # Markdown table header-only rows
        r'^\s*[-]{3,}\s*$',        # Horizontal rules
        r'^\s*[#]{4,}',            # Deep headings thường là nav
    ]
    for line in lines:
        if any(re.match(pat, line) for pat in skip_patterns):
            continue
        filtered.append(line)

    # Ghép lại và loại bỏ nhiều dòng trắng liên tiếp
    content = "\n".join(filtered)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


async def browse_website(url: str = None, user_input: str = None, extract_links: bool = False, **kwargs) -> str:
    """
    Truy cập URL và trích xuất nội dung trang web, trả về dạng Markdown.

    Tham số:
        url (str): URL trực tiếp cần truy cập.
        user_input (str): Câu lệnh người dùng (sẽ tự phân tích URL từ đây nếu không có `url`).
        extract_links (bool): Nếu True, cố gắng trích xuất các link hướng dẫn (Chương tiếp, Trang sau...).
    """
    # Ưu tiên: tham số url trực tiếp > phân tích từ user_input
    target_url = url
    if not target_url and user_input:
        target_url = _extract_url(user_input)
    if not target_url:
        return "❌ Không tìm thấy URL hợp lệ. Vui lòng cung cấp đường link cụ thể."

    logger.info(f"🌐 [WebBrowser] Đang truy cập: {target_url}")

    browser_cfg = BrowserConfig(headless=True, verbose=False)
    
    # Nếu cần trích xuất link, chúng ta không bỏ qua các tag chứa navigation
    excluded_tags = ["footer", "header", "aside", "script", "style", "form"]
    if not extract_links:
        excluded_tags.extend(["nav", "button"])
        
    run_cfg = CrawlerRunConfig(
        word_count_threshold=10,
        remove_overlay_elements=True,
        excluded_tags=excluded_tags,
        wait_until="domcontentloaded",
    )

    try:
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=target_url, config=run_cfg)

        if not result.success:
            return f"⚠️ Không thể tải trang: {result.error_message}"

        content = _clean_content(result.markdown or "")

        if not content:
            return "⚠️ Đã tải trang nhưng không trích xuất được nội dung văn bản."

        # Trả về nội dung, giới hạn MAX_CONTENT_LENGTH ký tự
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH]
            content += f"\n\n---\n⚠️ *Nội dung đã được cắt tại {MAX_CONTENT_LENGTH} ký tự. Trang gốc có nhiều hơn.*"

        logger.info(f"✅ [WebBrowser] Đã trích xuất {len(content)} ký tự từ {target_url}")

        if extract_links:
            # Thu thập các link điều hướng quan trọng
            nav_links = []
            keywords = ["chương tiếp", "trang sau", "next", "sau >", "tiếp theo", "chương sau"]
            
            # Crawl4AI thường trả về danh sách link trong result.links
            # Ở đây chúng ta duyệt qua các link đó (Internal/External)
            all_links = (result.links.get("internal", []) + result.links.get("external", []))
            
            unique_links = {}
            for link in all_links:
                href = link.get("href", "")
                text = link.get("text", "").lower().strip()
                if not href or not text:
                    continue
                # Ưu tiên các link chứa keyword quan trọng
                if any(kw in text for kw in keywords):
                    # Chỉ lấy link dài nhất nếu trùng href (tránh lấy icon)
                    if href not in unique_links or len(text) > len(unique_links[href]):
                        unique_links[href] = text
            
            if unique_links:
                nav_section = "\n\n### 🔗 LINK ĐIỀU HƯỚNG (PHÁT HIỆN ĐƯỢC):\n"
                for href, text in unique_links.items():
                    nav_section += f"- **{text.capitalize()}**: {href}\n"
                content += nav_section

        return content

    except Exception as e:
        logger.error(f"❌ [WebBrowser] Lỗi: {e}")
        return f"❌ Lỗi khi truy cập trang web: {str(e)}"

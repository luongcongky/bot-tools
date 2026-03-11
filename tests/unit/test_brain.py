import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from app.core.orchestration.orchestrator import process_request

# Cấu hình logging để xem chi tiết các bước xử lý ngầm
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestBrain")

async def run_test():
    """
    Hàm giả lập gửi tin nhắn của người dùng tới hệ thống Orchestration.
    """
    print("="*50)
    print("HỆ THỐNG KIỂM TRA AI ORCHESTRATION")
    print("="*50)
    
    while True:
        # Nhập câu hỏi từ terminal
        user_input = input("\nNhập câu hỏi test (hoặc 'exit' để thoát): ")
        
        if user_input.lower() in ['exit', 'quit', 'thoát']:
            break
            
        print(f"\n[USER]: {user_input}")
        print("-" * 30)
        
        try:
            # Gọi trực tiếp hàm xử lý chính của orchestration
            # Hàm này sẽ chạy Vector Search -> LLM -> Registry
            response = await process_request(user_input)
            
            print(f"\n[AI RESPONSE]:\n{response}")
            
        except Exception as e:
            logger.error(f"Lỗi trong quá trình test: {e}")
            
    print("\nKết thúc chương trình test.")

if __name__ == "__main__":
    # Chạy loop async
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        pass

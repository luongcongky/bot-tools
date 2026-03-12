import logging
import os
import sys
import warnings

# PHẢI CẤU HÌNH LOGGING TRƯỚC
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Chặn log chi tiết từ các thư viện gây nhiễu
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub.utils._http").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Tắt telemetry và các warning không cần thiết từ HF Hub
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Chặn warning bằng thư viện warnings
warnings.filterwarnings("ignore", message=".*unauthenticated requests to the HF Hub.*")
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub.*")
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)
logging.getLogger("googleapiclient.discovery").setLevel(logging.ERROR)

from app.adapters.telegram.bot import run_bot

if __name__ == "__main__":
    run_bot()

# My Bot - Hexagonal Architecture

Dự án này được tổ chức theo kiến trúc Hexagonal (Ports & Adapters) để đảm bảo tính mở rộng và dễ bảo trì.

## Cấu trúc thư mục (Directory Structure)

```text
my_bot/
├── app/
│   ├── adapters/               # Cổng kết nối với thế giới bên ngoài (Inputs)
│   │   ├── telegram/           # Xử lý Telegram Bot API
│   │   ├── voice/              # Xử lý Speech-to-Text (STT) - [Future]
│   │   └── web_chat/           # Xử lý WebSocket/REST cho chat - [Future]
│   ├── core/                   # Trái tim của hệ thống (Business Logic)
│   │   ├── orchestration/      # Bộ điều phối (Planner & Executor)
│   │   │   ├── orchestrator.py # Luồng xử lý chính
│   │   │   ├── planner.py      # Lập kế hoạch (Ollama:Gemma2)
│   │   │   └── executor.py     # Thực thi kế hoạch
│   │   └── ai/                 # Kết nối LLM và Prompts
│   │       ├── llm_client.py   # Client kết nối Ollama
│   │       └── prompt_templates.py # Quản lý System Prompts
│   ├── services/               # Logic nghiệp vụ ứng dụng
│   │   └── tool_manager.py     # Quản lý nạp và gọi Tool động
│   ├── infrastructure/         # Kết nối hạ tầng cơ sở
│   │   ├── database/           # Cấu hình Postgres và Session
│   │   └── repositories/       # Truy vấn dữ liệu (History, Tools)
│   └── models/                 # Định nghĩa schemas (Pydantic models)
├── migrations/                 # Quản lý DB versioning (Alembic)
├── tests/                      # Thư mục chứa mã nguồn test
│   └── unit/                   # Test unit cho core và tools
├── tools/                      # Thư mục mã nguồn các tool thực thi
└── main.py                     # Điểm chạy ứng dụng chính
```

## Cách chạy dự án

1. Kích hoạt môi trường ảo: `source venv/bin/activate`
2. Cài đặt dependency: `pip install -r requirements.txt`
3. Chạy bot: `python3 main.py`

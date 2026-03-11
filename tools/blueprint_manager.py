import subprocess
import os

async def punch_blueprint(user_input=None, **kwargs):
    """
    Kích hoạt trực tiếp punch_task từ module tools.
    """
    try:
        from tools import punch_task
        # Chạy trực tiếp function async
        await punch_task.run(**kwargs)
        return "✅ Punch Blueprint thành công bằng cách gọi trực tiếp!"
            
    except Exception as e:
        return f"⚠️ Hệ thống gặp sự cố khi gọi punch_task: {str(e)}"

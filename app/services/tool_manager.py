import importlib
import logging
import inspect
import asyncio
from app.infrastructure.database.session import get_db_connection

logger = logging.getLogger("ToolManager")

async def execute_tool(intent_key, parameters, user_input="", chat_id="default"):
    """
    Nạp và thực thi code Python dựa trên intent_key được chọn.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = "SELECT internal_result FROM ai_intents WHERE intent_key = %s"
        cur.execute(query, (intent_key,))
        row = cur.fetchone()
        
        if not row or not row[0]:
            return {"status": "error", "message": f"Tool '{intent_key}' chưa được cấu hình code thực thi."}
        
        internal_path = row[0]
        if ":" not in internal_path:
            return {"status": "error", "message": f"Cấu hình sai định dạng file:hàm cho {intent_key}"}
            
        file_name, func_name = internal_path.split(":")
        module_path = f"tools.{file_name}"
        
        # Load module dynamically
        module = importlib.import_module(module_path)
        importlib.reload(module)
        func = getattr(module, func_name)
        
        # Inspect parameters
        sig = inspect.signature(func)
        call_args = {}
        for name in sig.parameters:
            if name in parameters:
                call_args[name] = parameters[name]
            elif name == "user_input":
                call_args["user_input"] = user_input
            elif name == "chat_id" and "chat_id" not in parameters:
                # Tự động inject chat_id từ context nếu tool cần nhưng AI không truyền
                call_args["chat_id"] = chat_id
        
        logger.info(f"--- [TOOL MANAGER] Đang chạy: {file_name}.{func_name} ---")
        
        # Execute (Async/Sync)
        if inspect.iscoroutinefunction(func):
            result = await func(**call_args)
        else:
            result = func(**call_args)
            
        return {"status": "success", "result": result}

    except ImportError:
        logger.error(f"Không tìm thấy file: tools/{file_name}.py")
        return {"status": "error", "message": "File thực thi bị thiếu."}
    except AttributeError:
        logger.error(f"Hàm {func_name} không tồn tại trong {file_name}.py")
        return {"status": "error", "message": "Hàm xử lý bị thiếu."}
    except Exception as e:
        logger.error(f"Lỗi thực thi tool {intent_key}: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        if conn:
            cur.close()
            conn.close()

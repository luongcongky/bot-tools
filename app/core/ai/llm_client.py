from ollama import AsyncClient
import logging

logger = logging.getLogger("LLMClient")

async def get_llm_response(model, messages, format=None, options=None):
    try:
        client = AsyncClient()
        kwargs = {"model": model, "messages": messages}
        if format:
            kwargs["format"] = format
        if options:
            kwargs["options"] = options
            
        response = await client.chat(**kwargs)
        return response['message']['content']
    except Exception as e:
        logger.error(f"Error calling Ollama (Async): {e}")
        raise

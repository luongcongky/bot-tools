from ollama import AsyncClient
import logging

logger = logging.getLogger("LLMClient")

async def get_llm_response(model, messages, format=None):
    try:
        client = AsyncClient()
        if format:
            response = await client.chat(model=model, format=format, messages=messages)
        else:
            response = await client.chat(model=model, messages=messages)
        
        return response['message']['content']
    except Exception as e:
        logger.error(f"Error calling Ollama (Async): {e}")
        raise

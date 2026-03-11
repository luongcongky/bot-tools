from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class ChatMessage(BaseModel):
    chat_id: str
    role: str
    content: str
    created_at: Optional[datetime] = None

class AIIntent(BaseModel):
    intent_key: str
    description: str
    is_action: bool
    internal_result: Optional[str] = None
    description_vector: Optional[List[float]] = None

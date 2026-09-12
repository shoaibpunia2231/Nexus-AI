"""
chat.py -- Router for the context-aware clinical educational assistant.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from services.chatbot_service import ClinicalChatbot

router = APIRouter(prefix="/api", tags=["Chatbot"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or prompt")
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current patient session data (demographics, parameters, prediction)",
    )
    history: Optional[List[ChatMessage]] = Field(
        default=[],
        description="Recent conversation history",
    )


class ChatResponse(BaseModel):
    response: str
    is_safe: bool = True
    disclaimer: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(payload: ChatRequest):
    """
    Context-aware educational chat endpoint for answering questions about
    blood parameters, dengue warning symptoms, and current session results.
    """
    try:
        chat_hist = [h.dict() for h in payload.history] if payload.history else []
        reply = ClinicalChatbot.get_response(
            user_message=payload.message,
            context=payload.context or {},
            chat_history=chat_hist,
        )
        return ChatResponse(
            response=reply,
            is_safe=True,
            disclaimer=ClinicalChatbot.SYSTEM_DISCLAIMER,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chatbot service error: {str(e)}",
        )

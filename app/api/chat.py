"""Chat-based report assistant endpoints — accountant only."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app.core.security import require_roles
from app.db import get_db
from app.models.user import User, UserRole
from app.schemas.chat import ChatHistoryResponse, ChatMessageOut, ChatRequest, ChatResponse
from app.services import chat_service

router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    db: DbSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.ACCOUNTANT)),
):
    reply, chart = chat_service.answer(db, message=body.message, user=user)
    return ChatResponse(reply=reply, chart=chart)


@router.get("/api/chat/history", response_model=ChatHistoryResponse)
def get_chat_history(
    db: DbSession = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ACCOUNTANT)),
):
    rows = chat_service.history(db)
    messages = [
        ChatMessageOut(
            id=r.id,
            role=r.role,
            message=r.message,
            reply=r.reply,
            chart=r.chart_html,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return ChatHistoryResponse(messages=messages)

import time
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, ChatLog, UsageLog
from app.schemas import ChatRequest, ChatResponse
from app.auth import get_current_user
from app.llm import get_llm_provider, get_available_models

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a prompt to the LLM and get a response."""
    start_time = time.time()

    try:
        llm = get_llm_provider()
        model = request.model or llm.default_model

        # Call LLM
        response_text, prompt_tokens, completion_tokens = llm.chat(
            prompt=request.prompt,
            model=model,
        )

        latency = time.time() - start_time

        # Log chat to database
        chat_log = ChatLog(
            user_id=current_user.id,
            prompt=request.prompt,
            response=response_text,
            model=model,
        )
        db.add(chat_log)

        # Log usage
        usage_log = UsageLog(
            user_id=current_user.id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
        db.add(usage_log)
        db.commit()

        logger.info(
            f"Chat completed: user_id={current_user.id}, model={model}, "
            f"latency={latency:.2f}s, tokens={prompt_tokens + completion_tokens}"
        )

        return ChatResponse(
            response=response_text,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    except Exception as e:
        logger.error(f"Chat failed: user_id={current_user.id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get response from LLM: {str(e)}"
        )


@router.get("/models", response_model=List[str])
async def list_models(current_user: User = Depends(get_current_user)):
    """Get list of available models."""
    return get_available_models()


@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for the current user."""
    chats = (
        db.query(ChatLog)
        .filter(ChatLog.user_id == current_user.id)
        .order_by(ChatLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": chat.id,
            "prompt": chat.prompt,
            "response": chat.response,
            "model": chat.model,
            "created_at": chat.created_at.isoformat(),
        }
        for chat in chats
    ]

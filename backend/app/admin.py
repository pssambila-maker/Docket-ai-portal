"""Admin API endpoints for user management and usage statistics."""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, ChatLog, UsageLog
from app.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# Schemas
class UserStats(BaseModel):
    id: int
    email: str
    role: str
    created_at: datetime
    total_requests: int
    total_tokens: int

    class Config:
        from_attributes = True


class UsageByModel(BaseModel):
    model: str
    request_count: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int


class UsageByUser(BaseModel):
    user_id: int
    email: str
    request_count: int
    total_tokens: int


class DailyUsage(BaseModel):
    date: str
    request_count: int
    total_tokens: int


class AdminStats(BaseModel):
    total_users: int
    total_requests: int
    total_tokens: int
    active_users_today: int
    requests_today: int
    tokens_today: int


class AdminDashboard(BaseModel):
    stats: AdminStats
    usage_by_model: List[UsageByModel]
    usage_by_user: List[UsageByUser]
    daily_usage: List[DailyUsage]


# Admin dependency
async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role for access."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/users", response_model=List[UserStats])
async def list_users(
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get all users with their usage stats."""
    users = db.query(User).all()

    result = []
    for user in users:
        # Get usage stats for this user
        usage_stats = db.query(
            func.count(UsageLog.id).label('total_requests'),
            func.coalesce(func.sum(UsageLog.total_tokens), 0).label('total_tokens')
        ).filter(UsageLog.user_id == user.id).first()

        result.append(UserStats(
            id=user.id,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
            total_requests=usage_stats.total_requests or 0,
            total_tokens=usage_stats.total_tokens or 0,
        ))

    return result


@router.get("/stats", response_model=AdminDashboard)
async def get_admin_stats(
    days: int = 7,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive admin statistics."""
    today = datetime.utcnow().date()
    start_date = today - timedelta(days=days)

    # Overall stats
    total_users = db.query(func.count(User.id)).scalar()
    total_requests = db.query(func.count(UsageLog.id)).scalar()
    total_tokens = db.query(func.coalesce(func.sum(UsageLog.total_tokens), 0)).scalar()

    # Today's stats
    today_start = datetime.combine(today, datetime.min.time())
    active_users_today = db.query(func.count(func.distinct(UsageLog.user_id))).filter(
        UsageLog.created_at >= today_start
    ).scalar()
    requests_today = db.query(func.count(UsageLog.id)).filter(
        UsageLog.created_at >= today_start
    ).scalar()
    tokens_today = db.query(func.coalesce(func.sum(UsageLog.total_tokens), 0)).filter(
        UsageLog.created_at >= today_start
    ).scalar()

    stats = AdminStats(
        total_users=total_users or 0,
        total_requests=total_requests or 0,
        total_tokens=total_tokens or 0,
        active_users_today=active_users_today or 0,
        requests_today=requests_today or 0,
        tokens_today=tokens_today or 0,
    )

    # Usage by model
    model_usage = db.query(
        UsageLog.model,
        func.count(UsageLog.id).label('request_count'),
        func.sum(UsageLog.total_tokens).label('total_tokens'),
        func.sum(UsageLog.prompt_tokens).label('prompt_tokens'),
        func.sum(UsageLog.completion_tokens).label('completion_tokens'),
    ).group_by(UsageLog.model).all()

    usage_by_model = [
        UsageByModel(
            model=m.model,
            request_count=m.request_count,
            total_tokens=m.total_tokens or 0,
            prompt_tokens=m.prompt_tokens or 0,
            completion_tokens=m.completion_tokens or 0,
        )
        for m in model_usage
    ]

    # Usage by user
    user_usage = db.query(
        UsageLog.user_id,
        User.email,
        func.count(UsageLog.id).label('request_count'),
        func.sum(UsageLog.total_tokens).label('total_tokens'),
    ).join(User, UsageLog.user_id == User.id).group_by(
        UsageLog.user_id, User.email
    ).order_by(func.sum(UsageLog.total_tokens).desc()).limit(10).all()

    usage_by_user = [
        UsageByUser(
            user_id=u.user_id,
            email=u.email,
            request_count=u.request_count,
            total_tokens=u.total_tokens or 0,
        )
        for u in user_usage
    ]

    # Daily usage for the last N days
    daily_usage_query = db.query(
        func.date(UsageLog.created_at).label('date'),
        func.count(UsageLog.id).label('request_count'),
        func.sum(UsageLog.total_tokens).label('total_tokens'),
    ).filter(
        UsageLog.created_at >= datetime.combine(start_date, datetime.min.time())
    ).group_by(func.date(UsageLog.created_at)).order_by(func.date(UsageLog.created_at)).all()

    daily_usage = [
        DailyUsage(
            date=str(d.date),
            request_count=d.request_count,
            total_tokens=d.total_tokens or 0,
        )
        for d in daily_usage_query
    ]

    return AdminDashboard(
        stats=stats,
        usage_by_model=usage_by_model,
        usage_by_user=usage_by_user,
        daily_usage=daily_usage,
    )


@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update a user's role."""
    if role not in ["user", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'user' or 'admin'"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent removing your own admin access
    if user.id == admin.id and role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin access"
        )

    user.role = role
    db.commit()

    logger.info(f"User {user_id} role updated to {role} by admin {admin.id}")
    return {"message": f"User role updated to {role}"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a user and their data."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete related data
    db.query(ChatLog).filter(ChatLog.user_id == user_id).delete()
    db.query(UsageLog).filter(UsageLog.user_id == user_id).delete()
    db.delete(user)
    db.commit()

    logger.info(f"User {user_id} deleted by admin {admin.id}")
    return {"message": "User deleted successfully"}

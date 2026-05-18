"""User 和 RoleBinding 数据库模型"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


# 角色到Agent的映射 — role名即Agent目录名
VALID_ROLES = ["presales", "pm", "product", "design", "architect", "frontend", "backend", "qa", "admin"]


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[str] = mapped_column(
        String(32), default=lambda: datetime.now().isoformat()
    )

    roles: Mapped[list["RoleBinding"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class RoleBinding(Base):
    __tablename__ = "role_bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="roles")

"""依赖注入 — 认证守卫、RBAC校验、引擎实例"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .models.user import User, RoleBinding
from .services.auth_service import decode_access_token

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """从JWT提取当前用户"""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的认证令牌")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """要求admin角色"""
    roles = [rb.role for rb in user.roles]
    if "admin" not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def require_role(role: str):
    """要求指定角色（工厂函数）"""
    def _check(user: User = Depends(get_current_user)) -> User:
        roles = [rb.role for rb in user.roles]
        if "admin" in roles or role in roles:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"需要 {role} 或 admin 角色",
        )
    return _check


def can_operate_agent(user: User, agent_name: str) -> bool:
    """检查用户是否有权操作指定Agent的资产"""
    roles = [rb.role for rb in user.roles]
    if "admin" in roles:
        return True
    return agent_name in roles

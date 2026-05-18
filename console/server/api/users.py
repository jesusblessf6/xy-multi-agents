"""用户管理 API — admin 专用"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.user import User, RoleBinding, VALID_ROLES
from ..services.auth_service import hash_password
from ..dependencies import get_current_user, require_admin

router = APIRouter()


class CreateUserRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""
    roles: list[str] = []


class UpdateUserRequest(BaseModel):
    display_name: str | None = None
    password: str | None = None
    roles: list[str] | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str
    roles: list[str]


@router.get("", response_model=list[UserResponse])
async def list_users(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users = db.query(User).all()
    return [
        UserResponse(
            id=u.id, username=u.username, display_name=u.display_name,
            roles=[rb.role for rb in u.roles],
        )
        for u in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    req: CreateUserRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    for role in req.roles:
        if role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail=f"无效角色: {role}")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        display_name=req.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    for role in req.roles:
        db.add(RoleBinding(user_id=user.id, role=role))
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id, username=user.username, display_name=user.display_name,
        roles=[rb.role for rb in user.roles],
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    req: UpdateUserRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if req.display_name is not None:
        user.display_name = req.display_name
    if req.password is not None:
        user.password_hash = hash_password(req.password)
    if req.roles is not None:
        for role in req.roles:
            if role not in VALID_ROLES:
                raise HTTPException(status_code=400, detail=f"无效角色: {role}")
        db.query(RoleBinding).filter(RoleBinding.user_id == user.id).delete()
        for role in req.roles:
            db.add(RoleBinding(user_id=user.id, role=role))

    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id, username=user.username, display_name=user.display_name,
        roles=[rb.role for rb in user.roles],
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    db.commit()

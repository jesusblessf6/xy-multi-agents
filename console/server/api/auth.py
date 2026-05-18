"""认证 API"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db import get_db
from ..models.user import User
from ..services.auth_service import create_access_token, verify_password
from ..dependencies import get_current_user

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str
    roles: list[str]


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    token = create_access_token({"sub": str(user.id)})
    return LoginResponse(access_token=token)


@router.get("/me", response_model=UserInfo)
async def get_me(user: User = Depends(get_current_user)):
    return UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        roles=[rb.role for rb in user.roles],
    )

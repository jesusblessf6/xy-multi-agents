"""Console API — 后台管理服务"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="XY Console API",
    description="后台管理 — 知识管理 + 评审审批",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from .api import auth, users, assets, reviews, projects, dashboard  # noqa: E402, F401

app.include_router(auth.router, prefix="/auth", tags=["认证"])
app.include_router(users.router, prefix="/users", tags=["用户管理"])
app.include_router(assets.router, prefix="/agents", tags=["资产管理"])
app.include_router(reviews.router, prefix="/reviews", tags=["评审"])
app.include_router(projects.router, prefix="/projects", tags=["项目"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])


@app.get("/health")
async def health():
    return {"status": "ok"}

"""Portal API — 前台需求管理 + 进度展示"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="XY Portal API",
    description="前台 — 需求提交、项目进度查看",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .api import requirements, projects, pipeline, agents  # noqa: E402, F401

app.include_router(requirements.router, prefix="/requirements", tags=["需求"])
app.include_router(projects.router, prefix="/projects", tags=["项目"])
app.include_router(pipeline.router, prefix="/pipeline", tags=["流水线"])
app.include_router(agents.router, prefix="/agents", tags=["Agent"])


@app.get("/health")
async def health():
    return {"status": "ok"}

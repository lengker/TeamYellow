# app/main.py
from fastapi import FastAPI
from app.api.v1 import recognize
from app.api.v1 import export # 导入你写的 export 模块

app = FastAPI(title="VHHH ATC Speech Analysis System")

@app.get("/")
async def root():
    return {"status": "running", "module": "A-3 Speech Pre-processing", "message": "API 服务已启动"}

# 统一在底部集中注册所有的路由模块
app.include_router(recognize.router, prefix="/api/v1", tags=["Speech Recognition"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Data Export"])
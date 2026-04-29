# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import recognize
from app.services.speech_service import SpeechService


# 动作三：引入全局 Lifespan 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 [生命周期] 正在启动服务，加载并锁死 ASR/VAD 模型单例...")
    # 将模型实例挂载到 FastAPI 的 app.state 上
    app.state.speech_handler = SpeechService()
    print("✅ [生命周期] 模型已就绪，内存池已稳定！")

    yield  # 这里是应用运行时的停顿点

    # 接收到关闭指令时，彻底释放内存
    print("🛑 [生命周期] 服务关闭，正在清空模型内存...")
    del app.state.speech_handler


# 挂载 lifespan
app = FastAPI(title="VHHH ATC Speech Analysis System", lifespan=lifespan)

# 注册路由
app.include_router(recognize.router, prefix="/api/v1", tags=["Speech Recognition"])


@app.get("/")
async def root():
    return {"status": "running", "module": "A-3 Speech Pre-processing", "message": "高性能内存优化版本已启动"}
# a3_speech_processing_3/app/api/v1/export.py - 适配新数据库设计
import os
import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.db.session import get_db
from app.db.crud import get_audio_records_by_strategy
from app.engine.export_engine import ExportEngine

router = APIRouter()
exporter = ExportEngine()

# --- 任务状态内存字典 (模拟 Redis 队列) ---
# 格式: { "task_id": {"status": "排队中/打包中/已完成/失败", "file_path": "...", "progress": 0} }
EXPORT_TASKS = {}


class ExportRequest(BaseModel):
    start_time: datetime
    end_time: datetime
    keyword: Optional[str] = None
    strategy_name: str = "custom_search"


def remove_temp_file(path: str, task_id: str):
    """延迟清理机制：文件下载完毕后，清理磁盘并注销内存任务"""
    if os.path.exists(path):
        os.remove(path)
        print(f"🧹 [资源释放] 已清理过期ZIP文件: {path}")
    if task_id in EXPORT_TASKS:
        del EXPORT_TASKS[task_id]
        print(f"🧹 [内存释放] 任务 {task_id} 生命周期结束，已注销。")


def run_export_worker(task_id: str, request: ExportRequest, db: Session):
    """
    [后台工作节点 Worker]
    独立执行数据库查询与打包，实现 CPU 资源隔离，不阻塞主服务
    """
    try:
        EXPORT_TASKS[task_id]["status"] = "打包中(数据检索)"
        EXPORT_TASKS[task_id]["progress"] = 20

        # 1. 数据库检索 (耗时操作)
        records = get_audio_records_by_strategy(
            db=db,
            start_time=request.start_time,
            end_time=request.end_time,
            keyword=request.keyword,
            limit=1000
        )

        if not records:
            EXPORT_TASKS[task_id]["status"] = "失败"
            EXPORT_TASKS[task_id]["message"] = "当前策略下未检索到音频数据"
            return

        EXPORT_TASKS[task_id]["status"] = "打包中(压缩写入)"
        EXPORT_TASKS[task_id]["progress"] = 60

        # 2. 调用 Engine 层进行 ZIP 压缩 (IO密集型操作)
        zip_path = exporter.create_export_package(records, strategy_name=request.strategy_name)

        # 3. 任务完成，写入最终状态
        EXPORT_TASKS[task_id]["status"] = "已完成"
        EXPORT_TASKS[task_id]["progress"] = 100
        EXPORT_TASKS[task_id]["file_path"] = zip_path
        print(f"✅ [异步任务] 任务 {task_id} 处理完毕，等待前端拉取。")

    except Exception as e:
        print(f"❌ [异步任务] 处理异常: {str(e)}")
        EXPORT_TASKS[task_id]["status"] = "失败"
        EXPORT_TASKS[task_id]["message"] = f"服务器内部错误: {str(e)}"


# ==============================================================
#  API 1: 提交异步导出任务 (秒回 Task ID)
# ==============================================================
@router.post("/strategy/submit")
async def submit_export_task(
        request: ExportRequest,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_db)
):
    # 生成唯一任务 ID
    task_id = str(uuid.uuid4())

    # 初始化任务状态
    EXPORT_TASKS[task_id] = {
        "status": "排队中",
        "progress": 0,
        "file_path": None,
        "message": ""
    }

    # 将繁重任务推入后台队列
    background_tasks.add_task(run_export_worker, task_id, request, db)

    return {
        "code": 200,
        "message": "导出任务已成功派发至后台",
        "task_id": task_id
    }


# ==============================================================
#  API 2: 状态轮询接口 (解决前端接口假死)
# ==============================================================
@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    if task_id not in EXPORT_TASKS:
        raise HTTPException(status_code=404, detail="任务ID不存在或已过期失效")

    task_info = EXPORT_TASKS[task_id]
    return {
        "code": 200,
        "task_id": task_id,
        "status": task_info["status"],
        "progress": task_info["progress"],
        "message": task_info.get("message", "")
    }


# ==============================================================
#  API 3: 延迟下载与清理接口
# ==============================================================
@router.get("/download/{task_id}")
async def download_exported_file(task_id: str, background_tasks: BackgroundTasks):
    task_info = EXPORT_TASKS.get(task_id)

    if not task_info or task_info["status"] != "已完成":
        raise HTTPException(status_code=400, detail="打包任务尚未完成或已失败")

    file_path = task_info["file_path"]
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="导出文件已过期被清理或丢失")

    # 核心设计：前端只要调用了下载，就在后台触发“延迟清理”，保护硬盘不被挤爆
    background_tasks.add_task(remove_temp_file, file_path, task_id)

    return FileResponse(
        path=file_path,
        filename=os.path.basename(file_path),
        media_type="application/x-zip-compressed"
    )
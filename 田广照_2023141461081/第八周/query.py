"""
时序检索接口 (RQ-A-3-30) - 适配新数据库设计
支持按时间范围、关键词进行地空通话检索
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.db.session import get_db
from app.engine.query_engine import (
    QueryEngine,
    TimeRangeResponse,
    AudioDetailResponse,
    get_query_engine
)

router = APIRouter()


@router.get("/", response_model=TimeRangeResponse)
async def query_timestamps(
    start_time: datetime = Query(..., description="开始时间 (ISO 8601 格式, 如: 2024-01-01T00:00:00)"),
    end_time: datetime = Query(..., description="结束时间 (ISO 8601 格式, 如: 2024-01-01T23:59:59)"),
    keyword: Optional[str] = Query(None, description="关键词搜索 (模糊匹配文件名或源URL)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db)
):
    """
    时序检索接口 - 按时间范围查询地空通话记录

    支持功能：
    - 按起止时间范围查询
    - 关键词模糊搜索
    - 分页返回结果

    示例请求：
    ```
    GET /api/v1/query/?start_time=2024-01-01T00:00:00&end_time=2024-01-01T23:59:59&keyword=landing&page=1&page_size=20
    ```
    """
    # 参数校验
    if start_time >= end_time:
        raise HTTPException(status_code=400, detail="开始时间必须早于结束时间")

    # 使用查询引擎执行搜索
    engine = get_query_engine(db)
    return engine.search_audio_records(
        start_time=start_time,
        end_time=end_time,
        keyword=keyword,
        page=page,
        page_size=page_size
    )


@router.get("/detail/{audio_id}", response_model=AudioDetailResponse)
async def get_record_detail(
    audio_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单条语音记录的详细信息

    包含：
    - 基础文件信息
    - 音频元数据
    - 标注片段列表 (如果有)
    """
    engine = get_query_engine(db)
    result = engine.get_record_detail(audio_id)

    if not result:
        raise HTTPException(status_code=404, detail=f"音频ID {audio_id} 不存在")

    return result
"""
时序检索引擎 (Query Engine)
整合数据模型、CRUD操作和查询逻辑
"""
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional, Tuple

from app.db.models import LngAudioRecords


# ==================== 数据模型 ====================

class AudioRecordItem(BaseModel):
    """单条语音记录"""
    id: int
    file_name: str
    file_path: str
    duration: Optional[float]
    asr_content: Optional[str]
    ground_truth: Optional[str]
    channel: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TimeRangeResponse(BaseModel):
    """时序检索响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页条数")
    data: List[AudioRecordItem] = Field(..., description="语音记录列表")


class TimestampSegment(BaseModel):
    """时间戳片段"""
    start_time: float = Field(..., description="开始时间(秒)")
    end_time: float = Field(..., description="结束时间(秒)")
    text: str = Field(..., description="转写文本")
    speaker: Optional[str] = Field(None, description="说话人标识")


class AudioDetailResponse(BaseModel):
    """音频详情响应"""
    id: int
    file_name: str
    duration: Optional[float]
    asr_content: Optional[str]
    channel: Optional[str]
    created_at: datetime
    segments: List[TimestampSegment] = Field([], description="时间戳片段列表")


# ==================== 查询引擎 ====================

class QueryEngine:
    """
    时序检索引擎
    封装所有查询相关的业务逻辑
    """

    def __init__(self, db: Session):
        self.db = db

    def search_audio_records(
        self,
        start_time: datetime,
        end_time: datetime,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> TimeRangeResponse:
        """
        高级时序检索：支持关键词过滤

        Args:
            start_time: 开始时间
            end_time: 结束时间
            keyword: 关键词 (模糊匹配ASR内容)
            page: 页码
            page_size: 每页条数

        Returns:
            TimeRangeResponse 包含总数和分页数据
        """
        # 计算分页偏移
        skip = (page - 1) * page_size

        # 构建基础查询
        query = self.db.query(LngAudioRecords).filter(
            and_(
                LngAudioRecords.created_at >= start_time,
                LngAudioRecords.created_at <= end_time
            )
        )

        # 关键词过滤
        if keyword:
            query = query.filter(LngAudioRecords.asr_content.ilike(f"%{keyword}%"))

        # 先获取总数
        total = query.count()

        # 再获取分页数据 (按时间倒序)
        records = query.order_by(
            LngAudioRecords.created_at.desc()
        ).offset(skip).limit(page_size).all()

        # 转换为响应模型
        data = [AudioRecordItem.model_validate(record) for record in records]

        return TimeRangeResponse(
            total=total,
            page=page,
            page_size=page_size,
            data=data
        )

    def get_record_by_id(self, record_id: int) -> Optional[LngAudioRecords]:
        """根据ID获取单条记录"""
        return self.db.query(LngAudioRecords).filter(
            LngAudioRecords.id == record_id
        ).first()

    def get_record_detail(self, record_id: int) -> Optional[AudioDetailResponse]:
        """
        获取单条语音记录的详细信息

        Returns:
            AudioDetailResponse 或 None (记录不存在)
        """
        record = self.get_record_by_id(record_id)

        if not record:
            return None

        return AudioDetailResponse(
            id=record.id,
            file_name=record.file_name,
            duration=record.duration,
            asr_content=record.asr_content,
            channel=record.channel,
            created_at=record.created_at,
            segments=[]  # TODO: 后续可从 timestamps 表关联获取
        )


# ==================== 便捷函数 ====================

def get_query_engine(db: Session) -> QueryEngine:
    """获取查询引擎实例"""
    return QueryEngine(db)

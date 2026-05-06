"""
数据库 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional

from app.db.models import (
    LngAudioRecords, LngAnnotations
)


# LNG_AUDIO_RECORDS CRUD
def create_audio_record(db: Session, audio_data: dict) -> LngAudioRecords:
    """创建音频记录"""
    db_audio = LngAudioRecords(**audio_data)
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio


def get_audio_record(db: Session, audio_id: int) -> Optional[LngAudioRecords]:
    """根据音频ID获取音频信息"""
    return db.query(LngAudioRecords).filter(LngAudioRecords.audio_id == audio_id).first()


def get_audio_records_by_strategy(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 1000
) -> List[LngAudioRecords]:
    """
    策略检索：按时间范围、文本关键字对音频记录进行检索
    """
    query = db.query(LngAudioRecords).filter(
        and_(
            LngAudioRecords.start_time_utc >= start_time,
            LngAudioRecords.end_time_utc <= end_time
        )
    )

    if keyword:
        # 根据识别结果文本(asr_content)进行过滤
        query = query.join(LngAnnotations).filter(
            LngAnnotations.asr_content.ilike(f"%{keyword}%")
        )

    return query.offset(skip).limit(limit).all()


# LNG_ANNOTATIONS CRUD
def create_annotation(db: Session, annotation_data: dict) -> LngAnnotations:
    """创建标注记录"""
    db_annotation = LngAnnotations(**annotation_data)
    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)
    return db_annotation


def get_annotations_by_audio(db: Session, audio_id: int) -> List[LngAnnotations]:
    """根据音频ID获取标注列表"""
    return db.query(LngAnnotations).filter(LngAnnotations.audio_id == audio_id).all()
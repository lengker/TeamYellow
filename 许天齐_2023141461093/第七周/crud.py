"""
数据库 CRUD 操作
"""
from sqlalchemy.orm import Session
from app.db import models
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from app.db.models import LngAudioRecords, LngTracks


# AudioFile CRUD
def create_audio_file(db: Session, filename: str, file_path: str, duration: float = None, sample_rate: int = None):
    db_audio = models.AudioFile(filename=filename, file_path=file_path, duration=duration, sample_rate=sample_rate)
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio


def get_audio_file(db: Session, audio_file_id: int) -> Optional[models.AudioFile]:
    return db.query(models.AudioFile).filter(models.AudioFile.id == audio_file_id).first()


def get_audio_files(db: Session, skip: int = 0, limit: int = 100) -> List[models.AudioFile]:
    return db.query(models.AudioFile).offset(skip).limit(limit).all()


def delete_audio_file(db: Session, audio_file_id: int):
    db_audio = db.query(models.AudioFile).filter(models.AudioFile.id == audio_file_id).first()
    if db_audio:
        db.delete(db_audio)
        db.commit()
    return db_audio


# Transcription CRUD
def create_transcription(db: Session, audio_file_id: int, text: str, language: str = None, confidence: float = None):
    db_trans = models.Transcription(
        audio_file_id=audio_file_id,
        text=text,
        language=language,
        confidence=confidence
    )
    db.add(db_trans)
    db.commit()
    db.refresh(db_trans)
    return db_trans


def get_transcription(db: Session, transcription_id: int) -> Optional[models.Transcription]:
    return db.query(models.Transcription).filter(models.Transcription.id == transcription_id).first()


def get_transcriptions_by_audio(db: Session, audio_file_id: int) -> List[models.Transcription]:
    return db.query(models.Transcription).filter(models.Transcription.audio_file_id == audio_file_id).all()


# Timestamp CRUD
def create_timestamp(db: Session, transcription_id: int, start_time: float, end_time: float, text: str, speaker: str = None):
    db_ts = models.Timestamp(
        transcription_id=transcription_id,
        start_time=start_time,
        end_time=end_time,
        text=text,
        speaker=speaker
    )
    db.add(db_ts)
    db.commit()
    db.refresh(db_ts)
    return db_ts


def get_timestamps_by_transcription(db: Session, transcription_id: int) -> List[models.Timestamp]:
    return db.query(models.Timestamp).filter(models.Timestamp.transcription_id == transcription_id).all()


def get_timestamps_by_time_range(db: Session, start: float, end: float) -> List[models.Timestamp]:
    return db.query(models.Timestamp).filter(
        models.Timestamp.start_time >= start,
        models.Timestamp.end_time <= end
    ).all()


# Strategy CRUD
def create_strategy(db: Session, name: str, description: str = None, rules: str = None):
    db_strategy = models.Strategy(name=name, description=description, rules=rules)
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    return db_strategy


def get_strategy(db: Session, strategy_id: int) -> Optional[models.Strategy]:
    return db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()


def get_strategies(db: Session, skip: int = 0, limit: int = 100) -> List[models.Strategy]:
    return db.query(models.Strategy).offset(skip).limit(limit).all()


def update_strategy(db: Session, strategy_id: int, **kwargs):
    db_strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    if db_strategy:
        for key, value in kwargs.items():
            setattr(db_strategy, key, value)
        db.commit()
        db.refresh(db_strategy)
    return db_strategy


def delete_strategy(db: Session, strategy_id: int):
    db_strategy = db.query(models.Strategy).filter(models.Strategy.id == strategy_id).first()
    if db_strategy:
        db.delete(db_strategy)
        db.commit()
    return db_strategy



def create_audio_record(db: Session, record_data: dict) -> LngAudioRecords:
    """
    新建一条语音识别记录
    :param db: 数据库会话 (由连接池生成)
    :param record_data: 包含文件信息的字典
    """
    db_record = LngAudioRecords(**record_data)
    db.add(db_record)
    db.commit()
    db.refresh(db_record) # 刷新以获取数据库自增的 ID
    return db_record

def get_audio_record_by_id(db: Session, record_id: int):
    """根据 ID 查询单条语音记录"""
    return db.query(LngAudioRecords).filter(LngAudioRecords.id == record_id).first()

def get_audio_records_by_time_range(db: Session, start_time: datetime, end_time: datetime, skip: int = 0, limit: int = 20):
    """
    对标接口文档 RQ-A-3-30：按起止时间查询地空通话
    包含分页逻辑 (skip, limit)
    """
    return db.query(LngAudioRecords).filter(
        and_(
            LngAudioRecords.created_at >= start_time,
            LngAudioRecords.created_at <= end_time
        )
    ).offset(skip).limit(limit).all()

# ==========================================
# LngTracks (航迹表) 相关 DAO 操作
# ==========================================

def create_track(db: Session, track_data: dict) -> LngTracks:
    """写入一条航迹数据"""
    db_track = LngTracks(**track_data)
    db.add(db_track)
    db.commit()
    db.refresh(db_track)
    return db_track

def get_audio_records_by_strategy(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        channel: Optional[str] = None,
        keyword: Optional[str] = None,
        skip: int = 0,
        limit: int = 1000
) -> List[LngAudioRecords]:
    """
    [第七周任务: 策略检索底层 DAO]
    复合查询：按时间范围、频道、文本关键字对 LNG_AUDIO_RECORDS 进行精准检索。
    """
    # 基础条件：时间范围是硬性过滤
    query = db.query(LngAudioRecords).filter(
        and_(
            LngAudioRecords.created_at >= start_time,
            LngAudioRecords.created_at <= end_time
        )
    )

    # 动态追加条件：如果传了频道，则过滤频道
    if channel:
        query = query.filter(LngAudioRecords.channel == channel)

    # 动态追加条件：如果传了关键字，则在 asr_content 中进行模糊搜索
    if keyword:
        # 使用 ilike 进行忽略大小写的模糊匹配
        query = query.filter(LngAudioRecords.asr_content.ilike(f"%{keyword}%"))

    # 执行分页并返回结果
    return query.offset(skip).limit(limit).all()
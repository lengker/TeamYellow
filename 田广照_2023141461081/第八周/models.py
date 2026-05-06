"""
定义数据库表结构 - 仅保留与export/query/recognize接口相关的表
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class LngAirports(Base):
    """
    LNG_AIRPORTS（机场表）
    """
    __tablename__ = "LNG_AIRPORTS"

    airport_code = Column(String(10), primary_key=True)
    name = Column(String(255), nullable=False)
    country_code = Column(String(3), nullable=True)
    airports_latitude = Column(Float, nullable=False)
    airports_longitude = Column(Float, nullable=False)


class LngUsers(Base):
    """
    LNG_USERS（用户表）
    """
    __tablename__ = "LNG_USERS"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)


class LngTracks(Base):
    """
    LNG_TRACKS（航迹表）
    """
    __tablename__ = "LNG_TRACKS"

    track_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    flight_id = Column(String(20), nullable=False)
    tracks_latitude = Column(Float, nullable=False)
    tracks_longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    speed = Column(Float, nullable=True)
    heading = Column(Float, nullable=True)
    departure_airport_code = Column(String(10), ForeignKey("LNG_AIRPORTS.airport_code"), nullable=True)
    arrival_airport_code = Column(String(10), ForeignKey("LNG_AIRPORTS.airport_code"), nullable=True)
    next_id = Column(Integer, ForeignKey("LNG_TRACKS.track_id"), nullable=True)
    prev_id = Column(Integer, ForeignKey("LNG_TRACKS.track_id"), nullable=True)

    departure_airport = relationship("LngAirports", foreign_keys=[departure_airport_code])
    arrival_airport = relationship("LngAirports", foreign_keys=[arrival_airport_code])
    next_track = relationship("LngTracks", foreign_keys=[next_id], remote_side=[track_id])
    prev_track = relationship("LngTracks", foreign_keys=[prev_id], remote_side=[track_id])


class LngAudioRecords(Base):
    """
    LNG_AUDIO_RECORDS（音频表）
    """
    __tablename__ = "LNG_AUDIO_RECORDS"

    audio_id = Column(Integer, primary_key=True, autoincrement=True)
    source_url = Column(String(500), nullable=False)
    start_time_utc = Column(DateTime, nullable=False)
    end_time_utc = Column(DateTime, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    status = Column(Integer, default=0)
    last_access_at = Column(DateTime, default=datetime.utcnow)
    track_id = Column(Integer, ForeignKey("LNG_TRACKS.track_id"), nullable=False)
    next_id = Column(Integer, ForeignKey("LNG_AUDIO_RECORDS.audio_id"), nullable=True)
    prev_id = Column(Integer, ForeignKey("LNG_AUDIO_RECORDS.audio_id"), nullable=True)

    track = relationship("LngTracks")
    next_audio = relationship("LngAudioRecords", foreign_keys=[next_id], remote_side=[audio_id])
    prev_audio = relationship("LngAudioRecords", foreign_keys=[prev_id], remote_side=[audio_id])

    __table_args__ = (
        CheckConstraint('end_time_utc >= start_time_utc', name='check_audio_time_range'),
        CheckConstraint('status IN (0, 1, 2, 3)', name='check_audio_status'),
    )


class LngAnnotations(Base):
    """
    LNG_ANNOTATIONS（标注表）
    """
    __tablename__ = "LNG_ANNOTATIONS"

    annotation_id = Column(Integer, primary_key=True, autoincrement=True)
    label_type = Column(String(100), nullable=True)
    author_id = Column(Integer, ForeignKey("LNG_USERS.user_id"), nullable=False)
    audio_id = Column(Integer, ForeignKey("LNG_AUDIO_RECORDS.audio_id"), nullable=False)
    relative_start = Column(Float, nullable=False)
    relative_end = Column(Float, nullable=False)
    abs_start_time = Column(DateTime, nullable=False)
    abs_end_time = Column(DateTime, nullable=False)
    asr_content = Column(Text, nullable=True)
    vad_confidence = Column(Float, nullable=True)
    is_annotated = Column(Integer, default=0)
    annotation_text = Column(Text, nullable=True)
    annotation_time = Column(DateTime, nullable=True)
    storage_tag = Column(String(100), nullable=True)
    next_id = Column(Integer, ForeignKey("LNG_ANNOTATIONS.annotation_id"), nullable=True)
    prev_id = Column(Integer, ForeignKey("LNG_ANNOTATIONS.annotation_id"), nullable=True)

    author = relationship("LngUsers")
    audio = relationship("LngAudioRecords")
    next_annotation = relationship("LngAnnotations", foreign_keys=[next_id], remote_side=[annotation_id])
    prev_annotation = relationship("LngAnnotations", foreign_keys=[prev_id], remote_side=[annotation_id])

    __table_args__ = (
        CheckConstraint('relative_start <= relative_end', name='check_relative_time_range'),
        CheckConstraint('abs_end_time >= abs_start_time', name='check_abs_time_range'),
        CheckConstraint('is_annotated IN (0, 1)', name='check_is_annotated'),
    )


class LngVspData(Base):
    """
    LNG_VSP_DATA（VSP数据表）
    """
    __tablename__ = "LNG_VSP_DATA"

    vsp_id = Column(Integer, primary_key=True, autoincrement=True)
    airport_code = Column(String(10), ForeignKey("LNG_AIRPORTS.airport_code"), nullable=False)
    region = Column(String(100), nullable=True)
    runway = Column(String(50), nullable=True)
    taxiway = Column(String(50), nullable=True)
    vor_id = Column(String(50), nullable=True)
    waypoint = Column(String(50), nullable=True)
    approach_type = Column(String(50), nullable=True)
    gate = Column(String(50), nullable=True)
    holding_point = Column(String(50), nullable=True)
    sector_name = Column(String(100), nullable=True)

    airport = relationship("LngAirports")


class LngStorageLog(Base):
    """
    LNG_STORAGE_LOG（存储日志表）
    """
    __tablename__ = "LNG_STORAGE_LOG"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_type = Column(String(20), nullable=False)
    source_url = Column(String(500), nullable=False)
    released_space = Column(Integer, nullable=False)
    op_time = Column(DateTime, default=datetime.utcnow, nullable=False)

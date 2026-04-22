# a3_speech_processing_1/app/services/speech_service.py
import os
import re
from sqlalchemy.orm import Session
from app.engine.vad_processor import VADEngine
from app.engine.sense_voice import ASREngine
from app.db.crud import create_audio_record


class SpeechService:
    def __init__(self):
        self.vad = VADEngine(top_db=20)
        self.asr = ASREngine()

    def extract_callsign(self, text: str) -> str:
        """
        [任务 1: 结构化解析]
        从 ASR 文本中提取潜在的航班呼号 (简易正则版)。
        真实业务中，这一步可能需要调用单独的 NER (命名实体识别) 模型。
        """
        if not text:
            return ""
        # 简单正则：匹配连续的大写字母加数字，例如 "CPA123", "CCA456"
        match = re.search(r'([A-Z]{2,3}\d{2,4})', text)
        if match:
            return match.group(1)
        return ""

    def validate_asr_result(self, text: str, duration: float) -> bool:
        """
        [任务 3: 数据异常校验与容错测试]
        拦截由于底噪过大导致的无意义识别结果。
        """
        # 容错规则 1: 空文本拦截
        if not text or text.strip() == "":
            return False

        # 容错规则 2: 过短且无意义的单字拦截 (例如只识别出一个 "啊" 或 "the")
        if duration > 2.0 and len(text.strip()) <= 2:
            return False

        return True

    def process_and_save_audio(self, db: Session, file_path: str, channel: str = "APP"):
        """
        [任务 2: 入库业务逻辑开发]
        核心业务流：VAD -> ASR -> 校验 -> 结构化入库
        """
        print(f"========== 开始处理并入库任务: {file_path} ==========")

        segments = self.vad.process(file_path)
        saved_results = []

        for i, seg in enumerate(segments):
            # 1. 引擎识别
            raw_text = self.asr.recognize(seg["audio_data"])
            duration = seg["end_time"] - seg["start_time"]

            # 2. 容错校验 (拦截脏数据)
            if not self.validate_asr_result(raw_text, duration):
                print(f"⚠️ [拦截] 片段 {i} 识别无效或被判定为底噪: '{raw_text}'")
                continue  # 跳过该片段，不入库

            # 3. 结构化解析 (提取呼号)
            callsign = self.extract_callsign(raw_text)

            print(f"✅ [{seg['start_time']:.2f}s - {seg['end_time']:.2f}s] [呼号:{callsign}] : {raw_text}")

            # 4. 组装标准 DTO (入库数据结构)
            record_data = {
                "file_name": f"{os.path.basename(file_path)}_seg{i}",
                "file_path": file_path,
                "duration": round(duration, 2),
                "asr_content": raw_text,
                "channel": channel
            }

            # 5. 安全写入数据库 (依赖 DAO 层)
            try:
                saved_record = create_audio_record(db=db, record_data=record_data)

                saved_results.append({
                    "db_id": saved_record.id,
                    "text": raw_text,
                    "callsign": callsign,  # 携带结构化信息返回
                    "start": seg["start_time"],
                    "end": seg["end_time"]
                })
            except Exception as e:
                print(f"❌ [入库失败] 数据库写入异常: {str(e)}")
                # 记录日志，但不中断整个文件的处理进程

        print(f"========== 任务完成！有效片段入库 {len(saved_results)} 条 ==========")
        return saved_results
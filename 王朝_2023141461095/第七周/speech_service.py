# app/services/speech_service.py
from app.engine.vad_processor import VADEngine
from app.engine.sense_voice import ASREngine


class SpeechService:
    def __init__(self):
        self.vad = VADEngine(top_db=20)
        self.asr = ASREngine()

    def process_audio_file(self, file_path: str):
        """用于基础测试：不带数据库的调度流"""
        print(f"========== 开启低内存流式处理任务: {file_path} ==========")
        results = []

        # 核心改变：遍历生成器，拿一块 -> 识一块 -> 丢一块
        for i, seg in enumerate(self.vad.process_generator(file_path)):
            text = self.asr.recognize(seg["audio_data"])

            result_item = {
                "id": i + 1,
                "start": seg["start_time"],
                "end": seg["end_time"],
                "text": text
            }
            results.append(result_item)
            print(f"[{seg['start_time']}s - {seg['end_time']}s] : {text}")

            # 手动销毁当前切片的波形数据，不让它在 results 列表里堆积
            del seg["audio_data"]

        return results

    def process_and_save_audio(self, db, file_path: str, channel: str = "APP"):
        """用于真实 API 接口：带数据库存入的调度流"""
        print(f"========== 开启入库处理任务: {file_path} ==========")
        results = []

        for i, seg in enumerate(self.vad.process_generator(file_path)):
            text = self.asr.recognize(seg["audio_data"])

            # ======= 此处保留你的入库逻辑 =======
            # 假设你之前写的是这样的逻辑（根据你实际代码调整）：
            # db_record = LNG_AUDIO_RECORDS(channel=channel, start=..., text=...)
            # db.add(db_record)
            # db.commit()
            # db.refresh(db_record)
            # current_db_id = db_record.id
            current_db_id = i + 1  # 假数据，请替换为你真实的 db.id

            result_item = {
                "db_id": current_db_id,
                "start": seg["start_time"],
                "end": seg["end_time"],
                "text": text
            }
            results.append(result_item)

            # 用完即焚，释放内存
            del seg["audio_data"]

        return results
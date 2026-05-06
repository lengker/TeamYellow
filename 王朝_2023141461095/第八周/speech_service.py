import os
import re
import gc
from sqlalchemy.orm import Session
from app.engine.vad_processor import VADEngine
from app.engine.sense_voice import ASREngine
from app.db.crud import create_audio_record

class SpeechService:
    def __init__(self):
        self.vad = VADEngine(top_db=20)
        self.asr = ASREngine()

    def extract_callsign(self, text: str) -> str:
        """[任务 1: 结构化解析] 提取航班呼号"""
        if not text: return ""
        # 匹配大写字母+数字，如 CPA123
        match = re.search(r'([A-Z]{2,3}\d{2,4})', text)
        return match.group(1) if match else ""

    def validate_asr_result(self, text: str, duration: float) -> bool:
        """[任务 3: 数据异常校验] 拦截底噪导致的脏数据"""
        if not text or text.strip() == "": return False
        # 逻辑：时间挺长但没识别出几个字，通常是电流声杂音
        if duration > 2.0 and len(text.strip()) <= 2: return False
        return True

    def clean_vhhh_text(self, text: str) -> str:
        """
        [W8 核心任务: 真实场景数据清洗]
        因为 VHHH 是纯英文环境，SenseVoice 在遇到电台底噪时极易产生中日韩乱码。
        此函数将强行剔除所有非 ASCII 字符，只保留英文、数字和基础标点。
        """
        if not text:
            return ""
        # 魔法正则：[^\x00-\x7F]+ 代表所有非 ASCII 字符（中文、日文假名等）
        # 我们把它们全部替换成空字符串
        cleaned_text = re.sub(r'[^\x00-\x7F]+', '', text)
        return cleaned_text.strip()

    def process_and_save_audio(self, db: Session, file_path: str, channel: str = "APP"):
        """
        [V2 优化版核心流]
        1. 增加 channel 参数防止报错
        2. 使用 process_generator 节省内存
        3. 增加 try-finally 资源回收
        """
        print(f"========== 开始处理并入库任务: {file_path} ==========")
        saved_results = []

        # 使用生成器模式，一次只处理一个片段，内存恒定
        for i, seg in enumerate(self.vad.process_generator(file_path)):
            raw_text = ""
            try:
                # 1. 引擎识别 (这步可能会产生日文乱码)
                raw_text = self.asr.recognize(seg["audio_data"])

                # 2. 【W8 新增逻辑】: VHHH 纯英文清洗
                clean_text = self.clean_vhhh_text(raw_text)
                duration = seg["end_time"] - seg["start_time"]

                # 3. 容错校验 (注意：现在用清洗后的 clean_text 来校验)
                # 如果一段声音洗完之后连一个英文字母都不剩了，那就说明纯粹是噪音！
                if not self.validate_asr_result(clean_text, duration):
                    print(f"⚠️ [拦截] 片段 {i} 判定为底噪或被清洗为空，直接丢弃: (原音:{raw_text})")
                    continue

                # 4. 结构化解析与入库 (后面的代码继续用 clean_text)
                callsign = self.extract_callsign(clean_text)

                record_data = {
                    "file_name": f"{os.path.basename(file_path)}_seg{i}",
                    "file_path": file_path,
                    "duration": round(duration, 2),
                    "asr_content": clean_text,  # 存入干净的文本
                    # "channel": channel # 根据你之前和天齐的沟通决定是否打开
                }

                saved_record = create_audio_record(db=db, record_data=record_data)

                saved_results.append({
                    "db_id": saved_record.id,
                    "text": raw_text,
                    "callsign": callsign,
                    "start": seg["start_time"],
                    "end": seg["end_time"]
                })
                print(f"✅ [{seg['start_time']:.2f}s] 入库成功: {clean_text}")

            except Exception as e:
                print(f"❌ [片段处理失败] : {str(e)}")
            finally:
                # 【核心内存优化】处理完一个片段，立刻从内存抹除波形数据
                if "audio_data" in seg:
                    del seg["audio_data"]
                gc.collect() # 强制加速垃圾回收

        print(f"========== 任务完成！共入库 {len(saved_results)} 条记录 ==========")
        return saved_results
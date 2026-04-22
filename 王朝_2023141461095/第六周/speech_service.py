from engine.vad_engine import VADEngine
from engine.asr_engine import ASREngine

class SpeechService:
    def __init__(self):
        # 服务启动时，把两个引擎都预热好
        self.vad = VADEngine(top_db=20)
        self.asr = ASREngine()

    def process_audio_file(self, file_path: str):
        print(f"========== 开始处理任务: {file_path} ==========")

        # 1. 先过 VAD，拿到切好的片段
        segments = self.vad.process(file_path)

        results = []
        # 2. 遍历每一个有效片段，送给 ASR 去听写
        for i, seg in enumerate(segments):
            text = self.asr.recognize(seg["audio_data"])

            # 组装最终结果
            result_item = {
                "id": i + 1,
                "start": seg["start_time"],
                "end": seg["end_time"],
                "text": text
            }
            results.append(result_item)

            # 实时打印进度
            print(f"[{seg['start_time']}s - {seg['end_time']}s] : {text}")

        return results


# 测试运行逻辑（你可以直接运行这个脚本看效果）
if __name__ == "__main__":
    service = SpeechService()
    # 找一段真实的长录音测试
    # service.process_audio_file("../../storage/test_long_audio.wav")
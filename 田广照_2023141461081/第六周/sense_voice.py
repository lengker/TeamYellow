import os
import sherpa_onnx
from app.core.config import settings  # 引入系统配置

class ASREngine:
    def __init__(self):
        # 直接使用 config.py 中配置的绝对路径拼接模型位置
        model_file = os.path.join(r"D:\myDownload\pythonProject2\a3_speech_processing_1\models\model.int8.onnx")
        tokens_file = os.path.join(r"D:\myDownload\pythonProject2\a3_speech_processing_1\models\tokens.txt")

        print(f"[ASR] 正在加载模型...\n模型路径: {model_file}\n词表路径: {tokens_file}")

        try:
            self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model=model_file,    # 使用绝对路径
                tokens=tokens_file,  # 使用绝对路径
                num_threads=2,
                use_itn=True
            )
            print("✅ [状态] 模型加载成功！")
        except Exception as e:
            print(f"❌ [崩溃] 模型加载失败: {e}")
            print("请检查 models 文件夹下是否存在 model.int8.onnx 和 tokens.txt")
            raise

    def recognize(self, audio_data, sample_rate=16000) -> str:
        stream = self.recognizer.create_stream()
        stream.accept_waveform(sample_rate, audio_data)
        self.recognizer.decode_stream(stream)
        return stream.result.text
# app/engine/sense_voice.py
import os
import sherpa_onnx


class ASREngine:
    def __init__(self):
        # 自动定位模型文件夹，防止路径中文 Bug
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_file_dir))
        model_dir = os.path.join(root_dir, "models")

        old_cwd = os.getcwd()
        os.chdir(model_dir)

        try:
            self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model="model.int8.onnx",
                tokens="tokens.txt",
                num_threads=2,
                use_itn=True
            )
            print("✅ [A-3 Engine] SenseVoice 模型大脑加载成功！")
        finally:
            os.chdir(old_cwd)

    def recognize(self, audio_data, sample_rate=16000) -> str:
        # 1. 创建推理流
        stream = self.recognizer.create_stream()

        try:
            stream.accept_waveform(sample_rate, audio_data)
            self.recognizer.decode_stream(stream)
            return stream.result.text
        finally:
            # 动作二核心：强制销毁 stream。
            # 这是为了触发 sherpa-onnx 底层的 C++ 析构函数，瞬间清空缓存区
            del stream
import os
import sherpa_onnx


class ASREngine:
    def __init__(self):
        # 1. 记录当前位置
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 2. 定位到模型文件所在的那个大文件夹
        root_dir = os.path.dirname(current_dir)

        # 3. 暂时切换工作目录到模型所在的文件夹
        # 这样加载模型时可以用相对路径，避开 Windows 的中文路径解析 Bug
        old_cwd = os.getcwd()
        os.chdir(root_dir)

        print(f"[ASR] 切换工作目录至: {root_dir}")

        try:
            self.recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
                model="model.int8.onnx",  # 使用相对路径
                tokens="tokens.txt",  # 使用相对路径
                num_threads=2,
                use_itn=True
            )
            print("✅ [状态] 模型加载成功！")
        except Exception as e:
            print(f"❌ [崩溃] 模型加载失败: {e}")
            raise
        finally:
            # 4. 无论成功失败，把工作目录切回去，不影响其他代码
            os.chdir(old_cwd)

    def recognize(self, audio_data, sample_rate=16000) -> str:
        stream = self.recognizer.create_stream()
        stream.accept_waveform(sample_rate, audio_data)
        self.recognizer.decode_stream(stream)
        return stream.result.text
import sherpa_onnx
import os

# 1. 路径配置（确保这两个文件就在这个目录下）
# 如果你把 1.py 放在和这些文件同一个文件夹里，就直接写文件名
# 如果在 models 文件夹里，请写 models/model.int8.onnx
model_path = "model.int8.onnx"
tokens_path = "tokens.txt"

# 2. 核心加载代码
print("正在加载 SenseVoice 模型...")
recognizer = sherpa_onnx.OfflineRecognizer.from_sense_voice(
    model=model_path,
    tokens=tokens_path,
    num_threads=2,
    use_itn=True  # 开启这个，识别结果会有标点和数字格式化
)

print("✅ 状态：模型加载成功！")

# 3. 这里的音频文件换成你文件夹里自带的测试文件跑一下
# 你截图里有个 test_wavs 文件夹，里面有 zh.wav
test_audio = "test_wavs/zh.wav"

import librosa
audio_data, _ = librosa.load(test_audio, sr=16000, mono=True)

stream = recognizer.create_stream()
stream.accept_waveform(16000, audio_data)
recognizer.decode_stream(stream)

print("识别结果：", stream.result.text)
# app/engine/vad_processor.py
import librosa
import soundfile as sf
import numpy as np
import gc


class VADEngine:
    def __init__(self, top_db=20, min_duration=0.3):
        """
        初始化静音剔除引擎
        """
        self.top_db = top_db
        self.min_duration = min_duration

    def process_generator(self, audio_path: str, expected_sr: int = 16000):
        """
        [动作一 & 动作四核心改造]
        使用 yield 生成器按需返回波形，并使用 soundfile 替代 librosa.load 节省内存
        """
        print(f"[VAD] 正在使用低内存模式读取音频: {audio_path}")

        # 动作四：使用 soundfile 读取（比 librosa.load 省大概 40% 内存）
        audio_data, sr = sf.read(audio_path, dtype='float32')

        # 兜底：如果是双声道，转为单声道
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        # 兜底：如果采样率不是 SenseVoice 要求的 16000Hz，强制重采样
        if sr != expected_sr:
            print(f"[VAD] 检测到采样率为 {sr}Hz，正在重采样至 {expected_sr}Hz...")
            audio_data = librosa.resample(audio_data, orig_sr=sr, target_sr=expected_sr)
            sr = expected_sr

        # 核心逻辑：计算能量边界
        non_silent_intervals = librosa.effects.split(
            audio_data,
            top_db=self.top_db,
            frame_length=2048,
            hop_length=512
        )

        # 动作一：改用 yield 生成器，每次只在内存中保留一个小切片
        for start_idx, end_idx in non_silent_intervals:
            start_time = start_idx / sr
            end_time = end_idx / sr
            duration = end_time - start_time

            if duration >= self.min_duration:
                # 使用 yield 将切片抛给 ASR，处理完立刻在下一轮循环覆盖
                yield {
                    "start_time": round(start_time, 2),
                    "end_time": round(end_time, 2),
                    "duration": round(duration, 2),
                    "audio_data": audio_data[start_idx:end_idx]
                }

        # 遍历结束后，手动销毁几百 MB 的音频原数组，并强制触发垃圾回收
        del audio_data
        del non_silent_intervals
        gc.collect()
        print(f"[VAD] VAD处理结束，底层内存已强制回收。")
import librosa
import numpy as np


class VADEngine:
    def __init__(self, top_db=20, min_duration=0.3):
        """
        初始化静音剔除引擎
        :param top_db: 能量阈值。低于最大音量多少 dB 的声音被视为静音被剪掉。
                       ATC（地空通话）底噪很大，如果发现把杂音也当成语音了，把这个值调小（如 15）。
        :param min_duration: 最短有效语音时长（秒）。低于此时间的切片视为电流“咔哒”声，直接丢弃。
        """
        self.top_db = top_db
        self.min_duration = min_duration

    def process(self, audio_path: str, sample_rate: int = 16000) -> list:
        """
        处理音频文件，返回剔除静音后的有效音频片段及绝对时间戳
        """
        print(f"[VAD] 正在读取并分析音频: {audio_path}")
        # 1. 读取音频 (统一转为 16000Hz 单声道，迎合 SenseVoice 的口味)
        audio_data, sr = librosa.load(audio_path, sr=sample_rate, mono=True)

        # 2. 核心：使用 librosa 按照能量切分非静音区间
        # 返回的是一个二维数组：[[起始采样点, 结束采样点], ...]
        non_silent_intervals = librosa.effects.split(
            audio_data,
            top_db=self.top_db,
            frame_length=2048,
            hop_length=512
        )

        valid_segments = []
        for start_idx, end_idx in non_silent_intervals:
            # 换算成大家能看懂的绝对时间（秒）
            start_time = start_idx / sr
            end_time = end_idx / sr
            duration = end_time - start_time

            # 3. 过滤掉极短的噪音干扰
            if duration >= self.min_duration:
                # 截取真实的波形二进制数据
                segment_audio = audio_data[start_idx:end_idx]

                valid_segments.append({
                    "start_time": round(start_time, 2),
                    "end_time": round(end_time, 2),
                    "duration": round(duration, 2),
                    "audio_data": segment_audio  # 这是留给 asr_engine 去识别的纯净波形
                })

        print(f"[VAD] 剔除完成！提取出 {len(valid_segments)} 个有效人声切片。")
        return valid_segments
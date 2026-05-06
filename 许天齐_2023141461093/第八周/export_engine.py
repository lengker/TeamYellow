# a3_speech_processing_3/app/engine/export_engine.py
import os
import zipfile
import csv
from datetime import datetime
from typing import List
from app.db.models import LngAudioRecords


class ExportEngine:
    def __init__(self, storage_dir: str = "storage"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def create_export_package(self, records: List[LngAudioRecords], strategy_name: str = "custom") -> str:
        if not records:
            raise ValueError("没有找到符合条件的数据，无法打包。")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"export_{strategy_name}_{timestamp}.zip"
        zip_filepath = os.path.join(self.storage_dir, zip_filename)
        csv_filename = "index.csv"
        csv_filepath = os.path.join(self.storage_dir, csv_filename)

        try:
            # 1. 临时生成 CSV 索引文件 (修复了之前表头的笔误)
            with open(csv_filepath, mode='w', newline='', encoding='utf-8-sig') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["ID", "File_Name", "Channel", "ASR_Content", "Created_At"])

                for r in records:
                    # 容错：防止有的记录 channel 是空的导致报错
                    channel_val = getattr(r, 'channel', 'UNKNOWN')
                    writer.writerow([
                        r.id, r.file_name, channel_val, r.asr_content,
                        r.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    ])

            # 2. 将音频文件和 CSV 打包进 ZIP
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(csv_filepath, arcname=csv_filename)

                for r in records:
                    if os.path.exists(r.file_path):
                        zipf.write(r.file_path, arcname=f"audio/{os.path.basename(r.file_path)}")

            return zip_filepath

        finally:
            # 无论打包成功与否，清理临时的 CSV 文件
            if os.path.exists(csv_filepath):
                os.remove(csv_filepath)
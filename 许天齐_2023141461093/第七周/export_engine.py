# a3_speech_processing_1/app/engine/export_engine.py
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
        """
        [第七周任务: 导出引擎打包组装]
        将检索出的数据库记录及其对应的物理音频文件打包为 ZIP。
        并生成包含结构化元数据的 CSV 索引。
        """
        if not records:
            raise ValueError("没有找到符合条件的数据，无法打包。")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"export_{strategy_name}_{timestamp}.zip"
        zip_filepath = os.path.join(self.storage_dir, zip_filename)
        csv_filename = "index.csv"
        csv_filepath = os.path.join(self.storage_dir, csv_filename)

        print(f"📦 正在组装导出包: {zip_filename}，包含 {len(records)} 条记录...")

        try:
            # 1. 临时生成 CSV 索引文件
            with open(csv_filepath, mode='w', newline='', encoding='utf-8-sig') as csv_file:
                writer = csv.writer(csv_file)
                # 写入 CSV 表头
                writer.writerow(["ID", "File_Name", "Channel", "Duration(s)", "ASR_Content", "Created_At"])
                
                for r in records:
                    writer.writerow([
                        r.id, r.file_name, r.channel, r.duration, r.asr_content, 
                        r.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    ])

            # 2. 将音频文件和 CSV 打包进 ZIP
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 把索引表放进压缩包
                zipf.write(csv_filepath, arcname=csv_filename)
                
                # 把物理音频文件找出来并塞进压缩包
                for r in records:
                    if os.path.exists(r.file_path):
                        # arcname 避免将绝对路径的层级结构带入压缩包
                        zipf.write(r.file_path, arcname=f"audio/{os.path.basename(r.file_path)}")
                    else:
                        print(f"⚠️ [导出警告] 找不到对应的物理音频文件: {r.file_path}")

            print(f"✅ 打包完成: {zip_filepath}")
            return zip_filepath

        finally:
            # 无论打包成功失败，清理掉为了打包临时生成的独立 CSV 文件
            if os.path.exists(csv_filepath):
                os.remove(csv_filepath)
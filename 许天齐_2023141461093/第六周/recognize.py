# app/api/v1/recognize.py
import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

# 1. 关键修改：直接引入 Service 类，并在本文件中实例化
from app.services.speech_service import SpeechService
from app.db.session import get_db

router = APIRouter()

# 2. 在路由层初始化实例（这会在 uvicorn 启动扫描路由时完成模型预热）
print("🚀 正在预热 ASR/VAD 模型引擎...")
speech_handler = SpeechService()


@router.post("/process")
async def recognize_atc_audio(
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    os.makedirs("storage", exist_ok=True)
    temp_path = f"storage/{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 调用核心业务流
        results = speech_handler.process_and_save_audio(db=db, file_path=temp_path, channel="APP")

        return {
            "code": 200,
            "message": "success",
            "filename": file.filename,
            "data": results
        }
    except Exception as e:
        # 打印错误堆栈，方便你调试
        print(f"❌ 处理出错: {str(e)}")
        return {"code": 500, "message": f"处理失败: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
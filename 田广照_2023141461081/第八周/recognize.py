# app/api/v1/recognize.py - 适配新数据库设计
import os
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter()


@router.post("/process")
async def recognize_atc_audio(
        request: Request,  # 必须加上这个，为了获取全局状态
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    """
    语音识别接口 - 适配新数据库设计
    处理上传的ATC音频文件，进行语音识别并保存到数据库
    """
    os.makedirs("storage", exist_ok=True)
    temp_path = f"storage/{file.filename}"

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # [动作三核心] 从全局生命周期中提取已经加载好的模型单例
        # 这保证了无论多少人调用这个接口，都不会重复加载 200MB 的模型
        speech_handler = request.app.state.speech_handler

        # 调用核心业务流
        results = speech_handler.process_and_save_audio(db=db, file_path=temp_path, channel="APP")

        return {
            "code": 200,
            "message": "success",
            "filename": file.filename,
            "data": {
                "total_records": len(results),
                "audio_records": results
            }
        }
    except Exception as e:
        print(f"❌ 处理出错: {str(e)}")
        return {"code": 500, "message": f"处理失败: {str(e)}"}
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
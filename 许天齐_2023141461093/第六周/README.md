# 🎙️ 可视化ATC地空通话语音标注系统 - A3语音预处理模块

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)
![ONNX](https://img.shields.io/badge/Sherpa--ONNX-Engine-orange.svg)

## 1. 项目概述
本项目为 A-3 语音预处理模块，是 VHHH（香港赤鱲角国际机场）数据采集与处理系统的核心组件。其主要职责是接收 A-2 模块的语音流，执行 VAD（静音检测）与 ASR（语音识别），生成带时间戳的结构化文本，并提供高效的时序检索与导出服务。

**🎯 已完成阶段（第 5 周）：算法引擎融合与 DAO 模式基建**
完成了底层数据库抽象层的全面重构与 AI 引擎的工程化整合。通过引入 **SQLAlchemy 连接池** 与 **DAO 模式**，解决了高并发场景下的连接效率问题；成功将 **SenseVoice** 语音模型封装入 FastAPI 生命周期，实现了“音频上传 -> 算法推理 -> 自动入库”的全链路闭环。

**🚀 当前阶段（第 6 周）：检索导出 API 与系统综合联调**
本周的核心目标是开放对外数据服务。主要任务包括：基于业务需求完成 **时序检索接口 (RQ-A-3-30)** 和 **打包导出接口 (RQ-A-3-40)** 的开发；并利用多语种测试用例 (`test_wavs`) 完成从前端调用、语音解析到数据下发的端到端综合测试。

---

## 2. 核心技术栈
* **Web 框架**: FastAPI + Uvicorn
* **数据库 ORM**: SQLAlchemy 2.0 (配合高并发连接池)
* **AI 语音引擎**: Sherpa-ONNX (SenseVoice int8 量化模型)
* **音频处理**: Librosa, Soundfile

---

## 3. 目录结构

```text
a3_speech_processing/
├── app/
│   ├── api/                 # 【前台】Web 接口路由 (API v1)
│   │   ├── deps.py          # 存放通用的依赖项 (如数据库 Session 生成器)
│   │   └── v1/
│   │       ├── recognize.py # 语音识别接口 (RQ-A-3-10)
│   │       ├── query.py     # 时序检索接口 (RQ-A-3-30) [第6周重点]
│   │       └── export.py    # 策略导出接口 (RQ-A-3-40) [第6周重点]
│   ├── core/                # 【配置层】
│   │   ├── config.py        # 集中管理数据库 URL 及连接池调优参数
│   │   └── security.py      # API 密钥或跨域 (CORS) 配置
│   ├── db/                  # 【数据访问层】
│   │   ├── base.py          # ORM 模型基类 Base，统一全模块元数据
│   │   ├── session.py       # 初始化高并发连接池，提供防泄露的 get_db 依赖
│   │   ├── models.py        # 业务表结构定义 (LNG_TRACKS, LNG_AUDIO_RECORDS)
│   │   └── crud.py          # DAO 层：封装核心增删改查逻辑
│   ├── engine/              # 【算法核心引擎】
│   │   ├── sense_voice.py   # ASR 识别引擎加载与单例封装
│   │   ├── vad_processor.py # VAD 静音切分引擎
│   │   ├── ts_engine.py     # 时间戳计算工具
│   │   └── export_engine.py # 策略导出处理
│   ├── services/            # 【业务调度层】
│   │   └── speech_service.py# 串联“VAD切分 -> ASR识别 -> 结构化存库”业务流
│   └── main.py              # 【总控】项目启动入口，预热模型，注册路由
├── models/                  # 【模型存放区】存放 .onnx 等模型权重 (已忽略提交)
├── scripts/                 # 【测试与运维脚本】
│   └── test_db_pool_pressure.py # 多线程高并发压力测试脚本
├── storage/                 # 【存储区】存放临时音频或导出 ZIP (已忽略提交)
├── test_wavs/               # 【测试样例】存放用于综合联调的各语种测试音频 (zh/en/yue 等)
├── requirements.txt         # 项目依赖清单
├── .gitignore               # Git 忽略配置
└── README.md                # 项目说明文档
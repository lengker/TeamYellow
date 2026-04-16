import os
import time
import pandas as pd
import requests
import random

# ================= 配置区 =================
# 文件路径配置
EXCEL_PATH = "A3_Test_GroundTruth_List.xlsx"
AUDIO_DIR = "Alpha_Final_TestSet_50"  # 你的那个扁平化大文件夹
OUTPUT_EXCEL = "A3_Test_Result_Log_Run1.xlsx"  # 测试结果输出的Excel文件名

# API 配置 (等你们系统开发好了，填入真实的地址)
API_URL = "http://localhost:8000/api/v1/asr/recognize"

# 测试模式开关：True 代表使用模拟接口(适合前端测试跑通流程)，False 代表请求真实服务器
USE_MOCK_API = True


# ==========================================

def call_mock_api(audio_path, duration):
    """
    模拟 A-3 引擎的 API 响应。
    如果没有开发好系统，用这个函数来假装系统在工作，测试整个链路。
    """
    # 模拟处理耗时：假设服务器处理速度是音频长度的 0.2 倍 到 0.5 倍之间
    simulated_latency = float(duration) * random.uniform(0.2, 0.5)
    time.sleep(simulated_latency)

    # 模拟返回的 JSON 结果
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "text": f"[模拟识别结果] 成功处理了文件 {os.path.basename(audio_path)}",
            "vad_status": "normal"
        }
    }


def call_real_api(audio_path):
    """
    真实的 API 请求函数。等你们的服务器跑起来后就用这个。
    """
    try:
        with open(audio_path, 'rb') as f:
            # 这里的 'audio_file' 字段名需要跟你们后端商量好
            files = {'audio_file': (os.path.basename(audio_path), f, 'audio/mpeg')}
            response = requests.post(API_URL, files=files, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                return {"code": response.status_code, "msg": "API Error", "data": {"text": "请求失败"}}
    except Exception as e:
        return {"code": 500, "msg": str(e), "data": {"text": "网络异常"}}


def main():
    print("🚀 启动 A-3 ASR/VAD 引擎自动化测试流...\n")

    if not os.path.exists(EXCEL_PATH):
        print(f"❌ 找不到测试基准表: {EXCEL_PATH}，请检查路径。")
        return

    # 1. 读取 Excel 基准表
    print(f"📂 正在加载测试用例: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)
    total_cases = len(df)
    print(f"✅ 成功加载 {total_cases} 条测试数据。\n")

    # 准备记录结果的列表
    asr_outputs = []
    latencies = []

    # 2. 遍历测试用例，发起请求
    for index, row in df.iterrows():
        file_name = str(row['文件名 (File_Name)']).strip()
        duration = row['时长 (Duration)']

        # 处理时长数据，去掉 "s" 方便计算
        if isinstance(duration, str) and 's' in duration:
            duration = float(duration.replace('s', ''))

        audio_path = os.path.join(AUDIO_DIR, file_name)
        print(f"[{index + 1}/{total_cases}] 正在发送测试: {file_name}...")

        if not os.path.exists(audio_path):
            print(f"   ⚠️ 文件缺失，跳过此项。")
            asr_outputs.append("【文件缺失】")
            latencies.append(0.0)
            continue

        # 记录请求开始时间
        start_time = time.time()

        # 调用接口 (模拟或真实)
        if USE_MOCK_API:
            api_response = call_mock_api(audio_path, duration)
        else:
            api_response = call_real_api(audio_path)

        # 记录请求结束时间
        end_time = time.time()
        latency = round(end_time - start_time, 2)

        # 解析返回结果 (根据你们接口实际的 JSON 结构调整)
        if api_response.get("code") == 200:
            recognized_text = api_response.get("data", {}).get("text", "无文本")
        else:
            recognized_text = f"【接口报错】{api_response.get('msg')}"

        print(f"   ✓ 耗时: {latency}s | 识别结果: {recognized_text[:20]}...")

        asr_outputs.append(recognized_text)
        latencies.append(latency)

    # 3. 将结果写回 DataFrame
    df['AI识别文本 (ASR_Output)'] = asr_outputs
    df['接口耗时 (Latency)'] = latencies

    # 计算 RTF (实时率) 并写入备注列作为参考
    rtf_list = []
    for i in range(len(df)):
        dur = df.at[i, '时长 (Duration)']
        lat = df.at[i, '接口耗时 (Latency)']
        if isinstance(dur, str):
            dur = float(dur.replace('s', ''))
        if dur > 0 and lat > 0:
            rtf = round(lat / dur, 3)
            rtf_list.append(f"RTF: {rtf}")
        else:
            rtf_list.append("-")

    # 为了不覆盖原来的 Notes，我们把 RTF 追加到备注后面
    df['备注/缺陷 (Notes)'] = df['备注/缺陷 (Notes)'].fillna('') + " | " + pd.Series(rtf_list)

    # 4. 保存为新的 Excel 文件 (防止污染原始 Ground Truth)
    df.to_excel(OUTPUT_EXCEL, index=False)

    print("\n==========================================")
    print(f"🎉 测试执行完毕！")
    print(f"📊 测试报告已生成并保存至: {OUTPUT_EXCEL}")
    print("==========================================")


if __name__ == "__main__":
    main()
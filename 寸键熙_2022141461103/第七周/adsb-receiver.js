/**
 * ADSB 航迹数据接收器（含时间绑定逻辑）
 * 功能：
 * - 模拟数据推送（每3秒）
 * - 提取原始时间戳与接收时间，计算传输延迟
 * - 统一输出毫秒级时间字段
 */
class ADSBDataReceiver {
  constructor() {
    this.pushUrl = "http://localhost:8080/adsb/push";   // 后端接收接口
    this.dataList = [];                                 // 缓存数据列表
  }

  // 初始化：启动模拟推送定时器
  init() {
    console.log("✅ 时间绑定逻辑已启动，模拟数据每3秒推送一次");
    setInterval(() => this.simulatePush(), 3000);
  }

  // 模拟 ADSB 设备发送的原始数据（包含可选的时间字段）
  simulatePush() {
    const mockADSB = {
      icao: "TEST" + Math.floor(Math.random() * 1000),
      lat: 30.5678 + (Math.random() - 0.5) * 0.1,
      lon: 120.1234 + (Math.random() - 0.5) * 0.1,
      alt: 9000 + Math.random() * 500,
      speed: 420 + Math.random() * 30,
      // 模拟数据自带的原始时间（部分设备可能没有，此处随机生成最近30秒内的时间）
      src_time: Date.now() - Math.random() * 30000
    };
    this.handleData(JSON.stringify(mockADSB));
  }

  // 核心：数据处理 + 时间绑定
  handleData(raw) {
    try {
      let data = JSON.parse(raw);
      // 1. 获取原始时间（若数据中未提供，则回退为当前接收时间）
      const srcTime = data.src_time || Date.now();
      // 2. 系统接收时间（毫秒）
      const recvTime = Date.now();
      // 3. 绑定双时间戳与延迟
      data.bound_timestamp = {
        src: srcTime,
        recv: recvTime,
        diff_ms: recvTime - srcTime
      };
      // 同时保留一个统一的 timestamp 字段（接收时间）
      data.timestamp = recvTime;
      
      // 存入缓存
      this.dataList.push(data);
      
      // 控制台输出时间绑定详情（便于调试）
      console.log("📥 时间绑定完成:", {
        icao: data.icao,
        原始时间: new Date(srcTime).toLocaleString(),
        接收时间: new Date(recvTime).toLocaleString(),
        延迟_ms: data.bound_timestamp.diff_ms
      });
    } catch (e) {
      console.error("❌ 数据解析或时间绑定失败:", e);
    }
  }

  // 获取已接收的所有航迹数据（供其他模块调用）
  getAdsbData() {
    return this.dataList;
  }
}

// 启动接收器
const receiver = new ADSBDataReceiver();
receiver.init();
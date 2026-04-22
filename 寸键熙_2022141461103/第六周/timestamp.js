class ADSBDataReceiver {
  constructor() {
    this.pushUrl = "http://localhost:8080/adsb/push";
    this.dataList = [];
  }

  init() {
    console.log("✅ 时间绑定逻辑已启动");
    setInterval(() => this.simulatePush(), 3000);
  }

  // 模拟 ADSB 数据（增加可选时间字段）
  simulatePush() {
    const mockADSB = {
      icao: "TEST123",
      lat: 30.5678,
      lon: 120.1234,
      alt: 9000,
      speed: 420,
      // 模拟数据自带时间（可选，若无则用接收时间）
      src_time: Date.now() - Math.random() * 5000
    };
    this.handleData(JSON.stringify(mockADSB));
  }

  // 核心：时间绑定逻辑
  handleData(raw) {
    try {
      let data = JSON.parse(raw);
      // 1. 原始时间戳（数据自带或当前时间）
      const srcTime = data.src_time || Date.now();
      // 2. 系统接收时间戳
      const recvTime = Date.now();
      // 3. 绑定时间字段（毫秒级）
      data.bound_timestamp = {
        src: srcTime,
        recv: recvTime,
        diff_ms: recvTime - srcTime   // 传输延迟
      };
      // 同时保留原始时间字段（兼容）
      data.timestamp = recvTime;
      this.dataList.push(data);
      console.log(" 时间绑定完成:", {
        icao: data.icao,
        原始时间: new Date(srcTime).toISOString(),
        接收时间: new Date(recvTime).toISOString(),
        延迟_ms: data.bound_timestamp.diff_ms
      });
    } catch (e) {
      console.error(" 时间绑定失败", e);
    }
  }

  getAdsbData() {
    return this.dataList;
  }
}

const receiver = new ADSBDataReceiver();
receiver.init();
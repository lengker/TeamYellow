import { RetryQueue } from './retry-queue.js';

class ADSBDataReceiver {
  constructor() {
    this.pushUrl = "http://localhost:8080/api/track/receive";
    this.dataList = [];
    // 初始化重试队列，绑定发送函数
    this.retryQueue = new RetryQueue((trackData) => this.sendToBackend(trackData), 3);
  }

  init() {
    console.log("✅ 带数据丢失修复的ADSB接收器已启动");
    setInterval(() => this.simulatePush(), 3000);
  }

  simulatePush() {
    const mockADSB = {
      icao: "TEST" + Math.floor(Math.random() * 1000),
      lat: 30.5678 + (Math.random() - 0.5) * 0.1,
      lon: 120.1234 + (Math.random() - 0.5) * 0.1,
      alt: 9000 + Math.random() * 500,
      speed: 420 + Math.random() * 30,
      src_time: Date.now() - Math.random() * 30000
    };
    this.handleData(mockADSB);
  }

  handleData(data) {
    // 时间绑定（与之前相同）
    const srcTime = data.src_time || Date.now();
    const recvTime = Date.now();
    data.bound_timestamp = { src: srcTime, recv: recvTime, diff_ms: recvTime - srcTime };
    data.timestamp = recvTime;
    this.dataList.push(data);
    
    // 加入重试队列（自动发送，失败则缓存）
    this.retryQueue.enqueue(data);
  }

  async sendToBackend(trackData) {
    const response = await fetch(this.pushUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(trackData)
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  getAdsbData() { return this.dataList; }
}

const receiver = new ADSBDataReceiver();
receiver.init();
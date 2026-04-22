
class ADSBDataReceiver {
    constructor() {
      // 推送接口地址（模拟接口）
      this.pushUrl = "http://localhost:8080/adsb/push";
      // 存储接收的航迹数据
      this.dataList = [];
    }
  
    // 初始化接口
    init() {
      console.log("✅ 环境初始化完成，ADSB接收接口已启动");
      // 每3秒模拟推送一次数据
      setInterval(() => this.simulatePush(), 3000);
    }
  
    // 模拟ADSB数据推送（第五周调试专用）
    simulatePush = () => {
      const mockADSB = {
        icao: "TEST123",    // 飞机标识码
        lat: 30.5678,       // 纬度
        lon: 120.1234,      // 经度
        alt: 9000,          // 高度
        speed: 420          // 速度
      };
      // 把模拟数据传给接收函数
      this.handleData(JSON.stringify(mockADSB));
    }
  
    // 数据处理函数
    handleData = (raw) => {
      try {
        let data = JSON.parse(raw);
        data.timestamp = new Date().getTime(); // 绑定时间戳
        this.dataList.push(data);
        console.log("📥 接收航迹数据：", data);
      } catch (e) {
        console.error("❌ 解析失败", e);
      }
    }
  
    /**
     * 获取已接收的航迹数据（供后续模块调用）
     */
    getAdsbData() {
      return this.dataList;
    }
  }
  
  // 启动接收接口
  const receiver = new ADSBDataReceiver();
  receiver.init();
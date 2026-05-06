import { CacheManager } from './cache-manager.js';

/**
 * 带持久化的重试队列
 * 功能：发送失败自动缓存，网络恢复后重试，支持指数退避
 */
class RetryQueue {
  constructor(sendCallback, maxRetries = 3) {
    this.sendCallback = sendCallback;   // 发送函数，需返回 Promise
    this.maxRetries = maxRetries;
    this.cache = new CacheManager();
    this.isProcessing = false;
    this.init();
  }

  async init() {
    // 监听网络恢复事件
    window.addEventListener('online', () => {
      console.log('网络已恢复，开始重试缓存数据');
      this.processQueue();
    });
    // 页面关闭前，确保数据已缓存（不丢失）
    window.addEventListener('beforeunload', () => {
      if (this.pendingData) {
        this.cache.save(this.pendingData);
      }
    });
    // 加载未完成的缓存数据并重试
    await this.processQueue();
  }

  // 添加数据到队列（立即尝试发送）
  async enqueue(data) {
    // 先尝试发送
    try {
      await this.sendWithRetry(data);
      console.log('数据发送成功', data);
    } catch (err) {
      console.warn('发送失败，存入缓存', err);
      await this.cache.save(data);
    }
  }

  async sendWithRetry(data, attempt = 1) {
    try {
      return await this.sendCallback(data);
    } catch (err) {
      if (attempt < this.maxRetries) {
        const delay = Math.pow(2, attempt) * 1000; // 指数退避：2s,4s,8s
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.sendWithRetry(data, attempt + 1);
      }
      throw err;
    }
  }

  async processQueue() {
    if (this.isProcessing) return;
    this.isProcessing = true;
    try {
      const pendingList = await this.cache.loadAll();
      for (let item of pendingList) {
        try {
          await this.sendWithRetry(item);
          await this.cache.remove(item.id);
          console.log('缓存数据重发成功', item);
        } catch (err) {
          console.error('缓存数据重发失败，保留在缓存中', item, err);
        }
      }
    } finally {
      this.isProcessing = false;
    }
  }
}
/**
 * 持久化缓存管理器（支持 IndexedDB 降级 localStorage）
 * 用于存储未发送成功的航迹数据，防止丢失
 */
class CacheManager {
  constructor(storeName = 'adsb_queue') {
    this.storeName = storeName;
    this.db = null;
    this.useIndexedDB = 'indexedDB' in window;
    this.init();
  }

  async init() {
    if (!this.useIndexedDB) {
      console.warn('IndexedDB 不支持，降级使用 localStorage');
      return;
    }
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('ATCCache', 1);
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName, { keyPath: 'id', autoIncrement: true });
        }
      };
      request.onsuccess = (e) => {
        this.db = e.target.result;
        resolve();
      };
      request.onerror = (e) => reject(e);
    });
  }

  // 存储数据（支持对象或数组）
  async save(data) {
    if (this.useIndexedDB && this.db) {
      return new Promise((resolve, reject) => {
        const tx = this.db.transaction([this.storeName], 'readwrite');
        const store = tx.objectStore(this.storeName);
        const items = Array.isArray(data) ? data : [data];
        items.forEach(item => store.add({ ...item, cachedAt: Date.now() }));
        tx.oncomplete = () => resolve();
        tx.onerror = reject;
      });
    } else {
      // localStorage 降级
      const key = `cache_${Date.now()}_${Math.random()}`;
      localStorage.setItem(key, JSON.stringify(data));
      return Promise.resolve();
    }
  }

  // 取出所有未发送数据
  async loadAll() {
    if (this.useIndexedDB && this.db) {
      return new Promise((resolve, reject) => {
        const tx = this.db.transaction([this.storeName], 'readonly');
        const store = tx.objectStore(this.storeName);
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = reject;
      });
    } else {
      const keys = Object.keys(localStorage).filter(k => k.startsWith('cache_'));
      const items = keys.map(k => JSON.parse(localStorage.getItem(k)));
      return items;
    }
  }

  // 删除已成功发送的数据
  async remove(itemId) {
    if (this.useIndexedDB && this.db) {
      return new Promise((resolve, reject) => {
        const tx = this.db.transaction([this.storeName], 'readwrite');
        const store = tx.objectStore(this.storeName);
        store.delete(itemId);
        tx.oncomplete = resolve;
        tx.onerror = reject;
      });
    } else {
      // 简单处理：清除所有缓存（实际可按需优化）
      Object.keys(localStorage).forEach(k => {
        if (k.startsWith('cache_')) localStorage.removeItem(k);
      });
      return Promise.resolve();
    }
  }
}
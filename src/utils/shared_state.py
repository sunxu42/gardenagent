import json
import time
import threading
import os
from typing import Any, Dict
import redis
import lmdb

class StorageBackend:
    def set(self, key, value):
        pass
    
    def get(self, key):
        pass
    
    def delete(self, key):
        pass
    
    def keys(self, pattern):
        pass

class LMDBBackend(StorageBackend):
    def __init__(self, config):
        self.db_path = config.get('db_path', './shared_state.lmdb')
        self.max_db_size = config.get('max_db_size', 10 * 1024 * 1024)
        self.env = lmdb.open(self.db_path, map_size=self.max_db_size)
        self.key_prefix = b"shared_state:"
    
    def set(self, key, value):
        with self.env.begin(write=True) as txn:
            full_key = self.key_prefix + key.encode('utf-8')
            txn.put(full_key, value.encode('utf-8'))
    
    def get(self, key):
        with self.env.begin() as txn:
            full_key = self.key_prefix + key.encode('utf-8')
            value = txn.get(full_key)
            return value.decode('utf-8') if value else None
    
    def delete(self, key):
        with self.env.begin(write=True) as txn:
            full_key = self.key_prefix + key.encode('utf-8')
            txn.delete(full_key)
    
    def keys(self, pattern):
        with self.env.begin() as txn:
            cursor = txn.cursor()
            keys = []
            for key, _ in cursor:
                if key.startswith(self.key_prefix):
                    original_key = key[len(self.key_prefix):].decode('utf-8')
                    keys.append(original_key)
            return keys

class RedisBackend(StorageBackend):
    def __init__(self, config):
        self.client = redis.Redis(**config)
        self.key_prefix = "shared_state:"
    
    def set(self, key, value):
        full_key = f"{self.key_prefix}{key}"
        self.client.set(full_key, value)
    
    def get(self, key):
        full_key = f"{self.key_prefix}{key}"
        return self.client.get(full_key)
    
    def delete(self, key):
        full_key = f"{self.key_prefix}{key}"
        self.client.delete(full_key)
    
    def keys(self, pattern):
        full_pattern = f"{self.key_prefix}*"
        keys = self.client.keys(full_pattern)
        return [key.decode('utf-8').replace(self.key_prefix, '') for key in keys]

class SharedState:
    _instance = None
    _storage_backend = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, backend_type=None, config=None):
        if not cls._initialized:
            try:
                from yard.configs.secrets import load_secrets

                backend_type = (
                    backend_type
                    or load_secrets().shared_state_backend
                    or "lmdb"
                )
                config = config or {}
                
                if backend_type == 'lmdb':
                    cls._storage_backend = LMDBBackend(config)
                    print("SharedState LMDB后端已初始化")
                elif backend_type == 'redis':
                    cls._storage_backend = RedisBackend(config)
                    print("SharedState Redis后端已初始化")
                else:
                    raise ValueError(f"不支持的存储后端: {backend_type}")
                
                cls._initialized = True
            except Exception as e:
                print(f"SharedState初始化失败: {e}")
                raise


    @classmethod
    def register(cls, key, value):
        with cls._lock:
            try:
                if isinstance(value, (dict, list, tuple)):
                    value_str = json.dumps(value)
                else:
                    value_str = str(value)
                
                cls._storage_backend.set(key, value_str)
            except Exception as e:
                print(f"注册共享状态失败: {e}")

    @classmethod
    def get(cls, key, default=None):
        with cls._lock:
            try:
                value_str = cls._storage_backend.get(key)
                if value_str is None:
                    return default
                
                try:
                    return json.loads(value_str)
                except (json.JSONDecodeError, TypeError):
                    return value_str
                    
            except Exception as e:
                print(f"获取共享状态失败: {e}")
                return default

    @classmethod
    def remove(cls, key):
        with cls._lock:
            try:
                cls._storage_backend.delete(key)
            except Exception as e:
                print(f"删除共享状态失败: {e}")

    @classmethod
    def all(cls):
        with cls._lock:
            try:
                keys = cls._storage_backend.keys("*")
                result = {}
                for key in keys:
                    value = cls.get(key)
                    result[key] = value
                
                return result
            except Exception as e:
                print(f"获取所有共享状态失败: {e}")
                return {}

# 初始化SharedState
SharedState.initialize()

# 使用示例
if __name__ == "__main__":
    registry = SharedState()
    # 注册信息
    registry.register("user_1", {"name": "Alice", "age": 30})
    registry.register("config", {"debug": True, "port": 8080})

    # 按需获取
    print(registry.get("user_1"))  # 输出：{'name': 'Alice', 'age': 30}
    print(registry.get("config")["port"])  # 输出：8080

    # 获取所有
    print(registry.all())  # 输出所有注册的键值对


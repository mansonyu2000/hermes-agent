"""
config.py — RPA 配置加载器

用法:
  from config import config
  threshold = config.llm_timeout_s        # 2.0
  url = config.ollama_url                  # http://192.168.3.9:11434
  model = config.default_model             # qwen2.5:latest

配置文件: config.json (同目录)
缺文件时使用内置默认值，不报错。
"""

import json, os

_DEFAULT = {
    "llm_timeout_s": 2.0,
    "ollama_url": "http://192.168.3.9:11434",
    "default_model": "qwen2.5:latest",
    "vision_model": "qwen2.5vl:7b",
}


class Config:
    """单例配置。从 config.json 加载，缺项用默认值。"""

    _instance = None

    def __init__(self, path=None):
        if path is None:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self._path = path
        self._data = dict(_DEFAULT)
        self._load()

    def _load(self):
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except Exception:
            return  # 缺文件 → 用默认值

        # 从 "llm" 子对象提取扁平化键
        llm = raw.get("llm", {})
        if isinstance(llm, dict):
            for k in ("timeout_s", "ollama_url", "default_model", "vision_model"):
                if k in llm:
                    self._data[f"llm_{k}"] = llm[k]

        # 也支持顶层扁平键 (向后兼容)
        for k in ("llm_timeout_s", "ollama_url", "default_model", "vision_model"):
            if k in raw and not isinstance(raw[k], dict):
                self._data[k] = raw[k]

    # ── 属性访问 ──

    @property
    def llm_timeout_s(self):
        """超过此秒数 → 切 LLM 兜底"""
        return self._data.get("llm_timeout_s", 2.0)

    @property
    def ollama_url(self):
        return self._data.get("ollama_url", "http://192.168.3.9:11434")

    @property
    def default_model(self):
        return self._data.get("default_model", "qwen2.5:latest")

    @property
    def vision_model(self):
        return self._data.get("vision_model", "qwen2.5vl:7b")

    def get(self, key, default=None):
        return self._data.get(key, default)

    def reload(self):
        """重新加载配置文件（后台改完不用重启）"""
        self._load()

    def dump(self):
        """打印当前配置 → 调试用"""
        return {k: v for k, v in self._data.items()}


# 模块级单例
config = Config()

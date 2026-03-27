"""
全屋定制客户服务AI助手 - 核心模块

核心业务逻辑层，提供配置管理、数据库抽象、AI服务、认证授权和缓存管理
"""

__version__ = "2.0.0"
__author__ = "BINK不锈钢定制"

from .config import Config
from .database import DatabaseManager
from .ai_service import AIService
from .auth import AuthManager
from .cache import CacheManager

__all__ = [
    "Config",
    "DatabaseManager", 
    "AIService",
    "AuthManager",
    "CacheManager"
]

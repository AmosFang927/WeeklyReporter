#!/usr/bin/env python3
"""
Postback系统配置文件
"""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """系统配置类"""
    
    # 应用基础配置
    app_name: str = "Rector Postback Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")  # 使用不同的端口避免衝突
    workers: int = Field(default=1, env="WORKERS")
    
    # 数据库配置
    database_url: str = Field(
        default="postgresql+asyncpg://postback:postback123@localhost:5432/postback_db",
        env="DATABASE_URL"
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Redis配置
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    
    # Token配置
    ts_token_secret: str = Field(default="your-ts-token-secret", env="TS_TOKEN_SECRET")
    tlm_token_secret: str = Field(default="your-tlm-token-secret", env="TLM_TOKEN_SECRET")
    token_expire_hours: int = Field(default=24, env="TOKEN_EXPIRE_HOURS")
    
    # 业务配置
    data_retention_days: int = Field(default=7, env="DATA_RETENTION_DAYS")
    max_requests_per_minute: int = Field(default=1000, env="MAX_REQUESTS_PER_MINUTE")
    enable_duplicate_check: bool = Field(default=True, env="ENABLE_DUPLICATE_CHECK")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 监控配置
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8001, env="METRICS_PORT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


# 数据库配置
def get_database_url() -> str:
    """获取数据库连接URL"""
    return settings.database_url


# Redis配置
def get_redis_url() -> str:
    """获取Redis连接URL"""
    return settings.redis_url


# 日志配置
def setup_logging():
    """设置日志配置"""
    import logging
    
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format=settings.log_format
    )
    
    return logging.getLogger(__name__)


# 获取环境变量的便捷函数
def get_env(key: str, default: str = None) -> str:
    """获取环境变量"""
    return os.getenv(key, default) 
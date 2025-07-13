#!/usr/bin/env python3
"""
基础API客户端抽象类
为所有API客户端提供统一的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class BaseAPIClient(ABC):
    """API客户端基类"""
    
    def __init__(self, api_secret: str = None, api_key: str = None):
        self.api_secret = api_secret
        self.api_key = api_key
        self.authenticated = False
    
    @abstractmethod
    def authenticate(self) -> bool:
        """认证方法"""
        pass
    
    @abstractmethod
    def get_conversions(self, start_date: str, end_date: str, **kwargs) -> Dict[str, Any]:
        """获取转化数据"""
        pass
    
    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        pass
    
    def is_authenticated(self) -> bool:
        """检查认证状态"""
        return self.authenticated
    
    def get_client_info(self) -> Dict[str, Any]:
        """获取客户端信息"""
        return {
            "client_type": self.__class__.__name__,
            "authenticated": self.authenticated,
            "api_key": self.api_key[:10] + "..." if self.api_key else None
        } 
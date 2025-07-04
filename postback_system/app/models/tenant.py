#!/usr/bin/env python3
"""
租户数据模型
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class Tenant(Base):
    """
    租户模型
    用于管理多租户系统中的不同租户
    """
    __tablename__ = "tenants"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 租户标识
    tenant_code = Column(String(50), unique=True, nullable=False, index=True, comment="租户唯一代码")
    tenant_name = Column(String(100), nullable=False, comment="租户名称")
    
    # Token配置
    ts_token = Column(String(255), comment="TS Token")
    tlm_token = Column(String(255), comment="TLM Token")
    ts_param = Column(String(100), comment="TS Parameter")
    
    # 配置信息
    description = Column(Text, comment="租户描述")
    contact_email = Column(String(255), comment="联系邮箱")
    contact_phone = Column(String(50), comment="联系电话")
    
    # 业务配置
    max_daily_requests = Column(Integer, default=100000, comment="每日最大请求数")
    enable_duplicate_check = Column(Boolean, default=True, comment="是否启用重复检查")
    data_retention_days = Column(Integer, default=7, comment="数据保留天数")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    conversions = relationship("PostbackConversion", back_populates="tenant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, code='{self.tenant_code}', name='{self.tenant_name}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "tenant_code": self.tenant_code,
            "tenant_name": self.tenant_name,
            "ts_token": self.ts_token,
            "tlm_token": self.tlm_token,
            "ts_param": self.ts_param,
            "description": self.description,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "max_daily_requests": self.max_daily_requests,
            "enable_duplicate_check": self.enable_duplicate_check,
            "data_retention_days": self.data_retention_days,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_default_tenant(cls):
        """创建默认租户"""
        return cls(
            tenant_code="default",
            tenant_name="Default Tenant",
            description="Default tenant for testing",
            ts_token="default-ts-token",
            tlm_token="default-tlm-token",
            ts_param="default",
            contact_email="admin@example.com"
        ) 
#!/usr/bin/env python3
"""
Partner模型 - 管理不同的postback endpoints
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Numeric, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from typing import Optional, Dict, Any

# 兼容SQLite和PostgreSQL的JSON类型
try:
    from sqlalchemy.dialects.postgresql import JSONB
    JsonType = JSON
except ImportError:
    JsonType = JSON


class Partner(Base):
    """
    Partner模型
    管理不同的postback endpoints和對應的配置
    """
    __tablename__ = "partners"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # Partner标识
    partner_code = Column(String(50), unique=True, nullable=False, index=True, comment="Partner唯一代码")
    partner_name = Column(String(100), nullable=False, comment="Partner名称")
    
    # Endpoint配置
    endpoint_path = Column(String(100), unique=True, nullable=False, comment="Endpoint路径")
    endpoint_url = Column(String(500), comment="完整的Endpoint URL")
    
    # Cloud Run配置
    cloud_run_service_name = Column(String(100), comment="对应的Cloud Run服务名称")
    cloud_run_region = Column(String(50), default="asia-southeast1", comment="Cloud Run区域")
    cloud_run_project_id = Column(String(100), comment="Google Cloud项目ID")
    
    # 数据库配置
    database_name = Column(String(100), comment="专用数据库名称")
    database_url = Column(String(500), comment="专用数据库连接URL")
    
    # 参数映射配置
    parameter_mapping = Column(JsonType, comment="参数映射配置")
    
    # 状态配置
    is_active = Column(Boolean, default=True, comment="是否激活")
    enable_logging = Column(Boolean, default=True, comment="是否启用详细日志")
    
    # 业务配置
    max_daily_requests = Column(Integer, default=100000, comment="每日最大请求数")
    data_retention_days = Column(Integer, default=30, comment="数据保留天数")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    conversions = relationship("PartnerConversion", back_populates="partner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Partner(id={self.id}, code='{self.partner_code}', name='{self.partner_name}', endpoint='{self.endpoint_path}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "partner_code": self.partner_code,
            "partner_name": self.partner_name,
            "endpoint_path": self.endpoint_path,
            "endpoint_url": self.endpoint_url,
            "cloud_run_service_name": self.cloud_run_service_name,
            "cloud_run_region": self.cloud_run_region,
            "cloud_run_project_id": self.cloud_run_project_id,
            "database_name": self.database_name,
            "database_url": self.database_url,
            "parameter_mapping": self.parameter_mapping,
            "is_active": self.is_active,
            "enable_logging": self.enable_logging,
            "max_daily_requests": self.max_daily_requests,
            "data_retention_days": self.data_retention_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def create_involve_asia_partner(cls):
        """创建InvolveAsia Partner"""
        return cls(
            partner_code="involve_asia",
            partner_name="InvolveAsia",
            endpoint_path="/involve/event",
            endpoint_url="https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event",
            cloud_run_service_name="bytec-public-postback",
            cloud_run_region="asia-southeast1",
            cloud_run_project_id="472712465571",
            database_name="involve_asia_db",
            parameter_mapping={
                "sub_id": "aff_sub",
                "media_id": "aff_sub2", 
                "click_id": "aff_sub3",
                "usd_sale_amount": "usd_sale_amount",
                "usd_payout": "usd_payout",
                "offer_name": "offer_name",
                "conversion_id": "conversion_id",
                "conversion_datetime": "datetime_conversion"
            }
        )
    
    @classmethod
    def create_rector_partner(cls):
        """创建Rector Partner"""
        return cls(
            partner_code="rector",
            partner_name="Rector",
            endpoint_path="/rector/event",
            endpoint_url="https://rector-fitiology.icu/aa7dfd32-953b-42ee-a77e-fba556a71d2f",
            cloud_run_service_name="rector-postback",
            cloud_run_region="asia-southeast1",
            cloud_run_project_id="472712465571",
            database_name="rector_db",
            parameter_mapping={
                "media_id": "media_id",
                "sub_id": "sub_id",
                "usd_sale_amount": "usd_sale_amount",
                "usd_earning": "usd_earning",
                "offer_name": "offer_name",
                "conversion_id": "conversion_id",
                "conversion_datetime": "conversion_datetime",
                "click_id": "click_id"
            }
        )


class PartnerConversion(Base):
    """
    Partner专用转化数据模型
    为每个Partner提供独立的数据存储
    """
    __tablename__ = "partner_conversions"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # Partner关联
    partner_id = Column(Integer, ForeignKey("partners.id"), nullable=False, index=True, comment="Partner ID")
    
    # 核心字段
    conversion_id = Column(String(50), nullable=False, index=True, comment="转换ID")
    offer_id = Column(String(50), comment="Offer ID")
    offer_name = Column(Text, comment="Offer名称")
    
    # 时间字段
    conversion_datetime = Column(DateTime(timezone=True), comment="转换时间")
    
    # 金额字段
    usd_sale_amount = Column(Numeric(15, 2), comment="美元销售金额")
    usd_earning = Column(Numeric(15, 2), comment="美元佣金")
    
    # 自定义参数
    media_id = Column(String(255), comment="媒体ID")
    sub_id = Column(String(255), comment="子ID")
    click_id = Column(String(255), comment="点击ID")
    
    # 处理状态
    is_processed = Column(Boolean, default=False, comment="是否已处理")
    is_duplicate = Column(Boolean, default=False, comment="是否为重复数据")
    processing_error = Column(Text, comment="处理错误信息")
    
    # 原始数据存储
    raw_data = Column(JsonType, comment="完整的原始Postback数据")
    request_headers = Column(JsonType, comment="请求头信息")
    request_ip = Column(String(45), comment="请求IP地址")
    
    # 时间戳
    received_at = Column(DateTime(timezone=True), server_default=func.now(), comment="接收时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    partner = relationship("Partner", back_populates="conversions")
    
    def __repr__(self):
        return f"<PartnerConversion(id={self.id}, partner_id={self.partner_id}, conversion_id='{self.conversion_id}')>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "partner_id": self.partner_id,
            "conversion_id": self.conversion_id,
            "offer_id": self.offer_id,
            "offer_name": self.offer_name,
            "conversion_datetime": self.conversion_datetime.isoformat() if self.conversion_datetime else None,
            "usd_sale_amount": float(self.usd_sale_amount) if self.usd_sale_amount else None,
            "usd_earning": float(self.usd_earning) if self.usd_earning else None,
            "media_id": self.media_id,
            "sub_id": self.sub_id,
            "click_id": self.click_id,
            "is_processed": self.is_processed,
            "is_duplicate": self.is_duplicate,
            "processing_error": self.processing_error,
            "raw_data": self.raw_data,
            "request_ip": self.request_ip,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# 创建索引以提升查询性能
Index("idx_partner_conversion", PartnerConversion.partner_id, PartnerConversion.conversion_id, unique=True)
Index("idx_partner_datetime", PartnerConversion.partner_id, PartnerConversion.conversion_datetime)
Index("idx_partner_received", PartnerConversion.partner_id, PartnerConversion.received_at) 
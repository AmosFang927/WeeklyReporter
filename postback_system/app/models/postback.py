#!/usr/bin/env python3
"""
Postback转化数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Boolean, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
from decimal import Decimal
from typing import Optional, Dict, Any

# 兼容SQLite和PostgreSQL的JSON类型
try:
    from sqlalchemy.dialects.postgresql import JSONB
    # 使用 JSON 而不是 JSONB 以兼容 SQLite
    JsonType = JSON
except ImportError:
    JsonType = JSON


class PostbackConversion(Base):
    """
    Postback转化数据模型
    基于Involve Asia的Postback参数设计
    """
    __tablename__ = "postback_conversions"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 租户关联
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True, comment="租户ID")
    
    # Involve Asia核心字段
    conversion_id = Column(String(50), nullable=False, index=True, comment="Involve Asia系统唯一ID")
    offer_id = Column(String(50), comment="广告主或Offer唯一参考ID")
    offer_name = Column(Text, comment="广告主名称")
    
    # 时间字段
    datetime_conversion = Column(DateTime(timezone=True), comment="广告主系统转换的日期和时间")
    datetime_conversion_updated = Column(DateTime(timezone=True), comment="广告主系统最后更新转换的日期和时间")
    
    # 订单信息
    order_id = Column(String(100), comment="广告主系统的订单或预订ID")
    
    # 金额字段 (使用NUMERIC确保精度)
    sale_amount_local = Column(Numeric(15, 2), comment="本地销售金额或用户向广告主支付的金额")
    myr_sale_amount = Column(Numeric(15, 2), comment="马来西亚林吉特销售金额")
    usd_sale_amount = Column(Numeric(15, 2), comment="美元销售金额")
    
    # 佣金字段
    payout_local = Column(Numeric(15, 2), comment="基于本地货币的佣金")
    myr_payout = Column(Numeric(15, 2), comment="马来西亚林吉特佣金")
    usd_payout = Column(Numeric(15, 2), comment="美元佣金")
    
    # 货币代码
    conversion_currency = Column(String(3), comment="默认转换货币代码 (ISO 4217)")
    
    # 广告主自定义参数
    adv_sub = Column(String(255), comment="广告主系统的订单或预订ID")
    adv_sub2 = Column(String(255), comment="广告主自定义参数2")
    adv_sub3 = Column(String(255), comment="广告主自定义参数3")
    adv_sub4 = Column(String(255), comment="广告主自定义参数4")
    adv_sub5 = Column(String(255), comment="广告主自定义参数5")
    
    # 发布商自定义参数
    aff_sub = Column(String(255), comment="发布商自定义参数1")
    aff_sub2 = Column(String(255), comment="发布商自定义参数2")
    aff_sub3 = Column(String(255), comment="发布商自定义参数3")
    aff_sub4 = Column(String(255), comment="发布商自定义参数4")
    
    # 状态字段
    status = Column(String(50), comment="转换状态 (Pending, Approved, Rejected, Paid, Yet to Consume)")
    offer_status = Column(String(50), comment="Offer状态 (Active, Paused)")
    
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
    tenant = relationship("Tenant", back_populates="conversions")
    
    def __repr__(self):
        return f"<PostbackConversion(id={self.id}, conversion_id='{self.conversion_id}', tenant_id={self.tenant_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "conversion_id": self.conversion_id,
            "offer_id": self.offer_id,
            "offer_name": self.offer_name,
            "datetime_conversion": self.datetime_conversion.isoformat() if self.datetime_conversion else None,
            "datetime_conversion_updated": self.datetime_conversion_updated.isoformat() if self.datetime_conversion_updated else None,
            "order_id": self.order_id,
            "sale_amount_local": float(self.sale_amount_local) if self.sale_amount_local else None,
            "myr_sale_amount": float(self.myr_sale_amount) if self.myr_sale_amount else None,
            "usd_sale_amount": float(self.usd_sale_amount) if self.usd_sale_amount else None,
            "payout_local": float(self.payout_local) if self.payout_local else None,
            "myr_payout": float(self.myr_payout) if self.myr_payout else None,
            "usd_payout": float(self.usd_payout) if self.usd_payout else None,
            "conversion_currency": self.conversion_currency,
            "adv_sub": self.adv_sub,
            "adv_sub2": self.adv_sub2,
            "adv_sub3": self.adv_sub3,
            "adv_sub4": self.adv_sub4,
            "adv_sub5": self.adv_sub5,
            "aff_sub": self.aff_sub,
            "aff_sub2": self.aff_sub2,
            "aff_sub3": self.aff_sub3,
            "aff_sub4": self.aff_sub4,
            "status": self.status,
            "offer_status": self.offer_status,
            "is_processed": self.is_processed,
            "is_duplicate": self.is_duplicate,
            "processing_error": self.processing_error,
            "raw_data": self.raw_data,
            "request_ip": self.request_ip,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_primary_amount(self) -> Optional[Decimal]:
        """获取主要金额 (优先USD，然后本地货币)"""
        if self.usd_sale_amount:
            return self.usd_sale_amount
        elif self.sale_amount_local:
            return self.sale_amount_local
        return None
    
    def get_primary_payout(self) -> Optional[Decimal]:
        """获取主要佣金 (优先USD，然后本地货币)"""
        if self.usd_payout:
            return self.usd_payout
        elif self.payout_local:
            return self.payout_local
        return None
    
    def is_valid_conversion(self) -> bool:
        """检查转换数据是否有效"""
        # 基本验证：必须有conversion_id和至少一个金额
        if not self.conversion_id:
            return False
        
        if not (self.sale_amount_local or self.usd_sale_amount or self.myr_sale_amount):
            return False
        
        return True


# 创建复合索引以提升查询性能
Index("idx_tenant_conversion", PostbackConversion.tenant_id, PostbackConversion.conversion_id, unique=True)
Index("idx_tenant_datetime", PostbackConversion.tenant_id, PostbackConversion.datetime_conversion)
Index("idx_tenant_status", PostbackConversion.tenant_id, PostbackConversion.status)
Index("idx_received_at", PostbackConversion.received_at) 
#!/usr/bin/env python3
"""
Rector平台轉化數據模型
"""

from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.models.database import Base


class RectorConversion(Base):
    """Rector平台轉化數據表"""
    
    __tablename__ = "postback_conversions_rector"
    
    # 主鍵
    id = Column(Integer, primary_key=True, index=True)
    
    # Rector平台特定參數
    conversion_id = Column(String(255), index=True, comment="轉化ID")
    click_id = Column(String(255), index=True, comment="點擊ID")
    media_id = Column(String(255), index=True, comment="媒體ID")
    sub_id = Column(String(255), index=True, comment="子ID")
    
    # 金額參數
    usd_sale_amount = Column(Numeric(10, 2), comment="美元銷售金額")
    usd_earning = Column(Numeric(10, 2), comment="美元收益")
    
    # 其他參數
    offer_name = Column(String(500), comment="Offer名稱")
    conversion_datetime = Column(DateTime, comment="轉化時間")
    
    # 系統參數
    created_at = Column(DateTime, default=func.now(), comment="記錄創建時間")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="記錄更新時間")
    
    # 原始數據存儲（JSON格式）
    raw_data = Column(JSON, comment="原始請求數據")
    
    # 處理狀態
    status = Column(String(50), default="received", comment="處理狀態")
    processing_time_ms = Column(Numeric(10, 3), comment="處理時間(毫秒)")
    
    # 請求信息
    request_method = Column(String(10), comment="請求方法")
    request_ip = Column(String(45), comment="請求IP")
    user_agent = Column(Text, comment="用戶代理")
    
    def __repr__(self):
        return f"<RectorConversion(id={self.id}, conversion_id='{self.conversion_id}', click_id='{self.click_id}', usd_earning={self.usd_earning})>"
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            "id": self.id,
            "conversion_id": self.conversion_id,
            "click_id": self.click_id,
            "media_id": self.media_id,
            "sub_id": self.sub_id,
            "usd_sale_amount": float(self.usd_sale_amount) if self.usd_sale_amount else None,
            "usd_earning": float(self.usd_earning) if self.usd_earning else None,
            "offer_name": self.offer_name,
            "conversion_datetime": self.conversion_datetime.isoformat() if self.conversion_datetime else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "status": self.status,
            "processing_time_ms": float(self.processing_time_ms) if self.processing_time_ms else None,
            "raw_data": self.raw_data
        } 
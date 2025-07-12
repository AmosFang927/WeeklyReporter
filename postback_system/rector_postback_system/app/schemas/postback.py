#!/usr/bin/env python3
"""
Postback相关的Pydantic Schema模型
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


class PostbackRequest(BaseModel):
    """
    Postback请求模型
    基于Involve Asia的Postback参数
    """
    # Involve Asia核心参数
    conversion_id: str = Field(..., description="Involve Asia系统唯一ID")
    offer_id: Optional[str] = Field(None, description="广告主或Offer唯一参考ID")
    offer_name: Optional[str] = Field(None, description="广告主名称")
    
    # 时间参数
    datetime_conversion: Optional[str] = Field(None, description="转换时间 YYYY-MM-DD HH:MM:SS")
    datetime_conversion_updated: Optional[str] = Field(None, description="转换更新时间")
    
    # 订单信息
    order_id: Optional[str] = Field(None, description="订单或预订ID")
    
    # 金额参数
    sale_amount_local: Optional[Decimal] = Field(None, description="本地销售金额")
    myr_sale_amount: Optional[Decimal] = Field(None, description="马来西亚林吉特销售金额")
    usd_sale_amount: Optional[Decimal] = Field(None, description="美元销售金额")
    
    # 佣金参数
    payout_local: Optional[Decimal] = Field(None, description="本地货币佣金")
    myr_payout: Optional[Decimal] = Field(None, description="马来西亚林吉特佣金")
    usd_payout: Optional[Decimal] = Field(None, description="美元佣金")
    
    # 货币代码
    conversion_currency: Optional[str] = Field(None, max_length=3, description="货币代码 ISO 4217")
    
    # 广告主自定义参数
    adv_sub: Optional[str] = Field(None, description="广告主自定义参数1")
    adv_sub2: Optional[str] = Field(None, description="广告主自定义参数2")
    adv_sub3: Optional[str] = Field(None, description="广告主自定义参数3")
    adv_sub4: Optional[str] = Field(None, description="广告主自定义参数4")
    adv_sub5: Optional[str] = Field(None, description="广告主自定义参数5")
    
    # 发布商自定义参数
    aff_sub: Optional[str] = Field(None, description="发布商自定义参数1")
    aff_sub2: Optional[str] = Field(None, description="发布商自定义参数2")
    aff_sub3: Optional[str] = Field(None, description="发布商自定义参数3")
    aff_sub4: Optional[str] = Field(None, description="发布商自定义参数4")
    
    # 状态参数
    status: Optional[str] = Field(None, description="转换状态")
    offer_status: Optional[str] = Field(None, description="Offer状态")
    
    @validator('conversion_currency')
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('货币代码必须是3位字母')
        return v.upper() if v else v
    
    @validator('datetime_conversion', 'datetime_conversion_updated')
    def validate_datetime(cls, v):
        if v:
            try:
                datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                raise ValueError('时间格式必须是 YYYY-MM-DD HH:MM:SS')
        return v
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class PostbackResponse(BaseModel):
    """Postback响应模型"""
    success: bool = Field(..., description="处理是否成功")
    message: str = Field(..., description="响应消息")
    conversion_id: Optional[str] = Field(None, description="转换ID")
    tenant_code: Optional[str] = Field(None, description="租户代码")
    duplicate: bool = Field(False, description="是否为重复数据")
    processing_time_ms: Optional[float] = Field(None, description="处理时间(毫秒)")


class ConversionQuery(BaseModel):
    """转换数据查询模型"""
    tenant_code: Optional[str] = Field(None, description="租户代码")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")
    conversion_id: Optional[str] = Field(None, description="转换ID")
    order_id: Optional[str] = Field(None, description="订单ID")
    status: Optional[str] = Field(None, description="状态")
    min_amount: Optional[Decimal] = Field(None, description="最小金额")
    max_amount: Optional[Decimal] = Field(None, description="最大金额")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=1000, description="每页大小")
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class ConversionDetail(BaseModel):
    """转换详情模型"""
    id: int
    tenant_id: int
    conversion_id: str
    offer_id: Optional[str]
    offer_name: Optional[str]
    datetime_conversion: Optional[datetime]
    order_id: Optional[str]
    sale_amount_local: Optional[Decimal]
    usd_sale_amount: Optional[Decimal]
    usd_payout: Optional[Decimal]
    conversion_currency: Optional[str]
    aff_sub: Optional[str]
    aff_sub2: Optional[str]
    status: Optional[str]
    is_duplicate: bool
    received_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str
        }


class ConversionSummary(BaseModel):
    """转换汇总模型"""
    total_conversions: int = Field(..., description="总转换数")
    total_amount_usd: Decimal = Field(..., description="总金额(USD)")
    total_payout_usd: Decimal = Field(..., description="总佣金(USD)")
    unique_orders: int = Field(..., description="唯一订单数")
    duplicate_count: int = Field(..., description="重复数据数量")
    avg_amount_usd: Decimal = Field(..., description="平均金额(USD)")
    date_range: Dict[str, Optional[datetime]] = Field(..., description="日期范围")
    status_breakdown: Dict[str, int] = Field(..., description="状态分布")
    currency_breakdown: Dict[str, int] = Field(..., description="货币分布")
    
    class Config:
        json_encoders = {
            Decimal: str
        }


class ConversionsResponse(BaseModel):
    """转换列表响应模型"""
    conversions: List[ConversionDetail] = Field(..., description="转换列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")
    summary: Optional[ConversionSummary] = Field(None, description="汇总信息")


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(..., description="检查时间")
    database: str = Field(..., description="数据库状态")
    redis: str = Field(..., description="Redis状态")
    uptime_seconds: float = Field(..., description="运行时间(秒)")
    version: str = Field(..., description="版本号") 
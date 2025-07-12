#!/usr/bin/env python3
"""
租户相关的Pydantic Schema模型
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime


class TenantCreate(BaseModel):
    """创建租户模型"""
    tenant_code: str = Field(..., min_length=1, max_length=50, description="租户唯一代码")
    tenant_name: str = Field(..., min_length=1, max_length=100, description="租户名称")
    ts_token: Optional[str] = Field(None, max_length=255, description="TS Token")
    tlm_token: Optional[str] = Field(None, max_length=255, description="TLM Token")
    ts_param: Optional[str] = Field(None, max_length=100, description="TS Parameter")
    description: Optional[str] = Field(None, description="租户描述")
    contact_email: Optional[EmailStr] = Field(None, description="联系邮箱")
    contact_phone: Optional[str] = Field(None, max_length=50, description="联系电话")
    max_daily_requests: int = Field(100000, ge=1, description="每日最大请求数")
    enable_duplicate_check: bool = Field(True, description="是否启用重复检查")
    data_retention_days: int = Field(7, ge=1, le=365, description="数据保留天数")
    
    @validator('tenant_code')
    def validate_tenant_code(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('租户代码只能包含字母、数字、下划线和横线')
        return v.lower()


class TenantUpdate(BaseModel):
    """更新租户模型"""
    tenant_name: Optional[str] = Field(None, min_length=1, max_length=100, description="租户名称")
    ts_token: Optional[str] = Field(None, max_length=255, description="TS Token")
    tlm_token: Optional[str] = Field(None, max_length=255, description="TLM Token")
    ts_param: Optional[str] = Field(None, max_length=100, description="TS Parameter")
    description: Optional[str] = Field(None, description="租户描述")
    contact_email: Optional[EmailStr] = Field(None, description="联系邮箱")
    contact_phone: Optional[str] = Field(None, max_length=50, description="联系电话")
    max_daily_requests: Optional[int] = Field(None, ge=1, description="每日最大请求数")
    enable_duplicate_check: Optional[bool] = Field(None, description="是否启用重复检查")
    data_retention_days: Optional[int] = Field(None, ge=1, le=365, description="数据保留天数")
    is_active: Optional[bool] = Field(None, description="是否激活")


class TenantResponse(BaseModel):
    """租户响应模型"""
    id: int
    tenant_code: str
    tenant_name: str
    ts_token: Optional[str]
    tlm_token: Optional[str]
    ts_param: Optional[str]
    description: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    max_daily_requests: int
    enable_duplicate_check: bool
    data_retention_days: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantQuery(BaseModel):
    """租户查询模型"""
    tenant_code: Optional[str] = Field(None, description="租户代码")
    tenant_name: Optional[str] = Field(None, description="租户名称")
    is_active: Optional[bool] = Field(None, description="是否激活")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=1000, description="每页大小")


class TenantsResponse(BaseModel):
    """租户列表响应模型"""
    tenants: List[TenantResponse] = Field(..., description="租户列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class TenantStats(BaseModel):
    """租户统计模型"""
    tenant_id: int
    tenant_code: str
    tenant_name: str
    total_conversions: int = Field(..., description="总转换数")
    today_conversions: int = Field(..., description="今日转换数")
    total_amount_usd: float = Field(..., description="总金额(USD)")
    avg_daily_requests: float = Field(..., description="日均请求数")
    duplicate_rate: float = Field(..., description="重复率(%)")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")


class TenantStatsResponse(BaseModel):
    """租户统计响应模型"""
    stats: List[TenantStats] = Field(..., description="租户统计列表")
    total_tenants: int = Field(..., description="总租户数")
    active_tenants: int = Field(..., description="活跃租户数")
    total_conversions: int = Field(..., description="总转换数")
    total_amount_usd: float = Field(..., description="总金额(USD)") 
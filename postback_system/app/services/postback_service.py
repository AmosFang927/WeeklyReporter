#!/usr/bin/env python3
"""
Postback核心业务逻辑服务
负责处理转化数据的接收、验证、存储和查询
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from fastapi import Request

from app.models.tenant import Tenant
from app.models.postback import PostbackConversion
from app.schemas.postback import (
    PostbackRequest, 
    PostbackResponse, 
    ConversionQuery, 
    ConversionsResponse,
    ConversionDetail
)
from app.config import settings

logger = logging.getLogger(__name__)


def serialize_for_json(obj: Any) -> Any:
    """序列化对象以支持JSON存储"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    return obj


class PostbackService:
    """Postback业务逻辑服务"""
    
    async def process_postback(
        self,
        tenant: Tenant,
        postback_data: PostbackRequest,
        request: Request,
        db: AsyncSession
    ) -> PostbackResponse:
        """处理Postback数据的核心方法"""
        try:
            # 1. 重复检查
            is_duplicate = False
            if tenant.enable_duplicate_check:
                is_duplicate = await self._check_duplicate(
                    tenant.id, 
                    postback_data.conversion_id, 
                    db
                )
            
            # 2. 构造数据库记录
            conversion_record = PostbackConversion(
                tenant_id=tenant.id,
                conversion_id=postback_data.conversion_id,
                offer_id=postback_data.offer_id,
                offer_name=postback_data.offer_name,
                datetime_conversion=self._parse_datetime(postback_data.datetime_conversion),
                order_id=postback_data.order_id,
                sale_amount_local=postback_data.sale_amount_local,
                myr_sale_amount=postback_data.myr_sale_amount,
                usd_sale_amount=postback_data.usd_sale_amount,
                payout_local=postback_data.payout_local,
                myr_payout=postback_data.myr_payout,
                usd_payout=postback_data.usd_payout,
                conversion_currency=postback_data.conversion_currency,
                aff_sub=postback_data.aff_sub,
                aff_sub2=postback_data.aff_sub2,
                status=postback_data.status,
                is_duplicate=is_duplicate,
                raw_data=serialize_for_json(postback_data.dict()),
                request_headers=serialize_for_json(dict(request.headers)),
                request_ip=self._get_client_ip(request)
            )
            
            # 3. 保存到数据库
            if not is_duplicate:
                db.add(conversion_record)
                await db.commit()
                await db.refresh(conversion_record)
            
            return PostbackResponse(
                success=True,
                message="Postback处理成功",
                conversion_id=postback_data.conversion_id,
                tenant_code=tenant.tenant_code,
                duplicate=is_duplicate
            )
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Postback处理异常: {str(e)}")
            return PostbackResponse(
                success=False,
                message=f"处理失败: {str(e)}",
                conversion_id=postback_data.conversion_id,
                tenant_code=tenant.tenant_code
            )
    
    async def _check_duplicate(self, tenant_id: int, conversion_id: str, db: AsyncSession) -> bool:
        """检查重复转换"""
        query = select(PostbackConversion).where(
            and_(
                PostbackConversion.tenant_id == tenant_id,
                PostbackConversion.conversion_id == conversion_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none() is not None
    
    def _parse_datetime(self, datetime_str: Optional[str]) -> Optional[datetime]:
        """解析时间字符串"""
        if not datetime_str:
            return None
        try:
            return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        forwarded_ips = request.headers.get("X-Forwarded-For")
        if forwarded_ips:
            return forwarded_ips.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def query_conversions(self, query: ConversionQuery, db: AsyncSession) -> ConversionsResponse:
        """查询转换数据"""
        base_query = select(PostbackConversion)
        
        # 添加分页
        offset = (query.page - 1) * query.page_size
        result = await db.execute(
            base_query.order_by(desc(PostbackConversion.received_at))
                     .offset(offset)
                     .limit(query.page_size)
        )
        conversions = result.scalars().all()
        
        # 计算总数
        count_result = await db.execute(select(func.count(PostbackConversion.id)))
        total = count_result.scalar()
        
        conversion_details = [ConversionDetail.from_orm(conv) for conv in conversions]
        total_pages = (total + query.page_size - 1) // query.page_size
        
        return ConversionsResponse(
            conversions=conversion_details,
            total=total,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages
        )
    
    async def get_stats(self, tenant_code: Optional[str], hours: int, db: AsyncSession) -> Dict[str, Any]:
        """获取统计信息"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        query = select(PostbackConversion).where(
            PostbackConversion.received_at >= start_time
        )
        
        result = await db.execute(query)
        conversions = result.scalars().all()
        
        total_conversions = len(conversions)
        total_usd_amount = sum((c.usd_sale_amount or Decimal(0)) for c in conversions)
        
        return {
            'total_conversions': total_conversions,
            'total_usd_amount': float(total_usd_amount),
            'period_hours': hours,
            'requests_per_hour': total_conversions / hours if hours > 0 else 0
        }
    
    async def post_process_conversion(self, conversion_id: str, tenant_id: int):
        """异步后处理转换数据"""
        logger.info(f"后处理转换: conversion_id={conversion_id}, tenant_id={tenant_id}")
        # TODO: 添加ML预处理逻辑 
#!/usr/bin/env python3
"""
Postback接收API路由
核心功能：接收和处理转化回传数据
"""

import time
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any

from app.models.database import get_db
from app.schemas.postback import PostbackRequest, PostbackResponse, ConversionQuery, ConversionsResponse
from app.services.postback_service import PostbackService
from app.services.token_service import TokenService
from app.middleware.auth import verify_tenant_token
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/postback", tags=["Postback"])


# ====== 新增：ByteC定制化Endpoint ======
@router.get("/involve/event", response_class=PlainTextResponse)
async def bytec_involve_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    # ByteC定制参数映射
    conversion_id: str = Query(..., description="转换ID"),
    click_id: Optional[str] = Query(None, description="点击ID (映射到aff_sub)"),
    media_id: Optional[str] = Query(None, description="媒体ID (映射到aff_sub2)"),
    rewards: Optional[float] = Query(None, description="奖励金额 (映射到usd_payout)", alias="rewars"),  # 支持拼写错误
    event: Optional[str] = Query(None, description="事件类型 (映射到aff_sub3)"),
    event_time: Optional[str] = Query(None, description="事件时间 (映射到datetime_conversion)"),
    offer_name: Optional[str] = Query(None, description="Offer名称"),
    datetime_conversion: Optional[str] = Query(None, description="转换时间"),
    usd_sale_amount: Optional[float] = Query(None, description="美元销售金额"),
    
    # 可选的其他标准参数
    offer_id: Optional[str] = Query(None, description="Offer ID"),
    order_id: Optional[str] = Query(None, description="订单ID"),
    status: Optional[str] = Query(None, description="状态"),
    
    # Token参数（用于租户识别）
    ts_token: Optional[str] = Query(None, description="TS Token"),
    ts_param: Optional[str] = Query(None, description="TS Parameter"),
    tlm_token: Optional[str] = Query(None, description="TLM Token"),
    
    db: AsyncSession = Depends(get_db)
):
    """
    ByteC定制化Involve Postback端点
    
    Endpoint: /postback/involve/event
    映射: https://network.bytec.com/involve/event
    
    参数映射:
    - click_id -> aff_sub
    - media_id -> aff_sub2  
    - rewards/rewars -> usd_payout
    - event -> aff_sub3
    - event_time -> datetime_conversion (如果datetime_conversion为空)
    """
    start_time = time.time()
    
    try:
        # 1. 参数映射和清理
        # 使用event_time作为datetime_conversion的后备值
        final_datetime_conversion = datetime_conversion or event_time
        
        # 2. 租户验证和识别
        token_service = TokenService()
        tenant = await token_service.identify_tenant(
            ts_token=ts_token,
            ts_param=ts_param, 
            tlm_token=tlm_token,
            db=db
        )
        
        if not tenant:
            logger.warning(f"无法识别租户，tokens: ts_token={ts_token}, ts_param={ts_param}, tlm_token={tlm_token}")
            return PlainTextResponse("INVALID_TENANT", status_code=400)
        
        # 3. 构造Postback请求数据 (参数映射)
        from decimal import Decimal
        postback_data = PostbackRequest(
            conversion_id=conversion_id,
            offer_id=offer_id,
            offer_name=offer_name,
            datetime_conversion=final_datetime_conversion,
            order_id=order_id,
            usd_sale_amount=Decimal(str(usd_sale_amount)) if usd_sale_amount is not None else None,
            usd_payout=Decimal(str(rewards)) if rewards is not None else None,  # rewards -> usd_payout
            aff_sub=click_id,    # click_id -> aff_sub
            aff_sub2=media_id,   # media_id -> aff_sub2
            aff_sub3=event,      # event -> aff_sub3
            status=status
        )
        
        # 4. 处理Postback数据
        postback_service = PostbackService()
        result = await postback_service.process_postback(
            tenant=tenant,
            postback_data=postback_data,
            request=request,
            db=db
        )
        
        # 5. 异步后处理任务
        if result.success and not result.duplicate:
            background_tasks.add_task(
                postback_service.post_process_conversion,
                conversion_id=result.conversion_id,
                tenant_id=tenant.id
            )
        
        # 6. 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        
        # 7. 记录成功日志
        logger.info(f"ByteC Involve Postback处理完成: tenant={tenant.tenant_code}, "
                   f"conversion_id={conversion_id}, click_id={click_id}, "
                   f"media_id={media_id}, duplicate={result.duplicate}, "
                   f"time={processing_time:.2f}ms")
        
        # 8. 返回成功响应
        return PlainTextResponse("OK", status_code=200)
        
    except ValueError as e:
        logger.warning(f"ByteC Involve Postback参数验证失败: {str(e)}")
        return PlainTextResponse("INVALID_PARAMS", status_code=400)
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"ByteC Involve Postback处理异常: conversion_id={conversion_id}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        return PlainTextResponse("ERROR", status_code=500)


# ====== 原有的通用Endpoint ======
@router.get("/", response_class=PlainTextResponse)
async def postback_endpoint_get(
    request: Request,
    background_tasks: BackgroundTasks,
    # Involve Asia核心参数
    conversion_id: str = Query(..., description="转换ID"),
    offer_id: Optional[str] = Query(None, description="Offer ID"),
    offer_name: Optional[str] = Query(None, description="Offer名称"),
    datetime_conversion: Optional[str] = Query(None, description="转换时间"),
    datetime_conversion_updated: Optional[str] = Query(None, description="更新时间"),
    order_id: Optional[str] = Query(None, description="订单ID"),
    
    # 金额参数
    sale_amount_local: Optional[float] = Query(None, description="本地金额"),
    myr_sale_amount: Optional[float] = Query(None, description="马币金额"),
    usd_sale_amount: Optional[float] = Query(None, description="美元金额"),
    
    # 佣金参数
    payout_local: Optional[float] = Query(None, description="本地佣金"),
    myr_payout: Optional[float] = Query(None, description="马币佣金"),
    usd_payout: Optional[float] = Query(None, description="美元佣金"),
    
    # 其他参数
    conversion_currency: Optional[str] = Query(None, description="货币代码"),
    adv_sub: Optional[str] = Query(None, description="广告主参数1"),
    adv_sub2: Optional[str] = Query(None, description="广告主参数2"),
    adv_sub3: Optional[str] = Query(None, description="广告主参数3"),
    adv_sub4: Optional[str] = Query(None, description="广告主参数4"),
    adv_sub5: Optional[str] = Query(None, description="广告主参数5"),
    aff_sub: Optional[str] = Query(None, description="发布商参数1"),
    aff_sub2: Optional[str] = Query(None, description="发布商参数2"),
    aff_sub3: Optional[str] = Query(None, description="发布商参数3"),
    aff_sub4: Optional[str] = Query(None, description="发布商参数4"),
    status: Optional[str] = Query(None, description="状态"),
    offer_status: Optional[str] = Query(None, description="Offer状态"),
    
    # Token参数（用于租户识别）
    ts_token: Optional[str] = Query(None, description="TS Token"),
    ts_param: Optional[str] = Query(None, description="TS Parameter"),
    tlm_token: Optional[str] = Query(None, description="TLM Token"),
    
    db: AsyncSession = Depends(get_db)
):
    """
    Postback接收端点 (GET方法)
    
    接收电商平台的转化回传数据，这是系统的核心入口点。
    支持Involve Asia标准的所有参数，同时支持多租户Token验证。
    """
    start_time = time.time()
    
    try:
        # 1. 租户验证和识别
        token_service = TokenService()
        tenant = await token_service.identify_tenant(
            ts_token=ts_token,
            ts_param=ts_param, 
            tlm_token=tlm_token,
            db=db
        )
        
        if not tenant:
            logger.warning(f"无法识别租户，tokens: ts_token={ts_token}, ts_param={ts_param}, tlm_token={tlm_token}")
            return PlainTextResponse("INVALID_TENANT", status_code=400)
        
        # 2. 构造Postback请求数据
        postback_data = PostbackRequest(
            conversion_id=conversion_id,
            offer_id=offer_id,
            offer_name=offer_name,
            datetime_conversion=datetime_conversion,
            datetime_conversion_updated=datetime_conversion_updated,
            order_id=order_id,
            sale_amount_local=sale_amount_local,
            myr_sale_amount=myr_sale_amount,
            usd_sale_amount=usd_sale_amount,
            payout_local=payout_local,
            myr_payout=myr_payout,
            usd_payout=usd_payout,
            conversion_currency=conversion_currency,
            adv_sub=adv_sub,
            adv_sub2=adv_sub2,
            adv_sub3=adv_sub3,
            adv_sub4=adv_sub4,
            adv_sub5=adv_sub5,
            aff_sub=aff_sub,
            aff_sub2=aff_sub2,
            aff_sub3=aff_sub3,
            aff_sub4=aff_sub4,
            status=status,
            offer_status=offer_status
        )
        
        # 3. 处理Postback数据
        postback_service = PostbackService()
        result = await postback_service.process_postback(
            tenant=tenant,
            postback_data=postback_data,
            request=request,
            db=db
        )
        
        # 4. 异步后处理任务
        if result.success and not result.duplicate:
            background_tasks.add_task(
                postback_service.post_process_conversion,
                conversion_id=result.conversion_id,
                tenant_id=tenant.id
            )
        
        # 5. 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        
        # 6. 记录成功日志
        logger.info(f"Postback处理完成: tenant={tenant.tenant_code}, "
                   f"conversion_id={conversion_id}, "
                   f"duplicate={result.duplicate}, "
                   f"time={processing_time:.2f}ms")
        
        # 7. 返回成功响应 (根据行业标准，通常返回OK)
        return PlainTextResponse("OK", status_code=200)
        
    except ValueError as e:
        logger.warning(f"Postback参数验证失败: {str(e)}")
        return PlainTextResponse("INVALID_PARAMS", status_code=400)
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Postback处理异常: conversion_id={conversion_id}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        return PlainTextResponse("ERROR", status_code=500)


@router.post("/")
async def postback_endpoint_post(
    request: Request,
    postback_data: PostbackRequest,
    background_tasks: BackgroundTasks,
    ts_token: Optional[str] = Query(None, description="TS Token"),
    ts_param: Optional[str] = Query(None, description="TS Parameter"),
    tlm_token: Optional[str] = Query(None, description="TLM Token"),
    db: AsyncSession = Depends(get_db)
) -> PostbackResponse:
    """
    Postback接收端点 (POST方法)
    
    提供JSON格式的Postback数据接收，适用于高级集成场景。
    """
    start_time = time.time()
    
    try:
        # 1. 租户验证和识别
        token_service = TokenService()
        tenant = await token_service.identify_tenant(
            ts_token=ts_token,
            ts_param=ts_param,
            tlm_token=tlm_token,
            db=db
        )
        
        if not tenant:
            raise HTTPException(
                status_code=400,
                detail="无法识别租户，请检查Token参数"
            )
        
        # 2. 处理Postback数据
        postback_service = PostbackService()
        result = await postback_service.process_postback(
            tenant=tenant,
            postback_data=postback_data,
            request=request,
            db=db
        )
        
        # 3. 异步后处理任务
        if result.success and not result.duplicate:
            background_tasks.add_task(
                postback_service.post_process_conversion,
                conversion_id=result.conversion_id,
                tenant_id=tenant.id
            )
        
        # 4. 计算处理时间并返回详细响应
        processing_time = (time.time() - start_time) * 1000
        result.processing_time_ms = processing_time
        
        logger.info(f"Postback(POST)处理完成: tenant={tenant.tenant_code}, "
                   f"conversion_id={postback_data.conversion_id}, "
                   f"duplicate={result.duplicate}, "
                   f"time={processing_time:.2f}ms")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Postback(POST)处理异常: "
                    f"conversion_id={postback_data.conversion_id}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.get("/conversions")
async def get_conversions(
    query: ConversionQuery = Depends(),
    db: AsyncSession = Depends(get_db)
) -> ConversionsResponse:
    """
    查询转换数据
    
    提供灵活的转换数据查询功能，支持多种筛选条件。
    """
    try:
        postback_service = PostbackService()
        result = await postback_service.query_conversions(query, db)
        return result
        
    except Exception as e:
        logger.error(f"查询转换数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    健康检查端点
    
    检查Postback服务的健康状态，包括数据库连接等。
    """
    try:
        # 检查数据库连接
        await db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "connected",
            "message": "Postback service is running normally"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/stats")
async def get_stats(
    tenant_code: Optional[str] = Query(None, description="租户代码"),
    hours: int = Query(24, description="统计时间范围(小时)"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取Postback统计信息
    
    提供实时的转换统计数据，用于监控和分析。
    """
    try:
        postback_service = PostbackService()
        stats = await postback_service.get_stats(tenant_code, hours, db)
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}") 
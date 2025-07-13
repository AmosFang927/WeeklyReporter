#!/usr/bin/env python3
"""
Postback接收API路由
核心功能：接收和处理转化回传数据
"""

import time
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import logging
from datetime import datetime

# 简化的导入，避免复杂依赖
try:
    from app.models.database import get_db
    from app.schemas.postback import PostbackRequest, PostbackResponse, ConversionQuery, ConversionsResponse
    from app.services.postback_service import PostbackService
    from app.services.token_service import TokenService
    from app.middleware.auth import verify_tenant_token
    from app.config import settings
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)

# 创建路由器，移除prefix以便直接访问 /involve/event
router = APIRouter(tags=["Postback"])

# 内存存储（用于简化测试）
postback_records = []
record_counter = 0

# 数据库存储函数
async def store_conversion_to_db(
    db: AsyncSession,
    conversion_data: Dict[str, Any],
    request_info: Dict[str, Any],
    partner_id: int = 1  # 添加partner_id参数，默认为involve_asia (ID=1)
):
    """存储转化数据到数据库"""
    try:
        # 直接插入conversions表
        from sqlalchemy import text
        import json
        
        # 解析时间
        datetime_conversion = None
        if conversion_data.get('conversion_datetime'):
            try:
                datetime_conversion = datetime.fromisoformat(conversion_data['conversion_datetime'].replace('Z', '+00:00'))
            except:
                pass
        
        # 将conversion_data转换为JSON字符串
        raw_data_json = json.dumps(conversion_data)
        
        # 插入数据，添加partner_id字段
        await db.execute(text("""
            INSERT INTO conversions (
                tenant_id, conversion_id, offer_name, 
                usd_sale_amount, usd_payout, aff_sub, 
                event_time, raw_data, created_at, partner_id
            ) VALUES (
                :tenant_id, :conversion_id, :offer_name,
                :usd_sale_amount, :usd_payout, :aff_sub,
                :event_time, :raw_data, :created_at, :partner_id
            )
        """), {
            'tenant_id': 1,  # 默认租户
            'conversion_id': conversion_data.get('conversion_id'),
            'offer_name': conversion_data.get('offer_name'),
            'usd_sale_amount': conversion_data.get('usd_sale_amount'),
            'usd_payout': conversion_data.get('usd_payout'),
            'aff_sub': conversion_data.get('aff_sub'),
            'event_time': datetime_conversion,
            'raw_data': raw_data_json,  # 使用JSON字符串
            'created_at': datetime.utcnow(),
            'partner_id': partner_id  # 添加partner_id
        })
        
        await db.commit()
        logger.info(f"✅ 数据库存储成功: conversion_id={conversion_data.get('conversion_id')}, partner_id={partner_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库存储失败: {str(e)}")
        await db.rollback()
        return False


# ====== ByteC定制化Endpoint ======
@router.get("/involve/event")
async def bytec_involve_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),  # 添加数据库依赖
    # 根据真实URL模板的参数
    sub_id: Optional[str] = Query(None, description="发布商参数1 (aff_sub)"),
    media_id: Optional[str] = Query(None, description="媒体ID (aff_sub2)"),
    click_id: Optional[str] = Query(None, description="点击ID (aff_sub3)"),
    usd_sale_amount: Optional[str] = Query(None, description="美元销售金额 (支持字符串和数字)"),
    usd_payout: Optional[str] = Query(None, description="美元佣金 (支持字符串和数字)"),
    offer_name: Optional[str] = Query(None, description="Offer名称"),
    conversion_id: Optional[str] = Query(None, description="转换ID"),
    conversion_datetime: Optional[str] = Query(None, description="转换时间"),
    
    # 额外的可选参数
    offer_id: Optional[str] = Query(None, description="Offer ID"),
    order_id: Optional[str] = Query(None, description="订单ID"),
    status: Optional[str] = Query(None, description="状态"),
    
    # Token参数（用于租户识别）
    ts_token: Optional[str] = Query(None, description="TS Token"),
    ts_param: Optional[str] = Query(None, description="TS Parameter"),
    tlm_token: Optional[str] = Query(None, description="TLM Token"),
):
    """
    ByteC定制化Involve Postback端点
    
    真实URL模板：
    https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event?sub_id={aff_sub}&media_id={aff_sub2}&click_id={aff_sub3}&usd_sale_amount={usd_sale_amount}&usd_payout={usd_payout}&offer_name={offer_name}&conversion_id={conversion_id}&conversion_datetime={conversion_datetime}
    
    参数映射：
    - sub_id -> aff_sub
    - media_id -> aff_sub2
    - click_id -> aff_sub3
    - usd_sale_amount -> usd_sale_amount
    - usd_payout -> usd_payout
    - offer_name -> offer_name
    - conversion_id -> conversion_id
    - conversion_datetime -> datetime_conversion
    """
    global record_counter
    start_time = time.time()
    
    try:
        record_counter += 1
        
        # 安全转换字符串到数字的函数
        def safe_float_convert(value):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    # 尝试转换为数字
                    return float(value)
                except (ValueError, TypeError):
                    # 如果转换失败，返回None或保持原值
                    logger.warning(f"无法转换金额参数为数字: {value}")
                    return None
            return None
        
        # 转换金额参数
        usd_sale_amount_num = safe_float_convert(usd_sale_amount)
        usd_payout_num = safe_float_convert(usd_payout)
        
        # 构造处理后的数据
        processed_data = {
            "click_id": click_id,           # 直接映射
            "media_id": media_id,           # 直接映射
            "rewards": usd_payout_num,      # usd_payout -> rewards (转换后的数字)
            "conversion_id": conversion_id,  # 直接映射
            "event": None,                  # 当前模板中没有event参数
            "event_time": conversion_datetime, # conversion_datetime -> event_time
            "offer_name": offer_name,       # 直接映射
            "usd_sale_amount": usd_sale_amount_num, # 直接映射 (转换后的数字)
            "aff_sub": sub_id,              # sub_id -> aff_sub
            "aff_sub2": media_id,           # media_id -> aff_sub2
            "aff_sub3": click_id,           # click_id -> aff_sub3
            "usd_payout": usd_payout_num,   # 直接映射 (转换后的数字)
            "datetime_conversion": conversion_datetime, # conversion_datetime -> datetime_conversion
            "raw_params": dict(request.query_params),
            "original_usd_sale_amount": usd_sale_amount,  # 保留原始值
            "original_usd_payout": usd_payout             # 保留原始值
        }
        
        # 存储到数据库
        db_success = False
        if DB_AVAILABLE and db:
            request_info = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else "unknown"
            }
            
            db_success = await store_conversion_to_db(db, processed_data, request_info, partner_id=1)  # InvolveAsia ID=1
        
        # 存储到内存记录（备用）
        record = {
            "id": record_counter,
            "timestamp": time.time(),
            "method": "GET",
            "endpoint": "/involve/event",
            "data": processed_data,
            "processing_time_ms": 0,
            "db_stored": db_success
        }
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        record["processing_time_ms"] = processing_time
        
        postback_records.append(record)
        
        # 记录日志
        logger.info(f"ByteC Involve Postback处理完成: conversion_id={conversion_id}, "
                   f"click_id={click_id}, media_id={media_id}, "
                   f"usd_payout={usd_payout}, db_stored={db_success}, time={processing_time:.2f}ms")
        
        # 返回JSON响应（便于调试）
        return JSONResponse({
            "status": "success",
            "method": "GET",
            "endpoint": "/involve/event",
            "data": processed_data,
            "record_id": record_counter,
            "db_stored": db_success,
            "message": "Event received and stored successfully"
        })
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"ByteC Involve Postback处理异常: conversion_id={conversion_id}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        return JSONResponse({
            "status": "error",
            "method": "GET",
            "endpoint": "/involve/event",
            "error": str(e),
            "message": "Event processing failed"
        }, status_code=500)


@router.post("/involve/event")
async def bytec_involve_endpoint_post(
    request: Request,
    db: AsyncSession = Depends(get_db),  # 添加数据库依赖
    # 根据真实URL模板的参数
    sub_id: Optional[str] = Query(None, description="发布商参数1 (aff_sub)"),
    media_id: Optional[str] = Query(None, description="媒体ID (aff_sub2)"),
    click_id: Optional[str] = Query(None, description="点击ID (aff_sub3)"),
    usd_sale_amount: Optional[str] = Query(None, description="美元销售金额 (支持字符串和数字)"),
    usd_payout: Optional[str] = Query(None, description="美元佣金 (支持字符串和数字)"),
    offer_name: Optional[str] = Query(None, description="Offer名称"),
    conversion_id: Optional[str] = Query(None, description="转换ID"),
    conversion_datetime: Optional[str] = Query(None, description="转换时间"),
    
    # 额外的可选参数
    offer_id: Optional[str] = Query(None, description="Offer ID"),
    order_id: Optional[str] = Query(None, description="订单ID"),
    status: Optional[str] = Query(None, description="状态"),
    
    # Token参数（用于租户识别）
    ts_token: Optional[str] = Query(None, description="TS Token"),
    ts_param: Optional[str] = Query(None, description="TS Parameter"),
    tlm_token: Optional[str] = Query(None, description="TLM Token"),
):
    """
    ByteC定制化Involve Postback端点 (POST方法)
    """
    global record_counter
    start_time = time.time()
    
    try:
        record_counter += 1
        
        # 安全转换字符串到数字的函数
        def safe_float_convert(value):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    # 尝试转换为数字
                    return float(value)
                except (ValueError, TypeError):
                    # 如果转换失败，返回None或保持原值
                    logger.warning(f"无法转换金额参数为数字: {value}")
                    return None
            return None
        
        # 尝试从POST body中获取参数
        body_data = {}
        try:
            body_data = await request.json()
        except:
            pass
        
        # 合并query参数和body参数
        final_params = {
            "sub_id": sub_id or body_data.get("sub_id"),
            "media_id": media_id or body_data.get("media_id"),
            "click_id": click_id or body_data.get("click_id"),
            "usd_sale_amount": usd_sale_amount or body_data.get("usd_sale_amount"),
            "usd_payout": usd_payout or body_data.get("usd_payout"),
            "offer_name": offer_name or body_data.get("offer_name"),
            "conversion_id": conversion_id or body_data.get("conversion_id"),
            "conversion_datetime": conversion_datetime or body_data.get("conversion_datetime"),
        }
        
        # 转换金额参数
        usd_sale_amount_num = safe_float_convert(final_params["usd_sale_amount"])
        usd_payout_num = safe_float_convert(final_params["usd_payout"])
        
        # 构造处理后的数据
        processed_data = {
            "click_id": final_params["click_id"],
            "media_id": final_params["media_id"],
            "rewards": usd_payout_num,      # 转换后的数字
            "conversion_id": final_params["conversion_id"],
            "event": None,
            "event_time": final_params["conversion_datetime"],
            "offer_name": final_params["offer_name"],
            "usd_sale_amount": usd_sale_amount_num,  # 转换后的数字
            "aff_sub": final_params["sub_id"],
            "aff_sub2": final_params["media_id"],
            "aff_sub3": final_params["click_id"],
            "usd_payout": usd_payout_num,   # 转换后的数字
            "datetime_conversion": final_params["conversion_datetime"],
            "raw_params": dict(request.query_params),
            "body_data": body_data,
            "original_usd_sale_amount": final_params["usd_sale_amount"],  # 保留原始值
            "original_usd_payout": final_params["usd_payout"]             # 保留原始值
        }
        
        # 存储到数据库
        db_success = False
        if DB_AVAILABLE and db:
            request_info = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else "unknown"
            }
            
            db_success = await store_conversion_to_db(db, processed_data, request_info, partner_id=1)  # InvolveAsia ID=1
        
        # 存储到内存记录（备用）
        record = {
            "id": record_counter,
            "timestamp": time.time(),
            "method": "POST",
            "endpoint": "/involve/event",
            "data": processed_data,
            "processing_time_ms": 0,
            "db_stored": db_success
        }
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        record["processing_time_ms"] = processing_time
        
        postback_records.append(record)
        
        # 记录日志
        logger.info(f"ByteC Involve Postback (POST) 处理完成: conversion_id={final_params['conversion_id']}, "
                   f"click_id={final_params['click_id']}, media_id={final_params['media_id']}, "
                   f"usd_payout={final_params['usd_payout']}, db_stored={db_success}, time={processing_time:.2f}ms")
        
        # 返回JSON响应
        return JSONResponse({
            "status": "success",
            "method": "POST",
            "endpoint": "/involve/event",
            "data": processed_data,
            "record_id": record_counter,
            "db_stored": db_success,
            "message": "Event received and stored successfully"
        })
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"ByteC Involve Postback (POST) 处理异常: error={str(e)}, time={processing_time:.2f}ms")
        return JSONResponse({
            "status": "error",
            "method": "POST",
            "endpoint": "/involve/event",
            "error": str(e),
            "message": "Event processing failed"
        }, status_code=500)


# ====== AccessTrade定制化Endpoint ======
@router.get("/acesstrade/event")
async def bytec_acesstrade_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),  # 添加数据库依赖
    # AccessTrade参数（与InvolveAsia相同的参数结构）
    sub_id: Optional[str] = Query(None, description="发布商参数1 (aff_sub)"),
    media_id: Optional[str] = Query(None, description="媒体ID (aff_sub2)"),
    click_id: Optional[str] = Query(None, description="点击ID (aff_sub3)"),
    usd_sale_amount: Optional[str] = Query(None, description="美元销售金额 (支持字符串和数字)"),
    usd_payout: Optional[str] = Query(None, description="美元佣金 (支持字符串和数字)"),
    offer_name: Optional[str] = Query(None, description="Offer名称"),
    conversion_id: Optional[str] = Query(None, description="转换ID"),
    conversion_datetime: Optional[str] = Query(None, description="转换时间"),
    
    # 额外的可选参数
    offer_id: Optional[str] = Query(None, description="Offer ID"),
    order_id: Optional[str] = Query(None, description="订单ID"),
    status: Optional[str] = Query(None, description="状态"),
    
    # Token参数（用于租户识别）
    ts_token: Optional[str] = Query(None, description="TS Token"),
    ts_param: Optional[str] = Query(None, description="TS Parameter"),
    tlm_token: Optional[str] = Query(None, description="TLM Token"),
):
    """
    ByteC定制化AccessTrade Postback端点
    
    真实URL模板：
    https://bytec-public-postback-472712465571.asia-southeast1.run.app/acesstrade/event?sub_id={aff_sub}&media_id={aff_sub2}&click_id={aff_sub3}&usd_sale_amount={usd_sale_amount}&usd_payout={usd_payout}&offer_name={offer_name}&conversion_id={conversion_id}&conversion_datetime={conversion_datetime}
    
    参数映射：
    - sub_id -> aff_sub
    - media_id -> aff_sub2
    - click_id -> aff_sub3
    - usd_sale_amount -> usd_sale_amount
    - usd_payout -> usd_payout
    - offer_name -> offer_name
    - conversion_id -> conversion_id
    - conversion_datetime -> datetime_conversion
    """
    global record_counter
    start_time = time.time()
    
    try:
        record_counter += 1
        
        # 安全转换字符串到数字的函数
        def safe_float_convert(value):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    # 尝试转换为数字
                    return float(value)
                except (ValueError, TypeError):
                    # 如果转换失败，返回None或保持原值
                    logger.warning(f"无法转换金额参数为数字: {value}")
                    return None
            return None
        
        # 转换金额参数
        usd_sale_amount_num = safe_float_convert(usd_sale_amount)
        usd_payout_num = safe_float_convert(usd_payout)
        
        # 构造处理后的数据
        processed_data = {
            "click_id": click_id,           # 直接映射
            "media_id": media_id,           # 直接映射
            "rewards": usd_payout_num,      # usd_payout -> rewards (转换后的数字)
            "conversion_id": conversion_id,  # 直接映射
            "event": None,                  # 当前模板中没有event参数
            "event_time": conversion_datetime, # conversion_datetime -> event_time
            "offer_name": offer_name,       # 直接映射
            "usd_sale_amount": usd_sale_amount_num, # 直接映射 (转换后的数字)
            "aff_sub": sub_id,              # sub_id -> aff_sub
            "aff_sub2": media_id,           # media_id -> aff_sub2
            "aff_sub3": click_id,           # click_id -> aff_sub3
            "usd_payout": usd_payout_num,   # 直接映射 (转换后的数字)
            "datetime_conversion": conversion_datetime, # conversion_datetime -> datetime_conversion
            "raw_params": dict(request.query_params),
            "original_usd_sale_amount": usd_sale_amount,  # 保留原始值
            "original_usd_payout": usd_payout,            # 保留原始值
            "partner": "acesstrade"                       # 标识为AccessTrade
        }
        
        # 存储到数据库
        db_success = False
        if DB_AVAILABLE and db:
            request_info = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else "unknown"
            }
            
            db_success = await store_conversion_to_db(db, processed_data, request_info, partner_id=2) # AccessTrade ID is 2
        
        # 存储到内存记录（备用）
        record = {
            "id": record_counter,
            "timestamp": time.time(),
            "method": "GET",
            "endpoint": "/acesstrade/event",
            "data": processed_data,
            "processing_time_ms": 0,
            "db_stored": db_success
        }
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        record["processing_time_ms"] = processing_time
        
        postback_records.append(record)
        
        # 记录日志
        logger.info(f"ByteC AccessTrade Postback处理完成: conversion_id={conversion_id}, "
                   f"click_id={click_id}, media_id={media_id}, "
                   f"usd_payout={usd_payout}, db_stored={db_success}, time={processing_time:.2f}ms")
        
        # 返回JSON响应（便于调试）
        return JSONResponse({
            "status": "success",
            "method": "GET",
            "endpoint": "/acesstrade/event",
            "data": processed_data,
            "record_id": record_counter,
            "db_stored": db_success,
            "message": "AccessTrade event received and stored successfully"
        })
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"ByteC AccessTrade Postback处理异常: conversion_id={conversion_id}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        return JSONResponse({
            "status": "error",
            "method": "GET",
            "endpoint": "/acesstrade/event",
            "error": str(e),
            "message": "AccessTrade event processing failed"
        }, status_code=500)


@router.get("/digenesia/event")
async def bytec_digenesia_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),  # 添加数据库依赖
    # Digenesia参数（与InvolveAsia相同的参数结构）
    sub_id: Optional[str] = Query(None, description="发布商参数1 (aff_sub)"),
    media_id: Optional[str] = Query(None, description="媒体ID (aff_sub2)"),
    click_id: Optional[str] = Query(None, description="点击ID (aff_sub3)"),
    usd_sale_amount: Optional[str] = Query(None, description="美元销售金额 (支持字符串和数字)"),
    usd_payout: Optional[str] = Query(None, description="美元佣金 (支持字符串和数字)"),
    offer_name: Optional[str] = Query(None, description="Offer名称"),
    conversion_id: Optional[str] = Query(None, description="转换ID"),
    conversion_datetime: Optional[str] = Query(None, description="转换时间"),
    
    # 额外的可选参数
    offer_id: Optional[str] = Query(None, description="Offer ID"),
    order_id: Optional[str] = Query(None, description="订单ID"),
    status: Optional[str] = Query(None, description="状态"),
    
    # Token参数（用于租户识别）
    ts_token: Optional[str] = Query(None, description="TS Token"),
    ts_param: Optional[str] = Query(None, description="TS Parameter"),
    tlm_token: Optional[str] = Query(None, description="TLM Token"),
):
    """
    ByteC定制化Digenesia Postback端点
    
    URL模板：
    https://bytec-public-postback-472712465571.asia-southeast1.run.app/digenesia/event?sub_id={aff_sub}&media_id={aff_sub2}&click_id={aff_sub3}&usd_sale_amount={usd_sale_amount}&usd_payout={usd_payout}&offer_name={offer_name}&conversion_id={conversion_id}&conversion_datetime={conversion_datetime}
    
    参数映射：
    - sub_id -> aff_sub
    - media_id -> aff_sub2
    - click_id -> aff_sub3
    - usd_sale_amount -> usd_sale_amount
    - usd_payout -> usd_payout
    - offer_name -> offer_name
    - conversion_id -> conversion_id
    - conversion_datetime -> datetime_conversion
    """
    global record_counter
    start_time = time.time()
    
    try:
        record_counter += 1
        
        # 安全转换字符串到数字的函数
        def safe_float_convert(value):
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    # 尝试转换为数字
                    return float(value)
                except (ValueError, TypeError):
                    # 如果转换失败，返回None或保持原值
                    logger.warning(f"无法转换金额参数为数字: {value}")
                    return None
            return None
        
        # 转换金额参数
        usd_sale_amount_num = safe_float_convert(usd_sale_amount)
        usd_payout_num = safe_float_convert(usd_payout)
        
        # 构造处理后的数据
        processed_data = {
            "click_id": click_id,           # 直接映射
            "media_id": media_id,           # 直接映射
            "rewards": usd_payout_num,      # usd_payout -> rewards (转换后的数字)
            "conversion_id": conversion_id,  # 直接映射
            "event": None,                  # 当前模板中没有event参数
            "event_time": conversion_datetime, # conversion_datetime -> event_time
            "offer_name": offer_name,       # 直接映射
            "usd_sale_amount": usd_sale_amount_num, # 直接映射 (转换后的数字)
            "aff_sub": sub_id,              # sub_id -> aff_sub
            "aff_sub2": media_id,           # media_id -> aff_sub2
            "aff_sub3": click_id,           # click_id -> aff_sub3
            "usd_payout": usd_payout_num,   # 直接映射 (转换后的数字)
            "datetime_conversion": conversion_datetime, # conversion_datetime -> datetime_conversion
            "raw_params": dict(request.query_params),
            "original_usd_sale_amount": usd_sale_amount,  # 保留原始值
            "original_usd_payout": usd_payout,             # 保留原始值
            "partner": "digenesia"          # 添加partner标识
        }
        
        # 存储到数据库
        db_success = False
        if DB_AVAILABLE and db:
            request_info = {
                "method": request.method,
                "url": str(request.url),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else "unknown"
            }
            
            db_success = await store_conversion_to_db(db, processed_data, request_info, partner_id=2)  # Digenesia ID=2
        
        # 存储到内存记录（备用）
        record = {
            "id": record_counter,
            "timestamp": time.time(),
            "method": "GET",
            "endpoint": "/digenesia/event",
            "data": processed_data,
            "processing_time_ms": 0,
            "db_stored": db_success
        }
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        record["processing_time_ms"] = processing_time
        
        postback_records.append(record)
        
        # 记录日志
        logger.info(f"ByteC Digenesia Postback处理完成: conversion_id={conversion_id}, "
                   f"click_id={click_id}, media_id={media_id}, "
                   f"usd_payout={usd_payout}, db_stored={db_success}, time={processing_time:.2f}ms")
        
        # 返回JSON响应（便于调试）
        return JSONResponse({
            "status": "success",
            "method": "GET",
            "endpoint": "/digenesia/event",
            "data": processed_data,
            "record_id": record_counter,
            "db_stored": db_success,
            "message": "Digenesia event received and stored successfully"
        })
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"ByteC Digenesia Postback处理异常: conversion_id={conversion_id}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        return JSONResponse({
            "status": "error",
            "method": "GET",
            "endpoint": "/digenesia/event",
            "error": str(e),
            "message": "Digenesia event processing failed"
        }, status_code=500)


# ====== 辅助端点 ======
@router.get("/involve/records")
async def get_involve_records(limit: int = Query(10, description="返回记录数量")):
    """
    获取最近的involve事件记录
    """
    recent_records = postback_records[-limit:] if postback_records else []
    return {
        "status": "success",
        "total_records": len(postback_records),
        "recent_records": recent_records,
        "message": f"返回最近{len(recent_records)}条记录"
    }


@router.get("/involve/health")
async def involve_health_check():
    """
    Involve系统健康检查
    """
    return {
        "status": "healthy",
        "service": "ByteC Postback System",
        "endpoint": "/involve/event",
        "methods": ["GET", "POST"],
        "total_records": len(postback_records),
        "timestamp": time.time(),
        "database_enabled": DB_AVAILABLE
    }

# 添加数据库验证endpoint
@router.get("/involve/db-test")
async def involve_db_test(db: AsyncSession = Depends(get_db)):
    """
    测试数据库连接和查询
    """
    try:
        from sqlalchemy import text
        
        # 测试数据库连接
        result = await db.execute(text("SELECT COUNT(*) FROM conversions WHERE DATE(created_at) = CURRENT_DATE"))
        today_count = result.scalar()
        
        # 获取最新的5条记录
        result = await db.execute(text("""
            SELECT conversion_id, offer_name, usd_sale_amount, usd_payout, created_at 
            FROM conversions 
            ORDER BY created_at DESC 
            LIMIT 5
        """))
        recent_records = result.fetchall()
        
        return {
            "status": "success",
            "database_connection": "ok",
            "today_conversions": today_count,
            "recent_records": [
                {
                    "conversion_id": row[0],
                    "offer_name": row[1],
                    "usd_sale_amount": float(row[2]) if row[2] else None,
                    "usd_payout": float(row[3]) if row[3] else None,
                    "created_at": row[4].isoformat() if row[4] else None
                }
                for row in recent_records
            ]
        }
        
    except Exception as e:
        logger.error(f"数据库测试失败: {str(e)}")
        return {
            "status": "error",
            "database_connection": "failed",
            "error": str(e)
        }


# ====== 原有的通用Endpoint ======
@router.get("/postback/")
async def postback_endpoint_get(
    request: Request,
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
):
    """
    Postback接收端点 (GET方法)
    
    接收电商平台的转化回传数据，这是系统的核心入口点。
    支持Involve Asia标准的所有参数，同时支持多租户Token验证。
    """
    global record_counter
    start_time = time.time()
    
    try:
        record_counter += 1
        
        # 构造处理后的数据
        processed_data = {
            "conversion_id": conversion_id,
            "offer_id": offer_id,
            "offer_name": offer_name,
            "datetime_conversion": datetime_conversion,
            "datetime_conversion_updated": datetime_conversion_updated,
            "order_id": order_id,
            "sale_amount_local": sale_amount_local,
            "myr_sale_amount": myr_sale_amount,
            "usd_sale_amount": usd_sale_amount,
            "payout_local": payout_local,
            "myr_payout": myr_payout,
            "usd_payout": usd_payout,
            "conversion_currency": conversion_currency,
            "adv_sub": adv_sub,
            "adv_sub2": adv_sub2,
            "adv_sub3": adv_sub3,
            "adv_sub4": adv_sub4,
            "adv_sub5": adv_sub5,
            "aff_sub": aff_sub,
            "aff_sub2": aff_sub2,
            "aff_sub3": aff_sub3,
            "aff_sub4": aff_sub4,
            "status": status,
            "offer_status": offer_status,
            "ts_token": ts_token,
            "ts_param": ts_param,
            "tlm_token": tlm_token,
            "raw_params": dict(request.query_params)
        }
        
        # 存储到内存记录
        record = {
            "id": record_counter,
            "timestamp": time.time(),
            "method": "GET",
            "endpoint": "/postback/",
            "data": processed_data,
            "processing_time_ms": 0
        }
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        record["processing_time_ms"] = processing_time
        
        postback_records.append(record)
        
        # 记录日志
        logger.info(f"Postback处理完成: conversion_id={conversion_id}, "
                   f"time={processing_time:.2f}ms")
        
        # 返回JSON响应
        return JSONResponse({
            "status": "success",
            "method": "GET",
            "endpoint": "/postback/",
            "data": processed_data,
            "record_id": record_counter,
            "message": "Postback received successfully"
        })
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Postback处理异常: conversion_id={conversion_id}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        return JSONResponse({
            "status": "error",
            "method": "GET",
            "endpoint": "/postback/",
            "error": str(e),
            "message": "Postback processing failed"
        }, status_code=500)


@router.post("/postback/")
async def postback_endpoint_post(
    request: Request,
    ts_token: Optional[str] = Query(None, description="TS Token"),
    ts_param: Optional[str] = Query(None, description="TS Parameter"),
    tlm_token: Optional[str] = Query(None, description="TLM Token"),
):
    """
    Postback接收端点 (POST方法)
    
    提供JSON格式的Postback数据接收，适用于高级集成场景。
    """
    global record_counter
    start_time = time.time()
    
    try:
        record_counter += 1
        
        # 尝试从POST body中获取数据
        body_data = {}
        try:
            body_data = await request.json()
        except:
            pass
        
        # 合并query参数和body参数
        all_params = dict(request.query_params)
        all_params.update(body_data)
        
        # 构造处理后的数据
        processed_data = {
            "ts_token": ts_token,
            "ts_param": ts_param,
            "tlm_token": tlm_token,
            "body_data": body_data,
            "query_params": dict(request.query_params),
            "all_params": all_params,
            "content_type": request.headers.get("content-type", "")
        }
        
        # 存储到内存记录
        record = {
            "id": record_counter,
            "timestamp": time.time(),
            "method": "POST",
            "endpoint": "/postback/",
            "data": processed_data,
            "processing_time_ms": 0
        }
        
        # 计算处理时间
        processing_time = (time.time() - start_time) * 1000
        record["processing_time_ms"] = processing_time
        
        postback_records.append(record)
        
        logger.info(f"Postback(POST)处理完成: record_id={record_counter}, "
                   f"time={processing_time:.2f}ms")
        
        return JSONResponse({
            "status": "success",
            "method": "POST",
            "endpoint": "/postback/",
            "data": processed_data,
            "record_id": record_counter,
            "message": "Postback received successfully"
        })
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Postback(POST)处理异常: error={str(e)}, time={processing_time:.2f}ms")
        return JSONResponse({
            "status": "error",
            "method": "POST",
            "endpoint": "/postback/",
            "error": str(e),
            "message": "Postback processing failed"
        }, status_code=500)


@router.get("/postback/conversions")
async def get_conversions(
    limit: int = Query(10, description="返回记录数量"),
    offset: int = Query(0, description="偏移量"),
):
    """
    查询转换数据
    
    提供灵活的转换数据查询功能，支持多种筛选条件。
    """
    try:
        # 从内存记录中获取数据
        total_records = len(postback_records)
        records = postback_records[offset:offset + limit] if postback_records else []
        
        return {
            "status": "success",
            "total_records": total_records,
            "limit": limit,
            "offset": offset,
            "records": records,
            "message": f"返回{len(records)}条转换记录"
        }
        
    except Exception as e:
        logger.error(f"查询转换数据失败: {str(e)}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "message": "查询失败"
        }, status_code=500)


@router.get("/postback/health")
async def health_check():
    """
    健康检查端点
    
    检查Postback服务的健康状态，包括数据库连接等。
    """
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "database": "memory_storage",
            "total_records": len(postback_records),
            "message": "Postback service is running normally"
        }
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "message": "Service unavailable"
        }, status_code=503)


@router.get("/postback/stats")
async def get_stats(
    tenant_code: Optional[str] = Query(None, description="租户代码"),
    hours: int = Query(24, description="统计时间范围(小时)"),
):
    """
    获取Postback统计信息
    
    提供实时的转换统计数据，用于监控和分析。
    """
    try:
        # 计算统计数据
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        
        # 过滤指定时间范围内的记录
        recent_records = [r for r in postback_records if r.get("timestamp", 0) >= cutoff_time]
        
        # 按方法分组统计
        get_count = sum(1 for r in recent_records if r.get("method") == "GET")
        post_count = sum(1 for r in recent_records if r.get("method") == "POST")
        
        # 按端点分组统计
        involve_count = sum(1 for r in recent_records if "/involve/event" in r.get("endpoint", ""))
        postback_count = sum(1 for r in recent_records if "/postback/" in r.get("endpoint", ""))
        
        stats = {
            "status": "success",
            "time_range_hours": hours,
            "total_records": len(postback_records),
            "recent_records": len(recent_records),
            "by_method": {
                "GET": get_count,
                "POST": post_count
            },
            "by_endpoint": {
                "involve_event": involve_count,
                "postback": postback_count
            },
            "timestamp": current_time
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "message": "获取统计失败"
        }, status_code=500) 
#!/usr/bin/env python3
"""
Rector平台Postback API路由
"""

import time
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import json

# 數據庫和模型導入
try:
    from app.models.database import get_db
    from app.models.rector_conversion import RectorConversion
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(tags=["Rector-Postback"])

# 內存存儲（備用方案）
rector_records = []
rector_record_counter = 0


# ====== Rector平台專用端點 ======
@router.get("/aa7dfd32-953b-42ee-a77e-fba556a71d2f")
async def rector_postback_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    # Rector平台特定參數
    media_id: Optional[str] = Query(None, description="媒體ID"),
    sub_id: Optional[str] = Query(None, description="子ID"),
    usd_sale_amount: Optional[str] = Query(None, description="美元銷售金額"),
    usd_earning: Optional[str] = Query(None, description="美元收益"),
    offer_name: Optional[str] = Query(None, description="Offer名稱"),
    conversion_id: Optional[str] = Query(None, description="轉化ID"),
    conversion_datetime: Optional[str] = Query(None, description="轉化時間"),
    click_id: Optional[str] = Query(None, description="點擊ID"),
    
    # 可選的額外參數
    campaign_id: Optional[str] = Query(None, description="Campaign ID"),
    affiliate_id: Optional[str] = Query(None, description="Affiliate ID"),
    
    # 數據庫會話
    db: AsyncSession = Depends(get_db) if DB_AVAILABLE else None
):
    """Rector平台Postback接收端點"""
    global rector_record_counter
    start_time = time.time()
    
    try:
        rector_record_counter += 1
        
        # 解析時間格式
        parsed_datetime = None
        if conversion_datetime:
            try:
                for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        parsed_datetime = datetime.strptime(conversion_datetime, fmt)
                        break
                    except ValueError:
                        continue
            except Exception as e:
                logger.warning(f"無法解析轉化時間: {conversion_datetime}, error: {e}")
        
        # 安全轉換金額
        def safe_decimal_convert(value):
            if value is None or value == "":
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                logger.warning(f"無法轉換金額: {value}")
                return None
        
        usd_sale_amount_num = safe_decimal_convert(usd_sale_amount)
        usd_earning_num = safe_decimal_convert(usd_earning)
        
        # 構造原始數據
        raw_data = {
            "media_id": media_id,
            "sub_id": sub_id,
            "usd_sale_amount": usd_sale_amount,
            "usd_earning": usd_earning,
            "offer_name": offer_name,
            "conversion_id": conversion_id,
            "conversion_datetime": conversion_datetime,
            "click_id": click_id,
            "campaign_id": campaign_id,
            "affiliate_id": affiliate_id,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None
        }
        
        processing_time = (time.time() - start_time) * 1000
        
        # 存儲到數據庫
        if DB_AVAILABLE and db:
            try:
                conversion = RectorConversion(
                    conversion_id=conversion_id,
                    click_id=click_id,
                    media_id=media_id,
                    sub_id=sub_id,
                    usd_sale_amount=usd_sale_amount_num,
                    usd_earning=usd_earning_num,
                    offer_name=offer_name,
                    conversion_datetime=parsed_datetime,
                    raw_data=raw_data,
                    status="received",
                    processing_time_ms=processing_time,
                    request_method="GET",
                    request_ip=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent")
                )
                
                db.add(conversion)
                await db.commit()
                await db.refresh(conversion)
                
                record_id = conversion.id
                storage_type = "database"
                
            except Exception as e:
                logger.error(f"數據庫存儲失敗: {e}")
                record_id = rector_record_counter
                storage_type = "memory"
        else:
            record_id = rector_record_counter
            storage_type = "memory"
        
        # 內存存儲（備用或當數據庫不可用時）
        if storage_type == "memory":
            memory_record = {
                "id": rector_record_counter,
                "timestamp": time.time(),
                "method": "GET",
                "endpoint": "/aa7dfd32-953b-42ee-a77e-fba556a71d2f",
                "data": raw_data,
                "processing_time_ms": processing_time
            }
            rector_records.append(memory_record)
        
        # 記錄日誌
        logger.info(f"Rector Postback處理完成: conversion_id={conversion_id}, "
                   f"click_id={click_id}, media_id={media_id}, "
                   f"usd_earning={usd_earning}, storage={storage_type}, "
                   f"time={processing_time:.2f}ms")
        
        # 返回成功響應
        return JSONResponse({
            "status": "success",
            "method": "GET",
            "endpoint": "/aa7dfd32-953b-42ee-a77e-fba556a71d2f",
            "data": {
                "conversion_id": conversion_id,
                "click_id": click_id,
                "media_id": media_id,
                "sub_id": sub_id,
                "usd_sale_amount": usd_sale_amount_num,
                "usd_earning": usd_earning_num,
                "offer_name": offer_name,
                "conversion_datetime": conversion_datetime,
                "parsed_datetime": parsed_datetime.isoformat() if parsed_datetime else None
            },
            "record_id": record_id,
            "storage_type": storage_type,
            "processing_time_ms": processing_time,
            "message": "Rector conversion received successfully"
        })
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"Rector Postback處理異常: conversion_id={conversion_id}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        
        return JSONResponse({
            "status": "error",
            "method": "GET",
            "endpoint": "/aa7dfd32-953b-42ee-a77e-fba556a71d2f",
            "error": str(e),
            "processing_time_ms": processing_time,
            "message": "Rector conversion processing failed"
        }, status_code=500)


@router.get("/rector/health")
async def rector_health_check():
    """Rector服務健康檢查"""
    return JSONResponse({
        "status": "healthy",
        "service": "Rector Postback Service",
        "endpoint": "/aa7dfd32-953b-42ee-a77e-fba556a71d2f",
        "timestamp": time.time(),
        "database_available": DB_AVAILABLE,
        "memory_records": len(rector_records)
    })


@router.get("/rector/records")
async def get_rector_records(
    limit: int = Query(10, description="返回記錄數量"),
    offset: int = Query(0, description="偏移量"),
    db: AsyncSession = Depends(get_db) if DB_AVAILABLE else None
):
    """獲取Rector平台轉化記錄"""
    try:
        if DB_AVAILABLE and db:
            from sqlalchemy import select, desc
            
            query = select(RectorConversion).order_by(desc(RectorConversion.created_at))
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            result = await db.execute(query)
            conversions = result.scalars().all()
            
            records = [conv.to_dict() for conv in conversions]
            
            return JSONResponse({
                "status": "success",
                "total_records": len(records),
                "limit": limit,
                "offset": offset,
                "records": records,
                "source": "database",
                "message": f"返回{len(records)}條Rector轉化記錄"
            })
            
        else:
            total_records = len(rector_records)
            start_idx = offset
            end_idx = min(offset + limit, total_records)
            records = rector_records[start_idx:end_idx]
            
            return JSONResponse({
                "status": "success",
                "total_records": total_records,
                "limit": limit,
                "offset": offset,
                "records": records,
                "source": "memory",
                "message": f"返回{len(records)}條Rector轉化記錄"
            })
            
    except Exception as e:
        logger.error(f"查詢Rector記錄失敗: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "message": "查詢Rector記錄失敗"
        }, status_code=500)

#!/usr/bin/env python3
"""
多Partner Postback API路由
支持動態endpoint處理不同的Partner
"""

import time
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import json

from app.models.database import get_db
from app.services.partner_service import PartnerService
from app.models.partner import Partner

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(tags=["Multi-Partner Postback"])


async def get_partner_service(db: AsyncSession = Depends(get_db)) -> PartnerService:
    """獲取Partner服務實例"""
    return PartnerService(db)


@router.get("/{endpoint_path:path}")
async def dynamic_partner_endpoint(
    endpoint_path: str,
    request: Request,
    partner_service: PartnerService = Depends(get_partner_service),
    # 通用參數
    conversion_id: Optional[str] = Query(None, description="轉換ID"),
    offer_id: Optional[str] = Query(None, description="Offer ID"),
    offer_name: Optional[str] = Query(None, description="Offer名稱"),
    conversion_datetime: Optional[str] = Query(None, description="轉換時間"),
    
    # 金額參數
    usd_sale_amount: Optional[str] = Query(None, description="美元銷售金額"),
    usd_earning: Optional[str] = Query(None, description="美元佣金"),
    usd_payout: Optional[str] = Query(None, description="美元佣金(別名)"),
    
    # 自定義參數
    media_id: Optional[str] = Query(None, description="媒體ID"),
    sub_id: Optional[str] = Query(None, description="子ID"),
    click_id: Optional[str] = Query(None, description="點擊ID"),
    
    # 其他參數
    order_id: Optional[str] = Query(None, description="訂單ID"),
    status: Optional[str] = Query(None, description="狀態"),
):
    """
    動態Partner Postback端點
    
    支持所有Partner的通用處理邏輯
    根據endpoint_path自動識別Partner並處理對應的參數映射
    """
    start_time = time.time()
    
    try:
        logger.info(f"🚀 開始處理動態Partner Postback: endpoint_path={endpoint_path}")
        
        # 步驟1: 查找Partner
        logger.info(f"🔍 步驟1: 查找Partner配置")
        partner = await partner_service.get_partner_by_endpoint(f"/{endpoint_path}")
        
        if not partner:
            logger.error(f"❌ 未找到Partner配置: endpoint_path={endpoint_path}")
            raise HTTPException(
                status_code=404, 
                detail=f"Partner not found for endpoint: {endpoint_path}"
            )
        
        logger.info(f"✅ 找到Partner: {partner.partner_name} (code: {partner.partner_code})")
        
        # 步驟2: 收集原始數據
        logger.info(f"📊 步驟2: 收集原始數據")
        raw_data = dict(request.query_params)
        
        # 添加請求信息
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        logger.info(f"📋 原始參數: {raw_data}")
        
        # 步驟3: 參數映射處理
        logger.info(f"🔄 步驟3: 參數映射處理")
        if partner.parameter_mapping:
            mapped_data = {}
            for source_key, target_key in partner.parameter_mapping.items():
                if source_key in raw_data:
                    mapped_data[target_key] = raw_data[source_key]
                    logger.info(f"  映射: {source_key} -> {target_key} = {raw_data[source_key]}")
            
            # 合併映射後的數據
            raw_data.update(mapped_data)
        
        # 步驟4: 檢查重複轉化
        logger.info(f"🔍 步驟4: 檢查重複轉化")
        if conversion_id:
            is_duplicate = await partner_service.check_duplicate_conversion(
                partner.id, conversion_id
            )
            if is_duplicate:
                logger.warning(f"⚠️ 發現重複轉化: conversion_id={conversion_id}")
                return JSONResponse({
                    "status": "duplicate",
                    "partner": partner.partner_name,
                    "conversion_id": conversion_id,
                    "message": "Duplicate conversion detected"
                })
        
        # 步驟5: 創建轉化記錄
        logger.info(f"💾 步驟5: 創建轉化記錄")
        conversion = await partner_service.create_partner_conversion(
            partner_id=partner.id,
            raw_data=raw_data,
            request_headers=request_info,
            request_ip=request_info["client_ip"]
        )
        
        if not conversion:
            logger.error(f"❌ 創建轉化記錄失敗")
            raise HTTPException(
                status_code=500,
                detail="Failed to create conversion record"
            )
        
        # 步驟6: 標記為已處理
        logger.info(f"✅ 步驟6: 標記為已處理")
        await partner_service.mark_conversion_processed(conversion.id)
        
        # 計算處理時間
        processing_time = (time.time() - start_time) * 1000
        
        # 返回成功響應
        response_data = {
            "status": "success",
            "partner": {
                "code": partner.partner_code,
                "name": partner.partner_name,
                "endpoint": partner.endpoint_path
            },
            "conversion": {
                "id": conversion.id,
                "conversion_id": conversion.conversion_id,
                "offer_name": conversion.offer_name,
                "usd_sale_amount": float(conversion.usd_sale_amount) if conversion.usd_sale_amount else None,
                "usd_earning": float(conversion.usd_earning) if conversion.usd_earning else None,
                "media_id": conversion.media_id,
                "sub_id": conversion.sub_id,
                "click_id": conversion.click_id
            },
            "processing_time_ms": round(processing_time, 2),
            "message": "Conversion processed successfully"
        }
        
        logger.info(f"🎉 Partner Postback處理完成: "
                   f"partner={partner.partner_name}, "
                   f"conversion_id={conversion.conversion_id}, "
                   f"time={processing_time:.2f}ms")
        
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ Partner Postback處理異常: endpoint_path={endpoint_path}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        
        return JSONResponse({
            "status": "error",
            "endpoint_path": endpoint_path,
            "error": str(e),
            "processing_time_ms": round(processing_time, 2),
            "message": "Conversion processing failed"
        }, status_code=500)


@router.post("/{endpoint_path:path}")
async def dynamic_partner_endpoint_post(
    endpoint_path: str,
    request: Request,
    partner_service: PartnerService = Depends(get_partner_service),
):
    """
    動態Partner Postback端點 (POST方法)
    """
    start_time = time.time()
    
    try:
        logger.info(f"🚀 開始處理POST Partner Postback: endpoint_path={endpoint_path}")
        
        # 步驟1: 查找Partner
        logger.info(f"🔍 步驟1: 查找Partner配置")
        partner = await partner_service.get_partner_by_endpoint(f"/{endpoint_path}")
        
        if not partner:
            logger.error(f"❌ 未找到Partner配置: endpoint_path={endpoint_path}")
            raise HTTPException(
                status_code=404, 
                detail=f"Partner not found for endpoint: {endpoint_path}"
            )
        
        # 步驟2: 解析POST數據
        logger.info(f"📊 步驟2: 解析POST數據")
        try:
            body_data = await request.json()
        except:
            # 如果不是JSON，嘗試解析表單數據
            body_data = dict(await request.form())
        
        # 合併查詢參數和POST數據
        raw_data = dict(request.query_params)
        raw_data.update(body_data)
        
        # 添加請求信息
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        logger.info(f"📋 原始數據: {raw_data}")
        
        # 步驟3: 參數映射處理
        logger.info(f"🔄 步驟3: 參數映射處理")
        if partner.parameter_mapping:
            mapped_data = {}
            for source_key, target_key in partner.parameter_mapping.items():
                if source_key in raw_data:
                    mapped_data[target_key] = raw_data[source_key]
                    logger.info(f"  映射: {source_key} -> {target_key} = {raw_data[source_key]}")
            
            raw_data.update(mapped_data)
        
        # 步驟4: 檢查重複轉化
        logger.info(f"🔍 步驟4: 檢查重複轉化")
        conversion_id = raw_data.get('conversion_id')
        if conversion_id:
            is_duplicate = await partner_service.check_duplicate_conversion(
                partner.id, conversion_id
            )
            if is_duplicate:
                logger.warning(f"⚠️ 發現重複轉化: conversion_id={conversion_id}")
                return JSONResponse({
                    "status": "duplicate",
                    "partner": partner.partner_name,
                    "conversion_id": conversion_id,
                    "message": "Duplicate conversion detected"
                })
        
        # 步驟5: 創建轉化記錄
        logger.info(f"💾 步驟5: 創建轉化記錄")
        conversion = await partner_service.create_partner_conversion(
            partner_id=partner.id,
            raw_data=raw_data,
            request_headers=request_info,
            request_ip=request_info["client_ip"]
        )
        
        if not conversion:
            logger.error(f"❌ 創建轉化記錄失敗")
            raise HTTPException(
                status_code=500,
                detail="Failed to create conversion record"
            )
        
        # 步驟6: 標記為已處理
        logger.info(f"✅ 步驟6: 標記為已處理")
        await partner_service.mark_conversion_processed(conversion.id)
        
        # 計算處理時間
        processing_time = (time.time() - start_time) * 1000
        
        # 返回成功響應
        response_data = {
            "status": "success",
            "partner": {
                "code": partner.partner_code,
                "name": partner.partner_name,
                "endpoint": partner.endpoint_path
            },
            "conversion": {
                "id": conversion.id,
                "conversion_id": conversion.conversion_id,
                "offer_name": conversion.offer_name,
                "usd_sale_amount": float(conversion.usd_sale_amount) if conversion.usd_sale_amount else None,
                "usd_earning": float(conversion.usd_earning) if conversion.usd_earning else None,
                "media_id": conversion.media_id,
                "sub_id": conversion.sub_id,
                "click_id": conversion.click_id
            },
            "processing_time_ms": round(processing_time, 2),
            "message": "Conversion processed successfully"
        }
        
        logger.info(f"🎉 POST Partner Postback處理完成: "
                   f"partner={partner.partner_name}, "
                   f"conversion_id={conversion.conversion_id}, "
                   f"time={processing_time:.2f}ms")
        
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        logger.error(f"❌ POST Partner Postback處理異常: endpoint_path={endpoint_path}, "
                    f"error={str(e)}, time={processing_time:.2f}ms")
        
        return JSONResponse({
            "status": "error",
            "endpoint_path": endpoint_path,
            "error": str(e),
            "processing_time_ms": round(processing_time, 2),
            "message": "Conversion processing failed"
        }, status_code=500)


@router.get("/{endpoint_path}/stats")
async def get_partner_stats(
    endpoint_path: str,
    hours: int = Query(24, description="統計時間範圍(小時)"),
    partner_service: PartnerService = Depends(get_partner_service),
):
    """獲取Partner統計信息"""
    try:
        partner = await partner_service.get_partner_by_endpoint(f"/{endpoint_path}")
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        stats = await partner_service.get_partner_stats(partner.id, hours)
        
        return {
            "partner": partner.partner_name,
            "endpoint": endpoint_path,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"獲取Partner統計失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{endpoint_path}/conversions")
async def get_partner_conversions(
    endpoint_path: str,
    limit: int = Query(10, description="返回記錄數量"),
    partner_service: PartnerService = Depends(get_partner_service),
):
    """獲取Partner轉化記錄"""
    try:
        partner = await partner_service.get_partner_by_endpoint(f"/{endpoint_path}")
        if not partner:
            raise HTTPException(status_code=404, detail="Partner not found")
        
        conversions = await partner_service.get_recent_conversions(partner.id, limit)
        
        return {
            "partner": partner.partner_name,
            "endpoint": endpoint_path,
            "conversions": [conv.to_dict() for conv in conversions]
        }
        
    except Exception as e:
        logger.error(f"獲取Partner轉化記錄失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
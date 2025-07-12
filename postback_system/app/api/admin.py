#!/usr/bin/env python3
"""
管理端點 - 用於系統管理和數據庫初始化
"""

import logging
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.database import get_db
from app.models.partner import Partner

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])

@router.post("/init-database")
async def init_database(db: AsyncSession = Depends(get_db)):
    """
    初始化數據庫表結構和基礎數據
    """
    try:
        logger.info("🚀 開始初始化數據庫...")
        
        # 創建租戶表
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS tenants (
                id SERIAL PRIMARY KEY,
                tenant_code VARCHAR(50) UNIQUE NOT NULL,
                tenant_name VARCHAR(100) NOT NULL,
                ts_token VARCHAR(255),
                tlm_token VARCHAR(255),
                ts_param VARCHAR(100),
                description TEXT,
                contact_email VARCHAR(255),
                contact_phone VARCHAR(50),
                max_daily_requests INTEGER DEFAULT 100000,
                enable_duplicate_check BOOLEAN DEFAULT TRUE,
                data_retention_days INTEGER DEFAULT 7,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # 創建夥伴表
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS partners (
                id SERIAL PRIMARY KEY,
                partner_code VARCHAR(50) UNIQUE NOT NULL,
                partner_name VARCHAR(100) NOT NULL,
                endpoint_path VARCHAR(100) UNIQUE NOT NULL,
                endpoint_url VARCHAR(500),
                cloud_run_service_name VARCHAR(100),
                cloud_run_region VARCHAR(50) DEFAULT 'asia-southeast1',
                cloud_run_project_id VARCHAR(100),
                database_name VARCHAR(100),
                database_url VARCHAR(500),
                parameter_mapping JSONB,
                is_active BOOLEAN DEFAULT TRUE,
                enable_logging BOOLEAN DEFAULT TRUE,
                max_daily_requests INTEGER DEFAULT 100000,
                data_retention_days INTEGER DEFAULT 30,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # 創建夥伴轉化表
        await db.execute(text("""
            CREATE TABLE IF NOT EXISTS partner_conversions (
                id SERIAL PRIMARY KEY,
                partner_id INTEGER REFERENCES partners(id),
                conversion_id VARCHAR(50) NOT NULL,
                offer_id VARCHAR(50),
                offer_name TEXT,
                conversion_datetime TIMESTAMP WITH TIME ZONE,
                usd_sale_amount DECIMAL(15,2),
                usd_earning DECIMAL(15,2),
                media_id VARCHAR(255),
                sub_id VARCHAR(255),
                click_id VARCHAR(255),
                is_processed BOOLEAN DEFAULT FALSE,
                is_duplicate BOOLEAN DEFAULT FALSE,
                processing_error TEXT,
                raw_data JSONB,
                request_headers JSONB,
                request_ip VARCHAR(45),
                received_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        # 插入默認租戶
        await db.execute(text("""
            INSERT INTO tenants (tenant_code, tenant_name, description, is_active)
            VALUES ('default', 'Default Tenant', 'Default tenant for ByteC Postback System', TRUE)
            ON CONFLICT (tenant_code) DO NOTHING;
        """))
        
        # 插入Involve夥伴
        await db.execute(text("""
            INSERT INTO partners (
                partner_code, partner_name, endpoint_path, endpoint_url,
                cloud_run_service_name, cloud_run_region, cloud_run_project_id,
                database_name, parameter_mapping, is_active
            ) VALUES (
                'involve_asia', 'InvolveAsia', '/involve/event',
                'https://bytec-public-postback-crwdeesavq-as.a.run.app/involve/event',
                'bytec-public-postback', 'asia-southeast1', 'solar-idea-463423-h8',
                'involve_asia_db', 
                '{"sub_id": "aff_sub", "media_id": "aff_sub2", "click_id": "aff_sub3", "usd_sale_amount": "usd_sale_amount", "usd_payout": "usd_payout", "offer_name": "offer_name", "conversion_id": "conversion_id", "conversion_datetime": "datetime_conversion"}'::jsonb,
                TRUE
            )
            ON CONFLICT (partner_code) DO UPDATE SET
                endpoint_url = EXCLUDED.endpoint_url,
                cloud_run_project_id = EXCLUDED.cloud_run_project_id,
                parameter_mapping = EXCLUDED.parameter_mapping,
                updated_at = CURRENT_TIMESTAMP;
        """))
        
        # 插入Digenesia夥伴
        await db.execute(text("""
            INSERT INTO partners (
                partner_code, partner_name, endpoint_path, endpoint_url,
                cloud_run_service_name, cloud_run_region, cloud_run_project_id,
                database_name, parameter_mapping, is_active
            ) VALUES (
                'digenesia', 'Digenesia', '/digenesia/event',
                'https://bytec-public-postback-crwdeesavq-as.a.run.app/partner/digenesia/event',
                'bytec-public-postback', 'asia-southeast1', 'solar-idea-463423-h8',
                'digenesia_db',
                '{"aff_sub": "aff_sub", "aff_sub2": "aff_sub2", "aff_sub3": "aff_sub3", "usd_sale_amount": "usd_sale_amount", "usd_payout": "usd_payout", "offer_name": "offer_name", "conversion_id": "conversion_id", "conversion_datetime": "conversion_datetime"}'::jsonb,
                TRUE
            )
            ON CONFLICT (partner_code) DO UPDATE SET
                endpoint_url = EXCLUDED.endpoint_url,
                cloud_run_project_id = EXCLUDED.cloud_run_project_id,
                parameter_mapping = EXCLUDED.parameter_mapping,
                updated_at = CURRENT_TIMESTAMP;
        """))
        
        # 創建索引
        await db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_partners_endpoint_path ON partners(endpoint_path);
            CREATE INDEX IF NOT EXISTS idx_partners_is_active ON partners(is_active);
            CREATE INDEX IF NOT EXISTS idx_partner_conversions_partner_id ON partner_conversions(partner_id);
            CREATE INDEX IF NOT EXISTS idx_partner_conversions_conversion_id ON partner_conversions(conversion_id);
            CREATE INDEX IF NOT EXISTS idx_partner_conversions_received_at ON partner_conversions(received_at);
        """))
        
        await db.commit()
        
        # 驗證數據
        result = await db.execute(text("SELECT COUNT(*) FROM partners WHERE is_active = TRUE"))
        active_partners = result.scalar()
        
        result = await db.execute(text("SELECT partner_code, partner_name, endpoint_path FROM partners WHERE is_active = TRUE"))
        partners = result.fetchall()
        
        partner_list = []
        for partner in partners:
            partner_list.append({
                "code": partner[0],
                "name": partner[1],
                "endpoint": partner[2]
            })
        
        logger.info("✅ 數據庫初始化完成")
        
        return JSONResponse({
            "status": "success",
            "message": "數據庫初始化完成",
            "active_partners": active_partners,
            "partners": partner_list
        })
        
    except Exception as e:
        logger.error(f"❌ 數據庫初始化失敗: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"數據庫初始化失敗: {str(e)}")

@router.get("/partners")
async def list_partners(db: AsyncSession = Depends(get_db)):
    """
    列出所有夥伴
    """
    try:
        result = await db.execute(text("""
            SELECT partner_code, partner_name, endpoint_path, is_active 
            FROM partners 
            ORDER BY partner_code
        """))
        partners = result.fetchall()
        
        partner_list = []
        for partner in partners:
            partner_list.append({
                "code": partner[0],
                "name": partner[1],
                "endpoint": partner[2],
                "is_active": partner[3]
            })
        
        return JSONResponse({
            "status": "success",
            "partners": partner_list,
            "total": len(partner_list)
        })
        
    except Exception as e:
        logger.error(f"❌ 獲取夥伴列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取夥伴列表失敗: {str(e)}")

@router.get("/database-status")
async def database_status(db: AsyncSession = Depends(get_db)):
    """
    檢查數據庫狀態
    """
    try:
        await db.execute(text("SELECT 1"))
        
        # 檢查表是否存在
        result = await db.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN ('partners', 'partner_conversions', 'tenants')
        """))
        tables = [row[0] for row in result.fetchall()]
        
        return JSONResponse({
            "status": "healthy",
            "database_connection": "ok",
            "tables": tables,
            "tables_count": len(tables)
        })
        
    except Exception as e:
        logger.error(f"❌ 數據庫狀態檢查失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"數據庫連接失敗: {str(e)}") 
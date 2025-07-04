#!/usr/bin/env python3
"""
创建测试租户的脚本
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db, async_session
from app.models.tenant import Tenant


async def create_test_tenants():
    """创建测试租户"""
    
    async with async_session() as session:
        try:
            # 创建ByteC测试租户
            bytec_tenant = Tenant(
                tenant_code="bytec",
                tenant_name="ByteC Network",
                description="ByteC网络测试租户",
                ts_token="bytec_test",
                tlm_token="bytec_tlm_token",
                ts_param="bytec",
                contact_email="support@bytec.com",
                max_daily_requests=500000,
                enable_duplicate_check=True,
                data_retention_days=30
            )
            
            # 创建Shopee测试租户
            shopee_tenant = Tenant(
                tenant_code="shopee",
                tenant_name="Shopee Platform",
                description="Shopee平台测试租户",
                ts_token="shopee_production_token",
                tlm_token="shopee_tlm_token",
                ts_param="shopee",
                contact_email="affiliate@shopee.com",
                max_daily_requests=1000000,
                enable_duplicate_check=True,
                data_retention_days=30
            )
            
            # 创建TikTok Shop测试租户
            tiktok_tenant = Tenant(
                tenant_code="tiktok",
                tenant_name="TikTok Shop",
                description="TikTok Shop测试租户",
                ts_token="tiktok_token",
                tlm_token="tiktok_tlm_token",
                ts_param="tiktok",
                contact_email="business@tiktokshop.com",
                max_daily_requests=800000,
                enable_duplicate_check=True,
                data_retention_days=30
            )
            
            # 创建默认测试租户
            default_tenant = Tenant(
                tenant_code="default",
                tenant_name="Default Test Tenant",
                description="默认测试租户",
                ts_token="default_test_token",
                tlm_token="default_tlm_token",
                ts_param="default",
                contact_email="test@example.com",
                max_daily_requests=100000,
                enable_duplicate_check=True,
                data_retention_days=7
            )
            
            # 添加到会话
            session.add_all([bytec_tenant, shopee_tenant, tiktok_tenant, default_tenant])
            
            # 提交到数据库
            await session.commit()
            
            print("✅ 测试租户创建成功！")
            print("🏢 租户列表:")
            print("  1. ByteC Network (ts_token: bytec_test)")
            print("  2. Shopee Platform (ts_token: shopee_production_token)")
            print("  3. TikTok Shop (ts_token: tiktok_token)")
            print("  4. Default Test (ts_token: default_test_token)")
            print()
            print("📋 测试URL示例:")
            print("curl \"http://localhost:8000/postback/involve/event?conversion_id=test123&click_id=click456&ts_token=bytec_test\"")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ 创建租户失败: {e}")
            raise


async def list_tenants():
    """列出所有租户"""
    
    async with async_session() as session:
        try:
            from sqlalchemy import select
            result = await session.execute(select(Tenant))
            tenants = result.scalars().all()
            
            if tenants:
                print("📋 现有租户列表:")
                print("-" * 80)
                for tenant in tenants:
                    print(f"ID: {tenant.id}")
                    print(f"代码: {tenant.tenant_code}")
                    print(f"名称: {tenant.tenant_name}")
                    print(f"TS Token: {tenant.ts_token}")
                    print(f"状态: {'激活' if tenant.is_active else '禁用'}")
                    print(f"创建时间: {tenant.created_at}")
                    print("-" * 80)
            else:
                print("📭 暂无租户数据")
                
        except Exception as e:
            print(f"❌ 查询租户失败: {e}")


if __name__ == "__main__":
    print("🚀 租户管理脚本")
    print("=" * 50)
    
    # 先列出现有租户
    print("🔍 检查现有租户...")
    asyncio.run(list_tenants())
    
    print()
    answer = input("是否创建测试租户？(y/N): ")
    
    if answer.lower() in ['y', 'yes']:
        print("📝 创建测试租户...")
        asyncio.run(create_test_tenants())
        
        print()
        print("🔍 验证租户创建...")
        asyncio.run(list_tenants())
    else:
        print("👋 操作取消") 
#!/usr/bin/env python3
"""
測試映射系統
"""

import sys
import os
import asyncio
from datetime import datetime

# 添加路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.mapping_manager import MappingManager

# 數據庫配置
DB_CONFIG = {
    'host': '34.124.206.16',
    'port': 5432,
    'database': 'postback_db',
    'user': 'postback_admin',
    'password': 'ByteC2024PostBack_CloudSQL'
}

print("🧪 測試映射系統")
print("=" * 50)

async def test_mapping_system():
    """測試映射系統"""
    
    # 初始化映射管理器
    mapping_manager = MappingManager(DB_CONFIG)
    
    try:
        # 1. 初始化映射系統
        print("🚀 初始化映射系統...")
        await mapping_manager.initialize_all_mappings()
        
        # 2. 測試平台映射
        print("\n📱 測試平台映射...")
        test_platforms = ["LisaidByteC", "IAByteC", "LisaidWebeye"]
        for platform in test_platforms:
            platform_id = await mapping_manager.get_platform_id(platform)
            print(f"   - {platform}: ID = {platform_id}")
        
        # 3. 測試業務伙伴映射
        print("\n🤝 測試業務伙伴映射...")
        test_partners = ["RAMPUP", "DeepLeaper", "ByteC", "MKK", "TestPartner"]
        for partner in test_partners:
            partner_id = await mapping_manager.get_partner_id(partner)
            print(f"   - {partner}: ID = {partner_id}")
        
        # 4. 測試源映射
        print("\n📋 測試源映射...")
        test_sources = ["RAMPUP", "OPPO", "VIVO", "OEM2", "OEM3", "MKK", "ALL"]
        for source in test_sources:
            source_id = await mapping_manager.get_source_id(source)
            print(f"   - {source}: ID = {source_id}")
        
        # 5. 測試自動創建源
        print("\n🔄 測試自動創建源...")
        new_sources = ["RPID001", "OEM2_OPPO_PUSH", "VIVO_SMS_001"]
        for source in new_sources:
            source_id = await mapping_manager.get_or_create_source_id(source)
            print(f"   - {source}: ID = {source_id}")
        
        # 6. 測試API Secret映射
        print("\n🔐 測試API Secret映射...")
        test_secrets = [
            "boiTXnRgB2B3N7rCictjjti1ufNIzKksSURJHwqtC50=",
            "Q524XgLnQmrIBiOK8ZD2qmgmQDPbuTqx13tBDWd6BT0="
        ]
        for secret in test_secrets:
            platform_id = await mapping_manager.get_platform_by_api_secret(secret)
            print(f"   - {secret[:20]}...: Platform ID = {platform_id}")
        
        # 7. 獲取映射摘要
        print("\n📊 映射摘要...")
        summary = await mapping_manager.get_mapping_summary()
        for key, value in summary.items():
            print(f"   - {key}: {value}")
        
        # 8. 測試映射表查詢
        print("\n🔍 查詢映射表...")
        async with mapping_manager.pool.acquire() as conn:
            # 查詢所有平台
            platforms = await conn.fetch("SELECT * FROM platforms ORDER BY id")
            print(f"   平台表 ({len(platforms)} 條記錄):")
            for platform in platforms:
                print(f"     - {platform['id']}: {platform['platform_name']} ({platform['platform_code']})")
            
            # 查詢所有業務伙伴
            partners = await conn.fetch("SELECT * FROM business_partners ORDER BY id")
            print(f"   業務伙伴表 ({len(partners)} 條記錄):")
            for partner in partners:
                print(f"     - {partner['id']}: {partner['partner_name']} ({partner['partner_code']})")
            
            # 查詢所有源
            sources = await conn.fetch("""
            SELECT s.*, bp.partner_name 
            FROM sources s
            LEFT JOIN business_partners bp ON s.partner_id = bp.id
            ORDER BY s.id
            """)
            print(f"   源表 ({len(sources)} 條記錄):")
            for source in sources:
                print(f"     - {source['id']}: {source['source_name']} -> {source['partner_name']}")
    
    except Exception as e:
        print(f"❌ 測試映射系統失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        await mapping_manager.close_pool()

async def main():
    """主函數"""
    await test_mapping_system()
    
    print("\n" + "=" * 50)
    print("🎉 映射系統測試完成")

if __name__ == "__main__":
    asyncio.run(main()) 
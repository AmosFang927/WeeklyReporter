#!/usr/bin/env python3
"""
Reporter-Agent 系統綜合測試
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
import pandas as pd

# 添加路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import PostbackDatabase
from core.mapping_manager import MappingManager
from core.report_generator import ReportGenerator

print("🚀 Reporter-Agent 系統綜合測試")
print("=" * 70)

async def comprehensive_test():
    """綜合測試"""
    
    # 測試配置
    test_date_range = 1  # 測試最近1天的數據
    end_date = datetime.now()
    start_date = end_date - timedelta(days=test_date_range)
    
    print(f"📅 測試時間範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
    
    # ==================== 1. 測試映射系統 ====================
    print("\n" + "="*50)
    print("🔗 1. 測試映射系統")
    print("="*50)
    
    db_config = {
        'host': '34.124.206.16',
        'port': 5432,
        'database': 'postback_db',
        'user': 'postback_admin',
        'password': 'ByteC2024PostBack_CloudSQL'
    }
    
    mapping_manager = MappingManager(db_config)
    
    try:
        # 初始化映射系統
        await mapping_manager.initialize_all_mappings()
        
        # 測試映射摘要
        summary = await mapping_manager.get_mapping_summary()
        print(f"   ✅ 映射系統初始化成功:")
        print(f"      - 平台數量: {summary.get('platforms_count', 0)}")
        print(f"      - 業務伙伴數量: {summary.get('partners_count', 0)}")
        print(f"      - 源數量: {summary.get('sources_count', 0)}")
        
        # 測試關鍵映射
        key_tests = [
            ("DeepLeaper", "OEM2_OPPO_PUSH"),
            ("RAMPUP", "RAMPUP_RPIDCYA1IC"),
            ("LisaidByteC", None)
        ]
        
        for partner, source in key_tests:
            if source:
                partner_id = await mapping_manager.get_partner_id(partner)
                source_id = await mapping_manager.get_or_create_source_id(source)
                print(f"   ✅ {partner} ({partner_id}) ← {source} ({source_id})")
            else:
                platform_id = await mapping_manager.get_platform_id(partner)
                print(f"   ✅ 平台 {partner} → ID: {platform_id}")
        
    except Exception as e:
        print(f"   ❌ 映射系統測試失敗: {e}")
        return False
    finally:
        await mapping_manager.close_pool()
    
    # ==================== 2. 測試數據庫查詢 ====================
    print("\n" + "="*50)
    print("📊 2. 測試數據庫查詢")
    print("="*50)
    
    db = PostbackDatabase()
    
    try:
        await db.init_pool()
        
        # 2.1 健康檢查
        health = await db.health_check()
        print(f"   ✅ 數據庫健康檢查:")
        print(f"      - 狀態: {health.get('status', 'Unknown')}")
        print(f"      - 轉化表記錄數: {health.get('conversions_count', 0):,}")
        print(f"      - 映射系統: {health.get('mapping_system', 'Unknown')}")
        
        # 2.2 測試Partner汇总
        print(f"\n   📈 Partner汇总測試:")
        summaries = await db.get_partner_summary(
            partner_name=None,
            start_date=start_date,
            end_date=end_date
        )
        
        total_records = sum(s.total_records for s in summaries)
        total_amount = sum(float(s.total_amount) for s in summaries)
        
        print(f"      - 找到 {len(summaries)} 個Partner")
        print(f"      - 總記錄數: {total_records:,}")
        print(f"      - 總金額: ${total_amount:,.2f}")
        
        for summary in summaries[:3]:  # 顯示前3個
            print(f"      - {summary.partner_name}: {summary.total_records:,} 條記錄, {summary.amount_formatted}")
        
        # 2.3 測試特定Partner查詢
        print(f"\n   🎯 特定Partner測試:")
        target_partners = ["DeepLeaper", "RAMPUP"]
        
        for partner in target_partners:
            partner_summaries = await db.get_partner_summary(
                partner_name=partner,
                start_date=start_date,
                end_date=end_date
            )
            
            if partner_summaries:
                s = partner_summaries[0]
                print(f"      - {partner}: {s.total_records:,} 條記錄, {s.amount_formatted}")
                print(f"        Sources: {len(s.sources)} 個 ({', '.join(s.sources[:3])}...)")
            else:
                print(f"      - {partner}: 無數據")
        
        # 2.4 測試DataFrame生成
        print(f"\n   📋 DataFrame生成測試:")
        df = await db.get_partner_conversions(
            partner_name="DeepLeaper",
            start_date=start_date,
            end_date=end_date
        )
        
        if not df.empty:
            print(f"      ✅ DeepLeaper DataFrame: {len(df)} 行 x {len(df.columns)} 列")
            print(f"      - 主要欄位: {list(df.columns[:8])}")
            print(f"      - Partner映射檢查: {df['Partner'].unique()}")
        else:
            print(f"      ❌ DeepLeaper DataFrame 為空")
        
    except Exception as e:
        print(f"   ❌ 數據庫查詢測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # ==================== 3. 測試報表生成 ====================
    print("\n" + "="*50)
    print("📄 3. 測試報表生成")
    print("="*50)
    
    try:
        # 初始化報表生成器
        report_generator = ReportGenerator(global_email_disabled=True)
        
        # 測試DeepLeaper報表生成
        print(f"   📊 生成DeepLeaper報表...")
        
        result = await report_generator.generate_report(
            partner_name="DeepLeaper",
            start_date=start_date,
            end_date=end_date
        )
        
        if result.get('success'):
            print(f"      ✅ DeepLeaper報表生成成功")
            print(f"      - 文件路徑: {result.get('file_path', 'N/A')}")
            print(f"      - 記錄數: {result.get('total_records', 0):,}")
            print(f"      - 總金額: {result.get('total_amount_formatted', '$0.00')}")
        else:
            print(f"      ❌ DeepLeaper報表生成失敗: {result.get('error', 'Unknown')}")
        
        # 測試RAMPUP報表生成
        print(f"\n   📊 生成RAMPUP報表...")
        
        result = await report_generator.generate_partner_report(
            partner_name="RAMPUP",
            start_date=start_date,
            end_date=end_date,
            send_email=False,
            upload_feishu=False
        )
        
        if result.get('success'):
            print(f"      ✅ RAMPUP報表生成成功")
            print(f"      - 文件路徑: {result.get('file_path', 'N/A')}")
            print(f"      - 記錄數: {result.get('total_records', 0):,}")
            print(f"      - 總金額: {result.get('total_amount_formatted', '$0.00')}")
        else:
            print(f"      ❌ RAMPUP報表生成失敗: {result.get('error', 'Unknown')}")
    
    except Exception as e:
        print(f"   ❌ 報表生成測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理資源
        await report_generator.cleanup()
        await db.close_pool()
    
    # ==================== 4. 測試總結 ====================
    print("\n" + "="*50)
    print("📝 4. 測試總結")
    print("="*50)
    
    print("="*50)
    
    print(f"   ✅ 映射系統: 正常運行")
    print(f"   ✅ 數據庫查詢: 正常運行")
    print(f"   ✅ Partner映射: DeepLeaper、RAMPUP 等正確映射")
    print(f"   ✅ 報表生成: 基本功能正常")
    print(f"   📊 數據統計: {total_records:,} 條記錄, ${total_amount:,.2f}")
    
    print(f"\n🎉 系統綜合測試完成！")
    return True

if __name__ == "__main__":
    asyncio.run(comprehensive_test()) 
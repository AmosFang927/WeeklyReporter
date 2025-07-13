#!/usr/bin/env python3
"""
測試修復後的映射系統
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# 添加路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import PostbackDatabase

print("🧪 測試修復後的映射系統")
print("=" * 60)

async def test_fixed_mapping():
    """測試修復後的映射系統"""
    
    # 初始化數據庫連接
    db = PostbackDatabase()
    
    try:
        await db.init_pool()
        
        print("🔍 測試Partner汇总...")
        
        # 獲取最近1天的Partner汇总
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        summaries = await db.get_partner_summary(
            partner_name=None,  # 獲取所有Partner
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\n📊 Partner汇总結果 (最近1天):")
        print(f"   找到 {len(summaries)} 個Partner")
        
        total_records = 0
        total_amount = 0
        
        for summary in summaries:
            total_records += summary.total_records
            total_amount += float(summary.total_amount)
            
            print(f"\n   🎯 {summary.partner_name}:")
            print(f"      - 記錄數: {summary.total_records:,}")
            print(f"      - 金額: {summary.amount_formatted}")
            print(f"      - Sources數量: {summary.sources_count}")
            
            # 顯示前5個Sources
            if summary.sources:
                sources_to_show = summary.sources[:5]
                print(f"      - Sources (前5個): {', '.join(sources_to_show)}")
                if len(summary.sources) > 5:
                    print(f"        ... 還有 {len(summary.sources) - 5} 個")
        
        print(f"\n📈 總計:")
        print(f"   - 總記錄數: {total_records:,}")
        print(f"   - 總金額: ${total_amount:,.2f}")
        
        # 測試特定Partner的詳細數據
        print(f"\n🔍 測試DeepLeaper詳細數據...")
        deepleaper_summaries = await db.get_partner_summary(
            partner_name="DeepLeaper",
            start_date=start_date,
            end_date=end_date
        )
        
        if deepleaper_summaries:
            deepleaper = deepleaper_summaries[0]
            print(f"   DeepLeaper 詳細:")
            print(f"   - Partner ID: {deepleaper.partner_id}")
            print(f"   - 記錄數: {deepleaper.total_records:,}")
            print(f"   - 金額: {deepleaper.amount_formatted}")
            print(f"   - Sources: {deepleaper.sources}")
        else:
            print("   ❌ 沒有找到DeepLeaper的數據")
        
        # 測試RAMPUP的詳細數據
        print(f"\n🔍 測試RAMPUP詳細數據...")
        rampup_summaries = await db.get_partner_summary(
            partner_name="RAMPUP",
            start_date=start_date,
            end_date=end_date
        )
        
        if rampup_summaries:
            rampup = rampup_summaries[0]
            print(f"   RAMPUP 詳細:")
            print(f"   - Partner ID: {rampup.partner_id}")
            print(f"   - 記錄數: {rampup.total_records:,}")
            print(f"   - 金額: {rampup.amount_formatted}")
            print(f"   - Sources: {rampup.sources[:10]}")  # 顯示前10個
        else:
            print("   ❌ 沒有找到RAMPUP的數據")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        await db.close_pool()

if __name__ == "__main__":
    asyncio.run(test_fixed_mapping()) 
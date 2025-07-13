#!/usr/bin/env python3
"""
檢查aff_sub字段的映射情況
"""

import asyncio
import asyncpg
from datetime import datetime, timedelta

async def check_aff_sub_mapping():
    """檢查aff_sub字段的映射情況"""
    
    conn = await asyncpg.connect(
        host='34.124.206.16',
        port=5432,
        database='postback_db',
        user='postback_admin',
        password='ByteC2024PostBack_CloudSQL'
    )
    
    print("🔍 檢查aff_sub字段的映射情況")
    print("=" * 60)
    
    # 獲取最近7天的unique aff_sub值
    result = await conn.fetch("""
    SELECT 
        c.aff_sub,
        COUNT(*) as count,
        s.source_name as mapped_source,
        bp.partner_name as mapped_partner
    FROM conversions c
    LEFT JOIN sources s ON s.source_name = c.aff_sub
    LEFT JOIN business_partners bp ON s.partner_id = bp.id
    WHERE c.created_at >= NOW() - INTERVAL '7 days' 
      AND c.aff_sub IS NOT NULL
    GROUP BY c.aff_sub, s.source_name, bp.partner_name
    ORDER BY count DESC, c.aff_sub
    """)
    
    print(f"📋 最近7天的aff_sub值 (共 {len(result)} 種):")
    
    mapped_count = 0
    unmapped_count = 0
    unmapped_records = 0
    
    for row in result:
        aff_sub = row['aff_sub']
        count = row['count']
        mapped_partner = row['mapped_partner']
        
        if mapped_partner:
            status = "✅"
            mapped_count += 1
            print(f"  {status} {aff_sub} (數量: {count}) → {mapped_partner}")
        else:
            status = "❌"
            unmapped_count += 1
            unmapped_records += count
            print(f"  {status} {aff_sub} (數量: {count}) → 未映射")
    
    print("\n📊 映射統計:")
    print(f"  - 已映射的aff_sub類型: {mapped_count}")
    print(f"  - 未映射的aff_sub類型: {unmapped_count}")
    print(f"  - 未映射的記錄數量: {unmapped_records}")
    
    # 檢查未映射的aff_sub是否應該被映射
    if unmapped_count > 0:
        print("\n🔄 檢查未映射的aff_sub是否符合config.py模式:")
        
        # 導入config模式檢查
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
        from config import match_source_to_partner
        
        for row in result:
            if not row['mapped_partner']:
                aff_sub = row['aff_sub']
                count = row['count']
                expected_partner = match_source_to_partner(aff_sub)
                
                if expected_partner != aff_sub:  # 如果找到了匹配的partner（不是返回原始值）
                    print(f"  🔧 {aff_sub} (數量: {count}) 應該映射到 → {expected_partner}")
                else:
                    print(f"  ❓ {aff_sub} (數量: {count}) 沒有匹配的Partner模式")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_aff_sub_mapping()) 
#!/usr/bin/env python3
"""
簡化的Reporter-Agent測試腳本
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# 添加路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🧪 Reporter-Agent 簡化測試開始")
print("=" * 50)

# 1. 測試模塊導入
print("📦 測試模塊導入...")
try:
    from core.database import PostbackDatabase
    print("✅ 數據庫模塊導入成功")
except ImportError as e:
    print(f"❌ 數據庫模塊導入失敗: {e}")

try:
    from modules.feishu_uploader import FeishuUploader
    print("✅ 飛書上傳模塊導入成功")
except ImportError as e:
    print(f"❌ 飛書上傳模塊導入失敗: {e}")

try:
    from modules.email_sender import EmailSender
    print("✅ 郵件發送模塊導入成功")
except ImportError as e:
    print(f"❌ 郵件發送模塊導入失敗: {e}")

# 2. 測試數據庫連接
print("\n🔌 測試數據庫連接...")
async def test_database():
    try:
        db = PostbackDatabase()
        partners = await db.get_available_partners()
        print(f"✅ 數據庫連接成功，找到 {len(partners)} 個Partners: {partners}")
        return True
    except Exception as e:
        print(f"❌ 數據庫連接失敗: {e}")
        return False

# 3. 測試數據查詢
print("\n🔍 測試數據查詢...")
async def test_data_query():
    try:
        db = PostbackDatabase()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # 測試獲取轉化數據
        df = await db.get_conversion_dataframe("ALL", start_date, end_date)
        print(f"✅ 數據查詢成功，找到 {len(df)} 條轉化記錄")
        
        if len(df) > 0:
            print(f"📊 數據預覽:")
            print(f"   - 總銷售額: ${df['Sale Amount (USD)'].sum():.2f}")
            print(f"   - 日期範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
            print(f"   - 主要Partners: {df['Partner'].unique()}")
        
        return True
    except Exception as e:
        print(f"❌ 數據查詢失敗: {e}")
        return False

# 4. 執行測試
async def main():
    print("\n🚀 開始異步測試...")
    
    # 測試數據庫連接
    db_success = await test_database()
    
    if db_success:
        # 測試數據查詢
        await test_data_query()
    
    print("\n" + "=" * 50)
    print("🎉 簡化測試完成")

if __name__ == "__main__":
    asyncio.run(main()) 
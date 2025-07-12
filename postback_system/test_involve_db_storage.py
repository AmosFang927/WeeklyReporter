#!/usr/bin/env python3
"""
测试involve endpoint的数据库存储功能
"""

import asyncio
import asyncpg
import requests
import json
from datetime import datetime
import time

# 数据库连接配置
DATABASE_URL = "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@34.124.206.16:5432/postback_db"

# API endpoint
API_URL = "https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event"

async def check_database_before_test():
    """检查测试前的数据库状态"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 获取今天的数据数量
        today = datetime.now().date()
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM conversions 
            WHERE DATE(created_at) = $1
        """, today)
        
        print(f"📊 测试前数据库状态:")
        print(f"   今天的转化数据数量: {count}")
        
        await conn.close()
        return count
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {str(e)}")
        return None

async def check_database_after_test(initial_count, test_conversion_ids):
    """检查测试后的数据库状态"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # 获取今天的数据数量
        today = datetime.now().date()
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM conversions 
            WHERE DATE(created_at) = $1
        """, today)
        
        print(f"📊 测试后数据库状态:")
        print(f"   今天的转化数据数量: {count}")
        print(f"   新增数据数量: {count - initial_count}")
        
        # 检查测试数据是否存在
        for conversion_id in test_conversion_ids:
            result = await conn.fetchrow("""
                SELECT conversion_id, offer_name, usd_sale_amount, usd_payout, created_at
                FROM conversions 
                WHERE conversion_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """, conversion_id)
            
            if result:
                print(f"✅ 找到测试数据: {conversion_id}")
                print(f"   - offer_name: {result['offer_name']}")
                print(f"   - usd_sale_amount: {result['usd_sale_amount']}")
                print(f"   - usd_payout: {result['usd_payout']}")
                print(f"   - created_at: {result['created_at']}")
            else:
                print(f"❌ 未找到测试数据: {conversion_id}")
        
        await conn.close()
        return count
        
    except Exception as e:
        print(f"❌ 数据库检查失败: {str(e)}")
        return None

def test_get_request():
    """测试GET请求"""
    print("🔍 测试GET请求...")
    
    test_data = {
        "sub_id": "test_db_storage_get",
        "media_id": "test_media_db_get",
        "click_id": "test_click_db_get",
        "usd_sale_amount": "150.75",
        "usd_payout": "22.50",
        "offer_name": "Database Test Offer GET",
        "conversion_id": f"db_test_get_{int(time.time())}",
        "conversion_datetime": "2025-07-12T12:00:00Z"
    }
    
    try:
        response = requests.get(API_URL, params=test_data, timeout=10)
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应: {json.dumps(result, indent=2)}")
            
            # 检查是否有数据库存储标识
            if result.get('db_stored'):
                print("✅ GET请求 - 数据库存储成功")
                return test_data['conversion_id']
            else:
                print("❌ GET请求 - 数据库存储失败")
                return None
        else:
            print(f"❌ GET请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ GET请求异常: {str(e)}")
        return None

def test_post_request():
    """测试POST请求"""
    print("🔍 测试POST请求...")
    
    test_data = {
        "sub_id": "test_db_storage_post",
        "media_id": "test_media_db_post",
        "click_id": "test_click_db_post",
        "usd_sale_amount": "200.50",
        "usd_payout": "35.75",
        "offer_name": "Database Test Offer POST",
        "conversion_id": f"db_test_post_{int(time.time())}",
        "conversion_datetime": "2025-07-12T12:05:00Z"
    }
    
    try:
        response = requests.post(
            API_URL,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应: {json.dumps(result, indent=2)}")
            
            # 检查是否有数据库存储标识
            if result.get('db_stored'):
                print("✅ POST请求 - 数据库存储成功")
                return test_data['conversion_id']
            else:
                print("❌ POST请求 - 数据库存储失败")
                return None
        else:
            print(f"❌ POST请求失败: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ POST请求异常: {str(e)}")
        return None

def test_db_test_endpoint():
    """测试数据库测试端点"""
    print("🔍 测试数据库测试端点...")
    
    try:
        response = requests.get(f"{API_URL[:-6]}/db-test", timeout=10)
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   响应: {json.dumps(result, indent=2)}")
            
            if result.get('status') == 'success':
                print("✅ 数据库测试端点 - 连接正常")
                return True
            else:
                print("❌ 数据库测试端点 - 连接失败")
                return False
        else:
            print(f"❌ 数据库测试端点失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 数据库测试端点异常: {str(e)}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试involve endpoint的数据库存储功能")
    print("=" * 60)
    
    # 1. 检查测试前的数据库状态
    initial_count = await check_database_before_test()
    if initial_count is None:
        print("❌ 无法连接数据库，测试终止")
        return
    
    print("\n" + "=" * 60)
    
    # 2. 测试数据库测试端点
    db_test_success = test_db_test_endpoint()
    
    print("\n" + "=" * 60)
    
    # 3. 测试GET请求
    get_conversion_id = test_get_request()
    
    print("\n" + "=" * 60)
    
    # 4. 测试POST请求
    post_conversion_id = test_post_request()
    
    print("\n" + "=" * 60)
    
    # 5. 等待数据同步
    print("⏳ 等待数据同步...")
    await asyncio.sleep(3)
    
    # 6. 检查测试后的数据库状态
    test_conversion_ids = []
    if get_conversion_id:
        test_conversion_ids.append(get_conversion_id)
    if post_conversion_id:
        test_conversion_ids.append(post_conversion_id)
    
    if test_conversion_ids:
        final_count = await check_database_after_test(initial_count, test_conversion_ids)
        
        print("\n" + "=" * 60)
        
        # 7. 测试总结
        print("📋 测试总结:")
        print(f"   数据库测试端点: {'✅ 成功' if db_test_success else '❌ 失败'}")
        print(f"   GET请求测试: {'✅ 成功' if get_conversion_id else '❌ 失败'}")
        print(f"   POST请求测试: {'✅ 成功' if post_conversion_id else '❌ 失败'}")
        
        if final_count and final_count > initial_count:
            print(f"   数据库存储: ✅ 成功 (新增 {final_count - initial_count} 条记录)")
        else:
            print(f"   数据库存储: ❌ 失败 (数据未写入数据库)")
        
        # 总体结果
        success_count = sum([db_test_success, bool(get_conversion_id), bool(post_conversion_id)])
        if success_count == 3 and final_count > initial_count:
            print("\n🎉 所有测试通过！involve endpoint数据库存储功能正常工作")
        else:
            print(f"\n⚠️  测试结果: {success_count}/3 通过，需要检查问题")
    else:
        print("\n❌ 没有成功的测试数据，无法验证数据库存储")

if __name__ == "__main__":
    asyncio.run(main()) 
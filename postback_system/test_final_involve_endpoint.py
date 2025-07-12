#!/usr/bin/env python3
"""
完整测试involve endpoint的功能
"""

import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timezone
import time

# 数据库连接配置
DATABASE_URL = "postgresql://postback_admin:ByteC2024PostBack_CloudSQL_20250708@34.124.206.16:5432/postback_db"

# API endpoint
API_URL = "https://bytec-public-postback-472712465571.asia-southeast1.run.app"

async def get_db_count():
    """获取数据库中今天的记录数"""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        today = datetime.now().date()
        count = await conn.fetchval("""
            SELECT COUNT(*) FROM conversions 
            WHERE DATE(created_at) = $1
        """, today)
        await conn.close()
        return count
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        return None

def test_endpoint(endpoint, method="GET", data=None):
    """测试endpoint"""
    try:
        url = f"{API_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        
        return {
            "status_code": response.status_code,
            "response": response.json()
        }
    except Exception as e:
        return {
            "status_code": 0,
            "error": str(e)
        }

async def main():
    """主测试函数"""
    print("🔍 开始完整测试 involve endpoint")
    print("=" * 50)
    
    # 1. 获取初始数据库状态
    print("📊 Step 1: 获取初始数据库状态")
    initial_count = await get_db_count()
    print(f"数据库中今天的记录数: {initial_count}")
    
    # 2. 测试健康检查
    print("\n🏥 Step 2: 测试健康检查")
    health_result = test_endpoint("/health")
    print(f"健康检查状态: {health_result['status_code']}")
    if health_result['status_code'] == 200:
        print(f"数据库状态: {health_result['response'].get('database_status', 'unknown')}")
    
    # 3. 测试involve健康检查
    print("\n🏥 Step 3: 测试involve健康检查")
    involve_health_result = test_endpoint("/involve/health")
    print(f"involve健康检查状态: {involve_health_result['status_code']}")
    if involve_health_result['status_code'] == 200:
        print(f"数据库启用: {involve_health_result['response'].get('database_enabled', 'unknown')}")
        print(f"记录总数: {involve_health_result['response'].get('total_records', 'unknown')}")
    
    # 4. 测试数据库连接
    print("\n🔌 Step 4: 测试数据库连接")
    db_test_result = test_endpoint("/involve/db-test")
    print(f"数据库连接测试状态: {db_test_result['status_code']}")
    if db_test_result['status_code'] == 200:
        print(f"数据库连接: {db_test_result['response'].get('database_connection', 'unknown')}")
        print(f"今天的转化数据: {db_test_result['response'].get('today_conversions', 'unknown')}")
    
    # 5. 测试GET请求
    print("\n📥 Step 5: 测试GET请求")
    timestamp = int(time.time())
    test_data = {
        "sub_id": f"test_sub_{timestamp}",
        "media_id": f"test_media_{timestamp}",
        "click_id": f"test_click_{timestamp}",
        "usd_sale_amount": "100.50",
        "usd_payout": "15.25",
        "offer_name": "Test Final Offer",
        "conversion_id": f"test_conv_{timestamp}",
        "conversion_datetime": datetime.now(timezone.utc).isoformat()
    }
    
    # 构建GET请求URL
    get_url = f"/involve/event?sub_id={test_data['sub_id']}&media_id={test_data['media_id']}&click_id={test_data['click_id']}&usd_sale_amount={test_data['usd_sale_amount']}&usd_payout={test_data['usd_payout']}&offer_name={test_data['offer_name']}&conversion_id={test_data['conversion_id']}&conversion_datetime={test_data['conversion_datetime']}"
    
    get_result = test_endpoint(get_url)
    print(f"GET请求状态: {get_result['status_code']}")
    if get_result['status_code'] == 200:
        response_data = get_result['response']
        print(f"记录ID: {response_data.get('record_id', 'unknown')}")
        print(f"数据库存储: {response_data.get('db_stored', 'unknown')}")
        print(f"消息: {response_data.get('message', 'unknown')}")
    
    # 6. 测试POST请求
    print("\n📤 Step 6: 测试POST请求")
    post_data = {
        "sub_id": f"test_sub_post_{timestamp}",
        "media_id": f"test_media_post_{timestamp}",
        "click_id": f"test_click_post_{timestamp}",
        "usd_sale_amount": "200.75",
        "usd_payout": "30.50",
        "offer_name": "Test Final POST Offer",
        "conversion_id": f"test_conv_post_{timestamp}",
        "conversion_datetime": datetime.now(timezone.utc).isoformat()
    }
    
    post_result = test_endpoint("/involve/event", method="POST", data=post_data)
    print(f"POST请求状态: {post_result['status_code']}")
    if post_result['status_code'] == 200:
        response_data = post_result['response']
        print(f"记录ID: {response_data.get('record_id', 'unknown')}")
        print(f"数据库存储: {response_data.get('db_stored', 'unknown')}")
        print(f"消息: {response_data.get('message', 'unknown')}")
    
    # 7. 等待并检查数据库状态
    print("\n⏳ Step 7: 等待并检查数据库状态")
    await asyncio.sleep(5)
    
    final_count = await get_db_count()
    print(f"测试后数据库中今天的记录数: {final_count}")
    
    if initial_count is not None and final_count is not None:
        new_records = final_count - initial_count
        print(f"新增记录数: {new_records}")
        if new_records > 0:
            print("✅ 数据库存储测试通过")
        else:
            print("❌ 数据库存储测试失败")
    else:
        print("⚠️ 无法确定数据库状态")
    
    # 8. 总结
    print("\n📋 测试总结")
    print("=" * 50)
    print(f"健康检查: {'✅' if health_result['status_code'] == 200 else '❌'}")
    print(f"involve健康检查: {'✅' if involve_health_result['status_code'] == 200 else '❌'}")
    print(f"数据库连接: {'✅' if db_test_result['status_code'] == 200 else '❌'}")
    print(f"GET请求: {'✅' if get_result['status_code'] == 200 else '❌'}")
    print(f"POST请求: {'✅' if post_result['status_code'] == 200 else '❌'}")
    
    if initial_count is not None and final_count is not None:
        new_records = final_count - initial_count
        print(f"数据库存储: {'✅' if new_records > 0 else '❌'}")
    else:
        print("数据库存储: ⚠️ 无法确定")

if __name__ == "__main__":
    asyncio.run(main()) 
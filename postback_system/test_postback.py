#!/usr/bin/env python3
"""
Postback系统测试脚本
"""

import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200

async def test_system_info():
    """测试系统信息"""
    print("\n🔍 测试系统信息...")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/info")
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2)}")

async def test_postback_get():
    """测试GET方式Postback"""
    print("\n🔍 测试GET方式Postback...")
    
    # 测试参数
    params = {
        "conversion_id": "test_conv_001",
        "offer_id": "offer_100",
        "offer_name": "Test Offer",
        "usd_sale_amount": 50.00,
        "usd_payout": 5.00,
        "order_id": "order_12345",
        "status": "Approved",
        "ts_token": "test-token",
        "aff_sub": "affiliate_123",
        "aff_sub2": "campaign_456"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/postback/", params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")

async def test_postback_post():
    """测试POST方式Postback"""
    print("\n🔍 测试POST方式Postback...")
    
    # 测试数据
    data = {
        "conversion_id": "test_conv_002",
        "offer_id": "offer_200",
        "offer_name": "Test Offer 2",
        "usd_sale_amount": 75.50,
        "usd_payout": 7.55,
        "order_id": "order_67890",
        "status": "Pending",
        "datetime_conversion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "conversion_currency": "USD",
        "aff_sub": "affiliate_789",
        "adv_sub": "advertiser_123"
    }
    
    params = {"ts_token": "test-token"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/postback/", 
            params=params,
            json=data
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), indent=2)}")

async def test_duplicate_postback():
    """测试重复数据处理"""
    print("\n🔍 测试重复数据处理...")
    
    params = {
        "conversion_id": "test_conv_001",  # 重复的conversion_id
        "offer_id": "offer_100",
        "usd_sale_amount": 50.00,
        "usd_payout": 5.00,
        "ts_token": "test-token"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/postback/", params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")

async def test_query_conversions():
    """测试查询转换数据"""
    print("\n🔍 测试查询转换数据...")
    
    params = {
        "page": 1,
        "page_size": 5
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/postback/conversions", params=params)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"总数: {data.get('total', 0)}")
            print(f"转换数据: {len(data.get('conversions', []))}")
            for conv in data.get('conversions', [])[:2]:  # 显示前2条
                print(f"  - ID: {conv['conversion_id']}, 金额: ${conv.get('usd_sale_amount', 0)}")
        else:
            print(f"错误: {response.text}")

async def test_stats():
    """测试统计信息"""
    print("\n🔍 测试统计信息...")
    
    params = {"hours": 24}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/postback/stats", params=params)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"24小时内转换数: {stats.get('total_conversions', 0)}")
            print(f"总金额(USD): ${stats.get('total_usd_amount', 0)}")
            print(f"每小时请求数: {stats.get('requests_per_hour', 0):.2f}")
        else:
            print(f"错误: {response.text}")

async def test_invalid_data():
    """测试无效数据处理"""
    print("\n🔍 测试无效数据处理...")
    
    # 测试缺少必填字段
    params = {
        "offer_id": "offer_100",
        "usd_sale_amount": 50.00,
        # 缺少conversion_id
        "ts_token": "test-token"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/postback/", params=params)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")

async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始Postback系统测试")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health_check),
        ("系统信息", test_system_info),
        ("GET Postback", test_postback_get),
        ("POST Postback", test_postback_post),
        ("重复数据", test_duplicate_postback),
        ("查询转换", test_query_conversions),
        ("统计信息", test_stats),
        ("无效数据", test_invalid_data)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if test_name == "健康检查":
                success = await test_func()
                results.append((test_name, "✅" if success else "❌"))
            else:
                await test_func()
                results.append((test_name, "✅"))
        except Exception as e:
            print(f"❌ {test_name} 测试失败: {str(e)}")
            results.append((test_name, "❌"))
        
        await asyncio.sleep(0.5)  # 短暂延迟
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    for test_name, status in results:
        print(f"  {status} {test_name}")
    
    success_count = sum(1 for _, status in results if status == "✅")
    print(f"\n成功: {success_count}/{len(results)}")

if __name__ == "__main__":
    print("请确保Postback系统正在运行 (python main.py)")
    print("等待3秒后开始测试...")
    import time
    time.sleep(3)
    
    asyncio.run(run_all_tests()) 
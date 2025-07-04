#!/usr/bin/env python3
"""
ByteC Involve Endpoint测试脚本
测试新的 /postback/involve/event endpoint
"""

import requests
import json
import time
from urllib.parse import urlencode

# 测试配置
BASE_URL = "http://localhost:8000"
ENDPOINT = "/postback/involve/event"

def test_bytec_involve_endpoint():
    """测试ByteC定制化的involve endpoint"""
    
    print("🚀 开始测试ByteC Involve Endpoint")
    print("=" * 50)
    
    # 测试用例1: 基本参数测试
    print("🔍 测试1: 基本参数测试...")
    
    params = {
        'conversion_id': 'bytec_test_001',
        'click_id': 'click_12345',
        'media_id': 'media_67890',
        'rewards': '25.50',
        'event': 'purchase',
        'event_time': '2024-07-03 22:30:00',
        'offer_name': 'ByteC Test Offer',
        'usd_sale_amount': '100.00',
        'ts_token': 'bytec_test_token'
    }
    
    url = f"{BASE_URL}{ENDPOINT}?" + urlencode(params)
    
    try:
        response = requests.get(url, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200 and response.text == "OK":
            print("✅ 测试1通过")
        else:
            print("❌ 测试1失败")
            
    except Exception as e:
        print(f"❌ 测试1异常: {e}")
    
    print()
    
    # 测试用例2: 拼写错误参数测试 (rewars vs rewards)
    print("🔍 测试2: 拼写错误参数测试...")
    
    params2 = {
        'conversion_id': 'bytec_test_002',
        'click_id': 'click_54321',
        'rewars': '15.25',  # 故意拼写错误
        'event': 'lead',
        'event_time': '2024-07-03 22:35:00'
    }
    
    url2 = f"{BASE_URL}{ENDPOINT}?" + urlencode(params2)
    
    try:
        response = requests.get(url2, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 测试2通过 (支持拼写错误)")
        else:
            print("❌ 测试2失败")
            
    except Exception as e:
        print(f"❌ 测试2异常: {e}")
    
    print()
    
    # 测试用例3: 最小参数测试
    print("🔍 测试3: 最小参数测试...")
    
    params3 = {
        'conversion_id': 'bytec_test_003'
    }
    
    url3 = f"{BASE_URL}{ENDPOINT}?" + urlencode(params3)
    
    try:
        response = requests.get(url3, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code in [200, 400]:  # 可能因为缺少必要参数而返回400
            print("✅ 测试3通过")
        else:
            print("❌ 测试3失败")
            
    except Exception as e:
        print(f"❌ 测试3异常: {e}")
    
    print()
    
    # 测试用例4: 完整参数测试 (模拟真实场景)
    print("🔍 测试4: 完整参数测试 (真实场景模拟)...")
    
    params4 = {
        'conversion_id': 'CONV_20240703_001',
        'click_id': 'CLK_SH_001_20240703',
        'media_id': 'MED_TT_001',
        'rewards': '12.75',
        'event': 'purchase',
        'event_time': '2024-07-03 22:40:00',
        'offer_name': 'Shopee Summer Sale',
        'datetime_conversion': '2024-07-03 22:40:00',
        'usd_sale_amount': '85.50',
        'offer_id': 'OFFER_001',
        'order_id': 'ORDER_12345678',
        'status': 'Approved',
        'ts_token': 'shopee_production_token'
    }
    
    url4 = f"{BASE_URL}{ENDPOINT}?" + urlencode(params4)
    
    try:
        response = requests.get(url4, timeout=10)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 测试4通过")
        else:
            print("❌ 测试4失败")
            
    except Exception as e:
        print(f"❌ 测试4异常: {e}")
    
    print()
    
    # 测试系统状态
    print("🔍 检查系统状态...")
    
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"✅ 系统健康状态: {health_data.get('status')}")
            print(f"📊 数据库状态: {health_data.get('database')}")
            print(f"⏱️ 运行时间: {health_data.get('uptime_seconds')}秒")
        else:
            print("❌ 系统健康检查失败")
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
    
    print()
    
    # 查询转换数据
    print("🔍 查询转换数据...")
    
    try:
        conversions_response = requests.get(f"{BASE_URL}/postback/conversions?page=1&page_size=5", timeout=5)
        if conversions_response.status_code == 200:
            conversions_data = conversions_response.json()
            print(f"📈 转换数据总数: {conversions_data.get('total')}")
            print(f"📄 当前页数据: {len(conversions_data.get('conversions', []))}")
        else:
            print("❌ 转换数据查询失败")
    except Exception as e:
        print(f"❌ 转换数据查询异常: {e}")
    
    print()
    print("=" * 50)
    print("🎯 测试完成！")
    print()
    print("📋 参数映射说明:")
    print("  click_id → aff_sub (点击ID)")
    print("  media_id → aff_sub2 (媒体ID)")
    print("  rewards/rewars → usd_payout (奖励金额)")
    print("  event → aff_sub3 (事件类型)")
    print("  event_time → datetime_conversion (事件时间)")
    print()
    print("🌐 对外URL格式:")
    print("  https://network.bytec.com/involve/event?conversion_id={conversion_id}&click_id={aff_sub}&media_id={aff_sub2}&rewards={usd_payout}&conversion_id={conversion_id}&event={aff_sub3}&event_time={datetime_conversion}&offer_name={offer_name}&usd_sale_amount={usd_sale_amount}")


def test_url_generation():
    """生成测试URL示例"""
    
    print("\n🔗 生成测试URL示例:")
    print("=" * 50)
    
    examples = [
        {
            'name': 'Shopee转换示例',
            'params': {
                'conversion_id': 'SP_CONV_001',
                'click_id': 'SP_CLK_12345',
                'media_id': 'SP_MED_001',
                'rewards': '15.50',
                'event': 'purchase',
                'event_time': '2024-07-03 23:00:00',
                'offer_name': 'Shopee Electronics',
                'usd_sale_amount': '299.99'
            }
        },
        {
            'name': 'TikTok Shop转换示例',
            'params': {
                'conversion_id': 'TT_CONV_002',
                'click_id': 'TT_CLK_67890',
                'media_id': 'TT_MED_002',
                'rewars': '8.25',  # 故意拼写错误测试
                'event': 'add_to_cart',
                'event_time': '2024-07-03 23:05:00',
                'offer_name': 'TikTok Fashion Sale'
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}:")
        
        # 本地URL
        local_url = f"http://localhost:8000/postback/involve/event?" + urlencode(example['params'])
        print(f"   本地: {local_url}")
        
        # 生产URL
        prod_url = f"https://network.bytec.com/involve/event?" + urlencode(example['params'])
        print(f"   生产: {prod_url}")


if __name__ == "__main__":
    print("请确保Postback系统正在运行 (python run.py)")
    print("等待3秒后开始测试...")
    time.sleep(3)
    
    test_bytec_involve_endpoint()
    test_url_generation() 
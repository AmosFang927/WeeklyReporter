#!/usr/bin/env python3
"""
🧪 Cloudflare Workers模拟测试
模拟Cloudflare Workers代理行为，验证端到端的请求处理流程
"""

import requests
import time
import json
from urllib.parse import urlencode, parse_qs

# 配置
LOCAL_SERVER = 'http://localhost:8000'
LOCALTUNNEL_SERVER = 'https://bytec-postback.loca.lt'

class CloudflareWorkerSimulator:
    """模拟Cloudflare Workers的行为"""
    
    def __init__(self, backend_url):
        self.backend_url = backend_url
        self.request_count = 0
        
    def simulate_request(self, path, params):
        """模拟Worker处理请求"""
        self.request_count += 1
        start_time = time.time()
        
        print(f"\n🔄 [{self.request_count}] 模拟Worker请求处理...")
        print(f"📍 路径: {path}")
        print(f"📋 参数: {params}")
        
        # 1. 模拟安全验证
        if 'conversion_id' not in params:
            return self._error_response("Missing required parameter: conversion_id", 400)
        
        # 2. 构建后端URL
        backend_path = "/postback/involve/event"
        backend_url = f"{self.backend_url}{backend_path}"
        full_url = f"{backend_url}?{urlencode(params)}"
        
        print(f"🎯 代理到: {full_url}")
        
        try:
            # 3. 模拟代理请求
            headers = {
                'X-Forwarded-For': '203.0.113.195',  # 模拟客户端IP
                'X-Forwarded-Proto': 'https',
                'X-Forwarded-Host': 'network.bytec.com',
                'X-Worker-Proxy': 'ByteC-Network-Simulator',
                'User-Agent': 'CloudflareWorker/Simulator'
            }
            
            response = requests.get(full_url, headers=headers, timeout=10)
            duration = (time.time() - start_time) * 1000
            
            # 4. 模拟响应处理
            result = {
                'status': response.status_code,
                'body': response.text,
                'duration_ms': round(duration, 2),
                'headers': dict(response.headers)
            }
            
            print(f"✅ 代理成功: {response.status_code} ({duration:.2f}ms)")
            return result
            
        except requests.exceptions.RequestException as e:
            duration = (time.time() - start_time) * 1000
            print(f"❌ 代理失败: {str(e)} ({duration:.2f}ms)")
            return self._error_response(f"Backend connection failed: {str(e)}", 502)
    
    def _error_response(self, message, status):
        """创建错误响应"""
        return {
            'status': status,
            'body': message,
            'duration_ms': 0,
            'headers': {'Content-Type': 'text/plain', 'X-Error': 'true'}
        }

def run_simulation_tests():
    """运行完整的模拟测试套件"""
    
    print("🚀 ByteC Cloudflare Workers 端到端模拟测试")
    print("=" * 60)
    
    # 首先测试本地服务器
    print("\n1️⃣ 验证本地服务器状态...")
    try:
        health_response = requests.get(f"{LOCAL_SERVER}/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ 本地服务器运行正常")
        else:
            print("❌ 本地服务器状态异常")
            return False
    except:
        print("❌ 本地服务器无法连接")
        return False
    
    # 创建Worker模拟器
    simulator = CloudflareWorkerSimulator(LOCAL_SERVER)
    
    # 测试用例
    test_cases = [
        {
            'name': '基本功能测试',
            'path': '/involve/event',
            'params': {
                'conversion_id': 'sim_test_001',
                'click_id': 'click_sim_001'
            },
            'expected_status': 200
        },
        {
            'name': '完整参数测试',
            'path': '/involve/event',
            'params': {
                'conversion_id': 'sim_test_002',
                'click_id': 'CLK_SIM_002',
                'media_id': 'MED_SIM_002',
                'event': 'purchase',
                'offer_name': 'Cloudflare Test Offer',
                'event_time': '2024-07-03 23:15:00'
            },
            'expected_status': 200
        },
        {
            'name': '支持rewars拼写错误',
            'path': '/involve/event',
            'params': {
                'conversion_id': 'sim_test_003',
                'click_id': 'CLK_SIM_003',
                'rewars': '25.50'  # 故意的拼写错误
            },
            'expected_status': 200
        },
        {
            'name': '缺少必需参数',
            'path': '/involve/event',
            'params': {
                'click_id': 'CLK_SIM_004'
                # 故意缺少conversion_id
            },
            'expected_status': 400
        },
        {
            'name': '实际场景模拟',
            'path': '/involve/event',
            'params': {
                'conversion_id': 'IV_240703_001',
                'click_id': 'SPE_240703_12345',
                'media_id': 'TTS_SHOP_001',
                'rewards': '15.75',
                'event': 'purchase',
                'event_time': '2024-07-03 23:20:00',
                'offer_name': 'Shopee Electronics Deal',
                'usd_sale_amount': '89.99'
            },
            'expected_status': 200
        }
    ]
    
    # 执行测试
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n2️⃣.{i} {test['name']}")
        print("-" * 40)
        
        result = simulator.simulate_request(test['path'], test['params'])
        
        if result['status'] == test['expected_status']:
            print(f"✅ 测试通过: {result['status']} (预期: {test['expected_status']})")
            if result['status'] == 200:
                print(f"📤 响应: {result['body'][:50]}...")
            passed += 1
        else:
            print(f"❌ 测试失败: {result['status']} (预期: {test['expected_status']})")
            print(f"📤 响应: {result['body']}")
            failed += 1
    
    # 性能测试
    print(f"\n3️⃣ 性能压力测试")
    print("-" * 40)
    
    start_time = time.time()
    concurrent_requests = []
    
    for i in range(5):
        params = {
            'conversion_id': f'perf_test_{i+1:03d}',
            'click_id': f'perf_click_{i+1:03d}',
            'event': 'purchase'
        }
        result = simulator.simulate_request('/involve/event', params)
        concurrent_requests.append(result['duration_ms'])
    
    total_time = (time.time() - start_time) * 1000
    avg_response_time = sum(concurrent_requests) / len(concurrent_requests)
    
    print(f"📊 5个连续请求统计:")
    print(f"   总耗时: {total_time:.2f}ms")
    print(f"   平均响应时间: {avg_response_time:.2f}ms")
    print(f"   最快: {min(concurrent_requests):.2f}ms")
    print(f"   最慢: {max(concurrent_requests):.2f}ms")
    
    # 测试总结
    print(f"\n🎯 测试总结")
    print("=" * 60)
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📊 总请求数: {simulator.request_count}")
    
    if failed == 0:
        print("\n🎉 所有测试通过！Cloudflare Workers部署准备就绪")
        print("📋 接下来可以：")
        print("   1. 部署到 Cloudflare Workers")
        print("   2. 配置自定义域名 network.bytec.com")
        print("   3. 进行生产环境测试")
        return True
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请修复后重试")
        return False

if __name__ == "__main__":
    success = run_simulation_tests()
    exit(0 if success else 1) 
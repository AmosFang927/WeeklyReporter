#!/usr/bin/env python3
"""
Cloud Run WeeklyReporter服务测试脚本
"""

import requests
import json
import time

SERVICE_URL = "https://weeklyreporter-crwdeesavq-de.a.run.app"

def test_health_check():
    """测试健康检查端点"""
    print("🏥 测试健康检查...")
    try:
        response = requests.get(f"{SERVICE_URL}/")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data['status']}")
            print(f"版本: {data['version']}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_status():
    """测试状态端点"""
    print("\n📊 测试状态端点...")
    try:
        response = requests.get(f"{SERVICE_URL}/status")
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态端点正常: {data['status']}")
            print(f"支持的端点: {list(data['endpoints'].keys())}")
            return True
        else:
            print(f"❌ 状态端点失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 状态端点异常: {e}")
        return False

def test_simple_run():
    """测试简单的运行端点"""
    print("\n🧪 测试简单运行端点...")
    try:
        payload = {
            "partner": "RAMPUP",
            "start_date": "2025-06-25",
            "end_date": "2025-06-25",
            "limit": 5,
            "save_json": False,
            "upload_feishu": False,
            "send_email": False
        }
        
        print(f"📋 发送请求: {json.dumps(payload, indent=2)}")
        response = requests.post(
            f"{SERVICE_URL}/run",
            json=payload,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 运行请求成功: {data['status']}")
            print(f"消息: {data['message']}")
            print(f"命令: {data['command']}")
            return True
        else:
            print(f"❌ 运行请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 运行请求异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试WeeklyReporter Cloud Run服务")
    print(f"🌐 服务地址: {SERVICE_URL}")
    print("=" * 60)
    
    # 测试所有端点
    health_ok = test_health_check()
    status_ok = test_status()
    run_ok = test_simple_run()
    
    print("\n" + "=" * 60)
    print("📋 测试结果总结:")
    print(f"健康检查: {'✅' if health_ok else '❌'}")
    print(f"状态端点: {'✅' if status_ok else '❌'}")
    print(f"运行端点: {'✅' if run_ok else '❌'}")
    
    if all([health_ok, status_ok, run_ok]):
        print("\n🎉 所有测试通过！服务运行正常。")
        return 0
    else:
        print("\n⚠️  部分测试失败，需要进一步检查。")
        return 1

if __name__ == "__main__":
    exit(main()) 
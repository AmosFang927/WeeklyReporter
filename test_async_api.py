#!/usr/bin/env python3
"""
异步API测试脚本
用于验证异步I/O实现是否正常工作
"""

import sys
import os
import time
import asyncio
from datetime import datetime, timedelta

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.logger import print_step
import config

def test_async_api_basic():
    """基础异步API测试"""
    print_step("基础测试", "开始测试异步API基础功能...")
    
    try:
        # 导入异步API模块
        from modules.involve_asia_api_async import AsyncInvolveAsiaAPI
        print_step("导入成功", "异步API模块导入成功")
        
        # 创建API实例
        api = AsyncInvolveAsiaAPI()
        print_step("实例创建", "异步API实例创建成功")
        
        # 测试配置获取
        async_config = config.get_async_config()
        print_step("配置获取", f"异步配置: {async_config}")
        
        return True
        
    except ImportError as e:
        print_step("导入失败", f"异步API模块导入失败: {str(e)}")
        return False
    except Exception as e:
        print_step("测试失败", f"基础测试失败: {str(e)}")
        return False

def test_async_authentication():
    """测试异步认证"""
    print_step("认证测试", "开始测试异步API认证...")
    
    try:
        from modules.involve_asia_api_async import AsyncInvolveAsiaAPI
        
        async def test_auth():
            api = AsyncInvolveAsiaAPI()
            result = await api.authenticate()
            return result
        
        result = asyncio.run(test_auth())
        
        if result:
            print_step("认证成功", "异步API认证测试通过")
            return True
        else:
            print_step("认证失败", "异步API认证测试失败")
            return False
            
    except Exception as e:
        print_step("认证异常", f"异步认证测试异常: {str(e)}")
        return False

def test_async_data_fetch():
    """测试异步数据获取"""
    print_step("数据获取测试", "开始测试异步数据获取...")
    
    try:
        from modules.involve_asia_api_async import AsyncInvolveAsiaAPI
        
        # 使用昨天的日期进行测试
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        async def test_fetch():
            api = AsyncInvolveAsiaAPI()
            
            # 设置测试限制，避免获取太多数据
            original_limit = config.MAX_RECORDS_LIMIT
            config.MAX_RECORDS_LIMIT = 50
            
            try:
                # 认证
                if not await api.authenticate():
                    return None, "认证失败"
                
                # 获取数据
                data = await api.get_conversions_async(yesterday, yesterday)
                return data, None
                
            finally:
                # 恢复原始限制
                config.MAX_RECORDS_LIMIT = original_limit
        
        start_time = time.time()
        data, error = asyncio.run(test_fetch())
        end_time = time.time()
        
        if error:
            print_step("数据获取失败", f"异步数据获取失败: {error}")
            return False
        
        if data and 'data' in data:
            record_count = data['data'].get('current_page_count', 0)
            elapsed_time = end_time - start_time
            print_step("数据获取成功", f"异步获取 {record_count} 条记录，耗时 {elapsed_time:.2f}秒")
            
            # 检查异步标记
            if data['data'].get('async_mode'):
                print_step("异步标记", "数据包含异步模式标记 ✅")
            else:
                print_step("异步标记", "数据缺少异步模式标记 ⚠️")
            
            return True
        else:
            print_step("数据获取失败", "异步数据获取返回空数据")
            return False
            
    except Exception as e:
        print_step("数据获取异常", f"异步数据获取测试异常: {str(e)}")
        return False

def test_performance_comparison():
    """测试性能比较"""
    print_step("性能比较", "开始测试同步vs异步性能比较...")
    
    try:
        from modules.involve_asia_api_async import compare_sync_vs_async_performance
        
        # 使用昨天的日期进行测试
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print_step("性能测试", "执行同步vs异步性能比较...")
        result = compare_sync_vs_async_performance(yesterday, yesterday, test_pages=3)
        
        print_step("性能结果", f"异步时间: {result['async_time']:.2f}s")
        print_step("性能结果", f"同步时间: {result['sync_time']:.2f}s")
        print_step("性能结果", f"性能提升: {result['performance_ratio']:.2f}x")
        print_step("性能结果", f"时间节省: {result['time_saved_seconds']:.2f}s")
        
        if result['async_success'] and result['sync_success']:
            print_step("性能测试成功", "同步和异步模式都运行成功")
            return True
        else:
            print_step("性能测试失败", "部分模式运行失败")
            return False
            
    except Exception as e:
        print_step("性能测试异常", f"性能比较测试异常: {str(e)}")
        return False

def test_main_integration():
    """测试main.py集成"""
    print_step("集成测试", "开始测试main.py异步集成...")
    
    try:
        # 导入main模块
        import main
        
        # 检查异步API是否可用
        if main.ASYNC_API_AVAILABLE:
            print_step("集成检查", "main.py中异步API可用 ✅")
        else:
            print_step("集成检查", "main.py中异步API不可用 ❌")
            return False
        
        # 检查配置函数
        if hasattr(config, 'should_use_async_api'):
            should_use = config.should_use_async_api()
            print_step("配置检查", f"should_use_async_api: {should_use}")
        else:
            print_step("配置检查", "should_use_async_api函数不存在 ❌")
            return False
        
        print_step("集成测试成功", "main.py异步集成测试通过")
        return True
        
    except Exception as e:
        print_step("集成测试异常", f"集成测试异常: {str(e)}")
        return False

def test_concurrent_configuration():
    """测试并发配置"""
    print_step("并发配置测试", "开始测试并发配置功能...")
    
    try:
        # 测试配置获取
        async_config = config.get_async_config()
        print_step("配置信息", f"最大并发数: {async_config['max_concurrent_requests']}")
        print_step("配置信息", f"批次大小: {async_config['async_batch_size']}")
        
        # 测试动态并发数计算
        for pages in [1, 5, 10, 20, 50]:
            optimal = config.get_optimal_concurrent_requests(pages)
            print_step("动态配置", f"{pages}页 → 建议并发数: {optimal}")
        
        return True
        
    except Exception as e:
        print_step("并发配置异常", f"并发配置测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🧪 异步API测试套件")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("基础功能测试", test_async_api_basic),
        ("异步认证测试", test_async_authentication),
        ("异步数据获取测试", test_async_data_fetch),
        ("性能比较测试", test_performance_comparison),
        ("main.py集成测试", test_main_integration),
        ("并发配置测试", test_concurrent_configuration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 40}")
        print(f"🧪 {test_name}")
        print(f"{'=' * 40}")
        
        try:
            result = test_func()
            if result:
                print_step("测试结果", f"✅ {test_name} 通过")
                passed += 1
            else:
                print_step("测试结果", f"❌ {test_name} 失败")
                failed += 1
        except Exception as e:
            print_step("测试异常", f"❌ {test_name} 异常: {str(e)}")
            failed += 1
    
    print(f"\n{'=' * 60}")
    print("📊 测试总结")
    print(f"{'=' * 60}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 成功率: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print(f"\n🎉 所有测试通过！异步API功能正常")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查异步API实现")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
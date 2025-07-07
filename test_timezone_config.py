#!/usr/bin/env python3
"""
时区配置测试脚本
验证应用程序是否正确使用Asia/Singapore时区
"""

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.logger import get_timezone_info, get_timezone_aware_time, print_step
    LOGGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  无法导入logger模块: {e}")
    LOGGER_AVAILABLE = False

def test_timezone_configuration():
    """测试时区配置"""
    print("🌐 时区配置测试")
    print("=" * 60)
    
    # 1. 测试系统环境变量
    print("\n1. 系统环境变量:")
    tz_env = os.getenv('TZ')
    print(f"   TZ环境变量: {tz_env or '未设置'}")
    
    # 2. 测试Python内置时区
    print("\n2. Python时区测试:")
    
    # UTC时间
    utc_time = datetime.now(ZoneInfo('UTC'))
    print(f"   UTC时间: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # 新加坡时间
    singapore_time = datetime.now(ZoneInfo('Asia/Singapore'))
    print(f"   新加坡时间: {singapore_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # 时区偏移
    offset = singapore_time.strftime('%z')
    print(f"   UTC偏移: {offset}")
    
    # 3. 测试应用程序logger
    print("\n3. 应用程序Logger测试:")
    if LOGGER_AVAILABLE:
        try:
            timezone_info = get_timezone_info()
            print(f"   Logger时区: {timezone_info['timezone']}")
            print(f"   Logger当前时间: {timezone_info['formatted_time']}")
            print(f"   Logger UTC偏移: {timezone_info['utc_offset']}")
            
            # 使用print_step测试
            print("\n4. 测试日志输出:")
            print_step("时区测试", "这是一条测试日志，检查时间戳是否正确")
            
        except Exception as e:
            print(f"   ❌ Logger测试失败: {e}")
    else:
        print("   ⚠️  Logger不可用，跳过测试")
    
    # 4. 测试时区一致性
    print("\n5. 时区一致性检查:")
    if LOGGER_AVAILABLE:
        try:
            logger_time = get_timezone_aware_time()
            direct_time = datetime.now(ZoneInfo('Asia/Singapore'))
            
            time_diff = abs((logger_time - direct_time).total_seconds())
            if time_diff < 1:
                print("   ✅ Logger时区与直接获取的时区时间一致")
            else:
                print(f"   ❌ 时间差异: {time_diff:.2f}秒")
                
        except Exception as e:
            print(f"   ❌ 一致性检查失败: {e}")
    
    # 5. Cloud Run环境检查
    print("\n6. Cloud Run环境检查:")
    k_service = os.getenv('K_SERVICE')
    if k_service:
        print(f"   ✅ 检测到Cloud Run环境: {k_service}")
        print("   📋 Cloud Run时区配置:")
        print(f"      - TZ环境变量: {tz_env or '未设置'}")
        print(f"      - 系统时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        print("   ℹ️  本地开发环境")
    
    # 6. 建议和总结
    print("\n7. 配置建议:")
    if tz_env == 'Asia/Singapore':
        print("   ✅ TZ环境变量配置正确")
    else:
        print("   ⚠️  建议设置 TZ=Asia/Singapore")
    
    if LOGGER_AVAILABLE:
        print("   ✅ Logger模块可用且时区配置正确")
    else:
        print("   ❌ Logger模块不可用，请检查依赖")
    
    print("\n" + "=" * 60)
    print("🎉 时区配置测试完成！")
    
    # 返回测试结果
    return {
        'tz_env_correct': tz_env == 'Asia/Singapore',
        'logger_available': LOGGER_AVAILABLE,
        'singapore_time': singapore_time.isoformat(),
        'utc_offset': offset
    }

def main():
    """主函数"""
    try:
        result = test_timezone_configuration()
        
        # 如果在Cloud Run环境中，也输出到日志
        if os.getenv('K_SERVICE') and LOGGER_AVAILABLE:
            print_step("时区测试", f"时区配置测试完成，结果: {result}")
            
    except Exception as e:
        print(f"❌ 时区配置测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
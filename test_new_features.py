#!/usr/bin/env python3
"""
测试新功能：数据限制和Partner过滤
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from modules.involve_asia_api import InvolveAsiaAPI
from modules.data_processor import DataProcessor

def test_config_functions():
    """测试配置函数"""
    print("🧪 测试配置函数...")
    
    # 测试默认状态（无限制）
    print(f"默认最大记录数限制: {config.MAX_RECORDS_LIMIT}")
    print(f"默认目标Partner: {config.TARGET_PARTNER}")
    
    # 测试get_target_partners
    target_partners = config.get_target_partners()
    print(f"目标Partner列表: {target_partners}")
    
    # 测试is_partner_enabled
    for partner in ['RAMPUP', 'OPPO', 'VIVO', 'TestPub']:
        enabled = config.is_partner_enabled(partner)
        print(f"Partner '{partner}' 是否启用: {enabled}")
    
    print("✅ 配置函数测试完成\n")

def test_partner_filtering():
    """测试Partner过滤功能"""
    print("🧪 测试Partner过滤功能...")
    
    # 设置只处理RAMPUP
    original_target = config.TARGET_PARTNER
    config.TARGET_PARTNER = "RAMPUP"
    
    print(f"设置目标Partner为: {config.TARGET_PARTNER}")
    
    # 测试过滤
    target_partners = config.get_target_partners()
    print(f"过滤后的Partner列表: {target_partners}")
    
    for partner in ['RAMPUP', 'OPPO', 'VIVO', 'TestPub']:
        enabled = config.is_partner_enabled(partner)
        print(f"Partner '{partner}' 是否启用: {enabled}")
    
    # 恢复原设置
    config.TARGET_PARTNER = original_target
    print("✅ Partner过滤测试完成\n")

def test_records_limit():
    """测试记录数限制功能"""
    print("🧪 测试记录数限制功能...")
    
    # 设置记录数限制
    original_limit = config.MAX_RECORDS_LIMIT
    config.MAX_RECORDS_LIMIT = 5
    
    print(f"设置最大记录数限制为: {config.MAX_RECORDS_LIMIT}")
    
    # 创建测试数据
    test_data = {
        "status": "success",
        "data": {
            "count": 10,
            "data": [
                {"id": i, "aff_sub1": "RAMPUP", "sale_amount": 100.0} 
                for i in range(10)
            ]
        }
    }
    
    # 测试数据处理器
    processor = DataProcessor()
    result = processor._load_data(test_data)
    
    print(f"原始数据记录数: {len(test_data['data']['data'])}")
    print(f"处理后数据记录数: {len(result) if result is not None else 0}")
    
    # 恢复原设置
    config.MAX_RECORDS_LIMIT = original_limit
    print("✅ 记录数限制测试完成\n")

def test_combination():
    """测试组合功能"""
    print("🧪 测试组合功能（限制 + Partner过滤）...")
    
    # 同时设置记录限制和Partner过滤
    original_limit = config.MAX_RECORDS_LIMIT
    original_target = config.TARGET_PARTNER
    
    config.MAX_RECORDS_LIMIT = 3
    config.TARGET_PARTNER = "RAMPUP"
    
    print(f"设置最大记录数限制: {config.MAX_RECORDS_LIMIT}")
    print(f"设置目标Partner: {config.TARGET_PARTNER}")
    
    # 测试配置
    target_partners = config.get_target_partners()
    print(f"目标Partner列表: {target_partners}")
    
    print("当前配置状态:")
    for partner in ['RAMPUP', 'OPPO', 'VIVO', 'TestPub']:
        enabled = config.is_partner_enabled(partner)
        print(f"  - Partner '{partner}': {'✅ 启用' if enabled else '❌ 禁用'}")
    
    # 恢复原设置
    config.MAX_RECORDS_LIMIT = original_limit
    config.TARGET_PARTNER = original_target
    
    print("✅ 组合功能测试完成\n")

def main():
    """主测试函数"""
    print("🚀 开始测试新功能：数据限制和Partner过滤")
    print("=" * 60)
    
    test_config_functions()
    test_partner_filtering()
    test_records_limit()
    test_combination()
    
    print("🎉 所有测试完成！")
    print("\n💡 使用示例:")
    print("  # 限制100条记录，只处理RAMPUP")
    print("  python main.py --limit 100 --partner RAMPUP --start-date 2025-06-17 --end-date 2025-06-18")
    print("  # 只处理OPPO")
    print("  python main.py --partner OPPO")
    print("  # 限制50条记录")
    print("  python main.py --limit 50")

if __name__ == "__main__":
    main() 
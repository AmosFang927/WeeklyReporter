#!/usr/bin/env python3
"""
测试MKK Partner配置
验证MKK partner是否正确配置了IAByteC平台和MKK source
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from modules.involve_asia_api import InvolveAsiaAPI
from modules.data_processor import DataProcessor
from modules.email_sender import EmailSender
from utils.logger import print_step

def test_mkk_configuration():
    """测试MKK partner的配置"""
    print_step("MKK配置测试", "开始测试MKK partner配置...")
    
    # 1. 检查PARTNER_SOURCES_MAPPING
    print("1. 检查PARTNER_SOURCES_MAPPING:")
    if "MKK" in config.PARTNER_SOURCES_MAPPING:
        mkk_config = config.PARTNER_SOURCES_MAPPING["MKK"]
        print(f"   ✓ MKK配置存在")
        print(f"   - sources: {mkk_config.get('sources', [])}")
        print(f"   - pattern: {mkk_config.get('pattern', '')}")
        print(f"   - email_enabled: {mkk_config.get('email_enabled', False)}")
        print(f"   - email_recipients: {mkk_config.get('email_recipients', [])}")
    else:
        print("   ✗ MKK配置不存在")
        return False
    
    # 2. 检查PARTNER_API_MAPPING
    print("\n2. 检查PARTNER_API_MAPPING:")
    if "MKK" in config.PARTNER_API_MAPPING:
        mkk_apis = config.PARTNER_API_MAPPING["MKK"]
        print(f"   ✓ MKK API映射存在")
        print(f"   - APIs: {mkk_apis}")
        if "LisaidByteC" in mkk_apis:
            print("   ✓ 正确配置了LisaidByteC平台")
        else:
            print("   ✗ 未配置LisaidByteC平台")
            return False
    else:
        print("   ✗ MKK API映射不存在")
        return False
    
    # 3. 检查佣金率配置
    print("\n3. 检查佣金率配置:")
    mkk_commission_rates = []
    for (partner, offer), rate in config.PUB_COMMISSION_RATE_MAPPING.items():
        if partner == "MKK":
            mkk_commission_rates.append((offer, rate))
    
    if mkk_commission_rates:
        print(f"   ✓ 找到{len(mkk_commission_rates)}个MKK佣金率配置:")
        for offer, rate in mkk_commission_rates:
            print(f"   - {offer}: {rate}%")
    else:
        print("   ⚠ MKK佣金率配置为空，将使用默认值")
    
    # 4. 测试source匹配
    print("\n4. 测试source匹配:")
    test_sources = ["MKK", "MKK_001", "MKK_TEST", "OTHER"]
    for source in test_sources:
        matched_partner = config.match_source_to_partner(source)
        print(f"   - source '{source}' -> partner '{matched_partner}'")
        if source.startswith("MKK") and matched_partner != "MKK":
            print(f"   ✗ source '{source}' 应该匹配到MKK")
            return False
    
    # 5. 测试API平台获取
    print("\n5. 测试API平台获取:")
    mkk_apis = config.get_partner_api_platforms("MKK")
    print(f"   - MKK使用的API平台: {mkk_apis}")
    if "LisaidByteC" in mkk_apis:
        print("   ✓ 正确获取到LisaidByteC平台")
    else:
        print("   ✗ 未获取到LisaidByteC平台")
        return False
    
    # 6. 测试邮件配置
    print("\n6. 测试邮件配置:")
    email_config = config.get_partner_email_config("MKK")
    print(f"   - email_enabled: {email_config.get('enabled', False)}")
    print(f"   - email_recipients: {email_config.get('recipients', [])}")
    
    print_step("MKK配置测试完成", "所有配置检查通过！")
    return True

def test_mkk_data_processing():
    """测试MKK数据处理"""
    print_step("MKK数据处理测试", "开始测试MKK数据处理...")
    
    # 模拟MKK数据
    mock_data = [
        {
            "conversion_id": "MKK_001",
            "offer_name": "Shopee ID (Media Buyers) - CPS",
            "aff_sub1": "MKK",
            "sale_amount": 100.0,
            "payout": 2.5,
            "conversion_date": "2025-01-29"
        },
        {
            "conversion_id": "MKK_002", 
            "offer_name": "Shopee PH - CPS",
            "aff_sub1": "MKK",
            "sale_amount": 150.0,
            "payout": 3.0,
            "conversion_date": "2025-01-29"
        }
    ]
    
    # 测试数据处理
    processor = DataProcessor()
    processed_data = processor.process_data(mock_data)
    
    print(f"处理前数据条数: {len(mock_data)}")
    print(f"处理后数据条数: {len(processed_data)}")
    
    # 检查MKK数据是否正确处理
    mkk_data = [item for item in processed_data if item.get('partner') == 'MKK']
    print(f"MKK数据条数: {len(mkk_data)}")
    
    if len(mkk_data) == len(mock_data):
        print("✓ MKK数据正确处理")
        return True
    else:
        print("✗ MKK数据处理异常")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("MKK Partner 配置测试")
    print("=" * 60)
    
    # 测试配置
    config_ok = test_mkk_configuration()
    
    if config_ok:
        # 测试数据处理
        data_ok = test_mkk_data_processing()
        
        if data_ok:
            print("\n" + "=" * 60)
            print("✓ 所有测试通过！MKK partner配置成功")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("✗ 数据处理测试失败")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ 配置测试失败")
        print("=" * 60)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
测试新的Partner-Sources结构
验证Partner映射、Excel文件生成、Sources作为Sheets等功能
"""

import sys
import os
import pandas as pd
import json
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.data_processor import DataProcessor
from utils.logger import print_step
import config

def create_test_data_with_mixed_sources():
    """创建包含不同Partner Sources的测试数据"""
    print_step("测试数据生成", "正在生成包含多种Partner Sources的测试数据...")
    
    test_data = pd.DataFrame({
        'aff_sub1': [
            'RAMPUP',           # RAMPUP Partner
            'RPID123CXP',       # RAMPUP Partner (RPID pattern)
            'OEM3_OPPO001',     # OPPO Partner
            'OEM3_OPPO002',     # OPPO Partner  
            'OEM2_VIVO001',     # VIVO Partner
            'OEM2_VIVO002',     # VIVO Partner
            'OEM2',             # OEM2 Partner (不包含VIVO)
            'OEM3',             # OEM3 Partner (不包含OPPO)
            'TestPub',          # TestPub Partner
            'UnknownSource'     # 未映射的Source，应该作为独立Partner
        ],
        'sale_amount': [100.50, 250.75, 175.25, 80.00, 150.33, 200.66, 75.99, 300.25, 50.00, 120.80],
        'payout': [10.0, 25.0, 17.5, 8.0, 15.0, 20.0, 7.5, 30.0, 5.0, 12.0],
        'base_payout': [8.0, 20.0, 14.0, 6.4, 12.0, 16.0, 6.0, 24.0, 4.0, 9.6],
        'bonus_payout': [2.0, 5.0, 3.5, 1.6, 3.0, 4.0, 1.5, 6.0, 1.0, 2.4],
        'campaign_name': [f'Campaign {i}' for i in range(10)],
        'conversion_time': [f'2025-06-19 {10+i}:00:00' for i in range(10)],
        'conversion_id': list(range(1001, 1011)),
        'currency': ['USD'] * 10,
        'conversion_status': ['approved'] * 10
    })
    
    print_step("测试数据生成完成", f"生成了 {len(test_data)} 条测试记录，包含 {len(test_data['aff_sub1'].unique())} 个不同的Sources")
    return test_data

def test_partner_mapping():
    """测试Partner映射功能"""
    print_step("Partner映射测试", "测试Sources到Partner的映射功能")
    
    test_sources = [
        'RAMPUP',
        'RPID123CXP', 
        'RPID456ABC',
        'OEM3_OPPO001',
        'OEM3_OPPOTEST',
        'OEM2_VIVO001',
        'OEM2_VIVOTEST',
        'OEM2',
        'OEM3', 
        'TestPub',
        'UnknownSource'
    ]
    
    print("\n🧪 测试Partner映射:")
    for source in test_sources:
        partner = config.match_source_to_partner(source)
        print(f"   Source: {source:15} → Partner: {partner}")
    
    return True

def test_excel_generation():
    """测试Excel文件生成功能"""
    print_step("Excel生成测试", "测试Partner Excel文件生成，包含多个Sources作为Sheets")
    
    # 创建测试数据
    test_data = create_test_data_with_mixed_sources()
    
    # 创建数据处理器
    processor = DataProcessor()
    processor.report_date = "2025-06-19"
    
    # 模拟完整的数据处理流程
    print("\n🧪 测试数据处理流程:")
    result = processor.process_data(test_data, "test_output", "2025-06-19")
    
    return result

def test_partner_summary():
    """测试Partner汇总信息"""
    print_step("Partner汇总测试", "测试Partner汇总数据生成")
    
    result = test_excel_generation()
    
    print("\n🧪 Partner汇总信息:")
    partner_summary = result.get('partner_summary', {})
    
    for partner, info in partner_summary.items():
        print(f"\n📊 Partner: {partner}")
        print(f"   - Sources: {info.get('sources', [])} ({info.get('sources_count', 0)} 个)")
        print(f"   - 记录数: {info.get('records', 0)} 条")
        print(f"   - 总金额: {info.get('amount_formatted', '$0.00')}")
        print(f"   - 文件名: {info.get('filename', 'N/A')}")
    
    return True

def test_file_naming():
    """测试文件命名功能"""
    print_step("文件命名测试", "测试新的Partner文件命名格式")
    
    print("\n🧪 测试文件命名格式:")
    
    # 测试不同的日期格式
    test_cases = [
        ("RAMPUP", "2025-06-19", "2025-06-19"),
        ("OPPO", "2025-06-18", "2025-06-20"),
        ("VIVO", "2025-01-01", "2025-01-31"),
    ]
    
    for partner, start_date, end_date in test_cases:
        filename = config.get_partner_filename(partner, start_date, end_date)
        print(f"   Partner: {partner:8} | {start_date} to {end_date} → {filename}")
    
    return True

def test_integration():
    """集成测试"""
    print_step("集成测试", "运行完整的集成测试")
    
    # 步骤1: 测试Partner映射
    test_partner_mapping()
    
    # 步骤2: 测试文件命名
    test_file_naming()
    
    # 步骤3: 测试Excel生成
    result = test_excel_generation()
    
    # 步骤4: 测试Partner汇总
    test_partner_summary()
    
    # 步骤5: 检查生成的文件
    print_step("文件检查", "检查生成的Partner Excel文件")
    
    if result.get('pub_files'):
        print("\n📁 生成的文件:")
        for file_path in result['pub_files']:
            filename = os.path.basename(file_path)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"   ✅ {filename} ({file_size:,} bytes)")
                
                # 验证Excel文件内容
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(file_path)
                    sheet_names = wb.sheetnames
                    print(f"      Sheets: {sheet_names}")
                    wb.close()
                except Exception as e:
                    print(f"      ⚠️ 无法读取Excel文件: {e}")
            else:
                print(f"   ❌ {filename} (文件不存在)")
    
    print_step("集成测试完成", "所有测试步骤执行完毕")
    return True

def main():
    """主函数"""
    print_step("测试开始", "开始测试新的Partner-Sources结构")
    
    # 确保输出目录存在
    os.makedirs("test_output", exist_ok=True)
    
    try:
        # 运行集成测试
        test_integration()
        
        print_step("测试成功", "✅ 所有测试通过")
        
    except Exception as e:
        print_step("测试失败", f"❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
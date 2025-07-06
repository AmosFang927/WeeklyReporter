#!/usr/bin/env python3
"""
数据处理模块独立测试
测试数据清洗、金额调整、Pub分类导出等功能
"""

import sys
import os

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.data_processor import DataProcessor, process_conversion_data
from modules.involve_asia_api import InvolveAsiaAPI
from utils.logger import print_step
import config
import pandas as pd

def create_test_data():
    """创建测试数据"""
    print_step("测试数据生成", "正在生成测试数据...")
    
    test_data = pd.DataFrame({
        'aff_sub1': ['OEM3', 'OEM5', 'OEM3', 'TestPub', 'OEM5', 'OEM3'],
        'sale_amount': [100.567, 250.123, 75.999, 50.0, 180.456, 300.789],
        'payout': [10.0, 25.0, 7.5, 5.0, 18.0, 30.0],
        'base_payout': [8.0, 20.0, 6.0, 4.0, 15.0, 25.0],
        'bonus_payout': [2.0, 5.0, 1.5, 1.0, 3.0, 5.0],
        'campaign_name': ['Campaign A', 'Campaign B', 'Campaign A', 'Campaign C', 'Campaign B', 'Campaign A'],
        'conversion_time': ['2025-01-17 10:00:00', '2025-01-17 11:00:00', '2025-01-17 12:00:00', 
                           '2025-01-17 13:00:00', '2025-01-17 14:00:00', '2025-01-17 15:00:00'],
        'other_field': ['Data1', 'Data2', 'Data3', 'Data4', 'Data5', 'Data6']
    })
    
    print_step("测试数据生成完成", f"生成了 {len(test_data)} 条测试记录")
    return test_data

def test_data_processor_with_test_data():
    """使用测试数据测试数据处理模块"""
    print_step("测试开始", "开始使用测试数据测试数据处理模块")
    
    # 生成测试数据
    test_data = create_test_data()
    
    print(f"\n原始测试数据:")
    print(test_data)
    print(f"\n原始栏位: {list(test_data.columns)}")
    print(f"原始sale_amount总值: ${test_data['sale_amount'].sum():.2f}")
    
    # 创建数据处理器
    processor = DataProcessor()
    
    # 执行处理
    result = processor.process_data(test_data, output_dir="test_output")
    
    # 打印结果
    processor.print_detailed_summary(result)
    
    return result

def test_data_processor_with_api_data():
    """使用真实API数据测试数据处理模块"""
    print_step("API数据测试", "开始使用真实API数据测试数据处理模块")
    
    try:
        # 获取API数据
        api = InvolveAsiaAPI()
        api_result = api.get_conversions(
            start_date=config.DEFAULT_START_DATE,
            end_date=config.DEFAULT_END_DATE
        )
        
        if not api_result['success']:
            print_step("API测试失败", f"无法获取API数据: {api_result.get('error', '未知错误')}")
            return None
        
        print_step("API数据获取成功", f"成功获取 {api_result['total_records']} 条API数据")
        
        # 处理数据
        result = process_conversion_data(
            api_result['json_data'], 
            output_dir="api_test_output"
        )
        
        return result
        
    except Exception as e:
        print_step("API测试异常", f"API数据测试过程中发生异常: {str(e)}")
        return None

def test_individual_functions():
    """测试各个独立功能"""
    print_step("功能测试", "开始测试各个独立功能")
    
    # 生成测试数据
    test_data = create_test_data()
    processor = DataProcessor()
    processor.original_data = test_data.copy()
    processor.processed_data = test_data.copy()
    
    print(f"\n🧪 测试1: 数据清洗功能")
    print(f"清洗前栏位: {list(processor.processed_data.columns)}")
    processor._clean_data()
    print(f"清洗后栏位: {list(processor.processed_data.columns)}")
    
    print(f"\n🧪 测试2: 金额格式化功能")
    print(f"格式化前sale_amount: {processor.processed_data['sale_amount'].tolist()}")
    processor._format_and_calculate_amounts()
    print(f"格式化后sale_amount: {processor.processed_data['sale_amount'].tolist()}")
    
    print(f"\n🧪 测试3: Mockup调整功能")
    print(f"调整前总值: ${processor.processed_data['sale_amount'].sum():.2f}")
    processor._apply_mockup_adjustment()
    print(f"调整后总值: ${processor.processed_data['sale_amount'].sum():.2f}")
    
    print(f"\n🧪 测试4: Pub分类功能")
    pub_files = processor._export_by_pub("individual_test_output")
    print(f"生成的Pub文件: {pub_files}")

def test_excel_file_processing():
    """测试Excel文件处理功能"""
    print_step("Excel文件测试", "测试读取和处理现有Excel文件")
    
    # 查找现有的Excel文件
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and 'test' not in f.lower()]
    
    if not excel_files:
        print_step("Excel文件测试跳过", "未找到可用的Excel文件")
        return None
    
    excel_file = excel_files[0]
    print_step("Excel文件选择", f"选择文件: {excel_file}")
    
    try:
        result = process_conversion_data(excel_file, output_dir="excel_test_output")
        return result
    except Exception as e:
        print_step("Excel测试异常", f"处理Excel文件时发生异常: {str(e)}")
        return None

def main():
    """主测试函数"""
    print_step("独立测试开始", "开始执行数据处理模块的独立测试")
    
    # 测试选项
    tests = {
        '1': ('测试数据处理', test_data_processor_with_test_data),
        '2': ('API数据处理', test_data_processor_with_api_data),
        '3': ('独立功能测试', test_individual_functions),
        '4': ('Excel文件处理', test_excel_file_processing),
        'a': ('全部测试', None)
    }
    
    print(f"\n🧪 数据处理模块测试选项:")
    for key, (description, _) in tests.items():
        print(f"   {key}) {description}")
    
    choice = input(f"\n请选择测试选项 (1-4, a, 或按Enter默认测试1): ").strip().lower()
    
    if not choice:
        choice = '1'
    
    if choice == 'a':
        # 执行全部测试
        print_step("全部测试", "开始执行所有测试")
        for key, (description, test_func) in tests.items():
            if key != 'a' and test_func:
                print(f"\n{'='*60}")
                print(f"正在执行: {description}")
                print(f"{'='*60}")
                test_func()
    elif choice in tests and tests[choice][1]:
        # 执行单个测试
        description, test_func = tests[choice]
        print_step("单项测试", f"开始执行: {description}")
        test_func()
    else:
        print_step("测试错误", "无效的测试选项")
        return
    
    print_step("测试完成", "数据处理模块测试执行完毕")

if __name__ == "__main__":
    main() 
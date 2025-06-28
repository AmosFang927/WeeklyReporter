#!/usr/bin/env python3
"""
调试 ByteC 报表中转换数量显示不正确的问题
"""

import json
import pandas as pd
from modules.bytec_report_generator import ByteCReportGenerator
from utils.logger import print_step

def debug_conversion_issue():
    """调试转换数量问题"""
    print_step("调试开始", "开始调试 ByteC 报表转换数量问题")
    
    # 读取最新的JSON数据
    json_file = "output/conversions_20250626_222229.json"
    print_step("读取数据", f"读取JSON文件: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # 创建ByteC报表生成器
    generator = ByteCReportGenerator()
    
    # 第一步：数据预处理
    print_step("数据预处理", "开始数据预处理")
    df = generator._prepare_data(raw_data)
    print_step("预处理结果", f"预处理后数据量: {len(df)} 条记录")
    
    # 第二步：数据汇总
    print_step("数据汇总", "开始按 offer_name + aff_sub1 汇总")
    summary_data = generator._create_offer_summary(df)
    print_step("汇总结果", f"汇总后组合数: {len(summary_data)}")
    
    # 打印详细的汇总结果
    if len(summary_data) > 0:
        print_step("汇总详情", "各组合的转换数量:")
        for idx, row in summary_data.iterrows():
            offer_name = row['Offer Name']
            source = row['Source']
            conversions = row['Conversions']
            sales = row['Sales Amount']
            print_step("组合详情", f"  {offer_name} + {source}: {conversions} 转换, ${sales:,.2f} 销售额")
        
        total_conversions = summary_data['Conversions'].sum()
        total_sales = summary_data['Sales Amount'].sum()
        print_step("总计", f"总转换数: {total_conversions}, 总销售额: ${total_sales:,.2f}")
    
    # 验证原始数据的分组统计
    print_step("原始数据验证", "验证原始数据的分组统计")
    combo_counts = df.groupby(['offer_name', 'aff_sub1']).size().sort_values(ascending=False)
    print_step("原始分组统计", f"原始数据分组结果:")
    for (offer, source), count in combo_counts.items():
        print_step("原始组合", f"  {offer} + {source}: {count} 条记录")
    
    print_step("验证完成", f"原始数据总记录数: {combo_counts.sum()}")
    
    return summary_data

if __name__ == "__main__":
    debug_conversion_issue() 
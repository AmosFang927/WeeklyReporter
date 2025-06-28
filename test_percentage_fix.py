#!/usr/bin/env python3
"""
测试百分比格式化修复
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

def test_percentage_formatting():
    """测试百分比格式化"""
    
    # 创建测试数据
    test_data = pd.DataFrame({
        'Offer Name': ['TikTok Shop ID - CPS', 'Shopee ID (Media Buyers) - CPS'],
        'Sales Amount': [100.0, 200.0],
        'Partner': ['YueMeng', 'RAMPUP'],
        'Avg. Commission Rate': [2.38, 0.57],
        'Adv Commission Rate': [2.38, 0.57],
        'Pub Commission Rate': [1.0, 2.5],  # 这些应该显示为1.00%和2.50%，不是100%和250%
        'ByteC ROI': [138.0, 22.91]
    })
    
    print("原始数据:")
    print(test_data)
    
    # 创建Excel工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = "测试"
    
    # 写入数据
    for r in dataframe_to_rows(test_data, index=False, header=True):
        ws.append(r)
    
    # 应用百分比格式
    columns = list(test_data.columns)
    percentage_columns = []
    
    for i, column_name in enumerate(columns):
        excel_col_index = i + 1
        if column_name in ['Avg. Commission Rate', 'Adv Commission Rate', 'Pub Commission Rate', 'ByteC ROI']:
            percentage_columns.append(excel_col_index)
    
    print(f"\n百分比列索引: {percentage_columns}")
    
    # 应用百分比格式 (修复后的逻辑)
    total_rows = len(test_data) + 1  # 标题行 + 数据行
    
    for col_index in percentage_columns:
        for row in range(2, total_rows + 1):  # 从第2行开始，跳过标题行
            cell = ws.cell(row=row, column=col_index)
            if cell.value is not None:
                print(f"处理单元格 ({row}, {col_index}): 原值 = {cell.value}")
                try:
                    cell.number_format = '0.00%'
                    # 修复后的逻辑：所有百分比值都除以100
                    if isinstance(cell.value, (int, float)):
                        original_value = cell.value
                        cell.value = cell.value / 100.0
                        print(f"  转换后: {original_value} -> {cell.value} (显示为 {original_value}%)")
                except Exception as e:
                    print(f"  格式化错误: {e}")
    
    # 保存文件
    output_path = "test_percentage_format.xlsx"
    wb.save(output_path)
    print(f"\n测试文件已保存到: {output_path}")
    
    return output_path

if __name__ == "__main__":
    test_percentage_formatting() 
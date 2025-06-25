#!/usr/bin/env python3
"""
特殊字符处理测试脚本
专门测试Excel工作表名称和数据内容中特殊字符的处理
"""

import pandas as pd
import os
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import re

def clean_sheet_name(name):
    """
    清理Excel工作表名称，移除不支持的字符
    """
    import re
    
    if not name or not str(name).strip():
        return "Unknown"
    
    # 转换为字符串并去除前后空格
    clean_name = str(name).strip()
    
    # 移除或替换Excel不支持的字符
    # 替换路径分隔符
    clean_name = clean_name.replace('/', '_').replace('\\', '_')
    # 替换Excel特殊字符
    clean_name = clean_name.replace('[', '(').replace(']', ')')
    clean_name = clean_name.replace(':', '-').replace('*', '_')
    clean_name = clean_name.replace('?', '_').replace('\'', '')
    
    # 移除其他可能有问题的Unicode字符，保留基本字母、数字、空格和常见符号
    # 使用正则表达式保留安全字符
    clean_name = re.sub(r'[^\w\s\-\(\)\_\.]', '_', clean_name)
    
    # 移除多余的空格和下划线
    clean_name = re.sub(r'\s+', ' ', clean_name)  # 多个空格合并为一个
    clean_name = re.sub(r'_+', '_', clean_name)   # 多个下划线合并为一个
    clean_name = clean_name.strip('_').strip()    # 去除开头结尾的下划线和空格
    
    # 确保不以单引号开头或结尾
    clean_name = clean_name.strip('\'')
    
    # 限制长度为31个字符
    if len(clean_name) > 31:
        clean_name = clean_name[:28] + "..."
    
    # 如果清理后为空，使用默认名称
    if not clean_name:
        clean_name = "Unknown"
    
    return clean_name

def clean_row_data(row):
    """
    清理行数据中的特殊字符，确保Excel兼容性
    """
    import re
    
    cleaned_row = []
    for cell in row:
        if cell is None:
            cleaned_row.append(None)
        elif isinstance(cell, (int, float)):
            # 数字类型直接保留
            cleaned_row.append(cell)
        else:
            # 字符串类型需要清理
            cell_str = str(cell)
            
            # 移除可能导致Excel问题的控制字符和特殊Unicode字符
            # 保留基本的ASCII字符、常见Unicode字符
            cleaned_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', cell_str)
            
            # 移除可能有问题的Unicode字符（保留基本字母、数字、常见符号）
            # 这个正则表达式比较宽松，保留大部分字符但移除控制字符
            cleaned_str = re.sub(r'[^\x20-\x7E\u00A0-\u024F\u1E00-\u1EFF\u2000-\u206F\u20A0-\u20CF\u2100-\u214F]', '_', cleaned_str)
            
            # 移除开头的特殊字符（如不可见字符）
            cleaned_str = cleaned_str.strip()
            
            cleaned_row.append(cleaned_str)
    
    return cleaned_row

def test_problematic_string():
    """测试有问题的字符串"""
    problematic_string = "￼Áo thun nữ ôm body cổ cao 2CM tay ngắn vải thun đẹp mềmmại thoáng mát a95"
    
    print("🧪 测试特殊字符处理")
    print("=" * 60)
    print(f"原始字符串: {repr(problematic_string)}")
    print(f"原始字符串长度: {len(problematic_string)}")
    print(f"原始字符串显示: {problematic_string}")
    
    # 测试工作表名称清理
    clean_sheet = clean_sheet_name(problematic_string)
    print(f"\n清理后的工作表名称: {repr(clean_sheet)}")
    print(f"清理后的工作表名称显示: {clean_sheet}")
    print(f"清理后的工作表名称长度: {len(clean_sheet)}")
    
    # 测试行数据清理
    test_row = [1, problematic_string, 100.50, None, "normal text"]
    cleaned_row = clean_row_data(test_row)
    print(f"\n原始行数据: {test_row}")
    print(f"清理后行数据: {cleaned_row}")
    
    return clean_sheet, cleaned_row

def create_test_excel():
    """创建测试Excel文件"""
    print("\n📊 创建测试Excel文件")
    print("=" * 60)
    
    # 测试数据
    problematic_string = "￼Áo thun nữ ôm body cổ cao 2CM tay ngắn vải thun đẹp mềmmại thoáng mát a95"
    
    # 创建测试DataFrame
    test_data = {
        'id': [1, 2, 3],
        'product_name': [
            problematic_string,
            "Normal Product Name",
            "Another ★特殊★ Product"
        ],
        'price': [100.50, 200.75, 300.00],
        'description': [
            "This has special chars: ★♪♫♬",
            "Normal description",
            problematic_string
        ]
    }
    
    df = pd.DataFrame(test_data)
    print(f"测试数据:")
    print(df)
    
    try:
        # 创建工作簿
        wb = Workbook()
        wb.remove(wb.active)
        
        # 清理工作表名称
        clean_sheet = clean_sheet_name(problematic_string)
        ws = wb.create_sheet(title=clean_sheet)
        
        print(f"\n✅ 成功创建工作表: '{clean_sheet}'")
        
        # 写入数据（清理特殊字符）
        for r in dataframe_to_rows(df, index=False, header=True):
            cleaned_row = clean_row_data(r)
            ws.append(cleaned_row)
        
        # 保存文件
        output_file = "test_special_chars.xlsx"
        wb.save(output_file)
        
        print(f"✅ 成功保存Excel文件: {output_file}")
        
        # 检查文件大小
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"📁 文件大小: {file_size:,} bytes")
            
            # 验证文件可以正常读取
            try:
                test_df = pd.read_excel(output_file)
                print(f"✅ 文件验证成功，读取到 {len(test_df)} 行数据")
                print("验证数据:")
                print(test_df)
                return True
            except Exception as e:
                print(f"❌ 文件验证失败: {e}")
                return False
        else:
            print(f"❌ 文件未生成")
            return False
            
    except Exception as e:
        print(f"❌ Excel创建失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def analyze_character_codes():
    """分析问题字符串中的字符编码"""
    problematic_string = "￼Áo thun nữ ôm body cổ cao 2CM tay ngắn vải thun đẹp mềmmại thoáng mát a95"
    
    print("\n🔍 字符编码分析")
    print("=" * 60)
    
    for i, char in enumerate(problematic_string):
        code_point = ord(char)
        print(f"位置 {i:2d}: '{char}' -> U+{code_point:04X} ({code_point})")
        
        # 检查是否是控制字符
        if code_point < 32 or (127 <= code_point <= 159):
            print(f"         ⚠️ 控制字符!")
        elif code_point == 65532:  # U+FFFC 对象替换字符
            print(f"         ⚠️ 对象替换字符!")
        elif code_point > 65535:
            print(f"         ⚠️ 超出基本多语言平面!")

def main():
    """主测试函数"""
    print("🚀 特殊字符处理测试")
    print("=" * 80)
    
    # 1. 分析字符编码
    analyze_character_codes()
    
    # 2. 测试字符串清理
    clean_sheet, cleaned_row = test_problematic_string()
    
    # 3. 创建测试Excel文件
    success = create_test_excel()
    
    print("\n📋 测试总结")
    print("=" * 60)
    if success:
        print("✅ 所有测试通过！特殊字符处理正常工作。")
    else:
        print("❌ 测试失败！需要进一步调试特殊字符处理。")
    
    return success

if __name__ == "__main__":
    main() 
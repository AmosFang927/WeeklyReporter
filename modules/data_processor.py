#!/usr/bin/env python3
"""
数据清洗与调整模块
负责处理从Involve Asia获取的原始数据，包括数据清洗、格式化、分类导出等功能
"""

import pandas as pd
import os
from datetime import datetime
from utils.logger import print_step
import config
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import NamedStyle

class DataProcessor:
    """数据处理器类"""
    
    def __init__(self):
        self.original_data = None
        self.processed_data = None
        self.total_sale_amount = 0
        self.pub_summary = {}
        self.report_date = None
    
    def process_data(self, data_source, output_dir=None, report_date=None):
        """
        完整的数据处理流程
        
        Args:
            data_source: 数据源（DataFrame、Excel文件路径或JSON数据）
            output_dir: 输出目录，默认使用config.OUTPUT_DIR
            report_date: 报告日期，用于文件名，默认使用当前日期
        
        Returns:
            dict: 处理结果摘要
        """
        print_step("数据处理开始", "开始执行完整的数据清洗与调整流程")
        
        if output_dir is None:
            output_dir = config.OUTPUT_DIR
        
        # 设置报告日期
        if report_date:
            self.report_date = report_date
        
        # 步骤1: 加载数据
        self._load_data(data_source)
        
        # 步骤2: 数据清洗
        self._clean_data()
        
        # 步骤3: 格式化金额并统计
        self._format_and_calculate_amounts()
        
        # 步骤4: 调整金额（Mockup）
        self._apply_mockup_adjustment()
        
        # 步骤5: 按Pub分类导出
        pub_files = self._export_by_pub(output_dir)
        
        # 步骤6: 生成处理摘要
        result = self._generate_summary(pub_files, output_dir)
        
        print_step("数据处理完成", "所有数据处理步骤执行完毕")
        return result
    
    def _load_data(self, data_source):
        """加载数据源"""
        print_step("数据加载", "正在加载原始数据...")
        
        if isinstance(data_source, pd.DataFrame):
            self.original_data = data_source.copy()
        elif isinstance(data_source, str) and data_source.endswith('.xlsx'):
            self.original_data = pd.read_excel(data_source)
        elif isinstance(data_source, str) and data_source.endswith('.json'):
            # 处理JSON格式数据
            import json
            with open(data_source, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            if 'data' in json_data and 'data' in json_data['data']:
                conversion_records = json_data['data']['data']
                self.original_data = pd.DataFrame(conversion_records)
            else:
                raise ValueError("JSON数据格式不正确")
        elif isinstance(data_source, dict):
            # 直接处理字典格式的JSON数据
            if 'data' in data_source and 'data' in data_source['data']:
                conversion_records = data_source['data']['data']
                self.original_data = pd.DataFrame(conversion_records)
            else:
                raise ValueError("JSON数据格式不正确")
        else:
            raise ValueError(f"不支持的数据源格式: {type(data_source)}")
        
        print_step("数据加载完成", f"成功加载 {len(self.original_data)} 条记录，{len(self.original_data.columns)} 个字段")
        
        # 复制到处理数据
        self.processed_data = self.original_data.copy()
    
    def _clean_data(self):
        """数据清洗 - 移除不需要的栏位"""
        print_step("数据清洗", f"正在移除不需要的栏位: {config.REMOVE_COLUMNS}")
        
        # 检查哪些栏位实际存在
        existing_columns = [col for col in config.REMOVE_COLUMNS if col in self.processed_data.columns]
        missing_columns = [col for col in config.REMOVE_COLUMNS if col not in self.processed_data.columns]
        
        if existing_columns:
            self.processed_data = self.processed_data.drop(columns=existing_columns)
            print_step("栏位移除", f"成功移除栏位: {existing_columns}")
        
        if missing_columns:
            print_step("栏位警告", f"以下栏位不存在，跳过移除: {missing_columns}")
        
        print_step("清洗完成", f"清洗后剩余 {len(self.processed_data.columns)} 个字段")
    
    def _format_and_calculate_amounts(self):
        """格式化金额并计算总值"""
        print_step("金额处理", "正在格式化sale_amount栏位并计算总值...")
        
        if 'sale_amount' not in self.processed_data.columns:
            print_step("金额处理警告", "sale_amount栏位不存在，跳过金额处理")
            return
        
        # 转换为数值类型并处理异常值
        self.processed_data['sale_amount'] = pd.to_numeric(
            self.processed_data['sale_amount'], 
            errors='coerce'
        ).fillna(0)
        
        # 格式化为两位小数
        self.processed_data['sale_amount'] = self.processed_data['sale_amount'].round(2)
        
        # 计算总值
        self.total_sale_amount = self.processed_data['sale_amount'].sum()
        
        print_step("金额统计", f"sale_amount总值: ${self.total_sale_amount:,.2f} USD")
        print_step("金额格式化完成", f"所有金额已格式化为美金格式（小数点后两位）")
    
    def _apply_mockup_adjustment(self):
        """应用Mockup调整倍数"""
        print_step("金额调整", f"正在应用Mockup调整倍数: {config.MOCKUP_MULTIPLIER * 100}%")
        
        if 'sale_amount' not in self.processed_data.columns:
            print_step("金额调整警告", "sale_amount栏位不存在，跳过金额调整")
            return
        
        # 保存调整前的总值
        original_total = self.processed_data['sale_amount'].sum()
        
        # 应用调整倍数
        self.processed_data['sale_amount'] = (
            self.processed_data['sale_amount'] * config.MOCKUP_MULTIPLIER
        ).round(2)
        
        # 计算调整后的总值
        adjusted_total = self.processed_data['sale_amount'].sum()
        
        print_step("金额调整完成", f"调整前总值: ${original_total:,.2f} → 调整后总值: ${adjusted_total:,.2f}")
        
        # 更新总值
        self.total_sale_amount = adjusted_total
    
    def _export_by_pub(self, output_dir):
        """按Pub分类导出Excel文件"""
        print_step("Pub分类导出", "正在按aff_sub1 (Pub) 字段分类导出...")
        
        if 'aff_sub1' not in self.processed_data.columns:
            print_step("分类导出警告", "aff_sub1 (Pub) 栏位不存在，跳过分类导出")
            return []
        
        # 获取所有唯一的Pub值
        unique_pubs = self.processed_data['aff_sub1'].dropna().unique()
        print_step("Pub统计", f"发现 {len(unique_pubs)} 个不同的Pub: {list(unique_pubs)}")
        
        pub_files = []
        # 使用查询的日期作为文件名日期，如果没有则使用当前日期
        report_date = getattr(self, 'report_date', datetime.now().strftime("%Y-%m-%d"))
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        for pub in unique_pubs:
            # 过滤该Pub的数据
            pub_data = self.processed_data[self.processed_data['aff_sub1'] == pub].copy()
            
            # 生成文件名
            safe_pub_name = str(pub).replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_')
            filename = f"{safe_pub_name}_ConversionReport_{report_date}.xlsx"
            filepath = os.path.join(output_dir, filename)
            
            # 导出Excel并设置货币格式
            self._export_excel_with_currency_format(pub_data, filepath)
            
            # 统计信息
            pub_total = pub_data['sale_amount'].sum() if 'sale_amount' in pub_data.columns else 0
            self.pub_summary[pub] = {
                'records': len(pub_data),
                'total_amount': pub_total,
                'amount_formatted': f"${pub_total:,.2f}",
                'filename': filename
            }
            
            pub_files.append(filepath)
            
            print_step("Pub导出", f"Pub '{pub}': {len(pub_data)} 条记录，总金额 ${pub_total:,.2f} → {filename}")
        
        print_step("分类导出完成", f"成功生成 {len(pub_files)} 个Pub分类文件")
        return pub_files
    
    def _generate_summary(self, pub_files, output_dir):
        """生成处理结果摘要"""
        print_step("生成摘要", "正在生成数据处理结果摘要...")
        
        summary = {
            'success': True,
            'original_records': len(self.original_data) if self.original_data is not None else 0,
            'processed_records': len(self.processed_data) if self.processed_data is not None else 0,
            'total_sale_amount': self.total_sale_amount,
            'mockup_multiplier': config.MOCKUP_MULTIPLIER,
            'removed_columns': config.REMOVE_COLUMNS,
            'pub_count': len(self.pub_summary),
            'pub_files': pub_files,
            'pub_summary': self.pub_summary,
            'output_directory': output_dir
        }
        
        return summary
    
    def _export_excel_with_currency_format(self, data, filepath):
        """
        导出Excel并为sale_amount栏位设置美元货币格式
        
        Args:
            data: 要导出的DataFrame
            filepath: 输出文件路径
        """
        # 创建工作簿和工作表
        wb = Workbook()
        ws = wb.active
        ws.title = "Conversion Report"
        
        # 写入数据（包含标题行）
        for r in dataframe_to_rows(data, index=False, header=True):
            ws.append(r)
        
        # 查找sale_amount列的索引
        sale_amount_col = None
        if 'sale_amount' in data.columns:
            sale_amount_col = data.columns.get_loc('sale_amount') + 1  # Excel列索引从1开始
        
        if sale_amount_col:
            # 创建货币格式样式
            currency_style = NamedStyle(name="currency_usd")
            currency_style.number_format = '"$"#,##0.00'
            
            # 应用货币格式到sale_amount列（跳过标题行）
            for row in range(2, len(data) + 2):  # 从第2行开始（第1行是标题）
                cell = ws.cell(row=row, column=sale_amount_col)
                cell.number_format = '"$"#,##0.00'
        
        # 保存文件
        wb.save(filepath)
        print_step("货币格式", f"已为 {filepath} 设置美元货币格式")
    
    def print_detailed_summary(self, summary):
        """打印详细的处理摘要"""
        print_step("处理摘要", "数据处理完成，详细结果如下:")
        
        print(f"📊 数据处理统计:")
        print(f"   - 原始记录数: {summary['original_records']:,}")
        print(f"   - 处理后记录数: {summary['processed_records']:,}")
        print(f"   - 移除栏位: {', '.join(summary['removed_columns'])}")
        print(f"   - Mockup调整倍数: {summary['mockup_multiplier'] * 100}%")
        
        print(f"💰 金额统计:")
        print(f"   - 调整后总金额: ${summary['total_sale_amount']:,.2f} USD")
        
        print(f"📂 Pub分类导出:")
        print(f"   - 不同Pub数量: {summary['pub_count']}")
        print(f"   - 生成文件数量: {len(summary['pub_files'])}")
        print(f"   - 输出目录: {summary['output_directory']}")
        
        if summary['pub_summary']:
            print(f"📋 各Pub详细信息:")
            for pub, info in summary['pub_summary'].items():
                print(f"   - {pub}: {info['records']} 条记录, ${info['total_amount']:,.2f}, 文件: {info['filename']}")

# 便捷函数
def process_conversion_data(data_source, output_dir=None):
    """
    便捷的数据处理函数
    
    Args:
        data_source: 数据源
        output_dir: 输出目录
    
    Returns:
        dict: 处理结果摘要
    """
    processor = DataProcessor()
    summary = processor.process_data(data_source, output_dir)
    processor.print_detailed_summary(summary)
    return summary 
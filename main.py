#!/usr/bin/env python3
"""
WeeklyReporter 主程序
集成Involve Asia API数据获取和Excel转换功能
"""

import sys
import os
import time
import argparse
from datetime import datetime
from modules.involve_asia_api import InvolveAsiaAPI
from modules.json_to_excel import JSONToExcelConverter
from modules.data_processor import DataProcessor
from modules.feishu_uploader import FeishuUploader
from modules.email_sender import EmailSender
from modules.scheduler import ReportScheduler
from modules.bytec_report_generator import ByteCReportGenerator
from utils.logger import print_step, log_error
import config

class WeeklyReporter:
    """周报生成器主类"""
    
    def __init__(self, api_secret=None, api_key=None, global_email_disabled=False):
        self.api_client = InvolveAsiaAPI(api_secret=api_secret, api_key=api_key)
        self.converter = JSONToExcelConverter()
        self.data_processor = DataProcessor()
        self.feishu_uploader = FeishuUploader()
        self.email_sender = EmailSender(global_email_disabled=global_email_disabled)
        self.bytec_generator = ByteCReportGenerator(api_secret=api_secret)
        self.scheduler = None
    
    def get_multi_api_data(self, api_list, start_date, end_date, max_records=None):
        """
        从多个API获取数据并合并
        
        Args:
            api_list: API配置列表 [{'name': 'LisaidByteC', 'secret': '...', 'key': '...'}, ...]
            start_date: 开始日期
            end_date: 结束日期
            max_records: 最大记录数限制
            
        Returns:
            dict: 合并后的数据，包含来源API标记
        """
        print_step("多API模式", f"开始从 {len(api_list)} 个API获取数据")
        
        all_conversions = []
        api_errors = []
        api_success_count = 0
        total_records = 0
        
        for i, api_config in enumerate(api_list, 1):
            api_name = api_config['name']
            api_secret = api_config['secret']
            api_key = api_config['key']
            
            print()
            print("=" * 60)
            print(f"🚀 API {i}/{len(api_list)}: {api_name}")
            print("=" * 60)
            print_step(f"API-{api_name}", f"开始获取 {api_name} 数据...")
            
            # 强制刷新输出
            import sys
            sys.stdout.flush()
            
            try:
                # 创建临时API客户端
                temp_client = InvolveAsiaAPI(api_secret=api_secret, api_key=api_key)
                
                # 临时设置记录限制
                original_limit = config.MAX_RECORDS_LIMIT
                if max_records is not None:
                    config.MAX_RECORDS_LIMIT = max_records
                
                # 认证
                print_step(f"API-{api_name}", f"开始认证...")
                sys.stdout.flush()
                if not temp_client.authenticate():
                    error_msg = f"API认证失败: {api_name}"
                    api_errors.append(error_msg)
                    print_step(f"API-{api_name}", f"❌ {error_msg}")
                    continue
                print_step(f"API-{api_name}", f"认证成功，开始获取数据...")
                sys.stdout.flush()
                
                # 获取数据
                print_step(f"API-{api_name}", f"调用get_conversions方法...")
                sys.stdout.flush()
                api_data = temp_client.get_conversions(start_date, end_date, api_name=api_name)
                print_step(f"API-{api_name}", f"get_conversions方法执行完成")
                sys.stdout.flush()
                
                # 恢复原始限制
                config.MAX_RECORDS_LIMIT = original_limit
                
                if not api_data or 'data' not in api_data:
                    error_msg = f"数据获取失败: {api_name}"
                    api_errors.append(error_msg)
                    print_step(f"API-{api_name}", f"❌ {error_msg}")
                    continue
                
                # 获取转换记录 - 修复数据路径
                if 'data' in api_data and 'data' in api_data['data']:
                    # 标准API返回结构: {'data': {'data': [conversions...]}}
                    conversions = api_data['data']['data']
                elif 'data' in api_data and 'conversions' in api_data['data']:
                    # 备用结构: {'data': {'conversions': [...]}}
                    conversions = api_data['data']['conversions']
                else:
                    # 其他可能结构
                    conversions = api_data.get('data', [])
                
                record_count = len(conversions) if isinstance(conversions, list) else 0
                
                # 检查是否没有数据 - 这是正常情况，不应该算作错误
                if record_count == 0:
                    print_step(f"API-{api_name}", f"⚠️ {api_name} 在指定日期范围内没有数据，跳过该API")
                    print("=" * 60)
                    print(f"⚠️ API {i}/{len(api_list)} ({api_name}) 无数据但继续执行")
                    print("=" * 60)
                    # 将这个API标记为成功但无数据
                    api_success_count += 1
                    continue
                
                # 为每条记录添加API来源标记（只有在需要ByteC报表时才添加）
                should_add_api_fields = self._should_add_api_source_fields()
                if should_add_api_fields:
                    for conversion in conversions:
                        conversion['api_source'] = api_name
                        conversion['api_platform'] = config.get_platform_from_api_secret(api_secret)
                    print_step(f"API-{api_name}", f"为ByteC报表添加API来源标记: {api_name}")
                else:
                    print_step(f"API-{api_name}", f"非ByteC报表模式，跳过API来源标记")
                
                all_conversions.extend(conversions)
                total_records += record_count
                api_success_count += 1
                
                print_step(f"API-{api_name}", f"✅ 成功获取 {record_count:,} 条记录")
                print("=" * 60)
                print(f"✅ API {i}/{len(api_list)} ({api_name}) 完成")
                print("=" * 60)
                
            except Exception as e:
                error_msg = f"API异常: {api_name} - {str(e)}"
                api_errors.append(error_msg)
                print_step(f"API-{api_name}", f"❌ {error_msg}")
                continue
        
        # 检查是否有任何API成功获取了数据
        if api_success_count == 0:
            # 所有API都失败了，这是真正的错误
            error_summary = f"多API获取失败: 所有 {len(api_list)} 个API都失败"
            print_step("多API错误", f"❌ {error_summary}")
            
            # 列出所有错误
            for error in api_errors:
                print_step("API错误详情", f"   • {error}")
            
            raise Exception(f"{error_summary}。错误详情: {'; '.join(api_errors)}")
        elif api_success_count != len(api_list):
            # 部分API失败或没有数据，但至少有一个API成功，这是可以接受的
            failed_count = len(api_list) - api_success_count
            if api_errors:
                print_step("多API警告", f"⚠️ 部分API处理异常: {failed_count}/{len(api_list)} 个API失败或无数据")
                # 列出所有错误
                for error in api_errors:
                    print_step("API警告详情", f"   • {error}")
            else:
                print_step("多API信息", f"ℹ️ 部分API无数据: {failed_count}/{len(api_list)} 个API在该日期范围内没有数据")
        
        # 如果没有获取到任何数据记录，也算是失败
        if total_records == 0:
            print_step("多API错误", f"❌ 所有API都没有返回数据")
            raise Exception("所有API都没有返回数据，请检查日期范围和数据源")
        
        # 构造API统计信息
        should_add_api_fields = self._should_add_api_source_fields()
        if should_add_api_fields:
            # 纯ByteC模式：基于api_source字段进行统计
            api_breakdown = {api['name']: len([c for c in all_conversions if c.get('api_source') == api['name']]) 
                           for api in api_list}
        else:
            # 非纯ByteC模式：基于API调用顺序进行估算（因为没有api_source字段）
            api_breakdown = {}
            current_index = 0
            for i, api_config in enumerate(api_list):
                # 简单估算：假设每个API获取的记录数相对均匀
                if i < len(api_list) - 1:
                    # 不是最后一个API，计算平均分配
                    api_records = total_records // len(api_list)
                else:
                    # 最后一个API，包含剩余的所有记录
                    api_records = total_records - current_index
                api_breakdown[api_config['name']] = api_records
                current_index += api_records
        
        # 构造合并后的数据结构
        merged_data = {
            'data': {
                'conversions': all_conversions,
                'current_page_count': total_records,
                'total_count': total_records,
                'api_sources': [api['name'] for api in api_list],
                'merge_info': {
                    'total_apis': len(api_list),
                    'successful_apis': api_success_count,
                    'total_records': total_records,
                    'api_breakdown': api_breakdown,
                    'has_api_source_fields': should_add_api_fields
                }
            },
            'success': True,
            'message': f"成功合并 {api_success_count} 个API的数据"
        }
        
        print_step("多API完成", f"✅ 成功合并 {total_records:,} 条记录 (来自 {api_success_count} 个API)")
        print_step("API数据分布", f"数据分布: {merged_data['data']['merge_info']['api_breakdown']}")
        
        return merged_data
    
    def _is_bytec_processing(self):
        """
        判断当前是否在处理ByteC Partner
        
        Returns:
            bool: 如果当前target_partner是ByteC则返回True，否则返回False
        """
        # 从config中获取当前的TARGET_PARTNER设置
        target_partner = getattr(config, 'TARGET_PARTNER', None)
        
        if target_partner is None:
            return False
        
        # 处理单个Partner和多个Partner的情况
        if isinstance(target_partner, str):
            return target_partner == "ByteC"
        elif isinstance(target_partner, list):
            return "ByteC" in target_partner
        
        return False
    
    def _should_process_bytec(self, target_partner):
        """
        判断是否需要处理ByteC Partner
        
        Args:
            target_partner: 目标Partner，可以是字符串、列表或None
            
        Returns:
            bool: 如果需要处理ByteC则返回True，否则返回False
        """
        if target_partner is None:
            # None表示处理所有Partner，包括ByteC
            return True
        
        # 处理单个Partner和多个Partner的情况
        if isinstance(target_partner, str):
            return target_partner == "ByteC"
        elif isinstance(target_partner, list):
            return "ByteC" in target_partner
        
        return False
    
    def _should_add_api_source_fields(self):
        """
        判断是否需要在数据中添加api_source和api_platform字段
        这些字段只有在ByteC报表中才需要，标准Partner报表不需要
        
        Returns:
            bool: 如果需要添加API字段则返回True，否则返回False
        """
        # 从config中获取当前的TARGET_PARTNER设置
        target_partner = getattr(config, 'TARGET_PARTNER', None)
        
        if target_partner is None:
            return False
        
        # 只有在纯ByteC模式下才添加API字段
        # 多Partner模式下，即使包含ByteC，也不在原始数据中添加这些字段
        # ByteC报表生成器会自己处理API信息
        if isinstance(target_partner, str):
            return target_partner == "ByteC"
        else:
            # 多Partner模式下不添加API字段
            return False
    
    def run_full_workflow(self, start_date=None, end_date=None, output_filename=None, save_json=False, upload_to_feishu=False, send_email=False, send_self_email=False, max_records=None, target_partner=None):
        """
        运行完整的工作流程
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            output_filename: Excel输出文件名
            save_json: 是否保存中间JSON文件
            upload_to_feishu: 是否上传到飞书
            send_email: 是否发送邮件
            send_self_email: 是否发送邮件到默认收件人群组
            max_records: 最大记录数限制
            target_partner: 指定要处理的Partner
        
        Returns:
            dict: 包含生成文件路径的结果
        """
        print_step("工作流开始", "开始执行WeeklyReporter完整工作流")
        
        # 应用配置参数
        if max_records is not None:
            config.MAX_RECORDS_LIMIT = max_records
            print_step("数据限制", f"设置最大记录数限制: {max_records}")
        
        if target_partner is not None:
            config.TARGET_PARTNER = target_partner
            print_step("Partner过滤", f"设置目标Partner: {target_partner}")
        
        result = {
            'success': False,
            'json_file': None,
            'excel_file': None,
            'error': None
        }
        
        try:
            # 步骤1&2: 智能判断是否需要多API模式
            use_multi_api_mode = False
            required_apis = []
            
            # 根据target_partner决定API需求
            if target_partner:
                # 处理单个或多个Partner的情况
                if isinstance(target_partner, list):
                    partner_list = target_partner
                else:
                    partner_list = [target_partner]
            else:
                # target_partner为None表示处理所有Partner
                partner_list = list(config.PARTNER_SOURCES_MAPPING.keys())
                print_step("Partner展开", f"target_partner为None，展开为所有Partner: {', '.join(partner_list)}")
            
            # 检查是否需要多API
            needs_multi, apis = config.needs_multi_api_for_partners(partner_list)
            if needs_multi:
                use_multi_api_mode = True
                required_apis = apis
                print_step("多API模式", f"检测到Partner({', '.join(partner_list)})需要多API: {', '.join(apis)}")
            
            if use_multi_api_mode:
                print_step("API准备", f"将从 {len(required_apis)} 个API获取数据: {', '.join(required_apis)}")
                
                # 构造API配置列表
                api_configs = []
                for api_name in required_apis:
                    api_config = get_api_configs().get(api_name)
                    if not api_config:
                        result['error'] = f"API配置错误：未找到 {api_name} 的配置信息"
                        return result
                    api_configs.append({
                        'name': api_name,
                        'secret': api_config['api_secret'],
                        'key': api_config['api_key']
                    })
                
                # 确定日期范围
                actual_start_date = start_date
                actual_end_date = end_date
                if not actual_start_date or not actual_end_date:
                    actual_start_date, actual_end_date = config.get_default_date_range()
                
                # 从多个API获取数据
                conversion_data = self.get_multi_api_data(
                    api_configs, 
                    actual_start_date, 
                    actual_end_date, 
                    max_records
                )
                
            else:
                # 标准单API模式
                # 步骤1: API认证
                if not self.api_client.authenticate():
                    result['error'] = "API认证失败"
                    return result
                
                # 步骤2: 获取数据
                if start_date and end_date:
                    conversion_data = self.api_client.get_conversions(start_date, end_date)
                else:
                    conversion_data = self.api_client.get_conversions_default_range()
            
            if not conversion_data:
                result['error'] = "数据获取失败"
                return result
            
            # 步骤3: 保存JSON（可选）
            if save_json:
                if use_multi_api_mode:
                    # 多API模式：使用自定义保存方法
                    import json
                    import os
                    from datetime import datetime
                    
                    # 生成文件名
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    json_filename = f"conversions_{timestamp}.json"
                    json_filepath = os.path.join(config.OUTPUT_DIR, json_filename)
                    
                    # 保存多API格式的数据
                    with open(json_filepath, 'w', encoding='utf-8') as f:
                        json.dump(conversion_data, f, indent=2, ensure_ascii=False)
                    
                    result['json_file'] = json_filepath
                    print_step("JSON保存", f"✅ 已保存多API格式JSON: {json_filepath}")
                else:
                    # 标准单API模式：使用原有方法
                    json_file = self.api_client.save_to_json(conversion_data)
                    result['json_file'] = json_file
            
            # 步骤4: 检查是否为 ByteC 特殊报表
            # 获取实际的日期范围
            actual_start_date = start_date
            actual_end_date = end_date
            if not actual_start_date or not actual_end_date:
                # 如果没有指定日期，使用默认日期范围
                actual_start_date, actual_end_date = config.get_default_date_range()
            
            # 检查是否需要处理ByteC（支持单个和多个Partner模式）
            should_process_bytec = self._should_process_bytec(target_partner)
            is_bytec_only = target_partner == "ByteC"
            
            if is_bytec_only:
                # 纯ByteC模式：只生成ByteC报表
                print_step("ByteC特殊报表", "生成 ByteC 公司专用汇总报表")
                # 生成 ByteC 报表
                bytec_file = self.bytec_generator.generate_bytec_report(
                    conversion_data, 
                    actual_start_date, 
                    actual_end_date
                )
                result['excel_file'] = bytec_file
                result['bytec_file'] = bytec_file
                
                # 为 ByteC 准备处理摘要
                result['processing_summary'] = {
                    'total_records': conversion_data['data']['current_page_count'],
                    'total_sale_amount': 0,  # 将在后续计算
                    'adjusted_total_amount_formatted': '$0.00',  # 将在后续计算
                    'partner_summary': {'ByteC': {'records': conversion_data['data']['current_page_count'], 'amount_formatted': '$0.00'}},
                    'partner_count': 1
                }
                result['pub_files'] = [bytec_file]  # 为了兼容性
            else:
                # 标准数据处理与清洗
                print_step("数据处理", "开始执行数据清洗与Pub分类导出")
                
                # 传递完整的日期范围信息
                processor_result = self.data_processor.process_data(
                    conversion_data, 
                    start_date=actual_start_date, 
                    end_date=actual_end_date
                )
                result['processing_summary'] = processor_result
                result['pub_files'] = processor_result.get('pub_files', [])
                
                # 如果需要处理ByteC，在标准处理后生成ByteC报表
                if should_process_bytec:
                    print_step("ByteC额外报表", "在标准处理基础上生成 ByteC 公司专用汇总报表")
                    bytec_file = self.bytec_generator.generate_bytec_report(
                        conversion_data, 
                        actual_start_date, 
                        actual_end_date
                    )
                    result['bytec_file'] = bytec_file
                    # 将ByteC文件添加到pub_files列表中
                    if result['pub_files'] is None:
                        result['pub_files'] = []
                    result['pub_files'].append(bytec_file)
                    
                    # 在处理摘要中添加ByteC信息
                    if 'partner_summary' not in result['processing_summary']:
                        result['processing_summary']['partner_summary'] = {}
                    result['processing_summary']['partner_summary']['ByteC'] = {
                        'records': conversion_data['data']['current_page_count'], 
                        'amount_formatted': '$0.00'
                    }
            
            # 步骤5: 生成主Excel文件（仅适用于标准处理流程）
            if not is_bytec_only:  # 只有在非纯ByteC模式下才生成主Excel文件
                print_step("主Excel生成", "使用清洗后的数据生成主Excel文件")
                # 确定输出文件名，如果没有指定则使用日期范围
                if not output_filename:
                    output_filename = f"AllPartners_ConversionReport_{actual_start_date}_to_{actual_end_date}.xlsx"
                
                # 使用清洗后的数据生成主Excel文件
                cleaned_data = self.data_processor.processed_data
                excel_file = self._generate_main_excel_from_cleaned_data(cleaned_data, output_filename)
                result['excel_file'] = excel_file
            
            # 步骤6: 飞书上传（可选）
            if upload_to_feishu:
                print_step("飞书上传", "开始上传所有Excel文件到飞书")
                
                # 收集所有需要上传的文件
                upload_files = [result['excel_file']]  # 主Excel文件
                if result.get('pub_files'):
                    upload_files.extend(result['pub_files'])  # Pub分类文件
                
                # 执行上传
                upload_result = self.feishu_uploader.upload_files(upload_files)
                result['feishu_upload'] = upload_result
                
                if upload_result['success']:
                    print_step("飞书上传完成", f"✅ 成功上传 {upload_result['success_count']} 个文件到飞书")
                else:
                    print_step("飞书上传部分失败", f"⚠️ 上传完成，成功 {upload_result['success_count']} 个，失败 {upload_result['failed_count']} 个")
            
            # 步骤7: 邮件发送（可选）
            if send_email:
                print_step("邮件发送", "开始按Partner分别发送转换报告邮件")
                
                # 准备Partner汇总数据用于邮件发送
                partner_summary_for_email = self._prepare_partner_summary_for_email(result)
                
                # 按Partner分别发送邮件
                email_result = self.email_sender.send_partner_reports(
                    partner_summary_for_email, 
                    result.get('feishu_upload'),
                    actual_end_date,  # 传递报告日期（使用结束日期）
                    actual_start_date  # 传递开始日期
                )
                result['email_result'] = email_result
                
                if email_result['success']:
                    print_step("邮件发送完成", f"✅ 已成功发送 {email_result['total_sent']} 个Partner报告邮件")
                else:
                    print_step("邮件发送失败", f"⚠️ 邮件发送完成：成功 {email_result['total_sent']} 个，失败 {email_result['total_failed']} 个")
            
            # 步骤7.5: 默认收件人邮件发送（可选）
            if send_self_email:
                print_step("默认邮件发送", "开始发送邮件到默认收件人群组")
                
                # 发送到默认收件人
                self_email_result = self.send_self_email(result, actual_start_date, actual_end_date)
                result['self_email_result'] = self_email_result
                
                if self_email_result['success']:
                    print_step("默认邮件完成", f"✅ 已成功发送 {self_email_result['total_sent']} 个Partner专用邮件到默认收件人")
                else:
                    print_step("默认邮件失败", f"❌ 发送到默认收件人失败：成功 {self_email_result.get('total_sent', 0)} 个，失败 {self_email_result.get('total_failed', 0)} 个")
            
            # 步骤8: 完成
            result['success'] = True
            print_step("工作流完成", "WeeklyReporter工作流执行成功")
            
            # 输出最终结果
            self._print_final_result(result)
            
            return result
            
        except Exception as e:
            error_msg = f"工作流执行失败: {str(e)}"
            print_step("工作流失败", error_msg)
            log_error(error_msg)
            result['error'] = error_msg
            return result
        
    def run_feishu_upload_only(self, file_patterns=None):
        """
        只执行飞书上传功能
        
        Args:
            file_patterns: 文件路径模式，如果为None则上传output目录下所有xlsx文件
        
        Returns:
            dict: 上传结果
        """
        print_step("飞书上传开始", "开始独立的飞书上传任务")
        
        if file_patterns:
            file_paths = file_patterns if isinstance(file_patterns, list) else [file_patterns]
        else:
            # 自动找到output目录下的所有xlsx文件
            import glob
            file_paths = glob.glob(os.path.join(config.OUTPUT_DIR, "*.xlsx"))
            
            if not file_paths:
                print_step("文件查找", "❌ 在output目录下没有找到Excel文件")
                return {'success': False, 'error': '没有找到文件'}
            
            print_step("文件查找", f"在output目录下找到 {len(file_paths)} 个Excel文件")
        
        # 执行上传
        upload_result = self.feishu_uploader.upload_files(file_paths)
        return upload_result
    
    def _generate_main_excel_from_cleaned_data(self, cleaned_data, output_filename):
        """
        使用清洗后的数据生成主Excel文件
        
        Args:
            cleaned_data: 经过清洗处理的DataFrame
            output_filename: 输出文件名
        
        Returns:
            str: 生成的Excel文件路径
        """
        from openpyxl import Workbook
        from openpyxl.utils.dataframe import dataframe_to_rows
        import os
        
        # 生成完整路径
        output_path = os.path.join(config.OUTPUT_DIR, output_filename)
        
        # 创建工作簿和工作表
        wb = Workbook()
        ws = wb.active
        ws.title = config.EXCEL_SHEET_NAME
        
        # 写入数据（包含标题行），清理特殊字符
        for r in dataframe_to_rows(cleaned_data, index=False, header=True):
            # 清理行中的特殊字符
            cleaned_row = self._clean_row_data(r)
            ws.append(cleaned_row)
        
        # 查找sale_amount列的索引并设置货币格式
        if 'sale_amount' in cleaned_data.columns:
            sale_amount_col = cleaned_data.columns.get_loc('sale_amount') + 1  # Excel列索引从1开始
            
            # 应用货币格式到sale_amount列（跳过标题行）
            for row in range(2, len(cleaned_data) + 2):  # 从第2行开始（第1行是标题）
                cell = ws.cell(row=row, column=sale_amount_col)
                cell.number_format = '"$"#,##0.00'
            
            print_step("货币格式", f"已为主Excel文件的sale_amount栏位设置美元货币格式")
        
        # 保存文件
        wb.save(output_path)
        print_step("主Excel完成", f"成功生成清洗后的主Excel文件: {output_path}")
        
        return output_path
    
    def _clean_row_data(self, row):
        """
        清理行数据中的特殊字符，确保Excel兼容性
        
        Args:
            row: 数据行（列表或元组）
            
        Returns:
            list: 清理后的数据行
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
    
    def _prepare_partner_summary_for_email(self, result):
        """准备Partner汇总数据用于邮件发送"""
        partner_summary_for_email = {}
        
        # 从处理结果中提取Partner信息
        processing_summary = result.get('processing_summary', {})
        partner_summary = processing_summary.get('partner_summary', {})
        
        if result.get('pub_files'):
            for pub_file_path in result['pub_files']:
                filename = os.path.basename(pub_file_path)
                partner_name = filename.split('_')[0]  # 从文件名提取Partner名称
                partner_info = partner_summary.get(partner_name, {})
                
                partner_summary_for_email[partner_name] = {
                    'records': partner_info.get('records', 0),
                    'amount_formatted': partner_info.get('amount_formatted', '$0.00'),
                    'file_path': pub_file_path
                }
        
        return partner_summary_for_email
    
    def send_self_email(self, result, actual_start_date, actual_end_date):
        """
        发送Partner专用邮件到默认收件人群组
        保持Partner邮件内容和逻辑，只改变收件人为默认邮箱
        
        Args:
            result: 工作流执行结果
            actual_start_date: 实际开始日期
            actual_end_date: 实际结束日期
            
        Returns:
            dict: 邮件发送结果
        """
        print_step("默认邮件发送", "开始发送Partner专用邮件到默认收件人群组...")
        
        # 默认收件人
        default_recipients = ["AmosFang927@gmail.com"]
        
        # 准备Partner汇总数据（与正常Partner邮件发送相同的逻辑）
        partner_summary_for_email = self._prepare_partner_summary_for_email(result)
        
        if not partner_summary_for_email:
            error_msg = "没有找到Partner数据，无法发送邮件"
            print_step("默认邮件错误", f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
        
        # 发送结果统计
        total_sent = 0
        total_failed = 0
        send_results = {}
        
        # 为每个Partner发送专用邮件到默认收件人
        for partner_name, partner_data in partner_summary_for_email.items():
            print_step(f"默认邮件-{partner_name}", f"正在发送{partner_name}专用邮件到默认收件人...")
            
            try:
                # 使用与正常Partner邮件相同的数据准备逻辑
                email_data = self.email_sender._prepare_partner_email_data(
                    partner_name, 
                    partner_data, 
                    actual_end_date, 
                    actual_start_date
                )
                
                # 准备附件文件列表（只包含该Partner的文件）
                file_paths = []
                if partner_data.get('file_path'):
                    file_paths.append(partner_data['file_path'])
                
                # 获取该Partner的飞书信息
                feishu_info = self.email_sender._get_partner_feishu_info(
                    partner_name, 
                    result.get('feishu_upload')
                )
                
                # 发送Partner专用邮件到默认收件人（使用原有的Partner邮件逻辑）
                partner_result = self.email_sender._send_single_partner_email(
                    partner_name,
                    email_data,
                    file_paths,
                    default_recipients,  # 使用默认收件人替代Partner配置的收件人
                    feishu_info,
                    actual_end_date
                )
                
                send_results[partner_name] = partner_result
                
                if partner_result['success']:
                    total_sent += 1
                    print_step(f"默认邮件-{partner_name}", f"✅ 成功发送{partner_name}专用邮件到默认收件人")
                else:
                    total_failed += 1
                    print_step(f"默认邮件-{partner_name}", f"❌ 发送{partner_name}专用邮件失败: {partner_result['error']}")
                    
            except Exception as e:
                total_failed += 1
                error_msg = f"发送{partner_name}专用邮件异常: {str(e)}"
                print_step(f"默认邮件-{partner_name}", f"❌ {error_msg}")
                send_results[partner_name] = {'success': False, 'error': error_msg}
        
        # 返回发送结果
        overall_success = total_failed == 0
        
        if overall_success:
            print_step("默认邮件完成", f"✅ 成功发送 {total_sent} 个Partner专用邮件到默认收件人")
        else:
            print_step("默认邮件部分失败", f"⚠️ 邮件发送完成：成功 {total_sent} 个，失败 {total_failed} 个")
        
        return {
            'success': overall_success,
            'total_sent': total_sent,
            'total_failed': total_failed,
            'recipients': default_recipients,
            'partner_results': send_results,
            'message': f"发送到默认收件人：成功 {total_sent} 个Partner邮件，失败 {total_failed} 个"
        }
    
    # 保持向后兼容性的方法别名
    def _prepare_pub_summary_for_email(self, result):
        """向后兼容性方法，调用新的_prepare_partner_summary_for_email"""
        return self._prepare_partner_summary_for_email(result)
    
    def _prepare_email_data(self, result, start_date=None, end_date=None):
        """准备邮件数据（兼容性保留）"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 从处理结果中提取信息
        processing_summary = result.get('processing_summary', {})
        total_records = processing_summary.get('total_records', 0)
        total_amount = processing_summary.get('adjusted_total_amount_formatted', '$0.00')
        
        # 准备Partner文件信息（更新变量名）
        partner_files_info = []
        if result.get('pub_files'):  # 保持pub_files变量名以保持兼容性
            partner_summary = processing_summary.get('partner_summary', {})  # 新的变量名
            for partner_file_path in result['pub_files']:
                filename = os.path.basename(partner_file_path)
                partner_name = filename.split('_')[0]  # 从文件名提取Partner名称
                partner_info = partner_summary.get(partner_name, {})
                
                partner_files_info.append({
                    'filename': filename,
                    'records': partner_info.get('records', 0),
                    'amount': partner_info.get('amount_formatted', '$0.00')
                })
        
        return {
            'total_records': total_records,
            'total_amount': total_amount,
            'start_date': start_date or today,
            'end_date': end_date or today,
            'main_file': result.get('excel_file', ''),
            'partner_files': partner_files_info,  # 新的变量名
            'pub_files': partner_files_info  # 保持向后兼容性
        }
    
    def run_api_only(self, start_date=None, end_date=None, save_to_file=True):
        """
        只运行API数据获取
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            save_to_file: 是否保存到文件
        
        Returns:
            dict: API返回的数据
        """
        print_step("API模式", "只执行API数据获取")
        
        # 认证
        if not self.api_client.authenticate():
            return None
        
        # 获取数据
        if start_date and end_date:
            data = self.api_client.get_conversions(start_date, end_date)
        else:
            data = self.api_client.get_conversions_default_range()
        
        # 保存文件
        if data and save_to_file:
            self.api_client.save_to_json(data)
        
        return data
    
    def run_convert_only(self, json_input, output_filename=None):
        """
        只运行JSON到Excel转换
        
        Args:
            json_input: JSON数据（字典、字符串或文件路径）
            output_filename: 输出文件名
        
        Returns:
            str: 生成的Excel文件路径
        """
        print_step("转换模式", "只执行JSON到Excel转换")
        
        return self.converter.convert(json_input, output_filename)
    
    def run_process_only(self, data_input, output_dir=None):
        """
        只运行数据处理
        
        Args:
            data_input: 数据源（Excel文件、JSON文件或其他支持格式）
            output_dir: 输出目录
        
        Returns:
            dict: 数据处理结果摘要
        """
        print_step("数据处理模式", "只执行数据清洗与Pub分类")
        
        result = self.data_processor.process_data(data_input, output_dir)
        self.data_processor.print_detailed_summary(result)
        return result
    
    def _print_final_result(self, result):
        """打印最终结果摘要"""
        print_step("最终结果", "工作流执行结果摘要:")
        
        print("🎯 执行结果:")
        print(f"   ✅ 成功状态: {'是' if result['success'] else '否'}")
        
        if result['json_file']:
            print(f"   📄 JSON文件: {result['json_file']}")
        
        if result['excel_file']:
            print(f"   📊 Excel文件: {result['excel_file']}")
        
        if result.get('pub_files'):
            print(f"   📂 Pub分类文件: {len(result['pub_files'])} 个")
            for pub_file in result['pub_files'][:3]:  # 只显示前3个
                filename = pub_file.split('/')[-1] if '/' in pub_file else pub_file
                print(f"      - {filename}")
            if len(result['pub_files']) > 3:
                print(f"      ... 还有 {len(result['pub_files']) - 3} 个文件")
        
        if result.get('processing_summary'):
            summary = result['processing_summary']
            print(f"   💰 总金额: ${summary.get('total_sale_amount', 0):,.2f} USD")
            print(f"   📋 Partner数量: {summary.get('partner_count', summary.get('pub_count', 0))} 个")  # 兼容性处理
        
        if result['error']:
            print(f"   ❌ 错误信息: {result['error']}")
        
        print(f"   ⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def get_api_configs():
    """获取API配置映射"""
    return {
        "LisaidWebeye": {
            "api_secret": "PPoTSymFFxjJu0CXhCrOD0bCpReCjcZNOyEr0BveZm8=",
            "api_key": "general"
        },
        "LisaidByteC": {
            "api_secret": "boiTXnRgB2B3N7rCictjjti1ufNIzKksSURJHwqtC50=",
            "api_key": "general"
        },
        "IAByteC": {
            "api_secret": "Q524XgLnQmrIBiOK8ZD2qmgmQDPbuTqx13tBDWd6BT0=",
            "api_key": "general"
        }
    }

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='WeeklyReporter - Involve Asia数据获取和Excel转换工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 运行完整工作流（使用默认日期范围）
  python main.py

  # 指定日期范围
  python main.py --start-date 2025-01-01 --end-date 2025-01-07

  # 使用指定的API配置
  python main.py --api LisaidWebeye
  python main.py --api LisaidByteC
  python main.py --api IAByteC

  # 限制获取记录数（例如只获取100条记录）
  python main.py --limit 100

  # 只处理特定Partner（例如只处理RAMPUP）
  python main.py --partner RAMPUP

  # 处理多个Partner（例如RAMPUP和YueMeng）
  python main.py --partner RAMPUP,YueMeng

  # 处理所有Partner
  python main.py --partner all

  # 组合使用：指定API和限制记录数
  python main.py --api LisaidWebeye --limit 100 --partner RAMPUP --start-date 2025-06-17 --end-date 2025-06-18

  # 只获取API数据
  python main.py --api-only

  # 只转换现有JSON文件
  python main.py --convert-only conversions.json

  # 只处理现有数据文件（Excel/JSON）
  python main.py --process-only data.xlsx

  # 保存中间JSON文件并上传到飞书
  python main.py --save-json --upload-feishu

  # 只上传现有文件到飞书
  python main.py --upload-only

  # 处理数据但不发送邮件
  python main.py --no-email

  # 发送邮件到默认收件人群组（AmosFang927@gmail.com）
  python main.py --self-email

  # 测试飞书API连接
  python main.py --test-feishu
        ''')
    
    # API配置参数
    api_configs = get_api_configs()
    parser.add_argument('--api', type=str, choices=list(api_configs.keys()),
                       help=f'指定API配置，可选: {", ".join(api_configs.keys())}')
    
    # 日期参数
    parser.add_argument('--start-date', type=str, 
                       help='开始日期 (YYYY-MM-DD格式)')
    parser.add_argument('--end-date', type=str,
                       help='结束日期 (YYYY-MM-DD格式)')
    
    # 数据限制参数
    parser.add_argument('--limit', type=int,
                       help='最大记录数限制，例如 --limit 100 表示最多获取100条记录')
    parser.add_argument('--partner', type=str,
                       help='指定要处理的Partner，支持单个或多个（用逗号分隔），例如 --partner RAMPUP 或 --partner RAMPUP,YueMeng，使用 --partner all 处理所有Partner，默认处理所有Partner')
    
    # 输出文件名
    parser.add_argument('--output', '-o', type=str,
                       help='Excel输出文件名')
    
    # 模式选择
    parser.add_argument('--api-only', action='store_true',
                       help='只执行API数据获取')
    parser.add_argument('--convert-only', type=str, metavar='JSON_FILE',
                       help='只执行JSON到Excel转换，指定JSON文件路径')
    parser.add_argument('--process-only', type=str, metavar='DATA_FILE',
                       help='只执行数据处理，指定Excel或JSON文件路径')
    parser.add_argument('--upload-only', action='store_true',
                       help='只执行飞书上传，上传output目录下所有Excel文件')
    
    # 其他选项
    parser.add_argument('--save-json', action='store_true',
                       help='保存中间JSON文件')
    parser.add_argument('--upload-feishu', action='store_true',
                       help='上传所有Excel文件到飞书Sheet')
    parser.add_argument('--test-feishu', action='store_true',
                       help='测试飞书API连接')
    parser.add_argument('--send-email', action='store_true',
                       help='发送邮件报告')
    parser.add_argument('--self-email', action='store_true',
                       help='发送邮件到默认收件人群组 (AmosFang927@gmail.com)')
    parser.add_argument('--no-email', action='store_true',
                       help='不发送邮件给任何Partners')
    parser.add_argument('--test-email', action='store_true',
                       help='测试邮件连接')
    parser.add_argument('--start-scheduler', action='store_true',
                       help='启动定时任务（每日9点执行）')
    parser.add_argument('--run-scheduler-now', action='store_true',
                       help='立即执行一次定时任务（测试用）')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='显示详细日志')
    
    return parser

def main():
    """主函数"""
    # 确保在容器环境中输出不被缓冲
    import sys
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    
    print("🚀 WeeklyReporter - Involve Asia数据处理工具")
    print("=" * 60)
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📂 输出目录: {config.OUTPUT_DIR}")
    print(f"🌐 运行环境: {'Cloud Run' if os.getenv('K_SERVICE') else 'Local'}")
    print("=" * 60)
    sys.stdout.flush()  # 强制刷新输出
    
    # 解析命令行参数
    parser = create_parser()
    args = parser.parse_args()
    
    # 获取API配置
    api_secret = None
    api_key = None
    selected_api = None
    use_multi_api = False
    required_apis = []
    
    if args.api:
        # 用户手动指定了API
        selected_api = args.api
        print(f"🔑 用户指定API配置: {selected_api}")
    else:
        # 根据Partner自动选择API
        if args.partner:
            # 解析Partner列表，处理 "all" 关键字
            if args.partner.lower() == 'all':
                # 展开为所有Partner
                partner_list = list(config.PARTNER_SOURCES_MAPPING.keys())
                print(f"🔑 展开 --partner all 为所有Partner: {', '.join(partner_list)}")
            else:
                # 解析用逗号分隔的Partner列表
                partner_list = [p.strip() for p in args.partner.split(',')]
            
            needs_multi, apis = config.needs_multi_api_for_partners(partner_list)
            
            if needs_multi:
                use_multi_api = True
                required_apis = apis
                print(f"🔑 根据Partner({', '.join(partner_list)})需要调用多个API: {', '.join(apis)}")
                # 选择第一个API作为主API（为了兼容性）
                selected_api = apis[0]
            else:
                selected_api = config.get_preferred_api_for_partners(partner_list)
                print(f"🔑 根据Partner({', '.join(partner_list)})自动选择API: {selected_api}")
        else:
            # 没有指定Partner，使用默认API
            selected_api = config.DEFAULT_API_PLATFORM
            print(f"🔑 使用默认API配置: {selected_api}")
    
    # 获取API配置
    api_configs = get_api_configs()
    if selected_api in api_configs:
        api_config = api_configs[selected_api]
        api_secret = api_config['api_secret']
        api_key = api_config['api_key']
    else:
        print(f"❌ 未找到API配置: {selected_api}")
        sys.exit(1)
    
    # 创建WeeklyReporter实例
    # 先检查是否使用了--no-email参数
    global_email_disabled = False
    if hasattr(args, 'no_email') and args.no_email:
        global_email_disabled = True
    
    reporter = WeeklyReporter(api_secret=api_secret, api_key=api_key, global_email_disabled=global_email_disabled)
    
    # 设置多API支持
    if use_multi_api:
        print(f"📋 配置多API支持: {', '.join(required_apis)}")
        # 为多API调用准备API列表
        api_list = []
        for api_name in required_apis:
            if api_name in api_configs:
                api_info = api_configs[api_name]
                api_list.append({
                    'name': api_name,
                    'secret': api_info['api_secret'],
                    'key': api_info['api_key']
                })
        
        print(f"📊 已配置 {len(api_list)} 个API端点用于数据获取")
    
    try:
        if args.test_feishu:
            # 测试飞书连接
            test_reporter = WeeklyReporter(global_email_disabled=True)  # 测试功能不需要API配置，禁用邮件
            success = test_reporter.feishu_uploader.test_connection()
            print(f"\n{'✅ 飞书连接测试成功' if success else '❌ 飞书连接测试失败'}")
            sys.exit(0 if success else 1)
            
        elif args.test_email:
            # 测试邮件连接
            test_reporter = WeeklyReporter(global_email_disabled=True)  # 测试功能不需要API配置，禁用邮件
            success = test_reporter.email_sender.test_connection()
            print(f"\n{'✅ 邮件连接测试成功' if success else '❌ 邮件连接测试失败'}")
            sys.exit(0 if success else 1)
            
        elif args.start_scheduler:
            # 启动定时任务
            scheduler_reporter = WeeklyReporter(api_secret=api_secret, api_key=api_key, global_email_disabled=False)  # 调度器需要API配置，保持邮件功能
            scheduler_reporter.scheduler = ReportScheduler(scheduler_reporter)
            scheduler_reporter.scheduler.start()
            
            status = scheduler_reporter.scheduler.get_status()
            print(f"\n✅ 定时任务已启动")
            print(f"📅 执行时间: 每日 {status['daily_time']}")
            print(f"⏰ 下次执行: {status['next_run']}")
            print(f"\n定时任务将持续运行，按 Ctrl+C 停止...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                scheduler_reporter.scheduler.stop()
                print(f"\n👋 定时任务已停止")
                sys.exit(0)
                
        elif args.run_scheduler_now:
            # 立即执行定时任务
            scheduler_reporter = WeeklyReporter(api_secret=api_secret, api_key=api_key, global_email_disabled=False)  # 调度器需要API配置，保持邮件功能
            scheduler = ReportScheduler(scheduler_reporter)
            scheduler.run_now()
            sys.exit(0)
            
        elif args.convert_only:
            # 只转换模式
            excel_file = reporter.run_convert_only(args.convert_only, args.output)
            print(f"\n✅ 转换完成，Excel文件: {excel_file}")
            
        elif args.process_only:
            # 只数据处理模式
            result = reporter.run_process_only(args.process_only)
            if result['success']:
                print(f"\n✅ 数据处理完成，生成 {len(result['pub_files'])} 个Pub分类文件")
            else:
                print(f"\n❌ 数据处理失败")
                
        elif args.upload_only:
            # 只飞书上传模式
            result = reporter.run_feishu_upload_only()
            if result['success']:
                print(f"\n✅ 飞书上传完成，成功上传 {result['success_count']} 个文件")
            else:
                print(f"\n❌ 飞书上传失败: {result.get('error', '未知错误')}")
            
        elif args.api_only:
            # 应用配置参数
            if args.limit is not None:
                config.MAX_RECORDS_LIMIT = args.limit
                print(f"📋 设置最大记录数限制: {args.limit}")
            
            if args.partner is not None:
                config.TARGET_PARTNER = args.partner
                print(f"📋 设置目标Partner: {args.partner}")
            
            # 只获取API数据模式
            data = reporter.run_api_only(args.start_date, args.end_date)
            if data:
                print(f"\n✅ API数据获取完成，共 {data['data']['current_page_count']} 条记录")
            else:
                print("\n❌ API数据获取失败")
                
        else:
            # 处理多个Partner的情况
            target_partners = None
            if args.partner:
                # 检查是否为 'all' 关键字
                if args.partner.lower() == 'all':
                    # 处理所有Partner
                    target_partners = None  # None表示处理所有Partner
                    print("📋 指定处理所有Partner (--partner all)")
                else:
                    # 支持用逗号分隔和加号分隔的多个Partner
                    partner_string = args.partner
                    # 先按逗号分隔，再按加号分隔
                    all_partners = []
                    for part in partner_string.split(','):
                        for p in part.split('+'):
                            p = p.strip()
                            if p:
                                all_partners.append(p)
                    
                    target_partners = all_partners
                    if len(target_partners) == 1:
                        target_partners = target_partners[0]  # 单个Partner保持字符串格式
                    print(f"📋 指定处理的Partner: {target_partners}")
            
            # 确定是否发送邮件
            should_send_email = True  # 默认发送邮件
            should_send_self_email = False  # 默认不发送到默认收件人
            
            if args.no_email:
                should_send_email = False
                print("📧 已禁用邮件发送 (--no-email)")
            elif args.self_email:
                should_send_email = False  # 禁用常规邮件
                should_send_self_email = True  # 启用默认收件人邮件
                print("📧 已启用发送到默认收件人 (--self-email)")
            elif args.send_email:
                should_send_email = True
                print("📧 已启用邮件发送 (--send-email)")
            
            # 设置多API配置到reporter实例
            if use_multi_api:
                reporter.multi_api_configs = api_list
                print(f"🔧 已为reporter配置多API支持")
            
            # 完整工作流模式 - 默认执行所有流程
            result = reporter.run_full_workflow(
                start_date=args.start_date,
                end_date=args.end_date,
                output_filename=args.output,
                save_json=True,  # 默认保存JSON
                upload_to_feishu=True,  # 默认上传到飞书
                send_email=should_send_email,  # 根据参数决定是否发送邮件
                send_self_email=should_send_self_email,  # 根据参数决定是否发送到默认收件人
                max_records=args.limit,  # 数据限制
                target_partner=target_partners  # Partner过滤（支持单个或多个）
            )
            
            if result['success']:
                print(f"\n🎉 完整工作流执行成功！")
                print(f"📊 Excel文件已生成: {result['excel_file']}")
                sys.exit(0)
            else:
                print(f"\n❌ 工作流执行失败: {result['error']}")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 程序执行失败: {str(e)}")
        log_error(f"主程序执行失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
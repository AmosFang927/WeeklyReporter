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
from utils.logger import print_step, log_error
import config

class WeeklyReporter:
    """周报生成器主类"""
    
    def __init__(self):
        self.api_client = InvolveAsiaAPI()
        self.converter = JSONToExcelConverter()
        self.data_processor = DataProcessor()
        self.feishu_uploader = FeishuUploader()
        self.email_sender = EmailSender()
        self.scheduler = None
    
    def run_full_workflow(self, start_date=None, end_date=None, output_filename=None, save_json=False, upload_to_feishu=False, send_email=False, max_records=None, target_partner=None):
        """
        运行完整的工作流程
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            output_filename: Excel输出文件名
            save_json: 是否保存中间JSON文件
            upload_to_feishu: 是否上传到飞书
            send_email: 是否发送邮件
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
                json_file = self.api_client.save_to_json(conversion_data)
                result['json_file'] = json_file
            
            # 步骤4: 数据处理与清洗
            print_step("数据处理", "开始执行数据清洗与Pub分类导出")
            # 获取实际的日期范围
            actual_start_date = start_date
            actual_end_date = end_date
            if not actual_start_date or not actual_end_date:
                # 如果没有指定日期，使用默认日期范围
                actual_start_date, actual_end_date = config.get_default_date_range()
            
            # 传递完整的日期范围信息
            processor_result = self.data_processor.process_data(
                conversion_data, 
                start_date=actual_start_date, 
                end_date=actual_end_date
            )
            result['processing_summary'] = processor_result
            result['pub_files'] = processor_result.get('pub_files', [])
            
            # 步骤5: 生成主Excel文件（使用清洗后的数据）
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
        
        # 写入数据（包含标题行）
        for r in dataframe_to_rows(cleaned_data, index=False, header=True):
            ws.append(r)
        
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

  # 限制获取记录数（例如只获取100条记录）
  python main.py --limit 100

  # 只处理特定Partner（例如只处理RAMPUP）
  python main.py --partner RAMPUP

  # 处理多个Partner（例如RAMPUP和YueMeng）
  python main.py --partner RAMPUP,YueMeng

  # 组合使用：限制100条记录，只处理RAMPUP Partner
  python main.py --limit 100 --partner RAMPUP --start-date 2025-06-17 --end-date 2025-06-18

  # 组合使用：处理多个Partner
  python main.py --limit 100 --partner RAMPUP,YueMeng --start-date 2025-06-17 --end-date 2025-06-18

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

  # 测试飞书API连接
  python main.py --test-feishu
        ''')
    
    # 日期参数
    parser.add_argument('--start-date', type=str, 
                       help='开始日期 (YYYY-MM-DD格式)')
    parser.add_argument('--end-date', type=str,
                       help='结束日期 (YYYY-MM-DD格式)')
    
    # 数据限制参数
    parser.add_argument('--limit', type=int,
                       help='最大记录数限制，例如 --limit 100 表示最多获取100条记录')
    parser.add_argument('--partner', type=str,
                       help='指定要处理的Partner，支持单个或多个（用逗号分隔），例如 --partner RAMPUP 或 --partner RAMPUP,YueMeng，默认处理所有Partner')
    
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
    
    # 创建WeeklyReporter实例
    reporter = WeeklyReporter()
    
    try:
        if args.test_feishu:
            # 测试飞书连接
            reporter = WeeklyReporter()
            success = reporter.feishu_uploader.test_connection()
            print(f"\n{'✅ 飞书连接测试成功' if success else '❌ 飞书连接测试失败'}")
            sys.exit(0 if success else 1)
            
        elif args.test_email:
            # 测试邮件连接
            reporter = WeeklyReporter()
            success = reporter.email_sender.test_connection()
            print(f"\n{'✅ 邮件连接测试成功' if success else '❌ 邮件连接测试失败'}")
            sys.exit(0 if success else 1)
            
        elif args.start_scheduler:
            # 启动定时任务
            reporter = WeeklyReporter()
            reporter.scheduler = ReportScheduler(reporter)
            reporter.scheduler.start()
            
            status = reporter.scheduler.get_status()
            print(f"\n✅ 定时任务已启动")
            print(f"📅 执行时间: 每日 {status['daily_time']}")
            print(f"⏰ 下次执行: {status['next_run']}")
            print(f"\n定时任务将持续运行，按 Ctrl+C 停止...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                reporter.scheduler.stop()
                print(f"\n👋 定时任务已停止")
                sys.exit(0)
                
        elif args.run_scheduler_now:
            # 立即执行定时任务
            reporter = WeeklyReporter()
            scheduler = ReportScheduler(reporter)
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
                # 支持用逗号分隔的多个Partner
                target_partners = [p.strip() for p in args.partner.split(',') if p.strip()]
                if len(target_partners) == 1:
                    target_partners = target_partners[0]  # 单个Partner保持字符串格式
                print(f"📋 指定处理的Partner: {target_partners}")
            
            # 完整工作流模式 - 默认执行所有流程
            result = reporter.run_full_workflow(
                start_date=args.start_date,
                end_date=args.end_date,
                output_filename=args.output,
                save_json=True,  # 默认保存JSON
                upload_to_feishu=True,  # 默认上传到飞书
                send_email=True,  # 默认发送邮件
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
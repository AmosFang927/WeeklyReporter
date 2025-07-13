"""
Reporter-Agent: 报告生成器
整合Data-DMP-Agent和Data-Output-Agent的完整报告生成流程
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import (
    PARTNER_SOURCES_MAPPING,
    get_partner_email_config,
    get_default_date_range
)
from agents.data_dmp_agent.commission_calculator import CommissionCalculator
from agents.data_output_agent.output_processor import OutputProcessor


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self):
        self.commission_calculator = CommissionCalculator()
        self.output_processor = OutputProcessor()
    
    async def generate_partner_report(self, partner_name: str, start_date: str, end_date: str,
                                    output_formats: List[str] = None,
                                    custom_recipients: List[str] = None,
                                    dry_run: bool = False) -> Dict[str, Any]:
        """
        生成Partner报告
        
        Args:
            partner_name: Partner名称
            start_date: 开始日期
            end_date: 结束日期
            output_formats: 输出格式列表 ['json', 'excel', 'feishu', 'email']
            custom_recipients: 自定义收件人列表
            dry_run: 是否为测试模式
            
        Returns:
            Dict包含生成结果
        """
        try:
            print(f"📊 开始生成 {partner_name} 报告...")
            print(f"   📅 日期范围: {start_date} 到 {end_date}")
            
            # 1. 从Data-DMP-Agent获取数据
            print(f"   🔍 Step 1: 从Data-DMP-Agent获取数据...")
            conversion_data = await self.get_conversion_data(partner_name, start_date, end_date)
            
            if not conversion_data:
                return {
                    'success': False,
                    'error': f'没有找到 {partner_name} 的转化数据',
                    'partner_name': partner_name,
                    'date_range': f'{start_date} to {end_date}'
                }
            
            print(f"   ✅ 获取到 {len(conversion_data)} 条转化数据")
            
            # 2. 计算佣金
            print(f"   💰 Step 2: 计算佣金...")
            commission_data = await self.commission_calculator.calculate_commission(
                conversion_data, partner_name
            )
            
            total_amount = sum(record.get('commission_amount', 0) for record in commission_data)
            print(f"   ✅ 佣金计算完成，总金额: ${total_amount:,.2f}")
            
            # 3. 处理输出
            print(f"   📤 Step 3: 处理输出...")
            
            # 确定输出格式
            if output_formats is None:
                output_formats = ['json', 'excel', 'feishu', 'email']
            
            # 确定邮件收件人
            recipients = custom_recipients
            if not recipients:
                partner_config = get_partner_email_config(partner_name)
                if partner_config['enabled']:
                    recipients = partner_config['recipients']
            
            # 处理各种输出格式
            output_results = {}
            
            for format_type in output_formats:
                if format_type == 'json':
                    result = await self.output_processor.generate_json(
                        commission_data, partner_name, start_date, end_date
                    )
                    output_results['json'] = result
                    
                elif format_type == 'excel':
                    result = await self.output_processor.generate_excel(
                        commission_data, partner_name, start_date, end_date
                    )
                    output_results['excel'] = result
                    
                elif format_type == 'feishu':
                    if not dry_run:
                        result = await self.output_processor.upload_to_feishu(
                            commission_data, partner_name, start_date, end_date
                        )
                        output_results['feishu'] = result
                    else:
                        output_results['feishu'] = {
                            'success': True,
                            'message': 'Dry-run模式: 跳过飞书上传'
                        }
                        
                elif format_type == 'email':
                    if recipients and not dry_run:
                        result = await self.output_processor.send_email(
                            commission_data, partner_name, start_date, end_date, recipients
                        )
                        output_results['email'] = result
                    else:
                        output_results['email'] = {
                            'success': True,
                            'message': 'Dry-run模式: 跳过邮件发送' if dry_run else '没有配置邮件收件人'
                        }
            
            # 汇总结果
            success_count = sum(1 for result in output_results.values() if result.get('success'))
            total_count = len(output_results)
            
            return {
                'success': success_count == total_count,
                'partner_name': partner_name,
                'date_range': f'{start_date} to {end_date}',
                'total_records': len(commission_data),
                'total_amount': total_amount,
                'total_amount_formatted': f'${total_amount:,.2f}',
                'output_results': output_results,
                'summary': {
                    'success_count': success_count,
                    'total_count': total_count,
                    'processed_formats': list(output_results.keys())
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'报告生成失败: {str(e)}',
                'partner_name': partner_name,
                'date_range': f'{start_date} to {end_date}'
            }
    
    async def generate_all_partners_report(self, start_date: str, end_date: str,
                                         output_formats: List[str] = None,
                                         custom_recipients: Dict[str, List[str]] = None,
                                         dry_run: bool = False) -> Dict[str, Any]:
        """
        生成所有Partner的报告
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            output_formats: 输出格式列表
            custom_recipients: 自定义收件人字典 {partner_name: [recipients]}
            dry_run: 是否为测试模式
            
        Returns:
            Dict包含所有Partner的生成结果
        """
        print(f"🚀 开始生成所有Partner报告...")
        print(f"   📅 日期范围: {start_date} 到 {end_date}")
        
        all_results = {}
        success_count = 0
        total_count = 0
        
        # 获取所有Partner
        partners = list(PARTNER_SOURCES_MAPPING.keys())
        
        for partner_name in partners:
            print(f"\n{'='*50}")
            print(f"处理 {partner_name} Partner")
            print(f"{'='*50}")
            
            # 获取当前Partner的收件人列表
            recipients = None
            if custom_recipients and partner_name in custom_recipients:
                recipients = custom_recipients[partner_name]
            
            # 生成报告
            result = await self.generate_partner_report(
                partner_name=partner_name,
                start_date=start_date,
                end_date=end_date,
                output_formats=output_formats,
                custom_recipients=recipients,
                dry_run=dry_run
            )
            
            all_results[partner_name] = result
            total_count += 1
            
            if result['success']:
                success_count += 1
                print(f"✅ {partner_name} 报告生成成功")
        else:
                print(f"❌ {partner_name} 报告生成失败: {result.get('error', 'Unknown error')}")
        
        # 汇总结果
        print(f"\n{'='*50}")
        print(f"📊 所有Partner报告生成完成")
        print(f"{'='*50}")
        print(f"✅ 成功: {success_count}/{total_count}")
        print(f"❌ 失败: {total_count - success_count}/{total_count}")
        
        return {
            'success': success_count == total_count,
            'date_range': f'{start_date} to {end_date}',
            'total_partners': total_count,
            'success_count': success_count,
            'failed_count': total_count - success_count,
            'results': all_results
        }
    
    async def get_conversion_data(self, partner_name: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        从Data-DMP-Agent获取转化数据
        
        Args:
            partner_name: Partner名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            转化数据列表
        """
        try:
            # 这里应该调用实际的Data-DMP-Agent来获取数据
            # 目前使用模拟数据进行测试
            
            # 根据Partner生成不同的模拟数据
            partner_config = PARTNER_SOURCES_MAPPING.get(partner_name, {})
            sources = partner_config.get('sources', [partner_name])
            
            mock_data = []
            for i, source in enumerate(sources):
                for j in range(2):  # 每个source生成2条数据
                    mock_data.append({
                        'transaction_id': f'TXN_{partner_name}_{source}_{i}_{j}',
                        'partner_name': partner_name,
                        'source': source,
                        'offer_name': f'{source} - CPS',
                        'sale_amount': 100.0 + i * 10 + j * 5,
                        'currency': 'USD',
                        'conversion_date': start_date,
                        'status': 'confirmed',
                        'click_id': f'click_{partner_name}_{i}_{j}',
                        'advertiser_id': f'adv_{source}'
                    })
            
            return mock_data
            
        except Exception as e:
            print(f"❌ 获取转化数据失败: {e}")
            return []
    
    async def generate_scheduled_report(self, partner_filter: str = 'all', 
                                      days_ago: int = 2) -> Dict[str, Any]:
        """
        生成定时报告（用于Cloud Scheduler）
        
        Args:
            partner_filter: Partner过滤器 ('all' 或具体的Partner名称)
            days_ago: 多少天前的数据
            
        Returns:
            生成结果
        """
        # 计算日期范围
        target_date = datetime.now() - timedelta(days=days_ago)
        start_date = target_date.strftime('%Y-%m-%d')
        end_date = target_date.strftime('%Y-%m-%d')
        
        if partner_filter.lower() == 'all':
            # 生成所有Partner的报告
            return await self.generate_all_partners_report(
                start_date=start_date,
                end_date=end_date
            )
            else:
            # 生成特定Partner的报告
            return await self.generate_partner_report(
                partner_name=partner_filter,
                start_date=start_date,
                end_date=end_date
            ) 
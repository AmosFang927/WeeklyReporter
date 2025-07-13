"""
Reporter-Agent 整合测试
测试完整的数据流程：Data-DMP-Agent → Data-Output-Agent
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import PARTNER_SOURCES_MAPPING, EMAIL_AUTO_CC
from agents.reporter_agent.report_generator import ReportGenerator
from agents.data_dmp_agent.commission_calculator import CommissionCalculator
from agents.data_output_agent.output_processor import OutputProcessor


class ReporterAgentIntegrationTest:
    """Reporter-Agent整合测试类"""
    
    def __init__(self):
        self.report_generator = ReportGenerator()
        self.commission_calculator = CommissionCalculator()
        self.output_processor = OutputProcessor()
        
    async def test_single_partner_report(self, partner_name: str = "ByteC", 
                                       start_date: str = None, end_date: str = None):
        """测试单个Partner的报告生成"""
        print(f"\n🧪 测试单个Partner报告生成: {partner_name}")
        print("="*50)
        
        # 使用默认日期（2天前）
        if start_date is None or end_date is None:
            target_date = datetime.now() - timedelta(days=2)
            start_date = target_date.strftime('%Y-%m-%d')
            end_date = target_date.strftime('%Y-%m-%d')
        
        try:
            # 生成报告
            result = await self.report_generator.generate_partner_report(
                partner_name=partner_name,
                start_date=start_date,
                end_date=end_date,
                output_formats=['json', 'excel', 'feishu', 'email'],
                custom_recipients=[EMAIL_AUTO_CC],  # 发送给自己
                dry_run=False  # 实际测试，不是dry-run
            )
            
            # 输出结果
            if result['success']:
                print(f"✅ {partner_name} 报告生成成功")
                print(f"   📊 总记录数: {result['total_records']}")
                print(f"   💰 总金额: {result['total_amount_formatted']}")
                print(f"   📅 日期范围: {result['date_range']}")
                
                # 输出各格式的处理结果
                print("\n📋 输出格式处理结果:")
                for format_type, format_result in result['output_results'].items():
                    if format_result['success']:
                        print(f"   ✅ {format_type.upper()}: {format_result['message']}")
                        if format_type == 'excel' and 'file_path' in format_result:
                            print(f"      📁 文件路径: {format_result['file_path']}")
                        elif format_type == 'feishu' and 'feishu_url' in format_result:
                            print(f"      🔗 飞书链接: {format_result['feishu_url']}")
                        elif format_type == 'email' and 'sent_to' in format_result:
                            print(f"      📧 发送给: {', '.join(format_result['sent_to'])}")
                    else:
                        print(f"   ❌ {format_type.upper()}: {format_result.get('error', '失败')}")
                        
                print(f"\n📈 处理汇总:")
                print(f"   成功: {result['summary']['success_count']}/{result['summary']['total_count']}")
                print(f"   格式: {', '.join(result['summary']['processed_formats'])}")
                
            else:
                print(f"❌ {partner_name} 报告生成失败")
                print(f"   错误: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_all_partners_report(self, start_date: str = None, end_date: str = None):
        """测试所有Partner的报告生成"""
        print(f"\n🧪 测试所有Partner报告生成")
        print("="*50)
        
        # 使用默认日期（2天前）
        if start_date is None or end_date is None:
            target_date = datetime.now() - timedelta(days=2)
            start_date = target_date.strftime('%Y-%m-%d')
            end_date = target_date.strftime('%Y-%m-%d')
        
        try:
            # 生成所有Partner的报告
            result = await self.report_generator.generate_all_partners_report(
                start_date=start_date,
                end_date=end_date,
                output_formats=['json', 'excel'],  # 只测试JSON和Excel，避免过多的邮件
                custom_recipients={'ByteC': [EMAIL_AUTO_CC]},  # 只给ByteC发送邮件测试
                dry_run=True  # 测试模式
            )
            
            # 输出结果
            if result['success']:
                print(f"✅ 所有Partner报告生成成功")
                print(f"   📊 总Partner数: {result['total_partners']}")
                print(f"   ✅ 成功: {result['success_count']}")
                print(f"   ❌ 失败: {result['failed_count']}")
                print(f"   📅 日期范围: {result['date_range']}")
                
                # 输出各Partner的结果
                print("\n📋 各Partner处理结果:")
                for partner_name, partner_result in result['results'].items():
                    if partner_result['success']:
                        print(f"   ✅ {partner_name}: {partner_result['total_records']} 记录, {partner_result['total_amount_formatted']}")
                    else:
                        print(f"   ❌ {partner_name}: {partner_result.get('error', '失败')}")
                        
            else:
                print(f"❌ 部分Partner报告生成失败")
                print(f"   成功: {result['success_count']}/{result['total_partners']}")
                print(f"   失败: {result['failed_count']}/{result['total_partners']}")
                
            return result
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_commission_calculation(self, partner_name: str = "DeepLeaper"):
        """测试佣金计算功能"""
        print(f"\n🧪 测试佣金计算功能: {partner_name}")
        print("="*50)
        
        try:
            # 准备模拟数据
            mock_data = [
                {
                    'transaction_id': f'TXN_{partner_name}_001',
                    'partner_name': partner_name,
                    'offer_name': 'Shopee ID (Media Buyers) - CPS',
                    'sale_amount': 100.00,
                    'currency': 'USD',
                    'conversion_date': '2025-01-24',
                    'status': 'confirmed'
                },
                {
                    'transaction_id': f'TXN_{partner_name}_002',
                    'partner_name': partner_name,
                    'offer_name': 'Shopee TH - CPS',
                    'sale_amount': 200.00,
                    'currency': 'USD',
                    'conversion_date': '2025-01-24',
                    'status': 'confirmed'
                }
            ]
            
            print(f"📊 输入数据: {len(mock_data)} 条转化记录")
            
            # 计算佣金
            commission_data = await self.commission_calculator.calculate_commission(
                mock_data, partner_name
            )
            
            print(f"✅ 佣金计算完成")
            print(f"   📊 处理记录数: {len(commission_data)}")
            
            # 输出详细结果
            total_commission = 0
            for record in commission_data:
                print(f"   💰 {record.get('offer_name', 'N/A')}: "
                      f"${record.get('sale_amount', 0):.2f} → "
                      f"${record.get('commission_amount', 0):.2f} "
                      f"({record.get('commission_rate', 0):.2f}%)")
                total_commission += record.get('commission_amount', 0)
            
            print(f"   💰 总佣金: ${total_commission:.2f}")
            
            return {'success': True, 'commission_data': commission_data}
            
        except Exception as e:
            print(f"❌ 佣金计算测试失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_output_formats(self, partner_name: str = "RAMPUP"):
        """测试输出格式功能"""
        print(f"\n🧪 测试输出格式功能: {partner_name}")
        print("="*50)
        
        try:
            # 准备模拟数据
            mock_data = [
                {
                    'transaction_id': f'TXN_{partner_name}_001',
                    'partner_name': partner_name,
                    'offer_name': 'Shopee ID (Media Buyers) - CPS',
                    'sale_amount': 150.00,
                    'currency': 'USD',
                    'conversion_date': '2025-01-24',
                    'status': 'confirmed',
                    'commission_amount': 3.75,
                    'commission_rate': 2.5
                }
            ]
            
            start_date = '2025-01-24'
            end_date = '2025-01-24'
            
            print(f"📊 测试数据: {len(mock_data)} 条记录")
            
            # 测试各种输出格式
            formats_to_test = ['json', 'excel', 'feishu', 'email']
            results = {}
            
            for format_type in formats_to_test:
                print(f"\n📤 测试 {format_type.upper()} 格式...")
                
                try:
                    if format_type == 'json':
                        result = await self.output_processor.generate_json(
                            mock_data, partner_name, start_date, end_date
                        )
                    elif format_type == 'excel':
                        result = await self.output_processor.generate_excel(
                            mock_data, partner_name, start_date, end_date
                        )
                    elif format_type == 'feishu':
                        result = await self.output_processor.upload_to_feishu(
                            mock_data, partner_name, start_date, end_date
                        )
                    elif format_type == 'email':
                        result = await self.output_processor.send_email(
                            mock_data, partner_name, start_date, end_date, 
                            [EMAIL_AUTO_CC]
                        )
                    
                    results[format_type] = result
                    
                    if result['success']:
                        print(f"   ✅ {format_type.upper()}: {result['message']}")
                        if format_type == 'excel' and 'file_path' in result:
                            print(f"      📁 文件: {result['file_path']}")
                        elif format_type == 'feishu' and 'feishu_url' in result:
                            print(f"      🔗 链接: {result['feishu_url']}")
                        elif format_type == 'email' and 'sent_to' in result:
                            print(f"      📧 发送给: {', '.join(result['sent_to'])}")
                    else:
                        print(f"   ❌ {format_type.upper()}: {result.get('error', '失败')}")
                        
                except Exception as e:
                    print(f"   ❌ {format_type.upper()}: {e}")
                    results[format_type] = {'success': False, 'error': str(e)}
            
            # 汇总结果
            success_count = sum(1 for r in results.values() if r.get('success'))
            total_count = len(results)
            
            print(f"\n📈 输出格式测试汇总:")
            print(f"   成功: {success_count}/{total_count}")
            print(f"   失败: {total_count - success_count}/{total_count}")
            
            return {
                'success': success_count == total_count,
                'results': results,
                'success_count': success_count,
                'total_count': total_count
            }
            
        except Exception as e:
            print(f"❌ 输出格式测试失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def test_scheduled_report(self, partner_filter: str = "all", days_ago: int = 2):
        """测试定时报告功能"""
        print(f"\n🧪 测试定时报告功能: {partner_filter}, {days_ago} 天前")
        print("="*50)
        
        try:
            # 生成定时报告
            result = await self.report_generator.generate_scheduled_report(
                partner_filter=partner_filter,
                days_ago=days_ago
            )
            
            if result['success']:
                print(f"✅ 定时报告生成成功")
                
                if partner_filter.lower() == 'all':
                    print(f"   📊 总Partner数: {result['total_partners']}")
                    print(f"   ✅ 成功: {result['success_count']}")
                    print(f"   ❌ 失败: {result['failed_count']}")
                    print(f"   📅 日期范围: {result['date_range']}")
                else:
                    print(f"   📊 Partner: {result['partner_name']}")
                    print(f"   📊 总记录数: {result['total_records']}")
                    print(f"   💰 总金额: {result['total_amount_formatted']}")
                    print(f"   📅 日期范围: {result['date_range']}")
                    
            else:
                print(f"❌ 定时报告生成失败")
                print(f"   错误: {result.get('error', 'Unknown error')}")
                
            return result
            
        except Exception as e:
            print(f"❌ 定时报告测试失败: {e}")
            return {'success': False, 'error': str(e)}
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行Reporter-Agent整合测试")
        print("="*60)
        
        test_results = {}
        
        # 测试1: 单个Partner报告生成
        print("\n📝 测试1: 单个Partner报告生成")
        test_results['single_partner'] = await self.test_single_partner_report("ByteC")
        
        # 测试2: 佣金计算功能
        print("\n📝 测试2: 佣金计算功能")
        test_results['commission'] = await self.test_commission_calculation("DeepLeaper")
        
        # 测试3: 输出格式功能
        print("\n📝 测试3: 输出格式功能")
        test_results['output_formats'] = await self.test_output_formats("RAMPUP")
        
        # 测试4: 定时报告功能
        print("\n📝 测试4: 定时报告功能")
        test_results['scheduled_report'] = await self.test_scheduled_report("ByteC", 2)
        
        # 测试5: 所有Partner报告生成（简化版）
        print("\n📝 测试5: 所有Partner报告生成")
        test_results['all_partners'] = await self.test_all_partners_report()
        
        # 输出最终结果
        print("\n" + "="*60)
        print("📊 Reporter-Agent整合测试结果汇总")
        print("="*60)
        
        success_count = 0
        total_count = len(test_results)
        
        for test_name, result in test_results.items():
            if result.get('success'):
                print(f"✅ {test_name}: 通过")
                success_count += 1
            else:
                print(f"❌ {test_name}: 失败 - {result.get('error', 'Unknown error')}")
        
        print(f"\n📈 整体测试结果:")
        print(f"   ✅ 成功: {success_count}/{total_count}")
        print(f"   ❌ 失败: {total_count - success_count}/{total_count}")
        print(f"   📊 成功率: {success_count/total_count*100:.1f}%")
        
        if success_count == total_count:
            print(f"\n🎉 所有测试通过！Reporter-Agent运行正常。")
        else:
            print(f"\n⚠️  部分测试失败，请检查相关模块。")
        
        return {
            'overall_success': success_count == total_count,
            'success_count': success_count,
            'total_count': total_count,
            'success_rate': success_count/total_count*100,
            'detailed_results': test_results
        }


async def main():
    """主函数"""
    tester = ReporterAgentIntegrationTest()
    await tester.run_all_tests()


if __name__ == '__main__':
    asyncio.run(main()) 
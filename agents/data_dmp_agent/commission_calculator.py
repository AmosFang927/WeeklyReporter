#!/usr/bin/env python3
"""
佣金计算器
处理佣金计算逻辑：90%保留，10%作为margin
"""

import logging
from typing import Dict, Any, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime

logger = logging.getLogger(__name__)


class CommissionCalculator:
    """佣金计算器"""
    
    def __init__(self, margin_rate: float = 0.10):
        """
        初始化佣金计算器
        
        Args:
            margin_rate: Margin比例，默认10%
        """
        self.margin_rate = margin_rate
        self.payout_rate = 1.0 - margin_rate  # 90%
        
    def calculate_commission(self, conversion_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算佣金
        
        Args:
            conversion_data: 转化数据
            
        Returns:
            包含佣金计算结果的字典
        """
        try:
            result = {
                'conversion_id': conversion_data.get('conversion_id'),
                'partner_name': conversion_data.get('partner_name'),
                'original_payouts': {},
                'calculated_payouts': {},
                'margin_amounts': {},
                'calculation_metadata': {
                    'margin_rate': self.margin_rate,
                    'payout_rate': self.payout_rate,
                    'calculated_at': datetime.now().isoformat()
                }
            }
            
            # 获取原始payout数据
            payouts = conversion_data.get('payouts', {})
            
            # 计算各币种的佣金
            for currency, amount in payouts.items():
                if amount is not None:
                    original_amount = Decimal(str(amount))
                    
                    # 计算payout (90%)
                    payout_amount = original_amount * Decimal(str(self.payout_rate))
                    payout_amount = payout_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    # 计算margin (10%)
                    margin_amount = original_amount * Decimal(str(self.margin_rate))
                    margin_amount = margin_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    # 存储结果
                    result['original_payouts'][currency] = float(original_amount)
                    result['calculated_payouts'][currency] = float(payout_amount)
                    result['margin_amounts'][currency] = float(margin_amount)
            
            # 计算总计（以USD为准）
            if 'usd' in result['calculated_payouts']:
                result['summary'] = {
                    'total_original_usd': result['original_payouts'].get('usd', 0),
                    'total_payout_usd': result['calculated_payouts'].get('usd', 0),
                    'total_margin_usd': result['margin_amounts'].get('usd', 0),
                    'margin_percentage': self.margin_rate * 100
                }
            
            return result
            
        except Exception as e:
            logger.error(f"佣金计算失败: {str(e)}")
            return {
                'error': str(e),
                'conversion_id': conversion_data.get('conversion_id'),
                'calculation_failed': True
            }
    
    def calculate_partner_summary(self, conversions: list) -> Dict[str, Any]:
        """
        计算Partner汇总佣金
        
        Args:
            conversions: 转化数据列表
            
        Returns:
            Partner汇总信息
        """
        partner_summary = {}
        
        for conversion in conversions:
            commission_result = self.calculate_commission(conversion)
            
            if 'calculation_failed' in commission_result:
                continue
                
            partner_name = commission_result.get('partner_name', 'UNKNOWN')
            
            if partner_name not in partner_summary:
                partner_summary[partner_name] = {
                    'partner_name': partner_name,
                    'conversion_count': 0,
                    'total_original_usd': 0,
                    'total_payout_usd': 0,
                    'total_margin_usd': 0,
                    'conversions': []
                }
            
            # 累计数据
            summary = commission_result.get('summary', {})
            partner_summary[partner_name]['conversion_count'] += 1
            partner_summary[partner_name]['total_original_usd'] += summary.get('total_original_usd', 0)
            partner_summary[partner_name]['total_payout_usd'] += summary.get('total_payout_usd', 0)
            partner_summary[partner_name]['total_margin_usd'] += summary.get('total_margin_usd', 0)
            partner_summary[partner_name]['conversions'].append(commission_result)
        
        # 计算总计
        total_summary = {
            'total_partners': len(partner_summary),
            'total_conversions': sum(p['conversion_count'] for p in partner_summary.values()),
            'total_original_usd': sum(p['total_original_usd'] for p in partner_summary.values()),
            'total_payout_usd': sum(p['total_payout_usd'] for p in partner_summary.values()),
            'total_margin_usd': sum(p['total_margin_usd'] for p in partner_summary.values()),
            'margin_rate': self.margin_rate
        }
        
        return {
            'partner_summary': partner_summary,
            'total_summary': total_summary,
            'calculated_at': datetime.now().isoformat()
        }
    
    def get_margin_report(self, conversions: list, date_range: Dict[str, str]) -> Dict[str, Any]:
        """
        生成Margin报告
        
        Args:
            conversions: 转化数据列表
            date_range: 日期范围
            
        Returns:
            Margin报告
        """
        partner_summary = self.calculate_partner_summary(conversions)
        
        report = {
            'report_info': {
                'report_type': 'margin_report',
                'date_range': date_range,
                'generated_at': datetime.now().isoformat(),
                'margin_rate': self.margin_rate
            },
            'summary': partner_summary['total_summary'],
            'partner_details': partner_summary['partner_summary'],
            'raw_data': conversions
        }
        
        return report
    
    def set_margin_rate(self, new_rate: float):
        """
        设置新的Margin比例
        
        Args:
            new_rate: 新的margin比例 (0.0 - 1.0)
        """
        if not 0.0 <= new_rate <= 1.0:
            raise ValueError("Margin rate must be between 0.0 and 1.0")
        
        self.margin_rate = new_rate
        self.payout_rate = 1.0 - new_rate
        
        logger.info(f"Margin rate updated to {new_rate:.1%}")
    
    def get_commission_config(self) -> Dict[str, Any]:
        """获取佣金配置信息"""
        return {
            'margin_rate': self.margin_rate,
            'payout_rate': self.payout_rate,
            'margin_percentage': self.margin_rate * 100,
            'payout_percentage': self.payout_rate * 100
        } 
#!/usr/bin/env python3
"""
LinkShare Conversion Report Analyzer
轉化報告分析和導出功能
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import json
import logging

logger = logging.getLogger(__name__)

class ConversionAnalyzer:
    """轉化報告分析器"""
    
    def __init__(self, orders_data: List[Dict]):
        """
        初始化分析器
        
        Args:
            orders_data: 訂單數據列表
        """
        self.orders_data = orders_data
        self.df = self._create_dataframe()
        
    def _create_dataframe(self) -> pd.DataFrame:
        """創建 pandas DataFrame"""
        if not self.orders_data:
            return pd.DataFrame()
        
        # 轉換數據
        processed_data = []
        for order in self.orders_data:
            processed_order = {
                'affiliate_order_id': order.get('affiliate_order_id', ''),
                'shop_order_id': order.get('shop_order_id', ''),
                'product_id': order.get('product_id', ''),
                'product_name': order.get('product_name', ''),
                'order_amount': float(order.get('order_amount', 0)),
                'commission_amount': float(order.get('commission_amount', 0)),
                'commission_rate': float(order.get('commission_rate', 0)),
                'order_status': order.get('order_status', ''),
                'currency': order.get('currency', 'USD'),
                'affiliate_link': order.get('affiliate_link', ''),
                'order_create_time': order.get('order_create_time', 0),
                'commission_settle_time': order.get('commission_settle_time', 0)
            }
            
            # 轉換時間戳為日期
            if processed_order['order_create_time']:
                processed_order['order_date'] = datetime.fromtimestamp(
                    processed_order['order_create_time']
                ).strftime('%Y-%m-%d')
            else:
                processed_order['order_date'] = ''
                
            if processed_order['commission_settle_time']:
                processed_order['settle_date'] = datetime.fromtimestamp(
                    processed_order['commission_settle_time']
                ).strftime('%Y-%m-%d')
            else:
                processed_order['settle_date'] = ''
            
            processed_data.append(processed_order)
        
        return pd.DataFrame(processed_data)
    
    def get_summary_statistics(self) -> Dict:
        """獲取總體統計數據"""
        if self.df.empty:
            return {
                'total_orders': 0,
                'total_amount': 0,
                'total_commission': 0,
                'average_order_value': 0,
                'average_commission': 0,
                'average_commission_rate': 0
            }
        
        summary = {
            'total_orders': len(self.df),
            'total_amount': self.df['order_amount'].sum(),
            'total_commission': self.df['commission_amount'].sum(),
            'average_order_value': self.df['order_amount'].mean(),
            'average_commission': self.df['commission_amount'].mean(),
            'average_commission_rate': self.df['commission_rate'].mean(),
            'currency': self.df['currency'].iloc[0] if len(self.df) > 0 else 'USD'
        }
        
        return summary
    
    def get_product_statistics(self) -> pd.DataFrame:
        """按產品分組統計"""
        if self.df.empty:
            return pd.DataFrame()
        
        product_stats = self.df.groupby(['product_id', 'product_name']).agg({
            'affiliate_order_id': 'count',
            'order_amount': ['sum', 'mean'],
            'commission_amount': ['sum', 'mean'],
            'commission_rate': 'mean'
        }).round(2)
        
        # flatten column names
        product_stats.columns = [
            'order_count',
            'total_amount',
            'avg_amount',
            'total_commission',
            'avg_commission',
            'avg_commission_rate'
        ]
        
        # 重置索引
        product_stats.reset_index(inplace=True)
        
        # 按總訂單金額排序
        product_stats.sort_values('total_amount', ascending=False, inplace=True)
        
        return product_stats
    
    def get_daily_statistics(self) -> pd.DataFrame:
        """按日期分組統計"""
        if self.df.empty:
            return pd.DataFrame()
        
        # 過濾掉空的日期
        df_with_dates = self.df[self.df['order_date'] != ''].copy()
        
        if df_with_dates.empty:
            return pd.DataFrame()
        
        daily_stats = df_with_dates.groupby('order_date').agg({
            'affiliate_order_id': 'count',
            'order_amount': ['sum', 'mean'],
            'commission_amount': ['sum', 'mean']
        }).round(2)
        
        # flatten column names
        daily_stats.columns = [
            'order_count',
            'total_amount',
            'avg_amount',
            'total_commission',
            'avg_commission'
        ]
        
        # 重置索引並排序
        daily_stats.reset_index(inplace=True)
        daily_stats.sort_values('order_date', inplace=True)
        
        return daily_stats
    
    def get_status_statistics(self) -> pd.DataFrame:
        """按訂單狀態分組統計"""
        if self.df.empty:
            return pd.DataFrame()
        
        status_stats = self.df.groupby('order_status').agg({
            'affiliate_order_id': 'count',
            'order_amount': 'sum',
            'commission_amount': 'sum'
        }).round(2)
        
        status_stats.columns = ['order_count', 'total_amount', 'total_commission']
        status_stats.reset_index(inplace=True)
        status_stats.sort_values('total_amount', ascending=False, inplace=True)
        
        return status_stats
    
    def export_to_excel(self, filename: str) -> bool:
        """導出到 Excel 文件"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 總體摘要
                summary = self.get_summary_statistics()
                summary_df = pd.DataFrame([summary])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # 原始數據
                if not self.df.empty:
                    self.df.to_excel(writer, sheet_name='Raw_Data', index=False)
                
                # 產品統計
                product_stats = self.get_product_statistics()
                if not product_stats.empty:
                    product_stats.to_excel(writer, sheet_name='Product_Statistics', index=False)
                
                # 日期統計
                daily_stats = self.get_daily_statistics()
                if not daily_stats.empty:
                    daily_stats.to_excel(writer, sheet_name='Daily_Statistics', index=False)
                
                # 狀態統計
                status_stats = self.get_status_statistics()
                if not status_stats.empty:
                    status_stats.to_excel(writer, sheet_name='Status_Statistics', index=False)
            
            logger.info(f"✅ Excel report exported to: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to export Excel: {e}")
            return False
    
    def export_to_csv(self, base_filename: str) -> bool:
        """導出到 CSV 文件"""
        try:
            # 原始數據
            if not self.df.empty:
                raw_filename = f"{base_filename}_raw_data.csv"
                self.df.to_csv(raw_filename, index=False)
                logger.info(f"✅ Raw data exported to: {raw_filename}")
            
            # 總體摘要
            summary = self.get_summary_statistics()
            summary_filename = f"{base_filename}_summary.csv"
            summary_df = pd.DataFrame([summary])
            summary_df.to_csv(summary_filename, index=False)
            logger.info(f"✅ Summary exported to: {summary_filename}")
            
            # 產品統計
            product_stats = self.get_product_statistics()
            if not product_stats.empty:
                product_filename = f"{base_filename}_products.csv"
                product_stats.to_csv(product_filename, index=False)
                logger.info(f"✅ Product statistics exported to: {product_filename}")
            
            # 日期統計
            daily_stats = self.get_daily_statistics()
            if not daily_stats.empty:
                daily_filename = f"{base_filename}_daily.csv"
                daily_stats.to_csv(daily_filename, index=False)
                logger.info(f"✅ Daily statistics exported to: {daily_filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to export CSV: {e}")
            return False
    
    def print_summary_report(self) -> None:
        """打印摘要報告到控制台"""
        print("\n" + "="*60)
        print("📊 LINKSHARE CONVERSION REPORT SUMMARY")
        print("="*60)
        
        # 總體統計
        summary = self.get_summary_statistics()
        print(f"\n💰 OVERALL STATISTICS:")
        print(f"   📦 Total Orders: {summary['total_orders']:,}")
        print(f"   💵 Total Amount: {summary['currency']} {summary['total_amount']:,.2f}")
        print(f"   🎯 Total Commission: {summary['currency']} {summary['total_commission']:,.2f}")
        print(f"   📈 Average Order Value: {summary['currency']} {summary['average_order_value']:,.2f}")
        print(f"   💎 Average Commission: {summary['currency']} {summary['average_commission']:,.2f}")
        print(f"   📊 Average Commission Rate: {summary['average_commission_rate']:.2%}")
        
        # 產品統計（前10）
        product_stats = self.get_product_statistics()
        if not product_stats.empty:
            print(f"\n🏆 TOP PRODUCTS (by total amount):")
            top_products = product_stats.head(10)
            for i, row in top_products.iterrows():
                print(f"   {i+1:2d}. {row['product_name'][:40]:<40} | Orders: {row['order_count']:3d} | Amount: {summary['currency']} {row['total_amount']:8,.2f}")
        
        # 日期統計（最近10天）
        daily_stats = self.get_daily_statistics()
        if not daily_stats.empty:
            print(f"\n📅 DAILY STATISTICS (recent days):")
            recent_days = daily_stats.tail(10)
            for _, row in recent_days.iterrows():
                print(f"   {row['order_date']} | Orders: {row['order_count']:3d} | Amount: {summary['currency']} {row['total_amount']:8,.2f} | Commission: {summary['currency']} {row['total_commission']:6,.2f}")
        
        # 狀態統計
        status_stats = self.get_status_statistics()
        if not status_stats.empty:
            print(f"\n📋 ORDER STATUS BREAKDOWN:")
            for _, row in status_stats.iterrows():
                print(f"   {row['order_status']:<20} | Orders: {row['order_count']:3d} | Amount: {summary['currency']} {row['total_amount']:8,.2f}")
        
        print("="*60) 
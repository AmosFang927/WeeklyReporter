#!/usr/bin/env python3
"""
分析今天的postback转化数据
"""

import subprocess
import re
from urllib.parse import unquote
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
import json

def get_today_logs():
    """获取今天的转化日志"""
    cmd = [
        'gcloud', 'logging', 'read',
        'resource.type="cloud_run_revision" AND resource.labels.service_name="bytec-public-postback" AND textPayload:"/involve/event" AND timestamp>="2025-07-09T00:00:00Z"',
        '--limit=500',
        '--freshness=24h',
        '--format=value(timestamp,textPayload)',
        '--project', 'solar-idea-463423-h8'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logs = []
        for line in result.stdout.strip().split('\n'):
            if line.strip() and '/involve/event' in line:
                logs.append(line.strip())
        return logs
    else:
        print(f"获取日志失败: {result.stderr}")
        return []

def parse_conversion_log(log_line):
    """解析转化日志"""
    # 提取时间戳
    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', log_line)
    timestamp = None
    if timestamp_match:
        timestamp = timestamp_match.group(1)
    
    # 提取URL参数
    url_pattern = r'GET /involve/event\?([^"]+)'
    match = re.search(url_pattern, log_line)
    
    if not match:
        return None
    
    query_string = match.group(1)
    params = {}
    
    for param_pair in query_string.split('&'):
        if '=' in param_pair:
            key, value = param_pair.split('=', 1)
            params[key] = unquote(value)
    
    # 解析转化数据
    try:
        conversion = {
            'timestamp': timestamp,
            'conversion_id': params.get('conversion_id', ''),
            'offer_name': params.get('offer_name', ''),
            'usd_sale_amount': float(params.get('usd_sale_amount', 0)),
            'usd_payout': float(params.get('usd_payout', 0)),
            'sub_id': params.get('sub_id', ''),
            'media_id': params.get('media_id', ''),
            'datetime_conversion': params.get('datetime_conversion', '')
        }
        return conversion
    except:
        return None

def analyze_conversions():
    """分析转化数据"""
    print("🔍 正在获取今天的转化日志...")
    logs = get_today_logs()
    print(f"📄 获取到 {len(logs)} 条日志记录")
    
    if not logs:
        print("❌ 没有找到转化日志")
        return
    
    conversions = []
    for log in logs:
        conversion = parse_conversion_log(log)
        if conversion and conversion['conversion_id']:
            conversions.append(conversion)
    
    print(f"✅ 解析出 {len(conversions)} 条转化记录")
    
    if not conversions:
        print("❌ 没有有效的转化数据")
        return
    
    # 去重（根据conversion_id）
    unique_conversions = {}
    for conv in conversions:
        conv_id = conv['conversion_id']
        if conv_id not in unique_conversions:
            unique_conversions[conv_id] = conv
    
    conversions = list(unique_conversions.values())
    print(f"🔄 去重后有 {len(conversions)} 条唯一转化记录")
    
    # 统计分析
    print("\n" + "="*60)
    print("📊 今天的转化数据统计 (2025-07-09)")
    print("="*60)
    
    # 基本统计
    total_conversions = len(conversions)
    total_sales = sum(conv['usd_sale_amount'] for conv in conversions)
    total_payout = sum(conv['usd_payout'] for conv in conversions)
    
    print(f"📈 总转化数量: {total_conversions} 笔")
    print(f"💰 总销售金额: ${total_sales:.2f}")
    print(f"💵 总佣金金额: ${total_payout:.2f}")
    print(f"📊 平均订单金额: ${total_sales/total_conversions:.2f}")
    
    # 按offer分组统计
    print("\n🏢 按Offer统计:")
    print("-"*40)
    offer_stats = defaultdict(lambda: {'count': 0, 'sales': 0, 'payout': 0})
    
    for conv in conversions:
        offer = conv['offer_name']
        offer_stats[offer]['count'] += 1
        offer_stats[offer]['sales'] += conv['usd_sale_amount']
        offer_stats[offer]['payout'] += conv['usd_payout']
    
    for offer, stats in sorted(offer_stats.items(), key=lambda x: x[1]['sales'], reverse=True):
        print(f"  {offer}:")
        print(f"    📦 订单数: {stats['count']}")
        print(f"    💰 销售额: ${stats['sales']:.2f}")
        print(f"    💵 佣金: ${stats['payout']:.2f}")
        print()
    
    # 按媒体渠道统计
    print("📱 按媒体渠道统计:")
    print("-"*40)
    media_stats = defaultdict(lambda: {'count': 0, 'sales': 0, 'payout': 0})
    
    for conv in conversions:
        media = conv['sub_id'] or 'Unknown'
        media_stats[media]['count'] += 1
        media_stats[media]['sales'] += conv['usd_sale_amount']
        media_stats[media]['payout'] += conv['usd_payout']
    
    for media, stats in sorted(media_stats.items(), key=lambda x: x[1]['sales'], reverse=True):
        print(f"  {media}:")
        print(f"    📦 订单数: {stats['count']}")
        print(f"    💰 销售额: ${stats['sales']:.2f}")
        print(f"    💵 佣金: ${stats['payout']:.2f}")
        print()
    
    # 按时间段统计
    print("⏰ 按时间段统计:")
    print("-"*40)
    hour_stats = defaultdict(lambda: {'count': 0, 'sales': 0})
    
    for conv in conversions:
        if conv['timestamp']:
            try:
                hour = datetime.fromisoformat(conv['timestamp'].replace('Z', '')).hour
                hour_stats[hour]['count'] += 1
                hour_stats[hour]['sales'] += conv['usd_sale_amount']
            except:
                pass
    
    for hour in sorted(hour_stats.keys()):
        stats = hour_stats[hour]
        print(f"  {hour:02d}:00-{hour:02d}:59  📦 {stats['count']} 笔  💰 ${stats['sales']:.2f}")
    
    # 显示最新的几笔转化
    print("\n🕐 最新转化记录 (前10笔):")
    print("-"*40)
    
    # 按时间戳排序
    sorted_conversions = sorted(conversions, 
                              key=lambda x: x['timestamp'] or '', 
                              reverse=True)
    
    for i, conv in enumerate(sorted_conversions[:10], 1):
        print(f"{i:2d}. {conv['timestamp']}")
        print(f"    ID: {conv['conversion_id']}")
        print(f"    Offer: {conv['offer_name']}")
        print(f"    金额: ${conv['usd_sale_amount']:.2f} | 佣金: ${conv['usd_payout']:.2f}")
        print(f"    渠道: {conv['sub_id']}")
        print()

def main():
    print("📈 开始分析今天的postback转化数据...")
    print("-" * 60)
    analyze_conversions()
    print("\n✅ 分析完成!")

if __name__ == "__main__":
    main() 
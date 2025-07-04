#!/bin/bash

# YueMeng报表生成脚本
# 运行多个日期的报表并显示日志输出

echo "🚀 开始生成YueMeng报表 - 多日期批量处理"
echo "=================================================================="
echo "⏰ 开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=================================================================="

# 定义日期数组
dates=("2025-06-28" "2025-06-29" "2025-06-30" "2025-07-01")

# 计数器
total_dates=${#dates[@]}
current_count=0

# 遍历每个日期
for date in "${dates[@]}"; do
    current_count=$((current_count + 1))
    
    echo ""
    echo "📅 处理日期 $current_count/$total_dates: $date"
    echo "=================================================================="
    echo "🔧 命令: python main.py --partner YueMeng --start-date $date --end-date $date"
    echo "=================================================================="
    
    # 记录开始时间
    start_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "⏰ 开始时间: $start_time"
    
    # 运行命令并捕获输出
    python main.py --partner YueMeng --start-date "$date" --end-date "$date"
    exit_code=$?
    
    # 记录结束时间
    end_time=$(date '+%Y-%m-%d %H:%M:%S')
    echo "⏰ 结束时间: $end_time"
    
    # 检查执行结果
    if [ $exit_code -eq 0 ]; then
        echo "✅ 日期 $date 处理成功"
    else
        echo "❌ 日期 $date 处理失败 (退出码: $exit_code)"
    fi
    
    echo "=================================================================="
    
    # 如果不是最后一个日期，添加分隔和短暂延迟
    if [ $current_count -lt $total_dates ]; then
        echo "⏳ 准备处理下一个日期..."
        sleep 2
    fi
done

echo ""
echo "🎉 所有YueMeng报表处理完成!"
echo "=================================================================="
echo "📊 处理总结:"
echo "   • 总共处理日期数: $total_dates"
echo "   • 处理的日期: ${dates[*]}"
echo "   • 完成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "==================================================================" 
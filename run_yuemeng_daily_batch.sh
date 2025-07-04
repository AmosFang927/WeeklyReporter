#!/bin/bash
# YueMeng 合作伙伴日维度批次处理脚本 (逐日手动执行版本)
# 日期范围: 2025-06-01 到 2025-06-20 (共20天)
# 使用方法: chmod +x run_yuemeng_daily_batch.sh && ./run_yuemeng_daily_batch.sh

echo "🚀 YueMeng 日维度逐日处理工具"
echo "📅 日期范围: 2025-06-01 到 2025-06-20 (共20天)"
echo "🔄 模式: 逐日手动执行"
echo "========================================================"

# 定义日期数组
dates=(
    "2025-06-01"
    "2025-06-02"
    "2025-06-03"
    "2025-06-04"
    "2025-06-05"
    "2025-06-06"
    "2025-06-07"
    "2025-06-08"
    "2025-06-09"
    "2025-06-10"
    "2025-06-11"
    "2025-06-12"
    "2025-06-13"
    "2025-06-14"
    "2025-06-15"
    "2025-06-16"
    "2025-06-17"
    "2025-06-18"
    "2025-06-19"
    "2025-06-20"
)

# 初始化统计
total_days=${#dates[@]}
success_count=0
failed_count=0
current_day=1

echo ""
echo "📋 可用日期列表:"
for i in "${!dates[@]}"; do
    day_num=$((i + 1))
    echo "   $day_num. ${dates[$i]}"
done

echo ""
echo "🎯 使用方法:"
echo "   - 输入日期编号 (1-20) 执行指定日期"
echo "   - 输入 'next' 或 'n' 执行下一个未处理的日期"
echo "   - 输入 'list' 或 'l' 显示所有日期"
echo "   - 输入 'status' 或 's' 显示处理状态"
echo "   - 输入 'exit' 或 'q' 退出脚本"

# 跟踪已处理的日期
declare -a processed_dates=()

while true; do
    echo ""
    echo "========================================================"
    echo "📊 当前状态: 成功 $success_count 天, 失败 $failed_count 天"
    echo "🎯 请选择要执行的操作:"
    read -p "输入命令 (1-20/next/list/status/exit): " user_input

    case $user_input in
        [1-9]|1[0-9]|20)
            # 执行指定日期
            day_index=$((user_input - 1))
            if [ $day_index -ge 0 ] && [ $day_index -lt $total_days ]; then
                selected_date="${dates[$day_index]}"
                
                echo ""
                echo "📊 执行第 $user_input/$total_days 天: $selected_date"
                echo "----------------------------------------"
                
                # 检查是否已经处理过
                if [[ " ${processed_dates[@]} " =~ " $selected_date " ]]; then
                    echo "⚠️  日期 $selected_date 已经处理过了"
                    read -p "是否重新处理? (y/n): " retry_choice
                    if [[ "$retry_choice" != "y" && "$retry_choice" != "Y" ]]; then
                        continue
                    fi
                fi
                
                # 执行命令
                if python main.py --partner YueMeng --start-date "$selected_date" --end-date "$selected_date" --save-json; then
                    echo "✅ $selected_date 处理成功"
                    if [[ ! " ${processed_dates[@]} " =~ " $selected_date " ]]; then
                        ((success_count++))
                        processed_dates+=("$selected_date")
                    fi
                else
                    echo "❌ $selected_date 处理失败"
                    if [[ ! " ${processed_dates[@]} " =~ " $selected_date " ]]; then
                        ((failed_count++))
                        processed_dates+=("$selected_date")
                    fi
                fi
            else
                echo "❌ 无效的日期编号，请输入 1-20"
            fi
            ;;
        
        "next"|"n")
            # 执行下一个未处理的日期
            next_found=false
            for i in "${!dates[@]}"; do
                date="${dates[$i]}"
                if [[ ! " ${processed_dates[@]} " =~ " $date " ]]; then
                    day_num=$((i + 1))
                    echo ""
                    echo "📊 执行下一个日期 - 第 $day_num/$total_days 天: $date"
                    echo "----------------------------------------"
                    
                    # 执行命令
                    if python main.py --partner YueMeng --start-date "$date" --end-date "$date" --save-json; then
                        echo "✅ $date 处理成功"
                        ((success_count++))
                        processed_dates+=("$date")
                    else
                        echo "❌ $date 处理失败"
                        ((failed_count++))
                        processed_dates+=("$date")
                    fi
                    next_found=true
                    break
                fi
            done
            
            if [ "$next_found" = false ]; then
                echo "🎉 所有日期都已处理完成！"
            fi
            ;;
        
        "list"|"l")
            # 显示所有日期和状态
            echo ""
            echo "📋 所有日期状态:"
            for i in "${!dates[@]}"; do
                day_num=$((i + 1))
                date="${dates[$i]}"
                if [[ " ${processed_dates[@]} " =~ " $date " ]]; then
                    echo "   $day_num. $date ✅ (已处理)"
                else
                    echo "   $day_num. $date ⏳ (待处理)"
                fi
            done
            ;;
        
        "status"|"s")
            # 显示处理状态
            echo ""
            echo "📊 处理状态报告:"
            echo "✅ 成功处理: $success_count 天"
            echo "❌ 失败处理: $failed_count 天"
            echo "⏳ 待处理: $((total_days - ${#processed_dates[@]})) 天"
            echo "📁 输出文件位置: ./output/"
            ;;
        
        "exit"|"q")
            echo ""
            echo "========================================================"
            echo "📋 最终处理报告:"
            echo "✅ 成功处理: $success_count 天"
            echo "❌ 失败处理: $failed_count 天"
            echo "📁 输出文件位置: ./output/"
            echo "⏰ 退出时间: $(date)"
            echo "========================================================"
            echo "👋 感谢使用 YueMeng 日维度处理工具！"
            break
            ;;
        
        *)
            echo "❌ 无效命令。请输入 1-20, next, list, status, 或 exit"
            ;;
    esac
done
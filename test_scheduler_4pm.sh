#!/bin/bash

# WeeklyReporter - Cloud Scheduler 测试脚本 (4PM版本)
# 测试每天下午4点的调度任务

set -e

echo "🧪 WeeklyReporter Cloud Scheduler 测试 - 4PM版本"
echo "=" * 60

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
LOCATION="asia-east1"
JOB_NAME="weeklyreporter-daily-4pm"
CLOUD_RUN_URL="https://weeklyreporter-crwdeesavq-de.a.run.app"

echo "📋 测试配置："
echo "  项目ID: $PROJECT_ID"
echo "  位置: $LOCATION"
echo "  任务名称: $JOB_NAME"
echo "  目标合作伙伴: RAMPUP, YueMeng"
echo "  数据范围: 昨天"
echo ""

# 功能1：检查 Cloud Scheduler 任务状态
test_scheduler_status() {
    echo "🔍 测试1: 检查 Cloud Scheduler 任务状态"
    echo "=" * 40
    
    if gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID >/dev/null 2>&1; then
        echo "✅ Cloud Scheduler 任务存在"
        
        # 获取任务详情
        echo ""
        echo "📊 任务详情："
        gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID
        
        # 检查任务状态
        status=$(gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID --format="value(state)")
        echo ""
        echo "📅 任务状态: $status"
        
        if [ "$status" = "ENABLED" ]; then
            echo "✅ 任务已启用，将按计划执行"
        else
            echo "⚠️  任务状态: $status"
        fi
    else
        echo "❌ Cloud Scheduler 任务不存在"
        echo "💡 请先运行: ./setup_cloud_scheduler_4pm.sh"
        return 1
    fi
}

# 功能2：测试 Cloud Run 服务连接
test_cloud_run() {
    echo ""
    echo "🌐 测试2: 检查 Cloud Run 服务连接"
    echo "=" * 40
    
    echo "🔗 测试 Cloud Run 健康检查..."
    if curl -s -f "$CLOUD_RUN_URL/health" >/dev/null 2>&1; then
        echo "✅ Cloud Run 服务响应正常"
        
        # 获取服务信息
        response=$(curl -s "$CLOUD_RUN_URL/health" 2>/dev/null || echo "无法获取响应")
        echo "📡 健康检查响应: $response"
    else
        echo "❌ Cloud Run 服务无响应"
        echo "💡 请检查 Cloud Run 服务状态"
        return 1
    fi
}

# 功能3：手动触发测试
test_manual_trigger() {
    echo ""
    echo "🚀 测试3: 手动触发调度任务"
    echo "=" * 40
    
    echo "⚠️  即将手动触发调度任务，这将执行实际的数据处理流程"
    echo "📋 处理范围: RAMPUP, YueMeng 合作伙伴（昨天数据）"
    echo ""
    read -p "是否继续手动触发？(y/N): " confirm
    
    if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
        echo "🎯 正在手动触发任务..."
        
        if gcloud scheduler jobs run $JOB_NAME --location=$LOCATION --project=$PROJECT_ID; then
            echo "✅ 任务触发成功"
            echo "📝 任务已提交到队列，正在执行..."
            
            # 等待一段时间后检查执行状态
            echo "⏳ 等待 30 秒后检查执行状态..."
            sleep 30
            
            echo "📊 最近执行记录："
            gcloud logging read "resource.type=\"cloud_scheduler_job\" AND resource.labels.job_id=\"$JOB_NAME\"" \
                --limit=5 --format="table(timestamp, severity, textPayload)" \
                --project=$PROJECT_ID || echo "暂无日志记录"
        else
            echo "❌ 任务触发失败"
            return 1
        fi
    else
        echo "🚫 已取消手动触发"
    fi
}

# 功能4：查看执行历史
test_execution_history() {
    echo ""
    echo "📚 测试4: 查看执行历史"
    echo "=" * 40
    
    echo "📊 最近5次执行记录："
    gcloud logging read "resource.type=\"cloud_scheduler_job\" AND resource.labels.job_id=\"$JOB_NAME\"" \
        --limit=5 --format="table(timestamp, severity, textPayload)" \
        --project=$PROJECT_ID || echo "暂无历史记录"
}

# 功能5：验证生成的文件
test_output_files() {
    echo ""
    echo "📁 测试5: 检查本地输出文件"
    echo "=" * 40
    
    if [ -d "output" ]; then
        echo "📂 output 目录存在"
        
        # 查找最近的 Excel 文件
        recent_files=$(find output -name "*.xlsx" -mtime -1 2>/dev/null | head -5)
        
        if [ -n "$recent_files" ]; then
            echo "✅ 发现最近生成的 Excel 文件："
            echo "$recent_files" | while read file; do
                if [ -f "$file" ]; then
                    size=$(ls -lh "$file" | awk '{print $5}')
                    modified=$(ls -l "$file" | awk '{print $6, $7, $8}')
                    echo "  📄 $file (大小: $size, 修改时间: $modified)"
                fi
            done
        else
            echo "⚠️  output 目录中未发现最近的 Excel 文件"
        fi
    else
        echo "⚠️  output 目录不存在"
    fi
}

# 主测试流程
main() {
    # 运行所有测试
    test_scheduler_status
    test_cloud_run
    test_execution_history
    test_output_files
    test_manual_trigger
    
    echo ""
    echo "🎉 测试完成！"
    echo "=" * 60
    echo "📅 下次自动执行时间: 今天或明天下午4点 (北京时间)"
    echo ""
    echo "🔧 常用管理命令："
    echo "  查看任务状态: gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID"
    echo "  手动触发任务: gcloud scheduler jobs run $JOB_NAME --location=$LOCATION --project=$PROJECT_ID"
    echo "  查看执行日志: gcloud logging read 'resource.type=\"cloud_scheduler_job\" AND resource.labels.job_id=\"$JOB_NAME\"' --limit=10"
    echo "  暂停任务: gcloud scheduler jobs pause $JOB_NAME --location=$LOCATION --project=$PROJECT_ID"
    echo "  恢复任务: gcloud scheduler jobs resume $JOB_NAME --location=$LOCATION --project=$PROJECT_ID"
    echo "  删除任务: gcloud scheduler jobs delete $JOB_NAME --location=$LOCATION --project=$PROJECT_ID"
}

# 执行主流程
main 
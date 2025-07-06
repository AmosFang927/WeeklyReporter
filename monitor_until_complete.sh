#!/bin/bash
# reporter-agent 持续监控脚本
# 持续监听日志直到Cloud Run服务任务完成

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"
SERVICE_URL="https://reporter-agent-472712465571.asia-southeast1.run.app"

echo "🔄 reporter-agent 持续监控"
echo "=========================="
echo "🏷️ 服务: $SERVICE_NAME"
echo "📍 区域: $REGION"
echo "🔍 项目: $PROJECT_ID"
echo "🌐 服务URL: $SERVICE_URL"
echo ""
echo "📊 监控模式: 持续监听直到任务完成"
echo "💡 按 Ctrl+C 手动停止"
echo ""

# 设置项目
gcloud config set project $PROJECT_ID --quiet

# 检查任务状态函数
check_task_status() {
    local status_response=$(curl -s "$SERVICE_URL/tasks" 2>/dev/null)
    if [ $? -eq 0 ] && [ ! -z "$status_response" ]; then
        echo "$status_response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for task in data.get('tasks', []):
        if task.get('status') == 'running':
            print('running')
            exit(0)
    print('completed')
except:
    print('unknown')
" 2>/dev/null || echo "unknown"
    else
        echo "unknown"
    fi
}

# 显示任务状态函数
show_task_status() {
    local status_response=$(curl -s "$SERVICE_URL/tasks" 2>/dev/null)
    if [ $? -eq 0 ] && [ ! -z "$status_response" ]; then
        echo "$status_response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'📊 任务状态: 总共 {data.get(\"total\", 0)} 个任务')
    for task in data.get('tasks', []):
        status = task.get('status', 'unknown')
        task_id = task.get('id', 'unknown')
        progress = task.get('progress', 'no info')
        print(f'   🔍 {task_id}: {status} - {progress}')
except:
    print('   ❌ 无法获取任务状态')
" 2>/dev/null || echo "   ❌ 无法获取任务状态"
    else
        echo "   ❌ 服务连接失败"
    fi
}

# 主监控循环
LAST_TIMESTAMP=""
LAST_STATUS_CHECK=0
CHECK_INTERVAL=30  # 每30秒检查一次任务状态

echo "🔍 实时日志输出:"
echo "================================"

while true; do
    # 定期检查任务状态
    CURRENT_TIME=$(date +%s)
    if [ $((CURRENT_TIME - LAST_STATUS_CHECK)) -gt $CHECK_INTERVAL ]; then
        echo ""
        echo "📋 [$( date )] 任务状态检查:"
        show_task_status
        
        # 检查是否有正在运行的任务
        TASK_STATUS=$(check_task_status)
        if [ "$TASK_STATUS" = "completed" ]; then
            echo ""
            echo "✅ 所有任务已完成！监控结束。"
            break
        elif [ "$TASK_STATUS" = "unknown" ]; then
            echo "⚠️  任务状态未知，继续监控..."
        fi
        
        echo "================================"
        LAST_STATUS_CHECK=$CURRENT_TIME
    fi
    
    # 获取最新的日志条目
    CURRENT_LOGS=$(gcloud logging read \
      "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
      --limit=15 \
      --freshness=1m \
      --format="value(timestamp,severity,textPayload)" \
      --project=$PROJECT_ID 2>/dev/null)
    
    if [ ! -z "$CURRENT_LOGS" ]; then
        # 显示新的日志条目
        echo "$CURRENT_LOGS" | while IFS=$'\t' read -r timestamp severity message; do
            if [ ! -z "$timestamp" ] && [ "$timestamp" != "$LAST_TIMESTAMP" ]; then
                echo "[$timestamp] $severity: $message"
            fi
        done
        
        # 更新最后时间戳
        LAST_TIMESTAMP=$(echo "$CURRENT_LOGS" | head -1 | cut -f1)
    fi
    
    # 等待3秒后再次检查
    sleep 3
done

echo ""
echo "🎉 监控完成！"
echo "📊 最终任务状态:"
show_task_status 
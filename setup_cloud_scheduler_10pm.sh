#!/bin/bash

# Cloud Scheduler 设置脚本
# 每日晚上10:08执行WeeklyReporter任务
# Partners: RAMPUP, YueMeng
# Date Range: yesterday
# Limit: 100条记录

set -e

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
LOCATION="asia-east1"
JOB_NAME="weeklyreporter-daily"
SERVICE_URL="https://weeklyreporter-crwdeesavq-de.a.run.app"
SCHEDULE="8 22 * * *"  # 每日10:08 PM
TIMEZONE="Asia/Shanghai"

echo "🚀 正在设置 Cloud Scheduler 任务..."
echo "📅 执行时间: 每日晚上10:08 (北京时间)"
echo "🎯 目标服务: $SERVICE_URL"
echo "📋 Partners: RAMPUP, YueMeng"
echo "📊 限制: 100条记录"
echo "=" * 50

# 准备JSON消息体
MESSAGE_BODY='{
  "partners": ["RAMPUP", "YueMeng"],
  "date_range": "yesterday",
  "limit": 100,
  "save_json": true,
  "upload_feishu": true,
  "send_email": true,
  "trigger": "scheduler",
  "description": "Daily automated run for RAMPUP and YueMeng partners"
}'

# 检查是否已存在任务
echo "🔍 检查现有的 Cloud Scheduler 任务..."
if gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "⚠️  任务 '$JOB_NAME' 已存在，将进行更新..."
    
    # 更新现有任务
    gcloud scheduler jobs update http $JOB_NAME \
        --schedule="$SCHEDULE" \
        --uri="$SERVICE_URL/run" \
        --update-headers="Content-Type=application/json" \
        --message-body="$MESSAGE_BODY" \
        --location=$LOCATION \
        --project=$PROJECT_ID \
        --time-zone=$TIMEZONE \
        --description="Daily WeeklyReporter execution at 10:08 PM with RAMPUP and YueMeng partners"
    
    echo "✅ Cloud Scheduler 任务已更新成功！"
else
    echo "📝 创建新的 Cloud Scheduler 任务..."
    
    # 创建新任务
    gcloud scheduler jobs create http $JOB_NAME \
        --schedule="$SCHEDULE" \
        --uri="$SERVICE_URL/run" \
        --http-method=POST \
        --location=$LOCATION \
        --project=$PROJECT_ID \
        --time-zone=$TIMEZONE \
        --description="Daily WeeklyReporter execution at 10:08 PM with RAMPUP and YueMeng partners" \
        --headers="Content-Type=application/json" \
        --message-body="$MESSAGE_BODY"
    
    echo "✅ Cloud Scheduler 任务创建成功！"
fi

echo ""
echo "📋 任务详情:"
echo "  名称: $JOB_NAME"
echo "  执行时间: 每日 10:08 PM (北京时间)"
echo "  目标URL: $SERVICE_URL/run"
echo "  Partners: RAMPUP, YueMeng"
echo "  数据范围: 昨天"
echo "  记录限制: 100条"

echo ""
echo "🔧 管理命令:"
echo "  查看任务状态: gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION"
echo "  手动触发任务: gcloud scheduler jobs run $JOB_NAME --location=$LOCATION"
echo "  查看执行历史: gcloud logging read 'resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME' --limit=10"
echo "  暂停任务: gcloud scheduler jobs pause $JOB_NAME --location=$LOCATION"
echo "  恢复任务: gcloud scheduler jobs resume $JOB_NAME --location=$LOCATION"
echo "  删除任务: gcloud scheduler jobs delete $JOB_NAME --location=$LOCATION"

echo ""
echo "🧪 测试建议:"
echo "  1. 手动触发测试: ./test_scheduler_10pm.sh"
echo "  2. 查看实时日志: gcloud logs tail --filter='resource.type=cloud_run_revision'"
echo "  3. 测试日志输出: curl -X GET $SERVICE_URL/test-logging"

echo ""
echo "⏰ 下次执行时间:"
gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --format="value(schedule)" 2>/dev/null | \
    python3 -c "
import sys
from datetime import datetime, timedelta
import re

try:
    schedule = sys.stdin.read().strip()
    if schedule:
        # 解析cron表达式 '0 22 * * *'
        parts = schedule.split()
        if len(parts) >= 2:
            minute = int(parts[0])
            hour = int(parts[1])
            
            now = datetime.now()
            today_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if today_run > now:
                next_run = today_run
            else:
                next_run = today_run + timedelta(days=1)
            
            print(f'  {next_run.strftime(\"%Y-%m-%d %H:%M:%S\")} (北京时间)')
        else:
            print('  无法解析执行时间')
    else:
        print('  任务可能不存在')
except:
    print('  计算中...')
"

echo ""
echo "🎉 Cloud Scheduler 设置完成！"
echo "📅 任务将在每天晚上10:08(北京时间)自动执行" 
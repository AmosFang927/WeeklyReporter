#!/bin/bash

# Cloud Scheduler 执行验证脚本
# 用于检查任务是否正确执行且无错误

set -e

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
LOCATION="asia-east1"
JOB_NAME="weeklyreporter-daily"
SERVICE_URL="https://weeklyreporter-crwdeesavq-de.a.run.app"

echo "🔍 Cloud Scheduler 执行状态验证"
echo "============================================================"

# 1. 检查任务基本状态
echo ""
echo "📋 1. 检查任务基本状态..."
gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --format="table(
    name.scope(jobs):label=NAME,
    state:label=STATE,
    schedule:label=SCHEDULE,
    lastAttemptTime:label=LAST_ATTEMPT,
    timeZone:label=TIMEZONE
)"

# 获取任务状态
JOB_STATE=$(gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --format="value(state)" 2>/dev/null)
LAST_ATTEMPT=$(gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --format="value(lastAttemptTime)" 2>/dev/null)

if [[ "$JOB_STATE" == "ENABLED" ]]; then
    echo "✅ 任务状态: $JOB_STATE"
else
    echo "❌ 任务状态异常: $JOB_STATE"
fi

# 2. 检查最近的Scheduler执行记录
echo ""
echo "📊 2. 检查最近的Scheduler执行记录..."
echo "最近5次执行记录:"

gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME" \
    --limit=5 \
    --format="table(timestamp.date('%Y-%m-%d %H:%M:%S'):label=TIME,severity:label=LEVEL,httpRequest.status:label=HTTP_STATUS)" \
    --project=$PROJECT_ID

# 3. 检查是否有执行错误
echo ""
echo "⚠️  3. 检查执行错误..."
ERROR_COUNT=$(gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME AND severity>=ERROR" \
    --limit=5 \
    --format="value(timestamp)" \
    --project=$PROJECT_ID | wc -l)

if [[ $ERROR_COUNT -eq 0 ]]; then
    echo "✅ 最近5次执行无错误记录"
else
    echo "❌ 发现 $ERROR_COUNT 个错误记录:"
    gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME AND severity>=ERROR" \
        --limit=3 \
        --format="table(timestamp.date('%Y-%m-%d %H:%M:%S'):label=TIME,severity:label=LEVEL,textPayload:label=ERROR_MESSAGE)" \
        --project=$PROJECT_ID
fi

# 4. 检查Cloud Run应用日志
echo ""
echo "🚀 4. 检查Cloud Run应用执行日志..."

# 查找最近的Cloud Scheduler触发的日志
echo "查找最近包含'Cloud Scheduler'标记的日志:"
RECENT_LOGS=$(gcloud logging read 'resource.type=cloud_run_revision AND (textPayload:"Cloud Scheduler" OR textPayload:"[Cloud Scheduler]")' \
    --limit=10 \
    --format="value(timestamp,textPayload)" \
    --project=$PROJECT_ID)

if [[ -n "$RECENT_LOGS" ]]; then
    echo "✅ 找到Cloud Run执行日志:"
    echo "$RECENT_LOGS" | head -10
else
    echo "⚠️  未找到Cloud Scheduler触发的应用日志"
    echo "检查最近的Cloud Run日志:"
    gcloud logging read 'resource.type=cloud_run_revision' \
        --limit=5 \
        --format="table(timestamp.date('%Y-%m-%d %H:%M:%S'):label=TIME,severity:label=LEVEL,textPayload:label=MESSAGE)" \
        --project=$PROJECT_ID
fi

# 5. 检查HTTP响应状态
echo ""
echo "🌐 5. 检查HTTP响应状态..."

# 获取最近的HTTP状态码
HTTP_STATUS=$(gcloud logging read "resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME" \
    --limit=1 \
    --format="value(httpRequest.status)" \
    --project=$PROJECT_ID)

if [[ "$HTTP_STATUS" == "200" ]]; then
    echo "✅ 最近执行HTTP状态: $HTTP_STATUS (成功)"
elif [[ -n "$HTTP_STATUS" ]]; then
    echo "❌ 最近执行HTTP状态: $HTTP_STATUS (可能有问题)"
else
    echo "⚠️  未找到HTTP状态信息"
fi

# 6. 测试Cloud Run服务可用性
echo ""
echo "🔧 6. 测试Cloud Run服务当前状态..."

if curl -s --max-time 10 "$SERVICE_URL/health" > /dev/null; then
    echo "✅ Cloud Run服务当前可访问"
    HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health")
    echo "服务状态: $HEALTH_RESPONSE"
else
    echo "❌ Cloud Run服务当前不可访问"
fi

# 7. 检查下次执行时间
echo ""
echo "⏰ 7. 下次执行时间..."

NEXT_SCHEDULE=$(gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --format="value(scheduleTime)" 2>/dev/null)
if [[ -n "$NEXT_SCHEDULE" ]]; then
    echo "下次计划执行: $NEXT_SCHEDULE"
    # 转换为北京时间
    python3 -c "
import sys
from datetime import datetime
import pytz

schedule_time = '$NEXT_SCHEDULE'
if schedule_time:
    dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = dt.astimezone(beijing_tz)
    print(f'北京时间: {beijing_time.strftime(\"%Y-%m-%d %H:%M:%S\")}')
"
else
    echo "⚠️  未找到下次执行时间"
fi

# 8. 总结
echo ""
echo "📋 8. 执行状态总结"
echo "========================================"

# 汇总状态
SUMMARY_STATUS="正常"
SUMMARY_ISSUES=()

if [[ "$JOB_STATE" != "ENABLED" ]]; then
    SUMMARY_STATUS="异常"
    SUMMARY_ISSUES+=("任务状态异常")
fi

if [[ $ERROR_COUNT -gt 0 ]]; then
    SUMMARY_STATUS="有警告"
    SUMMARY_ISSUES+=("发现执行错误")
fi

if [[ "$HTTP_STATUS" != "200" && -n "$HTTP_STATUS" ]]; then
    SUMMARY_STATUS="有警告"
    SUMMARY_ISSUES+=("HTTP状态异常")
fi

echo "总体状态: $SUMMARY_STATUS"

if [[ ${#SUMMARY_ISSUES[@]} -gt 0 ]]; then
    echo "发现的问题:"
    for issue in "${SUMMARY_ISSUES[@]}"; do
        echo "  - $issue"
    done
else
    echo "✅ 所有检查项目正常"
fi

echo ""
echo "🔧 故障排除建议:"
echo "  1. 手动触发测试: gcloud scheduler jobs run $JOB_NAME --location=$LOCATION"
echo "  2. 查看实时日志: gcloud logs tail --filter='resource.type=cloud_run_revision'"
echo "  3. 检查服务状态: curl $SERVICE_URL/health"
echo "  4. 查看详细错误: gcloud logging read 'resource.type=cloud_scheduler_job AND severity>=ERROR' --limit=10"

echo ""
echo "📊 监控命令:"
echo "  重新运行验证: ./verify_scheduler_execution.sh"
echo "  监控实时日志: gcloud logs tail --filter='resource.type=cloud_run_revision OR resource.type=cloud_scheduler_job'"
echo "  查看任务状态: gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION"

echo ""
echo "🎉 验证完成！" 
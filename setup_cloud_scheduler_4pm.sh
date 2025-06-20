#!/bin/bash

# WeeklyReporter - Google Cloud Scheduler 设置脚本
# 配置每天下午4点自动运行，只处理 RAMPUP 和 YueMeng 合作伙伴
# 数据范围：昨天

set -e

echo "🚀 正在设置 WeeklyReporter Cloud Scheduler - 每日下午4点执行"
echo "=" * 60

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
LOCATION="asia-east1"
JOB_NAME="weeklyreporter-daily-4pm"
CLOUD_RUN_URL="https://weeklyreporter-crwdeesavq-de.a.run.app/run"
SCHEDULE="0 16 * * *"  # 每天下午4点
TIMEZONE="Asia/Shanghai"

# JSON 请求体 - 只处理 RAMPUP 和 YueMeng
MESSAGE_BODY='{
  "partners": ["RAMPUP", "YueMeng"],
  "date_range": "yesterday",
  "limit": 1000,
  "save_json": true,
  "upload_feishu": true,
  "send_email": true,
  "trigger": "scheduler",
  "description": "Daily 4PM automated run for RAMPUP and YueMeng partners"
}'

echo "📋 配置信息："
echo "  项目ID: $PROJECT_ID"
echo "  位置: $LOCATION"
echo "  任务名称: $JOB_NAME"
echo "  执行时间: 每天下午4点 (北京时间)"
echo "  目标合作伙伴: RAMPUP, YueMeng"
echo "  数据范围: 昨天"
echo "  Cloud Run URL: $CLOUD_RUN_URL"
echo ""

# 检查是否已存在同名任务
echo "🔍 检查是否已存在任务..."
if gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID >/dev/null 2>&1; then
    echo "⚠️  任务 '$JOB_NAME' 已存在，将删除旧任务并创建新任务..."
    gcloud scheduler jobs delete $JOB_NAME \
        --location=$LOCATION \
        --project=$PROJECT_ID \
        --quiet
    echo "✅ 已删除旧任务"
fi

# 创建新的 Cloud Scheduler 任务
echo "📅 正在创建新的 Cloud Scheduler 任务..."
gcloud scheduler jobs create http $JOB_NAME \
    --project=$PROJECT_ID \
    --location=$LOCATION \
    --schedule="$SCHEDULE" \
    --uri="$CLOUD_RUN_URL" \
    --http-method=POST \
    --time-zone="$TIMEZONE" \
    --description="Daily WeeklyReporter execution at 4 PM with RAMPUP and YueMeng partners" \
    --headers="Content-Type=application/json" \
    --message-body="$MESSAGE_BODY"

echo "✅ Cloud Scheduler 任务创建成功！"
echo ""

# 显示任务详情
echo "📊 任务详情："
gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID

echo ""
echo "🎯 任务配置完成！"
echo "=" * 60
echo "📅 调度信息："
echo "  • 任务名称: $JOB_NAME"
echo "  • 执行时间: 每天下午4点 (北京时间)"
echo "  • 目标合作伙伴: RAMPUP, YueMeng"
echo "  • 数据范围: 昨天"
echo "  • 下次运行: 今天或明天下午4点"
echo ""
echo "🔧 管理命令："
echo "  手动触发: gcloud scheduler jobs run $JOB_NAME --location=$LOCATION --project=$PROJECT_ID"
echo "  查看状态: gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID"
echo "  查看日志: gcloud logging read 'resource.type=\"cloud_scheduler_job\" AND resource.labels.job_id=\"$JOB_NAME\"' --limit=10"
echo "  删除任务: gcloud scheduler jobs delete $JOB_NAME --location=$LOCATION --project=$PROJECT_ID"
echo ""
echo "🚀 设置完成！任务将自动在每天下午4点执行。" 
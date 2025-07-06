#!/bin/bash
# Cloud Scheduler 设置脚本 - reporter-agent
# 每天晚上10:20执行WeeklyReporter任务

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_URL="https://reporter-agent-crwdeesavq-as.a.run.app"
LOCATION="asia-southeast1"
JOB_NAME="reporter-agent-daily"
SCHEDULE="0 8 * * *"  # 每天上午8:00 (新加坡时间)
TIMEZONE="Asia/Singapore"

echo "⏰ 设置 Cloud Scheduler - reporter-agent 每日定时任务"
echo "=================================================="
echo "📋 配置信息:"
echo "  项目ID: $PROJECT_ID"
echo "  服务URL: $SERVICE_URL"
echo "  任务名称: $JOB_NAME"
echo "  执行时间: 每天上午8:00 (新加坡时间)"
echo "  时区: $TIMEZONE"
echo "  位置: $LOCATION"
echo ""

# 检查 gcloud 设置
echo "🔧 设置 GCP 项目..."
gcloud config set project $PROJECT_ID

# 启用必要的 API
echo "🔧 启用 Cloud Scheduler API..."
gcloud services enable cloudscheduler.googleapis.com --quiet

# 检查是否已存在同名任务
echo "🔍 检查现有定时任务..."
existing_job=$(gcloud scheduler jobs list --location=$LOCATION --filter="name:$JOB_NAME" --format="value(name)" 2>/dev/null)

if [ ! -z "$existing_job" ]; then
    echo "⚠️  发现已存在的任务: $JOB_NAME"
    echo "🗑️  删除现有任务..."
    gcloud scheduler jobs delete $JOB_NAME \
        --location=$LOCATION \
        --quiet
    
    if [ $? -eq 0 ]; then
        echo "✅ 现有任务已删除"
    else
        echo "❌ 删除现有任务失败"
        exit 1
    fi
fi

# 创建新的定时任务
echo "🚀 创建新的定时任务..."

# 请求体 - 包含完整的WeeklyReporter配置
REQUEST_BODY='{
  "partners": ["RAMPUP"],
  "days_ago": 2,
  "save_json": true,
  "upload_feishu": true,
  "send_email": true,
  "trigger": "scheduler",
  "description": "Daily automated run for RAMPUP partner - 2 days ago data"
}'

echo "📝 请求体内容:"
echo "$REQUEST_BODY"
echo ""

# 创建 Cloud Scheduler 任务
gcloud scheduler jobs create http $JOB_NAME \
    --schedule="$SCHEDULE" \
    --uri="$SERVICE_URL/run" \
    --http-method=POST \
    --location=$LOCATION \
    --time-zone=$TIMEZONE \
    --description="Daily WeeklyReporter execution at 8:00 AM Singapore time" \
    --headers="Content-Type=application/json" \
    --message-body="$REQUEST_BODY"

if [ $? -eq 0 ]; then
    echo "✅ Cloud Scheduler任务创建成功！"
    echo ""
    echo "📋 任务详情:"
    echo "   任务名称: $JOB_NAME"
    echo "   执行时间: 每天上午8:00 (Asia/Singapore)"
    echo "   处理Partners: RAMPUP"
    echo "   数据范围: 2天前"
    echo "   数据限制: 无限制"
    echo "   邮件发送: ✅ 启用"
    echo "   飞书上传: ✅ 启用"
    echo "   JSON保存: ✅ 启用"
    echo ""
    
    # 显示任务详细信息
    echo "📊 任务详细信息:"
    gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION
    echo ""
    
    echo "🎉 设置完成！reporter-agent将每天上午8:00自动运行。"
    echo ""
    echo "🧪 手动测试任务:"
    echo "   gcloud scheduler jobs run $JOB_NAME --location=$LOCATION"
    echo ""
    echo "📝 管理命令:"
    echo "   查看任务列表: gcloud scheduler jobs list --location=$LOCATION"
    echo "   查看任务详情: gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION"
    echo "   手动触发: gcloud scheduler jobs run $JOB_NAME --location=$LOCATION"
    echo "   删除任务: gcloud scheduler jobs delete $JOB_NAME --location=$LOCATION"
    echo ""
else
    echo "❌ Cloud Scheduler任务创建失败！"
    exit 1
fi 
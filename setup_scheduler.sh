#!/bin/bash

echo "⏰ 设置 Cloud Scheduler - WeeklyReporter 每日定时任务"
echo "=================================================="

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
SERVICE_URL="https://weeklyreporter-472712465571.asia-east1.run.app"
LOCATION="asia-east1"
JOB_NAME="weeklyreporter-daily"
SCHEDULE="0 12 * * *"  # 每天中午12点
TIMEZONE="Asia/Shanghai"

echo "📋 配置信息:"
echo "  项目ID: $PROJECT_ID"
echo "  服务URL: $SERVICE_URL"
echo "  任务名称: $JOB_NAME"
echo "  执行时间: 每天中午12:00 (北京时间)"
echo "  时区: $TIMEZONE"
echo "  位置: $LOCATION"
echo ""

# 检查 gcloud 是否已安装和认证
if ! command -v gcloud &> /dev/null; then
    echo "❌ 错误: gcloud CLI 未安装"
    echo "请访问 https://cloud.google.com/sdk/docs/install 安装 Google Cloud SDK"
    exit 1
fi

# 设置项目
echo "🔧 设置 GCP 项目..."
gcloud config set project $PROJECT_ID

# 检查当前认证状态
echo "🔍 检查认证状态..."
gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ 请先进行 GCP 认证: gcloud auth login"
    exit 1
fi

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
gcloud scheduler jobs create http $JOB_NAME \
    --schedule="$SCHEDULE" \
    --uri="$SERVICE_URL/run" \
    --http-method=POST \
    --location=$LOCATION \
    --time-zone=$TIMEZONE \
    --description="Daily WeeklyReporter execution at 12:00 PM Beijing Time" \
    --headers="Content-Type=application/json" \
    --message-body='{"trigger":"scheduler","description":"Daily automated run"}' \
    --quiet

if [ $? -eq 0 ]; then
    echo "✅ Cloud Scheduler 任务创建成功！"
    echo ""
    echo "📊 任务详细信息:"
    gcloud scheduler jobs describe $JOB_NAME \
        --location=$LOCATION \
        --format="table(name,schedule,timeZone,httpTarget.uri)"
    
    echo ""
    echo "💡 管理命令:"
    echo "  查看任务: gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION"
    echo "  手动运行: gcloud scheduler jobs run $JOB_NAME --location=$LOCATION"
    echo "  暂停任务: gcloud scheduler jobs pause $JOB_NAME --location=$LOCATION"
    echo "  恢复任务: gcloud scheduler jobs resume $JOB_NAME --location=$LOCATION"
    echo "  删除任务: gcloud scheduler jobs delete $JOB_NAME --location=$LOCATION"
    
    echo ""
    echo "🎯 下一次执行时间: 明天中午12:00 (北京时间)"
    echo "📋 可以在 GCP Console > Cloud Scheduler 中查看和管理任务"
    
else
    echo "❌ Cloud Scheduler 任务创建失败"
    exit 1
fi

echo "=================================================="
echo "✅ Cloud Scheduler 设置完成！" 
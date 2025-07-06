#!/bin/bash

# Google Cloud Scheduler 8AM Report Agent All 设置脚本
# 每天上午8点运行WeeklyReporter，处理所有合作伙伴数据

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
JOB_NAME="reporter-agent-all-8am"
CLOUD_RUN_URL="https://reporter-agent-472712465571.asia-southeast1.run.app/run"
SCHEDULE="0 8 * * *"  # 每天上午8点
TIME_ZONE="Asia/Singapore"
DESCRIPTION="WeeklyReporter 每日上午8点执行 - 处理所有合作伙伴2天前数据"

echo "🚀 开始设置Google Cloud Scheduler (8AM Daily - All Partners)"
echo "================================================"
echo "项目ID: $PROJECT_ID"
echo "区域: $REGION" 
echo "任务名称: $JOB_NAME"
echo "执行时间: 每天上午8点 (Singapore时区 GMT+8)"
echo "目标URL: $CLOUD_RUN_URL"
echo "合作伙伴: 所有合作伙伴"
echo "数据范围: 2天前"
echo "================================================"

# 检查 gcloud 是否已安装和认证
if ! command -v gcloud &> /dev/null; then
    echo "❌ 错误: gcloud CLI 未安装"
    echo "请访问 https://cloud.google.com/sdk/docs/install 安装 Google Cloud SDK"
    exit 1
fi

# 设置项目
echo "📋 设置Google Cloud项目..."
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

# 检查并删除现有的同名任务
echo "🔍 检查现有任务..."
if gcloud scheduler jobs describe $JOB_NAME --location=$REGION --quiet >/dev/null 2>&1; then
    echo "⚠️ 发现现有任务 '$JOB_NAME'，正在删除..."
    gcloud scheduler jobs delete $JOB_NAME \
        --location=$REGION \
        --quiet
    echo "✅ 已删除现有任务"
else
    echo "✅ 没有发现同名任务"
fi

# 创建新的调度任务
echo "📅 创建新的Cloud Scheduler任务..."

# 创建HTTP请求体 - 处理所有合作伙伴，2天前的数据，无限制
REQUEST_BODY='{
    "partner": "all",
    "days_ago": 2,
    "save_json": true,
    "upload_feishu": true,
    "send_email": true,
    "trigger": "scheduler",
    "description": "Daily 8AM automated run for all partners - 2 days ago data"
}'

echo "📝 请求体内容:"
echo "$REQUEST_BODY"

# 创建Cloud Scheduler任务
gcloud scheduler jobs create http $JOB_NAME \
    --location=$REGION \
    --schedule="$SCHEDULE" \
    --time-zone="$TIME_ZONE" \
    --uri="$CLOUD_RUN_URL" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body="$REQUEST_BODY" \
    --description="$DESCRIPTION"

if [ $? -eq 0 ]; then
    echo "✅ Cloud Scheduler任务创建成功！"
    echo ""
    echo "📋 任务详情:"
    echo "   任务名称: $JOB_NAME"
    echo "   执行时间: 每天上午8点 (Asia/Singapore GMT+8)"
    echo "   处理Partners: 所有合作伙伴 (RAMPUP, YueMeng, ByteC)"
    echo "   数据范围: 2天前"
    echo "   数据限制: 无限制"
    echo "   邮件发送: ✅ 启用"
    echo "   飞书上传: ✅ 启用"
    echo "   JSON保存: ✅ 启用"
    echo ""
    echo "🔍 查看任务状态:"
    gcloud scheduler jobs describe $JOB_NAME --location=$REGION
    echo ""
    echo "▶️ 下次执行时间:"
    echo "   明天上午8点 (Asia/Singapore时区 GMT+8)"
    echo ""
    echo "💡 管理命令:"
    echo "   查看任务: gcloud scheduler jobs describe $JOB_NAME --location=$REGION"
    echo "   手动运行: gcloud scheduler jobs run $JOB_NAME --location=$REGION"
    echo "   暂停任务: gcloud scheduler jobs pause $JOB_NAME --location=$REGION"
    echo "   恢复任务: gcloud scheduler jobs resume $JOB_NAME --location=$REGION"
    echo "   删除任务: gcloud scheduler jobs delete $JOB_NAME --location=$REGION"
    echo ""
    echo "🧪 手动测试任务:"
    echo "   gcloud scheduler jobs run $JOB_NAME --location=$REGION"
else
    echo "❌ Cloud Scheduler任务创建失败！"
    exit 1
fi

echo ""
echo "🎉 设置完成！WeeklyReporter将每天上午8点自动运行，处理所有合作伙伴的2天前数据。"
echo "📍 部署区域: asia-southeast1 (新加坡)"
echo "⏰ 时区: Asia/Singapore (GMT+8)" 
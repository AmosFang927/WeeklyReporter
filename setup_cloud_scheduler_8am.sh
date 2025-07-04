#!/bin/bash

# Google Cloud Scheduler 8AM 设置脚本
# 每天上午8点运行WeeklyReporter，处理2天前的数据

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-east1"
JOB_NAME="weeklyreporter-daily-8am-rampup"
CLOUD_RUN_URL="https://weeklyreporter-crwdeesavq-de.a.run.app/run"
SCHEDULE="0 8 * * *"  # 每天上午8点
TIME_ZONE="Asia/Hong_Kong"
DESCRIPTION="WeeklyReporter 每日上午8点执行 - 处理RAMPUP合作伙伴2天前数据"

echo "🚀 开始设置Google Cloud Scheduler (8AM Daily - RAMPUP Only)"
echo "================================================"
echo "项目ID: $PROJECT_ID"
echo "区域: $REGION" 
echo "任务名称: $JOB_NAME"
echo "执行时间: 每天上午8点 (Hong Kong时区 GMT+8)"
echo "目标URL: $CLOUD_RUN_URL"
echo "合作伙伴: RAMPUP"
echo "数据范围: 2天前"
echo "================================================"

# 设置项目
echo "📋 设置Google Cloud项目..."
gcloud config set project $PROJECT_ID

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

# 创建HTTP请求体 - 只处理RAMPUP合作伙伴，无数据限制
REQUEST_BODY='{
    "partners": ["RAMPUP"],
    "days_ago": 2,
    "save_json": true,
    "upload_to_feishu": true,
    "send_email": true
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
    echo "   执行时间: 每天上午8点 (Asia/Hong_Kong GMT+8)"
    echo "   处理Partners: RAMPUP"
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
    echo "   明天上午8点 (Asia/Hong_Kong时区 GMT+8)"
    echo ""
    echo "🧪 手动测试任务:"
    echo "   gcloud scheduler jobs run $JOB_NAME --location=$REGION"
else
    echo "❌ Cloud Scheduler任务创建失败！"
    exit 1
fi

echo ""
echo "🎉 设置完成！WeeklyReporter将每天上午8点自动运行，只处理RAMPUP合作伙伴。" 
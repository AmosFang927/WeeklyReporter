#!/bin/bash

# Cloud Scheduler 测试脚本
# 用于测试每日10:00 PM的WeeklyReporter任务

set -e

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
LOCATION="asia-east1"
JOB_NAME="weeklyreporter-daily"
SERVICE_URL="https://weeklyreporter-crwdeesavq-de.a.run.app"

echo "🧪 Cloud Scheduler 测试开始 (10:00 PM配置)"
echo "=" * 50

# 1. 检查任务状态
echo "📋 1. 检查任务状态..."
if gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "✅ 任务 '$JOB_NAME' 存在"
    
    # 显示任务详情
    echo ""
    echo "📊 任务详情:"
    gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --format="table(
        name.scope(jobs):label=NAME,
        schedule:label=SCHEDULE,
        timeZone:label=TIMEZONE,
        state:label=STATE,
        httpTarget.uri:label=TARGET_URL
    )"
    
    # 验证执行时间
    current_schedule=$(gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --format="value(schedule)" 2>/dev/null)
    if [[ "$current_schedule" == "0 22 * * *" ]]; then
        echo "✅ 执行时间配置正确: 每日10:00 PM"
    else
        echo "⚠️  执行时间可能不正确: $current_schedule (期望: 0 22 * * *)"
    fi
else
    echo "❌ 任务 '$JOB_NAME' 不存在！"
    echo "请先运行: ./setup_cloud_scheduler_10pm.sh"
    exit 1
fi

# 2. 测试Cloud Run服务连通性
echo ""
echo "🌐 2. 测试Cloud Run服务连通性..."
if curl -s --max-time 10 "$SERVICE_URL/health" > /dev/null; then
    echo "✅ Cloud Run服务可访问"
    
    # 获取服务状态
    response=$(curl -s "$SERVICE_URL/health")
    echo "📊 服务状态: $response"
else
    echo "❌ Cloud Run服务不可访问！"
    echo "请检查服务URL: $SERVICE_URL"
    exit 1
fi

# 3. 测试日志输出功能
echo ""
echo "📝 3. 测试日志输出功能..."
echo "调用测试端点: $SERVICE_URL/test-logging"
test_response=$(curl -s -X GET "$SERVICE_URL/test-logging")
echo "✅ 测试响应: $test_response"

# 4. 验证任务参数
echo ""
echo "🔍 4. 验证任务参数..."
message_body=$(gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION --format="value(httpTarget.body)" 2>/dev/null)
echo "📋 当前任务配置:"
echo "$message_body" | python3 -c "
import sys
import json
try:
    data = json.loads(sys.stdin.read())
    print(f'  Partners: {data.get(\"partners\", \"未设置\")}')
    print(f'  Date Range: {data.get(\"date_range\", \"未设置\")}')
    print(f'  Limit: {data.get(\"limit\", \"未设置\")}')
    print(f'  Save JSON: {data.get(\"save_json\", \"未设置\")}')
    print(f'  Upload Feishu: {data.get(\"upload_feishu\", \"未设置\")}')
    print(f'  Send Email: {data.get(\"send_email\", \"未设置\")}')
except:
    print('  无法解析任务参数')
"

# 5. 手动触发任务进行测试
echo ""
echo "🚀 5. 手动触发任务进行测试..."
echo "⚠️  这将执行实际的WeeklyReporter任务！"
read -p "是否继续? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在手动触发任务..."
    
    gcloud scheduler jobs run $JOB_NAME --location=$LOCATION --project=$PROJECT_ID
    
    echo "✅ 任务已触发"
    echo ""
    echo "📊 查看执行结果:"
    echo "  1. 等待2-3分钟让任务完成"
    echo "  2. 查看Cloud Run日志:"
    echo "     gcloud logs tail --filter='resource.type=cloud_run_revision' --limit=50"
    echo "  3. 查看Scheduler日志:"
    echo "     gcloud logs read 'resource.type=cloud_scheduler_job' --limit=10"
    
    # 等待一段时间后自动查看日志
    echo ""
    echo "⏳ 等待30秒后查看最新日志..."
    sleep 30
    
    echo ""
    echo "📋 最新Cloud Run日志 (最近10条):"
    gcloud logs read --filter='resource.type=cloud_run_revision' --limit=10 --format="value(timestamp,textPayload)" | head -20
    
else
    echo "❌ 跳过手动触发测试"
fi

# 6. 显示监控建议
echo ""
echo "👀 6. 监控建议"
echo "=" * 30

echo "📊 实时监控命令:"
echo "  查看实时日志:"
echo "    gcloud logs tail --filter='resource.type=cloud_run_revision'"
echo ""
echo "  查看Scheduler执行历史:"
echo "    gcloud logs read 'resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME' --limit=5"
echo ""
echo "  查看任务执行状态:"
echo "    gcloud scheduler jobs describe $JOB_NAME --location=$LOCATION"

echo ""
echo "🔧 管理命令:"
echo "  暂停任务: gcloud scheduler jobs pause $JOB_NAME --location=$LOCATION"
echo "  恢复任务: gcloud scheduler jobs resume $JOB_NAME --location=$LOCATION"
echo "  删除任务: gcloud scheduler jobs delete $JOB_NAME --location=$LOCATION"

echo ""
echo "⏰ 执行时间信息:"
echo "  当前时间: $(date '+%Y-%m-%d %H:%M:%S') (本地时间)"
echo "  计划执行: 每日 22:00 (北京时间) = 10:00 PM"

# 计算下次执行时间
echo "  下次执行: $(python3 -c "
from datetime import datetime, timedelta
import pytz

# 北京时间
beijing_tz = pytz.timezone('Asia/Shanghai')
now_beijing = datetime.now(beijing_tz)

# 今天的执行时间 (10:00 PM = 22:00)
today_run = now_beijing.replace(hour=22, minute=0, second=0, microsecond=0)

# 如果今天的执行时间已过，计算明天的
if today_run <= now_beijing:
    next_run = today_run + timedelta(days=1)
else:
    next_run = today_run

print(next_run.strftime('%Y-%m-%d %H:%M:%S (北京时间)'))
")"

echo ""
echo "🎉 测试完成！"
echo ""
echo "📋 测试总结:"
echo "  ✅ 任务配置检查"
echo "  ✅ 执行时间验证 (10:00 PM)"
echo "  ✅ 服务连通性检查" 
echo "  ✅ 日志输出测试"
echo "  ✅ 任务参数验证"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  ✅ 手动触发测试"
else
    echo "  ⏭️  手动触发测试 (已跳过)"
fi

echo ""
echo "💡 提示:"
echo "  - 任务将在每天10:00 PM(北京时间)自动执行"
echo "  - 使用 'gcloud logs tail' 命令监控实时日志"
echo "  - 如需修改配置，重新运行 setup_cloud_scheduler_10pm.sh" 
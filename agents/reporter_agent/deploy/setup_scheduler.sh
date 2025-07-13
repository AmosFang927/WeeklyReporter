#!/bin/bash

# Cloud Scheduler 配置脚本
# 为Reporter-Agent设置定时任务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"
SCHEDULER_REGION="asia-southeast1"

echo -e "${BLUE}🚀 开始配置 Reporter-Agent Cloud Scheduler${NC}"
echo "=============================================="

# 获取服务URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")

if [ -z "$SERVICE_URL" ]; then
    echo -e "${RED}❌ 找不到 Reporter-Agent 服务，请先部署服务${NC}"
    exit 1
fi

echo -e "${BLUE}📋 项目: $PROJECT_ID${NC}"
echo -e "${BLUE}🏷️ 服务: $SERVICE_NAME${NC}"
echo -e "${BLUE}🌍 地区: $REGION${NC}"
echo -e "${BLUE}🔗 服务URL: $SERVICE_URL${NC}"
echo "=============================================="

# 启用Cloud Scheduler API
echo -e "${YELLOW}1. 启用Cloud Scheduler API...${NC}"
gcloud services enable cloudscheduler.googleapis.com

# 创建App Engine应用（如果不存在）
echo -e "${YELLOW}2. 检查App Engine应用...${NC}"
if ! gcloud app describe --project=$PROJECT_ID >/dev/null 2>&1; then
    echo -e "${YELLOW}   创建App Engine应用...${NC}"
    gcloud app create --region=$REGION --project=$PROJECT_ID
fi

# 删除现有的调度任务（如果存在）
echo -e "${YELLOW}3. 清理现有的调度任务...${NC}"
EXISTING_JOBS=$(gcloud scheduler jobs list --location=$SCHEDULER_REGION --format="value(name)" | grep "reporter-agent" || true)
if [ ! -z "$EXISTING_JOBS" ]; then
    echo "   发现现有任务，正在删除..."
    echo "$EXISTING_JOBS" | while read job; do
        gcloud scheduler jobs delete $job --location=$SCHEDULER_REGION --quiet
        echo "   已删除: $job"
    done
fi

# 创建新的调度任务
echo -e "${YELLOW}4. 创建新的调度任务...${NC}"

# 任务1: 每天8点 - 所有Partner报表
echo -e "${YELLOW}   创建任务: reporter-agent-daily-all${NC}"
gcloud scheduler jobs create http reporter-agent-daily-all \
    --schedule='0 8 * * *' \
    --uri="$SERVICE_URL/trigger?partner=ALL&days=1&email=true&feishu=true" \
    --http-method=GET \
    --location=$SCHEDULER_REGION \
    --description="每天8点生成所有Partner的转化报表" \
    --time-zone="Asia/Singapore"

# 任务2: 每天9点 - ByteC专用报表
echo -e "${YELLOW}   创建任务: reporter-agent-daily-bytec${NC}"
gcloud scheduler jobs create http reporter-agent-daily-bytec \
    --schedule='0 9 * * *' \
    --uri="$SERVICE_URL/trigger?partner=ByteC&days=1&email=true&feishu=true" \
    --http-method=GET \
    --location=$SCHEDULER_REGION \
    --description="每天9点生成ByteC专用转化报表" \
    --time-zone="Asia/Singapore"

# 任务3: 每周一10点 - 周报表
echo -e "${YELLOW}   创建任务: reporter-agent-weekly-all${NC}"
gcloud scheduler jobs create http reporter-agent-weekly-all \
    --schedule='0 10 * * 1' \
    --uri="$SERVICE_URL/trigger?partner=ALL&days=7&email=true&feishu=true" \
    --http-method=GET \
    --location=$SCHEDULER_REGION \
    --description="每周一10点生成所有Partner的周报表" \
    --time-zone="Asia/Singapore"

# 任务4: 每小时健康检查
echo -e "${YELLOW}   创建任务: reporter-agent-health-check${NC}"
gcloud scheduler jobs create http reporter-agent-health-check \
    --schedule='0 * * * *' \
    --uri="$SERVICE_URL/health" \
    --http-method=GET \
    --location=$SCHEDULER_REGION \
    --description="每小时健康检查" \
    --time-zone="Asia/Singapore"

# 列出创建的任务
echo -e "${YELLOW}5. 验证创建的任务...${NC}"
gcloud scheduler jobs list --location=$SCHEDULER_REGION --filter="name~reporter-agent"

echo -e "${GREEN}✅ Cloud Scheduler 配置完成！${NC}"
echo ""
echo "=============================================="
echo -e "${GREEN}🎉 调度任务设置完成${NC}"
echo "=============================================="
echo -e "${BLUE}📋 创建的调度任务:${NC}"
echo ""
echo -e "${YELLOW}1. reporter-agent-daily-all${NC}"
echo "   🕐 时间: 每天8点 (新加坡时间)"
echo "   📊 内容: 所有Partner的日报表"
echo "   🔗 URL: $SERVICE_URL/trigger?partner=ALL&days=1"
echo ""
echo -e "${YELLOW}2. reporter-agent-daily-bytec${NC}"
echo "   🕐 时间: 每天9点 (新加坡时间)"
echo "   📊 内容: ByteC专用日报表"
echo "   🔗 URL: $SERVICE_URL/trigger?partner=ByteC&days=1"
echo ""
echo -e "${YELLOW}3. reporter-agent-weekly-all${NC}"
echo "   🕐 时间: 每周一10点 (新加坡时间)"
echo "   📊 内容: 所有Partner的周报表"
echo "   🔗 URL: $SERVICE_URL/trigger?partner=ALL&days=7"
echo ""
echo -e "${YELLOW}4. reporter-agent-health-check${NC}"
echo "   🕐 时间: 每小时"
echo "   📊 内容: 健康检查"
echo "   🔗 URL: $SERVICE_URL/health"
echo ""
echo -e "${YELLOW}📋 管理调度任务的命令:${NC}"
echo "  # 查看所有任务"
echo "  gcloud scheduler jobs list --location=$SCHEDULER_REGION"
echo ""
echo "  # 手动触发任务"
echo "  gcloud scheduler jobs run reporter-agent-daily-all --location=$SCHEDULER_REGION"
echo ""
echo "  # 暂停任务"
echo "  gcloud scheduler jobs pause reporter-agent-daily-all --location=$SCHEDULER_REGION"
echo ""
echo "  # 恢复任务"
echo "  gcloud scheduler jobs resume reporter-agent-daily-all --location=$SCHEDULER_REGION"
echo ""
echo "  # 删除任务"
echo "  gcloud scheduler jobs delete reporter-agent-daily-all --location=$SCHEDULER_REGION"
echo ""
echo -e "${GREEN}✅ 设置完成！${NC}" 
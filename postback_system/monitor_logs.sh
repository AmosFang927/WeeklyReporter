#!/bin/bash
# Cloud Run 日志监控脚本

PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="bytec-public-postback"
REGION="asia-southeast1"
SERVICE_URL="https://bytec-public-postback-472712465571.asia-southeast1.run.app"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 ByteC Postback Cloud Run 日志监控${NC}"
echo "========================================"

# 检查参数
case "${1:-recent}" in
    "tail"|"实时")
        echo -e "${YELLOW}📡 启动实时日志流监控...${NC}"
        echo "按 Ctrl+C 停止监控"
        echo "每5秒刷新一次最新日志"
        echo "----------------------------------------"
        LATEST_REVISION=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.latestReadyRevisionName)")
        while true; do
            echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] 刷新最新日志...${NC}"
            gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND resource.labels.revision_name=$LATEST_REVISION" --limit=10 --freshness=2m --format="table(timestamp, severity, textPayload)" 2>/dev/null || echo "无新日志"
            echo "----------------------------------------"
            sleep 5
        done
        ;;
    "recent"|"最新")
        echo -e "${YELLOW}📋 查看最新日志 (最近50条)...${NC}"
        echo "----------------------------------------"
        LATEST_REVISION=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.latestReadyRevisionName)")
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND resource.labels.revision_name=$LATEST_REVISION" --limit=50 --freshness=30m --format="table(timestamp, severity, textPayload)"
        ;;
    "postback"|"转换")
        echo -e "${YELLOW}💰 查看Postback转换日志...${NC}"
        echo "----------------------------------------"
        LATEST_REVISION=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.latestReadyRevisionName)")
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND resource.labels.revision_name=$LATEST_REVISION AND textPayload:\"ByteC Involve Postback\"" --limit=100 --freshness=60m --format="table(timestamp, severity, textPayload)"
        ;;
    "errors"|"错误")
        echo -e "${RED}❌ 查看错误日志...${NC}"
        echo "----------------------------------------"
        LATEST_REVISION=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.latestReadyRevisionName)")
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND resource.labels.revision_name=$LATEST_REVISION AND severity>=ERROR" --limit=50 --freshness=30m --format="table(timestamp, severity, textPayload)"
        ;;
    "health"|"健康")
        echo -e "${GREEN}💚 查看健康检查日志...${NC}"
        echo "----------------------------------------"
        LATEST_REVISION=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.latestReadyRevisionName)")
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND resource.labels.revision_name=$LATEST_REVISION AND textPayload:\"/health\"" --limit=20 --freshness=30m --format="table(timestamp, severity, textPayload)"
        ;;
    "json"|"JSON")
        echo -e "${BLUE}📄 查看JSON格式日志...${NC}"
        echo "----------------------------------------"
        LATEST_REVISION=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.latestReadyRevisionName)")
        gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND resource.labels.revision_name=$LATEST_REVISION" --limit=20 --freshness=30m --format="json"
        ;;
    "help"|"帮助")
        echo -e "${BLUE}使用方法:${NC}"
        echo "  $0 [选项]"
        echo ""
        echo -e "${YELLOW}可用选项:${NC}"
        echo "  recent/最新    - 查看最新日志 (默认)"
        echo "  tail/实时      - 实时日志流"
        echo "  postback/转换  - 查看Postback转换日志"
        echo "  errors/错误    - 查看错误日志"
        echo "  health/健康    - 查看健康检查日志"
        echo "  json/JSON      - JSON格式输出"
        echo "  help/帮助      - 显示此帮助"
        echo ""
        echo -e "${GREEN}示例:${NC}"
        echo "  $0 tail        # 实时监控"
        echo "  $0 postback    # 查看转换数据"
        echo "  $0 errors      # 查看错误"
        ;;
    *)
        echo -e "${RED}❌ 未知选项: $1${NC}"
        echo "使用 '$0 help' 查看帮助"
        exit 1
        ;;
esac 
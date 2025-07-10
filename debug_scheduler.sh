#!/bin/bash
# Cloud Scheduler 診斷和監控腳本
# 用於調試 reporter-agent-all-8am 定時任務問題

set -e

# 配置參數
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
JOB_NAME="reporter-agent-all-8am"
SERVICE_NAME="reporter-agent"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Cloud Scheduler 診斷工具${NC}"
echo -e "${BLUE}===============================${NC}"
echo -e "${YELLOW}📋 項目: $PROJECT_ID${NC}"
echo -e "${YELLOW}🌍 區域: $REGION${NC}"
echo -e "${YELLOW}⏰ 任務: $JOB_NAME${NC}"
echo -e "${YELLOW}🏷️ 服務: $SERVICE_NAME${NC}"
echo ""

# 設置項目
gcloud config set project $PROJECT_ID --quiet

# 1. 檢查 Cloud Scheduler 狀態
echo -e "${CYAN}1. 檢查 Cloud Scheduler 狀態${NC}"
echo "================================"
gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="table(name,schedule,timeZone,state,lastAttemptTime)" 2>/dev/null || echo -e "${RED}❌ 無法獲取 Scheduler 狀態${NC}"
echo ""

# 2. 檢查最近的 Scheduler 執行日誌
echo -e "${CYAN}2. 最近 24 小時的 Scheduler 執行日誌${NC}"
echo "======================================"
gcloud logging read 'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'"' \
    --limit=10 \
    --format="table(timestamp,severity,textPayload)" \
    --freshness=24h 2>/dev/null || echo -e "${YELLOW}⚠️ 無 Scheduler 執行日誌${NC}"
echo ""

# 3. 檢查 Cloud Run 服務狀態
echo -e "${CYAN}3. 檢查 Cloud Run 服務狀態${NC}"
echo "============================="
gcloud run services describe $SERVICE_NAME --region=$REGION --format="table(metadata.name,status.url,spec.template.spec.timeoutSeconds,spec.template.spec.containers[0].resources.limits.memory,spec.template.spec.containers[0].resources.limits.cpu)" 2>/dev/null || echo -e "${RED}❌ 無法獲取服務狀態${NC}"
echo ""

# 4. 檢查最近的 Cloud Run 請求日誌
echo -e "${CYAN}4. 最近 2 小時的 Cloud Run HTTP 請求${NC}"
echo "==================================="
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'" AND httpRequest.requestMethod="POST"' \
    --limit=10 \
    --format="table(timestamp,httpRequest.status,httpRequest.userAgent)" \
    --freshness=2h 2>/dev/null || echo -e "${YELLOW}⚠️ 無 HTTP 請求日誌${NC}"
echo ""

# 5. 檢查任務執行詳細日誌
echo -e "${CYAN}5. 最近 2 小時的任務執行日誌${NC}"
echo "============================="
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'" AND (textPayload:"Cloud Scheduler" OR textPayload:"任务")' \
    --limit=20 \
    --format="table(timestamp,textPayload)" \
    --freshness=2h 2>/dev/null || echo -e "${YELLOW}⚠️ 無任務執行日誌${NC}"
echo ""

# 6. 檢查錯誤和超時日誌
echo -e "${CYAN}6. 最近 24 小時的錯誤日誌${NC}"
echo "==========================="
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'" AND (severity="ERROR" OR textPayload:"timeout" OR textPayload:"failed" OR textPayload:"Exception")' \
    --limit=10 \
    --format="table(timestamp,severity,textPayload)" \
    --freshness=24h 2>/dev/null || echo -e "${GREEN}✅ 無錯誤日誌${NC}"
echo ""

# 7. 檢查當前運行的任務
echo -e "${CYAN}7. 檢查當前運行的任務${NC}"
echo "========================"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)' 2>/dev/null)
if [ -n "$SERVICE_URL" ]; then
    echo -e "${BLUE}服務 URL: $SERVICE_URL${NC}"
    echo "檢查任務狀態..."
    curl -s "$SERVICE_URL/tasks" | python3 -m json.tool 2>/dev/null || echo -e "${YELLOW}⚠️ 無法獲取任務狀態${NC}"
else
    echo -e "${RED}❌ 無法獲取服務 URL${NC}"
fi
echo ""

# 8. 健康檢查
echo -e "${CYAN}8. 服務健康檢查${NC}"
echo "==================="
if [ -n "$SERVICE_URL" ]; then
    if curl -f -s "$SERVICE_URL/health" > /dev/null; then
        echo -e "${GREEN}✅ 健康檢查通過${NC}"
        curl -s "$SERVICE_URL/health" | python3 -m json.tool 2>/dev/null || curl -s "$SERVICE_URL/health"
    else
        echo -e "${RED}❌ 健康檢查失敗${NC}"
    fi
else
    echo -e "${RED}❌ 無法進行健康檢查${NC}"
fi
echo ""

# 9. 測試手動觸發
echo -e "${CYAN}9. 測試選項${NC}"
echo "=============="
echo -e "${YELLOW}💡 可用的測試命令:${NC}"
echo "   手動觸發任務: gcloud scheduler jobs run $JOB_NAME --location=$REGION"
echo "   測試 API 端點: curl -X POST -H 'Content-Type: application/json' -d '{\"partner\":\"all\",\"days_ago\":2}' $SERVICE_URL/run"
echo "   監控任務日誌: ./view_logs.sh recent 50 1"
echo "   查看詳細狀態: ./monitor_reporter_agent.sh status"
echo ""

# 10. 建議和總結
echo -e "${CYAN}10. 診斷建議${NC}"
echo "=============="
echo -e "${YELLOW}🔧 常見問題解決方案:${NC}"
echo "   1. 如果任務卡住: 檢查 API 調用是否超時"
echo "   2. 如果沒有日誌: 檢查 Cloud Run 服務是否正常運行"
echo "   3. 如果超時: 考慮優化數據處理邏輯或增加超時時間"
echo "   4. 如果權限問題: 檢查服務帳號權限"
echo ""
echo -e "${GREEN}✅ 診斷完成! 使用上述建議和測試命令進行進一步調試。${NC}" 
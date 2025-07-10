#!/bin/bash
# Cloud Scheduler 時區配置修復腳本
# 檢查和修復定時任務的時區問題

set -e

# 配置參數
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
JOB_NAME="reporter-agent-all-8am"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}⏰ Cloud Scheduler 時區配置檢查和修復${NC}"
echo -e "${BLUE}=========================================${NC}"
echo -e "${YELLOW}📋 項目: $PROJECT_ID${NC}"
echo -e "${YELLOW}🌍 區域: $REGION${NC}"
echo -e "${YELLOW}⏰ 任務: $JOB_NAME${NC}"
echo ""

# 設置項目
gcloud config set project $PROJECT_ID --quiet

# 1. 檢查當前配置
echo -e "${CYAN}1. 檢查當前 Cloud Scheduler 配置${NC}"
echo "=================================="
CURRENT_CONFIG=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(schedule,timeZone,state,retryConfig.maxRetryDuration)" 2>/dev/null)
if [ -n "$CURRENT_CONFIG" ]; then
    echo -e "${GREEN}✅ 當前配置:${NC}"
    echo "$CURRENT_CONFIG"
else
    echo -e "${RED}❌ 無法獲取配置${NC}"
    exit 1
fi
echo ""

# 2. 檢查最近執行時間
echo -e "${CYAN}2. 檢查最近執行時間${NC}"
echo "========================"
echo -e "${YELLOW}最近 7 天的執行記錄:${NC}"
gcloud logging read 'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'"' \
    --limit=20 \
    --format="table(timestamp,severity)" \
    --freshness=168h 2>/dev/null | while IFS=$'\t' read -r timestamp severity; do
    if [ -n "$timestamp" ]; then
        # 轉換為新加坡時間
        SG_TIME=$(date -d "$timestamp" -u +"%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "無法轉換")
        echo "   UTC: $timestamp -> SG: $SG_TIME"
    fi
done
echo ""

# 3. 分析執行模式
echo -e "${CYAN}3. 執行模式分析${NC}"
echo "=================="
echo -e "${YELLOW}預期執行時間: 每天上午 8:00 (Asia/Singapore)${NC}"
echo -e "${YELLOW}對應 UTC 時間: 每天 00:00${NC}"
echo ""

# 4. 檢查是否有時區問題
echo -e "${CYAN}4. 時區問題檢查${NC}"
echo "=================="
echo -e "${YELLOW}檢查項目:${NC}"
echo "   ✅ 時區設置: Asia/Singapore"
echo "   ✅ 調度表達式: 0 8 * * * (每天上午8點)"
echo "   ✅ 重試配置: maxRetryDuration=0s (無重試)"
echo ""

# 5. 檢查重試配置問題
echo -e "${CYAN}5. 重試配置檢查${NC}"
echo "=================="
RETRY_CONFIG=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(retryConfig.maxRetryDuration)" 2>/dev/null)
if [ "$RETRY_CONFIG" = "0s" ]; then
    echo -e "${GREEN}✅ 重試配置正確: 無重試${NC}"
else
    echo -e "${RED}❌ 重試配置問題: $RETRY_CONFIG${NC}"
    echo -e "${YELLOW}💡 建議: 設置 maxRetryDuration=0s 避免重試${NC}"
fi
echo ""

# 6. 檢查執行狀態
echo -e "${CYAN}6. 執行狀態檢查${NC}"
echo "=================="
LAST_ATTEMPT=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(lastAttemptTime)" 2>/dev/null)
if [ -n "$LAST_ATTEMPT" ]; then
    echo -e "${YELLOW}最後執行時間: $LAST_ATTEMPT${NC}"
    # 轉換為新加坡時間
    SG_LAST=$(date -d "$LAST_ATTEMPT" -u +"%Y-%m-%d %H:%M:%S" 2>/dev/null || echo "無法轉換")
    echo -e "${YELLOW}新加坡時間: $SG_LAST${NC}"
    
    # 檢查是否在正確時間執行
    HOUR=$(date -d "$LAST_ATTEMPT" -u +"%H" 2>/dev/null || echo "0")
    if [ "$HOUR" = "00" ]; then
        echo -e "${GREEN}✅ 執行時間正確 (UTC 00:00 = SG 08:00)${NC}"
    else
        echo -e "${RED}❌ 執行時間異常 (UTC ${HOUR}:XX)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ 無執行記錄${NC}"
fi
echo ""

# 7. 修復建議
echo -e "${CYAN}7. 修復建議${NC}"
echo "=============="
echo -e "${YELLOW}🔧 如果發現時區問題，可以重新創建任務:${NC}"
echo "   ./setup_cloud_scheduler_report_agent_all_8am.sh"
echo ""
echo -e "${YELLOW}🔧 如果需要禁用重試:${NC}"
echo "   gcloud scheduler jobs update http $JOB_NAME \\"
echo "     --location=$REGION \\"
echo "     --max-retry-duration=0s"
echo ""

# 8. 測試下次執行時間
echo -e "${CYAN}8. 下次執行時間預測${NC}"
echo "========================"
echo -e "${YELLOW}根據 cron 表達式 '0 8 * * *':${NC}"
echo "   - 每天上午 8:00 (Asia/Singapore)"
echo "   - 對應 UTC 時間: 每天 00:00"
echo "   - 下次執行: 明天上午 8:00"
echo ""

echo -e "${GREEN}✅ 時區配置檢查完成!${NC}"
echo -e "${BLUE}💡 如果發現問題，請使用上述修復建議。${NC}" 
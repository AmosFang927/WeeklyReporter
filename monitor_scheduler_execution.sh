#!/bin/bash
# Cloud Scheduler 執行時間監控腳本
# 確保定時任務在正確時間執行

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

echo -e "${BLUE}⏰ Cloud Scheduler 執行時間監控${NC}"
echo -e "${BLUE}===============================${NC}"
echo -e "${YELLOW}📋 項目: $PROJECT_ID${NC}"
echo -e "${YELLOW}🌍 區域: $REGION${NC}"
echo -e "${YELLOW}⏰ 任務: $JOB_NAME${NC}"
echo ""

# 設置項目
gcloud config set project $PROJECT_ID --quiet

# 獲取當前時間
CURRENT_UTC=$(date -u +"%Y-%m-%dT%H:%M:%S")
CURRENT_SG=$(date +"%Y-%m-%d %H:%M:%S")

echo -e "${CYAN}當前時間:${NC}"
echo "   UTC: $CURRENT_UTC"
echo "   SG:  $CURRENT_SG"
echo ""

# 檢查今天的執行情況
echo -e "${CYAN}檢查今天的執行情況:${NC}"
echo "========================"

# 獲取今天的執行記錄
TODAY=$(date +"%Y-%m-%d")
TODAY_UTC=$(date -u +"%Y-%m-%d")

echo -e "${YELLOW}今天 ($TODAY) 的執行記錄:${NC}"

# 使用 gcloud logging 獲取今天的執行記錄
EXECUTIONS=$(gcloud logging read 'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'" AND timestamp>="'$TODAY_UTC'T00:00:00Z"' \
    --limit=10 \
    --format="value(timestamp)" \
    --freshness=24h 2>/dev/null)

if [ -n "$EXECUTIONS" ]; then
    echo "$EXECUTIONS" | while read -r timestamp; do
        if [ -n "$timestamp" ]; then
            # 轉換為新加坡時間
            SG_TIME=$(python3 -c "
import datetime
utc_time = datetime.datetime.fromisoformat('$timestamp'.replace('Z', '+00:00'))
sg_time = utc_time + datetime.timedelta(hours=8)
print(sg_time.strftime('%Y-%m-%d %H:%M:%S'))
" 2>/dev/null || echo "無法轉換")
            
            # 檢查是否在正確時間執行
            HOUR=$(python3 -c "
import datetime
utc_time = datetime.datetime.fromisoformat('$timestamp'.replace('Z', '+00:00'))
sg_time = utc_time + datetime.timedelta(hours=8)
print(sg_time.hour)
" 2>/dev/null || echo "0")
            
            if [ "$HOUR" = "8" ]; then
                echo -e "   ✅ $SG_TIME (正常8點執行)"
            else
                echo -e "   ❌ $SG_TIME (異常時間)"
            fi
        fi
    done
else
    echo -e "${YELLOW}   今天還沒有執行記錄${NC}"
fi
echo ""

# 檢查明天的預期執行時間
echo -e "${CYAN}明天的預期執行時間:${NC}"
echo "========================"
TOMORROW=$(date -d "tomorrow" +"%Y-%m-%d")
TOMORROW_UTC=$(date -u -d "tomorrow" +"%Y-%m-%d")

echo -e "${YELLOW}明天 ($TOMORROW) 的預期執行:${NC}"
echo "   UTC: ${TOMORROW_UTC}T00:00:00Z"
echo "   SG:  ${TOMORROW} 08:00:00"
echo ""

# 檢查任務狀態
echo -e "${CYAN}任務狀態檢查:${NC}"
echo "=================="
STATE=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(state)" 2>/dev/null)
if [ "$STATE" = "ENABLED" ]; then
    echo -e "${GREEN}✅ 任務狀態: ENABLED${NC}"
else
    echo -e "${RED}❌ 任務狀態: $STATE${NC}"
fi

# 檢查重試配置
RETRY_CONFIG=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(retryConfig.maxRetryDuration)" 2>/dev/null)
if [ "$RETRY_CONFIG" = "0s" ]; then
    echo -e "${GREEN}✅ 重試配置: 已禁用${NC}"
else
    echo -e "${RED}❌ 重試配置: $RETRY_CONFIG${NC}"
fi
echo ""

# 檢查最近7天的執行統計
echo -e "${CYAN}最近7天執行統計:${NC}"
echo "======================"

# 統計正常執行和異常執行
NORMAL_COUNT=0
ABNORMAL_COUNT=0

EXECUTIONS_7DAYS=$(gcloud logging read 'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'"' \
    --limit=50 \
    --format="value(timestamp)" \
    --freshness=168h 2>/dev/null)

if [ -n "$EXECUTIONS_7DAYS" ]; then
    echo "$EXECUTIONS_7DAYS" | while read -r timestamp; do
        if [ -n "$timestamp" ]; then
            HOUR=$(python3 -c "
import datetime
utc_time = datetime.datetime.fromisoformat('$timestamp'.replace('Z', '+00:00'))
sg_time = utc_time + datetime.timedelta(hours=8)
print(sg_time.hour)
" 2>/dev/null || echo "0")
            
            if [ "$HOUR" = "8" ]; then
                NORMAL_COUNT=$((NORMAL_COUNT + 1))
            else
                ABNORMAL_COUNT=$((ABNORMAL_COUNT + 1))
            fi
        fi
    done
    
    echo -e "${YELLOW}統計結果:${NC}"
    echo "   正常8點執行: $NORMAL_COUNT 次"
    echo "   異常時間執行: $ABNORMAL_COUNT 次"
else
    echo -e "${YELLOW}   無執行記錄${NC}"
fi
echo ""

# 建議和總結
echo -e "${CYAN}監控建議:${NC}"
echo "=============="
echo -e "${YELLOW}🔧 如果發現異常執行:${NC}"
echo "   1. 檢查任務是否超時導致重試"
echo "   2. 確認重試配置是否正確"
echo "   3. 檢查 Cloud Run 服務狀態"
echo ""
echo -e "${YELLOW}🔧 監控命令:${NC}"
echo "   ./debug_scheduler.sh"
echo "   ./fix_scheduler_timezone.sh"
echo "   gcloud scheduler jobs describe $JOB_NAME --location=$REGION"
echo ""

echo -e "${GREEN}✅ 執行時間監控完成!${NC}"
echo -e "${BLUE}💡 建議每天檢查執行時間，確保按時執行。${NC}" 
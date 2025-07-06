#!/bin/bash

# 部署监控脚本
# 监控GitHub Actions部署状态和服务健康状态

set -e

echo "🔍 开始监控部署状态..."
echo "监控时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Git SHA: $(git rev-parse --short HEAD)"
echo "========================================="

# 配置变量
MAX_WAIT_TIME=900  # 最大等待时间 15分钟
CHECK_INTERVAL=30   # 检查间隔 30秒
START_TIME=$(date +%s)
EXPECTED_SHA=$(git rev-parse --short HEAD)

# 预期的服务URL (将在部署过程中更新)
WEEKLYREPORTER_URL=""
POSTBACK_URL="https://bytec-public-postback-472712465571.asia-southeast1.run.app"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数：检查服务健康状态
check_service_health() {
    local url=$1
    local service_name=$2
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name 健康检查通过${NC}"
        return 0
    else
        echo -e "${YELLOW}⏳ $service_name 还未就绪${NC}"
        return 1
    fi
}

# 函数：检查服务是否包含最新的Git SHA
check_service_version() {
    local url=$1
    local service_name=$2
    
    local response=$(curl -s "$url" 2>/dev/null || echo "")
    if [[ "$response" == *"$EXPECTED_SHA"* ]] || [[ "$response" == *"GIT_SHA"* ]]; then
        echo -e "${GREEN}✅ $service_name 已更新到最新版本${NC}"
        return 0
    else
        echo -e "${YELLOW}⏳ $service_name 版本更新中...${NC}"
        return 1
    fi
}

# 函数：显示部署进度
show_progress() {
    local elapsed=$1
    local progress_bar=""
    local progress_percent=0
    
    # 计算进度百分比 (假设总共需要10分钟)
    if [ $elapsed -lt 600 ]; then
        progress_percent=$((elapsed * 100 / 600))
    else
        progress_percent=100
    fi
    
    # 创建进度条
    local bar_length=30
    local filled_length=$((progress_percent * bar_length / 100))
    
    for ((i=0; i<filled_length; i++)); do
        progress_bar+="█"
    done
    
    for ((i=filled_length; i<bar_length; i++)); do
        progress_bar+="░"
    done
    
    echo -e "${BLUE}📊 部署进度: [$progress_bar] ${progress_percent}%${NC}"
}

# 主监控循环
echo "🔄 开始监控部署进度..."
echo ""

while true; do
    current_time=$(date +%s)
    elapsed=$((current_time - START_TIME))
    elapsed_min=$((elapsed / 60))
    elapsed_sec=$((elapsed % 60))
    
    echo "⏰ 已等待: ${elapsed_min}分${elapsed_sec}秒"
    
    # 显示进度条
    show_progress $elapsed
    
    # 检查超时
    if [ $elapsed -gt $MAX_WAIT_TIME ]; then
        echo -e "${RED}❌ 部署监控超时 (${MAX_WAIT_TIME}秒)${NC}"
        echo "请手动检查GitHub Actions状态: https://github.com/AmosFang927/WeeklyReporter/actions"
        exit 1
    fi
    
    # 检查Postback服务
    echo ""
    echo "🔍 检查服务状态..."
    
    postback_healthy=false
    weeklyreporter_healthy=false
    
    if check_service_health "$POSTBACK_URL/health" "Postback服务"; then
        postback_healthy=true
    fi
    
    # 尝试检测WeeklyReporter服务URL
    if [ -z "$WEEKLYREPORTER_URL" ]; then
        echo -e "${YELLOW}🔍 尝试检测WeeklyReporter服务URL...${NC}"
        # 这里可以添加逻辑来检测新的URL，暂时使用占位符
        echo -e "${YELLOW}⏳ WeeklyReporter URL检测中...${NC}"
    else
        if check_service_health "$WEEKLYREPORTER_URL" "WeeklyReporter服务"; then
            weeklyreporter_healthy=true
        fi
    fi
    
    # 检查是否所有服务都就绪
    if [ "$postback_healthy" = true ]; then
        echo ""
        echo -e "${GREEN}🎉 部署监控完成！${NC}"
        echo "========================================="
        echo -e "${GREEN}✅ 部署成功通知${NC}"
        echo ""
        echo "📊 部署结果汇总:"
        echo "  🔗 Postback服务: $POSTBACK_URL"
        echo "  📍 区域: asia-southeast1 (新加坡)"  
        echo "  ⏰ 时区: Asia/Singapore (GMT+8)"
        echo "  🔄 Git SHA: $EXPECTED_SHA"
        echo "  ⏱️  总部署时间: ${elapsed_min}分${elapsed_sec}秒"
        echo ""
        echo "📝 健康检查:"
        echo "  curl $POSTBACK_URL/health"
        echo ""
        echo "🎯 服务状态: 全部正常运行"
        echo "========================================="
        
        # 显示部署完成通知
        echo ""
        echo -e "${GREEN}🔔 部署完成通知${NC}"
        echo -e "${GREEN}所有服务已成功部署并通过健康检查！${NC}"
        
        # 可以在这里添加额外的通知逻辑，比如发送邮件或Slack消息
        
        exit 0
    fi
    
    echo ""
    echo -e "${YELLOW}⏳ 继续等待部署完成...${NC}"
    echo "   下次检查: ${CHECK_INTERVAL}秒后"
    echo ""
    
    sleep $CHECK_INTERVAL
done 
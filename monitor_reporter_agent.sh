#!/bin/bash

# Google Cloud Run Reporter-Agent 监控脚本
# 提供多种监控方式和实时状态查看

# 配置变量
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="reporter-agent"
REGION="asia-southeast1"
SERVICE_URL="https://reporter-agent-472712465571.asia-southeast1.run.app"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 显示帮助信息
show_help() {
    echo -e "${WHITE}🔍 Google Cloud Run Reporter-Agent 监控工具${NC}"
    echo -e "${CYAN}=================================================${NC}"
    echo -e "${WHITE}用法:${NC} $0 [命令]"
    echo ""
    echo -e "${WHITE}可用命令:${NC}"
    echo -e "  ${GREEN}status${NC}      - 查看服务状态"
    echo -e "  ${GREEN}health${NC}      - 检查服务健康状态"
    echo -e "  ${GREEN}logs${NC}        - 查看最近的日志"
    echo -e "  ${GREEN}logs-watch${NC}  - 持续监控日志"
    echo -e "  ${GREEN}tail${NC}        - 实时追踪日志 (类似 tail -f)"
    echo -e "  ${GREEN}tasks${NC}       - 查看任务执行状态"
    echo -e "  ${GREEN}metrics${NC}     - 查看性能指标"
    echo -e "  ${GREEN}watch${NC}       - 实时监控服务"
    echo -e "  ${GREEN}errors${NC}      - 查看错误日志"
    echo -e "  ${GREEN}scheduler${NC}   - 查看云调度器状态"
    echo -e "  ${GREEN}all${NC}         - 显示所有监控信息"
    echo -e "  ${GREEN}help${NC}        - 显示此帮助信息"
    echo ""
    echo -e "${WHITE}示例:${NC}"
    echo -e "  $0 status       # 查看服务状态"
    echo -e "  $0 logs         # 查看最近日志"
    echo -e "  $0 tail         # 实时追踪日志 (类似 tail -f)"
    echo -e "  $0 logs-watch   # 持续监控日志"
    echo -e "  $0 watch        # 实时监控"
    echo ""
}

# 获取服务状态
get_service_status() {
    echo -e "${BLUE}🔍 正在检查服务状态...${NC}"
    
    # 检查Cloud Run服务状态
    local service_info=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.conditions[0].status,status.url)" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Cloud Run 服务状态: 正常${NC}"
        echo -e "${WHITE}   服务URL: ${SERVICE_URL}${NC}"
    else
        echo -e "${RED}❌ Cloud Run 服务状态: 异常${NC}"
        return 1
    fi
    
    # 检查HTTP健康状态
    local health_response=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL/health" 2>/dev/null)
    
    if [[ "$health_response" == "200" ]]; then
        echo -e "${GREEN}✅ HTTP 健康检查: 正常${NC}"
    else
        echo -e "${RED}❌ HTTP 健康检查: 异常 (HTTP $health_response)${NC}"
    fi
}

# 获取详细健康状态
get_health_status() {
    echo -e "${BLUE}🏥 获取详细健康状态...${NC}"
    
    local health_data=$(curl -s "$SERVICE_URL/status" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo -e "${WHITE}服务信息:${NC}"
        
        # 使用grep和sed解析JSON（不依赖jq）
        local service_name=$(echo "$health_data" | grep -o '"service":"[^"]*"' | sed 's/"service":"\([^"]*\)"/\1/')
        local status=$(echo "$health_data" | grep -o '"status":"[^"]*"' | sed 's/"status":"\([^"]*\)"/\1/')
        local version=$(echo "$health_data" | grep -o '"version":"[^"]*"' | sed 's/"version":"\([^"]*\)"/\1/')
        local uptime=$(echo "$health_data" | grep -o '"uptime_seconds":[0-9.]*' | sed 's/"uptime_seconds":\([0-9.]*\)/\1/')
        local active_tasks=$(echo "$health_data" | grep -o '"active_tasks":[0-9]*' | sed 's/"active_tasks":\([0-9]*\)/\1/')
        local last_check=$(echo "$health_data" | grep -o '"last_health_check":"[^"]*"' | sed 's/"last_health_check":"\([^"]*\)"/\1/')
        
        echo "  服务名称: ${service_name:-N/A}"
        echo "  状态: ${status:-N/A}"
        echo "  版本: ${version:-N/A}"
        if [[ -n "$uptime" ]]; then
            local uptime_minutes=$(echo "$uptime" | awk '{print int($1/60)}')
            echo "  运行时间: ${uptime_minutes}分钟"
        else
            echo "  运行时间: N/A"
        fi
        echo "  活动任务: ${active_tasks:-0}个"
        echo "  最后健康检查: ${last_check:-N/A}"
    else
        echo -e "${RED}❌ 无法获取健康状态${NC}"
    fi
}

# 查看最近日志
get_recent_logs() {
    echo -e "${BLUE}📋 获取最近日志...${NC}"
    
    local time_filter=${1:-"1h"}
    
    gcloud logging read \
        'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'"' \
        --project=$PROJECT_ID \
        --limit=20 \
        --format="table(timestamp, severity, textPayload)" \
        --freshness=$time_filter
}

# 持续监控日志
watch_logs() {
    echo -e "${BLUE}📋 开始持续监控日志 (按 Ctrl+C 退出)...${NC}"
    echo -e "${YELLOW}实时显示 Cloud Run 日志，每5秒刷新一次${NC}"
    echo -e "${CYAN}=================================================${NC}"
    
    local last_timestamp=""
    
    while true; do
        echo -e "${WHITE}📊 日志监控 - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
        echo -e "${CYAN}=================================================${NC}"
        
        # 获取最新日志
        local logs=$(gcloud logging read \
            'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'"' \
            --project=$PROJECT_ID \
            --limit=15 \
            --format="table(timestamp, severity, textPayload)" \
            --freshness=10m 2>/dev/null)
        
        if [[ -n "$logs" ]]; then
            echo "$logs"
            
            # 提取任务进度信息
            local progress_info=$(echo "$logs" | grep -E "进度.*页|Progress.*page" | tail -1)
            if [[ -n "$progress_info" ]]; then
                echo -e "${GREEN}📈 最新进度: $progress_info${NC}"
            fi
            
            # 检查是否有错误
            local error_count=$(echo "$logs" | grep -i "error\|exception\|failed" | wc -l)
            if [[ $error_count -gt 0 ]]; then
                echo -e "${RED}⚠️ 发现 $error_count 个错误日志${NC}"
            fi
        else
            echo -e "${YELLOW}暂无新日志${NC}"
        fi
        
        echo -e "${CYAN}=================================================${NC}"
        echo -e "${YELLOW}⏱️ 5秒后刷新... (按 Ctrl+C 退出)${NC}"
        
                 sleep 5
         clear
     done
}

# 实时追踪日志 (类似 tail -f)
tail_logs() {
    echo -e "${BLUE}📋 开始实时追踪日志 (类似 tail -f, 按 Ctrl+C 退出)...${NC}"
    echo -e "${YELLOW}只显示新的日志条目，流式输出${NC}"
    echo -e "${CYAN}=================================================${NC}"
    
    local last_timestamp=""
    local first_run=true
    
    while true; do
        # 获取最新日志
        local logs=$(gcloud logging read \
            'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'"' \
            --project=$PROJECT_ID \
            --limit=10 \
            --format="csv(timestamp, severity, textPayload)" \
            --freshness=2m 2>/dev/null)
        
        if [[ -n "$logs" ]]; then
            # 跳过CSV标题行
            logs=$(echo "$logs" | tail -n +2)
            
            # 如果是第一次运行，显示最近的几条日志
            if [[ "$first_run" == "true" ]]; then
                echo -e "${CYAN}=== 最近的日志 ===${NC}"
                echo "$logs" | tail -3 | while IFS=',' read -r timestamp severity payload; do
                    # 清理时间戳和内容
                    timestamp=$(echo "$timestamp" | tr -d '"')
                    payload=$(echo "$payload" | tr -d '"')
                    
                    # 格式化输出
                    local time_short=$(echo "$timestamp" | cut -d'T' -f2 | cut -d'.' -f1)
                    
                    # 根据内容添加颜色
                    if [[ "$payload" == *"进度"* ]] || [[ "$payload" == *"📈"* ]]; then
                        echo -e "${GREEN}[$time_short] $payload${NC}"
                    elif [[ "$payload" == *"错误"* ]] || [[ "$payload" == *"Error"* ]]; then
                        echo -e "${RED}[$time_short] $payload${NC}"
                    elif [[ "$payload" == *"获取"* ]] || [[ "$payload" == *"🔄"* ]]; then
                        echo -e "${BLUE}[$time_short] $payload${NC}"
                    else
                        echo -e "${WHITE}[$time_short] $payload${NC}"
                    fi
                done
                echo -e "${CYAN}=== 开始实时追踪 ===${NC}"
                first_run=false
                last_timestamp=$(echo "$logs" | head -1 | cut -d',' -f1 | tr -d '"')
            else
                # 只显示新的日志条目
                local new_logs=""
                while IFS=',' read -r timestamp severity payload; do
                    timestamp=$(echo "$timestamp" | tr -d '"')
                    payload=$(echo "$payload" | tr -d '"')
                    
                    # 如果时间戳比上次记录的新，就显示
                    if [[ "$timestamp" > "$last_timestamp" ]]; then
                        local time_short=$(echo "$timestamp" | cut -d'T' -f2 | cut -d'.' -f1)
                        
                        # 根据内容添加颜色和图标
                        if [[ "$payload" == *"进度"* ]] || [[ "$payload" == *"📈"* ]]; then
                            echo -e "${GREEN}🚀 [$time_short] $payload${NC}"
                        elif [[ "$payload" == *"错误"* ]] || [[ "$payload" == *"Error"* ]]; then
                            echo -e "${RED}❌ [$time_short] $payload${NC}"
                        elif [[ "$payload" == *"获取"* ]] || [[ "$payload" == *"🔄"* ]]; then
                            echo -e "${BLUE}📡 [$time_short] $payload${NC}"
                        elif [[ "$payload" == *"完成"* ]] || [[ "$payload" == *"成功"* ]]; then
                            echo -e "${GREEN}✅ [$time_short] $payload${NC}"
                        else
                            echo -e "${WHITE}📝 [$time_short] $payload${NC}"
                        fi
                        
                        last_timestamp="$timestamp"
                    fi
                done <<< "$logs"
            fi
        fi
        
        sleep 2
    done
}

# 查看任务状态
get_task_status() {
    echo -e "${BLUE}📊 获取任务执行状态...${NC}"
    
    local tasks_data=$(curl -s "$SERVICE_URL/tasks?limit=10" 2>/dev/null)
    
    if [[ $? -eq 0 ]]; then
        echo -e "${WHITE}最近任务:${NC}"
        
        # 检查是否有任务
        if echo "$tasks_data" | grep -q '"tasks":\[\]'; then
            echo "  无活动任务"
        elif echo "$tasks_data" | grep -q '"tasks":\['; then
            # 解析任务数据（不依赖jq）
            local task_count=$(echo "$tasks_data" | grep -o '"total":[0-9]*' | sed 's/"total":\([0-9]*\)/\1/')
            echo "  总任务数: ${task_count:-0}"
            
            # 提取任务信息
            echo "$tasks_data" | sed 's/},{/\n},{/g' | grep -o '"id":"[^"]*"' | head -5 | while read -r id_line; do
                local task_id=$(echo "$id_line" | sed 's/"id":"\([^"]*\)"/\1/')
                echo "  任务ID: $task_id"
                
                # 获取对应的状态和进度
                local task_block=$(echo "$tasks_data" | grep -A 10 -B 5 "\"id\":\"$task_id\"")
                local status=$(echo "$task_block" | grep -o '"status":"[^"]*"' | sed 's/"status":"\([^"]*\)"/\1/')
                local progress=$(echo "$task_block" | grep -o '"progress":"[^"]*"' | sed 's/"progress":"\([^"]*\)"/\1/')
                
                echo "  状态: ${status:-N/A}"
                echo "  进度: ${progress:-N/A}"
                echo "  ---"
            done
        else
            echo "  无活动任务"
        fi
    else
        echo -e "${RED}❌ 无法获取任务状态${NC}"
    fi
}

# 查看性能指标
get_metrics() {
    echo -e "${BLUE}📈 获取性能指标...${NC}"
    
    # CPU使用率
    gcloud monitoring metrics list --filter="metric.type:run.googleapis.com/container/cpu/utilizations" --limit=1 >/dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        echo -e "${WHITE}CPU 使用率 (最近1小时):${NC}"
        gcloud monitoring metrics-descriptors describe run.googleapis.com/container/cpu/utilizations --format="value(description)" 2>/dev/null || echo "  无法获取CPU指标"
    fi
    
    # 内存使用率
    echo -e "${WHITE}内存配置:${NC}"
    gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(spec.template.spec.containers[0].resources.limits.memory)" 2>/dev/null | sed 's/^/  /'
    
    # 请求计数
    echo -e "${WHITE}最近请求活动:${NC}"
    local recent_requests=$(gcloud logging read \
        'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'" AND httpRequest.requestMethod!=""' \
        --project=$PROJECT_ID \
        --limit=5 \
        --format="value(httpRequest.requestMethod, httpRequest.status, timestamp)" \
        --freshness=1h 2>/dev/null)
    
    if [[ -n "$recent_requests" ]]; then
        echo "$recent_requests" | head -5 | sed 's/^/  /'
    else
        echo "  无最近请求记录"
    fi
}

# 查看错误日志
get_error_logs() {
    echo -e "${BLUE}🚨 获取错误日志...${NC}"
    
    gcloud logging read \
        'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'" AND (severity="ERROR" OR severity="WARNING" OR textPayload:"Exception" OR textPayload:"Error")' \
        --project=$PROJECT_ID \
        --limit=10 \
        --format="table(timestamp, severity, textPayload)" \
        --freshness=24h
}

# 查看云调度器状态
get_scheduler_status() {
    echo -e "${BLUE}⏰ 获取云调度器状态...${NC}"
    
    gcloud scheduler jobs describe reporter-agent-all-8am --location=$REGION --format="table(state, schedule, timeZone, httpTarget.uri)" 2>/dev/null || echo -e "${RED}❌ 无法获取调度器状态${NC}"
}

# 实时监控
watch_service() {
    echo -e "${BLUE}👁️ 开始实时监控服务 (按 Ctrl+C 退出)...${NC}"
    
    while true; do
        clear
        echo -e "${WHITE}📊 Reporter-Agent 实时监控 - $(date)${NC}"
        echo -e "${CYAN}=================================================${NC}"
        
        get_service_status
        echo ""
        get_health_status
        echo ""
        get_task_status
        echo ""
        echo -e "${YELLOW}⏱️ 5秒后刷新...${NC}"
        
        sleep 5
    done
}

# 显示所有监控信息
show_all() {
    echo -e "${WHITE}📋 Reporter-Agent 完整监控报告${NC}"
    echo -e "${CYAN}=================================================${NC}"
    
    get_service_status
    echo ""
    get_health_status
    echo ""
    get_task_status
    echo ""
    get_recent_logs "30m"
    echo ""
    get_scheduler_status
    echo ""
    get_metrics
}

# 主函数
main() {
    case "$1" in
        "status")
            get_service_status
            ;;
        "health")
            get_health_status
            ;;
        "logs")
            get_recent_logs "${2:-1h}"
            ;;
        "logs-watch")
            watch_logs
            ;;
        "tail")
            tail_logs
            ;;
        "tasks")
            get_task_status
            ;;
        "metrics")
            get_metrics
            ;;
        "watch")
            watch_service
            ;;
        "errors")
            get_error_logs
            ;;
        "scheduler")
            get_scheduler_status
            ;;
        "all")
            show_all
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@" 
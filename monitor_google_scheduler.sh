#!/bin/bash
# Google Cloud Scheduler 监控脚本
# 全面监控 Cloud Scheduler 任务状态、执行历史和性能

set -e

# 配置参数
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
JOB_NAME="reporter-agent-all-8am"
SERVICE_NAME="reporter-agent"
SERVICE_URL="https://reporter-agent-472712465571.asia-southeast1.run.app"
# 注意：真实的服务URL与gcloud查询的可能不同，使用实际工作的URL

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
    echo -e "${WHITE}⏰ Google Cloud Scheduler 监控工具${NC}"
    echo -e "${CYAN}=============================================${NC}"
    echo -e "${WHITE}用法:${NC} $0 [命令]"
    echo ""
    echo -e "${WHITE}可用命令:${NC}"
    echo -e "  ${GREEN}status${NC}      - 查看调度器状态"
    echo -e "  ${GREEN}history${NC}     - 查看执行历史"
    echo -e "  ${GREEN}today${NC}       - 查看今天的执行情况"
    echo -e "  ${GREEN}logs${NC}        - 查看调度器日志"
    echo -e "  ${GREEN}errors${NC}      - 查看错误日志"
    echo -e "  ${GREEN}metrics${NC}     - 查看性能指标"
    echo -e "  ${GREEN}watch${NC}       - 实时监控"
    echo -e "  ${GREEN}test${NC}        - 手动测试执行"
    echo -e "  ${GREEN}timezone${NC}    - 检查时区配置"
    echo -e "  ${GREEN}next${NC}        - 查看下次执行时间"
    echo -e "  ${GREEN}all${NC}         - 显示所有监控信息"
    echo -e "  ${GREEN}help${NC}        - 显示此帮助信息"
    echo ""
    echo -e "${WHITE}示例:${NC}"
    echo -e "  $0 status       # 查看调度器状态"
    echo -e "  $0 today        # 查看今天执行情况"
    echo -e "  $0 watch        # 实时监控"
    echo -e "  $0 test         # 手动测试执行"
    echo ""
}

# 设置项目
setup_project() {
    gcloud config set project $PROJECT_ID --quiet
}

# 获取调度器状态
get_scheduler_status() {
    echo -e "${BLUE}📊 获取调度器状态...${NC}"
    
    local job_info=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(name,schedule,timeZone,state,description,httpTarget.uri)" 2>/dev/null)
    
    if [[ -n "$job_info" ]]; then
        echo -e "${WHITE}任务信息:${NC}"
        echo "$job_info" | while IFS=$'\t' read -r name schedule timezone state description uri; do
            echo "  名称: $name"
            echo "  计划: $schedule"
            echo "  时区: $timezone"
            echo "  状态: $([ "$state" = "ENABLED" ] && echo -e "${GREEN}$state${NC}" || echo -e "${RED}$state${NC}")"
            echo "  描述: $description"
            echo "  目标: $uri"
        done
    else
        echo -e "${RED}❌ 无法获取调度器状态${NC}"
        return 1
    fi
    
    # 获取最后执行时间
    local last_attempt=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(status.lastAttemptTime)" 2>/dev/null)
    if [[ -n "$last_attempt" ]]; then
        echo "  最后执行: $last_attempt"
    fi
}

# 获取执行历史
get_execution_history() {
    local days=${1:-7}
    echo -e "${BLUE}📈 获取最近 $days 天的执行历史...${NC}"
    
    local executions=$(gcloud logging read \
        'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'"' \
        --limit=50 \
        --format="table(timestamp,severity,textPayload)" \
        --freshness=${days}d 2>/dev/null)
    
    if [[ -n "$executions" ]]; then
        echo "$executions"
    else
        echo -e "${YELLOW}⚠️ 无执行历史记录${NC}"
    fi
}

# 获取今天的执行情况
get_today_execution() {
    echo -e "${BLUE}📅 获取今天的执行情况...${NC}"
    
    local today=$(date +"%Y-%m-%d")
    local today_utc=$(date -u +"%Y-%m-%d")
    
    echo -e "${WHITE}今天 ($today) 的执行记录:${NC}"
    
    local executions=$(gcloud logging read \
        'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'" AND timestamp>="'$today_utc'T00:00:00Z"' \
        --limit=10 \
        --format="value(timestamp,severity)" \
        --freshness=24h 2>/dev/null)
    
    if [[ -n "$executions" ]]; then
        echo "$executions" | while IFS=$'\t' read -r timestamp severity; do
            if [[ -n "$timestamp" ]]; then
                # 转换为新加坡时间
                local sg_time=$(python3 -c "
import datetime
utc_time = datetime.datetime.fromisoformat('$timestamp'.replace('Z', '+00:00'))
sg_time = utc_time + datetime.timedelta(hours=8)
print(sg_time.strftime('%Y-%m-%d %H:%M:%S'))
" 2>/dev/null || echo "无法转换")
                
                # 检查是否在正确时间执行
                local hour=$(python3 -c "
import datetime
utc_time = datetime.datetime.fromisoformat('$timestamp'.replace('Z', '+00:00'))
sg_time = utc_time + datetime.timedelta(hours=8)
print(sg_time.hour)
" 2>/dev/null || echo "0")
                
                if [[ "$hour" = "8" ]]; then
                    echo -e "  ✅ $sg_time (正常8点执行) - $severity"
                else
                    echo -e "  ❌ $sg_time (异常时间) - $severity"
                fi
            fi
        done
    else
        echo -e "${YELLOW}  今天还没有执行记录${NC}"
    fi
    
    # 显示下次执行时间
    local tomorrow
    if [[ "$OSTYPE" == "darwin"* ]]; then
        tomorrow=$(date -v+1d +"%Y-%m-%d")
    else
        tomorrow=$(date -d "tomorrow" +"%Y-%m-%d")
    fi
    echo -e "${WHITE}明天预期执行时间:${NC}"
    echo "  $tomorrow 08:00:00 (Asia/Singapore)"
}

# 获取调度器日志
get_scheduler_logs() {
    local hours=${1:-24}
    echo -e "${BLUE}📝 获取最近 $hours 小时的调度器日志...${NC}"
    
    gcloud logging read \
        'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'"' \
        --limit=20 \
        --format="table(timestamp,severity,textPayload)" \
        --freshness=${hours}h 2>/dev/null || echo -e "${YELLOW}⚠️ 无日志记录${NC}"
}

# 获取错误日志
get_error_logs() {
    echo -e "${BLUE}🚨 获取错误日志...${NC}"
    
    # 调度器错误
    echo -e "${WHITE}调度器错误:${NC}"
    gcloud logging read \
        'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'" AND (severity="ERROR" OR severity="WARNING")' \
        --limit=10 \
        --format="table(timestamp,severity,textPayload)" \
        --freshness=24h 2>/dev/null || echo "  无错误记录"
    
    # Cloud Run 服务错误
    echo -e "${WHITE}Cloud Run 服务错误:${NC}"
    gcloud logging read \
        'resource.type="cloud_run_revision" AND resource.labels.service_name="'$SERVICE_NAME'" AND (severity="ERROR" OR textPayload:"Exception" OR textPayload:"timeout")' \
        --limit=10 \
        --format="table(timestamp,severity,textPayload)" \
        --freshness=24h 2>/dev/null || echo "  无错误记录"
}

# 获取性能指标
get_metrics() {
    echo -e "${BLUE}📊 获取性能指标...${NC}"
    
    # 执行成功率统计
    echo -e "${WHITE}执行成功率统计 (最近7天):${NC}"
    local success_count=$(gcloud logging read \
        'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'" AND severity="INFO"' \
        --limit=100 \
        --format="value(timestamp)" \
        --freshness=168h 2>/dev/null | wc -l)
    
    local error_count=$(gcloud logging read \
        'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'" AND severity="ERROR"' \
        --limit=100 \
        --format="value(timestamp)" \
        --freshness=168h 2>/dev/null | wc -l)
    
    local total_count=$((success_count + error_count))
    
    if [[ $total_count -gt 0 ]]; then
        local success_rate=$(python3 -c "print(f'{$success_count/$total_count*100:.1f}')" 2>/dev/null || echo "0")
        echo "  成功执行: $success_count 次"
        echo "  失败执行: $error_count 次"
        echo "  成功率: $success_rate%"
    else
        echo "  无执行记录"
    fi
    
    # Cloud Run 服务指标
    echo -e "${WHITE}Cloud Run 服务状态:${NC}"
    # 使用正确的服务URL
    echo "  服务URL: $SERVICE_URL"
    
    # 尝试获取服务配置信息
    local service_info=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(spec.template.spec.timeoutSeconds,spec.template.spec.containers[0].resources.limits.memory)" 2>/dev/null)
    if [[ -n "$service_info" ]]; then
        echo "$service_info" | while IFS=$'\t' read -r timeout memory; do
            echo "  超时设置: $timeout 秒"
            echo "  内存限制: $memory"
        done
    else
        echo "  超时设置: 3600 秒 (Cloud Scheduler配置)"
        echo "  内存限制: 配置信息不可用"
    fi
}

# 检查时区配置
check_timezone() {
    echo -e "${BLUE}🌍 检查时区配置...${NC}"
    
    local timezone=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(timeZone)" 2>/dev/null)
    local schedule=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(schedule)" 2>/dev/null)
    
    echo -e "${WHITE}时区配置:${NC}"
    echo "  时区: $timezone"
    echo "  计划: $schedule"
    
    if [[ "$timezone" = "Asia/Singapore" ]]; then
        echo -e "  状态: ${GREEN}✅ 正确${NC}"
    else
        echo -e "  状态: ${RED}❌ 需要修复${NC}"
        echo -e "  建议: 使用 ./fix_scheduler_timezone.sh 修复"
    fi
    
    # 显示当前时间
    echo -e "${WHITE}当前时间:${NC}"
    echo "  UTC: $(date -u)"
    echo "  Singapore: $(TZ=Asia/Singapore date)"
}

# 查看下次执行时间
get_next_execution() {
    echo -e "${BLUE}⏰ 查看下次执行时间...${NC}"
    
    local schedule=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(schedule)" 2>/dev/null)
    local timezone=$(gcloud scheduler jobs describe $JOB_NAME --location=$REGION --format="value(timeZone)" 2>/dev/null)
    
    echo -e "${WHITE}调度配置:${NC}"
    echo "  Cron: $schedule"
    echo "  时区: $timezone"
    
    # 计算下次执行时间
    if [[ "$schedule" = "0 8 * * *" ]]; then
        local tomorrow
        if [[ "$OSTYPE" == "darwin"* ]]; then
            tomorrow=$(date -v+1d +"%Y-%m-%d")
        else
            tomorrow=$(date -d "tomorrow" +"%Y-%m-%d")
        fi
        echo -e "${WHITE}下次执行:${NC}"
        echo "  日期: $tomorrow 08:00:00"
        echo "  时区: $timezone"
        
        # 计算剩余时间
        local next_run
        if [[ "$OSTYPE" == "darwin"* ]]; then
            next_run=$(date -j -f "%Y-%m-%d %H:%M:%S" "$tomorrow 08:00:00" +%s)
        else
            next_run=$(date -d "$tomorrow 08:00:00" +%s)
        fi
        local current_time=$(date +%s)
        local remaining=$((next_run - current_time))
        
        if [[ $remaining -gt 0 ]]; then
            local hours=$((remaining / 3600))
            local minutes=$(((remaining % 3600) / 60))
            echo "  剩余: ${hours}小时${minutes}分钟"
        else
            echo "  剩余: 即将执行"
        fi
    fi
}

# 手动测试执行
test_execution() {
    echo -e "${BLUE}🧪 手动测试执行...${NC}"
    
    echo -e "${YELLOW}警告: 这将手动触发调度器任务${NC}"
    read -p "确认执行? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}✅ 开始手动执行...${NC}"
        gcloud scheduler jobs run $JOB_NAME --location=$REGION
        
        echo -e "${BLUE}📝 等待执行结果...${NC}"
        sleep 5
        
        # 检查最近的执行日志
        echo -e "${WHITE}最近执行日志:${NC}"
        gcloud logging read \
            'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'"' \
            --limit=3 \
            --format="table(timestamp,severity,textPayload)" \
            --freshness=5m 2>/dev/null || echo "  无日志记录"
    else
        echo -e "${YELLOW}❌ 取消执行${NC}"
    fi
}

# 实时监控
watch_scheduler() {
    echo -e "${BLUE}👁️ 开始实时监控调度器 (按 Ctrl+C 退出)...${NC}"
    
    while true; do
        clear
        echo -e "${WHITE}⏰ Google Cloud Scheduler 实时监控 - $(date)${NC}"
        echo -e "${CYAN}=============================================${NC}"
        
        get_scheduler_status
        echo ""
        get_today_execution
        echo ""
        get_next_execution
        echo ""
        
        # 检查最近的执行
        echo -e "${WHITE}最近执行 (5分钟内):${NC}"
        local recent=$(gcloud logging read \
            'resource.type="cloud_scheduler_job" AND resource.labels.job_id="'$JOB_NAME'"' \
            --limit=3 \
            --format="value(timestamp,severity)" \
            --freshness=5m 2>/dev/null)
        
        if [[ -n "$recent" ]]; then
            echo "$recent" | sed 's/^/  /'
        else
            echo "  无最近执行记录"
        fi
        
        echo ""
        echo -e "${YELLOW}⏱️ 10秒后刷新...${NC}"
        sleep 10
    done
}

# 显示所有监控信息
show_all() {
    echo -e "${WHITE}⏰ Google Cloud Scheduler 完整监控报告${NC}"
    echo -e "${CYAN}=============================================${NC}"
    
    get_scheduler_status
    echo ""
    get_today_execution
    echo ""
    get_execution_history 7
    echo ""
    get_metrics
    echo ""
    check_timezone
    echo ""
    get_next_execution
    echo ""
    get_error_logs
}

# 主函数
main() {
    setup_project
    
    case "${1:-help}" in
        "status")
            get_scheduler_status
            ;;
        "history")
            get_execution_history ${2:-7}
            ;;
        "today")
            get_today_execution
            ;;
        "logs")
            get_scheduler_logs ${2:-24}
            ;;
        "errors")
            get_error_logs
            ;;
        "metrics")
            get_metrics
            ;;
        "timezone")
            check_timezone
            ;;
        "next")
            get_next_execution
            ;;
        "test")
            test_execution
            ;;
        "watch")
            watch_scheduler
            ;;
        "all")
            show_all
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 检查依赖
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ 错误: gcloud CLI 未安装${NC}"
    echo "请访问 https://cloud.google.com/sdk/docs/install 安装 Google Cloud SDK"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误: python3 未安装${NC}"
    exit 1
fi

# 运行主函数
main "$@" 
#!/bin/bash
# 简化版Google Cloud监控配置脚本
# 避免使用alpha命令，直接配置基本监控

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="bytec-public-postback"
REGION="asia-southeast1"
SERVICE_URL="https://bytec-public-postback-crwdeesavq-as.a.run.app"

echo -e "${BLUE}🔍 ByteC Postback - 简化监控配置${NC}"
echo -e "${BLUE}==========================================${NC}"
echo -e "${YELLOW}📋 项目: $PROJECT_ID${NC}"
echo -e "${YELLOW}🏷️ 服务: $SERVICE_NAME${NC}"
echo -e "${YELLOW}🌍 地区: $REGION${NC}"
echo -e "${YELLOW}🌐 服务URL: $SERVICE_URL${NC}"
echo ""

# 设置项目
echo -e "${YELLOW}🔧 设置Google Cloud项目...${NC}"
gcloud config set project $PROJECT_ID

# 检查已启用的APIs
echo -e "${YELLOW}📋 检查监控APIs状态...${NC}"
MONITORING_ENABLED=$(gcloud services list --enabled --filter="name:monitoring.googleapis.com" --format="value(name)" | wc -l)
LOGGING_ENABLED=$(gcloud services list --enabled --filter="name:logging.googleapis.com" --format="value(name)" | wc -l)

if [ "$MONITORING_ENABLED" -eq 0 ]; then
    echo -e "${YELLOW}🔧 启用监控API...${NC}"
    gcloud services enable monitoring.googleapis.com
fi

if [ "$LOGGING_ENABLED" -eq 0 ]; then
    echo -e "${YELLOW}🔧 启用日志API...${NC}"
    gcloud services enable logging.googleapis.com
fi

echo -e "${GREEN}✅ APIs检查完成${NC}"

# 创建监控配置目录
mkdir -p monitoring_config
cd monitoring_config

# 创建基础监控脚本
echo -e "${YELLOW}📊 创建监控脚本...${NC}"

cat > check_service_health.sh << 'EOF'
#!/bin/bash
# ByteC Postback服务健康检查脚本

SERVICE_URL="https://bytec-public-postback-crwdeesavq-as.a.run.app"
LOG_FILE="monitoring_log.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "[$TIMESTAMP] 开始健康检查..." >> $LOG_FILE

# 健康检查
RESPONSE=$(curl -s -w "\n%{http_code}\n%{time_total}" "$SERVICE_URL/health" || echo "ERROR")
HTTP_CODE=$(echo "$RESPONSE" | tail -2 | head -1)
RESPONSE_TIME=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "[$TIMESTAMP] ✅ 服务正常 - 响应时间: ${RESPONSE_TIME}s" >> $LOG_FILE
    echo "✅ 服务正常运行"
else
    echo "[$TIMESTAMP] ❌ 服务异常 - HTTP状态: $HTTP_CODE" >> $LOG_FILE
    echo "❌ 服务异常: HTTP $HTTP_CODE"
fi

# 测试postback端点
POSTBACK_RESPONSE=$(curl -s -w "%{http_code}" "$SERVICE_URL/involve/event?sub_id=monitor_test&conversion_id=health_check_$(date +%s)" || echo "ERROR")
POSTBACK_CODE=$(echo "$POSTBACK_RESPONSE" | tail -c 4)

if [ "$POSTBACK_CODE" = "200" ]; then
    echo "[$TIMESTAMP] ✅ Postback端点正常" >> $LOG_FILE
    echo "✅ Postback端点正常"
else
    echo "[$TIMESTAMP] ❌ Postback端点异常 - HTTP状态: $POSTBACK_CODE" >> $LOG_FILE
    echo "❌ Postback端点异常: HTTP $POSTBACK_CODE"
fi

echo "[$TIMESTAMP] 检查完成" >> $LOG_FILE
echo "详细日志: $LOG_FILE"
EOF

chmod +x check_service_health.sh

# 创建日志查看脚本
cat > view_logs.sh << 'EOF'
#!/bin/bash
# 查看Cloud Run服务日志

PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="bytec-public-postback"
REGION="asia-southeast1"

echo "🔍 最近的服务日志:"
echo "==================="

gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
    --limit=20 \
    --format="table(timestamp,severity,textPayload)" \
    --project=$PROJECT_ID

echo ""
echo "🔍 错误日志:"
echo "============"

gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" \
    --limit=10 \
    --format="table(timestamp,severity,textPayload)" \
    --project=$PROJECT_ID
EOF

chmod +x view_logs.sh

# 创建性能监控脚本
cat > performance_test.sh << 'EOF'
#!/bin/bash
# ByteC Postback性能测试脚本

SERVICE_URL="https://bytec-public-postback-crwdeesavq-as.a.run.app"
REPORT_FILE="performance_report.txt"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "ByteC Postback 性能测试报告" > $REPORT_FILE
echo "测试时间: $TIMESTAMP" >> $REPORT_FILE
echo "=============================" >> $REPORT_FILE

echo "🚀 开始性能测试..."

# 响应时间测试
echo "📊 响应时间测试:" >> $REPORT_FILE
for i in {1..5}; do
    RESPONSE_TIME=$(curl -s -w "%{time_total}" -o /dev/null "$SERVICE_URL/health")
    echo "  测试 $i: ${RESPONSE_TIME}s" >> $REPORT_FILE
    echo "测试 $i: ${RESPONSE_TIME}s"
    sleep 1
done

# 并发测试
echo "" >> $REPORT_FILE
echo "📊 并发测试 (5个并发请求):" >> $REPORT_FILE
for i in {1..5}; do
    curl -s "$SERVICE_URL/involve/event?sub_id=test$i&conversion_id=perf_test_$i" > /dev/null &
done
wait
echo "  5个并发请求完成" >> $REPORT_FILE
echo "5个并发请求完成"

echo "" >> $REPORT_FILE
echo "测试完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> $REPORT_FILE

echo "✅ 性能测试完成，报告保存到: $REPORT_FILE"
EOF

chmod +x performance_test.sh

# 创建监控面板URL文件
cat > monitoring_urls.txt << EOF
ByteC Postback 监控访问地址
===========================

Google Cloud Console:
- 项目主页: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID
- Cloud Run服务: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID
- 日志查看: https://console.cloud.google.com/logs/query?project=$PROJECT_ID
- 监控概览: https://console.cloud.google.com/monitoring/overview?project=$PROJECT_ID

服务URL:
- 服务主页: $SERVICE_URL
- 健康检查: $SERVICE_URL/health
- Postback端点: $SERVICE_URL/involve/event

本地监控脚本:
- 健康检查: ./check_service_health.sh
- 查看日志: ./view_logs.sh  
- 性能测试: ./performance_test.sh

生成时间: $(date '+%Y-%m-%d %H:%M:%S')
EOF

echo -e "${GREEN}✅ 监控配置完成！${NC}"
echo -e "${BLUE}📁 配置文件保存在: monitoring_config/目录${NC}"
echo ""
echo -e "${YELLOW}🔧 可用的监控工具:${NC}"
echo "  1. ./monitoring_config/check_service_health.sh  - 健康检查"
echo "  2. ./monitoring_config/view_logs.sh            - 查看日志"
echo "  3. ./monitoring_config/performance_test.sh     - 性能测试"
echo "  4. ./monitoring_config/monitoring_urls.txt     - 监控地址"
echo ""

# 执行初始健康检查
echo -e "${BLUE}🧪 执行初始健康检查...${NC}"
cd monitoring_config
./check_service_health.sh
cd ..

echo -e "${GREEN}🎉 简化监控配置完成！${NC}"
echo -e "${YELLOW}💡 提示: 你可以将健康检查脚本添加到cron任务中进行定期监控${NC}"
echo "   例如: */5 * * * * /path/to/check_service_health.sh" 
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

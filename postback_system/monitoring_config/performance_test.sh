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

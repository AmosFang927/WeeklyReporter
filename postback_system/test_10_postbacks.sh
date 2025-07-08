#!/bin/bash

# 测试10笔postback数据发送脚本
POSTBACK_URL="https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event"

echo "🚀 开始发送10笔测试postback数据..."
echo "📍 目标URL: $POSTBACK_URL"
echo "----------------------------------------"

# 发送10笔不同的测试数据
echo "📤 发送测试数据 1/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_001&media_id=campaign_mobile&click_id=click_001&usd_sale_amount=199.99&usd_payout=29.99&offer_name=Premium%20Software%20Suite&conversion_id=TEST_CONV_001&datetime_conversion=2025-07-07T21:30:00Z"

echo -e "\n📤 发送测试数据 2/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_002&media_id=campaign_desktop&click_id=click_002&usd_sale_amount=99.50&usd_payout=14.93&offer_name=Gaming%20Platform&conversion_id=TEST_CONV_002&datetime_conversion=2025-07-07T21:31:00Z"

echo -e "\n📤 发送测试数据 3/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_003&media_id=campaign_social&click_id=click_003&usd_sale_amount=149.99&usd_payout=22.50&offer_name=E-commerce%20Plan&conversion_id=TEST_CONV_003&datetime_conversion=2025-07-07T21:32:00Z"

echo -e "\n📤 发送测试数据 4/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_001&media_id=campaign_email&click_id=click_004&usd_sale_amount=299.00&usd_payout=44.85&offer_name=Enterprise%20License&conversion_id=TEST_CONV_004&datetime_conversion=2025-07-07T21:33:00Z"

echo -e "\n📤 发送测试数据 5/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_004&media_id=campaign_mobile&click_id=click_005&usd_sale_amount=49.99&usd_payout=7.50&offer_name=Mobile%20App%20Pro&conversion_id=TEST_CONV_005&datetime_conversion=2025-07-07T21:34:00Z"

echo -e "\n📤 发送测试数据 6/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_005&media_id=campaign_search&click_id=click_006&usd_sale_amount=79.99&usd_payout=12.00&offer_name=Cloud%20Storage&conversion_id=TEST_CONV_006&datetime_conversion=2025-07-07T21:35:00Z"

echo -e "\n📤 发送测试数据 7/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_002&media_id=campaign_retargeting&click_id=click_007&usd_sale_amount=189.99&usd_payout=28.50&offer_name=Design%20Software&conversion_id=TEST_CONV_007&datetime_conversion=2025-07-07T21:36:00Z"

echo -e "\n📤 发送测试数据 8/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_006&media_id=campaign_affiliate&click_id=click_008&usd_sale_amount=399.99&usd_payout=60.00&offer_name=Video%20Editor%20Pro&conversion_id=TEST_CONV_008&datetime_conversion=2025-07-07T21:37:00Z"

echo -e "\n📤 发送测试数据 9/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_003&media_id=campaign_social&click_id=click_009&usd_sale_amount=59.99&usd_payout=9.00&offer_name=Productivity%20Bundle&conversion_id=TEST_CONV_009&datetime_conversion=2025-07-07T21:38:00Z"

echo -e "\n📤 发送测试数据 10/10..."
curl -s -w "HTTP Status: %{http_code}\n" "$POSTBACK_URL?sub_id=test_affiliate_007&media_id=campaign_content&click_id=click_010&usd_sale_amount=129.99&usd_payout=19.50&offer_name=Marketing%20Tools&conversion_id=TEST_CONV_010&datetime_conversion=2025-07-07T21:39:00Z"

echo -e "\n✅ 所有测试数据发送完成！"
echo "----------------------------------------"

# 等待数据处理
echo "⏳ 等待3秒让数据完全处理..."
sleep 3

# 查询统计信息
echo "📊 查询系统统计信息..."
curl -s "https://bytec-public-postback-472712465571.asia-southeast1.run.app/postback/stats" | jq '.' 2>/dev/null || curl -s "https://bytec-public-postback-472712465571.asia-southeast1.run.app/postback/stats"

echo -e "\n🎯 测试完成！" 
#!/bin/bash

echo "🔍 检查 WeeklyReporter 服务部署状态"
echo "=================================="

PROJECT_ID="solar-idea-463423-h8"
SERVICE_NAME="weeklyreporter"

echo ""
echo "📍 检查所有区域的 Cloud Run 服务："
echo ""

# 检查常见区域
regions=("asia-east1" "europe-west1" "us-central1" "asia-northeast1")

for region in "${regions[@]}"; do
    echo "🔍 检查区域: $region"
    
    # 尝试获取服务信息
    service_url=$(gcloud run services describe $SERVICE_NAME \
        --platform managed \
        --region $region \
        --project $PROJECT_ID \
        --format 'value(status.url)' 2>/dev/null)
    
    if [ $? -eq 0 ] && [ ! -z "$service_url" ]; then
        echo "✅ 找到服务！"
        echo "   🔗 URL: $service_url"
        echo "   📍 区域: $region"
        echo ""
        
        # 测试健康检查
        echo "🏥 测试健康检查："
        curl -s "$service_url/health" | head -c 200
        echo ""
        echo ""
    else
        echo "❌ 在 $region 未找到服务"
        echo ""
    fi
done

echo "=================================="
echo "✅ 检查完成" 
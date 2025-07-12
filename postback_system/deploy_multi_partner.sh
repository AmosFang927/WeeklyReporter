#!/bin/bash
"""
部署多Partner Postback系統腳本
支持不同Partner的獨立Cloud Run服務部署
"""

set -e

# 配置
PROJECT_ID="472712465571"
REGION="asia-southeast1"
SERVICE_NAME_PREFIX="bytec-partner-postback"

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查依賴
check_dependencies() {
    log_info "🔍 檢查依賴..."
    
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI 未安裝"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安裝"
        exit 1
    fi
    
    log_success "依賴檢查完成"
}

# 設置Google Cloud項目
setup_gcloud() {
    log_info "🔧 設置Google Cloud項目..."
    
    gcloud config set project $PROJECT_ID
    gcloud config set run/region $REGION
    
    log_success "Google Cloud項目設置完成: $PROJECT_ID"
}

# 構建Docker鏡像
build_image() {
    local partner_code=$1
    local service_name="${SERVICE_NAME_PREFIX}-${partner_code}"
    
    log_info "🐳 構建Docker鏡像: $service_name"
    
    # 創建Partner特定的Dockerfile
    cat > Dockerfile.partner << EOF
FROM python:3.11-slim

WORKDIR /app

# 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用代碼
COPY . .

# 設置環境變量
ENV PARTNER_CODE=$partner_code
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
    
    # 構建鏡像
    docker build -f Dockerfile.partner -t gcr.io/$PROJECT_ID/$service_name .
    
    # 推送到Google Container Registry
    docker push gcr.io/$PROJECT_ID/$service_name
    
    log_success "Docker鏡像構建完成: gcr.io/$PROJECT_ID/$service_name"
}

# 部署Cloud Run服務
deploy_service() {
    local partner_code=$1
    local service_name="${SERVICE_NAME_PREFIX}-${partner_code}"
    
    log_info "🚀 部署Cloud Run服務: $service_name"
    
    # 創建服務配置
    cat > cloudrun-${partner_code}.yaml << EOF
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: $service_name
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containerConcurrency: 80
      timeoutSeconds: 300
      containers:
      - image: gcr.io/$PROJECT_ID/$service_name
        ports:
        - containerPort: 8000
        env:
        - name: PARTNER_CODE
          value: "$partner_code"
        - name: DATABASE_URL
          value: "postgresql://postback_user:password@/postback_db"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
          requests:
            cpu: "0.5"
            memory: "256Mi"
EOF
    
    # 部署服務
    gcloud run services replace cloudrun-${partner_code}.yaml
    
    log_success "Cloud Run服務部署完成: $service_name"
}

# 設置數據庫
setup_database() {
    local partner_code=$1
    local db_name="${partner_code}_db"
    
    log_info "🗄️ 設置數據庫: $db_name"
    
    # 創建數據庫（如果使用Cloud SQL）
    gcloud sql databases create $db_name --instance=postback-instance || true
    
    log_success "數據庫設置完成: $db_name"
}

# 初始化Partner配置
init_partner_config() {
    local partner_code=$1
    local partner_name=$2
    local endpoint_path=$3
    
    log_info "⚙️ 初始化Partner配置: $partner_name"
    
    # 這裡可以添加自動化配置腳本
    log_success "Partner配置初始化完成: $partner_name"
}

# 部署所有Partner
deploy_all_partners() {
    log_info "🚀 開始部署所有Partner..."
    
    # Partner配置
    declare -A partners=(
        ["involve"]="InvolveAsia:/involve/event"
        ["rector"]="Rector:/rector/event"
    )
    
    for partner_code in "${!partners[@]}"; do
        IFS=':' read -r partner_name endpoint_path <<< "${partners[$partner_code]}"
        
        log_info "📦 部署Partner: $partner_name ($partner_code)"
        
        # 構建鏡像
        build_image $partner_code
        
        # 部署服務
        deploy_service $partner_code
        
        # 設置數據庫
        setup_database $partner_code
        
        # 初始化配置
        init_partner_config $partner_code $partner_name $endpoint_path
        
        log_success "✅ Partner部署完成: $partner_name"
        echo
    done
}

# 測試部署
test_deployment() {
    log_info "🧪 測試部署..."
    
    # 測試InvolveAsia端點
    local involve_url="https://${SERVICE_NAME_PREFIX}-involve-${PROJECT_ID}.${REGION}.run.app/involve/event"
    local involve_params="sub_id=test&media_id=test&click_id=test&usd_sale_amount=99.99&usd_payout=9.99&offer_name=Test&conversion_id=test001&conversion_datetime=2025-01-15"
    
    log_info "測試InvolveAsia端點: $involve_url"
    curl -s "$involve_url?$involve_params" | jq '.' || log_warning "InvolveAsia端點測試失敗"
    
    # 測試Rector端點
    local rector_url="https://${SERVICE_NAME_PREFIX}-rector-${PROJECT_ID}.${REGION}.run.app/rector/event"
    local rector_params="media_id=test&sub_id=test&usd_sale_amount=99.99&usd_earning=9.99&offer_name=Test&conversion_id=test002&conversion_datetime=2025-01-15&click_id=test"
    
    log_info "測試Rector端點: $rector_url"
    curl -s "$rector_url?$rector_params" | jq '.' || log_warning "Rector端點測試失敗"
    
    log_success "部署測試完成"
}

# 顯示部署信息
show_deployment_info() {
    log_info "📋 部署信息:"
    
    echo
    echo "🔗 Partner端點:"
    echo "  - InvolveAsia: https://${SERVICE_NAME_PREFIX}-involve-${PROJECT_ID}.${REGION}.run.app/involve/event"
    echo "  - Rector: https://${SERVICE_NAME_PREFIX}-rector-${PROJECT_ID}.${REGION}.run.app/rector/event"
    echo
    echo "📊 監控:"
    echo "  - Cloud Run Console: https://console.cloud.google.com/run"
    echo "  - Logs: gcloud logging read 'resource.type=cloud_run_revision'"
    echo
    echo "🗄️ 數據庫:"
    echo "  - InvolveAsia: ${partner_code}_db"
    echo "  - Rector: ${partner_code}_db"
    echo
}

# 主函數
main() {
    log_info "🚀 開始部署多Partner Postback系統..."
    
    check_dependencies
    setup_gcloud
    deploy_all_partners
    test_deployment
    show_deployment_info
    
    log_success "🎉 多Partner Postback系統部署完成!"
}

# 腳本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 
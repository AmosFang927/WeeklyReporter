#!/bin/bash
# GCP Cloud SQL PostgreSQL 实例创建和配置脚本
# 包含网络和安全设置

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目配置
PROJECT_ID="solar-idea-463423-h8"
REGION="asia-southeast1"
ZONE="asia-southeast1-a"
INSTANCE_NAME="bytec-postback-db"
DATABASE_NAME="postback_db"
DB_USER="postback_admin"
DB_PASSWORD="ByteC2024PostBack_CloudSQL"

# 网络配置
VPC_NAME="bytec-postback-vpc"
SUBNET_NAME="bytec-postback-subnet"
VPC_CONNECTOR_NAME="bytec-postback-connector"
AUTHORIZED_NETWORKS="0.0.0.0/0"  # 生产环境应该限制具体IP

echo -e "${BLUE}🚀 开始创建GCP Cloud SQL PostgreSQL实例${NC}"
echo "=============================================="
echo -e "${BLUE}📋 项目: $PROJECT_ID${NC}"
echo -e "${BLUE}🏷️ 实例: $INSTANCE_NAME${NC}"
echo -e "${BLUE}🌍 地区: $REGION${NC}"
echo -e "${BLUE}🗄️ 数据库: $DATABASE_NAME${NC}"
echo "=============================================="

# 1. 检查和设置项目
echo -e "${YELLOW}1. 设置Google Cloud项目...${NC}"
gcloud config set project $PROJECT_ID

# 2. 启用必要的API服务
echo -e "${YELLOW}2. 启用必要的API服务...${NC}"
gcloud services enable sqladmin.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable vpcaccess.googleapis.com
gcloud services enable servicenetworking.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

echo -e "${GREEN}✅ API服务启用完成${NC}"

# 3. 创建VPC网络 (如果不存在)
echo -e "${YELLOW}3. 配置VPC网络...${NC}"
if ! gcloud compute networks describe $VPC_NAME --quiet 2>/dev/null; then
    echo "创建VPC网络: $VPC_NAME"
    gcloud compute networks create $VPC_NAME \
        --subnet-mode=custom \
        --description="ByteC Postback VPC网络"
else
    echo -e "${GREEN}✅ VPC网络 $VPC_NAME 已存在${NC}"
fi

# 4. 创建子网 (如果不存在)
if ! gcloud compute networks subnets describe $SUBNET_NAME --region=$REGION --quiet 2>/dev/null; then
    echo "创建子网: $SUBNET_NAME"
    gcloud compute networks subnets create $SUBNET_NAME \
        --network=$VPC_NAME \
        --region=$REGION \
        --range=10.0.0.0/28 \
        --description="ByteC Postback子网"
else
    echo -e "${GREEN}✅ 子网 $SUBNET_NAME 已存在${NC}"
fi

# 5. 配置私有服务连接
echo -e "${YELLOW}4. 配置私有服务连接...${NC}"
# 为Google服务分配IP范围
if ! gcloud compute addresses describe google-managed-services-$VPC_NAME --global --quiet 2>/dev/null; then
    gcloud compute addresses create google-managed-services-$VPC_NAME \
        --global \
        --purpose=VPC_PEERING \
        --prefix-length=16 \
        --network=$VPC_NAME \
        --description="Google管理服务的IP范围"
else
    echo -e "${GREEN}✅ Google服务IP范围已存在${NC}"
fi

# 创建私有连接
if ! gcloud services vpc-peerings list --network=$VPC_NAME --quiet | grep -q "google-managed-services-$VPC_NAME"; then
    gcloud services vpc-peerings connect \
        --service=servicenetworking.googleapis.com \
        --ranges=google-managed-services-$VPC_NAME \
        --network=$VPC_NAME \
        --project=$PROJECT_ID
else
    echo -e "${GREEN}✅ 私有服务连接已存在${NC}"
fi

# 6. 创建VPC连接器
echo -e "${YELLOW}5. 创建VPC连接器...${NC}"
if ! gcloud compute networks vpc-access connectors describe $VPC_CONNECTOR_NAME --region=$REGION --quiet 2>/dev/null; then
    gcloud compute networks vpc-access connectors create $VPC_CONNECTOR_NAME \
        --region=$REGION \
        --subnet=$SUBNET_NAME \
        --subnet-project=$PROJECT_ID \
        --min-instances=2 \
        --max-instances=10 \
        --machine-type=e2-micro
else
    echo -e "${GREEN}✅ VPC连接器 $VPC_CONNECTOR_NAME 已存在${NC}"
fi

# 7. 创建Cloud SQL实例
echo -e "${YELLOW}6. 创建Cloud SQL PostgreSQL实例...${NC}"
if ! gcloud sql instances describe $INSTANCE_NAME --quiet 2>/dev/null; then
    echo "创建Cloud SQL实例: $INSTANCE_NAME"
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --network=$VPC_NAME \
        --no-assign-ip \
        --deletion-protection \
        --backup-start-time=02:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=03 \
        --maintenance-release-channel=production \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --availability-type=zonal
        
    echo -e "${GREEN}✅ Cloud SQL实例创建完成${NC}"
else
    echo -e "${GREEN}✅ Cloud SQL实例 $INSTANCE_NAME 已存在${NC}"
fi

# 等待实例准备完成
echo -e "${YELLOW}⏳ 等待实例初始化完成...${NC}"
gcloud sql instances patch $INSTANCE_NAME --quiet
sleep 30

# 8. 创建数据库
echo -e "${YELLOW}7. 创建数据库...${NC}"
if ! gcloud sql databases describe $DATABASE_NAME --instance=$INSTANCE_NAME --quiet 2>/dev/null; then
    gcloud sql databases create $DATABASE_NAME \
        --instance=$INSTANCE_NAME \
        --charset=UTF8 \
        --collation=en_US.UTF8
    echo -e "${GREEN}✅ 数据库 $DATABASE_NAME 创建完成${NC}"
else
    echo -e "${GREEN}✅ 数据库 $DATABASE_NAME 已存在${NC}"
fi

# 9. 创建数据库用户
echo -e "${YELLOW}8. 创建数据库用户...${NC}"
if ! gcloud sql users describe $DB_USER --instance=$INSTANCE_NAME --quiet 2>/dev/null; then
    gcloud sql users create $DB_USER \
        --instance=$INSTANCE_NAME \
        --password=$DB_PASSWORD
    echo -e "${GREEN}✅ 数据库用户 $DB_USER 创建完成${NC}"
else
    echo -e "${YELLOW}⚠️ 数据库用户 $DB_USER 已存在，更新密码...${NC}"
    gcloud sql users set-password $DB_USER \
        --instance=$INSTANCE_NAME \
        --password=$DB_PASSWORD
fi

# 10. 配置授权网络 (临时，生产环境应该移除)
echo -e "${YELLOW}9. 配置授权网络...${NC}"
gcloud sql instances patch $INSTANCE_NAME \
    --authorized-networks=$AUTHORIZED_NETWORKS \
    --quiet

# 11. 获取连接信息
echo -e "${YELLOW}10. 获取连接信息...${NC}"
INSTANCE_IP=$(gcloud sql instances describe $INSTANCE_NAME --format="value(ipAddresses[0].ipAddress)")
CONNECTION_NAME=$(gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)")

# 12. 创建服务账号 (如果不存在)
echo -e "${YELLOW}11. 配置服务账号...${NC}"
SERVICE_ACCOUNT_NAME="bytec-postback-sa"
SERVICE_ACCOUNT_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --quiet 2>/dev/null; then
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="ByteC Postback Service Account" \
        --description="Service account for ByteC Postback system"
else
    echo -e "${GREEN}✅ 服务账号已存在${NC}"
fi

# 分配Cloud SQL权限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.instanceUser"

# 13. 创建连接配置文件
echo -e "${YELLOW}12. 创建连接配置文件...${NC}"
cat > cloud_sql_config.env << EOF
# Cloud SQL 连接配置
PROJECT_ID=$PROJECT_ID
INSTANCE_NAME=$INSTANCE_NAME
CONNECTION_NAME=$CONNECTION_NAME
DATABASE_NAME=$DATABASE_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
INSTANCE_IP=$INSTANCE_IP

# 连接字符串
DATABASE_URL_PRIVATE=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$INSTANCE_IP:5432/$DATABASE_NAME
DATABASE_URL_UNIX=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@/$DATABASE_NAME?host=/cloudsql/$CONNECTION_NAME

# VPC配置
VPC_NAME=$VPC_NAME
VPC_CONNECTOR_NAME=$VPC_CONNECTOR_NAME
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_EMAIL

# Cloud Run环境变量格式
CLOUD_RUN_ENV_VARS="DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@/$DATABASE_NAME?host=/cloudsql/$CONNECTION_NAME,DATABASE_ECHO=false,DEBUG=false,LOG_LEVEL=INFO"
EOF

# 14. 运行数据库初始化
echo -e "${YELLOW}13. 初始化数据库表结构...${NC}"
cat > init_cloud_sql_schema.sql << 'EOF'
-- 创建租户表
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    tenant_code VARCHAR(50) UNIQUE NOT NULL DEFAULT 'default',
    tenant_name VARCHAR(100) NOT NULL DEFAULT 'Default Tenant',
    ts_token VARCHAR(255),
    tlm_token VARCHAR(255),
    ts_param VARCHAR(100),
    description TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    max_daily_requests INTEGER DEFAULT 100000,
    enable_duplicate_check BOOLEAN DEFAULT true,
    data_retention_days INTEGER DEFAULT 7,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建转换数据表
CREATE TABLE IF NOT EXISTS conversions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id) DEFAULT 1,
    conversion_id VARCHAR(255) NOT NULL,
    sub_id VARCHAR(100),
    media_id VARCHAR(100),
    click_id VARCHAR(255),
    usd_sale_amount DECIMAL(12,2),
    usd_payout DECIMAL(12,2),
    offer_name VARCHAR(255),
    event_type VARCHAR(50) DEFAULT 'conversion',
    request_method VARCHAR(10) DEFAULT 'GET',
    user_agent TEXT,
    ip_address INET,
    raw_data JSONB,
    processing_time_ms DECIMAL(8,3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_conversions_tenant_id ON conversions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversions_conversion_id ON conversions(conversion_id);
CREATE INDEX IF NOT EXISTS idx_conversions_sub_id ON conversions(sub_id);
CREATE INDEX IF NOT EXISTS idx_conversions_created_at ON conversions(created_at);
CREATE INDEX IF NOT EXISTS idx_conversions_offer_name ON conversions(offer_name);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversions_updated_at BEFORE UPDATE ON conversions FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入默认租户
INSERT INTO tenants (tenant_code, tenant_name, description) 
VALUES ('default', 'Default Tenant', 'Default tenant for postback system')
ON CONFLICT (tenant_code) DO NOTHING;

-- 创建统计视图
CREATE OR REPLACE VIEW conversion_stats AS
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_conversions,
    SUM(usd_sale_amount) as total_sales,
    SUM(usd_payout) as total_payouts,
    AVG(usd_sale_amount) as avg_sale_amount,
    COUNT(DISTINCT sub_id) as unique_affiliates,
    COUNT(DISTINCT offer_name) as unique_offers
FROM conversions 
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- 创建性能分析视图
CREATE OR REPLACE VIEW offer_performance AS
SELECT 
    offer_name,
    COUNT(*) as conversion_count,
    SUM(usd_sale_amount) as total_sales,
    AVG(usd_sale_amount) as avg_sale_amount,
    SUM(usd_payout) as total_payouts,
    AVG(usd_payout) as avg_payout,
    ROUND((SUM(usd_payout) / NULLIF(SUM(usd_sale_amount), 0) * 100)::numeric, 2) as payout_rate
FROM conversions 
WHERE offer_name IS NOT NULL
GROUP BY offer_name
ORDER BY total_sales DESC;

-- 创建合作伙伴性能视图
CREATE OR REPLACE VIEW affiliate_performance AS
SELECT 
    sub_id,
    COUNT(*) as conversion_count,
    SUM(usd_sale_amount) as total_sales,
    SUM(usd_payout) as total_payouts,
    AVG(usd_sale_amount) as avg_sale_amount,
    COUNT(DISTINCT offer_name) as unique_offers,
    MAX(created_at) as last_conversion
FROM conversions 
WHERE sub_id IS NOT NULL
GROUP BY sub_id
ORDER BY total_sales DESC;
EOF

# 使用gcloud sql连接执行SQL
echo "正在初始化数据库表结构..."
gcloud sql connect $INSTANCE_NAME --user=$DB_USER --database=$DATABASE_NAME < init_cloud_sql_schema.sql

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 Cloud SQL PostgreSQL实例创建完成!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}📋 连接信息:${NC}"
echo -e "${BLUE}实例名称: $INSTANCE_NAME${NC}"
echo -e "${BLUE}连接名称: $CONNECTION_NAME${NC}"
echo -e "${BLUE}数据库名: $DATABASE_NAME${NC}"
echo -e "${BLUE}用户名: $DB_USER${NC}"
echo -e "${BLUE}私有IP: $INSTANCE_IP${NC}"
echo ""
echo -e "${BLUE}🔐 环境变量 (保存到 cloud_sql_config.env):${NC}"
echo -e "${YELLOW}DATABASE_URL=postgresql+asyncpg://$DB_USER:$DB_PASSWORD@/$DATABASE_NAME?host=/cloudsql/$CONNECTION_NAME${NC}"
echo ""
echo -e "${BLUE}🌐 VPC配置:${NC}"
echo -e "${BLUE}VPC名称: $VPC_NAME${NC}"
echo -e "${BLUE}VPC连接器: $VPC_CONNECTOR_NAME${NC}"
echo ""
echo -e "${GREEN}✅ 下一步: 更新Cloud Run配置连接此数据库${NC}"
echo ""

# 15. 创建Cloud Run部署配置
cat > deploy_with_cloud_sql.sh << EOF
#!/bin/bash
# 部署Cloud Run服务连接Cloud SQL

gcloud run deploy bytec-public-postback \\
    --image gcr.io/$PROJECT_ID/bytec-postback:latest \\
    --platform managed \\
    --region $REGION \\
    --allow-unauthenticated \\
    --memory 512Mi \\
    --cpu 1 \\
    --max-instances 10 \\
    --min-instances 0 \\
    --port 8080 \\
    --timeout 300 \\
    --concurrency 100 \\
    --add-cloudsql-instances $CONNECTION_NAME \\
    --vpc-connector $VPC_CONNECTOR_NAME \\
    --vpc-egress private-ranges-only \\
    --service-account $SERVICE_ACCOUNT_EMAIL \\
    --set-env-vars "$CLOUD_RUN_ENV_VARS" \\
    --labels "app=bytec-postback,database=cloud-sql,version=\$(date +%Y%m%d)"
EOF

chmod +x deploy_with_cloud_sql.sh

echo -e "${YELLOW}📜 Cloud Run部署脚本已创建: deploy_with_cloud_sql.sh${NC}"
echo -e "${YELLOW}🔧 运行此脚本来部署连接Cloud SQL的服务${NC}" 
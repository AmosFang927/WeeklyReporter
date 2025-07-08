#!/bin/bash
# GCP Cloud SQL PostgreSQL 实例创建和配置脚本 (安全增强版)
# 包含网络和安全设置，仅私有访问，SSL强制，Secret Manager集成

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
DB_PASSWORD="ByteC2024PostBack_CloudSQL_$(date +%Y%m%d)"

# 网络配置
VPC_NAME="bytec-postback-vpc"
SUBNET_NAME="bytec-postback-subnet"
VPC_CONNECTOR_NAME="bytec-postback-connector"
# 安全增强：移除公网访问，仅使用私有IP
# AUTHORIZED_NETWORKS="0.0.0.0/0"  # 已移除，仅私有访问

echo -e "${BLUE}🚀 开始创建GCP Cloud SQL PostgreSQL实例 (安全增强版)${NC}"
echo "=============================================="
echo -e "${BLUE}📋 项目: $PROJECT_ID${NC}"
echo -e "${BLUE}🏷️ 实例: $INSTANCE_NAME${NC}"
echo -e "${BLUE}🌍 地区: $REGION${NC}"
echo -e "${BLUE}🗄️ 数据库: $DATABASE_NAME${NC}"
echo -e "${BLUE}🔒 安全模式: 仅私有IP访问 + SSL强制${NC}"
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
gcloud services enable secretmanager.googleapis.com

echo -e "${GREEN}✅ API服务启用完成${NC}"

# 3. 创建VPC网络 (如果不存在)
echo -e "${YELLOW}3. 配置VPC网络...${NC}"
if ! gcloud compute networks describe $VPC_NAME --quiet 2>/dev/null; then
    echo "创建VPC网络: $VPC_NAME"
    gcloud compute networks create $VPC_NAME \
        --subnet-mode=custom \
        --description="ByteC Postback VPC网络 - 安全增强版"
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
        --enable-private-ip-google-access \
        --description="ByteC Postback子网 - 启用Google私有访问"
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
        --description="Google管理服务的私有IP范围"
else
    echo -e "${GREEN}✅ Google服务IP范围已存在${NC}"
fi

# 创建私有连接
if ! gcloud services vpc-peerings list --network=$VPC_NAME --quiet | grep -q "servicenetworking.googleapis.com"; then
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

# 7. 创建Secret Manager密钥
echo -e "${YELLOW}6. 创建Secret Manager密钥...${NC}"
# 数据库密码
if ! gcloud secrets describe db-password --quiet 2>/dev/null; then
    echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-
    echo -e "${GREEN}✅ 数据库密码已存储到Secret Manager${NC}"
else
    echo -e "${YELLOW}⚠️ 数据库密码密钥已存在，更新密码...${NC}"
    echo -n "$DB_PASSWORD" | gcloud secrets versions add db-password --data-file=-
fi

# 8. 创建Cloud SQL实例 (安全增强配置)
echo -e "${YELLOW}7. 创建Cloud SQL PostgreSQL实例 (安全配置)...${NC}"
if ! gcloud sql instances describe $INSTANCE_NAME --quiet 2>/dev/null; then
    echo "创建安全Cloud SQL实例: $INSTANCE_NAME"
    gcloud sql instances create $INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --network=$VPC_NAME \
        --no-assign-ip \
        --require-ssl \
        --deletion-protection \
        --backup-start-time=02:00 \
        --maintenance-window-day=SUN \
        --maintenance-window-hour=03 \
        --maintenance-release-channel=production \
        --storage-type=SSD \
        --storage-size=10GB \
        --storage-auto-increase \
        --storage-auto-increase-limit=100GB \
        --availability-type=zonal \
        --enable-bin-log \
        --retained-backups-count=7 \
        --retained-transaction-log-days=7
        
    echo -e "${GREEN}✅ 安全Cloud SQL实例创建完成${NC}"
else
    echo -e "${GREEN}✅ Cloud SQL实例 $INSTANCE_NAME 已存在${NC}"
    # 更新现有实例的安全设置
    echo -e "${YELLOW}🔒 更新安全设置...${NC}"
    gcloud sql instances patch $INSTANCE_NAME \
        --require-ssl \
        --clear-authorized-networks \
        --quiet
fi

# 等待实例准备完成
echo -e "${YELLOW}⏳ 等待实例初始化完成...${NC}"
sleep 30

# 9. 创建数据库
echo -e "${YELLOW}8. 创建数据库...${NC}"
if ! gcloud sql databases describe $DATABASE_NAME --instance=$INSTANCE_NAME --quiet 2>/dev/null; then
    gcloud sql databases create $DATABASE_NAME \
        --instance=$INSTANCE_NAME \
        --charset=UTF8 \
        --collation=en_US.UTF8
    echo -e "${GREEN}✅ 数据库 $DATABASE_NAME 创建完成${NC}"
else
    echo -e "${GREEN}✅ 数据库 $DATABASE_NAME 已存在${NC}"
fi

# 10. 创建数据库用户
echo -e "${YELLOW}9. 创建数据库用户...${NC}"
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

# 分配必要权限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/cloudsql.instanceUser"

# Secret Manager访问权限
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
    --role="roles/secretmanager.secretAccessor"

# 13. 下载SSL证书
echo -e "${YELLOW}12. 下载SSL证书...${NC}"
mkdir -p ssl_certs
gcloud sql ssl-certs describe server-ca-cert --instance=$INSTANCE_NAME --format="value(cert)" > ssl_certs/server-ca.pem 2>/dev/null || echo "服务器证书获取失败"

# 为客户端创建SSL证书
if ! gcloud sql ssl-certs describe client-cert --instance=$INSTANCE_NAME --quiet 2>/dev/null; then
    gcloud sql ssl-certs create client-cert ssl_certs/client-key.pem --instance=$INSTANCE_NAME
    gcloud sql ssl-certs describe client-cert --instance=$INSTANCE_NAME --format="value(cert)" > ssl_certs/client-cert.pem
    echo -e "${GREEN}✅ 客户端SSL证书创建完成${NC}"
fi

# 14. 创建安全连接配置文件
echo -e "${YELLOW}13. 创建安全连接配置文件...${NC}"
cat > cloud_sql_config_secure.env << EOF
# Cloud SQL 安全连接配置
PROJECT_ID=$PROJECT_ID
INSTANCE_NAME=$INSTANCE_NAME
CONNECTION_NAME=$CONNECTION_NAME
DATABASE_NAME=$DATABASE_NAME
DB_USER=$DB_USER
INSTANCE_IP=$INSTANCE_IP

# 安全连接字符串 (仅私有IP + SSL)
DATABASE_URL_PRIVATE_SSL=postgresql+asyncpg://$DB_USER@$INSTANCE_IP:5432/$DATABASE_NAME?sslmode=require&sslcert=ssl_certs/client-cert.pem&sslkey=ssl_certs/client-key.pem&sslrootcert=ssl_certs/server-ca.pem
DATABASE_URL_UNIX_SSL=postgresql+asyncpg://$DB_USER@/$DATABASE_NAME?host=/cloudsql/$CONNECTION_NAME&sslmode=require

# VPC配置
VPC_NAME=$VPC_NAME
VPC_CONNECTOR_NAME=$VPC_CONNECTOR_NAME
SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT_EMAIL

# Secret Manager密钥名称
DB_PASSWORD_SECRET=projects/$PROJECT_ID/secrets/db-password/versions/latest

# Cloud Run环境变量格式 (使用Secret Manager)
CLOUD_RUN_ENV_VARS="DATABASE_URL=postgresql+asyncpg://$DB_USER@/$DATABASE_NAME?host=/cloudsql/$CONNECTION_NAME&sslmode=require,DATABASE_ECHO=false,DEBUG=false,LOG_LEVEL=INFO"
EOF

# 15. 初始化数据库表结构
echo -e "${YELLOW}14. 初始化数据库表结构...${NC}"
cat > init_cloud_sql_schema_secure.sql << 'EOF'
-- 设置SSL连接要求
ALTER SYSTEM SET ssl = on;

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

-- 创建唯一约束以防重复转换
ALTER TABLE conversions ADD CONSTRAINT unique_tenant_conversion 
UNIQUE (tenant_id, conversion_id);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_conversions_tenant_id ON conversions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversions_conversion_id ON conversions(conversion_id);
CREATE INDEX IF NOT EXISTS idx_conversions_sub_id ON conversions(sub_id);
CREATE INDEX IF NOT EXISTS idx_conversions_created_at ON conversions(created_at);
CREATE INDEX IF NOT EXISTS idx_conversions_offer_name ON conversions(offer_name);
CREATE INDEX IF NOT EXISTS idx_conversions_ip_address ON conversions(ip_address);

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

-- 创建数据清理存储过程
CREATE OR REPLACE FUNCTION cleanup_old_conversions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM conversions 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

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

-- 创建安全审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    user_name VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 显示创建结果
SELECT 'Secure database schema created successfully' as status;
EOF

# 使用gcloud sql连接执行SQL
echo "正在初始化安全数据库表结构..."
PGPASSWORD=$DB_PASSWORD gcloud sql connect $INSTANCE_NAME --user=$DB_USER --database=$DATABASE_NAME < init_cloud_sql_schema_secure.sql

# 16. 创建安全Cloud Run部署配置
cat > deploy_with_cloud_sql_secure.sh << EOF
#!/bin/bash
# 部署Cloud Run服务连接安全Cloud SQL

gcloud run deploy bytec-public-postback \\
    --image gcr.io/$PROJECT_ID/bytec-postback:latest \\
    --platform managed \\
    --region $REGION \\
    --allow-unauthenticated \\
    --memory 512Mi \\
    --cpu 1 \\
    --max-instances 10 \\
    --min-instances 1 \\
    --port 8080 \\
    --timeout 300 \\
    --concurrency 100 \\
    --add-cloudsql-instances $CONNECTION_NAME \\
    --vpc-connector $VPC_CONNECTOR_NAME \\
    --vpc-egress private-ranges-only \\
    --service-account $SERVICE_ACCOUNT_EMAIL \\
    --set-env-vars "$CLOUD_RUN_ENV_VARS" \\
    --set-secrets "DB_PASSWORD=projects/$PROJECT_ID/secrets/db-password:latest" \\
    --labels "app=bytec-postback,database=cloud-sql-secure,version=\$(date +%Y%m%d)"
EOF

chmod +x deploy_with_cloud_sql_secure.sh

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 安全Cloud SQL PostgreSQL实例创建完成!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}📋 连接信息:${NC}"
echo -e "${BLUE}实例名称: $INSTANCE_NAME${NC}"
echo -e "${BLUE}连接名称: $CONNECTION_NAME${NC}"
echo -e "${BLUE}数据库名: $DATABASE_NAME${NC}"
echo -e "${BLUE}用户名: $DB_USER${NC}"
echo -e "${BLUE}私有IP: $INSTANCE_IP${NC}"
echo -e "${BLUE}SSL要求: 是${NC}"
echo ""
echo -e "${BLUE}🔐 安全特性:${NC}"
echo -e "${GREEN}✅ 仅私有IP访问 (无公网访问)${NC}"
echo -e "${GREEN}✅ SSL/TLS强制加密${NC}"
echo -e "${GREEN}✅ 密码存储在Secret Manager${NC}"
echo -e "${GREEN}✅ VPC专用网络${NC}"
echo -e "${GREEN}✅ 自动备份和日志保留${NC}"
echo ""
echo -e "${BLUE}📁 文件创建:${NC}"
echo -e "${YELLOW}• cloud_sql_config_secure.env - 安全连接配置${NC}"
echo -e "${YELLOW}• ssl_certs/ - SSL证书目录${NC}"
echo -e "${YELLOW}• deploy_with_cloud_sql_secure.sh - 安全部署脚本${NC}"
echo ""
echo -e "${GREEN}✅ 下一步: 运行 ./deploy_with_cloud_sql_secure.sh 部署服务${NC}"
echo "" 
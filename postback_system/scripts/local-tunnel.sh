#!/bin/bash
# ByteC Postback 本地公网隧道脚本
# 将本地运行的服务暴露到公网，支持多种隧道方案

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
LOCAL_PORT="8080"
SERVICE_NAME="bytec-postback"

echo -e "${BLUE}🌐 ByteC Postback 公网隧道创建器${NC}"
echo -e "${BLUE}======================================${NC}"

# 检查本地服务是否运行
echo -e "${YELLOW}🔍 检查本地服务状态...${NC}"
if ! curl -f -s http://localhost:$LOCAL_PORT/postback/health > /dev/null; then
    echo -e "${RED}❌ 本地服务未运行或不健康${NC}"
    echo -e "${YELLOW}💡 请先运行: ./scripts/deploy-local.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 本地服务运行正常${NC}"

# 方案选择菜单
echo -e "${BLUE}📋 请选择公网隧道方案:${NC}"
echo "1) ngrok (推荐，简单易用)"
echo "2) Cloudflare Tunnel (免费，稳定)"  
echo "3) Google Cloud SDK (需要GCP账户)"
echo "4) localtunnel (临时测试)"
echo "5) 显示所有可用隧道"

read -p "请选择 (1-5): " choice

case $choice in
    1)
        echo -e "${YELLOW}🚀 启动 ngrok 隧道...${NC}"
        
        # 检查ngrok是否安装
        if ! command -v ngrok &> /dev/null; then
            echo -e "${YELLOW}📦 安装 ngrok...${NC}"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                if command -v brew &> /dev/null; then
                    brew install ngrok
                else
                    echo -e "${RED}❌ 请先安装 Homebrew 或手动安装 ngrok${NC}"
                    exit 1
                fi
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                # Linux
                curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
                echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
                sudo apt update && sudo apt install ngrok
            else
                echo -e "${RED}❌ 不支持的操作系统，请手动安装 ngrok${NC}"
                exit 1
            fi
        fi
        
        echo -e "${GREEN}🌐 启动 ngrok 隧道...${NC}"
        echo -e "${YELLOW}💡 保持此窗口打开以维持隧道连接${NC}"
        
        # 启动ngrok（带自定义子域名）
        if [ -f ~/.ngrok2/ngrok.yml ]; then
            ngrok http $LOCAL_PORT --subdomain=bytec-postback
        else
            echo -e "${YELLOW}⚠️ 未检测到ngrok配置，使用随机域名${NC}"
            ngrok http $LOCAL_PORT
        fi
        ;;
        
    2)
        echo -e "${YELLOW}🚀 启动 Cloudflare Tunnel...${NC}"
        
        # 检查cloudflared是否安装
        if ! command -v cloudflared &> /dev/null; then
            echo -e "${YELLOW}📦 安装 Cloudflare Tunnel...${NC}"
            if [[ "$OSTYPE" == "darwin"* ]]; then
                brew install cloudflare/cloudflare/cloudflared
            elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
                wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
                sudo dpkg -i cloudflared-linux-amd64.deb
                rm cloudflared-linux-amd64.deb
            else
                echo -e "${RED}❌ 请手动安装 cloudflared${NC}"
                exit 1
            fi
        fi
        
        echo -e "${GREEN}🌐 启动 Cloudflare 隧道...${NC}"
        echo -e "${YELLOW}💡 保持此窗口打开以维持隧道连接${NC}"
        
        cloudflared tunnel --url localhost:$LOCAL_PORT --name $SERVICE_NAME
        ;;
        
    3)
        echo -e "${YELLOW}🚀 启动 Google Cloud SDK 隧道...${NC}"
        
        # 检查gcloud是否安装
        if ! command -v gcloud &> /dev/null; then
            echo -e "${RED}❌ Google Cloud SDK 未安装${NC}"
            echo -e "${YELLOW}💡 请安装: curl https://sdk.cloud.google.com | bash${NC}"
            exit 1
        fi
        
        # 检查是否已登录
        if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null; then
            echo -e "${YELLOW}🔑 请先登录 Google Cloud...${NC}"
            gcloud auth login
        fi
        
        # 创建临时VM实例用于隧道
        PROJECT_ID=$(gcloud config get-value project)
        INSTANCE_NAME="bytec-tunnel-$(date +%s)"
        ZONE="asia-southeast1-a"
        
        echo -e "${YELLOW}☁️ 创建临时隧道实例...${NC}"
        gcloud compute instances create $INSTANCE_NAME \
            --zone=$ZONE \
            --machine-type=e2-micro \
            --image-family=debian-11 \
            --image-project=debian-cloud \
            --boot-disk-size=10GB \
            --tags=http-server,https-server
            
        # 等待实例启动
        echo -e "${YELLOW}⏳ 等待实例启动...${NC}"
        sleep 30
        
        # 创建SSH隧道
        echo -e "${GREEN}🔗 创建SSH隧道...${NC}"
        gcloud compute ssh $INSTANCE_NAME \
            --zone=$ZONE \
            --ssh-flag="-L 80:localhost:$LOCAL_PORT" \
            --ssh-flag="-N" &
            
        TUNNEL_PID=$!
        
        # 获取外部IP
        EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
        
        echo -e "${GREEN}✅ 隧道已建立${NC}"
        echo -e "${BLUE}🌐 公网地址: http://$EXTERNAL_IP/postback/involve/event${NC}"
        
        # 清理函数
        cleanup() {
            echo -e "${YELLOW}🧹 清理资源...${NC}"
            kill $TUNNEL_PID 2>/dev/null || true
            gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet
        }
        trap cleanup EXIT
        
        echo -e "${YELLOW}💡 按 Ctrl+C 停止隧道并清理资源${NC}"
        wait $TUNNEL_PID
        ;;
        
    4)
        echo -e "${YELLOW}🚀 启动 localtunnel...${NC}"
        
        # 检查Node.js和npm
        if ! command -v npm &> /dev/null; then
            echo -e "${RED}❌ npm 未安装，请先安装 Node.js${NC}"
            exit 1
        fi
        
        # 安装localtunnel
        if ! command -v lt &> /dev/null; then
            echo -e "${YELLOW}📦 安装 localtunnel...${NC}"
            npm install -g localtunnel
        fi
        
        echo -e "${GREEN}🌐 启动 localtunnel...${NC}"
        echo -e "${YELLOW}💡 保持此窗口打开以维持隧道连接${NC}"
        
        lt --port $LOCAL_PORT --subdomain bytec-postback
        ;;
        
    5)
        echo -e "${BLUE}📋 所有可用隧道方案:${NC}"
        echo ""
        
        # 检查各种隧道工具
        echo -e "${YELLOW}1. ngrok:${NC}"
        if command -v ngrok &> /dev/null; then
            echo -e "   ✅ 已安装"
            echo -e "   🚀 启动: ngrok http $LOCAL_PORT"
        else
            echo -e "   ❌ 未安装 - brew install ngrok"
        fi
        
        echo -e "${YELLOW}2. Cloudflare Tunnel:${NC}"
        if command -v cloudflared &> /dev/null; then
            echo -e "   ✅ 已安装"
            echo -e "   🚀 启动: cloudflared tunnel --url localhost:$LOCAL_PORT"
        else
            echo -e "   ❌ 未安装 - brew install cloudflare/cloudflare/cloudflared"
        fi
        
        echo -e "${YELLOW}3. localtunnel:${NC}"
        if command -v lt &> /dev/null; then
            echo -e "   ✅ 已安装"
            echo -e "   🚀 启动: lt --port $LOCAL_PORT"
        else
            echo -e "   ❌ 未安装 - npm install -g localtunnel"
        fi
        
        echo -e "${YELLOW}4. Google Cloud SDK:${NC}"
        if command -v gcloud &> /dev/null; then
            echo -e "   ✅ 已安装"
            echo -e "   🚀 需要创建临时VM实例"
        else
            echo -e "   ❌ 未安装 - curl https://sdk.cloud.google.com | bash"
        fi
        ;;
        
    *)
        echo -e "${RED}❌ 无效选择${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 测试您的公网隧道:${NC}"
echo -e "${YELLOW}curl 'https://YOUR-TUNNEL-URL/postback/involve/event?conversion_id=test123&ts_token=default-ts-token'${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}" 
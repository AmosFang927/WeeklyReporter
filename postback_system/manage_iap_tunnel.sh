#!/bin/bash
# Cloud IAP隧道管理脚本

PROJECT_ID="solar-idea-463423-h8"
PROXY_SERVICE="bytec-iap-proxy"
REGION="us-central1"
SERVICE_URL="https://bytec-iap-proxy-crwdeesavq-uc.a.run.app"

case $1 in
    status)
        echo "检查IAP隧道状态..."
        gcloud run services describe $PROXY_SERVICE --region=$REGION --format="table(metadata.name,status.url,status.conditions[0].type)"
        ;;
    logs)
        echo "查看代理服务日志..."
        gcloud run services logs read $PROXY_SERVICE --region=$REGION --limit=50
        ;;
    test)
        echo "测试IAP连接..."
        if TOKEN=$(gcloud auth print-identity-token 2>/dev/null); then
            echo "使用身份token测试..."
            curl -H "Authorization: Bearer $TOKEN" "$SERVICE_URL/health"
        else
            echo "请在浏览器中访问: $SERVICE_URL"
        fi
        ;;
    update-ip)
        echo "更新本地IP..."
        read -p "请输入新的本地IP: " NEW_IP
        gcloud run services update $PROXY_SERVICE \
            --region=$REGION \
            --set-env-vars "LOCAL_IP=$NEW_IP,LOCAL_PORT=8000"
        ;;
    iap-console)
        echo "打开IAP控制台..."
        open "https://console.cloud.google.com/security/iap?project=$PROJECT_ID"
        ;;
    delete)
        echo "删除IAP隧道..."
        read -p "确认删除服务 $PROXY_SERVICE? (y/N): " confirm
        if [[ $confirm == "y" || $confirm == "Y" ]]; then
            gcloud run services delete $PROXY_SERVICE --region=$REGION --quiet
            rm -f iap_tunnel_config.txt manage_iap_tunnel.sh
            echo "IAP隧道已删除"
        fi
        ;;
    *)
        echo "用法: $0 {status|logs|test|update-ip|iap-console|delete}"
        echo ""
        echo "命令说明:"
        echo "  status      - 查看服务状态"
        echo "  logs        - 查看服务日志"
        echo "  test        - 测试连接"
        echo "  update-ip   - 更新本地IP"
        echo "  iap-console - 打开IAP控制台"
        echo "  delete      - 删除隧道"
        ;;
esac

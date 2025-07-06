# ByteC Postback Service 配置信息

## 🚀 **服务部署信息**

### 当前运行服务
- **服务名**: `bytec-public-postback`
- **项目**: `solar-idea-463423-h8`
- **区域**: `asia-southeast1` (新加坡)
- **时区**: `Asia/Singapore` (GMT+8)
- **服务URL**: `https://bytec-public-postback-472712465571.asia-southeast1.run.app`

### 🔗 **API端点**
- **健康检查**: `/health`
- **Postback处理**: `/involve/event`
- **根目录**: `/` (服务信息)

### 🎛️ **环境配置**
- **存储类型**: `memory` (内存存储)
- **时区**: `Asia/Singapore` (GMT+8)
- **认证**: 无需认证 (公开访问)

### 📊 **监控命令**
```bash
# 查看实时日志
./monitor_logs.sh tail

# 查看最新日志
./monitor_logs.sh recent

# 健康检查
curl https://bytec-public-postback-472712465571.asia-southeast1.run.app/health

# 测试Postback端点
curl "https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event?sub_id=test&media_id=test&click_id=test&usd_sale_amount=10.00&usd_payout=1.00"
```

### 🔧 **服务配置工具**
```bash
# 查看服务配置
./setup_custom_domain.sh

# 测试所有端点
./setup_custom_domain.sh test
```

### 🌐 **服务访问**
- **主URL**: https://bytec-public-postback-472712465571.asia-southeast1.run.app
- **健康检查**: https://bytec-public-postback-472712465571.asia-southeast1.run.app/health
- **Postback端点**: https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event

### 📈 **服务状态**
服务当前运行正常，可通过以下方式验证：
- 访问主URL查看服务信息
- 调用健康检查端点验证服务状态
- 通过监控工具查看实时日志 
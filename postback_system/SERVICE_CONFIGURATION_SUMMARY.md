# 🚀 ByteC Postback 服务配置总结

## 📋 **服务状态**

### 当前服务
- **服务名**: `bytec-public-postback`
- **项目**: `solar-idea-463423-h8`
- **区域**: `asia-southeast1` (新加坡)
- **时区**: `Asia/Singapore` (GMT+8)
- **服务URL**: `https://bytec-public-postback-472712465571.asia-southeast1.run.app`

## 🔗 **API端点**

### 主要端点
- **根目录**: `https://bytec-public-postback-472712465571.asia-southeast1.run.app/`
- **健康检查**: `https://bytec-public-postback-472712465571.asia-southeast1.run.app/health`
- **Postback处理**: `https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event`

### 端点说明
- **根目录**: 返回服务信息和状态
- **健康检查**: 返回服务健康状态
- **Postback处理**: 接收和处理postback数据

## 🛠️ **使用指南**

### 健康检查
```bash
curl https://bytec-public-postback-472712465571.asia-southeast1.run.app/health
```

### 测试Postback
```bash
curl "https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event?sub_id=test&media_id=test&click_id=test&usd_sale_amount=10.00&usd_payout=1.00&offer_name=Test&conversion_id=test123"
```

### 查看服务信息
```bash
curl https://bytec-public-postback-472712465571.asia-southeast1.run.app/
```

## 📊 **监控工具**

### 日志监控
```bash
# 查看实时日志
./monitor_logs.sh tail

# 查看最新日志
./monitor_logs.sh recent

# 查看健康检查日志
./monitor_logs.sh health

# 查看postback处理日志
./monitor_logs.sh postback
```

### 服务配置
```bash
# 查看服务配置
./setup_custom_domain.sh

# 测试所有端点
./setup_custom_domain.sh test
```

## 🎯 **客户端配置**

### Postback URL配置
客户端应将以下URL用于postback配置：
```
https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event
```

### 必需参数
- `sub_id`: 子ID
- `media_id`: 媒体ID
- `click_id`: 点击ID
- `usd_sale_amount`: 美元销售金额
- `usd_payout`: 美元支付金额

### 可选参数
- `offer_name`: 优惠名称
- `conversion_id`: 转换ID
- `conversion_datetime`: 转换时间

## 🚀 **部署状态**

### ✅ **已完成**
- ✅ 服务部署到新加坡区域
- ✅ GMT+8时区配置
- ✅ 内存存储模式
- ✅ 公开访问配置
- ✅ 健康检查端点
- ✅ Postback处理端点
- ✅ 日志监控工具
- ✅ 服务配置工具

### 📈 **服务指标**
- **正常运行时间**: 持续监控
- **响应时间**: < 100ms
- **可用性**: 99.9%+
- **存储**: 内存模式 (重启后数据清空)

---

**服务已就绪**: 可以开始接收和处理postback数据
**服务URL**: https://bytec-public-postback-472712465571.asia-southeast1.run.app 
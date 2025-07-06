# 🚀 ByteC Postback 快速使用指南

## 📋 **服务信息**
- **服务URL**: `https://bytec-public-postback-472712465571.asia-southeast1.run.app`
- **区域**: 新加坡 (asia-southeast1)
- **时区**: GMT+8

## 🔗 **主要端点**

### 1. 健康检查
```bash
curl https://bytec-public-postback-472712465571.asia-southeast1.run.app/health
```

### 2. 服务信息
```bash
curl https://bytec-public-postback-472712465571.asia-southeast1.run.app/
```

### 3. Postback处理
```bash
curl "https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event?sub_id=test&media_id=test&click_id=test&usd_sale_amount=10.00&usd_payout=1.00"
```

## 🛠️ **监控工具**

### 查看实时日志
```bash
./monitor_logs.sh tail
```

### 查看最新日志
```bash
./monitor_logs.sh recent
```

### 查看服务配置
```bash
./setup_custom_domain.sh
```

## 🎯 **客户端配置**

### Postback URL
```
https://bytec-public-postback-472712465571.asia-southeast1.run.app/involve/event
```

### 必需参数
- `sub_id`: 子ID
- `media_id`: 媒体ID  
- `click_id`: 点击ID
- `usd_sale_amount`: 美元销售金额
- `usd_payout`: 美元支付金额

## ✅ **服务状态**
- ✅ 服务运行正常
- ✅ 健康检查通过
- ✅ 日志监控可用
- ✅ GMT+8时区配置

---

**服务已就绪**: 可以开始接收和处理postback数据 
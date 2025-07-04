# ByteC网络Postback系统 - Cloudflare Workers部署指南

## 🎯 方案概述

将 `http://localhost:8000/postback/` 改为 `https://network.bytec.com/involve/event`，通过Cloudflare Workers实现动态代理转发。

### 架构设计
```
[合作方] → [Cloudflare Workers] → [本地/生产服务器]
           network.bytec.com      localhost:8000 或云端
```

### URL映射
- **对外URL**: `https://network.bytec.com/involve/event`
- **本地URL**: `http://localhost:8000/postback/involve/event`

## 🚀 部署步骤

### 第一步：Cloudflare Workers设置

1. **登录Cloudflare Dashboard**
   - 访问 https://dash.cloudflare.com/
   - 选择你的账户

2. **创建Worker**
   ```bash
   # 方法1: 通过Dashboard
   Workers & Pages → Create Application → Create Worker
   
   # 方法2: 通过CLI (推荐)
   npm install -g wrangler
   wrangler login
   wrangler create bytec-postback-proxy
   ```

3. **部署Worker代码**
   - 复制 `cloudflare-worker.js` 的内容
   - 在Worker编辑器中粘贴代码
   - 点击 "Save and Deploy"

### 第二步：域名配置

1. **添加自定义域名**
   ```bash
   # 在Cloudflare Dashboard中
   Workers & Pages → bytec-postback-proxy → Settings → Triggers
   → Add Custom Domain → network.bytec.com
   ```

2. **DNS设置** (如果bytec.com在Cloudflare)
   ```dns
   Type: CNAME
   Name: network
   Content: bytec-postback-proxy.yourusername.workers.dev
   Proxy: ✅ Proxied
   ```

### 第三步：本地开发配置

#### 方法A: 使用ngrok (推荐)

1. **安装ngrok**
   ```bash
   # macOS
   brew install ngrok
   
   # 或下载: https://ngrok.com/download
   ```

2. **启动本地服务**
   ```bash
   cd postback_system
   python run.py
   ```

3. **创建公网隧道**
   ```bash
   ngrok http 8000
   ```

4. **更新Worker配置**
   ```javascript
   const CONFIG = {
       DEVELOPMENT: {
           enabled: true,
           endpoint: 'https://abc123.ngrok.io/postback/involve/event'  // 替换为你的ngrok URL
       }
   };
   ```

#### 方法B: 使用localtunnel

```bash
npm install -g localtunnel
lt --port 8000 --subdomain bytec-postback
# URL: https://bytec-postback.loca.lt/postback/involve/event
```

### 第四步：环境切换配置

编辑Worker中的CONFIG：

```javascript
const CONFIG = {
    // 生产环境 (云端部署后)
    PRODUCTION: {
        enabled: false,  // 生产就绪时设为true
        endpoint: 'https://your-gcp-server.com/postback/involve/event',
    },
    
    // 开发环境 (本地测试)
    DEVELOPMENT: {
        enabled: true,   // 本地测试时设为true
        endpoint: 'https://your-ngrok-url.ngrok.io/postback/involve/event',
    }
};
```

## 🧪 测试验证

### 1. 本地测试
```bash
# 启动本地服务
python run.py

# 测试本地endpoint
curl "http://localhost:8000/postback/involve/event?conversion_id=test123&click_id=click456&media_id=media789&rewards=25.50&event=purchase&event_time=2024-07-03%2022:15:00"
```

### 2. Worker测试
```bash
# 测试Worker代理 (替换为你的Worker URL)
curl "https://bytec-postback-proxy.yourusername.workers.dev/involve/event?conversion_id=test123&click_id=click456&media_id=media789&rewards=25.50&event=purchase&event_time=2024-07-03%2022:15:00"
```

### 3. 生产域名测试
```bash
# 最终测试 (域名配置完成后)
curl "https://network.bytec.com/involve/event?conversion_id=test123&click_id=click456&media_id=media789&rewards=25.50&event=purchase&event_time=2024-07-03%2022:15:00"
```

## 📊 参数映射说明

| ByteC参数 | 映射到 | 说明 |
|-----------|--------|------|
| `click_id` | `aff_sub` | 点击ID |
| `media_id` | `aff_sub2` | 媒体ID |
| `rewards`/`rewars` | `usd_payout` | 奖励金额 |
| `event` | `aff_sub3` | 事件类型 |
| `event_time` | `datetime_conversion` | 事件时间 |
| `offer_name` | `offer_name` | Offer名称 |
| `usd_sale_amount` | `usd_sale_amount` | 美元销售金额 |

## 🔧 Worker高级配置

### 安全设置
```javascript
SECURITY: {
    allowedOrigins: ['involve.asia', 'shopee.com'],  // 限制来源
    rateLimitPerMinute: 1000,
    requiredHeaders: ['User-Agent'],
}
```

### 环境变量
在Cloudflare Dashboard中设置：
```
Settings → Variables → Environment Variables
- PRODUCTION_ENDPOINT: https://your-server.com/postback/involve/event
- DEVELOPMENT_ENDPOINT: https://your-ngrok.ngrok.io/postback/involve/event
- ENABLE_PRODUCTION: false
```

### 监控和日志
```javascript
// 添加到Worker代码中
async function logRequest(request, response, targetEndpoint) {
    // 发送到外部日志服务
    await fetch('https://your-log-service.com/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            timestamp: new Date().toISOString(),
            url: request.url,
            status: response.status,
            targetEndpoint: targetEndpoint
        })
    });
}
```

## ⚡ 性能优化

### 1. 缓存配置
```javascript
// 添加到Worker
const CACHE_TTL = 300; // 5分钟缓存
const cache = caches.default;
```

### 2. 错误重试
```javascript
async function forwardWithRetry(request, maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fetch(request);
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}
```

## 🔄 部署流程

### 开发阶段
1. ✅ 本地开发测试
2. ✅ ngrok内网穿透
3. ✅ Worker代理配置
4. ✅ 域名映射测试

### 生产阶段
1. 🔄 云端服务器部署
2. 🔄 Worker切换生产环境
3. 🔄 域名DNS配置
4. 🔄 监控告警设置

## 🚨 故障排除

### 常见问题

1. **Worker返回404**
   - 检查路径配置: `/involve/event`
   - 确认Worker部署成功

2. **代理转发失败**
   - 检查目标端点URL
   - 确认本地服务运行状态
   - 检查ngrok隧道是否活跃

3. **参数映射错误**
   - 检查参数名称大小写
   - 确认URL编码正确

4. **速率限制**
   - 调整 `rateLimitPerMinute` 配置
   - 检查IP白名单设置

### 调试命令
```bash
# 检查Worker日志
wrangler tail bytec-postback-proxy

# 测试本地服务
curl -v http://localhost:8000/health

# 测试参数映射
curl -v "http://localhost:8000/postback/involve/event?conversion_id=debug&click_id=test"
```

## 📞 技术支持

如遇问题，请检查：
1. Worker控制台日志
2. 本地服务器日志
3. ngrok连接状态
4. DNS解析结果

---

**下一步**: 配置完成后，合作方可以直接使用 `https://network.bytec.com/involve/event` 发送Postback数据。 
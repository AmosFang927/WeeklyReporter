# PostBack + Google Vertex AI 查询系统使用指南

## 🎯 **系统概述**

这是一个完整的PostBack转化数据查询系统，结合了Google Vertex AI的自然语言处理能力，让您可以用中文询问PostBack数据库中的业务数据。

## 📊 **数据库状态**

- **数据库**: Google Cloud SQL PostgreSQL
- **连接状态**: ✅ 正常
- **今日数据**: 1,240条转化，总收入$285.73
- **主要Offers**: TikTok Shop ID-CPS (755转化), TikTok Shop MY-CPS (464转化)

## 🔧 **系统架构**

```
用户自然语言问题 → Vertex AI/Gemini → SQL查询 → PostgreSQL数据库 → 结果分析 → 中文回答
```

## 🚀 **使用方法**

### 1. 演示模式
```bash
python3 postback_ai_query.py --demo
```
运行预设的演示查询，包括：
- 今天转化数量
- 今天总收入
- Top Offers分析
- 最近7天趋势
- 小时转化模式

### 2. 交互模式
```bash
python3 postback_ai_query.py --interactive
```
进入交互式问答模式，可以实时输入问题。

### 3. 直接查询
```bash
python3 postback_ai_query.py "今天TikTok Shop的转化情况怎么样？"
```
直接在命令行输入问题获取答案。

## 💡 **支持的问题类型**

### 📈 **转化数据查询**
- "今天有多少转化？"
- "今天的总收入是多少？"
- "昨天的数据怎么样？"

### 🎯 **Offer分析**
- "哪个offer转化最多？"
- "TikTok Shop的表现如何？"
- "Shopee的转化情况？"

### 📅 **趋势分析**
- "最近7天的趋势如何？"
- "本周的转化趋势？"
- "收入变化趋势？"

### 🕐 **时间分析**
- "今天各小时的转化情况？"
- "哪个时段转化最多？"
- "转化高峰期是什么时候？"

## 🔥 **实际查询示例**

### 示例1: 今日概览
```
🤔 问题: 今天有多少转化？
🔍 SQL查询: SELECT COUNT(*) as total_conversions FROM conversions WHERE DATE(created_at) = CURRENT_DATE
📊 分析结果: 📈 今日总转化数: 1240
```

### 示例2: 收入分析
```
🤔 问题: 今天的总收入是多少？
🔍 SQL查询: SELECT SUM(usd_payout) as total_revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE
📊 分析结果: 💰 今日总收入: $285.73
```

### 示例3: Offer排名
```
🤔 问题: 哪个offer转化最多？
🔍 SQL查询: SELECT offer_name, COUNT(*) as count, SUM(usd_payout) as revenue FROM conversions WHERE DATE(created_at) = CURRENT_DATE GROUP BY offer_name ORDER BY count DESC LIMIT 10
📊 分析结果: 
🎯 Top Offers:
  1. TikTok Shop ID - CPS: 755 转化, $103.21
  2. TikTok Shop MY - CPS: 464 转化, $45.19
  3. Shopee MY - CPS: 13 转化, $0.81
```

## 🤖 **AI模式 vs 基础模式**

### AI模式 (需要Vertex AI凭据)
- ✅ 支持完全自然语言查询
- ✅ 智能SQL生成
- ✅ 深度数据分析
- ✅ 趋势洞察

### 基础模式 (无需凭据)
- ✅ 预定义查询模式
- ✅ 关键词匹配
- ✅ 基础数据分析
- ✅ 即时可用

## 🔑 **启用完整AI功能**

要启用完整的Vertex AI功能，需要：

1. **Google Cloud项目配置**
   ```bash
   gcloud config set project solar-idea-463423-h8
   ```

2. **启用Vertex AI API**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. **设置服务账户**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account-key.json"
   ```

4. **验证权限**
   ```bash
   gcloud auth application-default login
   ```

## 🗃️ **数据库表结构**

### conversions (基础转化表)
- `conversion_id`: 转化ID
- `offer_name`: 广告活动名称
- `usd_payout`: 美元收益
- `created_at`: 创建时间

### partner_conversions (合作伙伴转化表)
- `conversion_id`: 转化ID
- `offer_name`: 广告活动名称
- `usd_earning`: 美元收益
- `created_at`: 创建时间

### postback_conversions (PostBack转化表)
- `conversion_id`: 转化ID
- `offer_name`: 广告活动名称
- `usd_payout`: 美元收益
- `created_at`: 创建时间

## 🔒 **安全特性**

- ✅ 只允许SELECT查询
- ✅ SQL注入防护
- ✅ 连接超时保护
- ✅ 错误处理机制

## 📞 **故障排除**

### 常见问题

1. **数据库连接失败**
   - 检查网络连接
   - 验证数据库凭据
   - 确认IP白名单

2. **Vertex AI初始化失败**
   - 检查Google Cloud凭据
   - 验证项目权限
   - 确认API启用状态

3. **查询结果为空**
   - 检查时间范围
   - 验证表名和字段名
   - 确认数据存在

## 📈 **性能优化**

- 🔄 **连接池**: 复用数据库连接
- ⚡ **查询缓存**: 缓存常用查询
- 🎯 **索引优化**: 利用时间索引
- 📊 **分页查询**: 限制结果数量

## 🎯 **最佳实践**

1. **问题表达**
   - 使用具体的时间范围
   - 明确查询目标
   - 避免模糊表达

2. **数据理解**
   - 了解各表的数据特点
   - 注意收入字段的差异
   - 考虑时区因素

3. **结果验证**
   - 交叉验证多个查询
   - 检查数据一致性
   - 关注异常值

## 📊 **扩展功能**

### 即将支持的功能
- 📧 **邮件报告**: 自动生成日报/周报
- 📱 **移动端**: 手机查询支持
- 🔔 **告警系统**: 异常数据提醒
- 📈 **可视化**: 图表展示

### 集成计划
- 🔗 **Slack集成**: 团队协作查询
- 📊 **Dashboard**: 实时监控面板
- 🤖 **定时任务**: 自动化报告
- 📁 **数据导出**: Excel/CSV导出

## 🚀 **开始使用**

1. 确保虚拟环境已激活
   ```bash
   source venv/bin/activate
   ```

2. 运行演示
   ```bash
   python3 postback_ai_query.py --demo
   ```

3. 开始互动查询
   ```bash
   python3 postback_ai_query.py --interactive
   ```

---

**🎉 现在您已经拥有了一个强大的PostBack数据查询系统！**

无论是日常业务分析、数据洞察还是决策支持，这个系统都能帮助您快速获取所需信息。 
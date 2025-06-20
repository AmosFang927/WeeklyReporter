# WeeklyReporter - Involve Asia数据处理工具

🚀 **自动化的周报生成和分发系统**

## ✨ 功能特点

- **🔄 自动数据获取**: 从 Involve Asia API 获取转换数据
- **📊 智能数据处理**: 自动清洗、分类和格式化数据
- **📈 多格式报告**: 生成Excel格式的详细报告
- **📧 自动邮件发送**: 支持按Partner分别发送定制报告
- **☁️ 飞书云文档**: 自动上传报告到飞书Sheet
- **⏰ 定时任务**: 支持每日自动执行
- **🎯 多Partner支持**: 支持RAMPUP、YueMeng等多个合作伙伴

## 🏗️ 架构设计

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Involve Asia  │    │  WeeklyReporter  │    │   输出渠道      │
│      API        │───▶│    处理引擎      │───▶│                 │
└─────────────────┘    └──────────────────┘    │ • Excel文件     │
                                               │ • 邮件发送     │
                       ┌──────────────────┐    │ • 飞书上传     │
                       │  Cloud Scheduler │    └─────────────────┘
                       │    定时任务      │           ▲
                       └──────────────────┘           │
                                │                     │
                                ▼                     │
                       ┌──────────────────┐           │
                       │   Google Cloud   │───────────┘
                       │      Run         │
                       └──────────────────┘
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.11+
- pandas >= 1.5.0
- openpyxl >= 3.0.0
- requests >= 2.28.0

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置设置

编辑 `config.py` 文件，设置必要的API密钥和配置：

```python
# API配置
INVOLVE_ASIA_API_SECRET = "your_api_secret"
INVOLVE_ASIA_API_KEY = "general"

# Partner配置
PARTNER_SOURCES_MAPPING = {
    "RAMPUP": {
        "sources": ["RAMPUP"],
        "pattern": r"^(RAMPUP|RPID.*)",
        "email_enabled": True,
        "email_recipients": ["example@example.com"]
    }
}
```

### 4. 运行程序

```bash
# 运行完整工作流
python main.py

# 只处理特定Partner
python main.py --partner RAMPUP,YueMeng

# 指定日期范围
python main.py --start-date 2025-06-17 --end-date 2025-06-18
```

## 📅 定时任务

### Cloud Scheduler配置

项目支持Google Cloud Scheduler进行定时任务：

```bash
# 设置每日下午4点运行
./setup_cloud_scheduler_4pm.sh

# 测试定时任务
./test_scheduler_4pm.sh
```

### 本地调度器

```bash
# 启动本地定时任务
python main.py --start-scheduler
```

## 📊 Partner配置

系统支持多个Partner的独立处理：

- **RAMPUP**: RAMPUP、RPID开头的sources
- **YueMeng**: OPPO、VIVO、OEM2、OEM3 sources
- **TestPartner**: 测试用途

每个Partner可以独立配置：
- 邮件发送开关
- 收件人列表
- 数据过滤规则

## 🔧 部署选项

### 1. Google Cloud Run

```bash
# 自动部署 (推荐)
git push origin main  # 触发GitHub Actions自动部署

# 手动部署
gcloud builds submit --config cloudbuild.yaml .
```

### 2. 本地运行

```bash
# 直接运行
python main.py

# Docker运行
docker-compose up
```

## 📁 输出文件

- **Excel报告**: `output/PartnerName_ConversionReport_YYYY-MM-DD.xlsx`
- **JSON数据**: `output/conversions_YYYYMMDD_HHMMSS.json`
- **日志文件**: 控制台输出和Cloud Logging

## 🛠️ 高级功能

### API端点

当部署到Cloud Run时，提供以下HTTP端点：

- `GET /health` - 健康检查
- `GET /status` - 服务状态
- `POST /run` - 触发报告生成

### 邮件模板

支持自定义HTML邮件模板，包含：
- Partner专属内容
- 数据汇总表格
- 飞书链接（可选）

### 飞书集成

- 自动上传Excel文件到指定文件夹
- 支持大文件分片上传
- 自动获取访问token

## 🔍 监控和调试

### 查看日志

```bash
# Cloud Run日志
gcloud logs read --limit=50 \
  --filter='resource.type="cloud_run_revision"'

# Scheduler日志
gcloud logs read --limit=20 \
  --filter='resource.type="cloud_scheduler_job"'
```

### 测试连接

```bash
# 测试飞书连接
python main.py --test-feishu

# 测试邮件连接
python main.py --test-email
```

## 📞 支持

如有问题，请查看：

1. [部署指南](GCP_DEPLOYMENT.md)
2. [邮件设置](EMAIL_SETUP_README.md)
3. [飞书配置](FEISHU_UPLOAD_README.md)
4. [调度器设置](SCHEDULER_SETUP_GUIDE.md)

---

**Last Updated**: 2025-06-20  
**Version**: 2.0.0  
**Cloud Scheduler**: ✅ Daily 4PM for RAMPUP & YueMeng partners 
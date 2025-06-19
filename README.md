# WeeklyReporter

一个用于从Involve Asia API获取conversion数据并生成Excel周报的自动化工具。

## 📋 功能特性

- 🔌 **API数据获取**: 从Involve Asia API获取conversion数据
- 📊 **Excel转换**: 将JSON数据转换为Excel格式
- 🔧 **模块化设计**: 每个功能独立模块，可单独测试
- 📝 **详细日志**: 关键步骤的详细日志记录
- ⚙️ **灵活配置**: 统一的配置管理

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置设置

编辑 `config.py` 文件中的API配置：

```python
INVOLVE_ASIA_API_SECRET = "your_api_secret_here"
INVOLVE_ASIA_API_KEY = "your_api_key_here"
```

### 3. 运行程序

```bash
# 运行完整工作流（使用默认日期范围）
python main.py

# 指定日期范围
python main.py --start-date 2025-01-01 --end-date 2025-01-07

# 指定输出文件名
python main.py --output "我的周报.xlsx"
```

## 📁 项目结构

```
WeeklyReporter/
├── main.py                 # 主程序入口
├── config.py               # 全局配置文件
├── requirements.txt        # 依赖管理
├── modules/                # 核心功能模块
│   ├── __init__.py
│   ├── involve_asia_api.py # API数据获取模块
│   └── json_to_excel.py    # JSON转Excel模块
├── utils/                  # 工具模块
│   ├── __init__.py
│   └── logger.py           # 日志工具
└── output/                 # 输出文件目录（自动创建）
```

## 🔧 使用方法

### 完整工作流

```bash
# 基本使用
python main.py

# 自定义日期范围
python main.py --start-date 2025-01-01 --end-date 2025-01-07

# 保存中间JSON文件
python main.py --save-json

# 自定义输出文件名
python main.py --output "weekly_report_custom.xlsx"
```

### 单独功能模块

```bash
# 只获取API数据
python main.py --api-only

# 只转换现有JSON文件
python main.py --convert-only conversions.json
```

### 命令行参数

- `--start-date`: 开始日期 (YYYY-MM-DD格式)
- `--end-date`: 结束日期 (YYYY-MM-DD格式)
- `--output, -o`: Excel输出文件名
- `--api-only`: 只执行API数据获取
- `--convert-only`: 只执行JSON到Excel转换
- `--save-json`: 保存中间JSON文件
- `--verbose, -v`: 显示详细日志

## 📊 模块功能

### 1. API模块 (`modules/involve_asia_api.py`)

负责从Involve Asia API获取conversion数据：

```python
from modules.involve_asia_api import InvolveAsiaAPI

api = InvolveAsiaAPI()
api.authenticate()
data = api.get_conversions("2025-01-01", "2025-01-07")
```

### 2. 转换模块 (`modules/json_to_excel.py`)

负责将JSON数据转换为Excel文件：

```python
from modules.json_to_excel import json_to_excel

excel_file = json_to_excel(json_data, "output.xlsx")
```

### 3. 日志工具 (`utils/logger.py`)

统一的日志记录功能：

```python
from utils.logger import print_step

print_step("步骤名称", "执行信息")
```

## ⚙️ 配置说明

### 核心配置 (`config.py`)

```python
# API配置
INVOLVE_ASIA_API_SECRET = "your_secret"
INVOLVE_ASIA_API_KEY = "general"

# 业务配置
DEFAULT_DATE_RANGE = 1  # 默认获取1天数据
PREFERRED_CURRENCY = "USD"

# 文件配置
OUTPUT_DIR = "output"
FILE_NAME_TEMPLATE = "Pub_WeeklyReport_{date}.xlsx"
```

### 环境变量支持

可以通过环境变量覆盖配置：

```bash
export INVOLVE_ASIA_API_SECRET="your_secret"
export PREFERRED_CURRENCY="USD"
```

## 📋 输出格式

### Excel文件

- **默认文件名**: `Pub_WeeklyReport_YYYY-MM-DD.xlsx`
- **工作表名**: `Conversion Report`
- **位置**: `output/` 目录

### JSON文件（可选）

- **文件名**: `conversions_YYYYMMDD_HHMMSS.json`
- **位置**: `output/` 目录

## 🔍 日志输出示例

```
🚀 WeeklyReporter - Involve Asia数据处理工具
============================================================
⏰ 启动时间: 2025-01-18 10:30:00
📂 输出目录: output
============================================================
[2025-01-18 10:30:01] 工作流开始: 开始执行WeeklyReporter完整工作流
[2025-01-18 10:30:01] 认证步骤: 正在执行API认证...
[2025-01-18 10:30:02] 认证成功: 获得Token: t-xxxxx...
[2025-01-18 10:30:02] 数据获取: 正在获取转换数据 (2025-01-17 到 2025-01-18)
[2025-01-18 10:30:05] 数据获取成功: 成功获取完整数据: 150 条转换记录，共 2 页
[2025-01-18 10:30:05] 开始转换: 正在将JSON数据转换为Excel格式...
[2025-01-18 10:30:06] 导出成功: 成功转换 150 条记录到 output/Pub_WeeklyReport_2025-01-18.xlsx
[2025-01-18 10:30:06] 工作流完成: WeeklyReporter工作流执行成功

🎉 完整工作流执行成功！
📊 Excel文件已生成: output/Pub_WeeklyReport_2025-01-18.xlsx
```

## 🚨 常见问题

### API认证失败

**问题**: 认证步骤失败
**解决**: 检查 `config.py` 中的API密钥是否正确

### 数据获取失败

**问题**: API返回429错误
**解决**: 程序会自动处理频率限制，等待后重试

### 文件输出问题

**问题**: 输出目录不存在
**解决**: 程序会自动创建 `output/` 目录

## 📧 技术支持

如有问题，请检查：

1. ✅ Python版本 >= 3.7
2. ✅ 依赖包已正确安装
3. ✅ API配置信息正确
4. ✅ 网络连接正常

## 📝 更新日志

### v1.0.0 (2025-01-18)

- ✨ 初始版本发布
- 🔌 Involve Asia API集成
- 📊 JSON到Excel转换功能
- 🔧 模块化架构设计
- 📝 详细日志记录 
# 📧 WeeklyReporter 邮件功能设置指南

## 📋 概述

WeeklyReporter 支持自动发送转换报告邮件，包含报告摘要、附件和飞书链接。本文档将指导您完成邮件功能的设置和使用。

## 🛠️ Gmail 应用密码设置

### 1. 开启两步验证
1. 登录您的 Google 账户：[myaccount.google.com](https://myaccount.google.com)
2. 点击左侧 "安全性"
3. 在 "登录 Google" 部分，确保已开启 "两步验证"
4. 如未开启，请按提示完成两步验证设置

### 2. 生成应用密码
1. 在 "安全性" 页面，找到 "两步验证" 下方的 "应用密码"
2. 点击 "应用密码"
3. 在 "选择应用" 下拉菜单中选择 "邮件"
4. 在 "选择设备" 下拉菜单中选择 "其他（自定义名称）"
5. 输入 "WeeklyReporter" 作为应用名称
6. 点击 "生成"
7. 复制生成的16位应用密码（格式：abcd efgh ijkl mnop）

### 3. 配置应用密码
1. 打开项目根目录的 `config.py` 文件
2. 找到以下行：
   ```python
   EMAIL_PASSWORD = "your_gmail_app_password_here"
   ```
3. 将 `your_gmail_app_password_here` 替换为您刚才生成的16位应用密码
4. 保存文件

## ⚙️ 邮件配置说明

在 `config.py` 文件中，您可以修改以下邮件相关配置：

```python
# 邮件配置
EMAIL_SENDER = "GaryBu0801@gmail.com"              # 发件人邮箱
EMAIL_RECEIVERS = ["AmosFang927@gmail.com"]        # 收件人列表（支持多个）
EMAIL_PASSWORD = "your_gmail_app_password_here"    # Gmail应用密码
SMTP_SERVER = "smtp.gmail.com"                     # SMTP服务器
SMTP_PORT = 587                                    # SMTP端口
EMAIL_ENABLE_TLS = True                            # 启用TLS加密
EMAIL_INCLUDE_ATTACHMENTS = True                   # 是否包含Excel附件
EMAIL_INCLUDE_FEISHU_LINKS = True                  # 是否包含飞书链接
EMAIL_SUBJECT_TEMPLATE = "Conversion Report - {date}"  # 邮件主题模板

# 定时任务配置
SCHEDULE_ENABLED = True                            # 启用定时任务
DAILY_REPORT_TIME = "09:00"                       # 每日发送时间（24小时制）
TIMEZONE = "Asia/Shanghai"                         # 时区设置
```

## 🧪 测试邮件功能

### 1. 测试邮件连接
```bash
python main.py --test-email
```

### 2. 运行专用测试脚本
```bash
python test_email.py
```

### 3. 发送测试邮件（包含样本数据）
```bash
python test_email.py
```

## 🚀 使用邮件功能

### 1. 手动发送邮件报告
```bash
# 生成报告并发送邮件
python main.py --send-email

# 生成报告、上传飞书并发送邮件
python main.py --upload-feishu --send-email

# 指定日期范围并发送邮件
python main.py --start-date 2025-06-18 --end-date 2025-06-18 --send-email
```

### 2. 启动定时任务
```bash
# 启动定时任务（每日9:00自动执行）
python main.py --start-scheduler

# 立即执行一次定时任务（测试用）
python main.py --run-scheduler-now
```

## 📧 邮件内容格式

发送的邮件包含以下内容：

### 邮件主题
```
Conversion Report - 2025-06-18
```

### 邮件正文
- **收件人称呼**：Hi Partners,
- **邮件主题**：Conversion Report + 今天日期 如附件，请查收
- **报告摘要**：
  - 日期范围
  - 总转换数
  - Total Sales Amount（USD）
- **生成的文件列表**
- **飞书上传状态**（如果启用）
- **飞书文件链接**（如果上传成功且启用链接）
- **签名**：AutoReporter Agent

### 附件
- 主报告：`Pub_ConversionReport_YYYY-MM-DD.xlsx`
- Pub分类报告：`PubName_ConversionReport_YYYY-MM-DD.xlsx`

## 🔧 故障排除

### 常见问题及解决方案

1. **邮件连接失败**
   ```
   错误：(535, '5.7.8 Username and Password not accepted')
   ```
   - 确认Gmail应用密码设置正确
   - 确认两步验证已开启
   - 检查EMAIL_SENDER配置是否正确

2. **邮件发送失败**
   ```
   错误：(587, 'Connection unexpectedly closed')
   ```
   - 检查网络连接
   - 确认SMTP配置正确
   - 尝试重新生成应用密码

3. **配置未生效**
   - 重启程序
   - 检查config.py文件保存是否正确
   - 确认没有语法错误

### 调试步骤

1. 运行连接测试：
   ```bash
   python main.py --test-email
   ```

2. 检查配置：
   ```python
   # 在Python中验证配置
   import config
   print(f"发件人: {config.EMAIL_SENDER}")
   print(f"收件人: {config.EMAIL_RECEIVERS}")
   print(f"密码已设置: {config.EMAIL_PASSWORD != 'your_gmail_app_password_here'}")
   ```

3. 查看详细错误信息：
   ```bash
   python test_email.py
   ```

## 📅 定时任务说明

### 启动定时任务
```bash
python main.py --start-scheduler
```

### 定时任务功能
- **执行时间**：每日9:00（可在config.py中修改DAILY_REPORT_TIME）
- **执行内容**：
  1. 获取前一天的转换数据
  2. 生成Excel报告
  3. 上传到飞书（如果配置）
  4. 发送邮件报告
- **后台运行**：在独立线程中运行，不阻塞主程序
- **停止方式**：按 Ctrl+C 停止

### 修改执行时间
在 `config.py` 中修改：
```python
DAILY_REPORT_TIME = "09:00"  # 24小时制格式
```

## 📝 集成到其他系统

如果您需要在其他Python项目中使用邮件功能：

```python
from modules.email_sender import send_report_email

# 准备邮件数据
email_data = {
    'total_records': 86,
    'total_amount': '$12,345.67',
    'start_date': '2025-06-18',
    'end_date': '2025-06-18',
    'main_file': 'report.xlsx',
    'pub_files': [...]
}

# 发送邮件
result = send_report_email(
    email_data, 
    file_paths=['report.xlsx'],
    feishu_upload_result=None
)

if result['success']:
    print("邮件发送成功!")
else:
    print(f"邮件发送失败: {result['error']}")
```

## 🔒 安全注意事项

1. **保护应用密码**：
   - 不要将应用密码提交到代码仓库
   - 考虑使用环境变量存储敏感信息
   - 定期更换应用密码

2. **配置访问权限**：
   - 确保config.py文件权限适当
   - 在生产环境中考虑使用加密配置

3. **邮件内容安全**：
   - 邮件内容可能包含敏感业务数据
   - 确认收件人列表的准确性
   - 考虑添加邮件加密（高级功能）

## 📞 技术支持

如果遇到问题：

1. 查看本文档的故障排除部分
2. 运行测试脚本获取详细错误信息
3. 检查Gmail账户设置和网络连接
4. 联系技术支持团队 
# 飞书上传功能使用说明

## 📋 功能概述

飞书上传模块支持将生成的Excel文件自动上传到飞书Sheet，实现数据的在线协作和共享。

## ⚙️ 配置步骤

### 1. 获取飞书访问令牌

1. 登录飞书开放平台: https://open.feishu.cn/
2. 创建企业自建应用
3. 获取应用的 `Access Token`
4. 确保应用有以下权限：
   - `drive:file` (文件读写权限)
   - `drive:folder` (文件夹读写权限)

### 2. 配置参数

在 `config.py` 文件中更新以下配置：

```python
# 飞书上传配置
FEISHU_ACCESS_TOKEN = "t-g204xxxxxxxxxx"  # 替换为你的访问令牌
FEISHU_PARENT_NODE = "fldcxxxxxxxxxx"     # 替换为目标文件夹ID
```

### 3. 获取文件夹ID

1. 在飞书云文档中找到要上传的目标文件夹
2. 打开文件夹，从URL中获取文件夹ID
3. 例如：`https://example.feishu.cn/drive/folder/fldcxxxxxxxxxx`
4. 这里的 `fldcxxxxxxxxxx` 就是文件夹ID

## 🚀 使用方法

### 1. 完整工作流 + 飞书上传

```bash
# 获取数据、生成Excel并上传到飞书
python main.py --upload-feishu

# 指定日期范围并上传
python main.py --start-date 2025-01-01 --end-date 2025-01-07 --upload-feishu
```

### 2. 只上传现有文件

```bash
# 上传output目录下所有Excel文件
python main.py --upload-only
```

### 3. 测试飞书连接

```bash
# 测试飞书API连接是否正常
python main.py --test-feishu
```

### 4. 使用测试脚本

```bash
# 运行独立的飞书上传测试
python test_feishu_upload.py
```

## 📊 上传文件类型

以下类型的Excel文件会被上传：

1. **主报告文件**: `Pub_ConversionReport_YYYY-MM-DD.xlsx`
2. **Pub分类文件**: `{Pub名称}_ConversionReport_YYYY-MM-DD.xlsx`

例如：
- `Pub_ConversionReport_2025-01-18.xlsx` (主报告)
- `OEM3_ConversionReport_2025-01-18.xlsx` (OEM3的分类报告)
- `OEM2_ConversionReport_2025-01-18.xlsx` (OEM2的分类报告)

## 🔍 状态检查

### 成功上传

```
✅ 飞书上传完成: 成功上传 4 个文件到飞书
📄 成功上传的文件:
   ✅ Pub_ConversionReport_2025-01-18.xlsx
      - 文件ID: doccnxxxxxxxxxx
      - 访问链接: https://example.feishu.cn/sheets/shtcnxxxxxxxxxx
   ✅ OEM3_ConversionReport_2025-01-18.xlsx
      - 文件ID: doccnxxxxxxxxxx
```

### 部分失败

```
⚠️ 飞书上传部分失败: 上传完成，成功 2 个，失败 1 个
❌ 上传失败的文件:
   ❌ OEM2_ConversionReport_2025-01-18.xlsx: 文件大小超限
```

## ⚠️ 常见问题

### 1. 访问令牌错误

**错误信息**: `❌ 飞书API连接失败: HTTP 401`

**解决方案**:
- 检查 `FEISHU_ACCESS_TOKEN` 是否正确
- 确认令牌是否过期
- 验证应用权限是否正确配置

### 2. 文件夹权限问题

**错误信息**: `❌ 上传失败: 无权限访问目标文件夹`

**解决方案**:
- 检查 `FEISHU_PARENT_NODE` 文件夹ID是否正确
- 确认应用对目标文件夹有写入权限
- 联系管理员开通相应权限

### 3. 网络连接问题

**错误信息**: `❌ 飞书API连接异常: timeout`

**解决方案**:
- 检查网络连接
- 确认防火墙设置
- 尝试使用代理

### 4. 文件大小限制

**错误信息**: `❌ 上传失败: 文件大小超限`

**解决方案**:
- 飞书单个文件限制通常为100MB
- 检查Excel文件大小
- 考虑压缩或分拆大文件

## 🔧 高级配置

### 自定义上传参数

在 `config.py` 中可以调整更多参数：

```python
# 飞书上传配置
FEISHU_UPLOAD_URL = "https://open.feishu.cn/open-apis/drive/v1/files/upload_all"
FEISHU_FILE_TYPE = "sheet"  # 文件类型
```

### 代码集成

在其他Python脚本中使用飞书上传：

```python
from modules.feishu_uploader import upload_to_feishu

# 上传单个文件
result = upload_to_feishu("path/to/file.xlsx")

# 上传多个文件
files = ["file1.xlsx", "file2.xlsx"]
result = upload_to_feishu(files)

# 检查结果
if result['success']:
    print(f"成功上传 {result['success_count']} 个文件")
```

## 📧 技术支持

如遇问题，请检查：

1. ✅ 飞书访问令牌配置正确
2. ✅ 目标文件夹权限充足
3. ✅ 网络连接正常
4. ✅ 文件大小在限制范围内

---

*最后更新: 2025-01-18*
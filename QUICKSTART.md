# 🚀 快速开始指南

## 5分钟上手教程

### 步骤1: 安装依赖

```bash
cd /Users/william/project/swagger_api_tester
pip install -r requirements.txt
```

### 步骤2: 运行示例测试

使用内置的Pet Store API示例：

```bash
python main.py -s examples/petstore_swagger.json -u https://petstore.swagger.io/v2
```

您会看到类似的输出：

```
============================================================
🚀 Swagger API自动化测试框架
============================================================

📖 正在解析Swagger文件: examples/petstore_swagger.json
   API: Pet Store API v1.0.0
   Spec版本: Swagger 2.0
   基础URL: https://petstore.swagger.io/v2

🔍 正在分析API端点...
   发现 3 个API端点

📝 正在生成测试用例...
   生成 45 个测试用例

🧪 开始执行测试...
   执行模式: 串行

   [1/3] GET /pet/{petId} (15个用例)
        ✓ 12/15 通过

   [2/3] POST /pet (20个用例)
        ✓ 18/20 通过

   [3/3] POST /store/order (10个用例)
        ✓ 9/10 通过

📊 正在生成测试报告...

============================================================
✨ 测试完成！
============================================================

总用例数: 45
通过: 39 ✓
失败: 6 ✗
通过率: 86.67%

📄 报告已生成: reports/report_20260119_143025.html
```

### 步骤3: 查看测试报告

在浏览器中打开生成的HTML报告：

```bash
open reports/report_*.html
```

报告包含：
- 📊 测试概览统计
- 📈 可视化图表
- 📋 详细的测试结果
- 🔍 请求/响应详情

## 测试您自己的API

### 方法1: 直接指定URL

如果您的Swagger文件中没有定义服务器URL：

```bash
python main.py -s your_swagger.yaml -u http://your-api.com/api/v1
```

### 方法2: 使用配置文件

1. 复制配置模板：

```bash
cp config/default_config.yaml config/my_config.yaml
```

2. 编辑`config/my_config.yaml`，添加您的认证信息：

```yaml
auth:
  type: http_bearer
  token: "your_actual_token_here"
```

3. 运行测试：

```bash
python main.py -s your_swagger.yaml -c config/my_config.yaml
```

## 常见API认证配置

### Bearer Token认证

```yaml
auth:
  type: http_bearer
  token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### API Key认证（Header）

```yaml
auth:
  type: apiKey
  name: X-API-Key
  in: header
  value: "your-api-key-12345"
```

### API Key认证（Query）

```yaml
auth:
  type: apiKey
  name: api_key
  in: query
  value: "your-api-key-12345"
```

### Basic认证

```yaml
auth:
  type: http_basic
  username: "admin"
  password: "password123"
```

## 高级功能

### 并行测试（提高速度）

```bash
python main.py -s swagger.json -u http://api.com --parallel --workers 10
```

### 自定义输出路径

```bash
python main.py -s swagger.yaml -u http://api.com -o my_reports/test_$(date +%Y%m%d).html
```

### 跳过SSL验证（开发环境）

```bash
python main.py -s swagger.yaml -u https://localhost:8000 --no-ssl-verify
```

### 增加超时时间

```bash
python main.py -s swagger.yaml -u http://slow-api.com --timeout 60
```

## 命令行参数速查

| 参数 | 简写 | 说明 | 必填 |
|-----|------|------|------|
| --spec | -s | Swagger文件路径 | ✅ |
| --base-url | -u | API基础URL | * |
| --config | -c | 配置文件路径 | ❌ |
| --output | -o | 报告输出路径 | ❌ |
| --parallel | - | 并行执行 | ❌ |
| --workers | - | 并行线程数 | ❌ |
| --timeout | - | 请求超时（秒） | ❌ |
| --no-ssl-verify | - | 跳过SSL验证 | ❌ |

*如果Swagger文件中定义了servers/host，则base-url可选

## 查看帮助

```bash
python main.py --help
```

## 故障排查

### 问题1: 找不到模块

```
ModuleNotFoundError: No module named 'requests'
```

**解决**: 安装依赖

```bash
pip install -r requirements.txt
```

### 问题2: 连接失败

```
❌ 连接错误: Failed to establish a new connection
```

**解决**:
- 检查API URL是否正确
- 检查网络连接
- 检查防火墙设置

### 问题3: 认证失败

```
❌ 状态码错误: 期望[200], 实际401
```

**解决**:
- 检查配置文件中的认证信息
- 确认token是否有效
- 检查认证类型是否正确

### 问题4: SSL证书错误

```
SSLError: certificate verify failed
```

**解决**: 使用`--no-ssl-verify`参数（仅限开发环境）

```bash
python main.py -s swagger.yaml -u https://api.com --no-ssl-verify
```

## 下一步

- 📖 阅读[完整文档](README.md)了解所有功能
- 📝 查看[测试设计文档](TEST_DESIGN.md)了解测试策略
- 🔧 自定义[配置文件](config/default_config.yaml)
- 📊 探索HTML报告的各项功能

## 需要帮助？

- 查看`README.md`中的详细说明
- 查看`TEST_DESIGN.md`了解测试方法
- 查看示例文件`examples/petstore_swagger.json`

祝测试愉快！🎉

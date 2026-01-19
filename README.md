# 🚀 Swagger API自动化测试框架

基于Python的Swagger/OpenAPI自动化测试框架，支持全面的API测试，包括正向、反向、边界值、安全性等多种测试场景。

## ✨ 特性

- ✅ **多版本兼容**: 支持Swagger 2.0和OpenAPI 3.0+
- ✅ **多格式支持**: 支持JSON和YAML两种文件格式
- ✅ **自动化测试**: 自动遍历所有API端点并生成测试用例
- ✅ **全面覆盖**: 支持正向、反向、边界值、Schema验证、安全测试等
- ✅ **混合数据模式**: 自动生成测试数据，支持手动配置覆盖
- ✅ **多种认证**: 支持Bearer Token、API Key、Basic Auth、OAuth2
- ✅ **并发执行**: 支持并行测试以提高效率
- ✅ **精美报告**: 生成可视化的HTML测试报告

## 📦 安装

### 1. 克隆项目（或直接使用）

```bash
cd /Users/william/project/swagger_api_tester
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

依赖包括:
- requests: HTTP请求库
- pyyaml: YAML文件解析
- jsonschema: JSON Schema验证
- pytest: 测试框架
- prance: Swagger解析增强
- openapi-spec-validator: OpenAPI规范验证
- colorama: 终端彩色输出
- jinja2: 模板引擎

## 🚀 快速开始

### 基础用法

```bash
# 测试示例Pet Store API
python main.py -s examples/petstore_swagger.json -u https://petstore.swagger.io/v2

# 使用配置文件
python main.py -s your_swagger.yaml -c config/default_config.yaml

# 指定输出路径
python main.py -s swagger.json -u http://api.example.com -o reports/my_report.html
```

### 高级用法

```bash
# 并行执行测试（10个线程）
python main.py -s swagger.yaml -u http://api.example.com --parallel --workers 10

# 设置请求超时时间为60秒
python main.py -s swagger.json -u http://api.example.com --timeout 60

# 跳过SSL证书验证
python main.py -s swagger.yaml -u https://api.example.com --no-ssl-verify
```

## 📝 配置文件

创建`config/test_config.yaml`文件来配置认证和测试选项:

```yaml
# 认证配置
auth:
  type: http_bearer
  token: "your_bearer_token_here"

# 或使用API Key
# auth:
#   type: apiKey
#   name: X-API-Key
#   in: header
#   value: your_api_key_here

# 测试执行配置
execution:
  timeout: 30
  verify_ssl: true
  parallel: true
  max_workers: 10
```

详细配置说明请参考 `config/default_config.yaml`

## 🧪 测试场景

框架会为每个API端点自动生成以下测试用例:

### 1. 正向测试 (P0)
- 使用有效数据验证接口正常功能
- 验证响应状态码和Schema

### 2. 反向测试 (P1)
- 缺少必填参数
- 参数类型错误
- 无效认证

### 3. 边界值测试 (P1)
- 字符串长度边界（空串、最大长度、超长）
- 数值范围边界（最小值、最大值、越界）
- 数组元素数量边界

### 4. Schema验证 (P0)
- 响应字段完整性
- 数据类型验证
- 枚举值验证
- 嵌套对象验证

### 5. 安全测试 (P2)
- SQL注入防护
- XSS攻击防护
- 特殊字符处理

### 6. 认证测试 (P1)
- 无认证信息
- 无效Token
- 过期Token

## 📊 测试报告

测试完成后会生成HTML格式的可视化报告，包含:

- **测试概览**: 总用例数、通过数、失败数、通过率
- **统计图表**: 按优先级和测试类型的统计
- **详细结果**:
  - 按端点分组的测试结果
  - 每个用例的请求/响应详情
  - 错误和警告信息
  - 响应时间统计

![报告示例](报告包含丰富的可视化信息和详细的测试结果)

## 📂 项目结构

```
swagger_api_tester/
├── core/                      # 核心功能模块
│   ├── parser.py             # Swagger/OpenAPI解析器
│   ├── test_generator.py     # 测试用例生成器
│   ├── data_generator.py     # 测试数据生成器
│   ├── executor.py           # 测试执行引擎
│   ├── validator.py          # 响应验证器
│   ├── auth.py               # 认证处理
│   └── reporter.py           # HTML报告生成器
├── config/                    # 配置文件
│   └── default_config.yaml   # 默认配置示例
├── examples/                  # 示例文件
│   └── petstore_swagger.json # Pet Store API示例
├── reports/                   # 测试报告输出目录
├── requirements.txt           # Python依赖
├── main.py                    # 主程序入口
├── TEST_DESIGN.md            # 测试用例设计文档
└── README.md                  # 本文件
```

## 🛠️ 自定义测试数据

虽然框架会自动生成测试数据，但您也可以通过配置文件为特定接口提供自定义数据:

```yaml
endpoints:
  - path: /api/users
    method: POST
    test_data:
      valid:
        username: "testuser"
        email: "test@example.com"
      invalid:
        - case: "invalid_email"
          data:
            username: "testuser"
            email: "not-an-email"
          expected_status: 400
```

## 📖 测试方法论

本框架基于专业的测试用例设计方法，参考了:

- **正向测试**: 验证正常业务流程
- **反向测试**: 验证异常处理和边界条件
- **等价类划分**: 减少冗余测试用例
- **边界值分析**: 重点测试边界条件
- **OWASP Top 10**: 安全测试最佳实践
- **契约测试**: 严格验证API与文档一致性

详细的测试设计文档请参考 `TEST_DESIGN.md`

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🔗 相关资源

- [OpenAPI规范](https://swagger.io/specification/)
- [Swagger官方文档](https://swagger.io/docs/)
- [API测试最佳实践](https://www.ministryoftesting.com/dojo/series/the-testing-planet-archive/lessons/api-testing-best-practices)

## ⚡ 常见问题

### Q: 如何处理需要登录的API？
A: 在配置文件中配置认证信息，框架支持多种认证方式。

### Q: 可以只测试部分端点吗？
A: 可以，在配置文件中使用`include_paths`或`exclude_paths`来过滤。

### Q: 如何提高测试速度？
A: 使用`--parallel`参数启用并行测试，并适当增加`--workers`数量。

### Q: 测试失败了怎么办？
A: 查看生成的HTML报告，里面有详细的错误信息、请求和响应内容。

### Q: 支持GraphQL API吗？
A: 目前仅支持REST API，GraphQL支持计划在未来版本中添加。

---

**开发者**: 基于test-case-design skill设计开发
**版本**: 1.0.0
**最后更新**: 2026-01

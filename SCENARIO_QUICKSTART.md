# 场景测试快速入门（2.0版本）

## 什么是场景测试？

场景测试（Scenario Testing）是一种**业务流程测试**方法，可以串联多个API调用，模拟真实的用户操作流程，并在步骤之间传递数据。

**与1.0单接口测试的区别：**

| 特性 | 1.0 单接口测试 | 2.0 场景测试 |
|-----|--------------|------------|
| 测试对象 | 单个API端点 | 业务流程 |
| 数据传递 | ❌ 不支持 | ✅ 支持变量提取和注入 |
| 执行顺序 | 独立执行 | 按流程串联执行 |
| 适用场景 | API契约测试 | 端到端业务测试 |

## 快速开始

### 1. 运行示例场景

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行用户注册登录场景
python main.py --scenario scenarios/user_workflow_example.yaml

# 运行条件分支场景（需要真实API）
python main.py --scenario scenarios/conditional_flow_example.yaml
```

### 2. 场景定义示例

创建一个场景文件 `my_scenario.yaml`：

```yaml
scenario:
  name: "我的测试场景"
  description: "简单的用户操作流程"
  version: "2.0"

  # 全局配置
  config:
    base_url: "https://api.example.com"
    timeout: 30

  # 测试步骤
  steps:
    # 步骤1: 用户登录
    - name: "用户登录"
      api: "POST /api/auth/login"
      request:
        body:
          username: "testuser"
          password: "password123"
      extract:
        - name: "access_token"
          path: "$.data.token"
        - name: "user_id"
          path: "$.data.userId"
      assert:
        - "status_code == 200"
        - "response.data.token != null"

    # 步骤2: 查询用户信息
    - name: "查询用户信息"
      api: "GET /api/users/${user_id}"
      request:
        headers:
          Authorization: "Bearer ${access_token}"
      assert:
        - "status_code == 200"
        - "response.username != null"
```

### 3. 执行场景

```bash
python main.py --scenario my_scenario.yaml
```

## 核心功能

### 1. 变量提取和注入

**从响应中提取变量：**

```yaml
extract:
  - name: "user_id"           # 变量名
    path: "$.data.id"          # JSONPath表达式
  - name: "token"
    header: "Authorization"    # 从响应头提取
  - name: "session_id"
    cookie: "JSESSIONID"       # 从Cookie提取
```

**在请求中使用变量：**

```yaml
request:
  path: "/api/users/${user_id}"         # 路径参数
  headers:
    Authorization: "Bearer ${token}"    # 请求头
  query:
    page: "${page_num}"                 # 查询参数
  body:
    userId: ${user_id}                  # 请求体
    name: "${username}"
```

### 2. 内置函数

在变量中使用内置函数：

```yaml
request:
  body:
    username: "user_${timestamp()}"           # 当前时间戳
    email: "test_${uuid()}@example.com"       # UUID
    token: "${random_string(32)}"             # 32位随机字符串
    age: ${random_int(18, 60)}                # 18-60的随机整数
    date: "${date('%Y-%m-%d')}"               # 格式化日期
```

### 3. 断言

支持多种断言方式：

```yaml
assert:
  # 状态码断言
  - "status_code == 200"
  - "status_code in [200, 201]"

  # 响应数据断言
  - "response.data.id != null"
  - "response.data.username == '${expected_username}'"
  - "response.data.age > 18"

  # 数组长度
  - "len(response.data.items) >= 1"
```

### 4. Setup和Teardown

```yaml
scenario:
  name: "测试场景"

  # 前置操作
  setup:
    - name: "清理测试数据"
      api: "DELETE /api/test/cleanup"

  # 主要步骤
  steps:
    - name: "创建数据"
      api: "POST /api/data"

  # 清理操作（即使测试失败也会执行）
  teardown:
    - name: "删除测试数据"
      api: "DELETE /api/data/${data_id}"
```

## 使用技巧

### 1. 变量作用域

变量有三个作用域：

- **global**: 全局变量（整个测试会话）
- **scenario**: 场景变量（当前场景）
- **step**: 步骤变量（当前步骤）

变量查找顺序：step → scenario → global

### 2. JSONPath提取

```yaml
# 提取单个值
path: "$.data.user.id"

# 提取数组第一个元素
path: "$.data.items[0].name"

# 提取所有元素
path: "$.data.items[*].id"
```

### 3. 调试技巧

场景执行后会显示：
- 每个步骤的执行结果
- 提取的变量
- 失败的断言
- 上下文变量快照

使用这些信息来调试场景。

## 常见问题

### Q: 变量没有被替换？

**A:** 检查：
1. 变量名是否正确（区分大小写）
2. 是否使用了 `${variable}` 语法
3. 变量是否在之前的步骤中提取

### Q: 断言总是失败？

**A:** 检查：
1. 响应数据结构是否与JSONPath匹配
2. 变量值是否正确
3. 断言表达式是否正确

### Q: 如何查看实际的请求和响应？

**A:** 场景执行失败时会显示详细的错误信息，包括请求和响应内容。

## 进阶功能（规划中）

以下功能正在开发中：

- [ ] 条件分支（if-then-else）
- [ ] 循环（loop）
- [ ] 并行执行（parallel）
- [ ] 场景测试HTML报告
- [ ] 数据驱动测试

## 文档参考

- [场景设计文档](SCENARIO_DESIGN_V2.md) - 完整的设计规范
- [README.md](README.md) - 1.0版本使用说明
- [测试设计](TEST_DESIGN.md) - 测试用例设计方法

---

**提示**: 场景测试功能目前处于2.0版本，核心功能已完成，高级功能正在开发中。

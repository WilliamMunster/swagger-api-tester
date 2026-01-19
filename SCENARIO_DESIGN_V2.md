# Swagger API自动化测试框架 2.0 - 业务流程测试设计

## 版本演进

| 版本 | 核心能力 | 适用场景 |
|------|---------|---------|
| 1.0 | 单接口测试 | 独立的API端点验证 |
| **2.0** | **业务流程测试** | **接口串联、数据依赖、条件分支** |

## 1.0 vs 2.0 对比

### 1.0 的局限性

```
❌ 只能测试单个接口
❌ 接口之间无法传递数据
❌ 无法模拟真实业务流程
❌ 无法处理条件分支
❌ 无法验证数据一致性
```

**示例问题**：
- 测试"查询订单"接口时，订单ID从哪里来？
- 测试"修改用户信息"后，如何验证"查询用户"返回的是修改后的数据？
- 如何测试"如果用户余额不足，则支付失败"这种业务逻辑？

### 2.0 的核心能力

```
✅ 场景编排：串联、并联、条件分支
✅ 数据传递：响应字段提取、变量注入
✅ 上下文管理：全局变量、场景变量
✅ 依赖分析：自动识别接口依赖关系
✅ 条件判断：根据响应决定下一步
✅ 流程验证：端到端数据一致性
```

---

## 核心概念

### 1. 测试场景（Scenario）

一个完整的业务流程，包含多个步骤。

```yaml
scenario:
  name: "用户下单流程"
  description: "测试从注册到下单的完整流程"
  steps:
    - 用户注册
    - 用户登录
    - 查询商品
    - 加入购物车
    - 创建订单
    - 支付订单
    - 查询订单状态
```

### 2. 步骤（Step）

场景中的单个API调用。

```yaml
step:
  name: "用户登录"
  api: "POST /api/auth/login"
  request:
    body:
      username: "${register.username}"  # 引用前一步的数据
      password: "123456"
  extract:  # 从响应中提取数据
    - name: "access_token"
      path: "$.data.token"
    - name: "user_id"
      path: "$.data.userId"
  assert:  # 断言
    - "status_code == 200"
    - "response.data.token != null"
```

### 3. 数据上下文（Context）

在整个场景中共享的数据。

```python
context = {
    "global": {  # 全局变量
        "base_url": "http://api.example.com",
        "api_key": "xxx"
    },
    "scenario": {  # 场景变量
        "user_id": "12345",
        "order_id": "67890",
        "access_token": "eyJhbG..."
    },
    "step": {  # 当前步骤变量
        "current_time": "2026-01-19"
    }
}
```

### 4. 变量提取（Extract）

从API响应中提取数据。

支持的提取方式：
- **JSONPath**: `$.data.userId`
- **正则表达式**: `order_id: (\d+)`
- **Header**: `header.X-Request-Id`
- **Cookie**: `cookie.session_id`

### 5. 条件分支（Condition）

根据响应结果决定下一步。

```yaml
condition:
  if: "response.data.balance >= 100"
  then:
    - step: "使用余额支付"
  else:
    - step: "使用第三方支付"
```

---

## 设计方案

### 架构图

```
┌─────────────────────────────────────────────────┐
│           Scenario Definition (YAML)            │
│  定义业务流程、数据依赖、条件分支                │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│         Scenario Parser（场景解析器）            │
│  解析YAML，构建执行计划                          │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│      Dependency Analyzer（依赖分析器）           │
│  分析接口依赖关系，生成执行顺序                   │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│    Scenario Executor（场景执行引擎）             │
│  ┌─────────────────────────────────────────┐   │
│  │  Context Manager（上下文管理器）         │   │
│  │  - 全局变量                              │   │
│  │  - 场景变量                              │   │
│  │  - 变量作用域                            │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │  Variable Extractor（变量提取器）        │   │
│  │  - JSONPath提取                          │   │
│  │  - 正则提取                              │   │
│  │  - Header/Cookie提取                     │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │  Variable Injector（变量注入器）         │   │
│  │  - 请求参数注入                          │   │
│  │  - 请求体注入                            │   │
│  │  - Header注入                            │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │  Condition Evaluator（条件判断器）       │   │
│  │  - 表达式求值                            │   │
│  │  - 分支选择                              │   │
│  └─────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│     Scenario Reporter（场景测试报告）            │
│  - 流程可视化                                    │
│  - 数据流追踪                                    │
│  - 断言结果                                      │
└─────────────────────────────────────────────────┘
```

---

## 场景定义 DSL

### 基础场景示例

```yaml
scenario:
  name: "用户注册登录流程"
  description: "测试用户注册并登录"

  # 全局配置
  config:
    base_url: "http://api.example.com"
    timeout: 30
    retry: 2

  # 前置操作（可选）
  setup:
    - step: "清理测试数据"
      api: "DELETE /api/test/cleanup"

  # 测试步骤
  steps:
    # 步骤1: 用户注册
    - name: "用户注册"
      api: "POST /api/users/register"
      request:
        body:
          username: "test_${timestamp}"
          email: "test_${timestamp}@example.com"
          password: "Test@123456"
      extract:
        - name: "user_id"
          path: "$.data.id"
        - name: "username"
          path: "$.data.username"
      assert:
        - "status_code == 201"
        - "response.data.id != null"

    # 步骤2: 用户登录
    - name: "用户登录"
      api: "POST /api/auth/login"
      request:
        body:
          username: "${username}"  # 引用上一步提取的变量
          password: "Test@123456"
      extract:
        - name: "access_token"
          path: "$.data.token"
      assert:
        - "status_code == 200"
        - "response.data.token != null"

    # 步骤3: 查询用户信息
    - name: "查询用户信息"
      api: "GET /api/users/${user_id}"
      request:
        headers:
          Authorization: "Bearer ${access_token}"
      assert:
        - "status_code == 200"
        - "response.data.username == '${username}'"

  # 后置清理（可选）
  teardown:
    - step: "删除测试用户"
      api: "DELETE /api/users/${user_id}"
```

### 条件分支场景

```yaml
scenario:
  name: "订单支付流程"
  steps:
    - name: "创建订单"
      api: "POST /api/orders"
      extract:
        - name: "order_id"
          path: "$.data.orderId"
        - name: "total_amount"
          path: "$.data.totalAmount"

    - name: "查询用户余额"
      api: "GET /api/users/${user_id}/balance"
      extract:
        - name: "balance"
          path: "$.data.balance"

    # 条件分支：根据余额选择支付方式
    - name: "支付决策"
      condition:
        if: "${balance} >= ${total_amount}"
        then:
          - name: "余额支付"
            api: "POST /api/orders/${order_id}/pay"
            request:
              body:
                payment_method: "balance"
            assert:
              - "status_code == 200"
              - "response.data.status == 'paid'"
        else:
          - name: "第三方支付"
            api: "POST /api/orders/${order_id}/pay"
            request:
              body:
                payment_method: "alipay"
            assert:
              - "status_code == 200"
              - "response.data.payUrl != null"
```

### 循环场景

```yaml
scenario:
  name: "批量创建商品"
  steps:
    - name: "批量创建"
      loop:
        items: [1, 2, 3, 4, 5]
        variable: "index"
        steps:
          - name: "创建商品${index}"
            api: "POST /api/products"
            request:
              body:
                name: "商品${index}"
                price: "${ index * 100 }"
            extract:
              - name: "product_${index}_id"
                path: "$.data.id"
```

### 并行执行场景

```yaml
scenario:
  name: "并发查询测试"
  steps:
    - name: "准备数据"
      api: "POST /api/data/prepare"
      extract:
        - name: "ids"
          path: "$.data.ids"

    - name: "并行查询"
      parallel:
        items: "${ids}"
        variable: "id"
        max_workers: 10
        steps:
          - name: "查询详情${id}"
            api: "GET /api/data/${id}"
            assert:
              - "status_code == 200"
```

---

## 变量系统

### 变量作用域

```yaml
# 1. 全局变量（整个测试会话）
global:
  base_url: "http://api.example.com"
  api_key: "xxx"

# 2. 场景变量（当前场景）
scenario:
  user_id: "12345"
  access_token: "eyJhbG..."

# 3. 步骤变量（当前步骤）
step:
  current_time: "2026-01-19"
  random_id: "abc123"
```

### 内置函数

支持在变量中使用内置函数：

```yaml
request:
  body:
    username: "user_${timestamp()}"           # 当前时间戳
    email: "test_${uuid()}@example.com"       # UUID
    random_str: "${random_string(10)}"        # 随机字符串
    random_int: "${random_int(1, 100)}"       # 随机整数
    current_date: "${date('YYYY-MM-DD')}"     # 格式化日期
    hash_value: "${md5('hello')}"             # MD5哈希
```

### 变量提取

#### JSONPath提取

```yaml
extract:
  - name: "user_id"
    path: "$.data.id"
  - name: "first_product_name"
    path: "$.data.products[0].name"
  - name: "all_ids"
    path: "$.data.items[*].id"
```

#### 正则提取

```yaml
extract:
  - name: "order_id"
    regex: 'order_id: "(\d+)"'
    group: 1
```

#### Header提取

```yaml
extract:
  - name: "request_id"
    header: "X-Request-Id"
```

### 变量注入

变量使用 `${variable_name}` 语法注入：

```yaml
request:
  path: "/api/users/${user_id}"
  query:
    page: "${page_num}"
  headers:
    Authorization: "Bearer ${access_token}"
  body:
    name: "${username}"
    age: ${age}  # 数字类型不需要引号
```

---

## 条件判断表达式

支持的运算符：

```yaml
# 比较运算符
- "age > 18"
- "balance >= 100"
- "status == 'active'"
- "name != null"

# 逻辑运算符
- "age > 18 and balance >= 100"
- "status == 'active' or status == 'pending'"
- "not is_deleted"

# 包含判断
- "'admin' in roles"
- "status in ['active', 'pending']"

# 复杂表达式
- "response.data.balance >= order.totalAmount"
- "len(response.data.items) > 0"
```

---

## 断言系统

### 状态码断言

```yaml
assert:
  - "status_code == 200"
  - "status_code in [200, 201]"
```

### 响应体断言

```yaml
assert:
  - "response.data.id != null"
  - "response.data.username == '${expected_username}'"
  - "response.data.age > 18"
  - "len(response.data.items) >= 1"
```

### Schema断言

```yaml
assert:
  - "validate_schema(response.data, 'UserSchema')"
```

### 自定义断言

```yaml
assert:
  - name: "验证邮箱格式"
    expression: "regex_match(response.data.email, r'^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$')"
```

---

## 依赖分析

### 自动依赖识别

框架会自动分析：

1. **参数依赖**：如果接口B的参数引用了接口A的响应，则B依赖A
2. **Schema依赖**：通过Swagger定义推断依赖关系
3. **语义依赖**：根据命名规则推断（如 POST /users 和 GET /users/{id}）

### 依赖图生成

```
注册用户 → 用户登录 → 查询用户信息
                ↓
              创建订单 → 订单支付 → 查询订单
                ↓           ↓
            查询购物车   查询支付状态
```

### 执行顺序优化

- 串行依赖：严格按顺序执行
- 并行机会：无依赖关系的步骤可以并行执行

---

## 使用示例

### 示例1：电商下单流程

```yaml
scenario:
  name: "电商下单完整流程"

  steps:
    - name: "用户登录"
      api: "POST /api/auth/login"
      request:
        body:
          username: "test_user"
          password: "password123"
      extract:
        - name: "token"
          path: "$.data.token"
        - name: "user_id"
          path: "$.data.userId"

    - name: "查询商品列表"
      api: "GET /api/products"
      request:
        headers:
          Authorization: "Bearer ${token}"
      extract:
        - name: "product_id"
          path: "$.data[0].id"
        - name: "product_price"
          path: "$.data[0].price"

    - name: "加入购物车"
      api: "POST /api/cart/items"
      request:
        headers:
          Authorization: "Bearer ${token}"
        body:
          productId: "${product_id}"
          quantity: 2
      assert:
        - "status_code == 200"

    - name: "创建订单"
      api: "POST /api/orders"
      request:
        headers:
          Authorization: "Bearer ${token}"
      extract:
        - name: "order_id"
          path: "$.data.orderId"
        - name: "total_amount"
          path: "$.data.totalAmount"
      assert:
        - "status_code == 201"
        - "response.data.totalAmount == ${product_price} * 2"

    - name: "订单支付"
      api: "POST /api/orders/${order_id}/pay"
      request:
        headers:
          Authorization: "Bearer ${token}"
        body:
          paymentMethod: "alipay"
      assert:
        - "status_code == 200"

    - name: "查询订单状态"
      api: "GET /api/orders/${order_id}"
      request:
        headers:
          Authorization: "Bearer ${token}"
      assert:
        - "status_code == 200"
        - "response.data.status == 'paid'"
```

---

## 技术实现要点

### 1. 场景解析器

```python
class ScenarioParser:
    def parse(yaml_file) -> Scenario:
        """解析YAML场景定义"""

    def validate(scenario) -> List[Error]:
        """验证场景定义的合法性"""
```

### 2. 上下文管理器

```python
class ContextManager:
    def __init__(self):
        self.global_vars = {}
        self.scenario_vars = {}
        self.step_vars = {}

    def set(name, value, scope='scenario'):
        """设置变量"""

    def get(name) -> Any:
        """获取变量（自动搜索作用域）"""

    def resolve(template: str) -> str:
        """解析模板字符串中的变量"""
```

### 3. 变量提取器

```python
class VariableExtractor:
    def extract_jsonpath(response, path: str) -> Any:
        """JSONPath提取"""

    def extract_regex(text, pattern: str, group: int) -> str:
        """正则提取"""

    def extract_header(headers, name: str) -> str:
        """Header提取"""
```

### 4. 条件判断器

```python
class ConditionEvaluator:
    def evaluate(expression: str, context: dict) -> bool:
        """求值条件表达式"""

    def select_branch(condition, context) -> List[Step]:
        """选择执行分支"""
```

### 5. 场景执行器

```python
class ScenarioExecutor:
    def execute(scenario: Scenario) -> ScenarioResult:
        """执行场景"""

        # 初始化上下文
        context = ContextManager()

        # 执行setup
        self.execute_setup(scenario.setup, context)

        # 执行主流程
        for step in scenario.steps:
            # 解析变量
            resolved_step = self.resolve_variables(step, context)

            # 执行API调用
            response = self.execute_api(resolved_step)

            # 提取变量
            self.extract_variables(response, step.extract, context)

            # 执行断言
            self.run_assertions(response, step.assert, context)

            # 处理条件分支
            if step.condition:
                next_steps = self.evaluate_condition(step.condition, context)
                for next_step in next_steps:
                    self.execute_step(next_step, context)

        # 执行teardown
        self.execute_teardown(scenario.teardown, context)
```

---

## 报告增强

### 流程可视化

```
┌────────────┐
│ 用户注册    │ ✓
└──────┬─────┘
       │
       ↓
┌────────────┐
│ 用户登录    │ ✓
└──────┬─────┘
       │
       ↓
┌────────────┐
│ 创建订单    │ ✓
└──────┬─────┘
       │
    ┌──┴──┐
    ↓     ↓
┌────────┐ ┌────────┐
│余额支付│ │第三方  │ ✗
│  (跳过)│ │  支付  │
└────────┘ └────────┘
```

### 数据流追踪

```
步骤1: 用户注册
  ↓ user_id = "12345"
  ↓ username = "test_user"

步骤2: 用户登录
  → 使用: username = "test_user"
  ↓ access_token = "eyJhbG..."

步骤3: 创建订单
  → 使用: access_token = "eyJhbG..."
  ↓ order_id = "67890"

步骤4: 订单支付
  → 使用: order_id = "67890"
  → 使用: access_token = "eyJhbG..."
```

---

## 总结

2.0版本通过引入**场景编排**、**数据上下文**、**条件分支**等能力，将框架从单接口测试升级为**业务流程测试**，能够：

✅ 真实模拟用户操作流程
✅ 验证接口之间的数据传递
✅ 测试复杂的业务逻辑
✅ 提供端到端的测试覆盖
✅ 自动化业务回归测试

这将大大提升API测试的价值和效率！

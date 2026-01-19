"""
场景执行引擎 - 执行业务流程测试场景
"""

import requests
import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .scenario_parser import ScenarioConfig, StepConfig
from .context_manager import ContextManager
from .variable_extractor import VariableExtractor
from .condition_evaluator import ConditionEvaluator


@dataclass
class StepResult:
    """步骤执行结果"""
    name: str
    api: str
    passed: bool
    status_code: Optional[int] = None
    response_time: float = 0.0
    request: Dict[str, Any] = field(default_factory=dict)
    response_data: Any = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    extracted_vars: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""


@dataclass
class ScenarioResult:
    """场景执行结果"""
    name: str
    description: str
    passed: bool
    total_steps: int
    passed_steps: int
    failed_steps: int
    skipped_steps: int
    total_time: float
    setup_results: List[StepResult] = field(default_factory=list)
    step_results: List[StepResult] = field(default_factory=list)
    teardown_results: List[StepResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    context_snapshot: Dict[str, Any] = field(default_factory=dict)


class ScenarioExecutor:
    """场景测试执行器"""

    def __init__(
            self,
            base_url: str = None,
            timeout: int = 30,
            verify_ssl: bool = True,
            auth_token: str = None
    ):
        """
        初始化场景执行器

        Args:
            base_url: API基础URL（如果场景配置中没有则使用此值）
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书
            auth_token: 认证Token（可选）
        """
        self.default_base_url = base_url
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.auth_token = auth_token
        self.session = requests.Session()

        # 初始化组件
        self.context = ContextManager()
        self.extractor = VariableExtractor()
        self.evaluator = ConditionEvaluator(self.context)

    def execute(self, scenario: ScenarioConfig) -> ScenarioResult:
        """
        执行场景

        Args:
            scenario: 场景配置

        Returns:
            ScenarioResult: 场景执行结果
        """
        start_time = time.time()

        # 初始化全局配置
        self._init_global_config(scenario.config)

        # 创建结果对象
        result = ScenarioResult(
            name=scenario.name,
            description=scenario.description,
            passed=True,
            total_steps=len(scenario.setup) + len(scenario.steps) + len(scenario.teardown),
            passed_steps=0,
            failed_steps=0,
            skipped_steps=0,
            total_time=0.0
        )

        try:
            # 1. 执行setup步骤
            if scenario.setup:
                print(f"\n⚙️  执行前置步骤...")
                result.setup_results = self._execute_steps(scenario.setup, "Setup")
                self._update_stats(result, result.setup_results)

            # 2. 执行主要步骤
            if scenario.steps:
                print(f"\n🚀 执行测试步骤...")
                result.step_results = self._execute_steps(scenario.steps, "Main")
                self._update_stats(result, result.step_results)

            # 3. 执行teardown步骤（即使前面失败也要执行）
            if scenario.teardown:
                print(f"\n🧹 执行清理步骤...")
                result.teardown_results = self._execute_steps(scenario.teardown, "Teardown")
                self._update_stats(result, result.teardown_results)

        except Exception as e:
            result.passed = False
            result.errors.append(f"场景执行异常: {str(e)}")
            print(f"\n❌ 场景执行异常: {e}")

        # 计算总耗时
        result.total_time = time.time() - start_time

        # 判断场景是否通过
        result.passed = result.failed_steps == 0 and not result.errors

        # 保存上下文快照
        result.context_snapshot = self.context.to_dict()

        return result

    def _init_global_config(self, config: Dict):
        """初始化全局配置"""
        # 设置base_url
        base_url = config.get('base_url', self.default_base_url)
        if base_url:
            self.context.set('base_url', base_url, 'global')

        # 设置其他全局配置
        if 'timeout' in config:
            self.timeout = config['timeout']

        for key, value in config.items():
            if key not in ['base_url', 'timeout', 'retry']:
                self.context.set(key, value, 'global')

    def _execute_steps(self, steps: List[StepConfig], phase: str) -> List[StepResult]:
        """
        执行步骤列表

        Args:
            steps: 步骤配置列表
            phase: 阶段名称（Setup/Main/Teardown）

        Returns:
            List[StepResult]: 步骤结果列表
        """
        results = []

        for i, step in enumerate(steps, 1):
            print(f"  [{i}/{len(steps)}] {step.name}")

            # 清除步骤变量
            self.context.clear_step()

            # 执行步骤
            step_result = self._execute_step(step)
            results.append(step_result)

            # 如果步骤失败且不是teardown阶段，可以选择停止
            if not step_result.passed and not step_result.skipped and phase != "Teardown":
                print(f"      ❌ 失败: {', '.join(step_result.errors)}")
                # 继续执行其他步骤（可以根据需要改为停止）
            elif step_result.skipped:
                print(f"      ⊘ 跳过: {step_result.skip_reason}")
            else:
                print(f"      ✓ 通过 ({step_result.response_time:.2f}s)")

        return results

    def _execute_step(self, step: StepConfig) -> StepResult:
        """
        执行单个步骤

        Args:
            step: 步骤配置

        Returns:
            StepResult: 步骤执行结果
        """
        result = StepResult(
            name=step.name,
            api=step.api,
            passed=False
        )

        try:
            # 1. 解析API定义（METHOD /path）
            method, path = self._parse_api(step.api)

            # 2. 构建请求
            url = self._build_url(path)
            headers = self._build_headers(step.request.get('headers', {}))
            params = self._build_params(step.request.get('query', {}))
            body = self._build_body(step.request.get('body'))

            # 3. 记录请求信息
            result.request = {
                'method': method,
                'url': url,
                'headers': headers,
                'params': params,
                'body': body
            }

            # 4. 执行HTTP请求
            start_time = time.time()
            response = self._make_request(method, url, headers, params, body)
            result.response_time = time.time() - start_time

            # 5. 记录响应信息
            result.status_code = response.status_code
            result.response_headers = dict(response.headers)

            # 解析响应数据
            try:
                result.response_data = response.json()
            except:
                result.response_data = response.text

            # 6. 提取变量
            if step.extract:
                extracted = self.extractor.extract(
                    result.response_data,
                    step.extract,
                    result.response_headers
                )
                result.extracted_vars = extracted

                # 将提取的变量保存到上下文
                for name, value in extracted.items():
                    self.context.set(name, value, 'scenario')
                    print(f"      📌 提取变量: {name} = {value}")

            # 7. 执行断言
            if step.assert_rules:
                assertion_errors = self._run_assertions(
                    step.assert_rules,
                    result.status_code,
                    result.response_data
                )
                if assertion_errors:
                    result.errors.extend(assertion_errors)
                    result.passed = False
                else:
                    result.passed = True
            else:
                # 没有断言规则，默认检查状态码是否为2xx
                if 200 <= result.status_code < 300:
                    result.passed = True
                else:
                    result.errors.append(f"状态码 {result.status_code} 不在成功范围内")
                    result.passed = False

            # 8. 处理条件分支
            if step.condition:
                self._handle_condition(step.condition, result)

        except requests.RequestException as e:
            result.passed = False
            result.errors.append(f"请求失败: {str(e)}")
        except Exception as e:
            result.passed = False
            result.errors.append(f"步骤执行异常: {str(e)}")

        return result

    def _parse_api(self, api: str) -> tuple:
        """
        解析API定义

        Args:
            api: API定义，如 "POST /api/users"

        Returns:
            (method, path): HTTP方法和路径
        """
        parts = api.strip().split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"API格式错误: {api}")

        method = parts[0].upper()
        path = parts[1]

        return method, path

    def _build_url(self, path: str) -> str:
        """
        构建完整URL

        Args:
            path: 路径（可能包含变量）

        Returns:
            str: 完整URL
        """
        # 解析路径中的变量
        resolved_path = self.context.resolve(path)

        # 获取base_url
        base_url = self.context.get('base_url', self.default_base_url)
        if not base_url:
            raise ValueError("未配置base_url")

        # 拼接URL
        base_url = base_url.rstrip('/')
        if not resolved_path.startswith('/'):
            resolved_path = '/' + resolved_path

        return base_url + resolved_path

    def _build_headers(self, headers: Dict) -> Dict:
        """构建请求头（解析变量）"""
        if not headers:
            headers = {}

        # 解析变量
        resolved = self.context.resolve(headers)

        # 添加认证头
        if self.auth_token and 'Authorization' not in resolved:
            resolved['Authorization'] = f'Bearer {self.auth_token}'

        return resolved

    def _build_params(self, params: Dict) -> Dict:
        """构建查询参数（解析变量）"""
        if not params:
            return {}

        return self.context.resolve(params)

    def _build_body(self, body: Any) -> Any:
        """构建请求体（解析变量）"""
        if body is None:
            return None

        return self.context.resolve(body)

    def _make_request(
            self,
            method: str,
            url: str,
            headers: Dict,
            params: Dict,
            body: Any
    ) -> requests.Response:
        """
        执行HTTP请求

        Args:
            method: HTTP方法
            url: 完整URL
            headers: 请求头
            params: 查询参数
            body: 请求体

        Returns:
            requests.Response: 响应对象
        """
        kwargs = {
            'timeout': self.timeout,
            'verify': self.verify_ssl
        }

        if headers:
            kwargs['headers'] = headers

        if params:
            kwargs['params'] = params

        if body is not None:
            if isinstance(body, dict):
                kwargs['json'] = body
            else:
                kwargs['data'] = body

        response = self.session.request(method, url, **kwargs)
        return response

    def _run_assertions(
            self,
            assert_rules: List[str],
            status_code: int,
            response_data: Any
    ) -> List[str]:
        """
        执行断言

        Args:
            assert_rules: 断言规则列表
            status_code: 响应状态码
            response_data: 响应数据

        Returns:
            List[str]: 错误列表（空表示全部通过）
        """
        errors = []

        for rule in assert_rules:
            try:
                # 替换 status_code 和 response 引用
                rule_with_context = rule.replace('status_code', str(status_code))

                # 求值断言表达式
                passed = self.evaluator.evaluate(rule_with_context, response_data)

                if not passed:
                    errors.append(f"断言失败: {rule}")

            except Exception as e:
                errors.append(f"断言执行错误: {rule} - {str(e)}")

        return errors

    def _handle_condition(self, condition: Dict, step_result: StepResult):
        """
        处理条件分支

        Args:
            condition: 条件配置
            step_result: 当前步骤的结果
        """
        try:
            # 求值条件
            condition_expr = condition.get('if')
            if not condition_expr:
                return

            passed = self.evaluator.evaluate(condition_expr, step_result.response_data)

            # 根据条件选择分支
            if passed:
                next_steps = condition.get('then', [])
            else:
                next_steps = condition.get('else', [])

            # 执行后续步骤
            if next_steps:
                # 这里简化处理，实际可能需要更复杂的逻辑
                print(f"      → 条件分支: {'then' if passed else 'else'}")

        except Exception as e:
            step_result.warnings.append(f"条件分支处理失败: {str(e)}")

    def _update_stats(self, scenario_result: ScenarioResult, step_results: List[StepResult]):
        """更新统计信息"""
        for step_result in step_results:
            if step_result.skipped:
                scenario_result.skipped_steps += 1
            elif step_result.passed:
                scenario_result.passed_steps += 1
            else:
                scenario_result.failed_steps += 1


# 测试代码
if __name__ == '__main__':
    from .scenario_parser import ScenarioParser

    # 解析场景
    parser = ScenarioParser()
    scenario = parser.parse_file('scenarios/user_workflow_example.yaml')

    # 执行场景
    executor = ScenarioExecutor()
    result = executor.execute(scenario)

    # 输出结果
    print(f"\n{'=' * 60}")
    print(f"场景: {result.name}")
    print(f"状态: {'✓ 通过' if result.passed else '✗ 失败'}")
    print(f"步骤: {result.total_steps} 个")
    print(f"  - 通过: {result.passed_steps}")
    print(f"  - 失败: {result.failed_steps}")
    print(f"  - 跳过: {result.skipped_steps}")
    print(f"耗时: {result.total_time:.2f}秒")
    print(f"{'=' * 60}")

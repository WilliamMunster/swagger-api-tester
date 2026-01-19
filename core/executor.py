"""
测试执行引擎 - 执行API测试用例并收集结果
"""

import requests
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from .validator import ResponseValidator
from .auth import AuthHandler


class TestResult:
    """单个测试用例的结果"""

    def __init__(self, test_case: Dict):
        self.test_case = test_case
        self.passed = False
        self.status_code = None
        self.response_data = None
        self.response_time = 0
        self.errors = []
        self.warnings = []
        self.request_info = {}
        self.response_info = {}

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'test_case_id': self.test_case.get('id'),
            'test_case_name': self.test_case.get('name'),
            'test_type': self.test_case.get('type'),
            'priority': self.test_case.get('priority'),
            'passed': self.passed,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'errors': self.errors,
            'warnings': self.warnings,
            'request': self.request_info,
            'response': self.response_info
        }


class TestExecutor:
    """API测试执行器"""

    def __init__(
            self,
            base_url: str,
            auth_handler: Optional[AuthHandler] = None,
            timeout: int = 30,
            verify_ssl: bool = True
    ):
        """
        初始化测试执行器

        Args:
            base_url: API基础URL
            auth_handler: 认证处理器
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书
        """
        self.base_url = base_url.rstrip('/')
        self.auth_handler = auth_handler
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()

    def execute_test_case(self, test_case: Dict, endpoint: Dict) -> TestResult:
        """
        执行单个测试用例

        Args:
            test_case: 测试用例
            endpoint: 端点信息

        Returns:
            TestResult对象
        """
        result = TestResult(test_case)

        try:
            # 构建请求
            url = self._build_url(test_case)
            headers = self._build_headers(test_case)
            params = test_case.get('query_params', {})

            # 应用认证（除非测试用例要求跳过）
            if self.auth_handler and not test_case.get('skip_auth'):
                headers, params = self.auth_handler.apply_auth(headers, params)

            # 记录请求信息
            result.request_info = {
                'method': test_case['method'],
                'url': url,
                'headers': headers,
                'params': params,
                'body': test_case.get('body')
            }

            # 发送请求
            start_time = time.time()
            response = self._send_request(
                method=test_case['method'],
                url=url,
                headers=headers,
                params=params,
                json=test_case.get('body')
            )
            end_time = time.time()

            # 记录响应信息
            result.status_code = response.status_code
            result.response_time = round((end_time - start_time) * 1000, 2)  # 转换为毫秒

            # 解析响应数据
            try:
                result.response_data = response.json() if response.text else None
            except:
                result.response_data = response.text

            result.response_info = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': result.response_data,
                'response_time_ms': result.response_time
            }

            # 验证响应
            self._validate_response(test_case, result, endpoint)

            # 判断测试是否通过
            result.passed = len(result.errors) == 0

        except requests.exceptions.Timeout:
            result.errors.append(f"请求超时（超过{self.timeout}秒）")
            result.passed = False

        except requests.exceptions.ConnectionError as e:
            result.errors.append(f"连接错误: {str(e)}")
            result.passed = False

        except Exception as e:
            result.errors.append(f"执行异常: {str(e)}")
            result.passed = False

        return result

    def execute_test_suite(
            self,
            test_cases: List[Dict],
            endpoint: Dict,
            parallel: bool = False,
            max_workers: int = 5
    ) -> List[TestResult]:
        """
        执行测试套件

        Args:
            test_cases: 测试用例列表
            endpoint: 端点信息
            parallel: 是否并行执行
            max_workers: 最大并行数

        Returns:
            测试结果列表
        """
        results = []

        if parallel:
            # 并行执行
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_case = {
                    executor.submit(self.execute_test_case, case, endpoint): case
                    for case in test_cases
                }

                for future in as_completed(future_to_case):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        case = future_to_case[future]
                        error_result = TestResult(case)
                        error_result.passed = False
                        error_result.errors.append(f"执行异常: {str(e)}")
                        results.append(error_result)
        else:
            # 串行执行
            for case in test_cases:
                result = self.execute_test_case(case, endpoint)
                results.append(result)

        return results

    def _build_url(self, test_case: Dict) -> str:
        """构建完整URL"""
        path = test_case['path']

        # 替换路径参数
        path_params = test_case.get('path_params', {})
        for param_name, param_value in path_params.items():
            path = path.replace(f"{{{param_name}}}", str(param_value))

        return f"{self.base_url}{path}"

    def _build_headers(self, test_case: Dict) -> Dict:
        """构建请求头"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # 添加测试用例指定的headers
        if test_case.get('headers'):
            headers.update(test_case['headers'])

        return headers

    def _send_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发送HTTP请求"""
        method = method.upper()

        if method == 'GET':
            return self.session.get(url, timeout=self.timeout, verify=self.verify_ssl, **kwargs)
        elif method == 'POST':
            return self.session.post(url, timeout=self.timeout, verify=self.verify_ssl, **kwargs)
        elif method == 'PUT':
            return self.session.put(url, timeout=self.timeout, verify=self.verify_ssl, **kwargs)
        elif method == 'DELETE':
            return self.session.delete(url, timeout=self.timeout, verify=self.verify_ssl, **kwargs)
        elif method == 'PATCH':
            return self.session.patch(url, timeout=self.timeout, verify=self.verify_ssl, **kwargs)
        elif method == 'OPTIONS':
            return self.session.options(url, timeout=self.timeout, verify=self.verify_ssl, **kwargs)
        elif method == 'HEAD':
            return self.session.head(url, timeout=self.timeout, verify=self.verify_ssl, **kwargs)
        else:
            raise ValueError(f"不支持的HTTP方法: {method}")

    def _validate_response(self, test_case: Dict, result: TestResult, endpoint: Dict):
        """验证响应"""
        # 1. 验证状态码
        expected_codes = test_case.get('expected_status_codes', [])
        if expected_codes and result.status_code not in expected_codes:
            result.errors.append(
                f"状态码错误: 期望{expected_codes}, 实际{result.status_code}"
            )

        # 2. 如果需要验证Schema
        if test_case.get('validate_schema') and result.response_data is not None:
            validator = ResponseValidator(endpoint)
            validation_result = validator.validate_response(
                status_code=result.status_code,
                response_data=result.response_data,
                headers=result.response_info.get('headers', {}),
                strict_schema=test_case.get('strict_schema', False)
            )

            result.errors.extend(validation_result['errors'])
            result.warnings.extend(validation_result['warnings'])

    def close(self):
        """关闭session"""
        self.session.close()

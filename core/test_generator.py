"""
测试用例生成器 - 根据API定义自动生成测试用例
"""

from typing import Dict, List, Any
from .data_generator import DataGenerator


class TestGenerator:
    """自动生成API测试用例"""

    def __init__(self, data_generator: DataGenerator = None):
        """
        初始化测试生成器

        Args:
            data_generator: 数据生成器实例
        """
        self.data_gen = data_generator or DataGenerator()

    def generate_test_cases(self, endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        为单个API端点生成全面的测试用例

        Args:
            endpoint: 端点信息字典（来自SwaggerParser.get_all_endpoints()）

        Returns:
            测试用例列表
        """
        test_cases = []

        # 1. 正向测试用例
        test_cases.extend(self._generate_positive_cases(endpoint))

        # 2. 必填参数验证用例
        test_cases.extend(self._generate_required_param_cases(endpoint))

        # 3. 参数类型验证用例
        test_cases.extend(self._generate_type_validation_cases(endpoint))

        # 4. 边界值测试用例
        test_cases.extend(self._generate_boundary_cases(endpoint))

        # 5. 认证测试用例
        if endpoint.get('security'):
            test_cases.extend(self._generate_auth_cases(endpoint))

        # 6. 响应Schema验证用例
        test_cases.extend(self._generate_schema_validation_cases(endpoint))

        # 7. 安全测试用例（可选）
        test_cases.extend(self._generate_security_cases(endpoint))

        return test_cases

    def _generate_positive_cases(self, endpoint: Dict) -> List[Dict]:
        """生成正向测试用例（P0）"""
        cases = []

        # 生成有效的请求数据
        query_params = {}
        path_params = {}
        headers = {}
        body = None

        for param in endpoint.get('parameters', []):
            param_name = param['name']
            param_in = param['in']
            schema = param['schema']

            # 生成有效数据
            value = self.data_gen.generate_from_schema(schema, valid=True)

            if param_in == 'query':
                query_params[param_name] = value
            elif param_in == 'path':
                path_params[param_name] = value
            elif param_in == 'header':
                headers[param_name] = value

        # 处理请求体
        request_body = endpoint.get('request_body')
        if request_body:
            body_schema = request_body.get('schema', {})
            body = self.data_gen.generate_from_schema(body_schema, valid=True)

        cases.append({
            'id': f"TC-{endpoint['operation_id']}-POS-001",
            'name': f"正向测试: {endpoint['summary'] or endpoint['path']}",
            'type': '正向测试',
            'priority': 'P0',
            'method': endpoint['method'],
            'path': endpoint['path'],
            'path_params': path_params,
            'query_params': query_params,
            'headers': headers,
            'body': body,
            'expected_status_codes': [200, 201, 204],
            'validate_schema': True,
            'description': f"验证{endpoint['method']} {endpoint['path']}接口在有效输入下能正常工作"
        })

        return cases

    def _generate_required_param_cases(self, endpoint: Dict) -> List[Dict]:
        """生成必填参数验证用例（P1）"""
        cases = []

        # 获取所有必填参数
        required_params = [p for p in endpoint.get('parameters', []) if p.get('required')]

        # 获取请求体中的必填字段
        request_body = endpoint.get('request_body')
        if request_body and request_body.get('required'):
            required_params.append({
                'name': 'request_body',
                'in': 'body',
                'required': True,
                'schema': request_body.get('schema', {})
            })

        # 为每个必填参数生成缺失测试用例
        for param in required_params:
            # 准备基础数据（包含所有其他参数）
            query_params = {}
            path_params = {}
            headers = {}
            body = None

            for p in endpoint.get('parameters', []):
                if p['name'] == param['name']:
                    continue  # 跳过当前要测试的必填参数

                value = self.data_gen.generate_from_schema(p['schema'], valid=True)
                if p['in'] == 'query':
                    query_params[p['name']] = value
                elif p['in'] == 'path':
                    path_params[p['name']] = value
                elif p['in'] == 'header':
                    headers[p['name']] = value

            # 如果测试的不是body，要包含有效的body
            if param['name'] != 'request_body' and request_body:
                body = self.data_gen.generate_from_schema(request_body['schema'], valid=True)

            cases.append({
                'id': f"TC-{endpoint['operation_id']}-REQ-{len(cases) + 1:03d}",
                'name': f"缺少必填参数: {param['name']}",
                'type': '反向测试',
                'priority': 'P1',
                'method': endpoint['method'],
                'path': endpoint['path'],
                'path_params': path_params,
                'query_params': query_params,
                'headers': headers,
                'body': body,
                'expected_status_codes': [400, 422],
                'validate_schema': False,
                'description': f"验证缺少必填参数'{param['name']}'时返回400/422错误"
            })

        return cases

    def _generate_type_validation_cases(self, endpoint: Dict) -> List[Dict]:
        """生成类型验证用例（P1）"""
        cases = []

        for param in endpoint.get('parameters', []):
            param_name = param['name']
            schema = param['schema']
            param_type = schema.get('type')

            # 只为有明确类型的参数生成类型错误用例
            if not param_type:
                continue

            # 准备测试数据
            query_params = {}
            path_params = {}
            headers = {}

            for p in endpoint.get('parameters', []):
                if p['name'] == param_name:
                    # 为当前参数生成错误类型的数据
                    value = self._generate_wrong_type_value(schema)
                else:
                    # 其他参数使用正确的数据
                    value = self.data_gen.generate_from_schema(p['schema'], valid=True)

                if p['in'] == 'query':
                    query_params[p['name']] = value
                elif p['in'] == 'path':
                    path_params[p['name']] = value
                elif p['in'] == 'header':
                    headers[p['name']] = value

            cases.append({
                'id': f"TC-{endpoint['operation_id']}-TYPE-{len(cases) + 1:03d}",
                'name': f"参数类型错误: {param_name}",
                'type': '反向测试',
                'priority': 'P1',
                'method': endpoint['method'],
                'path': endpoint['path'],
                'path_params': path_params,
                'query_params': query_params,
                'headers': headers,
                'body': None,
                'expected_status_codes': [400, 422],
                'validate_schema': False,
                'description': f"验证参数'{param_name}'类型错误时返回400/422"
            })

        return cases

    def _generate_boundary_cases(self, endpoint: Dict) -> List[Dict]:
        """生成边界值测试用例（P1）"""
        cases = []

        for param in endpoint.get('parameters', []):
            param_name = param['name']
            schema = param['schema']

            # 生成边界值
            boundary_values = self.data_gen.generate_boundary_values(schema)

            for boundary in boundary_values:
                query_params = {}
                path_params = {}
                headers = {}

                for p in endpoint.get('parameters', []):
                    if p['name'] == param_name:
                        value = boundary['value']
                    else:
                        value = self.data_gen.generate_from_schema(p['schema'], valid=True)

                    if p['in'] == 'query':
                        query_params[p['name']] = value
                    elif p['in'] == 'path':
                        path_params[p['name']] = value
                    elif p['in'] == 'header':
                        headers[p['name']] = value

                expected_status = [200, 201, 204] if boundary['expected_valid'] else [400, 422]

                cases.append({
                    'id': f"TC-{endpoint['operation_id']}-BND-{len(cases) + 1:03d}",
                    'name': f"边界值测试: {param_name} - {boundary['description']}",
                    'type': '边界值测试',
                    'priority': 'P1',
                    'method': endpoint['method'],
                    'path': endpoint['path'],
                    'path_params': path_params,
                    'query_params': query_params,
                    'headers': headers,
                    'body': None,
                    'expected_status_codes': expected_status,
                    'validate_schema': boundary['expected_valid'],
                    'description': f"验证参数'{param_name}'的{boundary['description']}"
                })

        return cases

    def _generate_auth_cases(self, endpoint: Dict) -> List[Dict]:
        """生成认证测试用例（P1）"""
        cases = []

        # 无认证信息
        cases.append({
            'id': f"TC-{endpoint['operation_id']}-AUTH-001",
            'name': "无认证信息",
            'type': '安全测试',
            'priority': 'P1',
            'method': endpoint['method'],
            'path': endpoint['path'],
            'path_params': {},
            'query_params': {},
            'headers': {},
            'body': None,
            'skip_auth': True,
            'expected_status_codes': [401],
            'validate_schema': False,
            'description': "验证缺少认证信息时返回401"
        })

        # 无效认证信息
        cases.append({
            'id': f"TC-{endpoint['operation_id']}-AUTH-002",
            'name': "无效认证信息",
            'type': '安全测试',
            'priority': 'P1',
            'method': endpoint['method'],
            'path': endpoint['path'],
            'path_params': {},
            'query_params': {},
            'headers': {'Authorization': 'Bearer invalid_token_12345'},
            'body': None,
            'skip_auth': True,
            'expected_status_codes': [401],
            'validate_schema': False,
            'description': "验证无效token时返回401"
        })

        return cases

    def _generate_schema_validation_cases(self, endpoint: Dict) -> List[Dict]:
        """生成响应Schema验证用例（P0）"""
        cases = []

        # 为每个成功的响应代码生成schema验证用例
        responses = endpoint.get('responses', {})
        for status_code in ['200', '201']:
            if status_code in responses:
                cases.append({
                    'id': f"TC-{endpoint['operation_id']}-SCH-{status_code}",
                    'name': f"响应Schema验证 ({status_code})",
                    'type': 'Schema验证',
                    'priority': 'P0',
                    'method': endpoint['method'],
                    'path': endpoint['path'],
                    'path_params': {},
                    'query_params': {},
                    'headers': {},
                    'body': None,
                    'expected_status_codes': [int(status_code)],
                    'validate_schema': True,
                    'strict_schema': True,
                    'description': f"验证{status_code}响应严格符合Schema定义"
                })

        return cases

    def _generate_security_cases(self, endpoint: Dict) -> List[Dict]:
        """生成安全测试用例（P2）"""
        cases = []

        # 只为接受字符串输入的参数生成安全测试
        string_params = [
            p for p in endpoint.get('parameters', [])
            if p.get('schema', {}).get('type') == 'string'
        ]

        if not string_params:
            return cases

        # 使用恶意payload测试
        malicious_payloads = self.data_gen.generate_malicious_payloads()

        for i, payload in enumerate(malicious_payloads[:3]):  # 限制数量
            # 选择一个参数进行测试
            param = string_params[0]

            query_params = {}
            if param['in'] == 'query':
                query_params[param['name']] = payload

            cases.append({
                'id': f"TC-{endpoint['operation_id']}-SEC-{i + 1:03d}",
                'name': f"安全测试: 恶意输入 #{i + 1}",
                'type': '安全测试',
                'priority': 'P2',
                'method': endpoint['method'],
                'path': endpoint['path'],
                'path_params': {},
                'query_params': query_params,
                'headers': {},
                'body': None,
                'expected_status_codes': [400, 422, 500],  # 应该被拦截或安全处理
                'validate_schema': False,
                'description': f"验证恶意输入被正确处理，不会导致安全问题"
            })

        return cases

    def _generate_wrong_type_value(self, schema: Dict) -> Any:
        """生成错误类型的值"""
        schema_type = schema.get('type')

        if schema_type == 'string':
            return 12345  # 返回数字而不是字符串
        elif schema_type in ['integer', 'number']:
            return "not_a_number"  # 返回字符串而不是数字
        elif schema_type == 'boolean':
            return "not_a_boolean"
        elif schema_type == 'array':
            return "not_an_array"
        elif schema_type == 'object':
            return "not_an_object"
        else:
            return None

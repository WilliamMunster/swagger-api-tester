"""
响应验证器 - 验证API响应是否符合Swagger定义
"""

from typing import Dict, List, Any, Optional
import jsonschema
from jsonschema import validate, ValidationError


class ResponseValidator:
    """API响应验证器"""

    def __init__(self, endpoint: Dict):
        """
        初始化验证器

        Args:
            endpoint: 端点信息（来自SwaggerParser）
        """
        self.endpoint = endpoint
        self.responses = endpoint.get('responses', {})

    def validate_response(
            self,
            status_code: int,
            response_data: Any,
            headers: Dict = None,
            strict_schema: bool = False
    ) -> Dict[str, Any]:
        """
        验证API响应

        Args:
            status_code: HTTP状态码
            response_data: 响应数据
            headers: 响应头
            strict_schema: 是否严格验证schema

        Returns:
            验证结果字典，包含:
            - valid: bool - 是否验证通过
            - errors: List[str] - 错误列表
            - warnings: List[str] - 警告列表
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }

        # 1. 验证状态码是否在定义中
        status_code_str = str(status_code)
        if status_code_str not in self.responses and 'default' not in self.responses:
            result['warnings'].append(
                f"状态码{status_code}未在Swagger定义中声明"
            )

        # 2. 获取响应定义
        response_def = self.responses.get(status_code_str) or self.responses.get('default', {})

        # 3. 验证响应Schema
        if strict_schema and response_data is not None:
            schema_errors = self._validate_schema(response_data, response_def)
            if schema_errors:
                result['valid'] = False
                result['errors'].extend(schema_errors)

        # 4. 验证必填字段
        if isinstance(response_data, dict):
            required_errors = self._validate_required_fields(response_data, response_def)
            if required_errors:
                result['valid'] = False
                result['errors'].extend(required_errors)

        # 5. 验证数据类型
        type_errors = self._validate_data_types(response_data, response_def)
        if type_errors:
            result['valid'] = False
            result['errors'].extend(type_errors)

        # 6. 验证响应头（如果定义了）
        if headers and 'headers' in response_def:
            header_warnings = self._validate_headers(headers, response_def['headers'])
            result['warnings'].extend(header_warnings)

        return result

    def _validate_schema(self, data: Any, response_def: Dict) -> List[str]:
        """使用jsonschema验证响应数据"""
        errors = []

        # 获取schema定义
        schema = self._get_response_schema(response_def)

        if not schema:
            return errors

        try:
            # 使用jsonschema进行验证
            validate(instance=data, schema=schema)
        except ValidationError as e:
            errors.append(f"Schema验证失败: {e.message} (路径: {'.'.join(str(p) for p in e.path)})")
        except Exception as e:
            errors.append(f"Schema验证异常: {str(e)}")

        return errors

    def _get_response_schema(self, response_def: Dict) -> Optional[Dict]:
        """获取响应的schema定义"""
        # OpenAPI 3.0+: schema在content中
        if 'content' in response_def:
            content = response_def['content']
            # 优先查找application/json
            for content_type in ['application/json', 'application/xml', '*/*']:
                if content_type in content:
                    return content[content_type].get('schema')

        # Swagger 2.0: schema直接在响应定义中
        if 'schema' in response_def:
            return response_def['schema']

        return None

    def _validate_required_fields(self, data: Dict, response_def: Dict) -> List[str]:
        """验证必填字段"""
        errors = []

        schema = self._get_response_schema(response_def)
        if not schema or not isinstance(data, dict):
            return errors

        required_fields = schema.get('required', [])

        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必填字段: {field}")

        return errors

    def _validate_data_types(self, data: Any, response_def: Dict) -> List[str]:
        """验证数据类型"""
        errors = []

        schema = self._get_response_schema(response_def)
        if not schema:
            return errors

        # 验证顶层类型
        expected_type = schema.get('type')
        actual_type = self._get_json_type(data)

        if expected_type and expected_type != actual_type:
            errors.append(
                f"响应类型错误: 期望{expected_type}, 实际{actual_type}"
            )

        # 如果是对象，验证属性类型
        if isinstance(data, dict) and 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if prop_name in data:
                    prop_value = data[prop_name]
                    expected_prop_type = prop_schema.get('type')
                    actual_prop_type = self._get_json_type(prop_value)

                    if expected_prop_type and expected_prop_type != actual_prop_type:
                        errors.append(
                            f"字段'{prop_name}'类型错误: 期望{expected_prop_type}, 实际{actual_prop_type}"
                        )

        return errors

    def _validate_headers(self, headers: Dict, header_defs: Dict) -> List[str]:
        """验证响应头"""
        warnings = []

        for header_name, header_def in header_defs.items():
            # 响应头名称不区分大小写
            header_value = None
            for h_name, h_value in headers.items():
                if h_name.lower() == header_name.lower():
                    header_value = h_value
                    break

            if header_def.get('required') and header_value is None:
                warnings.append(f"缺少必需的响应头: {header_name}")

        return warnings

    def _get_json_type(self, value: Any) -> str:
        """获取Python值对应的JSON类型"""
        if value is None:
            return 'null'
        elif isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'number'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, list):
            return 'array'
        elif isinstance(value, dict):
            return 'object'
        else:
            return 'unknown'

    def is_success_status(self, status_code: int) -> bool:
        """判断状态码是否表示成功"""
        return 200 <= status_code < 300

    def get_expected_status_codes(self) -> List[int]:
        """获取所有定义的状态码"""
        codes = []
        for code_str in self.responses.keys():
            if code_str == 'default':
                continue
            try:
                codes.append(int(code_str))
            except ValueError:
                pass
        return codes

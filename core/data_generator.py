"""
测试数据生成器 - 根据Schema自动生成测试数据
"""

import random
import string
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


class DataGenerator:
    """根据OpenAPI/Swagger schema生成测试数据"""

    def __init__(self, seed: Optional[int] = None):
        """
        初始化数据生成器

        Args:
            seed: 随机种子，用于生成可复现的测试数据
        """
        if seed:
            random.seed(seed)

    def generate_from_schema(self, schema: Dict, valid: bool = True) -> Any:
        """
        根据schema生成数据

        Args:
            schema: OpenAPI/Swagger schema定义
            valid: True生成有效数据，False生成无效数据

        Returns:
            生成的测试数据
        """
        if not schema or not isinstance(schema, dict):
            return None

        schema_type = schema.get('type')

        if schema_type == 'object':
            return self._generate_object(schema, valid)
        elif schema_type == 'array':
            return self._generate_array(schema, valid)
        elif schema_type == 'string':
            return self._generate_string(schema, valid)
        elif schema_type == 'integer':
            return self._generate_integer(schema, valid)
        elif schema_type == 'number':
            return self._generate_number(schema, valid)
        elif schema_type == 'boolean':
            return self._generate_boolean(schema, valid)
        else:
            # 如果没有指定type，尝试根据其他属性推断
            if 'properties' in schema:
                return self._generate_object(schema, valid)
            if 'items' in schema:
                return self._generate_array(schema, valid)
            return None

    def _generate_object(self, schema: Dict, valid: bool) -> Dict:
        """生成对象"""
        obj = {}
        properties = schema.get('properties', {})
        required = schema.get('required', [])

        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required

            if valid:
                # 生成有效数据：必填字段必须生成
                if is_required or random.random() > 0.3:  # 70%概率生成非必填字段
                    obj[prop_name] = self.generate_from_schema(prop_schema, valid=True)
            else:
                # 生成无效数据：随机省略必填字段或生成错误类型
                if is_required and random.random() > 0.5:
                    continue  # 省略必填字段
                else:
                    obj[prop_name] = self.generate_from_schema(prop_schema, valid=False)

        return obj

    def _generate_array(self, schema: Dict, valid: bool) -> List:
        """生成数组"""
        items_schema = schema.get('items', {})
        min_items = schema.get('minItems', 0)
        max_items = schema.get('maxItems', 10)

        if valid:
            # 生成有效数组
            count = random.randint(max(min_items, 1), min(max_items, 5))
        else:
            # 生成无效数组：超出范围
            if random.random() > 0.5 and min_items > 0:
                count = min_items - 1  # 少于最小值
            else:
                count = max_items + 1  # 超过最大值

        return [self.generate_from_schema(items_schema, valid) for _ in range(max(0, count))]

    def _generate_string(self, schema: Dict, valid: bool) -> str:
        """生成字符串"""
        format_type = schema.get('format')
        enum_values = schema.get('enum')
        min_length = schema.get('minLength', 1)
        max_length = schema.get('maxLength', 50)
        pattern = schema.get('pattern')

        # 如果有枚举值
        if enum_values:
            if valid:
                return random.choice(enum_values)
            else:
                return "invalid_enum_value_12345"

        # 根据format生成特定格式的字符串
        if valid:
            if format_type == 'email':
                return f"test{random.randint(1, 1000)}@example.com"
            elif format_type == 'uri' or format_type == 'url':
                return f"https://example.com/path{random.randint(1, 100)}"
            elif format_type == 'date':
                date = datetime.now() - timedelta(days=random.randint(0, 365))
                return date.strftime('%Y-%m-%d')
            elif format_type == 'date-time':
                dt = datetime.now() - timedelta(days=random.randint(0, 365))
                return dt.isoformat()
            elif format_type == 'uuid':
                import uuid
                return str(uuid.uuid4())
            elif format_type == 'password':
                return self._random_string(max(min_length, 8), 'password')
            else:
                # 普通字符串
                length = random.randint(min_length, min(max_length, 20))
                return self._random_string(length)
        else:
            # 生成无效字符串
            if random.random() > 0.5 and max_length > 0:
                # 超长字符串
                return self._random_string(max_length + 10)
            elif format_type == 'email':
                return "not-an-email"
            elif format_type == 'uri':
                return "not a uri"
            else:
                # 太短的字符串
                return self._random_string(max(0, min_length - 1))

    def _generate_integer(self, schema: Dict, valid: bool) -> int:
        """生成整数"""
        minimum = schema.get('minimum', 0)
        maximum = schema.get('maximum', 1000)
        enum_values = schema.get('enum')

        if enum_values:
            if valid:
                return random.choice(enum_values)
            else:
                return maximum + 999  # 超出枚举范围

        if valid:
            return random.randint(minimum, min(maximum, minimum + 100))
        else:
            # 生成无效整数：超出范围
            if random.random() > 0.5:
                return minimum - 1
            else:
                return maximum + 1

    def _generate_number(self, schema: Dict, valid: bool) -> float:
        """生成浮点数"""
        minimum = schema.get('minimum', 0.0)
        maximum = schema.get('maximum', 1000.0)

        if valid:
            return round(random.uniform(minimum, min(maximum, minimum + 100)), 2)
        else:
            # 生成无效数字：超出范围
            if random.random() > 0.5:
                return minimum - 1.0
            else:
                return maximum + 1.0

    def _generate_boolean(self, schema: Dict, valid: bool) -> bool:
        """生成布尔值"""
        return random.choice([True, False])

    def _random_string(self, length: int, type: str = 'alphanumeric') -> str:
        """
        生成随机字符串

        Args:
            length: 长度
            type: 类型 (alphanumeric, alpha, numeric, password)

        Returns:
            随机字符串
        """
        if length <= 0:
            return ""

        if type == 'alpha':
            chars = string.ascii_letters
        elif type == 'numeric':
            chars = string.digits
        elif type == 'password':
            # 密码包含大小写字母、数字和特殊字符
            chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        else:  # alphanumeric
            chars = string.ascii_letters + string.digits

        return ''.join(random.choice(chars) for _ in range(length))

    def generate_boundary_values(self, schema: Dict) -> List[Dict[str, Any]]:
        """
        生成边界值测试数据

        Args:
            schema: Schema定义

        Returns:
            边界值测试用例列表，每个包含 'description' 和 'value'
        """
        boundary_cases = []
        schema_type = schema.get('type')

        if schema_type == 'string':
            min_length = schema.get('minLength', 0)
            max_length = schema.get('maxLength')

            # 空字符串
            boundary_cases.append({
                'description': '空字符串',
                'value': '',
                'expected_valid': min_length == 0
            })

            # 最小长度
            if min_length > 0:
                boundary_cases.append({
                    'description': f'最小长度({min_length})',
                    'value': self._random_string(min_length),
                    'expected_valid': True
                })
                boundary_cases.append({
                    'description': f'小于最小长度({min_length - 1})',
                    'value': self._random_string(max(0, min_length - 1)),
                    'expected_valid': False
                })

            # 最大长度
            if max_length:
                boundary_cases.append({
                    'description': f'最大长度({max_length})',
                    'value': self._random_string(max_length),
                    'expected_valid': True
                })
                boundary_cases.append({
                    'description': f'超过最大长度({max_length + 1})',
                    'value': self._random_string(max_length + 1),
                    'expected_valid': False
                })

        elif schema_type in ['integer', 'number']:
            minimum = schema.get('minimum')
            maximum = schema.get('maximum')

            if minimum is not None:
                boundary_cases.extend([
                    {
                        'description': f'最小值({minimum})',
                        'value': minimum,
                        'expected_valid': True
                    },
                    {
                        'description': f'小于最小值({minimum - 1})',
                        'value': minimum - 1,
                        'expected_valid': False
                    }
                ])

            if maximum is not None:
                boundary_cases.extend([
                    {
                        'description': f'最大值({maximum})',
                        'value': maximum,
                        'expected_valid': True
                    },
                    {
                        'description': f'超过最大值({maximum + 1})',
                        'value': maximum + 1,
                        'expected_valid': False
                    }
                ])

        elif schema_type == 'array':
            min_items = schema.get('minItems', 0)
            max_items = schema.get('maxItems')
            items_schema = schema.get('items', {})

            # 空数组
            boundary_cases.append({
                'description': '空数组',
                'value': [],
                'expected_valid': min_items == 0
            })

            # 最小元素数
            if min_items > 0:
                boundary_cases.append({
                    'description': f'最小元素数({min_items})',
                    'value': [self.generate_from_schema(items_schema, True) for _ in range(min_items)],
                    'expected_valid': True
                })

            # 最大元素数
            if max_items:
                boundary_cases.append({
                    'description': f'最大元素数({max_items})',
                    'value': [self.generate_from_schema(items_schema, True) for _ in range(max_items)],
                    'expected_valid': True
                })
                boundary_cases.append({
                    'description': f'超过最大元素数({max_items + 1})',
                    'value': [self.generate_from_schema(items_schema, True) for _ in range(max_items + 1)],
                    'expected_valid': False
                })

        return boundary_cases

    def generate_malicious_payloads(self) -> List[str]:
        """
        生成常见的恶意payload用于安全测试

        Returns:
            恶意payload列表
        """
        return [
            # SQL注入
            "' OR '1'='1",
            "1; DROP TABLE users--",
            "admin'--",

            # XSS
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",

            # 路径遍历
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",

            # 命令注入
            "; ls -la",
            "| cat /etc/passwd",
            "`whoami`",

            # 特殊字符
            "null\x00byte",
            "超长" + "A" * 10000,
        ]

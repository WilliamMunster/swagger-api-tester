"""
条件判断器 - 求值条件表达式并选择执行分支
"""

import re
import operator
from typing import Any, Dict


class ConditionEvaluator:
    """条件表达式求值器"""

    # 运算符映射
    OPERATORS = {
        '==': operator.eq,
        '!=': operator.ne,
        '>': operator.gt,
        '>=': operator.ge,
        '<': operator.lt,
        '<=': operator.le,
        'in': lambda a, b: a in b,
        'not in': lambda a, b: a not in b,
    }

    def __init__(self, context_manager):
        """
        初始化条件判断器

        Args:
            context_manager: 上下文管理器实例
        """
        self.context = context_manager

    def evaluate(self, expression: str, response: Any = None) -> bool:
        """
        求值条件表达式

        支持的表达式:
        - 比较: age > 18, status == 'active'
        - 逻辑: age > 18 and balance >= 100
        - 包含: 'admin' in roles
        - 响应访问: response.data.balance >= 100

        Args:
            expression: 条件表达式
            response: 当前步骤的响应数据（可选）

        Returns:
            bool: 表达式结果
        """
        # 解析变量引用
        resolved_expr = self._resolve_variables(expression, response)

        # 求值表达式
        return self._evaluate_expression(resolved_expr)

    def _resolve_variables(self, expr: str, response: Any) -> str:
        """
        解析表达式中的变量引用

        将 ${var} 替换为实际值
        将 response.xxx 替换为实际值
        """
        # 1. 处理 response.xxx 引用
        if 'response.' in expr:
            expr = self._resolve_response_refs(expr, response)

        # 2. 处理 ${var} 引用
        expr = self.context.resolve(expr)

        return expr

    def _resolve_response_refs(self, expr: str, response: Any) -> str:
        """
        解析response.xxx引用

        例如: response.data.balance >= 100
        """
        if not response:
            return expr

        pattern = r'response\.([a-zA-Z0-9_.[\]]+)'

        def replacer(match):
            path = match.group(1)
            value = self._get_nested_value(response, path)
            # 返回可以被eval的字符串表示
            if isinstance(value, str):
                return f"'{value}'"
            else:
                return str(value)

        return re.sub(pattern, replacer, expr)

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """
        获取嵌套属性值

        支持: data.user.id, data.items[0].name
        """
        if not path:
            return data

        parts = path.replace('[', '.').replace(']', '').split('.')

        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    index = int(part)
                    current = current[index]
                except (ValueError, IndexError):
                    return None
            else:
                return None

            if current is None:
                return None

        return current

    def _evaluate_expression(self, expr: str) -> bool:
        """
        求值解析后的表达式

        使用Python的eval（有安全限制）
        """
        # 处理逻辑运算符
        expr = expr.replace(' and ', ' and_ ').replace(' or ', ' or_ ').replace(' not ', ' not_ ')

        try:
            # 构建安全的求值环境
            safe_dict = {
                '__builtins__': {},
                'True': True,
                'False': False,
                'None': None,
                'and_': lambda a, b: a and b,
                'or_': lambda a, b: a or b,
                'not_': lambda a: not a,
                'len': len,
            }

            # 简单的表达式求值
            result = eval(expr, safe_dict)
            return bool(result)
        except Exception as e:
            # 如果eval失败，尝试手动解析简单表达式
            return self._manual_evaluate(expr)

    def _manual_evaluate(self, expr: str) -> bool:
        """
        手动解析简单表达式

        处理形如: a == b, a > b, a in b 的表达式
        """
        expr = expr.strip()

        # 尝试每个运算符
        for op_str, op_func in self.OPERATORS.items():
            if op_str in expr:
                parts = expr.split(op_str, 1)
                if len(parts) == 2:
                    left = self._parse_value(parts[0].strip())
                    right = self._parse_value(parts[1].strip())
                    try:
                        return op_func(left, right)
                    except:
                        return False

        # 单个布尔值
        if expr.lower() in ['true', '1']:
            return True
        elif expr.lower() in ['false', '0', 'none', 'null']:
            return False

        return False

    def _parse_value(self, value_str: str) -> Any:
        """
        解析值字符串为Python类型
        """
        value_str = value_str.strip()

        # None/null
        if value_str.lower() in ['none', 'null']:
            return None

        # 布尔值
        if value_str.lower() == 'true':
            return True
        elif value_str.lower() == 'false':
            return False

        # 字符串（带引号）
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]

        # 数字
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # 列表
        if value_str.startswith('[') and value_str.endswith(']'):
            try:
                return eval(value_str)
            except:
                pass

        # 默认返回字符串
        return value_str


# 测试代码
if __name__ == '__main__':
    from .context_manager import ContextManager

    # 创建上下文
    context = ContextManager()
    context.set('age', 25)
    context.set('balance', 150)
    context.set('status', 'active')
    context.set('roles', ['admin', 'user'])

    # 创建判断器
    evaluator = ConditionEvaluator(context)

    # 测试用例
    test_cases = [
        ('age > 18', True),
        ('balance >= 100', True),
        ("status == 'active'", True),
        ("'admin' in roles", True),
        ('age > 18 and balance >= 100', True),
        ('age < 18 or balance < 100', False),
    ]

    print("条件判断测试:")
    for expr, expected in test_cases:
        result = evaluator.evaluate(expr)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {expr} => {result} (期望: {expected})")

    # 测试response引用
    response_data = {
        'data': {
            'balance': 200,
            'status': 'active'
        }
    }

    result = evaluator.evaluate('response.data.balance >= 100', response_data)
    print(f"\n  response.data.balance >= 100 => {result}")

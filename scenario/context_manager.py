"""
上下文管理器 - 管理场景执行过程中的变量和数据
"""

import re
import time
import uuid
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime


class ContextManager:
    """
    管理测试场景中的变量上下文

    支持三个作用域：
    - global: 全局变量（整个测试会话）
    - scenario: 场景变量（当前场景）
    - step: 步骤变量（当前步骤）
    """

    def __init__(self):
        """初始化上下文管理器"""
        self.global_vars: Dict[str, Any] = {}
        self.scenario_vars: Dict[str, Any] = {}
        self.step_vars: Dict[str, Any] = {}

        # 注册内置函数
        self._builtin_functions = {
            'timestamp': self._func_timestamp,
            'uuid': self._func_uuid,
            'random_string': self._func_random_string,
            'random_int': self._func_random_int,
            'date': self._func_date,
            'md5': self._func_md5,
        }

    def set(self, name: str, value: Any, scope: str = 'scenario'):
        """
        设置变量

        Args:
            name: 变量名
            value: 变量值
            scope: 作用域 (global/scenario/step)
        """
        if scope == 'global':
            self.global_vars[name] = value
        elif scope == 'scenario':
            self.scenario_vars[name] = value
        elif scope == 'step':
            self.step_vars[name] = value
        else:
            raise ValueError(f"Invalid scope: {scope}")

    def get(self, name: str, default: Any = None) -> Any:
        """
        获取变量（自动搜索作用域）

        搜索顺序: step -> scenario -> global

        Args:
            name: 变量名
            default: 默认值

        Returns:
            变量值
        """
        # 按作用域顺序查找
        if name in self.step_vars:
            return self.step_vars[name]
        elif name in self.scenario_vars:
            return self.scenario_vars[name]
        elif name in self.global_vars:
            return self.global_vars[name]
        else:
            return default

    def clear_step(self):
        """清除步骤变量"""
        self.step_vars = {}

    def clear_scenario(self):
        """清除场景变量"""
        self.scenario_vars = {}
        self.step_vars = {}

    def resolve(self, template: Any) -> Any:
        """
        解析模板中的变量引用

        支持:
        - ${var_name}: 变量引用
        - ${func()}: 函数调用
        - 嵌套结构（dict, list）

        Args:
            template: 模板（字符串、字典、列表等）

        Returns:
            解析后的值
        """
        if isinstance(template, str):
            return self._resolve_string(template)
        elif isinstance(template, dict):
            return {k: self.resolve(v) for k, v in template.items()}
        elif isinstance(template, list):
            return [self.resolve(item) for item in template]
        else:
            return template

    def _resolve_string(self, text: str) -> Any:
        """
        解析字符串中的变量引用

        Examples:
            "${user_id}" -> "12345"
            "Hello ${username}" -> "Hello test_user"
            "${timestamp()}" -> "1642597200"
        """
        # 如果整个字符串都是变量引用，直接返回变量值（保持原类型）
        if text.startswith('${') and text.endswith('}') and text.count('${') == 1:
            var_expr = text[2:-1]
            return self._evaluate_expression(var_expr)

        # 否则，替换所有变量引用为字符串
        pattern = r'\$\{([^}]+)\}'

        def replacer(match):
            expr = match.group(1)
            value = self._evaluate_expression(expr)
            return str(value) if value is not None else ''

        return re.sub(pattern, replacer, text)

    def _evaluate_expression(self, expr: str) -> Any:
        """
        求值表达式

        支持:
        - 变量引用: user_id
        - 函数调用: timestamp()
        - 带参数的函数: random_string(10)
        """
        expr = expr.strip()

        # 检查是否是函数调用
        if '(' in expr and expr.endswith(')'):
            func_name = expr[:expr.index('(')]
            args_str = expr[expr.index('(') + 1:-1].strip()

            # 解析参数
            args = []
            if args_str:
                # 简单的参数解析（支持字符串、数字）
                for arg in args_str.split(','):
                    arg = arg.strip()
                    if arg.startswith("'") and arg.endswith("'"):
                        args.append(arg[1:-1])  # 字符串
                    elif arg.isdigit():
                        args.append(int(arg))  # 整数
                    else:
                        args.append(arg)  # 其他

            # 调用函数
            if func_name in self._builtin_functions:
                return self._builtin_functions[func_name](*args)
            else:
                raise ValueError(f"Unknown function: {func_name}")

        # 普通变量引用
        return self.get(expr)

    # ========== 内置函数 ==========

    def _func_timestamp(self) -> int:
        """返回当前时间戳（秒）"""
        return int(time.time())

    def _func_uuid(self) -> str:
        """返回UUID字符串"""
        return str(uuid.uuid4())

    def _func_random_string(self, length: int = 10) -> str:
        """
        返回随机字符串

        Args:
            length: 长度
        """
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _func_random_int(self, min_val: int = 0, max_val: int = 100) -> int:
        """
        返回随机整数

        Args:
            min_val: 最小值
            max_val: 最大值
        """
        import random
        return random.randint(min_val, max_val)

    def _func_date(self, format_str: str = '%Y-%m-%d') -> str:
        """
        返回格式化的当前日期

        Args:
            format_str: 日期格式
        """
        return datetime.now().strftime(format_str)

    def _func_md5(self, text: str) -> str:
        """
        返回MD5哈希

        Args:
            text: 输入文本
        """
        return hashlib.md5(text.encode()).hexdigest()

    def to_dict(self) -> Dict:
        """导出所有变量为字典"""
        return {
            'global': self.global_vars.copy(),
            'scenario': self.scenario_vars.copy(),
            'step': self.step_vars.copy()
        }

    def __repr__(self) -> str:
        return f"ContextManager(global={len(self.global_vars)}, scenario={len(self.scenario_vars)}, step={len(self.step_vars)})"

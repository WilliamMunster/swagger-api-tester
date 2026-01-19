"""
变量提取器 - 从API响应中提取数据
"""

import re
import json
from typing import Any, Dict, List, Optional


class VariableExtractor:
    """从API响应中提取变量"""

    def extract(
            self,
            response: Any,
            extract_config: List[Dict],
            headers: Dict = None
    ) -> Dict[str, Any]:
        """
        根据配置提取变量

        Args:
            response: 响应数据（通常是dict）
            extract_config: 提取配置列表
            headers: 响应头

        Returns:
            提取的变量字典 {name: value}

        Example extract_config:
            [
                {"name": "user_id", "path": "$.data.id"},
                {"name": "token", "header": "Authorization"},
                {"name": "order_id", "regex": r"order_(\\d+)", "group": 1}
            ]
        """
        extracted = {}

        for config in extract_config:
            name = config.get('name')
            if not name:
                continue

            value = None

            # JSONPath提取
            if 'path' in config:
                value = self.extract_jsonpath(response, config['path'])

            # Header提取
            elif 'header' in config and headers:
                value = self.extract_header(headers, config['header'])

            # Cookie提取
            elif 'cookie' in config and headers:
                value = self.extract_cookie(headers, config['cookie'])

            # 正则提取
            elif 'regex' in config:
                # 将响应转为字符串
                text = json.dumps(response) if isinstance(response, (dict, list)) else str(response)
                value = self.extract_regex(
                    text,
                    config['regex'],
                    config.get('group', 0)
                )

            if value is not None:
                extracted[name] = value

        return extracted

    def extract_jsonpath(self, data: Any, path: str) -> Any:
        """
        使用JSONPath提取数据

        支持的语法：
        - $.data.id
        - $.data.items[0].name
        - $.data.items[*].id  (提取所有id)

        Args:
            data: 数据（dict或list）
            path: JSONPath表达式

        Returns:
            提取的值
        """
        if not isinstance(data, (dict, list)):
            return None

        # 移除开头的$
        if path.startswith('$.'):
            path = path[2:]
        elif path.startswith('$'):
            path = path[1:]

        if not path:
            return data

        try:
            return self._traverse_path(data, path)
        except (KeyError, IndexError, TypeError):
            return None

    def _traverse_path(self, data: Any, path: str) -> Any:
        """递归遍历路径"""
        if not path:
            return data

        # 分离第一个路径段
        if '.' in path:
            first, rest = path.split('.', 1)
        else:
            first, rest = path, ''

        # 处理数组索引 items[0] 或 items[*]
        if '[' in first:
            key = first[:first.index('[')]
            index_part = first[first.index('[') + 1:first.index(']')]

            # 获取数组
            if isinstance(data, dict):
                arr = data.get(key)
            else:
                arr = data

            if not isinstance(arr, list):
                return None

            # 处理通配符 [*]
            if index_part == '*':
                if not rest:
                    return arr
                else:
                    # 对每个元素继续遍历
                    return [self._traverse_path(item, rest) for item in arr]
            else:
                # 特定索引
                try:
                    index = int(index_part)
                    item = arr[index]
                    return self._traverse_path(item, rest) if rest else item
                except (ValueError, IndexError):
                    return None

        # 普通键访问
        else:
            if isinstance(data, dict):
                value = data.get(first)
                return self._traverse_path(value, rest) if rest else value
            else:
                return None

    def extract_regex(self, text: str, pattern: str, group: int = 0) -> Optional[str]:
        """
        使用正则表达式提取

        Args:
            text: 源文本
            pattern: 正则表达式
            group: 捕获组索引

        Returns:
            匹配的文本
        """
        match = re.search(pattern, text)
        if match:
            return match.group(group)
        return None

    def extract_header(self, headers: Dict, name: str) -> Optional[str]:
        """
        从响应头中提取

        Args:
            headers: 响应头字典
            name: 头名称（不区分大小写）

        Returns:
            头值
        """
        # HTTP头名称不区分大小写
        for key, value in headers.items():
            if key.lower() == name.lower():
                return value
        return None

    def extract_cookie(self, headers: Dict, name: str) -> Optional[str]:
        """
        从Set-Cookie头中提取特定cookie

        Args:
            headers: 响应头字典
            name: Cookie名称

        Returns:
            Cookie值
        """
        set_cookie = self.extract_header(headers, 'Set-Cookie')
        if not set_cookie:
            return None

        # 解析Set-Cookie头
        # 格式: name=value; path=/; domain=...
        pattern = rf'{name}=([^;]+)'
        match = re.search(pattern, set_cookie)
        if match:
            return match.group(1)
        return None


# 测试代码
if __name__ == '__main__':
    extractor = VariableExtractor()

    # 测试数据
    response_data = {
        'code': 200,
        'message': 'success',
        'data': {
            'user': {
                'id': 12345,
                'username': 'testuser',
                'email': 'test@example.com'
            },
            'items': [
                {'id': 1, 'name': 'item1'},
                {'id': 2, 'name': 'item2'},
                {'id': 3, 'name': 'item3'}
            ]
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'X-Request-Id': 'req-12345',
        'Set-Cookie': 'session_id=abc123; path=/; HttpOnly'
    }

    # 提取配置
    extract_config = [
        {'name': 'user_id', 'path': '$.data.user.id'},
        {'name': 'username', 'path': '$.data.user.username'},
        {'name': 'first_item_name', 'path': '$.data.items[0].name'},
        {'name': 'all_item_ids', 'path': '$.data.items[*].id'},
        {'name': 'request_id', 'header': 'X-Request-Id'},
        {'name': 'session_id', 'cookie': 'session_id'},
    ]

    # 执行提取
    result = extractor.extract(response_data, extract_config, headers)
    print("提取结果:")
    for name, value in result.items():
        print(f"  {name}: {value}")

"""
Swagger/OpenAPI解析器 - 兼容Swagger 2.0和OpenAPI 3.0+
"""

import json
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path


class SwaggerParser:
    """统一的Swagger/OpenAPI解析器"""

    def __init__(self, spec_path: str):
        """
        初始化解析器

        Args:
            spec_path: Swagger/OpenAPI文件路径（支持JSON和YAML）
        """
        self.spec_path = Path(spec_path)
        self.spec = self._load_spec()
        self.version = self._detect_version()
        self.base_url = self._get_base_url()

    def _load_spec(self) -> Dict:
        """加载并解析Swagger文件"""
        with open(self.spec_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 根据文件扩展名选择解析方式
        if self.spec_path.suffix.lower() in ['.yaml', '.yml']:
            return yaml.safe_load(content)
        elif self.spec_path.suffix.lower() == '.json':
            return json.loads(content)
        else:
            # 尝试YAML，失败则尝试JSON
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError:
                return json.loads(content)

    def _detect_version(self) -> str:
        """检测Swagger/OpenAPI版本"""
        if 'openapi' in self.spec:
            version = self.spec['openapi']
            return f"OpenAPI {version}"
        elif 'swagger' in self.spec:
            version = self.spec['swagger']
            return f"Swagger {version}"
        else:
            raise ValueError("无法识别的API规范格式，请确保文件包含'openapi'或'swagger'字段")

    def _get_base_url(self) -> str:
        """获取API基础URL"""
        # OpenAPI 3.0+
        if 'servers' in self.spec and self.spec['servers']:
            return self.spec['servers'][0]['url']

        # Swagger 2.0
        if 'host' in self.spec:
            scheme = self.spec.get('schemes', ['http'])[0]
            host = self.spec['host']
            base_path = self.spec.get('basePath', '')
            return f"{scheme}://{host}{base_path}"

        return ""

    def get_all_endpoints(self) -> List[Dict[str, Any]]:
        """
        获取所有API端点信息

        Returns:
            包含所有端点信息的列表，每个端点包含：
            - path: 路径
            - method: HTTP方法
            - operation_id: 操作ID
            - summary: 摘要
            - description: 描述
            - parameters: 参数列表
            - request_body: 请求体（OpenAPI 3.0+）
            - responses: 响应定义
            - security: 安全要求
            - tags: 标签
        """
        endpoints = []
        paths = self.spec.get('paths', {})

        for path, path_item in paths.items():
            # HTTP方法列表
            methods = ['get', 'post', 'put', 'delete', 'patch', 'options', 'head', 'trace']

            for method in methods:
                if method in path_item:
                    operation = path_item[method]
                    endpoint_info = {
                        'path': path,
                        'method': method.upper(),
                        'operation_id': operation.get('operationId', f"{method}_{path.replace('/', '_')}"),
                        'summary': operation.get('summary', ''),
                        'description': operation.get('description', ''),
                        'parameters': self._parse_parameters(operation, path_item),
                        'request_body': self._parse_request_body(operation),
                        'responses': operation.get('responses', {}),
                        'security': operation.get('security', self.spec.get('security', [])),
                        'tags': operation.get('tags', []),
                        'deprecated': operation.get('deprecated', False)
                    }
                    endpoints.append(endpoint_info)

        return endpoints

    def _parse_parameters(self, operation: Dict, path_item: Dict) -> List[Dict]:
        """
        解析参数（兼容Swagger 2.0和OpenAPI 3.0+）

        Args:
            operation: 操作对象
            path_item: 路径项对象

        Returns:
            参数列表
        """
        parameters = []

        # 合并path级别和operation级别的参数
        path_params = path_item.get('parameters', [])
        op_params = operation.get('parameters', [])

        all_params = path_params + op_params

        for param in all_params:
            # 处理$ref引用（简化处理）
            if '$ref' in param:
                # TODO: 实现$ref解析
                continue

            # OpenAPI 3.0+: schema在param.schema中
            # Swagger 2.0: type直接在param中
            schema = param.get('schema', {})
            if not schema:
                # Swagger 2.0格式
                schema = {
                    'type': param.get('type'),
                    'format': param.get('format'),
                    'enum': param.get('enum'),
                    'minimum': param.get('minimum'),
                    'maximum': param.get('maximum'),
                    'minLength': param.get('minLength'),
                    'maxLength': param.get('maxLength'),
                }

            param_info = {
                'name': param.get('name'),
                'in': param.get('in'),  # query, header, path, cookie
                'required': param.get('required', False),
                'description': param.get('description', ''),
                'schema': schema,
                'example': param.get('example'),
            }
            parameters.append(param_info)

        return parameters

    def _parse_request_body(self, operation: Dict) -> Optional[Dict]:
        """
        解析请求体（OpenAPI 3.0+）
        对于Swagger 2.0，body参数在parameters中

        Args:
            operation: 操作对象

        Returns:
            请求体信息或None
        """
        # OpenAPI 3.0+
        if 'requestBody' in operation:
            request_body = operation['requestBody']
            content = request_body.get('content', {})

            # 优先使用application/json
            for content_type in ['application/json', 'application/xml', 'multipart/form-data', '*/*']:
                if content_type in content:
                    return {
                        'required': request_body.get('required', False),
                        'content_type': content_type,
                        'schema': content[content_type].get('schema', {}),
                        'example': content[content_type].get('example'),
                    }

        # Swagger 2.0: 检查parameters中的body参数
        for param in operation.get('parameters', []):
            if param.get('in') == 'body':
                return {
                    'required': param.get('required', False),
                    'content_type': 'application/json',
                    'schema': param.get('schema', {}),
                }

        return None

    def get_security_definitions(self) -> Dict:
        """获取安全定义"""
        # OpenAPI 3.0+
        if 'components' in self.spec and 'securitySchemes' in self.spec['components']:
            return self.spec['components']['securitySchemes']

        # Swagger 2.0
        if 'securityDefinitions' in self.spec:
            return self.spec['securityDefinitions']

        return {}

    def get_api_info(self) -> Dict[str, str]:
        """获取API基本信息"""
        info = self.spec.get('info', {})
        return {
            'title': info.get('title', 'Unknown API'),
            'version': info.get('version', '1.0.0'),
            'description': info.get('description', ''),
            'spec_version': self.version,
            'base_url': self.base_url,
            'contact': info.get('contact', {}),
        }

    def get_definitions(self) -> Dict:
        """
        获取数据模型定义

        Returns:
            模型定义字典
        """
        # OpenAPI 3.0+
        if 'components' in self.spec and 'schemas' in self.spec['components']:
            return self.spec['components']['schemas']

        # Swagger 2.0
        if 'definitions' in self.spec:
            return self.spec['definitions']

        return {}

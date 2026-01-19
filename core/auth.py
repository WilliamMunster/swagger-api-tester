"""
认证处理模块 - 支持多种API认证方式
"""

from typing import Dict, Optional
from enum import Enum


class AuthType(Enum):
    """认证类型枚举"""
    NONE = "none"
    API_KEY = "apiKey"
    HTTP_BASIC = "http_basic"
    HTTP_BEARER = "http_bearer"
    OAUTH2 = "oauth2"


class AuthHandler:
    """API认证处理器"""

    def __init__(self, auth_config: Dict):
        """
        初始化认证处理器

        Args:
            auth_config: 认证配置字典，例如:
                {
                    "type": "http_bearer",
                    "token": "your_token_here"
                }
                或
                {
                    "type": "apiKey",
                    "name": "X-API-Key",
                    "in": "header",
                    "value": "your_api_key"
                }
        """
        self.config = auth_config
        self.auth_type = self._determine_auth_type()

    def _determine_auth_type(self) -> AuthType:
        """确定认证类型"""
        auth_type_str = self.config.get('type', 'none').lower()

        if auth_type_str == 'apikey':
            return AuthType.API_KEY
        elif auth_type_str in ['http', 'bearer', 'http_bearer']:
            return AuthType.HTTP_BEARER
        elif auth_type_str == 'basic':
            return AuthType.HTTP_BASIC
        elif auth_type_str == 'oauth2':
            return AuthType.OAUTH2
        else:
            return AuthType.NONE

    def apply_auth(self, headers: Dict, params: Dict) -> tuple[Dict, Dict]:
        """
        应用认证信息到请求

        Args:
            headers: HTTP headers字典
            params: 查询参数字典

        Returns:
            (更新后的headers, 更新后的params)
        """
        if self.auth_type == AuthType.NONE:
            return headers, params

        headers = headers.copy()
        params = params.copy()

        if self.auth_type == AuthType.HTTP_BEARER:
            token = self.config.get('token', '')
            headers['Authorization'] = f"Bearer {token}"

        elif self.auth_type == AuthType.HTTP_BASIC:
            import base64
            username = self.config.get('username', '')
            password = self.config.get('password', '')
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            headers['Authorization'] = f"Basic {credentials}"

        elif self.auth_type == AuthType.API_KEY:
            api_key_name = self.config.get('name', 'X-API-Key')
            api_key_value = self.config.get('value', '')
            api_key_in = self.config.get('in', 'header')

            if api_key_in == 'header':
                headers[api_key_name] = api_key_value
            elif api_key_in == 'query':
                params[api_key_name] = api_key_value

        elif self.auth_type == AuthType.OAUTH2:
            token = self.config.get('access_token', '')
            headers['Authorization'] = f"Bearer {token}"

        return headers, params

    @staticmethod
    def from_swagger_security(security_schemes: Dict, security_requirements: list) -> Optional['AuthHandler']:
        """
        从Swagger安全定义创建认证处理器

        Args:
            security_schemes: Swagger的securitySchemes或securityDefinitions
            security_requirements: 接口的security要求

        Returns:
            AuthHandler实例或None
        """
        if not security_requirements or not security_schemes:
            return None

        # 获取第一个安全要求
        first_req = security_requirements[0]
        if not first_req:
            return None

        # 获取安全scheme名称
        scheme_name = list(first_req.keys())[0]
        scheme = security_schemes.get(scheme_name)

        if not scheme:
            return None

        # 转换为AuthHandler配置
        scheme_type = scheme.get('type', '').lower()

        if scheme_type == 'apikey':
            return AuthHandler({
                'type': 'apiKey',
                'name': scheme.get('name', 'X-API-Key'),
                'in': scheme.get('in', 'header'),
                'value': ''  # 需要用户配置
            })
        elif scheme_type == 'http':
            http_scheme = scheme.get('scheme', 'bearer').lower()
            if http_scheme == 'bearer':
                return AuthHandler({
                    'type': 'http_bearer',
                    'token': ''  # 需要用户配置
                })
            elif http_scheme == 'basic':
                return AuthHandler({
                    'type': 'http_basic',
                    'username': '',
                    'password': ''
                })
        elif scheme_type == 'oauth2':
            return AuthHandler({
                'type': 'oauth2',
                'access_token': ''  # 需要用户配置
            })

        return None

"""
场景解析器 - 解析YAML场景定义文件
"""

import yaml
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class StepConfig:
    """测试步骤配置"""
    name: str
    api: str  # HTTP方法和路径，如 "POST /api/users"
    request: Dict[str, Any] = field(default_factory=dict)  # 请求配置（headers, query, body等）
    extract: List[Dict[str, Any]] = field(default_factory=list)  # 变量提取配置
    assert_rules: List[str] = field(default_factory=list)  # 断言规则
    condition: Optional[Dict[str, Any]] = None  # 条件分支
    loop: Optional[Dict[str, Any]] = None  # 循环配置
    parallel: Optional[Dict[str, Any]] = None  # 并行配置


@dataclass
class ScenarioConfig:
    """场景配置"""
    name: str
    description: str = ""
    version: str = "2.0"
    config: Dict[str, Any] = field(default_factory=dict)  # 全局配置（base_url, timeout等）
    setup: List[StepConfig] = field(default_factory=list)  # 前置步骤
    steps: List[StepConfig] = field(default_factory=list)  # 主要步骤
    teardown: List[StepConfig] = field(default_factory=list)  # 清理步骤


class ScenarioParser:
    """场景定义解析器"""

    def parse_file(self, yaml_file: str) -> ScenarioConfig:
        """
        解析YAML场景定义文件

        Args:
            yaml_file: YAML文件路径

        Returns:
            ScenarioConfig: 解析后的场景配置

        Raises:
            ValueError: 文件格式错误
            FileNotFoundError: 文件不存在
        """
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"场景文件不存在: {yaml_file}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAML格式错误: {e}")

        return self.parse(data)

    def parse(self, data: Dict) -> ScenarioConfig:
        """
        解析场景定义数据

        Args:
            data: 场景定义字典

        Returns:
            ScenarioConfig: 解析后的场景配置

        Raises:
            ValueError: 数据格式错误
        """
        if not isinstance(data, dict):
            raise ValueError("场景定义必须是一个字典")

        if 'scenario' not in data:
            raise ValueError("缺少 'scenario' 根节点")

        scenario_data = data['scenario']

        # 解析基本信息
        name = scenario_data.get('name')
        if not name:
            raise ValueError("缺少场景名称 'name'")

        description = scenario_data.get('description', '')
        version = scenario_data.get('version', '2.0')
        config = scenario_data.get('config', {})

        # 解析步骤
        setup_steps = self._parse_steps(scenario_data.get('setup', []))
        main_steps = self._parse_steps(scenario_data.get('steps', []))
        teardown_steps = self._parse_steps(scenario_data.get('teardown', []))

        if not main_steps:
            raise ValueError("场景必须包含至少一个测试步骤")

        return ScenarioConfig(
            name=name,
            description=description,
            version=version,
            config=config,
            setup=setup_steps,
            steps=main_steps,
            teardown=teardown_steps
        )

    def _parse_steps(self, steps_data: List[Dict]) -> List[StepConfig]:
        """
        解析步骤列表

        Args:
            steps_data: 步骤数据列表

        Returns:
            List[StepConfig]: 解析后的步骤列表
        """
        if not steps_data:
            return []

        steps = []
        for i, step_data in enumerate(steps_data):
            try:
                step = self._parse_step(step_data)
                steps.append(step)
            except Exception as e:
                raise ValueError(f"解析第 {i + 1} 个步骤时出错: {e}")

        return steps

    def _parse_step(self, step_data: Dict) -> StepConfig:
        """
        解析单个步骤

        Args:
            step_data: 步骤数据字典

        Returns:
            StepConfig: 解析后的步骤配置
        """
        if not isinstance(step_data, dict):
            raise ValueError("步骤定义必须是一个字典")

        # 必填字段
        name = step_data.get('name')
        if not name:
            raise ValueError("步骤缺少名称 'name'")

        api = step_data.get('api')
        if not api:
            raise ValueError(f"步骤 '{name}' 缺少 'api' 定义")

        # 可选字段
        request = step_data.get('request', {})
        extract = step_data.get('extract', [])
        assert_rules = step_data.get('assert', [])
        condition = step_data.get('condition')
        loop = step_data.get('loop')
        parallel = step_data.get('parallel')

        return StepConfig(
            name=name,
            api=api,
            request=request,
            extract=extract,
            assert_rules=assert_rules,
            condition=condition,
            loop=loop,
            parallel=parallel
        )

    def validate(self, scenario: ScenarioConfig) -> List[str]:
        """
        验证场景定义的合法性

        Args:
            scenario: 场景配置

        Returns:
            List[str]: 错误列表（空列表表示验证通过）
        """
        errors = []

        # 验证场景名称
        if not scenario.name or not scenario.name.strip():
            errors.append("场景名称不能为空")

        # 验证步骤
        if not scenario.steps:
            errors.append("场景必须包含至少一个测试步骤")

        # 验证每个步骤
        all_steps = scenario.setup + scenario.steps + scenario.teardown
        for i, step in enumerate(all_steps):
            step_errors = self._validate_step(step, i + 1)
            errors.extend(step_errors)

        return errors

    def _validate_step(self, step: StepConfig, index: int) -> List[str]:
        """
        验证单个步骤

        Args:
            step: 步骤配置
            index: 步骤索引（用于错误提示）

        Returns:
            List[str]: 错误列表
        """
        errors = []

        # 验证步骤名称
        if not step.name or not step.name.strip():
            errors.append(f"第 {index} 个步骤缺少名称")

        # 验证API定义
        if not step.api or not step.api.strip():
            errors.append(f"步骤 '{step.name}' 缺少API定义")
        else:
            # 验证API格式（应该是 "METHOD /path" 格式）
            parts = step.api.strip().split(None, 1)
            if len(parts) != 2:
                errors.append(f"步骤 '{step.name}' 的API格式错误，应为 'METHOD /path'")
            else:
                method, path = parts
                valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
                if method.upper() not in valid_methods:
                    errors.append(f"步骤 '{step.name}' 的HTTP方法 '{method}' 不支持")

        # 验证extract配置
        if step.extract:
            for extract_config in step.extract:
                if not isinstance(extract_config, dict):
                    errors.append(f"步骤 '{step.name}' 的extract配置必须是字典")
                elif 'name' not in extract_config:
                    errors.append(f"步骤 '{step.name}' 的extract配置缺少 'name' 字段")

        # 验证condition配置
        if step.condition:
            if not isinstance(step.condition, dict):
                errors.append(f"步骤 '{step.name}' 的condition配置必须是字典")
            elif 'if' not in step.condition:
                errors.append(f"步骤 '{step.name}' 的condition配置缺少 'if' 条件")

        return errors


# 测试代码
if __name__ == '__main__':
    parser = ScenarioParser()

    # 测试解析示例场景文件
    try:
        scenario = parser.parse_file('scenarios/user_workflow_example.yaml')
        print(f"✓ 成功解析场景: {scenario.name}")
        print(f"  描述: {scenario.description}")
        print(f"  步骤数: {len(scenario.steps)}")
        print(f"  清理步骤: {len(scenario.teardown)}")

        # 验证场景
        errors = parser.validate(scenario)
        if errors:
            print("\n验证错误:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n✓ 场景验证通过")

    except Exception as e:
        print(f"✗ 解析失败: {e}")

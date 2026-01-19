"""
Swagger API自动化测试框架 - 主程序入口
"""

import argparse
import yaml
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from core.parser import SwaggerParser
from core.test_generator import TestGenerator
from core.data_generator import DataGenerator
from core.executor import TestExecutor
from core.auth import AuthHandler
from core.reporter import HtmlReporter

# 场景测试模块
from scenario import ScenarioParser, ScenarioExecutor


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def run_scenario_test(scenario_file: str, base_url: str = None, config: Dict = None, output: str = None):
    """
    执行场景测试（2.0模式）

    Args:
        scenario_file: 场景定义文件路径
        base_url: API基础URL
        config: 配置字典
        output: 输出报告路径
    """
    print("=" * 60)
    print("🚀 Swagger API自动化测试框架 2.0 - 场景测试")
    print("=" * 60)

    # 1. 解析场景文件
    print(f"\n📖 正在解析场景文件: {scenario_file}")
    parser = ScenarioParser()
    scenario = parser.parse_file(scenario_file)

    print(f"   场景: {scenario.name}")
    print(f"   描述: {scenario.description}")
    print(f"   版本: {scenario.version}")
    print(f"   测试步骤: {len(scenario.steps)}个")
    if scenario.setup:
        print(f"   前置步骤: {len(scenario.setup)}个")
    if scenario.teardown:
        print(f"   清理步骤: {len(scenario.teardown)}个")

    # 2. 验证场景
    errors = parser.validate(scenario)
    if errors:
        print(f"\n❌ 场景验证失败:")
        for error in errors:
            print(f"   - {error}")
        sys.exit(1)

    print(f"   ✓ 场景验证通过")

    # 3. 初始化执行器
    auth_token = None
    if config and 'auth' in config:
        auth_config = config['auth']
        if auth_config.get('type') == 'http_bearer':
            auth_token = auth_config.get('token')

    executor = ScenarioExecutor(
        base_url=base_url,
        timeout=config.get('execution', {}).get('timeout', 30) if config else 30,
        verify_ssl=config.get('execution', {}).get('verify_ssl', True) if config else True,
        auth_token=auth_token
    )

    # 4. 执行场景
    print(f"\n🧪 开始执行场景测试...")
    result = executor.execute(scenario)

    # 5. 显示结果
    print(f"\n" + "=" * 60)
    print("✨ 场景测试完成！")
    print("=" * 60)

    print(f"\n场景: {result.name}")
    print(f"状态: {'✓ 通过' if result.passed else '✗ 失败'}")
    print(f"\n步骤统计:")
    print(f"  总计: {result.total_steps}")
    print(f"  通过: {result.passed_steps} ✓")
    print(f"  失败: {result.failed_steps} ✗")
    print(f"  跳过: {result.skipped_steps}")
    print(f"\n总耗时: {result.total_time:.2f}秒")

    # 6. 生成报告（简化版）
    if output:
        print(f"\n📊 正在生成测试报告...")
        # TODO: 实现场景测试报告生成
        print(f"   提示: 场景测试报告生成功能正在开发中")

    # 显示提取的变量
    if result.context_snapshot:
        print(f"\n📌 场景上下文变量:")
        for scope, vars_dict in result.context_snapshot.items():
            if vars_dict:
                print(f"  {scope}:")
                for key, value in vars_dict.items():
                    value_str = str(value)
                    if len(value_str) > 50:
                        value_str = value_str[:50] + "..."
                    print(f"    {key}: {value_str}")

    # 如果有失败步骤，返回非0退出码
    sys.exit(0 if result.failed_steps == 0 else 1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Swagger API自动化测试框架',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 1.0 单接口测试模式
  python main.py -s examples/petstore.json -u https://petstore.swagger.io/v2

  # 使用配置文件
  python main.py -s swagger.yaml -c config/test_config.yaml

  # 并行执行测试
  python main.py -s swagger.json -u http://api.example.com --parallel --workers 10

  # 2.0 场景测试模式
  python main.py --scenario scenarios/user_workflow_example.yaml

  # 场景测试使用配置文件
  python main.py --scenario scenarios/order_flow.yaml -c config/test_config.yaml
        """
    )

    # 测试模式选择
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '-s', '--spec',
        help='Swagger/OpenAPI规范文件路径（1.0单接口测试模式）'
    )
    mode_group.add_argument(
        '--scenario',
        help='场景定义文件路径（2.0场景测试模式）'
    )

    parser.add_argument(
        '-u', '--base-url',
        help='API基础URL（如果spec文件中没有定义则必填）'
    )

    parser.add_argument(
        '-c', '--config',
        help='配置文件路径（YAML格式）'
    )

    parser.add_argument(
        '-o', '--output',
        help='测试报告输出路径（默认: reports/report_<timestamp>.html）'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='并行执行测试用例'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='并行执行时的最大线程数（默认: 5）'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='请求超时时间（秒，默认: 30）'
    )

    parser.add_argument(
        '--no-ssl-verify',
        action='store_true',
        help='不验证SSL证书'
    )

    args = parser.parse_args()

    # 加载配置（如果有）
    config = {}
    if args.config:
        config = load_config(args.config)

    # 根据模式选择执行不同的测试
    if args.scenario:
        # 2.0 场景测试模式
        run_scenario_test(
            scenario_file=args.scenario,
            base_url=args.base_url,
            config=config,
            output=args.output
        )
        return

    # 1.0 单接口测试模式（原有逻辑）
    try:
        print("=" * 60)
        print("🚀 Swagger API自动化测试框架 1.0")
        print("=" * 60)

        # 1. 加载Swagger规范
        print(f"\n📖 正在解析Swagger文件: {args.spec}")
        swagger_parser = SwaggerParser(args.spec)
        api_info = swagger_parser.get_api_info()

        print(f"   API: {api_info['title']} v{api_info['version']}")
        print(f"   Spec版本: {api_info['spec_version']}")

        # 确定base_url
        base_url = args.base_url or api_info.get('base_url')
        if not base_url:
            print("\n❌ 错误: 无法确定API基础URL，请使用-u参数指定")
            sys.exit(1)

        print(f"   基础URL: {base_url}")

        # 2. 初始化认证处理器
        auth_handler = None
        if 'auth' in config:
            print(f"\n🔐 初始化认证处理器")
            auth_handler = AuthHandler(config['auth'])
        else:
            # 尝试从Swagger中自动配置认证
            security_defs = swagger_parser.get_security_definitions()
            if security_defs:
                print(f"\n💡 检测到API需要认证，但未提供认证配置")
                print(f"   请在配置文件中添加auth节点，参考config/default_config.yaml")

        # 4. 获取所有端点
        print(f"\n🔍 正在分析API端点...")
        endpoints = swagger_parser.get_all_endpoints()
        print(f"   发现 {len(endpoints)} 个API端点")

        # 5. 生成测试用例
        print(f"\n📝 正在生成测试用例...")
        data_gen = DataGenerator()
        test_gen = TestGenerator(data_gen)

        all_test_cases = []
        for endpoint in endpoints:
            if endpoint.get('deprecated'):
                continue  # 跳过已废弃的端点

            test_cases = test_gen.generate_test_cases(endpoint)
            all_test_cases.extend([(endpoint, test_cases)])

        total_cases = sum(len(cases) for _, cases in all_test_cases)
        print(f"   生成 {total_cases} 个测试用例")

        # 6. 执行测试
        print(f"\n🧪 开始执行测试...")
        print(f"   执行模式: {'并行' if args.parallel else '串行'}")
        if args.parallel:
            print(f"   并行线程数: {args.workers}")

        executor = TestExecutor(
            base_url=base_url,
            auth_handler=auth_handler,
            timeout=args.timeout,
            verify_ssl=not args.no_ssl_verify
        )

        all_results = []
        for i, (endpoint, test_cases) in enumerate(all_test_cases, 1):
            endpoint_name = f"{endpoint['method']} {endpoint['path']}"
            print(f"\n   [{i}/{len(all_test_cases)}] {endpoint_name} ({len(test_cases)}个用例)")

            results = executor.execute_test_suite(
                test_cases=test_cases,
                endpoint=endpoint,
                parallel=args.parallel,
                max_workers=args.workers
            )

            all_results.extend(results)

            # 显示进度
            passed = sum(1 for r in results if r.passed)
            print(f"        ✓ {passed}/{len(results)} 通过")

        executor.close()

        # 7. 生成报告
        print(f"\n📊 正在生成测试报告...")

        if not args.output:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"reports/report_{timestamp}.html"
        else:
            output_path = args.output

        reporter = HtmlReporter()
        report_file = reporter.generate_report(
            results=all_results,
            api_info=api_info,
            output_path=output_path
        )

        # 8. 显示测试总结
        print(f"\n" + "=" * 60)
        print("✨ 测试完成！")
        print("=" * 60)

        total = len(all_results)
        passed = sum(1 for r in all_results if r.passed)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        print(f"\n总用例数: {total}")
        print(f"通过: {passed} ✓")
        print(f"失败: {failed} ✗")
        print(f"通过率: {pass_rate:.2f}%")

        print(f"\n📄 报告已生成: {report_file}")

        # 如果有失败用例，返回非0退出码
        sys.exit(0 if failed == 0 else 1)

    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 执行错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

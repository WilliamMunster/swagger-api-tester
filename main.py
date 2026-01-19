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


def load_config(config_path: str) -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Swagger API自动化测试框架',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础测试
  python main.py -s examples/petstore.json -u https://petstore.swagger.io/v2

  # 使用配置文件
  python main.py -s swagger.yaml -c config/test_config.yaml

  # 并行执行测试
  python main.py -s swagger.json -u http://api.example.com --parallel --workers 10

  # 指定输出路径
  python main.py -s swagger.yaml -u http://api.example.com -o reports/my_report.html
        """
    )

    parser.add_argument(
        '-s', '--spec',
        required=True,
        help='Swagger/OpenAPI规范文件路径（支持JSON和YAML）'
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

    try:
        print("=" * 60)
        print("🚀 Swagger API自动化测试框架")
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

        # 2. 加载配置（如果有）
        config = {}
        if args.config:
            print(f"\n⚙️  正在加载配置文件: {args.config}")
            config = load_config(args.config)

        # 3. 初始化认证处理器
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

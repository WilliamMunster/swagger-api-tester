"""
测试报告生成器 - 生成HTML格式的测试报告
"""

from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
import json


class HtmlReporter:
    """HTML测试报告生成器"""

    def generate_report(
            self,
            results: List[Any],
            api_info: Dict,
            output_path: str
    ) -> str:
        """
        生成HTML测试报告

        Args:
            results: 测试结果列表（TestResult对象列表）
            api_info: API基本信息
            output_path: 输出文件路径

        Returns:
            生成的报告文件路径
        """
        # 统计数据
        stats = self._calculate_stats(results)

        # 按端点分组
        grouped_results = self._group_by_endpoint(results)

        # 生成HTML
        html_content = self._generate_html(api_info, stats, grouped_results, results)

        # 写入文件
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return str(output_file)

    def _calculate_stats(self, results: List) -> Dict:
        """计算统计数据"""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed

        pass_rate = (passed / total * 100) if total > 0 else 0

        # 按优先级统计
        priority_stats = {}
        for r in results:
            priority = r.test_case.get('priority', 'P3')
            if priority not in priority_stats:
                priority_stats[priority] = {'total': 0, 'passed': 0, 'failed': 0}

            priority_stats[priority]['total'] += 1
            if r.passed:
                priority_stats[priority]['passed'] += 1
            else:
                priority_stats[priority]['failed'] += 1

        # 按类型统计
        type_stats = {}
        for r in results:
            test_type = r.test_case.get('type', 'Unknown')
            if test_type not in type_stats:
                type_stats[test_type] = {'total': 0, 'passed': 0, 'failed': 0}

            type_stats[test_type]['total'] += 1
            if r.passed:
                type_stats[test_type]['passed'] += 1
            else:
                type_stats[test_type]['failed'] += 1

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': round(pass_rate, 2),
            'by_priority': priority_stats,
            'by_type': type_stats
        }

    def _group_by_endpoint(self, results: List) -> Dict:
        """按端点分组结果"""
        grouped = {}

        for result in results:
            test_case = result.test_case
            endpoint_key = f"{test_case['method']} {test_case['path']}"

            if endpoint_key not in grouped:
                grouped[endpoint_key] = []

            grouped[endpoint_key].append(result)

        return grouped

    def _generate_html(
            self,
            api_info: Dict,
            stats: Dict,
            grouped_results: Dict,
            all_results: List
    ) -> str:
        """生成HTML内容"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API测试报告 - {api_info.get('title', 'Unknown API')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
               background: #f5f5f5; padding: 20px; color: #333; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; margin-bottom: 10px; font-size: 28px; }}
        .meta {{ color: #7f8c8d; margin-bottom: 30px; font-size: 14px; }}
        .meta span {{ margin-right: 20px; }}

        /* 概览卡片 */
        .overview {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
        .card.success {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .card.failed {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .card.rate {{ background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }}
        .card h3 {{ font-size: 14px; opacity: 0.9; margin-bottom: 10px; }}
        .card .value {{ font-size: 36px; font-weight: bold; }}

        /* 统计图表 */
        .charts {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .chart {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef; }}
        .chart h3 {{ margin-bottom: 15px; color: #2c3e50; font-size: 16px; }}
        .bar-chart {{ display: flex; flex-direction: column; gap: 10px; }}
        .bar-item {{ display: flex; align-items: center; }}
        .bar-label {{ width: 100px; font-size: 14px; }}
        .bar-container {{ flex: 1; height: 24px; background: #e9ecef; border-radius: 4px; overflow: hidden; position: relative; }}
        .bar-fill {{ height: 100%; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); transition: width 0.3s; }}
        .bar-fill.success {{ background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%); }}
        .bar-fill.failed {{ background: linear-gradient(90deg, #eb3349 0%, #f45c43 100%); }}
        .bar-value {{ margin-left: 10px; font-size: 14px; color: #666; }}

        /* 端点结果 */
        .endpoint-section {{ margin-bottom: 30px; }}
        .endpoint-header {{ background: #2c3e50; color: white; padding: 15px 20px; border-radius: 6px; margin-bottom: 10px; cursor: pointer;
                           display: flex; justify-content: space-between; align-items: center; }}
        .endpoint-header:hover {{ background: #34495e; }}
        .method {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-right: 10px; }}
        .method.GET {{ background: #61affe; }}
        .method.POST {{ background: #49cc90; }}
        .method.PUT {{ background: #fca130; }}
        .method.DELETE {{ background: #f93e3e; }}
        .method.PATCH {{ background: #50e3c2; }}

        .test-results {{ display: none; }}
        .test-results.show {{ display: block; }}

        .test-case {{ background: white; border: 1px solid #e9ecef; border-radius: 4px; margin-bottom: 10px; overflow: hidden; }}
        .test-case-header {{ padding: 15px 20px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; }}
        .test-case-header:hover {{ background: #f8f9fa; }}
        .test-case.passed .test-case-header {{ border-left: 4px solid #28a745; }}
        .test-case.failed .test-case-header {{ border-left: 4px solid #dc3545; }}

        .status-badge {{ padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .status-badge.passed {{ background: #d4edda; color: #155724; }}
        .status-badge.failed {{ background: #f8d7da; color: #721c24; }}

        .test-details {{ padding: 20px; background: #f8f9fa; border-top: 1px solid #e9ecef; display: none; }}
        .test-details.show {{ display: block; }}

        .detail-section {{ margin-bottom: 15px; }}
        .detail-section h4 {{ color: #2c3e50; margin-bottom: 8px; font-size: 14px; }}
        .detail-section pre {{ background: #2c3e50; color: #f8f9fa; padding: 12px; border-radius: 4px; overflow-x: auto; font-size: 12px; }}

        .error-list {{ list-style: none; }}
        .error-list li {{ background: #f8d7da; color: #721c24; padding: 8px 12px; border-radius: 4px; margin-bottom: 5px; font-size: 13px; }}
        .warning-list li {{ background: #fff3cd; color: #856404; padding: 8px 12px; border-radius: 4px; margin-bottom: 5px; font-size: 13px; }}

        .response-time {{ color: #666; font-size: 12px; }}
        .toggle-icon {{ transition: transform 0.3s; }}
        .toggle-icon.rotate {{ transform: rotate(180deg); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔬 API自动化测试报告</h1>
        <div class="meta">
            <span><strong>API:</strong> {api_info.get('title', 'Unknown')}</span>
            <span><strong>版本:</strong> {api_info.get('version', '1.0.0')}</span>
            <span><strong>Spec:</strong> {api_info.get('spec_version', 'Unknown')}</span>
            <span><strong>测试时间:</strong> {now}</span>
        </div>

        <div class="overview">
            <div class="card">
                <h3>总用例数</h3>
                <div class="value">{stats['total']}</div>
            </div>
            <div class="card success">
                <h3>通过</h3>
                <div class="value">{stats['passed']}</div>
            </div>
            <div class="card failed">
                <h3>失败</h3>
                <div class="value">{stats['failed']}</div>
            </div>
            <div class="card rate">
                <h3>通过率</h3>
                <div class="value">{stats['pass_rate']}%</div>
            </div>
        </div>

        <div class="charts">
            <div class="chart">
                <h3>按优先级统计</h3>
                <div class="bar-chart">
                    {self._generate_priority_chart(stats['by_priority'])}
                </div>
            </div>
            <div class="chart">
                <h3>按测试类型统计</h3>
                <div class="bar-chart">
                    {self._generate_type_chart(stats['by_type'])}
                </div>
            </div>
        </div>

        <h2 style="margin-bottom: 20px; color: #2c3e50;">📋 测试结果详情</h2>

        {self._generate_endpoint_sections(grouped_results)}
    </div>

    <script>
        // 切换端点详情
        document.querySelectorAll('.endpoint-header').forEach(header => {{
            header.addEventListener('click', () => {{
                const results = header.nextElementSibling;
                const icon = header.querySelector('.toggle-icon');
                results.classList.toggle('show');
                icon.classList.toggle('rotate');
            }});
        }});

        // 切换测试用例详情
        document.querySelectorAll('.test-case-header').forEach(header => {{
            header.addEventListener('click', () => {{
                const details = header.nextElementSibling;
                details.classList.toggle('show');
            }});
        }});
    </script>
</body>
</html>"""

        return html

    def _generate_priority_chart(self, priority_stats: Dict) -> str:
        """生成优先级图表HTML"""
        html_parts = []

        for priority in ['P0', 'P1', 'P2', 'P3']:
            if priority not in priority_stats:
                continue

            stats = priority_stats[priority]
            total = stats['total']
            passed = stats['passed']
            pass_rate = (passed / total * 100) if total > 0 else 0

            html_parts.append(f"""
                <div class="bar-item">
                    <div class="bar-label">{priority}</div>
                    <div class="bar-container">
                        <div class="bar-fill success" style="width: {pass_rate}%"></div>
                    </div>
                    <div class="bar-value">{passed}/{total}</div>
                </div>
            """)

        return ''.join(html_parts)

    def _generate_type_chart(self, type_stats: Dict) -> str:
        """生成类型图表HTML"""
        html_parts = []

        for test_type, stats in type_stats.items():
            total = stats['total']
            passed = stats['passed']
            pass_rate = (passed / total * 100) if total > 0 else 0

            html_parts.append(f"""
                <div class="bar-item">
                    <div class="bar-label">{test_type}</div>
                    <div class="bar-container">
                        <div class="bar-fill success" style="width: {pass_rate}%"></div>
                    </div>
                    <div class="bar-value">{passed}/{total}</div>
                </div>
            """)

        return ''.join(html_parts)

    def _generate_endpoint_sections(self, grouped_results: Dict) -> str:
        """生成端点测试结果HTML"""
        html_parts = []

        for endpoint_key, results in grouped_results.items():
            method, path = endpoint_key.split(' ', 1)
            passed_count = sum(1 for r in results if r.passed)
            total_count = len(results)

            html_parts.append(f"""
                <div class="endpoint-section">
                    <div class="endpoint-header">
                        <div>
                            <span class="method {method}">{method}</span>
                            <span>{path}</span>
                            <span style="margin-left: 15px; font-size: 14px; opacity: 0.8;">
                                {passed_count}/{total_count} 通过
                            </span>
                        </div>
                        <span class="toggle-icon">▼</span>
                    </div>
                    <div class="test-results">
                        {self._generate_test_cases(results)}
                    </div>
                </div>
            """)

        return ''.join(html_parts)

    def _generate_test_cases(self, results: List) -> str:
        """生成测试用例HTML"""
        html_parts = []

        for result in results:
            status = 'passed' if result.passed else 'failed'
            status_text = '✓ 通过' if result.passed else '✗ 失败'

            # 错误和警告
            errors_html = ""
            if result.errors:
                error_items = ''.join(f"<li>{error}</li>" for error in result.errors)
                errors_html = f'<div class="detail-section"><h4>❌ 错误</h4><ul class="error-list">{error_items}</ul></div>'

            warnings_html = ""
            if result.warnings:
                warning_items = ''.join(f"<li>{warning}</li>" for warning in result.warnings)
                warnings_html = f'<div class="detail-section"><h4>⚠️ 警告</h4><ul class="warning-list">{warning_items}</ul></div>'

            # 请求和响应信息
            request_json = json.dumps(result.request_info, indent=2, ensure_ascii=False)
            response_json = json.dumps(result.response_info, indent=2, ensure_ascii=False)

            html_parts.append(f"""
                <div class="test-case {status}">
                    <div class="test-case-header">
                        <div>
                            <strong>{result.test_case.get('name')}</strong>
                            <span style="color: #666; margin-left: 10px; font-size: 13px;">
                                {result.test_case.get('type')} | {result.test_case.get('priority')}
                            </span>
                            <span class="response-time" style="margin-left: 10px;">⏱ {result.response_time}ms</span>
                        </div>
                        <span class="status-badge {status}">{status_text}</span>
                    </div>
                    <div class="test-details">
                        {errors_html}
                        {warnings_html}
                        <div class="detail-section">
                            <h4>📤 请求信息</h4>
                            <pre>{request_json}</pre>
                        </div>
                        <div class="detail-section">
                            <h4>📥 响应信息</h4>
                            <pre>{response_json}</pre>
                        </div>
                    </div>
                </div>
            """)

        return ''.join(html_parts)

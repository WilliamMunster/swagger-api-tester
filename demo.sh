#!/bin/bash

# Swagger API自动化测试框架 - 演示脚本

echo "======================================================"
echo "🎯 Swagger API自动化测试框架 - 快速演示"
echo "======================================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到Python，请先安装Python 3.8+"
    exit 1
fi

# 使用python3或python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "✅ Python版本:"
$PYTHON_CMD --version
echo ""

# 检查依赖
echo "📦 检查依赖包..."
if ! $PYTHON_CMD -c "import requests" 2>/dev/null; then
    echo "⚠️  警告: 依赖包未安装"
    echo "正在安装依赖..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败，请手动运行: pip install -r requirements.txt"
        exit 1
    fi
else
    echo "✅ 依赖包已安装"
fi
echo ""

# 运行示例测试
echo "======================================================"
echo "🚀 开始运行Pet Store API示例测试"
echo "======================================================"
echo ""
echo "提示: 这将测试公开的Pet Store API"
echo "      测试大约需要30-60秒"
echo ""
read -p "按Enter键继续..."
echo ""

# 执行测试
$PYTHON_CMD main.py \
    -s examples/petstore_swagger.json \
    -u https://petstore.swagger.io/v2

# 检查执行结果
if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================"
    echo "✨ 测试成功完成！"
    echo "======================================================"
    echo ""
    echo "📊 查看测试报告:"
    echo "   在浏览器中打开 reports/ 目录下的HTML文件"
    echo ""

    # 尝试自动打开报告
    LATEST_REPORT=$(ls -t reports/*.html 2>/dev/null | head -1)
    if [ -n "$LATEST_REPORT" ]; then
        echo "💡 尝试自动打开报告..."
        if command -v open &> /dev/null; then
            open "$LATEST_REPORT"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$LATEST_REPORT"
        else
            echo "   请手动打开: $LATEST_REPORT"
        fi
    fi
else
    echo ""
    echo "======================================================"
    echo "⚠️  测试完成，但有部分用例失败"
    echo "======================================================"
    echo ""
    echo "这是正常的，因为某些测试用例是故意测试失败场景"
    echo "请查看HTML报告了解详情"
fi

echo ""
echo "======================================================"
echo "📚 下一步"
echo "======================================================"
echo ""
echo "1. 查看完整文档:"
echo "   cat README.md"
echo ""
echo "2. 查看快速开始指南:"
echo "   cat QUICKSTART.md"
echo ""
echo "3. 测试您自己的API:"
echo "   python main.py -s your_swagger.yaml -u http://your-api.com"
echo ""
echo "4. 使用配置文件:"
echo "   python main.py -s your_swagger.yaml -c config/my_config.yaml"
echo ""
echo "5. 查看所有选项:"
echo "   python main.py --help"
echo ""
echo "======================================================"
echo "感谢使用！如有问题请查看文档或提交Issue"
echo "======================================================"

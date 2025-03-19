# MCP 客户端示例

这是一个使用 MCP SDK 的示例客户端，用于演示如何连接到 MCP 服务器并使用其功能。

## 功能特性

- 连接到 MCP 服务器
- 列出所有可用的工具、资源和提示
- 测试计算器工具（求和和平均值计算）
- 测试文件系统资源（列出目录内容）
- 测试提示模板（代码审查和Git提交消息生成）

## 安装

1. 创建虚拟环境（推荐）：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

运行客户端：

```bash
python demo_client.py <server_url>
```

例如：

```bash
python demo_client.py http://localhost:8000/sse
```

## 示例输出

程序将显示：
1. 服务器连接状态
2. 可用的工具、资源和提示列表
3. 计算器工具测试结果
4. 文件系统资源测试结果
5. 提示模板测试结果

## 注意事项

- 确保MCP服务器已经启动并可访问
- 确保提供的URL使用 http:// 或 https:// 协议
- 所有错误都会被适当处理并显示有用的错误消息 
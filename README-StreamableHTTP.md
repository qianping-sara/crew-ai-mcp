# StreamableHTTP MCP服务器和客户端

本项目实现了基于StreamableHTTP的MCP（Model Context Protocol）服务器和客户端，支持JSON响应和流式响应两种模式。

## 概述

StreamableHTTP实现提供了以下优点：
- 支持基于HTTP的请求-响应模式
- 可以在无状态环境（如Serverless Functions）中使用
- 提供会话管理，允许多个客户端连接
- 支持JSON响应和流式（SSE）响应两种模式

## 服务器组件

服务器部分包含两个主要文件：
- `src/streamable_http_server.py` - 服务器实现，基于FastAPI
- `src/streamable_http_server_main.py` - 服务器启动脚本

服务器继承了原有项目中的全部工具、资源和提示模板功能。

## 客户端示例

客户端示例位于 `examples_client/streamable_http_client.py`，提供了完整的StreamableHTTP MCP客户端实现，支持以下功能：
- 初始化和会话管理
- 工具、资源和提示模板列表获取
- 工具调用
- 资源访问
- 提示模板获取

## 运行服务器

要启动StreamableHTTP服务器，请执行以下命令：

```bash
python src/streamable_http_server_main.py
```

服务器默认在端口3000上启动。可以通过设置环境变量`PORT`来更改端口：

```bash
PORT=8080 python src/streamable_http_server_main.py
```

## 运行客户端示例

客户端示例需要安装依赖：

```bash
pip install aiohttp
```

然后可以通过以下命令运行客户端：

```bash
python examples_client/streamable_http_client.py http://localhost:3000/mcp
```

默认情况下，客户端使用流式响应模式。如果要使用JSON响应模式，可以添加`--json`参数：

```bash
python examples_client/streamable_http_client.py http://localhost:3000/mcp --json
```

## 与Serverless环境集成

StreamableHTTP实现特别适合在Serverless环境中部署：

1. 服务器可以部署为AWS Lambda、Azure Functions或Google Cloud Functions
2. 会话状态可以存储在Redis或DynamoDB等外部存储中
3. 客户端可以从任何支持HTTP请求的环境连接到服务器

## 自定义扩展

要添加自定义工具、资源或提示模板，可以按照原有项目的模式在相应模块中添加，然后确保在`streamable_http_server.py`中导入这些模块。


# 基本使用
python robust_mcp_client.py https://crew-ai-mcp-b7cdf81f032f.herokuapp.com/mcp

# 增加重试次数
python robust_mcp_client.py --retries 5 https://crew-ai-mcp-b7cdf81f032f.herokuapp.com/mcp

# 使用代理
python robust_mcp_client.py --proxy http://your-proxy-server:port https://crew-ai-mcp-b7cdf81f032f.herokuapp.com/mcp
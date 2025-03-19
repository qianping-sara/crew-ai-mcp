# Crew AI MCP Server

基于 Model Context Protocol (MCP) 实现的智能助手服务器，提供代码审查、Git 操作辅助、API 设计等功能。

## 功能特性

### 1. 资源访问
- 文件系统操作
  - 目录内容读取
  - 文件内容访问

### 2. 工具集成
- 计算工具
  - 数字列表求和
  - 平均值计算
  - 基础统计信息

- 用户管理
  - 用户信息获取
  - 用户验证

### 3. 提示模板
- 代码审查
  - 代码质量评估
  - 测试建议生成

- Git 辅助
  - 提交信息生成
  - Git 命令解释
  - 工作流程建议

- API 设计
  - RESTful API 设计
  - API 规范审查
  - API 测试用例生成

## 快速开始

### 环境要求
- Python 3.10 或更高版本
- MCP SDK 1.4.1 或更高版本

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/your-username/crew-ai-mcp.git
cd crew-ai-mcp
```

2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

### 使用方法

1. 直接运行服务器
```bash
python -m src.main
```

2. 与 Claude Desktop 集成
- 打开 Claude Desktop 配置文件：
```bash
code ~/Library/Application Support/Claude/claude_desktop_config.json
```
- 添加服务器配置：
```json
{
    "mcpServers": {
        "crew-ai-mcp": {
            "command": "python",
            "args": [
                "-m",
                "src.main"
            ]
        }
    }
}
```

## 项目结构

```
.
├── src/                  # 源代码目录
│   ├── mcp_server.py    # MCP服务器实例
│   ├── main.py          # 主入口文件
│   ├── resources/       # 资源模块
│   │   └── filesystem.py  # 文件系统资源
│   ├── tools/          # 工具模块
│   │   ├── calculator.py  # 计算工具
│   │   └── user.py       # 用户工具
│   └── prompts/        # 提示模块
│       ├── code_review.py # 代码审查提示
│       ├── git_helper.py  # Git辅助提示
│       └── api_design.py  # API设计提示
├── requirements.txt     # 项目依赖
└── vercel.json         # Vercel部署配置
```

## 扩展开发

### 添加新工具

1. 在 `src/tools/` 目录下创建新的 Python 文件
2. 导入 MCP 实例：
```python
from ..mcp_server import mcp
```
3. 使用装饰器定义工具：
```python
@mcp.tool()
async def my_tool(param: str) -> str:
    """工具描述"""
    return result
```

### 添加新提示

1. 在 `src/prompts/` 目录下创建新的 Python 文件
2. 使用装饰器定义提示：
```python
@mcp.prompt()
async def my_prompt(param: str) -> str:
    """提示描述"""
    return f"""提示模板内容：
    {param}
    """
```

### 添加新资源

1. 在 `src/resources/` 目录下创建新的 Python 文件
2. 使用装饰器定义资源：
```python
@mcp.resource("resource://{param}")
async def my_resource(param: str) -> str:
    """资源描述"""
    return resource_content
```

## 部署

### Vercel 部署
项目已配置 Vercel 部署文件，可直接部署：
```bash
vercel
```

### 自定义部署
可以将服务器集成到现有的 ASGI 应用中：
```python
from starlette.applications import Starlette
from starlette.routes import Mount
from src.mcp_server import mcp

app = Starlette(routes=[
    Mount('/', app=mcp.sse_app()),
])
```

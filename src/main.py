"""
MCP服务器主入口
导入所有模块并启动服务器
"""
# 导入MCP服务器实例
from src.mcp_server import mcp

# 导入所有资源模块
from src.resources import filesystem  # 直接导入filesystem模块

# 导入所有工具模块
from src.tools import calculator, user

# 导入所有提示模块
from src.prompts import code_review, git_helper, api_design

import os
import argparse
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse

async def health_check(request):
    """健康检查端点"""
    return JSONResponse({"status": "ok", "service": "crew-ai-mcp"})

def main():
    """启动MCP服务器"""
    parser = argparse.ArgumentParser(description="启动MCP服务器")
    parser.add_argument("--transport", default="sse", choices=["sse", "stdio"], 
                      help="指定传输协议: sse或stdio")
    args = parser.parse_args()

    # 从Heroku PORT环境变量获取端口
    port = int(os.environ.get("PORT", 8000))
    # 设置MCP_PORT环境变量，FastMCP库可能会使用这个变量
    os.environ["MCP_PORT"] = str(port)
    print(f"启动 MCP {args.transport.upper()} 服务器在端口 {port}...")
    
    if args.transport == 'stdio':
        return mcp.run(transport='stdio')
    else:
        # 创建Starlette应用并添加路由
        routes = [
            Route('/health', health_check),
        ]
        app = Starlette(routes=routes)
        
        # 将MCP应用挂载到Starlette应用上
        return mcp.run(transport='sse', app=app)


if __name__ == "__main__":
    main()
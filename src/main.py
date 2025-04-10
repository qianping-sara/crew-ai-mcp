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
import uvicorn
from uvicorn.config import Config
from uvicorn.server import Server

# 添加健康检查工具
@mcp.tool()
async def health() -> dict:
    """健康检查工具"""
    return {"status": "ok", "service": "crew-ai-mcp"}

def main():
    """启动MCP服务器"""
    # 从Heroku PORT环境变量获取端口
    port = int(os.environ.get("PORT", 8000))
    print(f"启动 MCP SSE 服务器在端口 {port}...")
    
    # 获取SSE应用程序
    app = mcp.sse_app()
    
    # 使用Server类直接启动，避免使用uvicorn.run()
    config = Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = Server(config=config)
    server.run()


if __name__ == "__main__":
    main()
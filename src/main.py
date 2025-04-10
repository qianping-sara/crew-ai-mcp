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

# 添加健康检查工具
@mcp.tool()
async def health() -> dict:
    """健康检查工具"""
    return {"status": "ok", "service": "crew-ai-mcp"}

def main():
    """启动MCP服务器"""
    # 从Heroku PORT环境变量获取端口
    port = int(os.environ.get("PORT", 8000))
    # 设置MCP_PORT环境变量，FastMCP库可能会使用这个变量
    os.environ["MCP_PORT"] = str(port)
    print(f"启动 MCP SSE 服务器在端口 {port}...")
    
    # 硬编码使用SSE传输方式
    return mcp.run(transport='sse')


if __name__ == "__main__":
    main()
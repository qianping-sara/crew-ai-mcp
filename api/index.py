from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP
import sys
import os

# 添加父目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入我们的MCP工具
from server import hello_world, calculate_sum, get_user_info

# 创建FastAPI应用
app = FastAPI(title="MCP Server API")

# 初始化MCP服务器
mcp = FastMCP("demo-server")

# 注册工具
mcp.tool()(hello_world)
mcp.tool()(calculate_sum)
mcp.tool()(get_user_info)

# 集成MCP到FastAPI
app.include_router(mcp.router, prefix="/mcp")

# 添加健康检查端点
@app.get("/")
async def health_check():
    return {"status": "ok", "message": "MCP Server is running"} 
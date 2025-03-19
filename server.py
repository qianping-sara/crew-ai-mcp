from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 服务器（仅在直接运行时使用）
mcp = FastMCP("demo-server")

async def hello_world() -> str:
    """一个简单的示例工具，返回问候语"""
    return "你好！我是 MCP 服务器。"

async def calculate_sum(numbers: List[float]) -> float:
    """计算一组数字的总和
    
    Args:
        numbers: 要计算总和的数字列表
    """
    return sum(numbers)

async def get_user_info(user_id: str) -> Dict[str, Any]:
    """获取用户信息（示例）
    
    Args:
        user_id: 用户ID
    """
    # 这里只是一个示例，实际应用中可能需要从数据库获取
    return {
        "id": user_id,
        "name": "示例用户",
        "email": "example@example.com",
        "role": "user"
    }

if __name__ == "__main__":
    # 仅在直接运行时注册工具并启动服务器
    mcp.tool()(hello_world)
    mcp.tool()(calculate_sum)
    mcp.tool()(get_user_info)
    mcp.run(transport='stdio') 
"""
MCP服务器实例
这个模块创建并导出MCP服务器实例，供其他模块使用
"""
from mcp.server.fastmcp import FastMCP

# 创建全局MCP服务器实例
mcp = FastMCP("crew-ai-mcp") 
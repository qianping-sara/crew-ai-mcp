"""
文件系统资源模块
提供文件系统相关的资源访问功能
"""
import os
from ..mcp_server import mcp

@mcp.resource("dir://{path}")
async def get_directory_contents(path: str) -> str:
    """获取指定目录的内容
    
    Args:
        path: 目录路径
    """
    try:
        contents = os.listdir(path)
        return "\n".join(contents)
    except Exception as e:
        return f"Error accessing directory: {str(e)}"

@mcp.resource("file://{path}")
async def get_file_contents(path: str) -> str:
    """获取文件内容
    
    Args:
        path: 文件路径
    """
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}" 
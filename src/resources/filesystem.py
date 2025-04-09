"""
文件系统资源模块
提供文件系统相关的资源访问功能
"""
import os
import logging
from urllib.parse import urlparse
from ..mcp_server import mcp

@mcp.resource("dir://{path}")
async def get_directory_contents(path: str) -> str:
    """获取指定目录的内容
    
    Args:
        path: 目录路径
    """
    try:
        print(f"获取目录内容: {path}")
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
        # 移除路径末尾可能存在的斜杠
        path = path.rstrip('/')
        print(f"读取文件 (原始路径): {path}")
        
        # 处理标准形式的file://path格式
        if path.startswith('/'):
            # 已经是绝对路径，直接使用
            file_path = path
        else:
            # 相对路径，基于当前工作目录
            file_path = os.path.join(os.getcwd(), path)
        
        print(f"解析后的文件路径: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}" 
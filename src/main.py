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

def main():
    """启动MCP服务器"""

    print("启动 MCP SSE 服务器...")
    return mcp.run(transport='sse')


if __name__ == "__main__":
    main()
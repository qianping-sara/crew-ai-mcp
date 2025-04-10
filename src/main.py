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
    parser = argparse.ArgumentParser(description="启动MCP服务器")
    parser.add_argument("--transport", default="sse", choices=["sse", "stdio"], 
                      help="指定传输协议: sse或stdio")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)),
                      help="服务器端口号 (默认: 从PORT环境变量获取或8000)")
    args = parser.parse_args()

    print(f"启动 MCP {args.transport.upper()} 服务器在端口 {args.port}...")
    if args.transport == 'stdio':
        return mcp.run(transport='stdio')
    else:
        return mcp.run(transport='sse', port=args.port)


if __name__ == "__main__":
    main()
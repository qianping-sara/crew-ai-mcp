"""
启动MCP StreamableHTTP服务器的简单脚本
"""
import os
import sys
from pathlib import Path

# 确保src目录在Python路径中
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# 导入服务器主函数
from streamable_http_server_main import main

if __name__ == "__main__":
    main() 
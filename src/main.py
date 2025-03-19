"""
MCP服务器主入口
导入所有模块并启动服务器
"""
# 导入MCP服务器实例
from .mcp_server import mcp

# 导入所有资源模块
from .resources import filesystem

# 导入所有工具模块
from .tools import calculator, user

# 导入所有提示模块
from .prompts import code_review, git_helper, api_design

def main():
    """启动MCP服务器"""
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main() 
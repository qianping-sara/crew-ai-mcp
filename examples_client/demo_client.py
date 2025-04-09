"""MCP HTTP client demo using MCP SDK.

此示例展示了如何连接到MCP服务器并使用其功能。
"""

import asyncio
import json
import sys
from typing import Any, Dict
from urllib.parse import urlparse

from mcp.client.session import ClientSession
from mcp.client.sse import sse_client


def print_items(name: str, result: Any) -> None:
    """打印项目列表，带有格式化。

    Args:
        name: 类别名称 (tools/resources/prompts)
        result: 包含项目列表的结果对象
    """
    print("", f"可用的 {name}:", sep="\n")
    items = getattr(result, name)
    if items:
        for item in items:
            print(" *", item.name)
    else:
        print("没有可用项目")


def extract_text_content(result: Any) -> str:
    """从工具返回值中提取文本内容。"""
    if hasattr(result, 'content') and result.content:
        for content in result.content:
            if hasattr(content, 'text'):
                return content.text
    return str(result)


async def test_calculator(session: ClientSession) -> None:
    """测试计算器工具。"""
    print("\n=== 测试计算器工具 ===")
    numbers = [1, 2, 3, 4, 5]
    
    try:
        # 测试求和
        result = await session.call_tool("calculate_sum", {"numbers": numbers})
        print(f"数字列表 {numbers} 的和为: {extract_text_content(result)}")
        
        # 测试平均值
        result = await session.call_tool("calculate_average", {"numbers": numbers})
        print(f"数字列表 {numbers} 的平均值为: {extract_text_content(result)}")
        
        # 测试统计信息
        result = await session.call_tool("calculate_stats", {"numbers": numbers})
        print(f"数字列表 {numbers} 的统计信息为: {extract_text_content(result)}")
    except Exception as e:
        print(f"计算器工具调用出错: {e}")


# async def test_filesystem(session: ClientSession) -> None:
#     """测试文件系统资源。"""
#     print("\n=== 测试文件系统资源 ===")
    
#     try:
#         # 列出当前目录内容
#         result = await session.read_resource("dir://.")
#         print("当前目录内容:")
#         if hasattr(result, 'contents') and result.contents:
#             for content in result.contents:
#                 if hasattr(content, 'text'):
#                     try:
#                         data = json.loads(content.text)
#                         print(data.get("content", "无内容"))
#                     except json.JSONDecodeError:
#                         print(content.text)
#         else:
#             print("无法读取目录内容")
#     except Exception as e:
#         print(f"文件系统资源访问出错: {e}")


async def test_prompts(session: ClientSession) -> None:
    """测试提示模板。"""
    print("\n=== 测试提示模板 ===")
    
    try:
        # 测试代码审查提示
        code = """
def add(a, b):
    return a + b
    """
        result = await session.get_prompt("review_code", {"code": code, "language": "python"})
        print("代码审查结果:")
        if hasattr(result, 'messages'):
            for msg in result.messages:
                if hasattr(msg, 'content') and hasattr(msg.content, 'text'):
                    print(msg.content.text)
        
        # 测试Git提交消息生成
        changes = "Added new calculator functionality"
        result = await session.get_prompt("generate_commit_message", {"diff": changes})
        print("\nGit提交消息:")
        if hasattr(result, 'messages'):
            for msg in result.messages:
                if hasattr(msg, 'content') and hasattr(msg.content, 'text'):
                    print(msg.content.text)
    except Exception as e:
        print(f"提示模板调用出错: {e}")


async def main(server_url: str):
    """连接到MCP服务器并测试其功能。

    Args:
        server_url: SSE端点的完整URL (例如 http://localhost:8000/sse)
    """
    if urlparse(server_url).scheme not in ("http", "https"):
        print("错误: 服务器URL必须以 http:// 或 https:// 开头")
        sys.exit(1)

    try:
        async with sse_client(server_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("已连接到MCP服务器:", server_url)
                
                # 列出所有可用功能
                print_items("tools", (await session.list_tools()))
                print_items("resources", (await session.list_resources()))
                print_items("prompts", (await session.list_prompts()))
                
                # 运行测试
                await test_calculator(session)
                # await test_filesystem(session)
                await test_prompts(session)

    except Exception as e:
        print(f"连接服务器时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python demo_client.py <server_url>")
        print("示例: python demo_client.py http://localhost:8000/sse")
        sys.exit(1)

    asyncio.run(main(sys.argv[1])) 
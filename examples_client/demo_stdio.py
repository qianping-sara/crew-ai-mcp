"""测试通过stdio方式连接MCP服务器的示例程序"""

import asyncio
import sys
import json
from typing import Any
from pathlib import Path
from contextlib import AsyncExitStack

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client
from mcp import StdioServerParameters

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

def print_resources(resources: Any) -> None:
    """打印资源列表
    
    Args:
        resources: 资源列表或内容
    """
    if hasattr(resources, 'contents') and resources.contents:
        # 处理结构化响应
        for content in resources.contents:
            if hasattr(content, 'text'):
                try:
                    # 尝试解析为JSON
                    data = json.loads(content.text)
                    if isinstance(data, dict) and "error" in data:
                        print(f"错误: {data['error']}")
                    else:
                        print(f"内容: {content.text}")
                except json.JSONDecodeError:
                    # 不是JSON，直接打印文本
                    print(content.text)
    else:
        # 兼容旧版代码中可能存在的情况
        if isinstance(resources, dict):
            if "error" in resources:
                print(f"错误: {resources['error']}")
            elif "content" in resources:
                print(f"文件内容 ({resources.get('type', '未知类型')}):")
                print("-" * 40)
                print(resources["content"])
                print("-" * 40)
            return
            
        if isinstance(resources, list):
            for resource in resources:
                type_str = "📁" if resource.get("type") == "inode/directory" else "📄"
                print(f" {type_str} {resource['name']} ({resource['uri']})")
                if "path" in resource:
                    print(f"   实际路径: {resource['path']}")
                if "type" in resource:
                    print(f"   类型: {resource['type']}")

async def test_filesystem(session: ClientSession) -> None:
    """测试文件系统资源"""
    print("\n=== 测试文件系统资源 ===")
    
    try:
        # 示例1：访问当前目录
        print(f"\n1. 访问当前目录")
        result = await session.read_resource(f"dir://.")
        print("目录内容:")
        print_resources(result)
            
        # 示例2：访问上级目录
        print(f"\n2. 访问上级目录")
        result = await session.read_resource(f"dir://..")
        print("目录内容:")
        print_resources(result)
            
        # 示例3：访问Python文件
        # print(f"\n3. 访问Python文件")
        # # 获取当前工作目录的绝对路径
        # cwd = Path.cwd()
        # # 构造文件的完整绝对路径
        # py_path = cwd / "src" / "resources" / "filesystem.py"
        # # 创建符合MCP规范的URI
        # file_uri = f"file://{py_path}"
        # print(f"尝试使用MCP规范URI: {file_uri}")
        # result = await session.read_resource(file_uri)
        # print_resources(result)
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")

async def main():
    """通过stdio方式连接到MCP服务器并测试功能"""
    try:
        print("正在启动MCP服务器...")
        # 创建服务器参数
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.main", "--transport", "stdio"],
            env=None,
            encoding='utf-8',
            cwd=str(Path.cwd())
        )
        
        print("正在通过stdio方式连接到MCP服务器...")
        async with stdio_client(server_params) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                print("已成功连接到MCP服务器")
                
                # 列出所有可用功能
                print("\n=== 列出所有可用功能 ===")
                print_items("tools", (await session.list_tools()))
                print_items("resources", (await session.list_resources()))
                print_items("prompts", (await session.list_prompts()))
                
                # 测试文件系统资源
                await test_filesystem(session)
                
    except Exception as e:
        print(f"连接服务器时出错: {e}")
        import traceback
        print(f"详细错误信息:\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 
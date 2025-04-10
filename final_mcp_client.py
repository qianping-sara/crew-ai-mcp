#!/usr/bin/env python
"""
最终MCP客户端 - 基于test_mini_flow.py的成功案例
"""
import requests
import json
import sys
import logging
import argparse
from urllib.parse import urlparse
import urllib3

# 禁用SSL警告
urllib3.disable_warnings()

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class McpClient:
    def __init__(self, url, proxy=None):
        self.url = url
        self.session_id = None
        self.session = requests.Session()
        self.session.verify = False
        if proxy:
            self.session.proxies = {'http': proxy, 'https': proxy}
    
    def initialize(self):
        """初始化会话"""
        print("初始化会话...")
        
        init_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "capabilities": {},
                "protocolVersion": "2025-03-26",
                "clientInfo": {
                    "name": "mcp-successful-client",
                    "version": "1.0.0"
                }
            },
            "id": "init1"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "mcp-successful-client/1.0"
        }
        
        try:
            response = self.session.post(
                self.url,
                json=init_data,
                headers=headers,
                timeout=30
            )
            
            print(f"初始化状态码: {response.status_code}")
            if response.status_code == 200:
                # 从响应头获取会话ID - 使用与服务器响应匹配的大小写
                session_id = response.headers.get("Mcp-Session-Id")
                if session_id:
                    self.session_id = session_id
                    print(f"获取到会话ID: {self.session_id}")
                    return True
                else:
                    print("错误: 未能获取会话ID")
                    return False
            else:
                print(f"初始化失败: {response.text}")
                return False
                
        except Exception as e:
            print(f"初始化异常: {e}")
            return False
    
    def list_tools(self):
        """列出可用工具"""
        if not self.session_id:
            print("错误: 未初始化会话")
            return []
            
        print(f"列出工具(会话ID: {self.session_id})...")
        
        tools_data = {
            "jsonrpc": "2.0",
            "method": "list_tools",
            "params": {},
            "id": "tools1"
        }
        
        # 使用与服务器响应匹配的大小写
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "mcp-successful-client/1.0",
            "Mcp-Session-Id": self.session_id
        }
        
        try:
            response = self.session.post(
                self.url,
                json=tools_data,
                headers=headers,
                timeout=30
            )
            
            print(f"列出工具状态码: {response.status_code}")
            if response.status_code == 200:
                try:
                    resp_data = response.json()
                    if "result" in resp_data and "tools" in resp_data["result"]:
                        tools = resp_data["result"]["tools"]
                        return tools
                    else:
                        print("响应格式异常，未找到工具列表")
                        return []
                except Exception as e:
                    print(f"解析工具列表出错: {e}")
                    return []
            else:
                print(f"列出工具失败: {response.text}")
                return []
                
        except Exception as e:
            print(f"列出工具异常: {e}")
            return []
    
    def call_tool(self, name, parameters):
        """调用工具"""
        if not self.session_id:
            print("错误: 未初始化会话")
            return None
            
        print(f"调用工具: {name}...")
        
        call_data = {
            "jsonrpc": "2.0",
            "method": "call_tool",
            "params": {
                "name": name,
                "parameters": parameters
            },
            "id": "call1"
        }
        
        # 使用与服务器响应匹配的大小写
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "mcp-successful-client/1.0",
            "Mcp-Session-Id": self.session_id
        }
        
        try:
            response = self.session.post(
                self.url,
                json=call_data,
                headers=headers,
                timeout=30
            )
            
            print(f"调用工具状态码: {response.status_code}")
            if response.status_code == 200:
                try:
                    return response.json()
                except Exception as e:
                    print(f"解析工具调用结果出错: {e}")
                    return None
            else:
                print(f"调用工具失败: {response.text}")
                return None
                
        except Exception as e:
            print(f"调用工具异常: {e}")
            return None

def main():
    parser = argparse.ArgumentParser(description="MCP客户端")
    parser.add_argument("url", help="MCP服务器URL")
    parser.add_argument("--proxy", help="HTTP代理地址")
    args = parser.parse_args()
    
    # 验证URL
    if not urlparse(args.url).scheme in ("http", "https"):
        print("错误: URL必须以http://或https://开头")
        sys.exit(1)
    
    client = McpClient(args.url, args.proxy)
    
    # 初始化
    if not client.initialize():
        print("初始化失败，退出")
        sys.exit(1)
    
    # 列出工具
    tools = client.list_tools()
    if tools:
        print("\n可用工具:")
        for tool in tools:
            print(f" * {tool.get('name')} - {tool.get('description', '无描述')}")
    else:
        print("无可用工具")
    
    # 测试计算器
    print("\n测试计算器工具...")
    numbers = [1, 2, 3, 4, 5]
    result = client.call_tool("calculate_sum", {"numbers": numbers})
    if result:
        print(f"计算结果: {json.dumps(result, indent=2)}")
    else:
        print("计算失败")

if __name__ == "__main__":
    main() 
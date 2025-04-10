#!/usr/bin/env python
"""
稳健型MCP客户端 - 能处理不稳定的会话状态
"""
import requests
import json
import sys
import logging
import argparse
import time
from urllib.parse import urlparse
import urllib3

# 禁用SSL警告
urllib3.disable_warnings()

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustMcpClient:
    def __init__(self, url, proxy=None, max_retries=3):
        self.url = url
        self.session_id = None
        self.session = requests.Session()
        self.session.verify = False
        self.max_retries = max_retries
        if proxy:
            self.session.proxies = {'http': proxy, 'https': proxy}
    
    def _reinitialize_if_needed(self):
        """如果当前没有会话ID，尝试重新初始化"""
        if not self.session_id:
            return self.initialize()
        return True
    
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
                    "name": "mcp-robust-client",
                    "version": "1.0.0"
                }
            },
            "id": "init1"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "mcp-robust-client/1.0"
        }
        
        for attempt in range(self.max_retries):
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
                        continue  # 尝试重试
                else:
                    print(f"初始化失败: {response.text}")
                    continue  # 尝试重试
                    
            except Exception as e:
                print(f"初始化异常: {e}")
                if attempt < self.max_retries - 1:
                    delay = (attempt + 1) * 2  # 递增延迟
                    print(f"将在{delay}秒后重试...")
                    time.sleep(delay)
                    
        print(f"初始化失败，已尝试{self.max_retries}次")
        return False
    
    def list_tools(self, auto_retry=True):
        """列出可用工具"""
        if not self._reinitialize_if_needed():
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
            "User-Agent": "mcp-robust-client/1.0",
            "Mcp-Session-Id": self.session_id
        }
        
        for attempt in range(self.max_retries):
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
                            continue  # 尝试重试
                    except Exception as e:
                        print(f"解析工具列表出错: {e}")
                        continue  # 尝试重试
                elif response.status_code == 400 and "会话ID无效" in response.text and auto_retry:
                    # 会话ID无效，尝试重新初始化
                    print("会话ID无效，尝试重新初始化...")
                    self.session_id = None  # 清除无效会话ID
                    if self.initialize():
                        # 重新初始化成功，重试此操作（不使用auto_retry避免无限循环）
                        return self.list_tools(auto_retry=False)
                    else:
                        print("重新初始化失败")
                        return []
                else:
                    print(f"列出工具失败: {response.text}")
                    continue  # 尝试重试
                    
            except Exception as e:
                print(f"列出工具异常: {e}")
                if attempt < self.max_retries - 1:
                    delay = (attempt + 1) * 2  # 递增延迟
                    print(f"将在{delay}秒后重试...")
                    time.sleep(delay)
        
        print(f"列出工具失败，已尝试{self.max_retries}次")
        return []
    
    def call_tool(self, name, parameters, auto_retry=True):
        """调用工具"""
        if not self._reinitialize_if_needed():
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
            "User-Agent": "mcp-robust-client/1.0",
            "Mcp-Session-Id": self.session_id
        }
        
        for attempt in range(self.max_retries):
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
                        continue  # 尝试重试
                elif response.status_code == 400 and "会话ID无效" in response.text and auto_retry:
                    # 会话ID无效，尝试重新初始化
                    print("会话ID无效，尝试重新初始化...")
                    self.session_id = None  # 清除无效会话ID
                    if self.initialize():
                        # 重新初始化成功，重试此操作（不使用auto_retry避免无限循环）
                        return self.call_tool(name, parameters, auto_retry=False)
                    else:
                        print("重新初始化失败")
                        return None
                else:
                    print(f"调用工具失败: {response.text}")
                    continue  # 尝试重试
                    
            except Exception as e:
                print(f"调用工具异常: {e}")
                if attempt < self.max_retries - 1:
                    delay = (attempt + 1) * 2  # 递增延迟
                    print(f"将在{delay}秒后重试...")
                    time.sleep(delay)
        
        print(f"调用工具失败，已尝试{self.max_retries}次")
        return None

def main():
    parser = argparse.ArgumentParser(description="稳健型MCP客户端")
    parser.add_argument("url", help="MCP服务器URL")
    parser.add_argument("--proxy", help="HTTP代理地址")
    parser.add_argument("--retries", type=int, default=3, help="最大重试次数")
    args = parser.parse_args()
    
    # 验证URL
    if not urlparse(args.url).scheme in ("http", "https"):
        print("错误: URL必须以http://或https://开头")
        sys.exit(1)
    
    client = RobustMcpClient(args.url, args.proxy, args.retries)
    
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
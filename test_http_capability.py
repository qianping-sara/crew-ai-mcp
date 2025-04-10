"""
测试HTTP能力和限制

测试各种HTTP请求类型和头部组合，帮助诊断Heroku服务器连接问题
"""
import requests
import argparse
import json
import time
import sys
from urllib.parse import urlparse

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
}

CLIENT_HEADERS = {
    "User-Agent": "mcp-test-client/1.0",
    "Accept": "application/json"
}

def test_capability(url, test_name, headers, timeout=10, method="GET", data=None):
    """测试特定HTTP能力"""
    print(f"\n===== 测试 {test_name} =====")
    print(f"请求: {method} {url}")
    print(f"头部: {json.dumps(headers, indent=2)}")
    if data:
        print(f"数据: {json.dumps(data, indent=2)}")
    
    start_time = time.time()
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        else:
            print(f"不支持的方法: {method}")
            return False
        
        duration = time.time() - start_time
        print(f"状态码: {response.status_code} (用时: {duration:.2f}秒)")
        print(f"响应头: {json.dumps(dict(response.headers), indent=2)}")
        
        if response.text:
            print(f"响应内容 (前200字符): {response.text[:200]}...")
            try:
                json_data = response.json()
                print(f"解析的JSON: {json.dumps(json_data, indent=2)[:200]}...")
            except:
                pass
        else:
            print("无响应内容")
        
        return response.status_code < 400
    except Exception as e:
        duration = time.time() - start_time
        print(f"错误: {e} (用时: {duration:.2f}秒)")
        return False

def run_tests(url):
    """运行一系列HTTP能力测试"""
    success_count = 0
    total_tests = 0
    
    # 测试1: 基本GET请求（浏览器头部）
    total_tests += 1
    if test_capability(url, "基本GET请求（浏览器头部）", BROWSER_HEADERS):
        success_count += 1
    
    # 测试2: 基本GET请求（客户端头部）
    total_tests += 1
    if test_capability(url, "基本GET请求（客户端头部）", CLIENT_HEADERS):
        success_count += 1
    
    # 测试3: JSON POST请求（浏览器头部）
    initialize_data = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "capabilities": {},
            "protocolVersion": "2025-03-26",
            "clientInfo": {
                "name": "capability-test",
                "version": "1.0.0"
            }
        },
        "id": "1"
    }
    
    total_tests += 1
    post_headers = BROWSER_HEADERS.copy()
    post_headers["Content-Type"] = "application/json"
    if test_capability(url, "JSON POST请求（浏览器头部）", post_headers, method="POST", data=initialize_data):
        success_count += 1
    
    # 测试4: JSON POST请求（客户端头部）
    total_tests += 1
    post_headers = CLIENT_HEADERS.copy()
    post_headers["Content-Type"] = "application/json"
    if test_capability(url, "JSON POST请求（客户端头部）", post_headers, method="POST", data=initialize_data):
        success_count += 1
    
    # 测试5: 长超时测试
    total_tests += 1
    if test_capability(url, "长超时测试（30秒）", BROWSER_HEADERS, timeout=30):
        success_count += 1
    
    # 测试6: 请求事件流
    total_tests += 1
    stream_headers = BROWSER_HEADERS.copy()
    stream_headers["Accept"] = "text/event-stream"
    if test_capability(url, "请求事件流", stream_headers):
        success_count += 1
    
    # 测试7: 维持会话测试
    # 首先获取会话ID
    session_id = None
    post_headers = BROWSER_HEADERS.copy()
    post_headers["Content-Type"] = "application/json"
    
    print("\n===== 测试 会话维持能力 =====")
    try:
        response = requests.post(url, headers=post_headers, json=initialize_data, timeout=10)
        if response.status_code == 200:
            session_id = response.headers.get("mcp-session-id")
            if session_id:
                print(f"获取到会话ID: {session_id}")
                
                # 使用会话ID发送第二个请求
                second_request = {
                    "jsonrpc": "2.0", 
                    "method": "list_tools", 
                    "id": "2"
                }
                
                session_headers = post_headers.copy()
                session_headers["mcp-session-id"] = session_id
                
                response2 = requests.post(url, headers=session_headers, json=second_request, timeout=10)
                print(f"会话请求状态码: {response2.status_code}")
                print(f"会话请求响应: {response2.text[:200]}...")
                
                if response2.status_code == 200:
                    success_count += 1
                    print("会话维持测试成功")
                else:
                    print("会话维持测试失败")
            else:
                print("未获取到会话ID")
        else:
            print(f"初始化请求失败，状态码: {response.status_code}")
    except Exception as e:
        print(f"会话维持测试失败: {e}")
    
    total_tests += 1
    
    # 结果统计
    print(f"\n===== 测试结果统计 =====")
    print(f"总测试数: {total_tests}")
    print(f"成功测试: {success_count}")
    print(f"失败测试: {total_tests - success_count}")
    print(f"成功率: {success_count / total_tests * 100:.1f}%")
    
    return success_count == total_tests

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试HTTP能力和限制")
    parser.add_argument("url", help="要测试的URL")
    args = parser.parse_args()
    
    # 验证URL格式
    if not urlparse(args.url).scheme in ("http", "https"):
        print("错误: URL必须以 http:// 或 https:// 开头")
        sys.exit(1)
    
    if run_tests(args.url):
        print("\n✅ 所有测试通过")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1) 
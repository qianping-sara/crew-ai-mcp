"""
简单的Heroku连接测试脚本，使用requests而非aiohttp
"""
import sys
import json
import requests
from urllib.parse import urlparse

def test_heroku_connection(url):
    """
    使用requests库测试连接到Heroku部署的MCP服务器
    """
    print(f"测试连接到Heroku: {url}")
    
    # 准备浏览器风格的头部
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }
    
    # 1. 测试GET请求
    try:
        print("发送GET请求测试基本连接...")
        response = requests.get(url, headers=headers, timeout=30)
        print(f"GET响应: HTTP {response.status_code}")
        print(f"响应内容: {response.text[:200]}...")
    except Exception as e:
        print(f"GET请求失败: {e}")
        return False
    
    # 2. 测试POST请求 - 初始化
    try:
        print("\n发送POST请求初始化MCP连接...")
        headers["Content-Type"] = "application/json"
        
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "capabilities": {},
                "protocolVersion": "2025-03-26",
                "clientInfo": {
                    "name": "simple-test-client",
                    "version": "1.0.0"
                }
            },
            "id": "test-1"
        }
        
        response = requests.post(
            url, 
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        print(f"POST响应: HTTP {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.text:
            print(f"响应内容: {response.text[:500]}...")
            try:
                data = response.json()
                print("成功解析JSON响应")
                session_id = response.headers.get("mcp-session-id")
                if session_id:
                    print(f"会话ID: {session_id}")
                return True
            except json.JSONDecodeError as e:
                print(f"无法解析JSON: {e}")
        else:
            print("服务器返回了空响应")
            
    except Exception as e:
        print(f"POST请求失败: {e}")
    
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <Heroku应用URL>")
        print(f"例如: {sys.argv[0]} https://your-app.herokuapp.com/mcp")
        sys.exit(1)
    
    url = sys.argv[1]
    
    # 验证URL格式
    if not urlparse(url).scheme in ("http", "https"):
        print("错误: URL必须以 http:// 或 https:// 开头")
        sys.exit(1)
    
    try:
        success = test_heroku_connection(url)
        if success:
            print("\n✅ 连接成功!")
            sys.exit(0)
        else:
            print("\n❌ 连接失败!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1) 
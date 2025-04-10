"""
StreamableHTTP MCP服务器启动脚本
"""
import os
import sys
import uvicorn

def main():
    """启动MCP StreamableHTTP服务器"""
    # 从环境变量获取端口，默认为3000
    # Heroku会提供PORT环境变量
    port = int(os.environ.get("PORT", 3000))
    print(f"启动 MCP StreamableHTTP 服务器在端口 {port}...")
    
    # 使用字符串形式指定应用程序，这在Heroku环境中是必需的
    # 这样可以正确设置workers和reload选项
    uvicorn.run("src.streamable_http_server:app", 
               host="0.0.0.0", 
               port=port, 
               log_level="info")

if __name__ == "__main__":
    main() 
"""
StreamableHTTP MCP服务器启动脚本
"""
import os
import uvicorn
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))

# 现在可以正确导入模块
from src.streamable_http_server import app

def main():
    """启动MCP StreamableHTTP服务器"""
    # 从环境变量获取端口，默认为3000
    # Heroku会提供PORT环境变量
    port = int(os.environ.get("PORT", 3000))
    print(f"启动 MCP StreamableHTTP 服务器在端口 {port}...")
    
    # 启动FastAPI应用，使用0.0.0.0绑定所有接口，这对Heroku是必需的
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main() 
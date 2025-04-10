"""
简化的MCP调试客户端
用于测试与服务器的连接
"""
import sys
import json
import asyncio
import aiohttp
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_connection(url: str, use_sse: bool = True):
    """测试与MCP服务器的连接"""
    logger.info(f"测试连接到: {url} (使用SSE: {use_sse})")
    
    # 准备请求数据
    request_data = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "capabilities": {},
            "protocolVersion": "2025-03-26",
            "clientInfo": {
                "name": "debug-client",
                "version": "1.0.0"
            }
        },
        "id": "debug-1"
    }
    
    # 准备请求头
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json" if not use_sse else "text/event-stream"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.debug(f"发送请求: {json.dumps(request_data)}")
            logger.debug(f"请求头: {headers}")
            
            async with session.post(url, json=request_data, headers=headers) as response:
                logger.info(f"收到响应: HTTP {response.status}")
                logger.info(f"响应头: {response.headers}")
                
                session_id = response.headers.get("mcp-session-id")
                if session_id:
                    logger.info(f"会话ID: {session_id}")
                else:
                    logger.warning("未收到会话ID")
                
                content_type = response.headers.get("content-type", "未知")
                logger.info(f"内容类型: {content_type}")
                
                if content_type.startswith("text/event-stream"):
                    # 读取SSE流
                    logger.info("读取SSE流...")
                    async for line in response.content:
                        line_text = line.decode("utf-8", errors="replace")
                        logger.info(f"SSE行: {line_text.strip()}")
                        if line_text.startswith("data:"):
                            try:
                                data = json.loads(line_text[5:].strip())
                                logger.info(f"解析的JSON: {json.dumps(data, indent=2)}")
                            except json.JSONDecodeError as e:
                                logger.error(f"无法解析JSON: {e}")
                else:
                    # 读取JSON响应
                    try:
                        text = await response.text()
                        logger.info(f"响应内容: {text[:200]}...")
                        if text.strip():
                            try:
                                data = json.loads(text)
                                logger.info(f"解析的JSON: {json.dumps(data, indent=2)}")
                            except json.JSONDecodeError as e:
                                logger.error(f"无法解析JSON: {e}")
                        else:
                            logger.warning("空响应内容")
                    except Exception as e:
                        logger.error(f"读取响应失败: {e}")
    
    except Exception as e:
        logger.error(f"连接测试失败: {e}", exc_info=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <服务器URL> [--json]")
        sys.exit(1)
    
    url = sys.argv[1]
    use_sse = "--json" not in sys.argv
    
    asyncio.run(test_connection(url, use_sse)) 
"""
Heroku连接测试脚本

使用简单的HTTP请求测试与Heroku部署的MCP服务器的连接
"""
import sys
import json
import asyncio
import aiohttp
import logging
from urllib.parse import urlparse
import time

# 启用详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_heroku_connection(url: str, retries: int = 3, timeout: int = 30):
    """测试与Heroku部署的MCP服务器的连接"""
    logger.info(f"测试连接到Heroku: {url}")
    
    # 准备请求数据
    request_data = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "capabilities": {},
            "protocolVersion": "2025-03-26",
            "clientInfo": {
                "name": "heroku-test-client",
                "version": "1.0.0"
            }
        },
        "id": "test-1"
    }
    
    # 设置超时时间较长
    timeout_obj = aiohttp.ClientTimeout(total=timeout)
    
    # 多次尝试连接
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"尝试 {attempt}/{retries}...")
            
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                # 先发送GET请求，测试基本连接
                logger.info("发送GET请求测试基本连接...")
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                    "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Connection": "keep-alive"
                }
                
                async with session.get(
                    url,
                    allow_redirects=True,
                    headers=headers
                ) as response:
                    logger.info(f"GET响应: HTTP {response.status}")
                    text = await response.text()
                    logger.info(f"响应内容: {text[:200]}...")
                
                # 发送POST请求初始化MCP连接
                logger.info("发送POST请求初始化MCP连接...")
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache"
                }
                
                async with session.post(
                    url, 
                    json=request_data,
                    headers=headers
                ) as response:
                    logger.info(f"POST响应: HTTP {response.status}")
                    logger.info(f"响应头: {response.headers}")
                    
                    try:
                        text = await response.text()
                        logger.info(f"响应内容: {text[:500]}...")
                        
                        if text.strip():
                            try:
                                data = json.loads(text)
                                logger.info("成功解析JSON响应")
                                return True
                            except json.JSONDecodeError as e:
                                logger.warning(f"无法解析JSON: {e}")
                    except Exception as e:
                        logger.error(f"读取响应失败: {e}")
            
            # 如果我们到达这里但没有成功返回，等待一会再重试
            if attempt < retries:
                wait_time = 2 ** attempt  # 指数退避
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
        
        except aiohttp.ClientConnectorError as e:
            logger.error(f"连接错误: {e}")
            if attempt < retries:
                wait_time = 2 ** attempt
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
        
        except asyncio.TimeoutError:
            logger.error(f"连接超时 ({timeout}秒)")
            if attempt < retries:
                # 增加下一次尝试的超时时间
                timeout = int(timeout * 1.5)
                timeout_obj = aiohttp.ClientTimeout(total=timeout)
                logger.info(f"增加超时时间到 {timeout} 秒并重试...")
                await asyncio.sleep(2)
        
        except Exception as e:
            logger.error(f"意外错误: {e}", exc_info=True)
            if attempt < retries:
                wait_time = 2 ** attempt
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
    
    logger.error(f"连接测试失败，已尝试 {retries} 次")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"用法: {sys.argv[0]} <Heroku应用URL> [超时时间]")
        print(f"例如: {sys.argv[0]} https://your-app.herokuapp.com/mcp 60")
        sys.exit(1)
    
    url = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    # 验证URL格式
    if not urlparse(url).scheme in ("http", "https"):
        print("错误: URL必须以 http:// 或 https:// 开头")
        sys.exit(1)
    
    try:
        start_time = time.time()
        success = asyncio.run(test_heroku_connection(url, retries=3, timeout=timeout))
        end_time = time.time()
        
        if success:
            print(f"✅ 连接成功! 总耗时: {end_time - start_time:.2f}秒")
            sys.exit(0)
        else:
            print(f"❌ 连接失败! 总耗时: {end_time - start_time:.2f}秒")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(130)
    
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        sys.exit(1) 
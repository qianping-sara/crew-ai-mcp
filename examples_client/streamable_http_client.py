"""
StreamableHTTP MCP客户端示例

此示例展示如何使用HTTP连接到MCP服务器，
支持JSON响应和流式响应两种模式。
"""

import sys
import json
import asyncio
import argparse
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
import aiohttp
import logging
from urllib.parse import urlparse

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StreamableHttpClient:
    """实现MCP StreamableHTTP客户端"""
    
    def __init__(
        self, 
        server_url: str, 
        use_streaming: bool = True,
        client_info: Dict[str, str] = None
    ):
        """
        初始化MCP客户端
        
        Args:
            server_url: MCP服务器URL (例如: http://localhost:3000/mcp)
            use_streaming: 是否使用流式响应模式
            client_info: 客户端信息
        """
        self.server_url = server_url
        self.use_streaming = use_streaming
        self.session_id: Optional[str] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.client_info = client_info or {
            "name": "mcp-streamable-http-client", 
            "version": "1.0.0"
        }
        self.server_capabilities: Dict[str, Any] = {}
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.http_session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.http_session:
            await self.http_session.close()
    
    async def initialize(self) -> Dict[str, Any]:
        """初始化MCP会话"""
        if self.http_session is None:
            # 创建更接近浏览器行为的连接器
            tcp_connector = aiohttp.TCPConnector(
                ssl=False,  # 禁用SSL验证
                force_close=False,  # 允许连接复用
                limit=10,  # 限制连接数
                ttl_dns_cache=300  # DNS缓存时间
            )
            
            self.http_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60),  # 增加超时时间到60秒
                connector=tcp_connector
            )
            
        # 准备初始化请求
        request_data = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "capabilities": {},
                "protocolVersion": "2025-03-26",
                "clientInfo": self.client_info
            },
            "id": "1"
        }
        
        # 准备请求头 - 模拟浏览器请求
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        if self.use_streaming:
            headers["Accept"] = "text/event-stream"
            
        # 发送初始化请求
        try:
            logger.info(f"连接到服务器: {self.server_url}")
            async with self.http_session.post(
                self.server_url, 
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)  # 明确指定此请求的超时
            ) as response:
                # 检查响应状态
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"初始化失败: HTTP {response.status} - {error_text}")
                
                # 获取会话ID
                self.session_id = response.headers.get("mcp-session-id")
                if not self.session_id:
                    raise Exception("服务器未返回会话ID")
                
                logger.info(f"已初始化MCP会话: {self.session_id}")
                
                # 处理响应
                if self.use_streaming and response.headers.get("content-type", "").startswith("text/event-stream"):
                    # 流式响应处理
                    async for event in self._parse_sse_stream(response):
                        if "result" in event:
                            if "serverInfo" in event["result"]:
                                self.server_capabilities = event["result"].get("capabilities", {})
                                logger.info(f"已连接到MCP服务器: {event['result']['serverInfo']}")
                                return event["result"]
                else:
                    # JSON响应处理
                    try:
                        result = await response.json()
                        if "result" in result:
                            if "serverInfo" in result["result"]:
                                self.server_capabilities = result["result"].get("capabilities", {})
                                logger.info(f"已连接到MCP服务器: {result['result']['serverInfo']}")
                                return result["result"]
                        if "error" in result:
                            raise Exception(f"MCP错误: {result['error']}")
                        return result
                    except aiohttp.ContentTypeError as e:
                        # 处理Content-Type不是application/json的情况
                        text = await response.text()
                        logger.warning(f"响应Content-Type不是JSON: {response.headers.get('content-type', '未知')}")
                        if text.strip():
                            logger.warning(f"响应内容: {text[:100]}...")
                            try:
                                # 尝试手动解析JSON
                                result = json.loads(text)
                                if "result" in result:
                                    if "serverInfo" in result["result"]:
                                        self.server_capabilities = result["result"].get("capabilities", {})
                                        logger.info(f"已连接到MCP服务器: {result['result']['serverInfo']}")
                                        return result["result"]
                                return result
                            except json.JSONDecodeError:
                                # 如果无法解析，则抛出原始错误
                                raise Exception(f"响应不是有效的JSON格式: {str(e)}")
                        else:
                            raise Exception("服务器返回了空响应")
        except Exception as e:
            logger.error(f"初始化时出错: {str(e)}")
            raise
    
    async def _parse_sse_stream(self, response: aiohttp.ClientResponse) -> AsyncGenerator[Dict[str, Any], None]:
        """解析SSE流响应"""
        buffer = ""
        try:
            async for line in response.content:
                decoded_line = line.decode('utf-8', errors='replace')
                logger.debug(f"收到SSE行: {decoded_line.strip()}")
                buffer += decoded_line
                
                if buffer.endswith('\n\n') or '\n\n' in buffer:
                    # 完整的SSE事件
                    events = buffer.split('\n\n')
                    # 保留最后一个不完整的事件（如果有）
                    if not buffer.endswith('\n\n'):
                        buffer = events.pop()
                    else:
                        buffer = ""
                    
                    for event in events:
                        if event.strip():
                            # 查找data行
                            data_line = None
                            for line in event.split('\n'):
                                if line.startswith('data:'):
                                    data_line = line
                                    break
                            
                            if data_line:
                                data_str = data_line[5:].strip()  # 移除'data:'前缀
                                try:
                                    data = json.loads(data_str)
                                    logger.debug(f"解析SSE事件: {data}")
                                    yield data
                                except json.JSONDecodeError as e:
                                    logger.warning(f"无法解析SSE事件 '{data_str}': {e}")
                            else:
                                logger.warning(f"SSE事件没有data行: {event}")
        except Exception as e:
            logger.error(f"解析SSE流时出错: {e}")
            raise
    
    async def send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送MCP请求并获取响应"""
        if not self.session_id:
            raise Exception("会话未初始化，请先调用initialize()")
            
        if self.http_session is None:
            raise Exception("HTTP会话已关闭")
            
        # 准备请求数据
        request_id = str(hash(f"{method}_{params}_{asyncio.get_event_loop().time()}") % 1000000)
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": request_id
        }
        
        logger.info(f"发送请求: {method}, ID={request_id}")
        
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "mcp-session-id": self.session_id,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache"
        }
        
        if self.use_streaming:
            headers["Accept"] = "text/event-stream"
            
        # 发送请求
        try:
            # 使用重试机制
            retries = 3
            for attempt in range(1, retries + 1):
                try:
                    logger.info(f"尝试 {attempt}/{retries}...")
                    async with self.http_session.post(
                        self.server_url,
                        json=request_data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as response:
                        # 检查响应状态
                        if response.status != 200:
                            error_text = await response.text()
                            raise Exception(f"请求失败: HTTP {response.status} - {error_text}")
                        
                        content_type = response.headers.get('content-type', '未知')
                        logger.info(f"收到响应: 状态={response.status}, Content-Type={content_type}")
                        
                        # 处理响应
                        if content_type.startswith("text/event-stream"):
                            # 流式响应处理
                            logger.info("处理流式响应...")
                            event_received = False
                            async for event in self._parse_sse_stream(response):
                                event_received = True
                                logger.info(f"收到SSE事件: {json.dumps(event)[:100]}...")
                                if "result" in event:
                                    return event
                                elif "error" in event:
                                    raise Exception(f"MCP错误: {event['error']}")
                            
                            if not event_received:
                                if attempt < retries:
                                    wait_time = 2 ** attempt
                                    logger.warning(f"未收到任何事件，{wait_time}秒后重试...")
                                    await asyncio.sleep(wait_time)
                                    continue
                                else:
                                    raise Exception("流式响应未返回任何事件")
                        else:
                            # JSON响应处理
                            try:
                                result = await response.text()
                                logger.info(f"收到JSON响应: {result[:200]}...")
                                if not result.strip():
                                    raise Exception("服务器返回了空响应")
                                
                                result_obj = json.loads(result)
                                if "error" in result_obj:
                                    raise Exception(f"MCP错误: {result_obj['error']}")
                                return result_obj
                            except aiohttp.ContentTypeError as e:
                                # 处理Content-Type不是application/json的情况
                                text = await response.text()
                                logger.warning(f"响应Content-Type不是JSON: {content_type}")
                                if text.strip():
                                    logger.info(f"尝试手动解析响应内容: {text[:200]}...")
                                    try:
                                        # 尝试手动解析JSON
                                        result = json.loads(text)
                                        return result
                                    except json.JSONDecodeError:
                                        logger.error(f"响应不是有效的JSON: {text}")
                                        if attempt < retries:
                                            wait_time = 2 ** attempt
                                            logger.warning(f"解析失败，{wait_time}秒后重试...")
                                            await asyncio.sleep(wait_time)
                                            continue
                                        # 如果无法解析，则抛出原始错误
                                        raise Exception(f"响应不是有效的JSON格式: {str(e)}")
                                else:
                                    logger.error("服务器返回了空响应内容")
                                    if attempt < retries:
                                        wait_time = 2 ** attempt
                                        logger.warning(f"收到空响应，{wait_time}秒后重试...")
                                        await asyncio.sleep(wait_time)
                                        continue
                                    raise Exception("服务器返回了空响应")
                    
                    # 如果执行到这里，说明请求成功，跳出重试循环
                    break
                    
                except (aiohttp.ClientConnectorError, asyncio.TimeoutError) as e:
                    if attempt < retries:
                        wait_time = 2 ** attempt
                        logger.warning(f"连接错误: {e}, {wait_time}秒后重试...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"连接失败，已重试{retries}次: {e}")
                        raise Exception(f"连接到服务器失败: {str(e)}")
        except Exception as e:
            logger.error(f"请求 {method} 时出错: {str(e)}")
            raise
    
    async def list_tools(self) -> List[Dict[str, str]]:
        """获取可用工具列表"""
        result = await self.send_request("list_tools")
        return result.get("result", {}).get("tools", [])
    
    async def list_resources(self) -> List[Dict[str, str]]:
        """获取可用资源列表"""
        result = await self.send_request("list_resources")
        return result.get("result", {}).get("resources", [])
    
    async def list_prompts(self) -> List[Dict[str, str]]:
        """获取可用提示模板列表"""
        result = await self.send_request("list_prompts")
        return result.get("result", {}).get("prompts", [])
    
    async def call_tool(self, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        result = await self.send_request("call_tool", {
            "name": name,
            "parameters": parameters
        })
        return result
    
    async def get_prompt(self, name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """获取提示模板"""
        result = await self.send_request("get_prompt", {
            "name": name,
            "parameters": parameters
        })
        return result
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """读取资源"""
        result = await self.send_request("read_resource", {
            "uri": uri
        })
        return result


async def print_items(name: str, items: List[Dict[str, str]]) -> None:
    """打印项目列表，带有格式化"""
    print("", f"可用的 {name}:", sep="\n")
    if items:
        for item in items:
            print(" *", item.get("name"), "-", item.get("description", "无描述"))
    else:
        print("没有可用项目")


async def test_calculator(client: StreamableHttpClient) -> None:
    """测试计算器工具"""
    print("\n=== 测试计算器工具 ===")
    numbers = [1, 2, 3, 4, 5]
    
    try:
        # 测试求和
        result = await client.call_tool("calculate_sum", {"numbers": numbers})
        content = result.get("result", {}).get("content", [])
        text = next((item.get("text") for item in content if item.get("type") == "text"), "无结果")
        print(f"数字列表 {numbers} 的和为: {text}")
    except Exception as e:
        print(f"计算器工具调用出错: {e}")


async def main() -> None:
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP StreamableHTTP 客户端示例")
    parser.add_argument("server_url", help="MCP服务器URL (例如: http://localhost:3000/mcp)")
    parser.add_argument("--json", action="store_true", help="使用JSON响应模式而非流式响应")
    args = parser.parse_args()
    
    # 验证URL格式
    if not urlparse(args.server_url).scheme in ("http", "https"):
        print("错误: 服务器URL必须以 http:// 或 https:// 开头")
        sys.exit(1)
    
    try:
        # 创建客户端
        async with StreamableHttpClient(
            server_url=args.server_url,
            use_streaming=not args.json
        ) as client:
            # 初始化会话
            await client.initialize()
            
            # 列出所有可用功能
            print("\n=== 可用功能 ===")
            await print_items("工具", await client.list_tools())
            await print_items("资源", await client.list_resources())
            await print_items("提示模板", await client.list_prompts())
            
            # 测试工具
            await test_calculator(client)
    
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n已退出")
    except Exception as e:
        print(f"未处理的错误: {e}")
        sys.exit(1) 
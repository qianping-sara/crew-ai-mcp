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
import os

# 日志配置
logging.basicConfig(
    level=logging.DEBUG,  # 使用DEBUG级别记录更多信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StreamableHttpClient:
    """实现MCP StreamableHTTP客户端"""
    
    def __init__(
        self, 
        server_url: str, 
        use_streaming: bool = False,
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
        self.session_id = None
        self.request_id = 0
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=120)  # 增加超时时间到120秒
        self.client_info = client_info or {
            "name": "mcp-streamable-http-client", 
            "version": "1.0.0"
        }
        self.server_capabilities: Dict[str, Any] = {}
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    async def initialize(self) -> Dict[str, Any]:
        """初始化MCP会话"""
        if self.session is None:
            # 创建更接近浏览器行为的连接器
            connector_options = {
                "ssl": False,  # 禁用SSL验证
                "force_close": False,
                "enable_cleanup_closed": True
            }
            
            # 添加代理支持
            proxy = os.environ.get("HTTP_PROXY")
            if proxy:
                logger.info(f"使用代理: {proxy}")
                connector_options["proxy"] = proxy
                
            tcp_connector = aiohttp.TCPConnector(**connector_options)
            
            self.session = aiohttp.ClientSession(
                timeout=self.timeout,
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
            logger.info(f"请求头: {headers}")
            logger.info(f"请求体: {json.dumps(request_data)}")
            
            async with self.session.post(
                self.server_url, 
                json=request_data,
                headers=headers,
                timeout=self.timeout  # 明确指定此请求的超时
            ) as response:
                # 检查响应状态
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"初始化失败: HTTP {response.status} - {error_text}")
                
                # 获取会话ID
                self.session_id = response.headers.get("Mcp-Session-Id") or response.headers.get("mcp-session-id")
                logger.info(f"响应头: {dict(response.headers)}")
                
                if not self.session_id:
                    logger.warning("服务器未返回会话ID")
                    raise Exception("服务器未返回会话ID")
                
                logger.info(f"已获取会话ID: {self.session_id}")
                
                content_type = response.headers.get("content-type", "未知")
                logger.info(f"响应类型: {content_type}")
                
                # 处理响应
                if content_type.startswith("text/event-stream"):
                    # 流式响应处理
                    logger.info("接收流式响应...")
                    received_data = False
                    async for event in self._parse_sse_stream(response):
                        received_data = True
                        logger.info(f"收到SSE事件: {json.dumps(event)[:200]}...")
                        if "result" in event:
                            logger.info("解析服务器信息")
                            if "serverInfo" in event["result"]:
                                self.server_capabilities = event["result"].get("capabilities", {})
                                logger.info(f"已连接到MCP服务器: {event['result']['serverInfo']}")
                                return event["result"]
                            return event["result"]
                    
                    if not received_data:
                        raise Exception("流式响应中没有收到数据")
                else:
                    # JSON响应处理
                    logger.info("接收JSON响应...")
                    raw_text = await response.text()
                    logger.info(f"原始响应: {raw_text[:200]}...")
                    
                    if not raw_text.strip():
                        raise Exception("服务器返回了空响应")
                    
                    try:
                        # 尝试解析JSON
                        result = json.loads(raw_text)
                        logger.info(f"解析JSON成功: {json.dumps(result)[:200]}...")
                        
                        if "result" in result:
                            if "serverInfo" in result["result"]:
                                self.server_capabilities = result["result"].get("capabilities", {})
                                logger.info(f"已连接到MCP服务器: {result['result']['serverInfo']}")
                                return result["result"]
                            return result["result"]
                        elif "error" in result:
                            raise Exception(f"MCP错误: {result['error']}")
                        
                        return result
                    except json.JSONDecodeError as e:
                        logger.error(f"无法解析JSON: {e}")
                        raise Exception(f"无法解析服务器响应: {e} - {raw_text[:100]}")
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
    
    async def send_request(self, method: str, params: Dict[str, Any] = None, retries: int = 3) -> Dict[str, Any]:
        """发送请求到MCP服务器
        
        Args:
            method: 请求方法
            params: 请求参数
            retries: 重试次数
        
        Returns:
            响应数据
        """
        if method != "initialize" and not self.session_id:
            raise Exception("会话未初始化，请先调用initialize()")
            
        if self.session is None:
            raise Exception("HTTP会话已关闭")
            
        # 准备请求数据
        self.request_id = str(hash(f"{method}_{params}_{asyncio.get_event_loop().time()}") % 1000000)
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": self.request_id
        }
        
        logger.info(f"发送请求: {method}, ID={self.request_id}")
        
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache", 
            "Pragma": "no-cache"
        }
        
        # 添加会话ID (如果已初始化)
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
            logger.debug(f"使用会话ID: {self.session_id}")
        
        if self.use_streaming:
            # 流式响应模式
            logger.info("使用流式响应模式")
            raise NotImplementedError("流式响应模式尚未实现")
        else:
            # JSON响应模式
            # 这里使用重试机制来处理临时网络问题
            for attempt in range(1, retries + 1):
                try:
                    logger.info(f"尝试 {attempt}/{retries}...")
                    async with self.session.post(
                        self.server_url,
                        json=request_data,
                        headers=headers,
                        timeout=self.timeout
                    ) as response:
                        # 检查响应状态
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"HTTP错误 {response.status}: {error_text}")
                            raise Exception(f"HTTP错误 {response.status}: {error_text}")
                        
                        # 获取并处理响应数据
                        logger.debug(f"收到响应: HTTP {response.status}")
                        
                        # 检查并更新会话ID
                        if "Mcp-Session-Id" in response.headers or "mcp-session-id" in response.headers:
                            new_session_id = response.headers.get("Mcp-Session-Id") or response.headers.get("mcp-session-id")
                            if not self.session_id:
                                self.session_id = new_session_id
                                logger.info(f"会话ID已设置: {self.session_id}")
                            elif self.session_id != new_session_id:
                                logger.warning(f"会话ID已更改: {self.session_id} -> {new_session_id}")
                                self.session_id = new_session_id
                        
                        # 解析JSON响应
                        try:
                            json_response = await response.json()
                            logger.debug(f"响应数据: {json.dumps(json_response)[:200]}...")
                            
                            # 检查错误
                            if "error" in json_response:
                                error = json_response["error"]
                                logger.error(f"RPC错误: {error}")
                                raise Exception(f"RPC错误: {error}")
                            
                            return json_response
                        except json.JSONDecodeError:
                            text = await response.text()
                            logger.error(f"无效的JSON响应: {text[:200]}...")
                            raise Exception(f"无效的JSON响应: {text[:200]}...")
                            
                except asyncio.TimeoutError:
                    logger.error(f"请求超时（尝试 {attempt}/{retries}）")
                    if attempt == retries:
                        raise Exception(f"请求多次超时，已放弃")
                except aiohttp.ClientError as e:
                    logger.error(f"HTTP客户端错误: {e}")
                    if attempt == retries:
                        raise Exception(f"HTTP客户端错误: {e}")
                
                # 如果需要重试，添加延迟
                if attempt < retries:
                    delay = 1 * attempt  # 递增延迟
                    logger.info(f"等待 {delay} 秒后重试...")
                    await asyncio.sleep(delay)
            
            raise Exception("所有请求尝试均失败")
    
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

async def main_with_args(server_url: str, use_streaming: bool = False) -> None:
    """带参数的主函数"""
    try:
        # 创建客户端
        async with StreamableHttpClient(
            server_url=server_url,
            use_streaming=use_streaming
        ) as client:
            print("客户端创建完成，开始初始化...")
            # 初始化会话
            try:
                result = await client.initialize()
                print(f"初始化成功: {json.dumps(result)[:200]}...")
                
                # 列出所有可用功能
                print("\n=== 可用功能 ===")
                try:
                    tools = await client.list_tools()
                    await print_items("工具", tools)
                except Exception as e:
                    print(f"获取工具列表失败: {e}")
                
                try:
                    resources = await client.list_resources()
                    await print_items("资源", resources)
                except Exception as e:
                    print(f"获取资源列表失败: {e}")
                
                try:
                    prompts = await client.list_prompts()
                    await print_items("提示模板", prompts)
                except Exception as e:
                    print(f"获取提示模板列表失败: {e}")
                
                # 测试工具
                try:
                    await test_calculator(client)
                except Exception as e:
                    print(f"测试计算器工具失败: {e}")
            except Exception as e:
                print(f"初始化失败: {e}")
                raise
    
    except Exception as e:
        print(f"错误: {e}")
        raise 

if __name__ == "__main__":
    try:
        # 设置更详细的日志级别
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 启用HTTP客户端调试
        aiohttp_logger = logging.getLogger('aiohttp')
        aiohttp_logger.setLevel(logging.DEBUG)
        
        # 默认使用JSON响应模式而非流式响应
        parser = argparse.ArgumentParser(description="MCP StreamableHTTP 客户端示例")
        parser.add_argument("server_url", help="MCP服务器URL (例如: http://localhost:3000/mcp)")
        parser.add_argument("--stream", action="store_true", help="使用流式响应模式而非JSON响应")
        parser.add_argument("--proxy", help="HTTP代理地址 (例如: http://127.0.0.1:7890)")
        args = parser.parse_args()
        
        # 验证URL格式
        if not urlparse(args.server_url).scheme in ("http", "https"):
            print("错误: 服务器URL必须以 http:// 或 https:// 开头")
            sys.exit(1)
            
        print(f"连接到: {args.server_url} (使用{'流式' if args.stream else 'JSON'}响应模式)")
        if args.proxy:
            print(f"使用代理: {args.proxy}")
            # 设置全局代理环境变量
            os.environ["HTTP_PROXY"] = args.proxy
            os.environ["HTTPS_PROXY"] = args.proxy
            
        # 创建客户端，默认使用JSON模式
        asyncio.run(main_with_args(args.server_url, use_streaming=args.stream))
    except KeyboardInterrupt:
        print("\n已退出")
    except Exception as e:
        print(f"未处理的错误: {e}")
        sys.exit(1) 
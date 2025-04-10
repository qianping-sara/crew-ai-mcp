"""
StreamableHTTP MCP服务器
提供基于HTTP的流式通信功能，支持JSON响应模式
"""
from typing import Dict, Optional, Any, List, Union
import json
import uuid
import logging
import asyncio
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入MCP服务器实例
try:
    from src.mcp_server import mcp
    from src.resources import filesystem
    from src.tools import calculator, user
    from src.prompts import code_review, git_helper, api_design
except ImportError:
    # 如果上面的导入失败，尝试相对导入(本地开发环境)
    from .mcp_server import mcp
    from .resources import filesystem
    from .tools import calculator, user
    from .prompts import code_review, git_helper, api_design

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="MCP StreamableHTTP Server")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头部
)

# 会话存储
sessions: Dict[str, Dict[str, Any]] = {}

class MCPRequest(BaseModel):
    jsonrpc: str
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[str] = None

@app.post("/mcp")
async def handle_mcp_request(request: Request, background_tasks: BackgroundTasks):
    """
    处理MCP请求
    支持初始化请求和普通请求，支持JSON响应和流式响应
    """
    try:
        # 获取会话ID和请求体
        session_id = request.headers.get("mcp-session-id")
        body = await request.json()
        
        logger.info(f"收到MCP请求: 会话ID={session_id}, 方法={get_method_from_body(body)}")
        
        # 检查是否是初始化请求
        if not session_id and is_initialize_request(body):
            # 新会话初始化
            session_id = str(uuid.uuid4())
            sessions[session_id] = {
                "status": "initializing",
                "queue": asyncio.Queue(),
                "response_mode": get_response_mode(request),
            }
            
            logger.info(f"新会话初始化: ID={session_id}, 响应模式={sessions[session_id]['response_mode']}")
            
            # 处理初始化请求
            result = await process_initialize_request(body, session_id)
            sessions[session_id]["status"] = "active"
            
            # 根据请求的Accept头决定返回JSON响应还是流式响应
            if sessions[session_id]["response_mode"] == "json":
                logger.info(f"使用JSON响应模式，会话ID={session_id}")
                return JSONResponse(
                    content=result,
                    headers={"mcp-session-id": session_id, "Content-Type": "application/json"}
                )
            else:
                logger.info(f"使用流式响应模式，会话ID={session_id}")
                # 将结果放入队列，并设置后台任务来处理未来的响应
                for item in format_as_sse(result):
                    await sessions[session_id]["queue"].put(item)
                
                # 启动后台流处理
                background_tasks.add_task(process_mcp_queue, session_id)
                
                return StreamingResponse(
                    stream_response(session_id),
                    media_type="text/event-stream",
                    headers={"mcp-session-id": session_id}
                )
        
        # 处理已有会话的请求
        elif session_id and session_id in sessions:
            # 处理常规请求
            logger.info(f"处理会话请求: ID={session_id}, 方法={get_method_from_body(body)}")
            result = await process_request(body, session_id)
            
            # 根据会话的响应模式决定如何返回结果
            if sessions[session_id]["response_mode"] == "json":
                logger.info(f"发送JSON响应: 会话ID={session_id}")
                return JSONResponse(
                    content=result,
                    headers={"Content-Type": "application/json"}
                )
            else:
                logger.info(f"发送流式响应: 会话ID={session_id}")
                # 对于流式会话，将结果放入队列 (队列由之前的StreamingResponse消费)
                for item in format_as_sse(result):
                    await sessions[session_id]["queue"].put(item)
                # 不要返回空Response，而是返回一个StreamingResponse
                return StreamingResponse(
                    stream_response(session_id),
                    media_type="text/event-stream"
                )
        else:
            # 无效请求
            logger.warning(f"无效请求: 会话ID={session_id}")
            return JSONResponse(
                status_code=400,
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32000,
                        "message": "无效请求: 会话ID无效或缺失"
                    },
                    "id": get_id_from_body(body)
                },
                headers={"Content-Type": "application/json"}
            )
    
    except Exception as e:
        logger.error(f"处理MCP请求时出错: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"服务器内部错误: {str(e)}"
                },
                "id": None
            },
            headers={"Content-Type": "application/json"}
        )

async def process_initialize_request(body: Union[Dict, List], session_id: str) -> Dict:
    """处理初始化请求"""
    # 这里需要根据MCP协议实际调用mcp实例的初始化方法
    # 简化版本：直接返回成功响应
    if isinstance(body, list):
        # 批量请求处理
        first_init = next((msg for msg in body if isinstance(msg, dict) and msg.get("method") == "initialize"), None)
        if first_init:
            request_id = first_init.get("id", "1")
            return {
                "jsonrpc": "2.0",
                "result": {
                    "serverInfo": {
                        "name": "mcp-streamable-http-server",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": True,
                        "resources": True,
                        "prompts": True,
                        "notifications": True
                    }
                },
                "id": request_id
            }
    else:
        # 单个请求处理
        request_id = body.get("id", "1")
        return {
            "jsonrpc": "2.0",
            "result": {
                "serverInfo": {
                    "name": "mcp-streamable-http-server",
                    "version": "1.0.0"
                },
                "capabilities": {
                    "tools": True,
                    "resources": True,
                    "prompts": True,
                    "notifications": True
                }
            },
            "id": request_id
        }

async def process_request(body: Union[Dict, List], session_id: str) -> Dict:
    """处理常规MCP请求"""
    # 实际实现中，这里应该根据请求方法调用mcp实例的对应方法
    # 简化版本：根据方法类型返回不同的响应
    if isinstance(body, list):
        # 批量请求处理
        return {"jsonrpc": "2.0", "result": "批量处理尚未实现", "id": "batch"}
    
    method = body.get("method", "")
    params = body.get("params", {})
    request_id = body.get("id", "1")
    
    if method == "list_tools":
        # 返回工具列表
        return {
            "jsonrpc": "2.0",
            "result": {
                "tools": [
                    {"name": "calculate_sum", "description": "计算数字列表的总和"},
                    {"name": "calculate_average", "description": "计算数字列表的平均值"},
                    {"name": "calculate_stats", "description": "计算数字列表的基本统计信息"},
                    {"name": "get_user_info", "description": "获取用户信息"},
                    {"name": "validate_user", "description": "验证用户ID是否有效"},
                    {"name": "health", "description": "健康检查工具"}
                ]
            },
            "id": request_id
        }
    elif method == "list_resources":
        # 返回资源列表
        return {
            "jsonrpc": "2.0",
            "result": {
                "resources": [
                    {"name": "dir", "description": "获取目录内容"},
                    {"name": "file", "description": "获取文件内容"}
                ]
            },
            "id": request_id
        }
    elif method == "list_prompts":
        # 返回提示模板列表
        return {
            "jsonrpc": "2.0",
            "result": {
                "prompts": [
                    {"name": "review_code", "description": "代码审查提示"},
                    {"name": "suggest_tests", "description": "测试建议提示"},
                    {"name": "generate_commit_message", "description": "生成Git提交消息"},
                    {"name": "generate_api_docs", "description": "生成API文档"}
                ]
            },
            "id": request_id
        }
    elif method == "call_tool":
        # 调用工具
        tool_name = params.get("name", "")
        tool_params = params.get("parameters", {})
        
        if tool_name == "calculate_sum":
            numbers = tool_params.get("numbers", [])
            result = sum(numbers)
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                },
                "id": request_id
            }
        elif tool_name == "health":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"status": "ok", "service": "crew-ai-mcp"})
                        }
                    ]
                },
                "id": request_id
            }
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32601,
                    "message": f"未知工具: {tool_name}"
                },
                "id": request_id
            }
    else:
        # 未知方法
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32601,
                "message": f"未知方法: {method}"
            },
            "id": request_id
        }

async def stream_response(session_id: str):
    """流式响应生成器"""
    queue = sessions[session_id]["queue"]
    try:
        while True:
            # 从队列中获取下一个SSE事件
            data = await queue.get()
            yield data
            
            # 标记任务完成
            queue.task_done()
    except asyncio.CancelledError:
        logger.info(f"会话 {session_id} 的流已取消")

async def process_mcp_queue(session_id: str):
    """处理MCP响应队列的后台任务"""
    try:
        # 此任务会在后台运行，处理发送到客户端的通知
        logger.info(f"启动队列处理，会话ID={session_id}")
    except Exception as e:
        logger.error(f"处理队列时出错: {str(e)}", exc_info=True)

def format_as_sse(data: Dict) -> List[str]:
    """将数据格式化为SSE事件"""
    try:
        json_data = json.dumps(data)
        # 确保使用正确的SSE格式：data: 后面是数据，以\n\n结尾
        return [f"data: {json_data}\n\n"]
    except Exception as e:
        logger.error(f"格式化SSE事件时出错: {str(e)}")
        return [f"data: {{\"error\": \"格式化SSE事件时出错: {str(e)}\"}}\n\n"]

def is_initialize_request(body: Union[Dict, List]) -> bool:
    """检查是否是初始化请求"""
    if isinstance(body, list):
        return any(isinstance(msg, dict) and msg.get("method") == "initialize" for msg in body)
    return isinstance(body, dict) and body.get("method") == "initialize"

def get_method_from_body(body: Union[Dict, List]) -> str:
    """从请求体中获取方法名"""
    if isinstance(body, list):
        methods = [msg.get("method") for msg in body if isinstance(msg, dict) and "method" in msg]
        return ", ".join(methods)
    return body.get("method", "unknown") if isinstance(body, dict) else "unknown"

def get_id_from_body(body: Union[Dict, List]) -> Optional[str]:
    """从请求体中获取ID"""
    if isinstance(body, list):
        for msg in body:
            if isinstance(msg, dict) and "id" in msg:
                return msg.get("id")
        return None
    return body.get("id") if isinstance(body, dict) else None

def get_response_mode(request: Request) -> str:
    """根据Accept头决定响应模式"""
    accept_header = request.headers.get("accept", "")
    if "text/event-stream" in accept_header:
        return "stream"
    return "json"

# 添加健康检查端点
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "mcp-streamable-http-server"}

# 添加根路径处理
@app.get("/")
async def root():
    """根路径欢迎页面"""
    html_content = """
    <html>
        <head>
            <title>MCP StreamableHTTP 服务器</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                h1 { color: #333; }
                pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; }
                code { font-family: monospace; }
            </style>
        </head>
        <body>
            <h1>MCP StreamableHTTP 服务器</h1>
            <p>这是一个基于Model Context Protocol的服务器，提供工具、资源和提示模板功能。</p>
            <h2>API 使用说明</h2>
            <p>请使用POST方法访问 <code>/mcp</code> 端点，发送符合JSON-RPC 2.0格式的请求。</p>
            <h3>初始化请求示例：</h3>
            <pre>
POST /mcp HTTP/1.1
Content-Type: application/json
Accept: application/json

{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "capabilities": {},
    "protocolVersion": "2025-03-26",
    "clientInfo": {
      "name": "test-client",
      "version": "1.0.0"
    }
  },
  "id": "1"
}
            </pre>
            <p>更多信息请参考 <a href="https://github.com/modelcontextprotocol/typescript-sdk">MCP 文档</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# 添加MCP GET方法支持
@app.get("/mcp")
async def mcp_get():
    """MCP GET方法说明"""
    return JSONResponse(
        content={
            "message": "MCP接口只接受POST请求",
            "documentation": "请使用POST方法发送符合JSON-RPC 2.0格式的请求",
            "example": {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "capabilities": {},
                    "protocolVersion": "2025-03-26",
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                },
                "id": "1"
            }
        },
        headers={"Content-Type": "application/json"}
    ) 
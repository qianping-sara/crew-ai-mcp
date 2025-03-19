"""
API设计提示模块
提供API设计相关的提示模板
"""
from typing import List
from ..mcp_server import mcp

@mcp.prompt()
async def design_rest_api(resource: str, operations: List[str]) -> str:
    """创建REST API设计提示
    
    Args:
        resource: 资源名称
        operations: 需要支持的操作列表
    """
    return f"""请为{resource}资源设计RESTful API，需要支持以下操作：
{', '.join(operations)}

请提供：
1. API端点设计
2. HTTP方法选择
3. 请求/响应格式
4. 状态码使用
5. 认证/授权建议
6. 错误处理策略
7. API文档示例
"""

@mcp.prompt()
async def review_api_spec(spec: str) -> str:
    """创建API规范审查提示
    
    Args:
        spec: API规范内容
    """
    return f"""请审查以下API规范：

```yaml
{spec}
```

请从以下方面进行评估：
1. RESTful原则符合度
2. 命名规范性
3. 安全性考虑
4. 可扩展性
5. 文档完整性
6. 版本控制策略
7. 改进建议
"""

@mcp.prompt()
async def generate_api_tests(endpoint: str, method: str, params: str) -> str:
    """创建API测试建议提示
    
    Args:
        endpoint: API端点
        method: HTTP方法
        params: 参数说明
    """
    return f"""请为以下API端点生成测试用例：

端点: {endpoint}
方法: {method}
参数: {params}

请包含以下类型的测试：
1. 正常流程测试
2. 参数验证测试
3. 边界条件测试
4. 错误处理测试
5. 性能测试建议
6. 安全测试场景
""" 
"""
代码审查提示模块
提供代码审查相关的提示模板
"""
from ..mcp_server import mcp

@mcp.prompt()
async def review_code(code: str, language: str) -> str:
    """创建代码审查提示
    
    Args:
        code: 要审查的代码
        language: 编程语言
    """
    return f"""请帮我审查以下{language}代码：

```{language}
{code}
```

请从以下几个方面进行审查：
1. 代码质量和可读性
2. 潜在的bug和安全问题
3. 性能优化建议
4. 最佳实践遵循情况
5. 文档和注释完整性
"""

@mcp.prompt()
async def suggest_tests(code: str, language: str) -> str:
    """创建测试建议提示
    
    Args:
        code: 要测试的代码
        language: 编程语言
    """
    return f"""请为以下{language}代码提供测试建议：

```{language}
{code}
```

请包含：
1. 需要测试的主要场景
2. 边界条件测试
3. 异常情况测试
4. 建议的测试框架和工具
5. 测试代码示例
""" 
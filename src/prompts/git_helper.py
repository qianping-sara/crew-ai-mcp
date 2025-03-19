"""
Git帮助提示模块
提供Git操作相关的提示模板
"""
from ..mcp_server import mcp

@mcp.prompt()
async def generate_commit_message(diff: str) -> str:
    """生成Git提交信息的提示
    
    Args:
        diff: Git差异内容
    """
    return f"""请根据以下代码变更生成一个符合约定式提交规范的提交信息：

```diff
{diff}
```

请遵循以下格式：
<type>(<scope>): <description>

[optional body]

[optional footer(s)]

其中type可以是：
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- perf: 性能优化
- test: 测试相关
- chore: 构建过程或辅助工具的变动
"""

@mcp.prompt()
async def explain_git_command(command: str) -> str:
    """解释Git命令的提示
    
    Args:
        command: Git命令
    """
    return f"""请详细解释以下Git命令的作用和注意事项：

```bash
{command}
```

请包含：
1. 命令的基本功能
2. 各个参数的含义
3. 执行后的影响
4. 常见使用场景
5. 潜在风险和注意事项
"""

@mcp.prompt()
async def suggest_git_workflow(team_size: int, project_type: str) -> str:
    """推荐Git工作流的提示
    
    Args:
        team_size: 团队规模
        project_type: 项目类型
    """
    return f"""请为一个{team_size}人的团队推荐适合{project_type}项目的Git工作流程：

请包含以下内容：
1. 推荐的分支策略
2. 代码审查流程
3. 版本发布流程
4. 冲突处理策略
5. CI/CD集成建议
6. 具体的Git命令示例
""" 
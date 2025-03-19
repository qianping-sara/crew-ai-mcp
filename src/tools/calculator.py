"""
计算工具模块
提供各种数学计算功能
"""
from typing import List
from ..mcp_server import mcp

@mcp.tool()
async def calculate_sum(numbers: List[float]) -> float:
    """计算数字列表的总和
    
    Args:
        numbers: 要计算的数字列表
    """
    return sum(numbers)

@mcp.tool()
async def calculate_average(numbers: List[float]) -> float:
    """计算数字列表的平均值
    
    Args:
        numbers: 要计算的数字列表
    """
    if not numbers:
        raise ValueError("Numbers list cannot be empty")
    return sum(numbers) / len(numbers)

@mcp.tool()
async def calculate_stats(numbers: List[float]) -> dict:
    """计算数字列表的基本统计信息
    
    Args:
        numbers: 要计算的数字列表
    """
    if not numbers:
        raise ValueError("Numbers list cannot be empty")
    return {
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "count": len(numbers)
    } 
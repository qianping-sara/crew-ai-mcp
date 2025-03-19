from setuptools import setup, find_packages

setup(
    name="crew-ai-mcp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp>=1.3.0",
        "aiohttp>=3.8.0",
    ],
) 
# Heroku部署指南

本文档提供将MCP StreamableHTTP服务器部署到Heroku的步骤。

## 前提条件

1. 已有Heroku账号
2. 已安装Heroku CLI
3. 熟悉基本的Git操作

## 部署步骤

### 1. 登录Heroku

```bash
heroku login
```

### 2. 创建Heroku应用

```bash
heroku create your-app-name
```

### 3. 部署到Heroku

直接推送代码到Heroku：

```bash
git push heroku main
```

或如果你在其他分支上：

```bash
git push heroku your-branch:main
```

### 4. 确认部署

应用部署完成后，你可以打开它：

```bash
heroku open
```

### 5. 查看日志

如果遇到问题，可以查看应用日志：

```bash
heroku logs --tail
```

## 配置

本项目已配置为在Heroku上默认使用StreamableHTTP模式启动。关键配置文件包括：

1. `Procfile` - 指定启动命令为`web: python -m src.streamable_http_server_main`
2. `requirements.txt` - 包含所有必需的依赖
3. `src/streamable_http_server_main.py` - 配置为使用Heroku提供的PORT环境变量

## 测试部署的API

部署完成后，你可以使用以下命令测试MCP服务器：

```bash
python debug_client.py https://your-app-name.herokuapp.com/mcp
```

或使用完整客户端：

```bash
python examples_client/streamable_http_client.py https://your-app-name.herokuapp.com/mcp
```

## 注意事项

1. Heroku使用动态端口分配，应用应该绑定到环境变量`PORT`指定的端口
2. Heroku的免费计划有休眠政策，长时间不访问应用会自动休眠
3. 如需持久存储数据，应该使用Heroku的附加服务如Postgres或Redis 
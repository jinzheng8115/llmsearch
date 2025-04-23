# Docker 部署指南

本文档提供了使用 Docker 部署智能搜索应用的详细说明。

## 前提条件

- 安装 [Docker](https://docs.docker.com/get-docker/)
- 安装 [Docker Compose](https://docs.docker.com/compose/install/)

## 开发环境部署

### 1. 准备环境变量

确保您已经创建了 `.env` 文件，并填写了所有必要的 API 密钥和配置。您可以参考 `.env.example` 文件：

```bash
cp .env.example .env
```

然后编辑 `.env` 文件，填写您的 API 密钥和其他配置。

### 2. 构建并启动容器

```bash
docker-compose up -d
```

这将在后台构建并启动应用程序。默认情况下，应用程序将在 http://localhost:5010 上可用。

### 3. 查看日志

```bash
docker-compose logs -f
```

### 4. 停止应用

```bash
docker-compose down
```

## 生产环境部署

对于生产环境，我们提供了一个单独的 Docker Compose 配置文件，它包含了一些生产环境特定的设置。

### 1. 准备环境变量

与开发环境相同，确保您已经创建了 `.env` 文件，并填写了所有必要的 API 密钥和配置。

### 2. 构建并启动容器

```bash
docker-compose -f docker-compose.prod.yml up -d
```

这将在后台构建并启动应用程序。在生产环境中，应用程序将在 http://localhost:80 上可用。

### 3. 查看日志

```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### 4. 停止应用

```bash
docker-compose -f docker-compose.prod.yml down
```

## 环境变量说明

以下是应用程序使用的主要环境变量：

### 基本配置
- `PORT`: 应用程序内部监听的端口（默认为 5000）

### 智谱AI配置
- `ZHIPUAI_API_KEY`: 智谱AI API 密钥
- `ZHIPUAI_API_URL`: 智谱AI API URL
- `ZHIPUAI_MODEL`: 使用的智谱AI模型
- `ZHIPUAI_TEMPERATURE`: 温度参数
- `ZHIPUAI_TOP_P`: Top-P 参数

### DeepSeek配置
- `DEEPSEEK_API_KEY`: DeepSeek API 密钥
- `DEEPSEEK_API_URL`: DeepSeek API URL
- `DEEPSEEK_MODEL`: 使用的DeepSeek模型
- `DEEPSEEK_TEMPERATURE`: 温度参数
- `DEEPSEEK_TOP_P`: Top-P 参数

### Bocha AI配置
- `BOCHAAI_API_KEY`: Bocha AI API 密钥
- `BOCHAAI_API_URL`: Bocha AI API URL
- `BOCHAAI_DEFAULT_FRESHNESS`: 默认时间范围

### SearXNG配置
- `SEARXNG_API_HOST`: SearXNG API 主机地址
- `SEARXNG_DEFAULT_LANGUAGE`: 默认语言
- `SEARXNG_DEFAULT_SAFESEARCH`: 默认安全搜索级别
- `SEARXNG_DEFAULT_ENGINES`: 默认搜索引擎列表
- `SEARXNG_DEFAULT_TIME_RANGE`: 默认时间范围

## 自定义配置

如果您需要自定义 Docker 配置，可以编辑 `docker-compose.yml` 或 `docker-compose.prod.yml` 文件。例如，您可以：

- 更改端口映射
- 添加更多环境变量
- 配置持久化存储
- 添加其他服务（如数据库）

## 故障排除

### 容器无法启动

检查日志以获取详细信息：

```bash
docker-compose logs
```

### API 连接问题

确保您的 `.env` 文件中包含正确的 API 密钥和 URL。

### 端口冲突

如果端口已被占用，您可以在 `docker-compose.yml` 文件中更改端口映射：

```yaml
ports:
  - "新端口:5000"
```

## 安全注意事项

- 不要将包含 API 密钥的 `.env` 文件提交到版本控制系统
- 在生产环境中，考虑使用 Docker Secrets 或其他安全的方式管理敏感信息
- 定期更新 Docker 镜像以获取安全补丁

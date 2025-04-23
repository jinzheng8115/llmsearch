# 智能搜索助手

一个基于多种大模型和搜索引擎的智能搜索助手，支持联网搜索和智能问答。

## 功能特点

- 智能判断是否需要搜索，自动进行搜索或直接回答
- 支持多种搜索引擎：智谱AI、Bocha AI、SearXNG
- 支持多种大模型：智谱AI GLM-4、DeepSeek
- 简洁美观的聊天界面
- 可配置的设置页面
- 响应式设计，适配移动设备

## 技术栈

- 前端：HTML, CSS, JavaScript
- 后端：Python, Flask
- API：智谱AI API, DeepSeek API, Bocha AI API, SearXNG API

## 安装与运行

### 方法1：直接安装

1. 安装依赖：

```bash
pip install -r requirements.txt
```

2. 配置环境变量：

创建一个`.env`文件，参考`.env.example`文件进行配置。

3. 启动服务器：

```bash
python app.py
```

4. 访问网站：

打开浏览器，访问 `http://localhost:5000`

### 方法2：Docker部署

1. 配置环境变量：

创建一个`.env`文件，参考`.env.example`文件进行配置。

2. 构建并启动容器：

```bash
docker-compose up -d
```

3. 访问网站：

打开浏览器，访问 `http://localhost:5010`

更多详细的Docker部署说明，请参考 [DOCKER_DEPLOY.md](DOCKER_DEPLOY.md)

## 使用方法

1. 在聊天输入框中输入问题
2. 点击发送按钮或按回车键
3. 系统会自动判断是否需要搜索，并给出回答

## 配置说明

在设置页面中，您可以配置：

- 默认大模型：智谱AI GLM-4 或 DeepSeek Reasoner
- 默认搜索引擎：智谱基础搜索、Bocha AI 或 SearXNG
- 搜索结果数量
- 时间范围
- SearXNG的高级设置

## 注意事项

- 需要有效的API密钥（智谱AI、DeepSeek、Bocha AI）
- 如果使用SearXNG，需要配置有效的SearXNG实例地址
- 搜索结果的质量取决于所选搜索引擎

## 贡献

欢迎提交Issue和Pull Request。

## 许可证

MIT

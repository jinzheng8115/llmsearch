#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
聊天API模块

这个模块提供了聊天API的实现，包括普通聊天和联网搜索聊天。
"""

import os
import json
import time
import requests
from urllib.parse import quote
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入搜索引擎模块
from search_engines import zhipuai, searxng, bochaai

# 导入智能联网搜索提示词
from chat_with_intelligent_search_new import INTELLIGENT_SEARCH_PROMPT

# 导入DeepSeek API模块
import deepseek_api

# 系统提示词
SYSTEM_PROMPT = '''你是一个有用的AI助手。你可以回答用户的各种问题，提供有用的信息和建议。

请遵循以下几点：
1. 提供准确、有用的信息
2. 如果不确定答案，坦诚承认
3. 避免有害、不当或违法的内容
4. 尊重用户隐私
5. 保持中立、客观的态度

请用中文回答用户的问题，除非用户明确要求使用其他语言。
'''

# 联网搜索系统提示词
SEARCH_SYSTEM_PROMPT = '''你是一个有用的AI助手。你可以获取最新信息来回答问题。

请基于提供的搜索结果回答问题。在回答中，请遵循以下几点：

1. 不要在回答正文中直接嵌入链接
2. 在回答正文中，可以使用数字引用来指代特定来源，例如："根据来源[1]，..."
3. 在回答的最后，必须添加一个"参考来源"部分
4. 在参考来源部分，必须列出所有提供给你的搜索结果，包括完整的URL链接，即使你没有直接引用其中的某些来源

参考来源部分的格式必须如下：

## 参考来源
1. [标题](链接)
2. [标题](链接)
...

请确保列出所有提供给你的搜索结果。如果搜索结果不足以回答问题，请坦诚说明，并尽可能基于你已有的知识提供帮助。

请用中文回答用户的问题，除非用户明确要求使用其他语言。
'''

def format_search_results(results, query):
    """
    格式化搜索结果为文本

    Args:
        results: 搜索结果列表
        query: 搜索查询

    Returns:
        格式化的搜索结果文本
    """
    if not results:
        return "没有找到相关搜索结果。"

    # 内容部分
    content_text = f"以下是关于\"{query}\"的搜索结果：\n\n"

    for i, result in enumerate(results, 1):
        title = result.get('title', '无标题')
        content = result.get('content', '无内容')

        # 不包含链接，只包含内容和编号
        content_text += f"{i}. {title}\n"
        content_text += f"   {content}\n\n"

    # 参考来源部分
    sources_text = "\n## 参考来源\n"

    for i, result in enumerate(results, 1):
        title = result.get('title', '无标题')
        url = result.get('link', '#')

        # 添加参考来源，确保 URL 是有效的
        if url and url != '#':
            sources_text += f"{i}. [{title}]({url})\n"
        else:
            sources_text += f"{i}. {title}\n"

    # 指导说明
    instruction_text = '''
请基于以上信息回答问题。在回答正文中，可以使用数字引用来指代特定来源，例如："根据来源[1]，..."。在回答的最后，请添加"参考来源"部分，并列出所有上述搜索结果，即使你没有直接引用其中的某些来源。
'''

    # 合并所有部分
    formatted_text = content_text + sources_text + instruction_text

    return formatted_text

# 模型配置
MODEL_CONFIGS = {
    'zhipuai': {
        'name': '智谱AI',
        'api_key_env': 'ZHIPUAI_API_KEY',
        'url': os.getenv('ZHIPUAI_API_URL'),
        'model_id': os.getenv('ZHIPUAI_MODEL'),
        'auth_header': lambda key: f'Bearer {key}',
        'request_format': lambda messages, stream: {
            'model': os.getenv('ZHIPUAI_MODEL'),
            'messages': messages,
            'temperature': float(os.getenv('ZHIPUAI_TEMPERATURE', 0.7)),
            'top_p': float(os.getenv('ZHIPUAI_TOP_P', 0.8)),
            'stream': stream
        }
    }
    # DeepSeek模型使用deepseek_api模块处理
}

# 默认模型
DEFAULT_MODEL = 'zhipuai'

def get_model_config(model_id=None):
    """获取模型配置"""
    if not model_id or model_id not in MODEL_CONFIGS:
        model_id = DEFAULT_MODEL
    return MODEL_CONFIGS[model_id]

def call_llm_model(prompt, system_prompt=SYSTEM_PROMPT, model_id=None, stream=False):
    """
    调用大模型

    Args:
        prompt: 用户提示
        system_prompt: 系统提示
        model_id: 模型标识符
        stream: 是否使用流式输出

    Returns:
        大模型的回复或流式响应对象
    """
    # 准备消息
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # 根据模型ID选择不同的API
    if model_id and model_id.startswith('deepseek'):
        # 使用DeepSeek模型
        try:
            # 从环境变量获取模型名称
            model_name = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

            if stream:
                # 流式输出模式
                response = deepseek_api.chat(messages, stream=True, model=model_name)
                return deepseek_api.format_stream_for_flask(response)
            else:
                # 非流式模式
                response = deepseek_api.chat(messages, stream=False, model=model_name)
                return deepseek_api.extract_response_content(response)['content']
        except Exception as e:
            return f"调用DeepSeek模型时出错: {str(e)}"
    else:
        # 使用智谱AI模型
        # 获取模型配置
        config = get_model_config(model_id)

        # 获取API密钥
        api_key = os.getenv(config['api_key_env'])
        if not api_key:
            return f"{config['name']} API密钥未配置。请在.env文件中设置{config['api_key_env']}环境变量。"

        # 准备请求参数
        url = config['url']
        headers = {
            "Content-Type": "application/json",
            "Authorization": config['auth_header'](api_key)
        }
        payload = config['request_format'](messages, stream)

        try:
            # 发送请求
            if stream:
                # 流式输出模式
                response = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
                response.raise_for_status()
                return response  # 返回原始响应对象，由调用者处理流式输出
            else:
                # 非流式模式
                response = requests.post(url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()

                # 解析响应
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content']
                else:
                    return f"{config['name']}未返回有效回复。"

        except Exception as e:
            return f"调用{config['name']}模型时出错: {str(e)}"

def chat(query, model_id=None, stream=False):
    """
    普通聊天

    Args:
        query: 用户问题
        model_id: 模型标识符
        stream: 是否使用流式输出

    Returns:
        dict: 包含AI回复的字典，或者流式响应对象
    """
    # 初始化结果
    result = {
        "id": f"chat_{int(time.time())}",
        "created": int(time.time()),
        "query": query,
        "model_id": model_id or DEFAULT_MODEL,
        "response": "",
        "search_performed": False,  # 添加这个字段以保持一致性
        "question_type": "",  # 添加这个字段以保持一致性
        "search_results": []  # 添加空的搜索结果列表
    }

    # 使用与智能联网搜索相同的系统提示词
    # 但是使用DIRECT_ANSWER任务类型
    task_prompt = f"任务类型: DIRECT_ANSWER\n用户问题: {query}"

    # 调用大模型，使用与智能联网搜索相同的提示词
    response = call_llm_model(task_prompt, INTELLIGENT_SEARCH_PROMPT, model_id, stream)

    # 如果是流式输出，需要修改返回方式
    if stream:
        # 在流式响应的第一个块中包含空的搜索结果信息
        if hasattr(response, 'iter_lines'):
            original_iter_lines = response.iter_lines

            def modified_iter_lines(*args, **kwargs):
                # 首先发送一个包含空搜索结果的特殊块
                search_info = json.dumps({
                    "search_results": [],
                    "question_type": ""
                })
                yield search_info.encode('utf-8')

                # 然后发送原始的流式响应
                for line in original_iter_lines(*args, **kwargs):
                    # 处理智谱AI和DeepSeek的流式输出格式
                    try:
                        line_text = line.decode('utf-8')
                        if line_text.startswith('{') and '"choices"' in line_text:
                            json_data = json.loads(line_text)

                            # 提取内容
                            if 'choices' in json_data and len(json_data['choices']) > 0:
                                # 智谱AI格式
                                if 'delta' in json_data['choices'][0] and 'content' in json_data['choices'][0]['delta']:
                                    content = json_data['choices'][0]['delta']['content']
                                    # 创建前端期望的格式
                                    frontend_data = {
                                        "content": content,
                                        "role": "assistant"
                                    }
                                    # 发送给前端
                                    yield f"data: {json.dumps(frontend_data)}\n\n"
                                    continue
                                # DeepSeek格式
                                elif 'message' in json_data['choices'][0] and 'content' in json_data['choices'][0]['message']:
                                    content = json_data['choices'][0]['message']['content']
                                    # 创建前端期望的格式
                                    frontend_data = {
                                        "content": content,
                                        "role": "assistant"
                                    }
                                    # 发送给前端
                                    yield f"data: {json.dumps(frontend_data)}\n\n"
                                    continue
                                # DeepSeek Reasoner模型的推理过程格式 - 非流式模式
                                elif 'message' in json_data['choices'][0] and 'reasoning_content' in json_data['choices'][0]['message']:
                                    reasoning = json_data['choices'][0]['message']['reasoning_content']
                                    # 检查推理内容是否为空或null
                                    if reasoning and reasoning != 'null' and reasoning.strip():
                                        # 创建前端期望的格式
                                        frontend_data = {
                                            "content": reasoning,
                                            "role": "assistant",
                                            "is_reasoning": True
                                        }
                                        # 发送给前端
                                        yield f"data: {json.dumps(frontend_data)}\n\n"
                                    continue
                                # DeepSeek Reasoner模型的推理过程格式 - 流式模式
                                elif 'delta' in json_data['choices'][0] and 'reasoning_content' in json_data['choices'][0]['delta']:
                                    print(f">>> 检测到推理内容: {json_data['choices'][0]['delta']['reasoning_content'][:30]}...")
                                    reasoning = json_data['choices'][0]['delta']['reasoning_content']
                                    # 检查推理内容是否为空或null
                                    if reasoning and reasoning != 'null' and reasoning.strip():
                                        # 创建前端期望的格式
                                        frontend_data = {
                                            "content": reasoning,
                                            "role": "assistant",
                                            "is_reasoning": True
                                        }
                                        # 发送给前端
                                        yield f"data: {json.dumps(frontend_data)}\n\n"
                                    continue
                    except Exception as e:
                        print(f">>> 解析JSON出错: {str(e)}")

                    # 如果不是特殊格式，直接传递
                    yield line

                # 发送结束消息 - 使用两种格式的结束消息，确保前端能正确处理
                # 首先发送JSON格式的结束消息
                yield f"data: {{\"done\": true}}\n\n"
                # 然后发送旧格式的结束消息
                yield f"data: [DONE]\n\n"
                print(f">>> 普通聊天流式输出完成")

            response.iter_lines = modified_iter_lines

        return response

    # 保存AI回复
    result["response"] = response

    return result

def chat_with_search(query, engine="search_std", count=10, model_id=None, stream=False, **kwargs):
    """
    联网搜索聊天

    Args:
        query: 用户问题
        engine: 搜索引擎
        count: 结果数量
        model_id: 模型标识符
        stream: 是否使用流式输出
        **kwargs: 其他搜索参数，如SearXNG的特殊参数

    Returns:
        dict: 包含搜索结果和AI回复的字典，或者流式响应对象
    """
    # 初始化结果
    result = {
        "id": f"chat_search_{int(time.time())}",
        "created": int(time.time()),
        "query": query,
        "engine": engine,
        "model_id": model_id or DEFAULT_MODEL,
        "search_results": [],
        "response": ""
    }

    # 执行搜索
    search_result = None

    if engine.startswith("search_"):
        # 使用智谱AI搜索
        search_result = zhipuai.search(query, engine)
    elif engine == "bochaai":
        # 使用Bocha AI搜索
        search_result = bochaai.search(query, count=count)
    elif engine == "searxng":
        # 使用SearXNG搜索
        # 提取SearXNG特殊参数
        searxng_params = {}

        # 处理可能的SearXNG参数
        if 'engines' in kwargs:
            searxng_params['engines'] = kwargs['engines']
        if 'language' in kwargs:
            searxng_params['language'] = kwargs['language']
        if 'safesearch' in kwargs:
            searxng_params['safesearch'] = kwargs['safesearch']
        if 'time_range' in kwargs:
            searxng_params['time_range'] = kwargs['time_range']

        # 调用SearXNG搜索
        print(f'SearXNG搜索参数: {searxng_params}')
        search_result = searxng.search(query, count=count, **searxng_params)
    else:
        result["error"] = f"不支持的搜索引擎: {engine}"
        return result

    # 检查搜索结果
    if not search_result or 'search_result' not in search_result or not search_result['search_result']:
        result["error"] = "搜索未返回结果"
        return result

    # 保存搜索结果
    result["search_results"] = search_result['search_result']

    # 格式化搜索结果
    formatted_results = format_search_results(search_result['search_result'], query)

    # 准备提示词
    prompt = f"请回答以下问题: {query}\n\n{formatted_results}"

    # 调用大模型
    response = call_llm_model(prompt, SEARCH_SYSTEM_PROMPT, model_id, stream)

    # 如果是流式输出，直接返回响应对象
    if stream:
        return response

    # 保存AI回复
    result["response"] = response

    return result



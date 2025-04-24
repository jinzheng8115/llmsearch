#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能联网搜索聊天模块

这个模块提供了智能联网搜索聊天功能，大模型会先分析用户的提问是否需要联网搜索，
如果需要，则进行搜索并将搜索结果发送给大模型进行处理。
"""

import os
import json
import time
import requests
import datetime
import re
from urllib.parse import quote
from dotenv import load_dotenv

# 导入 DeepSeek 输出格式化模块
from format_deepseek_output import format_deepseek_output

# 导入智能联网搜索提示词
from intelligent_search_prompt import (
    INTELLIGENT_SEARCH_PROMPT,
    SYSTEM_PROMPT,
    SEARCH_SYSTEM_PROMPT,
    get_current_time_info
)

# 加载环境变量
load_dotenv()

# 导入搜索引擎模块
from search_engines import zhipuai, bochaai, searxng

# 默认模型
DEFAULT_MODEL = 'zhipuai'

# 导入格式化搜索结果模块
from format_search_results_new import format_search_results

import openai

# 导入DeepSeek API模块
import deepseek_api

def call_zhipuai_model(prompt, system_prompt, stream=False):
    """
    调用智谱AI模型

    Args:
        prompt: 用户提示
        system_prompt: 系统提示
        stream: 是否使用流式输出

    Returns:
        智谱AI模型的回复或流式响应对象
    """
    # 获取API密钥和URL
    api_key = os.getenv('ZHIPUAI_API_KEY')
    if not api_key:
        return "智谱AI API密钥未配置。请在.env文件中设置ZHIPUAI_API_KEY环境变量。"

    url = os.getenv('ZHIPUAI_API_URL')
    model = os.getenv('ZHIPUAI_MODEL')

    # 准备消息
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # 准备请求参数
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": messages,
        "temperature": float(os.getenv('ZHIPUAI_TEMPERATURE', 0.7)),
        "top_p": float(os.getenv('ZHIPUAI_TOP_P', 0.8)),
        "stream": stream
    }

    try:
        # 发送请求
        if stream:
            # 流式输出模式
            response = requests.post(url, json=payload, headers=headers, stream=True, timeout=60)
            response.raise_for_status()
            print(f"=== 智谱AI模型调用完成 ===")
            print(f"响应类型: 流式输出")
            print(f"响应状态码: {response.status_code}\n")
            return response  # 返回原始响应对象，由调用者处理流式输出
        else:
            # 非流式模式
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()

            # 解析响应
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"=== 智谱AI模型调用完成 ===")
                print(f"响应类型: 普通响应")
                print(f"响应状态码: {response.status_code}")
                print(f"响应内容长度: {len(content)}\n")
                return content
            else:
                print(f"=== 智谱AI模型调用完成，但未返回有效回复 ===\n")
                return "智谱AI模型未返回有效回复。"

    except Exception as e:
        print(f"=== 智谱AI模型调用出错 ===")
        print(f"错误信息: {str(e)}\n")
        error_message = f"调用智谱AI模型时出错: {str(e)}"

        # 如果是流式输出模式，返回一个带有iter_lines方法的对象
        if stream:
            class ErrorResponse:
                def __init__(self, error_message):
                    self.error_message = error_message

                def iter_lines(self, *args, **kwargs):
                    # 返回一个只包含错误消息的迭代器
                    error_data = {
                        "error": f"调用智谱AI模型时出错: {self.error_message}"
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"

                    # 发送结束消息
                    yield f"data: {{\"done\": true}}\n\n"
                    # yield f"data: [DONE]\n\n" # 移除多余的结束标记

            return ErrorResponse(error_message)
        else:
            return error_message

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
    # 记录调用大模型的日志
    system_prompt_type = "SEARCH_SYSTEM_PROMPT" if system_prompt == SEARCH_SYSTEM_PROMPT else \
                        "INTELLIGENT_SEARCH_PROMPT" if system_prompt == INTELLIGENT_SEARCH_PROMPT else "SYSTEM_PROMPT"
    print(f"\n=== 正在调用大模型 ===")
    print(f"提示词类型: {system_prompt_type}")
    print(f"提示词长度: {len(prompt)}")
    print(f"模型 ID: {model_id or '默认'}")
    print(f"流式输出: {stream}")

    # 准备消息
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]

    # 根据模型ID选择不同的API
    if model_id and model_id.startswith('deepseek'):
        # 使用DeepSeek模型
        try:
            # 使用 DeepSeek 模型，从环境变量获取模型名称
            model_name = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

            if stream:
                # 流式输出模式
                response = deepseek_api.chat(messages, stream=True, model=model_name)

                # 创建一个带有 iter_lines 方法的对象，以兼容现有代码
                class StreamResponse:
                    def __init__(self, stream_generator):
                        self.stream_generator = stream_generator

                    def iter_lines(self, *args, **kwargs):
                        for chunk in self.stream_generator:
                            yield chunk

                return StreamResponse(deepseek_api.format_stream_for_flask(response))
            else:
                # 非流式模式
                response = deepseek_api.chat(messages, stream=False, model=model_name)
                result = deepseek_api.extract_response_content(response)

                # 如果有推理内容，返回字典
                if 'reasoning_content' in result:
                    # 格式化 DeepSeek 输出
                    formatted_content = format_deepseek_output(result['content'])
                    return {
                        "content": formatted_content,
                        "reasoning_content": result['reasoning_content']
                    }
                else:
                    # 格式化 DeepSeek 输出
                    formatted_content = format_deepseek_output(result['content'])
                    return formatted_content
        except Exception as e:
            error_message = f"调用DeepSeek模型时出错: {str(e)}"
            print(f"=== DeepSeek 模型调用出错 ===")
            print(f"错误信息: {str(e)}\n")

            # 如果是流式输出模式，返回一个带有iter_lines方法的对象
            if stream:
                class ErrorResponse:
                    def __init__(self, error_message):
                        self.error_message = error_message

                    def iter_lines(self, *args, **kwargs):
                        # 返回一个只包含错误消息的迭代器
                        error_data = {
                            "error": f"调用 DeepSeek 模型时出错: {self.error_message}"
                        }
                        yield f"data: {json.dumps(error_data)}\n\n"

                        # 发送结束消息
                        yield f"data: {{\"done\": true}}\n\n"

                return ErrorResponse(error_message)
            else:
                return error_message
    else:
        # 默认使用智谱 AI 模型
        return call_zhipuai_model(prompt, system_prompt, stream)

def analyze_search_need(query, model_id=None):
    """
    分析用户查询是否需要搜索

    Args:
        query: 用户查询
        model_id: 模型标识符

    Returns:
        bool: 是否需要搜索
    """
    print(f"\n>>> 开始分析是否需要搜索: {query}")

    # 使用合并提示词
    task_prompt = f"任务类型: ANALYZE_SEARCH_NEED\n用户问题: {query}"
    response = call_llm_model(task_prompt, INTELLIGENT_SEARCH_PROMPT, model_id)

    # 解析响应 - 修复后的逻辑，支持DeepSeek模型返回的字典格式
    need_search = False

    # 如果响应是字典类型（如DeepSeek模型返回的格式）
    if isinstance(response, dict):
        if 'content' in response and "需要搜索" in response['content']:
            need_search = True
    # 如果响应是字符串类型（如智谱AI模型返回的格式）
    elif isinstance(response, str) and "需要搜索" in response:
        need_search = True

    if need_search:
        print(f">>> 分析结果: 需要搜索")
        print(f">>> 大模型原始响应: {response}\n")
        return True
    else:
        print(f">>> 分析结果: 不需要搜索")
        print(f">>> 大模型原始响应: {response}\n")
        return False

def analyze_question_type(query, model_id=None):
    """
    分析用户问题类型

    Args:
        query: 用户查询
        model_id: 模型标识符

    Returns:
        str: 问题类型，"开放性问题"或"准确答案问题"
    """
    print(f"\n>>> 开始分析问题类型: {query}")

    # 使用合并提示词
    task_prompt = f"任务类型: ANALYZE_QUESTION_TYPE\n用户问题: {query}"
    response = call_llm_model(task_prompt, INTELLIGENT_SEARCH_PROMPT, model_id)

    # 解析响应 - 修复后的逻辑，支持DeepSeek模型返回的字典格式
    is_open_question = False

    # 如果响应是字典类型（如DeepSeek模型返回的格式）
    if isinstance(response, dict):
        if 'content' in response and "开放性问题" in response['content']:
            is_open_question = True
    # 如果响应是字符串类型（如智谱AI模型返回的格式）
    elif isinstance(response, str) and "开放性问题" in response:
        is_open_question = True

    if is_open_question:
        print(f">>> 分析结果: 开放性问题")
        print(f">>> 大模型原始响应: {response}\n")
        return "开放性问题"
    else:
        print(f">>> 分析结果: 准确答案问题")
        print(f">>> 大模型原始响应: {response}\n")
        return "准确答案问题"

def extract_search_keywords(query, model_id=None):
    """
    提取搜索关键词

    Args:
        query: 用户查询
        model_id: 模型标识符

    Returns:
        list: 搜索关键词列表
    """
    print(f"\n>>> 开始提取搜索关键词: {query}")

    # 使用合并提示词
    task_prompt = f"任务类型: EXTRACT_KEYWORDS\n用户问题: {query}"
    response = call_llm_model(task_prompt, INTELLIGENT_SEARCH_PROMPT, model_id)

    # 解析响应 - 修复后的逻辑，支持DeepSeek模型返回的字典格式
    response_text = ""

    # 如果响应是字典类型（如DeepSeek模型返回的格式）
    if isinstance(response, dict):
        if 'content' in response:
            response_text = response['content']
    # 如果响应是字符串类型（如智谱AI模型返回的格式）
    elif isinstance(response, str):
        response_text = response

    # 解析响应，按行分割
    keywords = [kw.strip() for kw in response_text.split('\n') if kw.strip()]

    if not keywords:
        # 如果没有提取到关键词，使用原始查询
        print(f">>> 未提取到关键词，使用原始查询: {query}")
        print(f">>> 大模型原始响应: {response}\n")
        return [query]

    # 后处理：检查并删除单独的时间关键词
    # 时间模式，如"2024年"、"2023年底"等
    time_patterns = [
        r'^\d{4}\s*[年月日]?$',  # 匹配年份，如"2024年"、"2024"
        r'^\d{4}\s*-\s*\d{4}$',  # 匹配年份范围，如"2023-2024"
        r'^\d{4}\s*[年]\s*\d{1,2}\s*[月]$',  # 匹配年月，如"2024年1月"
        r'^[上下本今去明][年月周季度]$',  # 匹配相对时间，如"今年"、"上季度"
    ]

    # 过滤单独的时间关键词
    filtered_keywords = []
    for kw in keywords:
        is_time_only = False
        for pattern in time_patterns:
            if re.match(pattern, kw):
                is_time_only = True
                print(f">>> 过滤单独的时间关键词: {kw}")
                break

        if not is_time_only:
            filtered_keywords.append(kw)

    # 如果过滤后没有关键词了，使用原始查询
    if not filtered_keywords:
        print(f">>> 过滤后没有关键词，使用原始查询: {query}")
        return [query]

    print(f">>> 提取的搜索关键词(过滤后): {filtered_keywords}")
    print(f">>> 大模型原始响应: {response}\n")
    return filtered_keywords

def perform_search(query, engine="search_std", count=10, **kwargs):
    """
    执行搜索

    Args:
        query: 搜索查询
        engine: 搜索引擎
        count: 结果数量
        **kwargs: 其他搜索参数

    Returns:
        list: 搜索结果列表
    """
    # 根据搜索引擎执行搜索
    if engine.startswith("search_"):
        # 使用智谱AI搜索
        search_result = zhipuai.search(query, engine)
    elif engine == "bochaai":
        # 使用Bocha AI搜索
        # 默认使用最近一个月的数据，除非特别指定
        freshness = kwargs.get('freshness', os.getenv('BOCHAAI_DEFAULT_FRESHNESS', 'oneMonth'))
        search_result = bochaai.search(query, freshness=freshness, count=count)
    elif engine == "searxng":
        # 使用SearXNG搜索
        # 提取SearXNG特殊参数
        searxng_params = {}

        # 从环境变量中读取默认设置
        searxng_params['engines'] = os.getenv('SEARXNG_DEFAULT_ENGINES', 'bing,baidu,360search,quark,sogou')
        searxng_params['language'] = os.getenv('SEARXNG_DEFAULT_LANGUAGE', 'auto')
        searxng_params['safesearch'] = int(os.getenv('SEARXNG_DEFAULT_SAFESEARCH', '0'))
        # 默认使用最近一个月的数据，除非特别指定
        searxng_params['time_range'] = os.getenv('SEARXNG_DEFAULT_TIME_RANGE', 'month')

        # 处理可能的SearXNG参数（允许覆盖默认值）
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
        return []

    # 检查搜索结果
    if not search_result or 'search_result' not in search_result or not search_result['search_result']:
        return []

    return search_result['search_result']

def analyze_query(query, model_id=None):
    """
    一次性分析用户查询（包括是否需要搜索、问题类型和搜索关键词）

    Args:
        query: 用户查询
        model_id: 模型标识符

    Returns:
        tuple: (是否需要搜索, 问题类型, 搜索关键词列表)
    """
    print(f"\n>>> 开始一次性分析用户查询: {query}")

    # 使用合并提示词
    task_prompt = f"任务类型: ANALYZE_QUERY\n用户问题: {query}"
    response = call_llm_model(task_prompt, INTELLIGENT_SEARCH_PROMPT, model_id)

    # 解析JSON响应
    try:
        # 尝试直接解析JSON
        import json

        # 如果响应是字典类型（如DeepSeek模型返回的格式）
        if isinstance(response, dict) and 'content' in response:
            response_text = response['content']
        # 如果响应是字符串类型（如智谱AI模型返回的格式）
        elif isinstance(response, str):
            response_text = response
        else:
            response_text = str(response)

        # 尝试从文本中提取JSON部分
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)

            need_search = result.get("need_search", False)
            question_type = result.get("question_type", "准确答案问题")
            keywords = result.get("keywords", [])

            # 如果没有关键词或不需要搜索，使用原始查询作为关键词
            if not keywords or not need_search:
                keywords = [query]

            print(f">>> 分析结果:")
            print(f">>> - 是否需要搜索: {need_search}")
            print(f">>> - 问题类型: {question_type}")
            print(f">>> - 搜索关键词: {keywords}")
            print(f">>> 大模型原始响应: {response}\n")

            return need_search, question_type, keywords
    except Exception as e:
        # 如果JSON解析失败，尝试从文本中提取信息
        print(f">>> JSON解析失败: {e}")
        print(f">>> 尝试从文本中提取信息")
        print(f">>> 大模型原始响应: {response}\n")

    # 如果JSON解析失败，使用备用方法提取信息
    # 提取是否需要搜索
    if isinstance(response, dict) and 'content' in response:
        response_text = response['content']
    elif isinstance(response, str):
        response_text = response
    else:
        response_text = str(response)

    need_search = "true" in response_text.lower() and "need_search" in response_text.lower()

    # 提取问题类型
    if "开放性问题" in response_text:
        question_type = "开放性问题"
    else:
        question_type = "准确答案问题"

    # 提取关键词
    keywords = [query]  # 默认使用原始查询
    if "keywords" in response_text.lower():
        # 尝试提取关键词列表
        try:
            keywords_part = response_text.split("keywords")[1]
            if "[" in keywords_part and "]" in keywords_part:
                keywords_str = keywords_part.split("[")[1].split("]")[0]
                extracted_keywords = [k.strip().strip('"\'') for k in keywords_str.split(",")]
                if extracted_keywords and extracted_keywords[0]:  # 确保提取的关键词非空
                    keywords = extracted_keywords
        except:
            pass

    print(f">>> 从文本中提取的结果:")
    print(f">>> - 是否需要搜索: {need_search}")
    print(f">>> - 问题类型: {question_type}")
    print(f">>> - 搜索关键词: {keywords}")

    return need_search, question_type, keywords

def chat_with_intelligent_search(query, engine="search_std", count=10, model_id=None, stream=False, skip_analysis=False, **kwargs):
    """
    智能联网搜索聊天

    Args:
        query: 用户问题
        engine: 搜索引擎
        count: 结果数量
        model_id: 模型标识符
        stream: 是否使用流式输出
        skip_analysis: 是否跳过分析步骤，直接搜索
        **kwargs: 其他搜索参数

    Returns:
        dict: 包含搜索结果和AI回复的字典，或者流式响应对象
    """
    print(f"\n===================================================")
    print(f"开始处理智能联网搜索聊天请求: {query}")
    print(f"搜索引擎: {engine}, 结果数量: {count}, 模型: {model_id or '默认'}, 流式: {stream}")
    print(f"跳过分析: {skip_analysis}")
    print(f"===================================================")

    # 初始化结果
    result = {
        "id": f"chat_search_{int(time.time())}",
        "created": int(time.time()),
        "query": query,
        "engine": engine,
        "model_id": model_id or DEFAULT_MODEL,
        "search_results": [],
        "response": "",
        "search_performed": False,
        "question_type": "准确答案问题",  # 默认问题类型
        "reconstructed_queries": [],  # 重构后的搜索关键词
        "query_reconstructed": False  # 是否进行了问题重构
    }

    # 如果不跳过分析，则进行一次性分析查询
    if not skip_analysis:
        # 一次性分析查询（包括是否需要搜索、问题类型和搜索关键词）
        need_search, question_type, keywords = analyze_query(query, model_id)

        # 保存问题类型和重构的关键词
        result["question_type"] = question_type
        result["reconstructed_queries"] = keywords
        result["query_reconstructed"] = True

        print(f">>> 问题重构完成，重构后的搜索关键词: {keywords}")
    else:
        # 跳过分析，直接搜索
        need_search = True
        question_type = "准确答案问题"  # 默认问题类型
        keywords = [query]  # 直接使用原始查询作为关键词

        # 保存问题类型
        result["question_type"] = question_type
        result["reconstructed_queries"] = keywords
        result["query_reconstructed"] = False

        print(f">>> 跳过分析，直接使用原始查询作为搜索关键词: {query}")
        print(f">>> 默认问题类型: {question_type}")

    if need_search:

        # 执行搜索
        all_results = []
        for keyword in keywords:
            print(f"\n>>> 正在搜索关键词: {keyword}")
            results = perform_search(keyword, engine, count, **kwargs)
            all_results.extend(results)
            print(f">>> 搜索关键词 '{keyword}' 完成，获取到 {len(results)} 条结果")

        # 去重（基于链接）
        unique_results = []
        seen_urls = set()
        for result_item in all_results:
            url = result_item.get('link', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result_item)

        # 限制结果数量
        if len(unique_results) > count:
            unique_results = unique_results[:count]

        print(f"\n>>> 搜索完成，共获取到 {len(all_results)} 条结果，去重后保留 {len(unique_results)} 条")

        # 保存搜索结果
        result["search_results"] = unique_results
        result["search_performed"] = True

        # 如果有搜索结果，格式化并准备提示词
        if unique_results:
            # 格式化搜索结果，传入问题类型
            formatted_results = format_search_results(unique_results, query, question_type)
            print(f"\n>>> 搜索结果已格式化，准备调用大模型处理")

            # 准备提示词，使用合并提示词
            task_prompt = f"任务类型: ANSWER_WITH_SEARCH\n用户问题: {query}\n\n{formatted_results}"

            # 调用大模型
            print(f"\n>>> 调用大模型处理搜索结果并回答问题")
            response = call_llm_model(task_prompt, INTELLIGENT_SEARCH_PROMPT, model_id, stream)
        else:
            # 如果没有搜索结果，使用普通聊天
            print(f"\n>>> 搜索结果为空，使用普通聊天模式回答")
            # 使用INTELLIGENT_SEARCH_PROMPT而不是SYSTEM_PROMPT
            task_prompt = f"任务类型: DIRECT_ANSWER\n用户问题: 我尝试搜索了相关信息，但没有找到结果。请基于你已有的知识回答这个问题: {query}"
            response = call_llm_model(task_prompt, INTELLIGENT_SEARCH_PROMPT, model_id, stream)
    else:
        # 不需要搜索，使用普通聊天
        print(f"\n>>> 不需要搜索，使用普通聊天模式回答")
        # 使用INTELLIGENT_SEARCH_PROMPT而不是SYSTEM_PROMPT
        task_prompt = f"任务类型: DIRECT_ANSWER\n用户问题: {query}"
        response = call_llm_model(task_prompt, INTELLIGENT_SEARCH_PROMPT, model_id, stream)

    # 如果是流式输出，需要修改返回方式
    if stream:
        # 在流式响应的第一个块中包含搜索结果信息
        if hasattr(response, 'iter_lines'):
            original_iter_lines = response.iter_lines

            def modified_iter_lines(*args, **kwargs):
                # 首先发送一个包含搜索结果和问题类型的特殊块 (如果需要)
                # 注意：前端目前不直接使用这个块，但保留以备将来使用
                # search_info = json.dumps({
                #     "search_results": result["search_results"],
                #     "question_type": result["question_type"]
                # })
                # yield f"data: {search_info}\n\n".encode('utf-8')

                # 然后直接迭代并传递已经格式化好的流式响应
                line_count = 0
                try:
                    for line in original_iter_lines(*args, **kwargs):
                        line_count += 1
                        # 打印调试信息
                        if isinstance(line, bytes):
                            line_str = line.decode('utf-8')
                        else:
                            line_str = line
                        print(f">>> 原始数据块: {line_str[:100]}...")

                        # 对 DeepSeek 模型的输出进行格式化处理
                        if model_id and model_id.startswith('deepseek'):
                            # 解析 JSON 数据
                            try:
                                if line_str.startswith('data: '):
                                    data_json = json.loads(line_str[6:].strip())
                                    # 只处理普通内容，不处理推理内容
                                    if 'content' in data_json and not data_json.get('is_reasoning', False):
                                        # 格式化内容
                                        data_json['content'] = format_deepseek_output(data_json['content'])
                                        # 重新构建数据行
                                        line_str = f"data: {json.dumps(data_json)}\n\n"
                            except Exception as e:
                                print(f">>> 格式化 DeepSeek 流式输出时出错: {e}")
                                # 出错时不修改原始数据
                                pass

                        yield line_str # 确保返回字符串而非字节
                except Exception as e:
                    print(f">>> 处理模型流时出错: {e}")
                    # 产生一个错误块给前端
                    error_data = {
                        "error": f"处理模型响应流时发生错误: {e}"
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
                    # 确保发送结束标记
                    yield f"data: {{\"done\": true}}\n\n"

                # 打印统计信息
                print(f">>> 流式输出已处理 {line_count} 行数据（由模型函数生成）")
                # 注意：结束标记 (`done: true`) 由模型函数内部的 iter_lines 发送

            response.iter_lines = modified_iter_lines

        print(f"\n>>> 返回流式响应对象")
        print(f"===================================================")
        return response

    # 保存AI回复
    if isinstance(response, dict) and "content" in response and "reasoning_content" in response:
        # 如果响应是包含推理内容的字典，分别保存内容和推理内容
        result["response"] = response["content"]
        result["reasoning_content"] = response["reasoning_content"]
    else:
        # 如果响应是普通字符串，直接保存
        result["response"] = response

    print(f"\n>>> 处理完成，返回结果")
    print(f"===================================================")
    return result



#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DeepSeek API 调用模块
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Union, Generator
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def chat(
    messages: List[Dict[str, Any]],
    stream: bool = False,
    model: str = None,
    max_tokens: int = None
) -> Union[Dict[str, Any], Generator]:
    """
    调用 DeepSeek API 进行对话

    Args:
        messages: 对话消息列表
        stream: 是否使用流式输出
        model: 使用的模型，默认为环境变量中的 DEEPSEEK_MODEL
        max_tokens: 最大生成 token 数量

    Returns:
        如果 stream=False，返回完整的响应对象
        如果 stream=True，返回一个生成器，用于流式输出
    """
    # 获取API密钥和URL
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("DeepSeek API密钥未配置。请在.env文件中设置DEEPSEEK_API_KEY环境变量。")

    base_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com')
    model_name = model or os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')

    # 创建 OpenAI 客户端
    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    # 准备请求参数
    params = {
        "model": model_name,
        "messages": messages,
        "stream": stream
    }

    # 如果是 deepseek-reasoner 模型，添加特定参数
    if 'deepseek-reasoner' in model_name.lower():
        if max_tokens:
            params["max_tokens"] = max_tokens
    else:
        # 如果不是 deepseek-reasoner 模型，可以添加温度和 top_p 参数
        params["temperature"] = float(os.getenv('DEEPSEEK_TEMPERATURE', 0.7))
        params["top_p"] = float(os.getenv('DEEPSEEK_TOP_P', 0.8))

    # 打印请求参数
    print(f"DeepSeek 请求参数: {json.dumps(params, ensure_ascii=False)}")

    try:
        # 发送请求
        if stream:
            # 流式输出模式
            response = client.chat.completions.create(**params)
            print(f"=== DeepSeek 模型调用完成 ===")
            print(f"响应类型: 流式输出\n")

            # 创建一个生成器，用于流式输出
            def stream_generator():
                for chunk in response:
                    yield chunk

            return stream_generator()
        else:
            # 非流式模式
            response = client.chat.completions.create(**params)
            print(f"=== DeepSeek 模型调用完成 ===")
            print(f"响应类型: 非流式输出\n")
            return response

    except Exception as e:
        print(f"调用 DeepSeek 模型时出错: {str(e)}")
        raise

def format_stream_for_flask(stream_response) -> Generator:
    """
    将 DeepSeek 流式响应格式化为 Flask SSE 格式

    Args:
        stream_response: DeepSeek 流式响应

    Returns:
        生成器，用于 Flask SSE 输出
    """
    try:
        # 首先发送一个特殊的消息，表示流式输出开始
        yield f"data: {{\"role\": \"assistant\", \"content\": \"\"}}\n\n"

        full_content = ""
        reasoning_content = ""

        for chunk in stream_response:
            # 处理推理内容 (deepseek-reasoner 模型特有)
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                reasoning = chunk.choices[0].delta.reasoning_content
                reasoning_content += reasoning
                # 发送推理内容 - 使用与智谱AI模型兼容的格式，但添加is_reasoning标记
                yield f"data: {{\"is_reasoning\": true, \"content\": {json.dumps(reasoning)}}}\n\n"
                continue

            # 处理普通内容
            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_content += content
                # 发送普通内容 - 使用与智谱AI模型兼容的格式
                yield f"data: {{\"content\": {json.dumps(content)}}}\n\n"

            # 处理结束消息
            if chunk.choices[0].finish_reason:
                # 发送完整的推理内容和普通内容
                if reasoning_content:
                    # 保留推理内容信息，但不影响最终结果的格式
                    yield f"data: {{\"reasoning_content\": {json.dumps(reasoning_content)}, \"full_content\": {json.dumps(full_content)}}}\n\n"

                # 发送结束消息
                yield f"data: {{\"done\": true}}\n\n"
                yield f"data: [DONE]\n\n"
                break

    except Exception as e:
        print(f"格式化流式响应时出错: {str(e)}")
        # 发送错误消息
        yield f"data: {{\"error\": {json.dumps(str(e))}}}\n\n"
        # 确保在错误后也发送 done 标记
        yield f"data: {{\"done\": true}}\n\n"
        yield f"data: [DONE]\n\n"

def extract_response_content(response) -> Dict[str, Any]:
    """
    从 DeepSeek 响应中提取内容

    Args:
        response: DeepSeek 响应对象

    Returns:
        包含响应内容的字典
    """
    result = {
        "role": "assistant",
        "content": response.choices[0].message.content
    }

    # 如果是 deepseek-reasoner 模型，提取推理内容
    if hasattr(response.choices[0].message, 'reasoning_content') and response.choices[0].message.reasoning_content:
        result["reasoning_content"] = response.choices[0].message.reasoning_content

    # 添加使用统计信息
    if hasattr(response, 'usage') and response.usage:
        result["usage"] = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

    return result



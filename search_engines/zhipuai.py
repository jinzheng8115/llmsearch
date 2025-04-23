#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智谱AI搜索引擎实现
"""

import os
import json
import time
import requests
from urllib.parse import urlparse, quote

def is_valid_url(url):
    """检查URL是否有效

    Args:
        url (str): 要检查的URL

    Returns:
        bool: URL是否有效
    """
    # 打印详细的URL信息以便调试
    print(f'检查URL有效性: {url}')

    # 简化的检查逻辑
    if not url or url == '#':
        print('  URL为空或为#，返回False')
        return False

    # 检查是否以http或https开头
    if not url.startswith('http://') and not url.startswith('https://'):
        print('  URL不以http或https开头，返回False')
        return False

    # 检查是否包含域名
    try:
        parsed_url = urlparse(url)
        if not parsed_url.netloc:
            print('  URL不包含域名，返回False')
            return False
    except Exception as e:
        print(f'  URL解析错误: {str(e)}，返回False')
        return False

    print('  URL有效，返回True')
    return True

def search(query, engine='search_std'):
    """
    使用智谱AI搜索引擎执行搜索

    Args:
        query (str): 搜索查询
        engine (str, optional): 搜索引擎类型. Defaults to 'search_std'.

    Returns:
        dict: 搜索结果
    """
    # 获取API密钥
    api_key = os.getenv('ZHIPUAI_API_KEY')

    if not api_key:
        return {'error': '智谱AI API密钥未配置'}

    # 准备请求参数 - 保持简单
    payload = {
        'search_engine': engine,  # 搜索引擎类型
        'search_query': query[:78]  # 限制查询不超过78个字符
    }

    # 智谱AI搜索引擎不支持高级选项
    # 只使用基本参数

    print(f'智谱AI 请求参数: {payload}')

    # 准备请求头部 - 保持简单
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    print(f'智谱AI 请求负载: {json.dumps(payload)}')

    # 发送请求 - 保持简单
    try:
        print(f'发送请求到智谱AI: 查询="{query}", 引擎={engine}')

        response = requests.post(
            'https://open.bigmodel.cn/api/paas/v4/web_search',
            json=payload,
            headers=headers,
            timeout=30  # 增加超时时间
        )

        # 检查响应状态码
        print(f'智谱AI 响应状态码: {response.status_code}')
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f'智谱AI API HTTP错误: {str(e)}')
        # 尝试获取错误响应的详细信息
        try:
            error_detail = response.json()
            print(f'智谱AI API错误详情: {json.dumps(error_detail, ensure_ascii=False)}')

            # 如果是400错误，可能是API密钥或请求格式问题
            if response.status_code == 400:
                print('尝试使用备用搜索结果')

                # 检查错误消息，如果是API密钥问题，打印更详细的信息
                error_message = error_detail.get('message', '')
                if 'api key' in error_message.lower() or 'apikey' in error_message.lower() or 'token' in error_message.lower():
                    print('智谱AI API密钥可能已过期或无效，请更新API密钥')
                # 返回一个带有错误信息的搜索结果
                return {
                    'id': f'zhipuai_error_400_{int(time.time())}',
                    'created': int(time.time()),
                    'search_intent': [
                        {
                            'query': query,
                            'intent': 'SEARCH_ALL',
                            'keywords': query
                        }
                    ],
                    'search_result': [
                        {
                            'title': f'搜索“{query}”',
                            'link': f'https://www.baidu.com/s?wd={quote(query)}',
                            'content': f'智谱AI搜索引擎暂时不可用，请尝试使用其他搜索引擎或稍后再试。\n\n错误信息: {str(e)}',
                            'media': 'Baidu',
                            'icon': '',
                            'refer': '错误'
                        }
                    ]
                }
        except:
            print(f'智谱AI API错误响应文本: {response.text}')
    except requests.exceptions.RequestException as e:
        print(f'智谱AI API请求错误: {str(e)}')
        # 创建一个错误响应
        return {
            'id': f'zhipuai_error_{int(time.time())}',
            'created': int(time.time()),
            'search_intent': [
                {
                    'query': query,
                    'intent': 'SEARCH_NONE',
                    'keywords': query
                }
            ],
            'search_result': [
                {
                    'title': '智谱AI 搜索错误',
                    'link': '#',
                    'content': f'请求智谱AI搜索引擎时发生错误: {str(e)}',
                    'media': '智谱AI',
                    'icon': '',
                    'refer': '错误'
                }
            ]
        }

    # 获取响应数据 - 简化处理
    try:
        result = response.json()
        print(f'智谱AI 搜索响应成功，结果数量: {len(result.get("search_result", []))}')

        # 确保处理搜索结果的代码被执行
        print('开始处理搜索结果...')
    except json.JSONDecodeError as e:
        print(f'智谱AI 响应JSON解析错误: {str(e)}')
        # 创建一个错误响应
        return {
            'id': f'zhipuai_json_error_{int(time.time())}',
            'created': int(time.time()),
            'search_intent': [
                {
                    'query': query,
                    'intent': 'SEARCH_NONE',
                    'keywords': query
                }
            ],
            'search_result': [
                {
                    'title': '智谱AI 响应格式错误',
                    'link': '#',
                    'content': f'无法解析智谱AI的响应: {str(e)}\n原始响应: {response.text[:500]}...',
                    'media': '智谱AI',
                    'icon': '',
                    'refer': '错误'
                }
            ]
        }

    # 确保响应结构符合前端期望
    print(f'智谱AI搜索响应成功，进行最小必要的处理')

    # 确保搜索结果字段存在
    if 'search_result' not in result:
        print('响应中没有search_result字段，创建空列表')
        result['search_result'] = []

    return result

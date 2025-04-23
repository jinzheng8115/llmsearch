#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SearXNG搜索引擎实现
"""

import os
import json
import time
import requests
from urllib.parse import urlparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def search(query, engines=None, language=None, safesearch=None, time_range=None, count=None):
    """
    使用SearXNG搜索引擎执行搜索

    Args:
        query (str): 搜索查询
        engines (str, optional): 要使用的搜索引擎，用逗号分隔。默认为None，使用SearXNG默认引擎。
        language (str, optional): 搜索结果的语言。默认为'auto'。
        safesearch (int, optional): 安全搜索级别(0-2)。默认为1。
        time_range (str, optional): 搜索结果的时间范围。可选值: day, week, month, year。
        count (int, optional): 返回结果的数量。默认为None，使用SearXNG默认值。

    Returns:
        dict: 搜索结果，格式化为与智谱AI兼容的格式
    """
    # 获取API主机地址
    api_host = os.getenv('SEARXNG_API_HOST')

    if not api_host:
        return {
            'id': f'searxng_error_{int(time.time())}',
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
                    'title': 'SearXNG API配置错误',
                    'link': '#',
                    'content': 'SearXNG API主机地址未配置。请在.env文件中设置SEARXNG_API_HOST环境变量。',
                    'media': 'SearXNG',
                    'icon': '',
                    'refer': '错误'
                }
            ]
        }

    # 准备搜索参数
    params = {
        'q': query,
        'format': 'json',
        'language': language if language is not None else os.getenv('SEARXNG_DEFAULT_LANGUAGE', 'auto'),
        'safesearch': safesearch if safesearch is not None else int(os.getenv('SEARXNG_DEFAULT_SAFESEARCH', '0'))
    }

    # 添加可选参数
    if engines:
        params['engines'] = engines
    else:
        # 从环境变量中读取默认引擎
        default_engines = os.getenv('SEARXNG_DEFAULT_ENGINES')
        if default_engines:
            params['engines'] = default_engines

    if time_range:
        params['time_range'] = time_range

    # 如果指定了结果数量，添加到参数中
    # 注意：SearXNG API可能不直接支持count参数，我们会在后续处理中限制结果数量
    max_results = 10  # 默认值
    if count is not None:
        max_results = count

    print(f'SearXNG 请求URL: {api_host.rstrip("/")}/search')
    print(f'SearXNG 请求参数: {json.dumps(params)}')

    # 创建一个与智谱AI响应格式兼容的结果
    converted_result = {
        # 根据智谱AI响应格式添加必要字段
        'id': f'searxng_{int(time.time())}',  # 生成一个任务ID
        'created': int(time.time()),  # 当前时间的Unix时间戳
        'search_intent': [
            {
                'query': query,  # 原始搜索query
                'intent': 'SEARCH_ALL',  # 搜索全网
                'keywords': query  # 搜索关键词
            }
        ],
        'search_result': [],  # 搜索结果列表
        'suggestions': [],    # 搜索建议列表
        'corrections': [],    # 拼写纠正列表
        'answers': [],        # 答案列表
        'infoboxes': [],      # 信息框列表
        'meta': {
            'source': 'SearXNG',
            'engines': engines or os.getenv('SEARXNG_DEFAULT_ENGINES', 'default'),
            'totalResults': 0,
            'time': 0
        }
    }

    try:
        # 执行搜索请求
        response = requests.get(
            f"{api_host.rstrip('/')}/search",
            params=params,
            timeout=10
        )
        response.raise_for_status()

        # 解析结果
        result = response.json()
        print(f'SearXNG 响应结构: {json.dumps(result)[:500]}...')

        # 处理搜索结果
        if 'results' in result and isinstance(result['results'], list):
            # 限制结果数量
            results = result['results'][:max_results]

            # 添加元数据
            converted_result['meta']['totalResults'] = result.get('number_of_results', len(results))
            converted_result['meta']['time'] = result.get('search_time', 0)

            # 处理建议、纠正和答案
            if 'suggestions' in result and isinstance(result['suggestions'], list):
                converted_result['suggestions'] = result['suggestions']

            if 'corrections' in result and isinstance(result['corrections'], list):
                converted_result['corrections'] = result['corrections']

            if 'answers' in result and isinstance(result['answers'], list):
                for answer in result['answers']:
                    answer_item = {
                        'title': answer.get('title', '答案'),
                        'content': answer.get('content', ''),
                        'link': answer.get('url', '#'),
                        'media': 'SearXNG',
                        'icon': '',
                        'refer': '答案'
                    }
                    converted_result['answers'].append(answer_item)

            if 'infoboxes' in result and isinstance(result['infoboxes'], list):
                for infobox in result['infoboxes']:
                    infobox_item = {
                        'title': infobox.get('title', '信息框'),
                        'content': infobox.get('content', ''),
                        'link': infobox.get('url', '#'),
                        'media': infobox.get('engine', 'SearXNG'),
                        'icon': infobox.get('img_src', ''),
                        'id': infobox.get('id', ''),
                        'infobox': True
                    }
                    converted_result['infoboxes'].append(infobox_item)

            # 转换每个搜索结果
            for item in results:
                # 提取必要的字段
                title = item.get('title', '')
                url = item.get('url', '#')
                content = item.get('content', '')
                engine = item.get('engine', '')
                template = item.get('template', '')

                # 尝试提取网站名称
                try:
                    domain = urlparse(url).netloc
                    media = domain
                except:
                    media = engine or 'SearXNG'

                # 提取更多信息（如果有）
                img_src = item.get('img_src', '')
                thumbnail = item.get('thumbnail', '')
                publishedDate = item.get('publishedDate', '')

                # 确定结果类型
                refer = ''
                if template == 'images.html' or 'images' in engine.lower() or img_src or thumbnail:
                    refer = '图片'
                elif template == 'videos.html' or 'videos' in engine.lower():
                    refer = '视频'
                elif template == 'torrent.html' or 'torrent' in engine.lower():
                    refer = '种子'
                elif template == 'map.html' or 'map' in engine.lower():
                    refer = '地图'

                # 构建内容
                if img_src:
                    content += f'<br><img src="{img_src}" alt="{title}" style="max-width:200px;">'
                elif thumbnail:
                    content += f'<br><img src="{thumbnail}" alt="{title}" style="max-width:200px;">'

                # 添加元数据到内容
                if publishedDate:
                    content += f'<br><small>发布时间: {publishedDate}</small>'

                if engine:
                    content += f'<br><small>搜索引擎: {engine}</small>'

                # 创建搜索结果项
                search_item = {
                    'title': title,
                    'link': url,
                    'content': content,
                    'media': media,
                    'icon': '',
                    'refer': refer
                }

                # 添加其他可能的字段
                for key in ['score', 'category', 'pretty_url', 'parsed_url', 'positions']:
                    if key in item:
                        search_item[key] = item[key]

                converted_result['search_result'].append(search_item)

        else:
            # 如果没有找到结果
            if 'error' in result:
                error_message = result.get('error', 'SearXNG未返回搜索结果')
            else:
                error_message = '未找到搜索结果'

            # 处理其他可能的字段
            if 'suggestions' in result and isinstance(result['suggestions'], list):
                converted_result['suggestions'] = result['suggestions']

            if 'corrections' in result and isinstance(result['corrections'], list):
                converted_result['corrections'] = result['corrections']

            if 'answers' in result and isinstance(result['answers'], list):
                for answer in result['answers']:
                    answer_item = {
                        'title': answer.get('title', '答案'),
                        'content': answer.get('content', ''),
                        'link': answer.get('url', '#'),
                        'media': 'SearXNG',
                        'icon': '',
                        'refer': '答案'
                    }
                    converted_result['answers'].append(answer_item)

            # 添加错误信息到搜索结果
            search_item = {
                'title': 'SearXNG 搜索结果',
                'link': '#',
                'content': error_message,
                'media': 'SearXNG',
                'icon': '',
                'refer': ''
            }
            converted_result['search_result'].append(search_item)

    except requests.exceptions.RequestException as e:
        print(f'SearXNG API请求错误: {str(e)}')
        # 创建一个错误响应
        search_item = {
            'title': 'SearXNG 搜索错误',
            'link': '#',
            'content': f'请求SearXNG搜索引擎时发生错误: {str(e)}',
            'media': 'SearXNG',
            'icon': '',
            'refer': '错误'
        }
        converted_result['search_result'].append(search_item)

    except json.JSONDecodeError as e:
        print(f'SearXNG 响应JSON解析错误: {str(e)}')
        # 创建一个错误响应
        search_item = {
            'title': 'SearXNG 响应格式错误',
            'link': '#',
            'content': f'无法解析SearXNG的响应: {str(e)}',
            'media': 'SearXNG',
            'icon': '',
            'refer': '错误'
        }
        converted_result['search_result'].append(search_item)

    return converted_result

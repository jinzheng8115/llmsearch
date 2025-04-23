#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Bocha AI搜索引擎实现
"""

import os
import json
import time
import requests

def search(query, freshness=None, summary=None, count=None, page=None):
    """
    使用Bocha AI搜索引擎执行搜索

    Args:
        query (str): 搜索查询，必填参数
        freshness (str, optional): 搜索指定时间范围内的网页。可选值：oneDay，oneWeek，oneMonth，oneYear，noLimit（默认），
                                  或者日期格式如"YYYY-MM-DD..YYYY-MM-DD"或"YYYY-MM-DD"。
        summary (bool, optional): 是否显示文本摘要。True为显示，False为不显示（默认）。
        count (int, optional): 返回结果的条数，范围为1-50，默认为10。
        page (int, optional): 页码，默认为1。

    Returns:
        dict: 搜索结果，格式化为与智谱AI兼容的格式
    """
    # 获取API密钥
    api_key = os.getenv('BOCHAAI_API_KEY')

    if not api_key:
        return {'error': 'Bocha AI API密钥未配置'}

    # 准备请求参数
    payload = {
        'query': query  # 必填参数：搜索查询
    }

    # 添加可选参数
    if freshness is not None:
        payload['freshness'] = freshness

    if summary is not None:
        payload['summary'] = summary

    if count is not None:
        # 确保 count 在有效范围内（1-50）
        payload['count'] = max(1, min(50, count))

    if page is not None:
        # 确保 page 是正整数
        payload['page'] = max(1, page)

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    print(f'Bocha AI 请求URL: https://api.bochaai.com/v1/web-search')
    print(f'Bocha AI 请求负载: {json.dumps(payload)}')

    # 发送请求
    response = requests.post(
        'https://api.bochaai.com/v1/web-search',
        json=payload,
        headers=headers,
        timeout=10  # 设置超时时间
    )

    # 检查响应状态
    response.raise_for_status()

    # 获取响应数据
    result = response.json()
    print(f'Bocha AI 响应结构: {json.dumps(result, indent=2)}')

    # 创建一个与智谱AI响应格式兼容的结果
    converted_result = {
        # 根据智谱AI响应格式添加必要字段
        'id': f'bochaai_{int(time.time())}',  # 生成一个任务ID
        'created': int(time.time()),  # 当前时间的Unix时间戳
        'search_intent': [
            {
                'query': query,  # 原始搜索query
                'intent': 'SEARCH_ALL',  # 搜索全网
                'keywords': query  # 搜索关键词
            }
        ],
        'search_result': [],  # 搜索结果列表
        'meta': {}  # Bocha AI特有的元数据，不影响智谱AI格式兼容性
    }

    # 根据Bocha AI文档处理响应
    print('完整响应结构:', json.dumps(result, indent=2, ensure_ascii=False)[:1000], '...')

    # 检查是否有data字段，这是Bocha AI响应的最外层结构
    if 'data' in result and isinstance(result['data'], dict):
        data = result['data']
        # 根据文档，检查 webPages 字段
        if 'webPages' in data and isinstance(data['webPages'], dict) and 'value' in data['webPages']:
            web_pages = data['webPages']
            web_page_values = web_pages.get('value', [])
            total_results = web_pages.get('totalEstimatedMatches', 0)

            # 将元数据添加到响应中
            converted_result['meta'] = {
                'totalResults': total_results,
                'source': 'Bocha AI',
                'webSearchUrl': web_pages.get('webSearchUrl', ''),
                'someResultsRemoved': web_pages.get('someResultsRemoved', False)
            }

            # 如果有查询上下文信息，添加到元数据中
            if 'queryContext' in data and isinstance(data['queryContext'], dict):
                query_context = data['queryContext']
                converted_result['meta']['originalQuery'] = query_context.get('originalQuery', query)

            print(f'找到 Bocha AI 搜索结果: {len(web_page_values)} 条，总计: {total_results}')

            for item in web_page_values:
                # 输出每个结果项的字段
                print(f'结果项字段: {list(item.keys())}')

                # 根据文档的WebPageValue字段定义提取数据
                title = item.get('name', '')
                url = item.get('url', '#')
                snippet = item.get('snippet', '')
                site_name = item.get('siteName', 'Bocha AI')
                display_url = item.get('displayUrl', url)
                date_published = item.get('datePublished', '')
                language = item.get('language', '')

                # 如果有summary字段且用户请求了摘要，优先使用summary
                if 'summary' in item and summary is True:
                    snippet = item.get('summary', snippet)

                # 构建更丰富的内容
                content = snippet
                if date_published:
                    content += f'<br><small>发布时间: {date_published}</small>'
                if site_name:
                    content += f'<br><small>网站: {site_name}</small>'
                if language:
                    content += f'<br><small>语言: {language}</small>'

                # 根据智谱AI响应格式创建搜索结果项
                search_item = {
                    'title': title,  # 标题
                    'link': url,     # 结果链接
                    'content': content,  # 内容摘要
                    'media': site_name or display_url,  # 网站名称
                    'icon': '',      # 网站图标，博查AI不提供这个字段
                    'refer': ''      # 角标序号，博查AI不提供这个字段
                }
                converted_result['search_result'].append(search_item)
            return converted_result
        # 如果没有webPages字段，尝试检查data中是否有images字段
        elif 'images' in data and isinstance(data['images'], dict) and 'value' in data['images']:
            # 如果有图片结果但没有网页结果，也可以展示图片信息
            image_values = data['images'].get('value', [])
            print(f'找到 Bocha AI 图片结果: {len(image_values)} 条')

            # 将图片结果转换为搜索结果
            for item in image_values[:5]:  # 只取前5张图片
                # 根据文档中的ImageValue字段定义提取数据
                title = item.get('name', '相关图片')
                url = item.get('hostPageUrl', item.get('contentUrl', '#'))
                thumbnail = item.get('thumbnailUrl', '')
                content = f'图片内容: {item.get("name", "")}'
                if thumbnail:
                    content += f'<br><img src="{thumbnail}" alt="{title}" style="max-width:200px;">'
                host = item.get('hostPageDisplayUrl', 'Bocha AI')
                date_published = item.get('datePublished', '')
                if date_published:
                    content += f'<br>发布时间: {date_published}'

                # 根据智谱AI响应格式创建图片搜索结果项
                search_item = {
                    'title': title or '相关图片',  # 标题
                    'link': url,     # 结果链接
                    'content': content,  # 内容摘要
                    'media': host,   # 网站名称
                    'icon': '',      # 网站图标
                    'refer': '图片'  # 角标序号，标记为图片结果
                }
                converted_result['search_result'].append(search_item)

            if converted_result['search_result']:
                return converted_result
        # 如果没有webPages和images字段，尝试检查data中是否有videos字段
        elif 'videos' in data and isinstance(data['videos'], dict) and 'value' in data['videos']:
            # 如果有视频结果但没有网页和图片结果，也可以展示视频信息
            video_values = data['videos'].get('value', [])
            print(f'找到 Bocha AI 视频结果: {len(video_values)} 条')

            # 将视频结果转换为搜索结果
            for item in video_values[:5]:  # 只取前5个视频
                # 根据文档中的VideoValue字段定义提取数据
                title = item.get('name', '相关视频')
                url = item.get('hostPageUrl', item.get('contentUrl', '#'))
                thumbnail = item.get('thumbnailUrl', '')
                description = item.get('description', '')
                publisher = ''
                if 'publisher' in item and isinstance(item['publisher'], list) and len(item['publisher']) > 0:
                    publisher = item['publisher'][0].get('name', '')

                # 构建视频内容
                content = description or f'视频: {title}'
                if thumbnail:
                    content += f'<br><img src="{thumbnail}" alt="{title}" style="max-width:200px;">'
                if publisher:
                    content += f'<br><small>发布者: {publisher}</small>'
                if item.get('duration'):
                    content += f'<br><small>时长: {item.get("duration")}</small>'
                if item.get('datePublished'):
                    content += f'<br><small>发布时间: {item.get("datePublished")}</small>'

                # 根据智谱AI响应格式创建视频搜索结果项
                search_item = {
                    'title': title or '相关视频',  # 标题
                    'link': url,     # 结果链接
                    'content': content,  # 内容摘要
                    'media': publisher or 'Bocha AI',  # 发布者或网站名称
                    'icon': '',      # 网站图标
                    'refer': '视频'  # 角标序号，标记为视频结果
                }
                converted_result['search_result'].append(search_item)

            if converted_result['search_result']:
                return converted_result

    # 如果没有找到data字段或者data中没有webPages/images字段
    print('未找到 Bocha AI 搜索结果字段')

    # 尝试检查是否有 results 字段（兼容其他可能的格式）
    if 'results' in result and isinstance(result['results'], list):
        print(f'找到备用 results 字段: {len(result["results"])} 条')

        for item in result['results']:
            title = item.get('title', '')
            url = item.get('url', '#')
            snippet = item.get('snippet', '')
            source = item.get('source', 'Bocha AI')

            # 根据智谱AI响应格式创建备用搜索结果项
            search_item = {
                'title': title,  # 标题
                'link': url,     # 结果链接
                'content': snippet,  # 内容摘要
                'media': source,  # 网站名称
                'icon': '',      # 网站图标
                'refer': ''      # 角标序号
            }
            converted_result['search_result'].append(search_item)
    else:
        # 如果没有找到有效的结果字段，创建一个错误结果
        error_message = '无法解析 Bocha AI 响应格式。请查看控制台了解详情。'
        # 根据智谱AI响应格式创建错误结果项
        search_item = {
            'title': 'Bocha AI 搜索结果解析错误',  # 标题
            'link': '#',  # 结果链接
            'content': error_message,  # 内容摘要
            'media': 'Bocha AI',  # 网站名称
            'icon': '',  # 网站图标
            'refer': '错误'  # 角标序号，标记为错误结果
        }
        converted_result['search_result'].append(search_item)

    return converted_result

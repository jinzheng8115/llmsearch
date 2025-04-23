#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
搜索引擎 - Python Flask版本
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory, make_response, Response
from flask_cors import CORS
from dotenv import load_dotenv

# 导入搜索引擎模块
from search_engines import zhipuai, bochaai, searxng

# AI搜索总结模块已移除

# 导入聊天API模块
import chat_api

# 导入智能联网搜索模块
import chat_with_intelligent_search_new as chat_with_intelligent_search

# 加载环境变量
load_dotenv()

app = Flask(__name__, static_folder='.')

# 启用CORS
CORS(app)

@app.route('/')
def index():
    """提供首页，直接返回聊天页面"""
    return send_from_directory('.', 'chat.html')

@app.route('/<path:path>')
def static_files(path):
    """提供静态文件"""
    return send_from_directory('.', path)

# 搜索API端点已移除

# 搜索总结路由已移除

@app.route('/api/chat', methods=['POST'])
def chat():
    """普通聊天API端点"""
    # 获取请求数据
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': '缺少必要的查询参数'}), 400

    query = data['query']
    model_id = data.get('model_id')  # 可选参数，指定使用的模型
    stream = data.get('stream', False)  # 是否使用流式输出

    if not query.strip():
        return jsonify({'error': '查询不能为空'}), 400

    try:
        print(f'发送普通聊天请求: {query}, 模型: {model_id or "默认"}, 流式: {stream}')

        # 调用聊天API
        if stream:
            # 流式输出模式
            def generate():
                print(f"\n>>> 开始普通聊天流式输出处理")
                response = chat_api.chat(query, model_id, stream=True)

                # 首先发送一个特殊的消息，表示流式输出开始
                yield f"data: {{\"role\": \"assistant\", \"content\": \"\"}}\n\n"

                # 恢复原始代码
                for chunk in response.iter_lines():
                    if chunk:
                        # 如果 chunk 是字节对象，则解码，否则直接使用
                        chunk_text = chunk.decode('utf-8') if isinstance(chunk, bytes) else chunk

                        # 打印调试信息
                        print(f">>> 原始数据块: {chunk_text}")

                        # 尝试解析原始数据块，看是否已经是JSON
                        try:
                            # 如果数据块以 'data: ' 开头，则移除这个前缀
                            json_text = chunk_text.replace('data: ', '', 1) if chunk_text.startswith('data: ') else chunk_text
                            json_data = json.loads(json_text)

                            # 如果已经是JSON且包含choices/delta/content，直接转发
                            if 'choices' in json_data and len(json_data['choices']) > 0 and 'delta' in json_data['choices'][0] and 'content' in json_data['choices'][0]['delta']:
                                content = json_data['choices'][0]['delta']['content']
                                if content:
                                    # 创建前端期望的格式
                                    frontend_data = {
                                        "content": content,
                                        "role": "assistant"
                                    }
                                    yield f"data: {json.dumps(frontend_data)}\n\n"
                                continue
                        except json.JSONDecodeError:
                            # 不是JSON，或格式不符，包装成标准格式
                            pass

                        # 如果不是特殊格式，将原始文本包装成前端期望的JSON格式
                        if chunk_text.startswith('data: '):
                            # 如果已经是 SSE 格式，直接转发
                            yield chunk_text + "\n"
                        else:
                            # 否则包装成前端期望的JSON格式
                            frontend_data = {
                                "content": chunk_text,
                                "role": "assistant"
                            }
                            yield f"data: {json.dumps(frontend_data)}\n\n"

                # 发送结束消息 - 使用两种格式的结束消息，确保前端能正确处理
                yield f"data: {{\"done\": true}}\n\n"
                yield f"data: [DONE]\n\n"
                print(f">>> 普通聊天流式输出完成")

            return Response(generate(), content_type='text/event-stream')
        else:
            # 非流式模式
            result = chat_api.chat(query, model_id)

            # 创建响应并添加缓存控制头
            response = make_response(jsonify(result))
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response

    except Exception as e:
        # 记录错误
        print(f'聊天API错误: {str(e)}')

        # 返回错误信息
        error_response = {
            'error': '聊天请求失败',
            'message': str(e)
        }

        return jsonify(error_response), 500

@app.route('/api/chat_with_search', methods=['POST'])
def chat_with_search():
    """联网搜索聊天API端点"""
    # 获取请求数据
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': '缺少必要的查询参数'}), 400

    query = data['query']
    engine = data.get('engine', 'search_std')  # 默认使用智谱基础搜索
    count = data.get('count', 10)  # 默认结果数量
    model_id = data.get('model_id')  # 可选参数，指定使用的模型
    stream = data.get('stream', False)  # 是否使用流式输出

    # SearXNG特殊参数，从环境变量中读取默认值
    searxng_engines = data.get('searxng_engines', os.getenv('SEARXNG_DEFAULT_ENGINES', 'bing,baidu,360search,quark,sogou'))
    searxng_language = data.get('searxng_language', os.getenv('SEARXNG_DEFAULT_LANGUAGE', 'auto'))
    searxng_safesearch = data.get('searxng_safesearch', int(os.getenv('SEARXNG_DEFAULT_SAFESEARCH', '0')))
    searxng_time_range = data.get('searxng_time_range', '')

    if not query.strip():
        return jsonify({'error': '查询不能为空'}), 400

    # 验证搜索引擎
    valid_engines = ['search_std', 'bochaai', 'searxng']
    if engine not in valid_engines:
        return jsonify({'error': f'无效的搜索引擎: {engine}'}), 400

    try:
        print(f'发送联网搜索聊天请求: {query}, 搜索引擎: {engine}, 结果数量: {count}, 模型: {model_id or "默认"}, 流式: {stream}')

        # 准备搜索参数
        search_params = {}

        # 如果是SearXNG搜索引擎，添加特殊参数
        if engine == 'searxng':
            if searxng_engines:
                search_params['engines'] = searxng_engines
            search_params['language'] = searxng_language
            search_params['safesearch'] = int(searxng_safesearch)
            if searxng_time_range:
                search_params['time_range'] = searxng_time_range

        print(f'搜索参数: {search_params}')

        # 调用智能联网搜索聊天API
        if stream:
            # 流式输出模式
            def generate():
                print(f"\n>>> 开始流式输出处理")
                response = chat_with_intelligent_search.chat_with_intelligent_search(query, engine, count, model_id, stream=True, **search_params)

                # 不再首先发送空消息，让 chat_with_intelligent_search 控制初始块

                # 直接迭代并传递来自 chat_with_intelligent_search 的已格式化块
                try:
                    # 重新加入初始空消息，前端可能需要它来初始化
                    yield f"data: {{\"role\": \"assistant\", \"content\": \"\"}}\n\n"
                    for line in response.iter_lines():
                        if line:
                            # print(f">>> generate: 转发块: {line.strip()}") # 调试时取消注释
                            # 如果 line 是字节对象，则解码，否则直接使用
                            if isinstance(line, bytes):
                                line_str = line.decode('utf-8')
                            else:
                                line_str = line

                            # 打印调试信息
                            print(f">>> 转发数据块: {line_str}")

                            # 确保数据块以 'data: ' 开头
                            if not line_str.startswith('data: '):
                                line_str = f"data: {line_str}"
                                print(f">>> 添加 'data: ' 前缀: {line_str}")

                            yield line_str
                    print(f">>> 流式输出转发完成")
                except Exception as e:
                    print(f">>> 在 generate 函数中处理流时出错: {e}")
                    # 尝试发送一个错误块给前端
                    try:
                        error_data = {
                            "error": f"处理响应流时发生服务器错误: {e}"
                        }
                        yield f"data: {json.dumps(error_data)}\n\n"
                        # 确保在错误后也发送 done 标记
                        yield f"data: {{\"done\": true}}\n\n"
                    except Exception as final_e:
                        print(f">>> 发送最终错误块失败: {final_e}")
                        # 即使发送错误块失败，也尝试发送 done 标记
                        try:
                            yield f"data: {{\"done\": true}}\n\n"
                        except Exception as done_e:
                            print(f">>> 发送最终 done 标记失败: {done_e}")

            return Response(generate(), content_type='text/event-stream')
        else:
            # 非流式模式
            result = chat_with_intelligent_search.chat_with_intelligent_search(query, engine, count, model_id, **search_params)

            # 创建响应并添加缓存控制头
            response = make_response(jsonify(result))
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response

    except Exception as e:
        # 记录错误
        print(f'联网搜索聊天API错误: {str(e)}')

        # 返回错误信息
        error_response = {
            'error': '联网搜索聊天请求失败',
            'message': str(e)
        }

        return jsonify(error_response), 500

@app.route('/api/settings')
def get_settings():
    """获取服务器端设置"""
    return jsonify({
        'defaultModel': os.getenv('ZHIPUAI_MODEL'),
        'defaultSearchEngine': 'search_std',
        'defaultResultCount': 10,
        'searxngLanguage': os.getenv('SEARXNG_DEFAULT_LANGUAGE', 'auto'),
        'searxngSafesearch': int(os.getenv('SEARXNG_DEFAULT_SAFESEARCH', '0')),
        'searxngEngines': os.getenv('SEARXNG_DEFAULT_ENGINES', 'bing,baidu,360search,quark,sogou'),
        'searxngTimeRange': os.getenv('SEARXNG_DEFAULT_TIME_RANGE', 'month'),
        'bochaaiTimeRange': os.getenv('BOCHAAI_DEFAULT_FRESHNESS', 'oneMonth'),
        'availableModels': [
            {'id': 'zhipuai', 'name': '智谱AI GLM-4'},
            {'id': 'deepseek-reasoner', 'name': 'DeepSeek Reasoner'}
        ]
    })

if __name__ == '__main__':
    # 获取端口，默认为5000
    port = int(os.getenv('PORT', 5000))

    # 启动服务器
    app.run(host='0.0.0.0', port=port, debug=True)

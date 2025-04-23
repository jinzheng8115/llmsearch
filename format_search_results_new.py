#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
搜索结果格式化模块

这个模块提供了格式化搜索结果的功能，根据不同问题类型提供不同的指导说明。
"""

def get_common_instruction():
    """
    获取通用的指导文本
    
    Returns:
        str: 包含对不健康内容过滤的指导文本
    """
    return """在回答正文中，可以使用数字引用来指代特定来源，例如："根据来源[1]，..."。在回答的最后，请添加"参考来源"部分，并列出搜索结果。

重要：请对每个搜索结果进行审核。如果某个搜索结果的标题或内容含有不健康、不适当或有害的内容（如色情、暴力、仇恨言论、非法活动等），请不要在参考来源部分列出该结果，也不要在回答中引用该结果的内容。"""

def format_search_results(results, query, question_type="准确答案问题"):
    """
    格式化搜索结果为文本

    Args:
        results: 搜索结果列表
        query: 搜索查询
        question_type: 问题类型，"开放性问题"或"准确答案问题"

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
        url = result.get('link', '#')

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

    # 获取通用指导文本
    common_instruction = get_common_instruction()

    # 检测查询中的关键词，判断是否是特定类型的问题
    data_keywords = ["税率", "关税", "经济", "数据", "统计", "价格", "比例", "数量", "多少"]
    news_keywords = ["新闻", "时事", "最新", "近期", "发布", "公布", "宣布", "报道"]
    tech_keywords = ["技术", "原理", "定义", "学术", "研究", "理论", "方法", "如何实现"]
    history_keywords = ["历史", "文化", "传统", "起源", "发展史", "演变"]
    
    # 检测查询属于哪种类型
    query_lower = query.lower()
    is_data_query = any(keyword in query_lower for keyword in data_keywords)
    is_news_query = any(keyword in query_lower for keyword in news_keywords)
    is_tech_query = any(keyword in query_lower for keyword in tech_keywords)
    is_history_query = any(keyword in query_lower for keyword in history_keywords)
    
    # 根据问题类型和内容类型提供不同的指导说明
    if is_data_query:
        # 数据类问题
        instruction_text = f'''
请基于以上信息回答问题。这是一个数据类问题，请注意：

1. 使用清晰的标题和子标题结构
2. 将关键数据用粗体或列表格式突出显示
3. 如有多组数据，使用有序列表呈现
4. 包含数据的时间范围和来源
5. 提供简要的数据解读和含义

{common_instruction}
'''
    elif is_news_query:
        # 新闻时事类问题
        instruction_text = f'''
请基于以上信息回答问题。这是一个新闻时事类问题，请注意：

1. 开头提供简洁的事件概述
2. 按时间顺序或重要性排列事件发展
3. 清晰标注时间、地点和相关人物
4. 区分事实和观点，并标注不同来源的观点
5. 如有多方观点，应平衡呈现

{common_instruction}
'''
    elif is_tech_query:
        # 技术学术类问题
        instruction_text = f'''
请基于以上信息回答问题。这是一个技术或学术类问题，请注意：

1. 先提供简明的定义或解释
2. 使用逐步深入的方式展开内容
3. 如有专业术语，提供简洁解释
4. 如有多种理论或方法，清晰列出并比较
5. 如适用，提供实际应用案例

{common_instruction}
'''
    elif is_history_query:
        # 历史文化类问题
        instruction_text = f'''
请基于以上信息回答问题。这是一个历史或文化类问题，请注意：

1. 提供时间背景和历史范围
2. 如有序列事件，使用时间线或分期呈现
3. 强调文化背景和历史语境
4. 如有不同观点或解释，平衡呈现

{common_instruction}
'''
    elif question_type == "开放性问题":
        # 开放性问题
        instruction_text = f'''
请基于以上信息回答问题。这是一个开放性问题，请注意：

1. 提供多角度的分析
2. 列出不同的观点和理论
3. 分析各种因素和影响
4. 如有争议点，平衡呈现不同立场
5. 在结尾提供全面的总结

{common_instruction}
'''
    else:  # 准确答案问题
        instruction_text = f'''
请基于以上信息回答问题。这是一个需要准确答案的问题，请提供简洁、直接的答案，并确保信息的准确性。使用清晰的标题和列表格式来组织信息，并将关键信息用粗体标出。

{common_instruction}
'''

    # 合并所有部分
    formatted_text = content_text + sources_text + instruction_text

    return formatted_text

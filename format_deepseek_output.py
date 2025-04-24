#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DeepSeek Reasoner 模型输出格式化模块

这个模块提供了格式化 DeepSeek Reasoner 模型输出的功能，
使其展示效果与智谱 AI 模型一样好。
"""

import re


def format_deepseek_output(content):
    """
    格式化 DeepSeek Reasoner 模型的输出

    Args:
        content: DeepSeek Reasoner 模型的原始输出内容

    Returns:
        格式化后的内容
    """
    if not content:
        return content

    # 1. 处理标题格式
    # 将 #### 格式的标题转换为标准 Markdown 标题
    content = re.sub(r'#{1,4}\s+([一二三四五六七八九十、]+、*)?([^#\n]+)',
                    lambda m: format_heading(m), content)

    # 2. 处理引用和参考文献
    # 规范化引用格式
    content = re.sub(r'\(来源\[(\d+)\]\)', r'[参考文献\1]', content)
    content = re.sub(r'\(来源\[(\d+)\]\[(\d+)\]\[(\d+)\]\)', r'[参考文献\1][参考文献\2][参考文献\3]', content)
    content = re.sub(r'（来源\[(\d+)\]）', r'[参考文献\1]', content)
    content = re.sub(r'\(来源\[(\d+)\]\[(\d+)\]\)', r'[参考文献\1][参考文献\2]', content)
    # 处理冒号后的引用
    content = re.sub(r'(\s+)\(来源\[(\d+)\]\):', r'\1[参考文献\2]:', content)

    # 3. 处理编号问题
    # 修复重复的编号
    content = fix_numbering(content)

    # 4. 处理分隔符和表格
    # 将表格转换为列表
    table_pattern = r'\|([^|\n]+)\|([^|\n]+)\|([^|\n]+)\|'
    content = re.sub(table_pattern, lambda m: format_table_row(m), content)

    # 处理表格分隔线
    content = re.sub(r'\|\s*-+\s*\|\s*-+\s*\|', '', content)

    # 处理剩余的 | 分隔符
    content = re.sub(r'\|([^|\n]+)\|', r'- \1', content)
    content = re.sub(r'([^\n])\|([^\n])', r'\1\n- \2', content)

    # 5. 优化整体排版
    # 确保段落之间有适当的空行
    content = re.sub(r'\n{3,}', '\n\n', content)  # 将多个连续空行替换为两个空行
    content = re.sub(r'([^\n])\n([^\n])', r'\1\n\n\2', content)  # 确保段落之间有空行

    # 6. 处理特殊符号
    # 替换一些可能导致格式问题的特殊符号
    content = content.replace('：', ': ')

    # 7. 处理列表格式
    # 确保列表项有正确的缩进和格式
    content = re.sub(r'^\s*(\d+)\.\s*', r'\1. ', content, flags=re.MULTILINE)  # 确保编号列表格式正确
    content = re.sub(r'^\s*[•·]\s*', r'- ', content, flags=re.MULTILINE)  # 将其他列表标记统一为 -

    # 8. 清理多余的空行和空格
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)  # 删除多余的空行
    content = re.sub(r'\n\s+', '\n', content)  # 删除行首空格

    return content


def format_heading(match):
    """
    格式化标题，将 #### 格式转换为 Markdown 标题

    Args:
        match: 正则表达式匹配对象

    Returns:
        格式化后的标题
    """
    prefix = match.group(1) or ''
    title = match.group(2).strip()

    # 根据标题内容判断级别
    if '一、' in prefix or '一、' in title or '一：' in title:
        return f'\n## {prefix}{title}\n'
    elif '二、' in prefix or '二、' in title or '二：' in title:
        return f'\n## {prefix}{title}\n'
    elif '三、' in prefix or '三、' in title or '三：' in title:
        return f'\n## {prefix}{title}\n'
    elif '四、' in prefix or '四、' in title or '四：' in title:
        return f'\n## {prefix}{title}\n'
    else:
        return f'\n### {prefix}{title}\n'


def format_table_row(match):
    """
    将表格行转换为列表项

    Args:
        match: 正则表达式匹配对象

    Returns:
        格式化后的列表项
    """
    col1 = match.group(1).strip()
    col2 = match.group(2).strip()
    col3 = match.group(3).strip()

    if col1 and col2 and col3:
        if col1 == '类型' and col2 == '代表机构' and col3 == '核心职能':
            # 这是表头，可以忽略
            return ''
        else:
            # 这是表格内容，转换为列表项
            return f"- {col1}: {col2} - {col3}\n"
    return ''


def fix_numbering(content):
    """
    修复内容中的编号问题，确保层级结构清晰

    Args:
        content: 原始内容

    Returns:
        修复编号后的内容
    """
    # 首先处理第一级列表项的特殊模式
    # 匹配形如 "1. 法国双轨制" 的模式
    pattern1 = r'(\d+)\. ([^\n]+)\s*\[\u53c2\u8003\u6587\u732e\d+\]:'  # 匹配带引用的标题行
    pattern2 = r'(\d+)\. ([^\n:]+):'  # 匹配不带引用的标题行

    # 存储所有匹配到的模式
    matches = []

    # 匹配第一种模式
    for match in re.finditer(pattern1, content):
        matches.append((match.start(), match.group()))

    # 匹配第二种模式
    for match in re.finditer(pattern2, content):
        matches.append((match.start(), match.group()))

    # 按位置排序匹配项
    matches.sort()

    # 如果没有匹配项，返回原始内容
    if not matches:
        return content

    # 处理每个匹配项
    result = content
    offset = 0  # 用于跟踪替换后的位置偏移

    # 跟踪当前的部分和编号
    current_section = 0
    section_pattern = r'^\s*##\s+[一二三四五六七八九十]+、'

    # 找到所有的部分标题
    sections = [m.start() for m in re.finditer(section_pattern, content, re.MULTILINE)]
    sections.append(len(content))  # 添加文档结尾作为最后一个部分的结束

    # 对每个部分单独处理编号
    for i in range(len(sections) - 1):
        section_start = sections[i]
        section_end = sections[i+1]
        section_content = content[section_start:section_end]

        # 在当前部分中找到所有的列表项
        section_matches = []
        for match in matches:
            if section_start <= match[0] < section_end:
                section_matches.append(match)

        # 如果没有列表项，继续下一个部分
        if not section_matches:
            continue

        # 处理当前部分的列表项
        for j, (pos, text) in enumerate(section_matches):
            # 提取原始编号
            old_num = re.match(r'(\d+)\.', text).group(1)
            # 新编号是当前列表项的索引+1
            new_num = j + 1

            # 替换编号
            new_text = text.replace(f"{old_num}.", f"{new_num}.")

            # 计算实际位置（考虑之前的替换导致的偏移）
            actual_pos = pos + offset

            # 替换文本
            result = result[:actual_pos] + new_text + result[actual_pos + len(text):]

            # 更新偏移
            offset += len(new_text) - len(text)

    return result


# 测试代码
if __name__ == "__main__":
    test_content = """
#### 一、历史起源与学术自治传统 欧洲现代大学体系可追溯至12-13世纪的中世纪大学。巴黎大学作为早期代表，其发展轨迹体现了教会与学术自治的博弈 (来源[1][3][9])：

1. 教会与王权的双重影响: 中世纪大学最初在教廷与封建君主控制下萌芽，但通过争取特许状逐渐获得学术自主权，形成独特的行会式管理模式。

2. 知识传承与创新: 早期大学以神学、法学、医学为核心学科，通过经院哲学体系培养学者，但13世纪后开始融入亚里士多德哲学等新思潮。

#### 二、国家特色与体系分化 欧洲各国大学体系呈现显著的多样性:

1. 法国双轨制 (来源[3]):

   1. 大学校（Grandes Écoles）与公立大学分立，前者侧重精英教育，后者强调大众化教育

   2. 1968年教育改革后，巴黎大学拆分为13所独立院校，形成分散化体系

1. 北欧实践导向模式 (来源[7]):

   1. 芬兰建立应用科学大学（UAS），与研究型大学形成互补

   2. 挪威推行政府直管体系，90%高校为公立性质

1. 南欧新趋势 (来源[4]):

   1. 葡萄牙斯本大学等通过欧盟Erasmus计划加强国际化

   2. 希腊高校正在改革学分互认体系

#### 三、现代体系的核心架构 当前欧洲大学体系呈现三层结构 (来源[5][9]): | 类型 | 代表机构 | 核心职能 | |------------------|----------------------|------------------------| | 研究型大学联盟 | LERU（24所成员）| 尖端科研与国际竞争力 | | 区域性教学联盟 | 科学布拉德团 | 文化传承与人才培养 | | 专业应用型院校 | 德国FH、芬兰UAS | 职业技能培训 |

#### 四、挑战与改革方向
    """

    formatted = format_deepseek_output(test_content)
    print(formatted)

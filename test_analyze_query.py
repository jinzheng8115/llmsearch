#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试一次性分析查询功能

这个脚本用于测试 analyze_query 函数，验证其是否能正确分析用户查询，
包括是否需要搜索、问题类型和搜索关键词。
"""

import os
import sys
import time
from dotenv import load_dotenv
from chat_with_intelligent_search_new import analyze_query, analyze_search_need, analyze_question_type, extract_search_keywords

# 加载环境变量
load_dotenv()

# 测试用例
TEST_CASES = [
    {
        "name": "需要搜索的开放性问题",
        "query": "欧洲大学体系有什么特点？",
        "expected": {
            "need_search": True,
            "question_type": "开放性问题"
        }
    },
    {
        "name": "需要搜索的准确答案问题",
        "query": "2024年世界杯在哪里举办？",
        "expected": {
            "need_search": True,
            "question_type": "准确答案问题"
        }
    },
    {
        "name": "不需要搜索的问题",
        "query": "你好，请帮我写一首诗",
        "expected": {
            "need_search": False
        }
    }
]

def run_tests(model_id=None):
    """运行测试用例"""
    print("=" * 80)
    print(f"开始测试一次性分析查询功能 (使用模型: {model_id or '默认'})")
    print("=" * 80)

    for i, test_case in enumerate(TEST_CASES):
        print(f"\n测试 {i+1}: {test_case['name']}")
        print(f"查询: {test_case['query']}")

        # 使用合并函数
        print("\n=== 使用合并函数 analyze_query ===")
        need_search, question_type, keywords = analyze_query(test_case['query'], model_id)

        # 验证结果
        expected = test_case['expected']
        if expected.get('need_search') == need_search:
            print(f"✅ 是否需要搜索: 预期 {expected.get('need_search')}, 实际 {need_search}")
        else:
            print(f"❌ 是否需要搜索: 预期 {expected.get('need_search')}, 实际 {need_search}")

        if 'question_type' in expected:
            if expected['question_type'] == question_type:
                print(f"✅ 问题类型: 预期 {expected['question_type']}, 实际 {question_type}")
            else:
                print(f"❌ 问题类型: 预期 {expected['question_type']}, 实际 {question_type}")

        print(f"搜索关键词: {keywords}")

        # 使用独立函数进行对比
        print("\n=== 使用独立函数 ===")
        need_search_old = analyze_search_need(test_case['query'], model_id)
        question_type_old = analyze_question_type(test_case['query'], model_id)
        if need_search_old:
            keywords_old = extract_search_keywords(test_case['query'], model_id)
        else:
            keywords_old = [test_case['query']]

        print(f"是否需要搜索: {need_search_old}")
        print(f"问题类型: {question_type_old}")
        print(f"搜索关键词: {keywords_old}")

        # 比较结果
        print("\n=== 结果比较 ===")
        if need_search == need_search_old and question_type == question_type_old:
            print("✅ 合并函数与独立函数结果一致")
        else:
            print("❌ 合并函数与独立函数结果不一致")

        print("-" * 80)

    print("\n测试完成")
    print("=" * 80)

if __name__ == "__main__":
    # 从命令行参数获取模型ID
    model_id = None
    if len(sys.argv) > 1:
        model_id = sys.argv[1]

    run_tests(model_id)

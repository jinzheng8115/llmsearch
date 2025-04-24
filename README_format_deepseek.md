# DeepSeek Reasoner 模型输出格式化模块

## 功能概述

这个模块提供了格式化 DeepSeek Reasoner 模型输出的功能，使其展示效果与智谱 AI 模型一样好。主要解决了以下问题：

1. **标题格式规范化**：将 `####` 格式的标题转换为标准 Markdown 标题
2. **引用格式统一**：将 `(来源[1])` 格式的引用转换为 `[参考文献1]` 格式
3. **表格转换为列表**：将表格格式转换为更易读的列表格式
4. **编号问题修复**：修复重复的编号，确保层级结构清晰
5. **排版优化**：确保段落之间有适当的空行，优化整体排版

## 文件说明

- `format_deepseek_output.py`：主要的格式化模块，包含格式化函数和辅助函数
- `test_format_deepseek.py`：测试脚本，用于验证格式化功能
- `demo_format_deepseek.py`：演示脚本，展示格式化前后的效果对比

## 集成方式

该模块已集成到 `chat_with_intelligent_search_new.py` 文件中，在以下位置进行了修改：

1. 导入格式化模块：
   ```python
   from format_deepseek_output import format_deepseek_output
   ```

2. 非流式模式下的格式化处理：
   ```python
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
   ```

3. 流式模式下的格式化处理：
   ```python
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
   ```

## 格式化效果

格式化前（DeepSeek Reasoner 模型原始输出）：
```
#### 一、历史起源与学术自治传统 欧洲现代大学体系可追溯至12-13世纪的中世纪大学。

1. 教会与王权的双重影响: 中世纪大学最初在教廷与封建君主控制下萌芽。

#### 二、国家特色与体系分化 欧洲各国大学体系呈现显著的多样性:
```

格式化后：
```
## 一、历史起源与学术自治传统 欧洲现代大学体系可追溯至12-13世纪的中世纪大学。

1. 教会与王权的双重影响: 中世纪大学最初在教廷与封建君主控制下萌芽。

## 二、国家特色与体系分化 欧洲各国大学体系呈现显著的多样性:
```

## 使用方法

1. 导入格式化模块：
   ```python
   from format_deepseek_output import format_deepseek_output
   ```

2. 调用格式化函数：
   ```python
   formatted_content = format_deepseek_output(original_content)
   ```

## 注意事项

- 格式化函数不会改变内容的实质，只会优化其展示形式
- 对于推理内容（reasoning_content），我们选择不进行格式化，保留其原始形式
- 如果格式化过程中出现错误，会返回原始内容，确保不会丢失信息

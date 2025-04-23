document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const loadingText = document.getElementById('loading-text');
    const webSearchToggle = document.getElementById('web-search-toggle');
    const searchEngineRadios = document.querySelectorAll('input[name="search-engine"]');

    // 加载设置
    const settings = JSON.parse(localStorage.getItem('searchSettings')) || {
        defaultModel: 'zhipuai',
        defaultSearchEngine: 'search_std',
        defaultResultCount: 10
    };

    // 初始化搜索引擎选择
    const defaultEngine = settings.defaultSearchEngine || 'search_std';
    document.querySelector(`input[name="search-engine"][value="${defaultEngine}"]`).checked = true;

    // 自动调整输入框高度
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // 发送按钮点击事件
    sendButton.addEventListener('click', function() {
        sendMessage();
    });

    // 回车键发送消息（Shift+Enter换行）
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // 搜索引擎切换动画
    searchEngineRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            // 添加动画效果
            const label = this.closest('.engine-label');
            label.style.transform = 'scale(1.05)';
            setTimeout(() => {
                label.style.transform = 'scale(1)';
            }, 200);
        });
    });

    // 联网搜索开关事件
    webSearchToggle.addEventListener('change', function() {
        const searchEngineSelector = document.getElementById('search-engine-selector');
        if (this.checked) {
            searchEngineSelector.style.display = 'flex';
        } else {
            searchEngineSelector.style.display = 'none';
        }
    });

    // 初始化联网搜索开关状态
    const searchEngineSelector = document.getElementById('search-engine-selector');
    if (webSearchToggle.checked) {
        searchEngineSelector.style.display = 'flex';
    } else {
        searchEngineSelector.style.display = 'none';
    }

    // 清理推理文本中的null
    function cleanupReasoningText() {
        const reasoningText = document.getElementById('reasoning-text');
        if (reasoningText) {
            // 获取当前文本
            let text = reasoningText.textContent;

            // 替换所有的null字符串
            text = text.replace(/\bnull\b/g, '').replace(/\bNULL\b/gi, '');

            // 移除连续的空行
            text = text.replace(/\n\s*\n\s*\n/g, '\n\n');

            // 更新文本
            reasoningText.textContent = text.trim();

            console.log('清理推理文本完成');
        }
    }

    // 发送消息函数
    function sendMessage() {
        console.log('发送消息函数被调用');
        const message = userInput.value.trim();
        if (!message) {
            console.log('消息为空，不发送');
            return;
        }
        console.log('将发送消息:', message);

        // 添加用户消息到聊天界面
        addMessage(message, 'user');

        // 清空输入框
        userInput.value = '';
        userInput.style.height = 'auto';

        // 禁用发送按钮和输入框
        sendButton.disabled = true;
        userInput.disabled = true;

        // 显示加载指示器
        loadingIndicator.style.display = 'flex';
        console.log('显示加载指示器');

        // 获取联网搜索状态和搜索引擎
        const useWebSearch = webSearchToggle.checked;
        const selectedEngine = document.querySelector('input[name="search-engine"]:checked').value;

        // 加载设置
        const settings = JSON.parse(localStorage.getItem('searchSettings')) || {
            defaultModel: 'zhipuai',
            defaultResultCount: 10,
            defaultTimeRange: 'month',  // 默认时间范围
            searxngEngines: '',
            searxngLanguage: 'auto',
            searxngSafesearch: 1,
            searxngTimeRange: 'month',
            bochaaiTimeRange: 'oneMonth'
        };

        // 获取模型设置
        const modelId = settings.defaultModel || 'zhipuai';
        const useStream = false; // 始终关闭流式输出
        const resultCount = settings.defaultResultCount || 10;

        // 获取SearXNG特殊设置
        const searxngEngines = settings.searxngEngines || '';
        const searxngLanguage = settings.searxngLanguage || 'auto';
        const searxngSafesearch = settings.searxngSafesearch !== undefined ? settings.searxngSafesearch : 1;
        const searxngTimeRange = settings.searxngTimeRange || 'month';

        // 根据联网搜索状态选择不同的API
        let apiUrl;
        let apiData;

        if (useWebSearch) {
            // 使用联网搜索API
            loadingText.textContent = '正在分析问题并搜索相关信息...';
            apiUrl = '/api/chat_with_search';
            apiData = {
                query: message,
                engine: selectedEngine,
                count: resultCount,
                model_id: modelId,
                stream: useStream
            };

            // 获取默认时间范围
            const defaultTimeRange = settings.defaultTimeRange || 'month';

            // 如果是SearXNG搜索引擎，添加特殊参数
            if (selectedEngine === 'searxng') {
                if (searxngEngines) apiData.searxng_engines = searxngEngines;
                apiData.searxng_language = searxngLanguage;
                apiData.searxng_safesearch = searxngSafesearch;

                // 优先使用SearXNG特定的时间范围，如果没有则使用默认时间范围
                const timeRange = settings.searxngTimeRange || defaultTimeRange;
                apiData.searxng_time_range = timeRange;

                console.log('SearXNG参数:', {
                    engines: searxngEngines,
                    language: searxngLanguage,
                    safesearch: searxngSafesearch,
                    time_range: timeRange
                });
            }
            // 如果是Bocha AI搜索引擎，添加时间范围参数
            else if (selectedEngine === 'bochaai') {
                // 优先使用Bocha AI特定的时间范围，如果没有则根据默认时间范围转换
                let timeRange = settings.bochaaiTimeRange || 'oneMonth';

                // 如果没有特定设置，将默认时间范围转换为Bocha AI格式
                if (timeRange === 'oneMonth' && defaultTimeRange !== 'month') {
                    // 将默认时间范围转换为Bocha AI格式
                    switch(defaultTimeRange) {
                        case 'day': timeRange = 'oneDay'; break;
                        case 'week': timeRange = 'oneWeek'; break;
                        case 'month': timeRange = 'oneMonth'; break;
                        case 'year': timeRange = 'oneYear'; break;
                        case '': timeRange = 'noLimit'; break;
                        default: timeRange = 'oneMonth';
                    }
                }

                apiData.freshness = timeRange;

                console.log('Bocha AI参数:', {
                    freshness: timeRange
                });
            }
            // 其他搜索引擎，添加默认时间范围参数
            else {
                // 对于智谱AI搜索引擎，添加时间范围参数
                if (defaultTimeRange) {
                    apiData.time_range = defaultTimeRange;
                    console.log('默认时间范围参数:', {
                        time_range: defaultTimeRange
                    });
                }
            }
        } else {
            // 使用普通聊天API
            loadingText.textContent = '正在思考中...';
            apiUrl = '/api/chat';
            apiData = {
                query: message,
                model_id: modelId,
                stream: useStream
            };
        }

        // 创建AI回复的消息元素
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant';

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content markdown';
        messageContent.innerHTML = '<p class="typing-indicator"><span>.</span><span>.</span><span>.</span></p>';

        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;

        // 如果使用流式输出
        if (apiData.stream) {
            // 调用API（流式模式）
            fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(apiData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('请求失败');
                }

                // 隐藏加载指示器
                loadingIndicator.style.display = 'none';

                // 初始化流式输出
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let fullResponse = '';
                let searchResults = null;

                // 清除打字指示器
                messageContent.innerHTML = '';

                // 处理流式数据
                function processStream() {
                    console.log('开始处理流式数据');
                    return reader.read().then(({ done, value }) => {
                        if (done) {
                            // 流式输出完成
                            console.log('流式输出完成');
                            console.log('最终完整响应:', fullResponse);

                            // 确保最终响应被显示
                            if (fullResponse) {
                                messageContent.innerHTML = processMarkdown(fullResponse);
                                chatContainer.scrollTop = chatContainer.scrollHeight;
                            }

                            // 如果有搜索结果，显示搜索结果
                            if (searchResults && searchResults.length > 0) {
                                addSearchResultsToMessage(messageContent, searchResults);
                            }

                            // 清理推理文本中的null
                            cleanupReasoningText();

                            return;
                        }

                        console.log('收到数据块，长度:', value.length);

                        // 解码数据
                        const newText = decoder.decode(value, { stream: true });
                        console.log('解码后的数据:', newText);
                        buffer += newText;

                        // 处理数据行
                        const lines = buffer.split('\n');
                        console.log('分割后的行数:', lines.length);
                        buffer = lines.pop(); // 保留未完成的行

                        for (const line of lines) {
                            if (line.startsWith('data: ')) {
                                const data = line.slice(6);

                                // 检查是否是结束消息
                                if (data === '[DONE]') {
                                    console.log('收到流式输出结束消息（旧格式）');
                                    continue;
                                }

                                // 尝试解析JSON格式的结束消息
                                try {
                                    const jsonData = JSON.parse(data);
                                    if (jsonData.done === true) {
                                        console.log('收到流式输出结束消息（JSON格式）');
                                        continue;
                                    }
                                } catch (e) {
                                    // 不是JSON格式的结束消息，继续处理
                                }

                                // 检查是否是结束消息 - 处理多种可能的格式
                                if (data === '[DONE]' || data.includes('[DONE]') ||
                                    data === 'data: [DONE]' || data.includes('data: [DONE]') ||
                                    data.includes('"done": true') || data.includes('data: {"done": true}')) {
                                    console.log('收到结束消息，跳过解析: ' + data);
                                    continue;
                                }

                                // 预处理：移除data中的null字符串和"data: "前缀
                                let cleanData = data.replace(/\bnull\b/g, '""').replace(/\bNULL\b/gi, '""');
                                console.log('原始数据:', data);

                                // 如果数据包含"data: "前缀，删除它
                                if (cleanData.startsWith('data: ')) {
                                    cleanData = cleanData.substring(6);
                                    console.log('移除data:前缀后:', cleanData);
                                }

                                try {
                                    // 尝试解析JSON
                                    console.log('尝试解析JSON:', cleanData);
                                    const json = JSON.parse(cleanData);
                                    console.log('解析成功，JSON对象:', json);

                                    // 打印完整的JSON对象以便于调试
                                    console.log('完整JSON对象:', JSON.stringify(json, null, 2));

                                    // 检查是否包含搜索结果和问题类型
                                    if (json.search_results) {
                                        searchResults = json.search_results;
                                        console.log('收到搜索结果:', searchResults.length);

                                        // 如果包含问题类型，显示问题类型
                                        if (json.question_type) {
                                            const questionType = json.question_type;
                                            console.log('问题类型:', questionType);

                                            // 创建问题类型标签
                                            const typeLabel = document.createElement('div');
                                            typeLabel.className = 'question-type-label';
                                            typeLabel.textContent = questionType === '开放性问题' ? '开放性问题' : '准确答案问题';
                                            typeLabel.style.backgroundColor = questionType === '开放性问题' ? '#4CAF50' : '#2196F3';
                                            typeLabel.style.color = 'white';
                                            typeLabel.style.padding = '2px 8px';
                                            typeLabel.style.borderRadius = '12px';
                                            typeLabel.style.fontSize = '12px';
                                            typeLabel.style.display = 'inline-block';
                                            typeLabel.style.marginBottom = '8px';

                                            // 将标签添加到消息内容前
                                            messageContent.prepend(typeLabel);
                                        }
                                        continue;
                                    }

                                    // 处理内容更新 - 前端格式
                                    if (json.content !== undefined) {
                                        fullResponse += json.content;

                                        // 实时更新消息内容
                                        messageContent.innerHTML = processMarkdown(fullResponse);
                                        chatContainer.scrollTop = chatContainer.scrollHeight;
                                        continue;
                                    }

                                    // 处理智谱AI的流式输出格式
                                    if (json.choices && json.choices.length > 0) {
                                        // 处理智谱AI的流式输出格式
                                        if (json.choices[0].delta && json.choices[0].delta.content !== undefined) {
                                            const content = json.choices[0].delta.content;
                                            fullResponse += content;

                                            // 实时更新消息内容
                                            messageContent.innerHTML = processMarkdown(fullResponse);
                                            chatContainer.scrollTop = chatContainer.scrollHeight;
                                            continue;
                                        }
                                    }

                                    // 处理 DeepSeek Reasoner 模型的推理过程输出
                                    if (json.is_reasoning && json.content !== undefined) {
                                        // 如果是推理过程的开始，创建推理过程区域
                                        if (!document.getElementById('reasoning-content')) {
                                            const reasoningDiv = document.createElement('div');
                                            reasoningDiv.id = 'reasoning-content';
                                            reasoningDiv.className = 'reasoning-content';
                                            reasoningDiv.innerHTML = '<h4>推理过程</h4><div id="reasoning-text"></div>';
                                            messageContent.appendChild(reasoningDiv);
                                            console.log('创建推理过程区域 (方式2)');
                                        }

                                        // 添加推理内容
                                        const reasoningText = document.getElementById('reasoning-text');

                                        // 获取内容
                                        let content = json.content;

                                        // 跳过null、'null'、undefined值
                                        if (content === null || content === undefined || content === 'null') {
                                            console.log('跳过null值 (方式2)');
                                            continue;
                                        }

                                        // 确保是字符串
                                        if (typeof content !== 'string') {
                                            content = String(content);
                                            console.log('将非字符串转换为字符串 (方式2)');
                                        }

                                        // 如果字符串中只有null，跳过
                                        if (content.trim() === 'null') {
                                            console.log('跳过只有null的字符串 (方式2)');
                                            continue;
                                        }

                                        // 移除所有null字符串和实际的null值
                                        let cleanContent = content
                                            .replace(/\bnull\b/g, '')
                                            .replace(/\bNULL\b/gi, '')
                                            .replace(/undefined/g, '');

                                        // 去除前后空白
                                        cleanContent = cleanContent.trim();

                                        // 只有在清理后的内容非空时才添加
                                        if (cleanContent && cleanContent !== '') {
                                            reasoningText.textContent += cleanContent;
                                            chatContainer.scrollTop = chatContainer.scrollHeight;
                                            console.log('添加推理内容 (方式2): ' + cleanContent.substring(0, 20) + '...');
                                        }
                                        continue;
                                    }

                                    // 如果是其他格式，尝试提取内容
                                    if (typeof json === 'object') {
                                        // 尝试从对象中提取可能的内容
                                        const extractedContent = extractContentFromObject(json);
                                        if (extractedContent) {
                                            fullResponse += extractedContent;

                                            // 实时更新消息内容
                                            messageContent.innerHTML = processMarkdown(fullResponse);
                                            chatContainer.scrollTop = chatContainer.scrollHeight;
                                        }
                                    }
                                } catch (e) {
                                    console.error('解析流式数据错误:', e, data);
                                }
                            }
                        }

                        return processStream();
                    });
                }

                // 从复杂对象中提取内容的辅助函数
                function extractContentFromObject(obj) {
                    // 如果对象中有明确的内容字段
                    if (obj.content) return obj.content;
                    if (obj.text) return obj.text;
                    if (obj.message && obj.message.content) return obj.message.content;

                    // 递归检查对象的所有属性
                    for (const key in obj) {
                        if (typeof obj[key] === 'object' && obj[key] !== null) {
                            const content = extractContentFromObject(obj[key]);
                            if (content) return content;
                        } else if (typeof obj[key] === 'string' && key.toLowerCase().includes('content')) {
                            return obj[key];
                        }
                    }

                    return null;
                }
            })
            .catch(error => {
                // 隐藏加载指示器
                loadingIndicator.style.display = 'none';

                // 显示错误消息
                messageContent.innerHTML = `<p class="error">请求失败: ${error.message}</p>`;
            })
            .finally(() => {
                // 启用发送按钮和输入框
                sendButton.disabled = false;
                userInput.disabled = false;
                userInput.focus();
            });
        } else {
            // 调用API（非流式模式）
            fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(apiData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('请求失败');
                }
                return response.json();
            })
            .then(data => {
                // 隐藏加载指示器
                loadingIndicator.style.display = 'none';

                // 处理API响应
                if (data.error) {
                    // 显示错误消息
                    messageContent.innerHTML = `<p class="error">发生错误: ${data.error}</p>`;
                } else {
                    // 处理推理过程（如果有）
                    if (data.reasoning_content) {
                        // 创建推理过程区域
                        const reasoningDiv = document.createElement('div');
                        reasoningDiv.id = 'reasoning-content';
                        reasoningDiv.className = 'reasoning-content';
                        reasoningDiv.innerHTML = '<h4>推理过程</h4><div id="reasoning-text"></div>';
                        messageContent.appendChild(reasoningDiv);

                        // 处理推理内容
                        let reasoning = data.reasoning_content;
                        if (reasoning && typeof reasoning === 'string') {
                            // 清理null字符串
                            reasoning = reasoning.replace(/\bnull\b/g, '').replace(/\bNULL\b/gi, '').replace(/undefined/g, '');
                            document.getElementById('reasoning-text').textContent = reasoning.trim();
                            console.log('非流式模式下添加推理内容');

                            // 清理推理文本中的null
                            cleanupReasoningText();
                        }
                    }

                    // 显示AI回复
                    let aiResponse = data.response || '抱歉，我无法回答这个问题。';

                    // 统一展示格式，无论是否有推理过程
                    // 如果没有推理过程区域，直接设置内容
                    if (!document.getElementById('reasoning-content')) {
                        messageContent.innerHTML = processMarkdown(aiResponse);
                    } else {
                        // 如果有推理过程区域，清除原有内容并重新设置
                        // 保留推理过程区域
                        const reasoningContent = document.getElementById('reasoning-content');
                        const responseDiv = document.createElement('div');
                        responseDiv.className = 'response-content';
                        responseDiv.innerHTML = processMarkdown(aiResponse);

                        // 清除推理过程区域之外的内容
                        const children = Array.from(messageContent.children);
                        for (const child of children) {
                            if (child.id !== 'reasoning-content') {
                                messageContent.removeChild(child);
                            }
                        }

                        // 添加新的响应内容
                        messageContent.appendChild(responseDiv);
                    }

                    // 如果使用了联网搜索，添加搜索结果信息
                    if (useWebSearch && data.search_results && data.search_results.length > 0) {
                        addSearchResultsToMessage(messageContent, data.search_results);
                    }

                    // 如果包含问题类型，显示问题类型
                    if (data.question_type) {
                        const questionType = data.question_type;
                        console.log('问题类型:', questionType);

                        // 创建问题类型标签
                        const typeLabel = document.createElement('div');
                        typeLabel.className = 'question-type-label';
                        typeLabel.textContent = questionType === '开放性问题' ? '开放性问题' : '准确答案问题';
                        typeLabel.style.backgroundColor = questionType === '开放性问题' ? '#4CAF50' : '#2196F3';
                        typeLabel.style.color = 'white';
                        typeLabel.style.padding = '2px 8px';
                        typeLabel.style.borderRadius = '12px';
                        typeLabel.style.fontSize = '12px';
                        typeLabel.style.display = 'inline-block';
                        typeLabel.style.marginBottom = '8px';

                        // 将标签添加到消息内容前
                        messageContent.prepend(typeLabel);
                    }

                    // 清理推理文本中的null
                    cleanupReasoningText();
                }
            })
            .catch(error => {
                // 隐藏加载指示器
                loadingIndicator.style.display = 'none';

                // 显示错误消息
                messageContent.innerHTML = `<p class="error">请求失败: ${error.message}</p>`;
            })
            .finally(() => {
                // 启用发送按钮和输入框
                sendButton.disabled = false;
                userInput.disabled = false;
                userInput.focus();
            });
        }

        // 滚动到底部
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 添加消息到聊天界面
    function addMessage(content, sender, searchResults = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content markdown';

        // 处理Markdown格式
        if (sender === 'assistant') {
            // 使用marked.js或其他Markdown解析库处理内容
            // 这里简单处理一些基本的Markdown语法
            content = processMarkdown(content);
        }

        messageContent.innerHTML = content;

        // 如果有搜索结果，添加搜索结果信息
        if (searchResults && searchResults.length > 0) {
            addSearchResultsToMessage(messageContent, searchResults);
        }

        messageDiv.appendChild(messageContent);
        chatContainer.appendChild(messageDiv);

        // 滚动到底部
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // 添加搜索结果到消息
    function addSearchResultsToMessage(messageContent, searchResults) {
        // 不显示搜索结果，使界面更简洁
        return;
    }

    // 简单的Markdown处理函数
    function processMarkdown(text) {
        // 处理代码块
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

        // 处理行内代码
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

        // 处理标题
        text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');

        // 处理粗体
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // 处理斜体
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // 处理链接
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

        // 处理无序列表
        text = text.replace(/^\s*[\-\*•]\s+(.*$)/gm, '<li>$1</li>');
        text = text.replace(/<li>(.*)<\/li>/g, '<ul><li>$1</li></ul>');
        text = text.replace(/<\/ul>\s*<ul>/g, '');

        // 处理有序列表
        text = text.replace(/^\s*\d+\.\s+(.*$)/gm, '<li>$1</li>');
        text = text.replace(/<li>(.*)<\/li>/g, '<ol><li>$1</li></ol>');
        text = text.replace(/<\/ol>\s*<ol>/g, '');

        // 处理引用
        text = text.replace(/^\s*>\s+(.*$)/gm, '<blockquote>$1</blockquote>');
        text = text.replace(/<\/blockquote>\s*<blockquote>/g, '<br>');

        // 处理段落
        text = text.replace(/\n\s*\n/g, '</p><p>');
        text = '<p>' + text + '</p>';
        text = text.replace(/<p><\/p>/g, '');

        // 处理参考来源部分
        const referenceRegex = /## 参考来源\s+([\s\S]*)/;
        const referenceMatch = text.match(referenceRegex);

        if (referenceMatch) {
            const referenceContent = referenceMatch[1];
            text = text.replace(referenceRegex, '');

            // 创建参考来源部分
            const referencesDiv = '<div class="references"><h3>参考来源</h3>' + referenceContent + '</div>';
            text += referencesDiv;
        }

        return text;
    }
});

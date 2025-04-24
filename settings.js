document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const defaultModelSelect = document.getElementById('default-model');
    const defaultSearchEngineSelect = document.getElementById('default-search-engine');
    const defaultResultCountSelect = document.getElementById('default-result-count');
    const defaultTimeRangeSelect = document.getElementById('default-time-range');
    const saveSettingsButton = document.getElementById('save-settings');
    const resetSettingsButton = document.getElementById('reset-settings');
    const settingsNavItems = document.querySelectorAll('.settings-nav li');
    const settingsPanels = document.querySelectorAll('.settings-panel');
    const engineSettings = document.querySelectorAll('.engine-setting');

    // 默认设置
    const defaultSettings = {
        defaultModel: 'zhipuai',  // 默认为智谱AI GLM-4
        defaultSearchEngine: 'searxng',  // 默认为SearXNG
        defaultResultCount: 10,
        defaultTimeRange: 'month',  // 默认时间范围
        // SearXNG特殊设置
        searxngEngines: 'bing,baidu,360search,quark,sogou',
        searxngLanguage: 'auto',
        searxngSafesearch: 1,
        // Bocha AI特殊设置
        bochaaiTimeRange: 'oneMonth'
    };

    // 加载设置
    function loadSettings() {
        const settings = JSON.parse(localStorage.getItem('searchSettings')) || defaultSettings;

        // 设置表单值
        defaultModelSelect.value = settings.defaultModel || defaultSettings.defaultModel;
        defaultSearchEngineSelect.value = settings.defaultSearchEngine || defaultSettings.defaultSearchEngine;
        defaultResultCountSelect.value = settings.defaultResultCount || defaultSettings.defaultResultCount;
        defaultTimeRangeSelect.value = settings.defaultTimeRange || defaultSettings.defaultTimeRange;

        // 加载SearXNG设置
        const searxngEnginesInput = document.getElementById('searxng-engines');
        const searxngLanguageSelect = document.getElementById('searxng-language');
        const searxngSafesearchSelect = document.getElementById('searxng-safesearch');

        if (searxngEnginesInput) searxngEnginesInput.value = settings.searxngEngines || defaultSettings.searxngEngines;
        if (searxngLanguageSelect) searxngLanguageSelect.value = settings.searxngLanguage || defaultSettings.searxngLanguage;
        if (searxngSafesearchSelect) searxngSafesearchSelect.value = settings.searxngSafesearch !== undefined ? settings.searxngSafesearch : defaultSettings.searxngSafesearch;

        // 显示当前搜索引擎的特定设置
        showEngineSettings(settings.defaultSearchEngine);
    }

    // 保存设置
    function saveSettings() {
        // 获取SearXNG设置元素
        const searxngEnginesInput = document.getElementById('searxng-engines');
        const searxngLanguageSelect = document.getElementById('searxng-language');
        const searxngSafesearchSelect = document.getElementById('searxng-safesearch');

        const settings = {
            defaultModel: defaultModelSelect.value,
            defaultSearchEngine: defaultSearchEngineSelect.value,
            defaultResultCount: parseInt(defaultResultCountSelect.value),
            defaultTimeRange: defaultTimeRangeSelect.value,
            // SearXNG设置
            searxngEngines: searxngEnginesInput ? searxngEnginesInput.value : defaultSettings.searxngEngines,
            searxngLanguage: searxngLanguageSelect ? searxngLanguageSelect.value : defaultSettings.searxngLanguage,
            searxngSafesearch: searxngSafesearchSelect ? parseInt(searxngSafesearchSelect.value) : defaultSettings.searxngSafesearch,
        };

        localStorage.setItem('searchSettings', JSON.stringify(settings));

        // 显示保存成功提示
        showNotification('设置已保存', 'success');
    }

    // 显示搜索引擎特定设置
    function showEngineSettings(engine) {
        // 隐藏所有引擎设置
        engineSettings.forEach(setting => {
            setting.style.display = 'none';
        });

        // 显示当前选中引擎的设置
        const currentEngineSetting = document.querySelector(`.engine-setting[data-engine="${engine}"]`);
        if (currentEngineSetting) {
            currentEngineSetting.style.display = 'block';
        }
    }

    // 切换设置面板
    function switchSettingsPanel(panelId) {
        // 隐藏所有面板
        settingsPanels.forEach(panel => {
            panel.classList.remove('active');
        });

        // 显示选中面板
        const activePanel = document.getElementById(panelId);
        if (activePanel) {
            activePanel.classList.add('active');
        }

        // 更新导航项状态
        settingsNavItems.forEach(item => {
            if (item.dataset.section === panelId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
    }

    // 重置设置
    function resetSettings() {
        if (confirm('确定要重置所有设置吗？这将清除所有自定义设置。')) {
            localStorage.removeItem('searchSettings');
            loadSettings();
            showNotification('设置已重置为默认值', 'info');
        }
    }

    // 显示通知
    function showNotification(message, type = 'success') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;

        // 根据类型设置图标
        let icon = 'check-circle';
        if (type === 'error') icon = 'exclamation-circle';
        if (type === 'info') icon = 'info-circle';
        if (type === 'warning') icon = 'exclamation-triangle';

        notification.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
        `;

        // 添加到页面
        document.body.appendChild(notification);

        // 显示通知
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);

        // 自动隐藏通知
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }



    // 绑定事件
    // 保存和重置按钮
    saveSettingsButton.addEventListener('click', saveSettings);
    resetSettingsButton.addEventListener('click', resetSettings);

    // 导航项切换
    settingsNavItems.forEach(item => {
        item.addEventListener('click', function() {
            const panelId = this.dataset.section;
            switchSettingsPanel(panelId);
        });
    });



    // 搜索引擎选择
    defaultSearchEngineSelect.addEventListener('change', function() {
        showEngineSettings(this.value);
    });

    // 初始加载设置
    loadSettings();

    // 添加通知样式
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 6px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s ease;
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 500;
        }

        .notification i {
            font-size: 18px;
        }

        .notification-success {
            background-color: #e7f7ed;
            color: #0a6b31;
            border-left: 4px solid #0a6b31;
        }

        .notification-error {
            background-color: #fde8e8;
            color: #c81e1e;
            border-left: 4px solid #c81e1e;
        }

        .notification-info {
            background-color: #e6f4ff;
            color: #0078d4;
            border-left: 4px solid #0078d4;
        }

        .notification-warning {
            background-color: #fff8e6;
            color: #b25000;
            border-left: 4px solid #b25000;
        }

        .notification.show {
            transform: translateY(0);
            opacity: 1;
        }
    `;
    document.head.appendChild(style);
});

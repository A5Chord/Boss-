# 配置信息文件

# 浏览器选项配置
BROWSER_OPTIONS = {
    "start_maximized": True,  # 启动时最大化窗口
    "disable_infobars": True,  # 禁用信息栏
    "disable_extensions": True,  # 禁用浏览器扩展
    "window_size": (1920, 1080)  # 设置浏览器窗口的大小
}

# 要爬取的职位和城市
JOBS = [
    '后端开发',
    '软件测试'
]
CITIES = {
    '101200100': '武汉',
    # '101280100': '广州'
}

# 爬取设置
MAX_RETRIES = 5  # 最大尝试次数
PAGE_COUNT = 3  # 爬取页数
MAX_KEYWORD_LENGTH = 7  # 最大关键词长度

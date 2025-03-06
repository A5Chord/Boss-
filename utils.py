import re
import threading
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer

from config import MAX_RETRIES, CITIES, PAGE_COUNT, BROWSER_OPTIONS


# 设置浏览器选项
def create_driver():
    edge_options = Options()
    if BROWSER_OPTIONS["start_maximized"]:
        edge_options.add_argument("--start-maximized")
    if BROWSER_OPTIONS["disable_infobars"]:
        edge_options.add_argument("--disable-infobars")
    if BROWSER_OPTIONS["disable_extensions"]:
        edge_options.add_argument("--disable-extensions")
    if BROWSER_OPTIONS["window_size"]:
        edge_options.add_argument(
            f"--window-size={BROWSER_OPTIONS['window_size'][0]},{BROWSER_OPTIONS['window_size'][1]}")

    return webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)


# 等待要爬取的元素出现
def wait_for_element(boss, element_class, max_count):
    attempt = 0
    while attempt < max_count:
        try:
            element_present = EC.presence_of_element_located((By.CLASS_NAME, f'{element_class}'))
            WebDriverWait(boss, 10).until(element_present)
            if attempt > 0:
                print(f"[{threading.current_thread().name}] 重试成功！")
            break
        except TimeoutException:
            attempt += 1
            print(f"[{threading.current_thread().name}] 尝试失败，正在重试[{attempt}/{max_count}]...")
            print("由于网站可能会反爬，最好打开浏览器进行手动验证！")
            if attempt == max_count:
                raise TimeoutException("在最大尝试次数内未找到元素！")
            time.sleep(3)


# 爬取各项信息
def start_crawling(boss, url):
    job_titles = []
    company_names = []
    locations = []
    salaries = []
    job_links = []

    boss.get(url)
    time.sleep(3)

    # 等待要爬取的元素出现
    wait_for_element(boss, 'job-name', MAX_RETRIES)

    try:
        job_titles.extend([item.text for item in boss.find_elements(By.CLASS_NAME, 'job-name')])
        company_names.extend([item.text for item in boss.find_elements(By.CSS_SELECTOR, '.company-info .company-name')])
        locations.extend([item.text for item in boss.find_elements(By.CLASS_NAME, 'job-area-wrapper')])
        salaries.extend([item.text for item in boss.find_elements(By.CLASS_NAME, 'salary')])
        job_links = [a.get_attribute('href') for a in boss.find_elements(By.XPATH, "//a[@class='job-card-left']")]

        print('职位数量：', len(job_titles))

        df1 = pd.DataFrame({
            '职位名称': job_titles,
            '公司名称': company_names,
            '位置': locations,
            '工资': salaries,
            '职位链接': job_links,
        })

        return df1

    except Exception as e:
        print(f"在爬取 {url} 时发生错误: {e}")
        return pd.DataFrame(columns=['职位名称', '公司名称', '位置', '工资', '职位链接'])


# 爬取并生成结果
def fetch_job_info(boss, job, city_code):
    print(f"开始爬取 {job} 位于 {CITIES[city_code]} 的职位信息...")
    df1 = pd.DataFrame(columns=['职位名称', '公司名称', '位置', '工资', '职位链接'])

    for i in range(1, PAGE_COUNT + 1):
        url = f'https://www.zhipin.com/web/geek/job?query={job}&city={city_code}&page={i}'
        print(f"链接：{url}")
        df1 = pd.concat([df1, start_crawling(boss, url)], axis=0)

    filename = f"{job}_{CITIES[city_code]}.csv"
    df1.to_csv(filename, index=False)
    print(f"{filename} 已保存！\n")
    return filename


# 过滤过长的词
def shorten_keywords(text, max_length):
    text = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', ' ', text)
    words = text.split()
    shortened_words = [word[:max_length] for word in words if len(word) <= max_length]
    return ' '.join(shortened_words)


# 生成词云图
def generate_wordcloud(text, job_title):
    text = ' '.join(text.split())
    wordcloud = (WordCloud(font_path="msyh.ttc",
                           width=4096, height=2160,
                           background_color='white',
                           max_words=150,
                           max_font_size=250,
                           min_font_size=30,
                           colormap='viridis')
                 .generate(text))

    plt.figure(figsize=(16, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title(f"{job_title} - 词云图", fontsize=20)

    output_file = f"{job_title}_词云图.png"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"{job_title} 词云图已保存！\n")
    plt.show()


# 计算TF-IDF
def calculate_tfidf(descriptions):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(descriptions)
    return tfidf_matrix, vectorizer.get_feature_names_out()


# 从CSV文件中获取职位链接
def read_job_links(file_name):
    df = pd.read_csv(file_name)
    return df['职位链接'].tolist()


# 爬取职位描述信息
def fetch_job_description(boss, url):

    boss.get(url)
    time.sleep(3)

    # 等待要爬取的元素出现
    wait_for_element(boss, 'job-sec-text', MAX_RETRIES)

    try:
        description_div = boss.find_element(By.CLASS_NAME, 'job-sec-text')
        description = description_div.text
        return description
    except Exception as e:
        print(f"获取职位描述信息时出错，url：{url}\n错误信息：{e}")
        return

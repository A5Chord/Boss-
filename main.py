from concurrent.futures import ThreadPoolExecutor
from matplotlib import rcParams
from config import JOBS, CITIES
from utils import generate_wordcloud, calculate_tfidf, read_job_links, \
    fetch_job_description, fetch_job_info, create_driver

if __name__ == "__main__":
    print("本项目用于爬取Boss直聘网站的职位信息与链接，并根据职位描述信息生成词云")
    print("正在初始化浏览器...\n")

    boss = create_driver()

    for job in JOBS:
        for city_code in CITIES:
            filename = fetch_job_info(boss, job, city_code)

            # 读取职位链接
            job_links = read_job_links(filename)

            # 爬取职位描述
            print("开始爬取职位描述信息...")
            descriptions = []

            # 使用线程池并发爬取职位描述
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(fetch_job_description, boss, link): link for link in job_links}
                for future in futures:
                    description = future.result()
                    if description:
                        descriptions.append(description)

        # 计算TF-IDF
        print(f"正在计算 {job} TF-词频...")
        tfidf_matrix, feature_names = calculate_tfidf(descriptions)

        # 生成词云图
        print(f"正在生成 {job} 词云图...")
        # 设置字体防止标题乱码
        rcParams['font.family'] = 'Microsoft YaHei'
        all_descriptions = " ".join(descriptions)
        generate_wordcloud(all_descriptions, job)

    # 关闭浏览器
    boss.quit()

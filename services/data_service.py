from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
import requests
from urllib.parse import quote

def fetch_and_process_homeworks(requester, course_id):
    """获取、排序和丰富作业数据

    Args:
        requester: OJRequester实例
        course_id: 课程ID

    Returns:
        enriched_homeworks: 包含详细信息的作业列表，如果获取失败则返回None
    """
    homeworks = requester.get_homeworks_list(course_id)
    if not homeworks or 'list' not in homeworks or not homeworks['list']:
        print("[\x1b[0;31mx\x1b[0m] 无法获取作业列表或列表为空")
        return None

    # 按截止日期排序作业列表
    sorted_homeworks = sorted(homeworks['list'],
                              key=lambda hw: hw.get('nextDate', '9999-12-31 23:59:59'))

    # 定义一个工作函数来获取作业详情
    def fetch_homework_detail(hw):
        """为单个作业获取详细信息的工作函数"""
        hw_id = hw['homeworkId']
        hw_details = requester.get_homework_info(hw_id, course_id)
        if hw_details:
            # 将详细信息合并到原始作业信息中
            hw['details'] = hw_details
        else:
            # 没有获取到详细信息时设置空字典
            hw['details'] = {}
        return hw

    # 使用多线程获取每个作业的详细信息
    enriched_homeworks = []
    max_workers = min(5, len(sorted_homeworks))  # 最多5个线程，或作业数量（取较小值）

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有作业的详情请求到线程池
        future_to_hw = {executor.submit(fetch_homework_detail, hw): hw for hw in sorted_homeworks}

        # 获取结果
        for future in as_completed(future_to_hw):
            try:
                hw = future.result()
                enriched_homeworks.append(hw)
            except Exception as exc:
                hw_id = future_to_hw[future].get('homeworkId', 'Unknown')
                print(f"\n[\x1b[0;31mx\x1b[0m] 获取作业 {hw_id} 详情时出错: {exc}")
                # 保留原始信息
                enriched_homeworks.append(future_to_hw[future])

    return enriched_homeworks

def fetch_and_process_problems(requester, homework_id, course_id):
    """获取并丰富问题数据，包括提交记录

    Args:
        requester: OJRequester实例
        homework_id: 作业ID
        course_id: 课程ID

    Returns:
        enriched_problems: 包含详细信息的问题列表，如果获取失败则返回None
    """
    print(f"\n[\x1b[0;36m!\x1b[0m] 获取作业ID{homework_id}的题目列表...")
    problems_list = requester.get_homework_problems(homework_id, course_id)

    if not problems_list or 'list' not in problems_list or not problems_list['list']:
        print("[\x1b[0;31mx\x1b[0m] 获取问题列表失败或列表为空")
        return None

    # 定义函数以获取问题详细信息和提交记录
    def fetch_problem_detail(problem):
        """为单个问题获取详细信息和提交记录的工作函数"""
        problem_id = problem.get('problemId', 'Unknown')

        # 获取问题详情
        problem_info = requester.get_problem_info(problem_id, homework_id, course_id)
        if problem_info:
            problem['details'] = problem_info
        else:
            problem['details'] = {}

        # 获取提交记录
        submission_records = requester.get_problem_submission_records(problem_id, homework_id, course_id)
        if submission_records and 'list' in submission_records and len(submission_records['list']) > 0:
            problem['submission_records'] = submission_records['list']
        else:
            problem['submission_records'] = []

        return problem

    # 使用多线程获取每个问题的详细信息
    original_problems = problems_list['list']
    problem_results = {}  # 使用字典存储结果，以保持顺序

    max_workers = min(5, len(original_problems))  # 最多5个线程

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有问题的详情请求到线程池，并记录原始索引
        futures = {}
        for i, problem in enumerate(original_problems):
            future = executor.submit(fetch_problem_detail, problem)
            futures[future] = (i, problem.get('problemId', 'Unknown'))

        # 创建进度计数
        completed = 0
        total = len(futures)

        # 获取结果
        for future in as_completed(futures):
            try:
                problem = future.result()
                index, problem_id = futures[future]
                problem_results[index] = problem
                completed += 1
                print(f"\r[\x1b[0;36m!\x1b[0m] 获取题目详情进度: {completed}/{total}", end="")
            except Exception as exc:
                index, problem_id = futures[future]
                print(f"\n[\x1b[0;31mx\x1b[0m] 获取题目 {problem_id} 详情时出错: {exc}")
                # 保留原始信息但添加空的details字典
                problem = original_problems[index]
                problem['details'] = {}
                problem['submission_records'] = []
                problem_results[index] = problem

    # 按原始顺序重建问题列表
    enriched_problems = [problem_results[i] for i in range(len(original_problems))]
    print("\r" + " " * 50 + "\r", end="")  # 清除进度显示

    return enriched_problems


def download_unit_test_file(course_code, problem_id, homework_id, problem_name):
    """
    下载单元测试文件

    Args:
        course_code: 课程代码，如 'CS109-25S'
        problem_id: 题目ID
        homework_id: 作业ID
        problem_name: 题目名称

    Returns:
        (bool, str): 第一个元素表示是否成功，第二个元素为文件路径或错误消息
    """
    # 基础URL，作者把单元测试文件放在了自费的阿里云OSS上
    base_url = "https://hexo-blog-netlify.oss-cn-shenzhen.aliyuncs.com/junittest"

    # 构造文件名，格式: "{problem_id}_{problem_name}.java"
    file_name = f"MainTest.java"

    # 构造URL
    url = f"{base_url}/{course_code}/{homework_id}/{problem_id}_{quote(problem_name)}/MainTest.java"


    # 保存路径
    from config import WORK_DIRECTORY
    save_path = os.path.join(WORK_DIRECTORY, file_name)

    # 下载文件
    try:
        response = requests.get(url, verify=False, timeout=10)

        if response.status_code == 200:
            # 检查是否为XML错误响应
            if response.text.strip().startswith('<?xml') and '<Error>' in response.text:
                print(f"[\x1b[0;33m!\x1b[0m] 服务器返回错误:")
                if '<Message>' in response.text:
                    message = re.search(r'<Message>(.*?)</Message>', response.text)
                    if message:
                        print(f"[\x1b[0;33m!\x1b[0m] {message.group(1)}")

                if '<Key>' in response.text:
                    key = re.search(r'<Key>(.*?)</Key>', response.text)
                    if key:
                        print(f"[\x1b[0;33m!\x1b[0m] 请求的文件: {key.group(1)}")

                return False, "[\x1b[0;33m!\x1b[0m]该题目暂无单元测试文件"

            # 正常响应，保存文件
            with open(save_path, 'wb') as file:
                file.write(response.content)
            return True, save_path
        elif response.status_code == 404:
            return False, "该题目暂无单元测试文件，你可以通过Pull Requests贡献单元测试到Github中，谢谢合作"
        else:
            return False, f"HTTP状态码: {response.status_code}"

    except Exception as e:
        return False, f"[\x1b[0;33m!\x1b[0m]下载异常: {str(e)}"
import requests
import json
import urllib3
import re
import os
from pickle import dump, load
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class OJRequester:
    def __init__(self):
        self.base_url = "https://oj.cse.sustech.edu.cn"
        self.session = requests.Session()

        # 设置通用请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Sec-Ch-Ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Priority': 'u=1, i'
        })
        self.csrf_token = None

    def cas_login(self, username, password):
        print("[\x1b[0;36m!\x1b[0m] 测试OAuth授权URL...")

        # 步骤1: 首先访问OJ主页，获取初始cookie
        self.session.get(self.base_url, verify=False)

        # 步骤2: 直接访问CAS的OAuth授权URL
        cas_authorize_url = "https://cas.sustech.edu.cn/cas/oauth2.0/authorize?response_type=code&client_id=FTdwYshmid34mMtRURbH5Naa6eclg4s6BVP7&redirect_uri=https://oj.cse.sustech.edu.cn/api/login/cas/"

        self.session.headers.update({'Referer': self.base_url})
        response = self.session.get(cas_authorize_url, allow_redirects=False, verify=False)

        if response.status_code != 302 or 'Location' not in response.headers:
            print("[\x1b[0;31mx\x1b[0m] 授权URL未返回预期的302重定向")
            return False

        # 步骤3: 跟随重定向到CAS登录页面
        login_url = response.headers['Location']
        print("[\x1b[0;36m!\x1b[0m] CAS登录中...")
        response = self.session.get(login_url, verify=False)

        if response.status_code != 200:
            print("[\x1b[0;31mx\x1b[0m] 访问登录页面失败")
            return False

        # 步骤4: 从登录页面提取execution参数
        execution = None
        match = re.search(r'name="execution" value="([^"]+)"', response.text)
        if match:
            execution = match.group(1)

        if not execution:
            print("[\x1b[0;31mx\x1b[0m] 无法从登录页面提取execution参数")
            return False

        # 步骤5: 提交登录表单
        login_data = {
            'username': username,
            'password': password,
            'execution': execution,
            '_eventId': 'submit'
        }

        self.session.headers.update({'Referer': login_url})
        response = self.session.post(login_url, data=login_data, allow_redirects=False, verify=False)

        if response.status_code != 302 or 'Location' not in response.headers:
            print("[\x1b[0;31mx\x1b[0m] 登录请求失败")
            if response.status_code == 401:
                print("[\x1b[0;31mx\x1b[0m] 用户名或密码错误")
            return False

        # 步骤6: 跟随登录成功后的所有重定向
        current_url = response.headers['Location']
        print("[\x1b[0;32m+\x1b[0m] CAS登录成功，开始跟随重定向链...")

        # 手动跟踪所有重定向
        max_redirects = 10
        redirect_count = 0

        while redirect_count < max_redirects:
            print(f"[\x1b[0;36m!\x1b[0m] 跟随重定向{redirect_count + 1}...")
            response = self.session.get(current_url, allow_redirects=False, verify=False)

            # 检查是否有更多重定向
            if response.status_code in (301, 302, 303, 307) and 'Location' in response.headers:
                current_url = response.headers['Location']
                redirect_count += 1

                # 如果重定向回到OJ系统，则完成最后跳转
                if self.base_url in current_url:
                    print(f"[\x1b[0;36m!\x1b[0m] 跟随重定向{redirect_count + 1}，重定向到OJ系统...")
                    response = self.session.get(current_url, allow_redirects=True, verify=False)
                    break
            else:
                # 没有更多的重定向
                break

        # 步骤7: 检查是否已经获取JCoderID
        jcoder_id = self.session.cookies.get('JCoderID')
        if not jcoder_id:
            print("[\x1b[0;31mx\x1b[0m] 登录过程未获取到JCoderID")
            return False

        print("[\x1b[0;32m+\x1b[0m] 获取到JCoderID")

        # 步骤8: 关键步骤! 调用cors API获取csrftoken
        headers = {
            'Accept': '*/*',
            'Referer': f'{self.base_url}/home',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        print(f"[\x1b[0;36m!\x1b[0m] 获取CSRF令牌中...")
        response = self.session.get(f"{self.base_url}/api/cors/", headers=headers, verify=False)

        if response.status_code != 200:
            print("[\x1b[0;31mx\x1b[0m] 访问cors API失败")
            return False

        # 检查是否已设置csrftoken
        csrf_token = self.session.cookies.get('csrftoken')
        if not csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 未能通过cors API获取csrftoken")
            return False

        self.csrf_token = csrf_token
        print("[\x1b[0;32m+\x1b[0m] 成功获取csrftoken")

        # 验证登录状态完整性
        if jcoder_id and csrf_token:
            print("[\x1b[0;32m+\x1b[0m] cookies获取完整")
            return True
        else:
            print("[\x1b[0;31mx\x1b[0m] 登录状态不完整")
            return False

    def save_cookies(self, filename="oj_cookies.pkl"):
        """保存cookies到文件"""
        # Store cookies and additional info like CSRF token and timestamp
        data = {
            'cookies': self.session.cookies,
            'csrf_token': self.csrf_token,
            'timestamp': datetime.now().timestamp()
        }

        try:
            with open(filename, 'wb') as f:
                dump(data, f)
            print(f"[\x1b[0;32m+\x1b[0m] Cookies保存到 {filename}")
            return True
        except Exception as e:
            print(f"[\x1b[0;31mx\x1b[0m] Cookies保存失败·: {e}")
            return False

    def load_cookies(self, filename="oj_cookies.pkl"):
        """从文件加载cookies"""
        if not os.path.exists(filename):
            print(f"[\x1b[0;33m!\x1b[0m] 没有找到保存的Cookies文件")
            return False

        try:
            with open(filename, 'rb') as f:
                data = load(f)

            # Check if cookies are too old
            timestamp = data.get('timestamp', 0)
            if datetime.now().timestamp() - timestamp > 7200:
                return False

            # Restore session cookies
            self.session.cookies = data['cookies']
            self.csrf_token = data.get('csrf_token')

            return True
        except Exception as e:
            print(f"[\x1b[0;31mx\x1b[0m] 保存Cookies时出错: {e}")
            return False

    def check_cookies_status(self):
        """检查Cookies有效性"""
        courses = self.get_my_courses()
        if courses and isinstance(courses, dict) and 'list' in courses:
            return True
        return False

    def clear_session(self):
        """Clear all cookies and session data to start fresh"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Sec-Ch-Ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Priority': 'u=1, i'
        })
        self.csrf_token = None

    def get_my_courses(self):
        """获取用户的课程列表"""
        if not self.csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 没有CSRF令牌，无法发送请求")
            return False

        url = f"{self.base_url}/api/union/my_courses_list/"

        # 设置请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': self.csrf_token,
            'Referer': f"{self.base_url}/union",
            'Origin': self.base_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # 设置请求数据
        data = {
            'page': '1',
            'offset': '40',
            'query': '',
            'tags': '[]'
        }

        # 发送请求
        response = self.session.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            try:
                result = response.json()
                if 'list' in result and result['list']:
                    return result
                else:
                    return result
            except json.JSONDecodeError:
                print("[\x1b[0;31mx\x1b[0m] 响应不是JSON格式")
                return False
        else:
            print(f"[\x1b[0;31mx\x1b[0m] 请求失败，HTTP状态码: {response.status_code}")
            return False

    def get_homeworks_list(self, course_id):
        """获取指定课程的作业列表"""
        if not self.csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 没有CSRF令牌，无法发送请求")
            return False

        url = f"{self.base_url}/api/course/homeworks/list/"

        # 设置请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': self.csrf_token,
            'Referer': f"{self.base_url}/course/{course_id}",
            'Origin': self.base_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # 设置请求数据 - 修改为正确的参数格式
        data = {
            'page': '1',
            'offset': '40',
            'courseId': course_id,
            'category': '0'
        }

        print(f"\n[\x1b[0;36m!\x1b[0m] 获取课程{course_id}的作业列表...")

        # 发送请求
        response = self.session.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            try:
                result = response.json()
                if 'list' in result and result['list']:
                    return result
                else:
                    print("[\x1b[0;33m!\x1b[0m] 获取到的作业列表为空")
                    return result
            except json.JSONDecodeError:
                print("[\x1b[0;31mx\x1b[0m] 响应不是JSON格式")
                return False
        else:
            print(f"[\x1b[0;31mx\x1b[0m] 请求失败，HTTP状态码: {response.status_code}")
            return False

    def get_homework_info(self, homework_id, course_id):
        """获取作业信息"""
        if not self.csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 没有CSRF令牌，无法发送请求")
            return False

        url = f"{self.base_url}/api/homework/general/"

        # 设置请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': self.csrf_token,
            'Referer': f"{self.base_url}/course/{course_id}/homework/{homework_id}",
            'Origin': self.base_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # 设置请求数据
        data = {
            'homeworkId': homework_id,
            'courseId': course_id
        }

        # 发送请求
        response = self.session.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except json.JSONDecodeError:
                print("[\x1b[0;31mx\x1b[0m] 响应不是JSON格式")
                return False
        else:
            print(f"[\x1b[0;31mx\x1b[0m] 请求失败，HTTP状态码: {response.status_code}")
            return False

    def get_homework_problems(self, homework_id, course_id):
        """获取作业的问题列表"""
        if not self.csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 没有CSRF令牌，无法发送请求")
            return False

        url = f"{self.base_url}/api/homework/problems/list/"

        # 设置请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': self.csrf_token,
            'Referer': f"{self.base_url}/course/{course_id}/homework/{homework_id}",
            'Origin': self.base_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # 设置请求数据
        data = {
            'homeworkId': homework_id,
            'courseId': course_id
        }

        # 发送请求
        response = self.session.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            try:
                result = response.json()
                if 'list' in result and result['list']:
                    return result
                else:
                    print("[\x1b[0;33m!\x1b[0m] 获取到的问题列表为空")
                    return result
            except json.JSONDecodeError:
                print("[\x1b[0;31mx\x1b[0m] 响应不是JSON格式")
                return False
        else:
            print(f"[\x1b[0;31mx\x1b[0m] 请求失败，HTTP状态码: {response.status_code}")
            return False

    def get_problem_info(self, problem_id, homework_id, course_id):
        """获取问题详细信息"""
        if not self.csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 没有CSRF令牌，无法发送请求")
            return False

        url = f"{self.base_url}/api/homework/problems/info/"

        # 设置请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': self.csrf_token,
            'Referer': f"{self.base_url}/course/{course_id}/homework/{homework_id}",
            'Origin': self.base_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # 设置请求数据
        data = {
            'problemId': problem_id,
            'homeworkId': homework_id,
            'courseId': course_id
        }

        # 发送请求
        response = self.session.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except json.JSONDecodeError:
                print("[\x1b[0;31mx\x1b[0m] 响应不是JSON格式")
                return False
        else:
            print(f"[\x1b[0;31mx\x1b[0m] 请求失败，HTTP状态码: {response.status_code}")
            return False

    def get_problem_submission_records(self, problem_id, homework_id, course_id):
        """获取问题的提交记录"""
        if not self.csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 没有CSRF令牌，无法发送请求")
            return False

        url = f"{self.base_url}/api/homework/submit/recent_records/"

        # 设置请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': self.csrf_token,
            'Referer': f"{self.base_url}/course/{course_id}/homework/{homework_id}",
            'Origin': self.base_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # 设置请求数据
        data = {
            'problemId': problem_id,
            'homeworkId': homework_id,
            'courseId': course_id
        }

        # 发送请求
        response = self.session.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except json.JSONDecodeError:
                print("[\x1b[0;31mx\x1b[0m] 响应不是JSON格式")
                return False
        else:
            print(f"[\x1b[0;31mx\x1b[0m] 请求失败，HTTP状态码: {response.status_code}")
            return False

def records_status_color(result_state):
    if result_state == 'AC':
        status = "AC"
        status_color = "\x1b[0;32m"  # 绿色
    elif result_state == 'WA':
        status = "WA"
        status_color = "\x1b[0;31m"  # 红色
    elif result_state == 'RE':
        status = "RE"
        status_color = "\x1b[0;35m"  # 紫色
    elif result_state == 'CE':
        status = "CE"
        status_color = "\x1b[0;33m"  # 黄红色
    elif result_state == 'TLE':
        status = "TLE"
        status_color = "\x1b[0;91m"  # 橙红色
    elif result_state == 'MLE':
        status = "MLE"
        status_color = "\x1b[0;91m"  # 橙红色
    else:
        status = result_state
        status_color = ''
    return status, status_color

def save_problem_to_file(problem, course_id, homework_id):
    """将题目内容保存为文件"""
    problem_id = problem.get('problemId', 'unknown')
    problem_name = problem.get('problemName', 'unknown').replace('/', '-').replace('\\', '-')  # 替换无效文件名字符
    details = problem.get('details', {})

    # 创建文件名 - 直接在当前目录下保存
    file_name = f"{homework_id}_{problem_id}_{problem_name}.md"

    # 创建一个markdown格式的内容
    content = f"# {problem_name}\n\n"
    content += f"**题目ID:** {problem_id}  \n"
    content += f"**课程:** {course_id}  \n"
    content += f"**作业:** {homework_id}  \n\n"

    # 添加题目属性
    content += "## 题目信息\n\n"

    # 难度
    difficulty = details.get('difficulty', 0)
    difficulty_text = ["未知", "入门", "简单", "普通", "困难", "魔鬼"][min(difficulty, 5)]
    content += f"**难度:** {difficulty_text}  \n"

    # IO模式
    io_mode = details.get('ioMode', 0)
    io_mode_text = "标准输入输出" if io_mode == 0 else "文件输入输出"
    content += f"**IO模式:** {io_mode_text}  \n"

    # 时间限制
    if 'timeLimit' in details:
        content += "**时间限制:**"
        for lang, limit in details['timeLimit'].items():
            content += f" {lang}: {limit} ms  \n"

    # 内存限制
    if 'memoryLimit' in details:
        content += "**内存限制:**"
        for lang, limit in details['memoryLimit'].items():
            content += f" {lang}: {limit} MB  \n"

    # 标签
    if 'publicTags' in details and details['publicTags']:
        content += "**标签:** " + ", ".join(details['publicTags']) + "  \n"

    content += "\n## 题目描述\n\n"

    # 添加题目内容
    if 'content' in details:
        content += details['content'] + "\n"
    else:
        content += "题目内容不可用\n"

    # 添加最近提交记录信息（如果有）- 现在显示最多5条记录
    if 'submission_records' in problem and problem['submission_records']:
        content += "\n## 最近提交记录\n\n"

        # 获取最多5条提交记录
        records_to_show = min(5, len(problem['submission_records']))

        for i in range(records_to_show):
            record = problem['submission_records'][i]
            record_id = record.get('recordId', 'Unknown')
            result_state = record.get('resultState', 'Unknown')
            score = record.get('score', 0)
            submission_time = record.get('submissionTime', 'Unknown')

            # 根据结果状态添加表情
            status_emoji = "❓"
            if result_state == 'AC':
                status_emoji = "✅"
            elif result_state == 'WA':
                status_emoji = "❌"
            elif result_state == 'TLE':
                status_emoji = "⏱️"
            elif result_state == 'MLE':
                status_emoji = "💾"
            elif result_state == 'RE':
                status_emoji = "💥"
            elif result_state == 'CE':
                status_emoji = "⚠️"

            content += f"### 提交 {i + 1} ({submission_time}) {status_emoji}\n\n"
            content += f"**记录ID:** {record_id}  \n"
            content += f"**状态:** {result_state}  \n"
            content += f"**分数:** {score}  \n"

            # 添加代码（如果有）
            if 'code' in record and record['code']:
                content += "\n**提交代码:**\n\n"
                for code_file_name, code in record['code'].items():
                    # 根据文件扩展名确定语言
                    lang = ""
                    if code_file_name.endswith('.java'):
                        lang = "java"
                    elif code_file_name.endswith('.py'):
                        lang = "python"
                    elif code_file_name.endswith('.cpp') or code_file_name.endswith('.c'):
                        lang = "cpp"
                    content += f"**{code_file_name}**\n\n```{lang}\n{code}\n```\n\n"

            # 如果不是最后一条记录，添加分隔线
            if i < records_to_show - 1:
                content += "---\n\n"

    # 保存文件 - 直接在当前目录
    try:
        # 不创建子目录，直接在当前目录保存
        with open(file_name, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_name
    except Exception as e:
        print(f"[\x1b[0;31mx\x1b[0m] 保存题目文件时出错: {e}")
        return None

# 主函数
def main():
    # 固定的用户名和密码
    username = "REMOVED"
    password = "REMOVED"

    requester = OJRequester()

    # Try loading cookies first
    login_successful = False
    if requester.load_cookies():
        # Verify if cookies are still valid
        if requester.check_cookies_status():
            login_successful = True
            print("[\x1b[0;32m+\x1b[0m] 使用本地cookies登录成功")
        else:
            requester.clear_session()

    # If cookies are invalid or not found, perform fresh login
    if not login_successful:
        if requester.cas_login(username, password):
            print("[\x1b[0;32m+\x1b[0m] CAS 登录成功")
            # Save the new cookies
            requester.save_cookies()
        else:
            print("[\x1b[0;31mx\x1b[0m] CAS 登录失败")
            return

    # 获取课程列表
    print(f"\n[\x1b[0;36m!\x1b[0m] 获取课程列表...")
    courses = requester.get_my_courses()
    if courses and 'list' in courses and len(courses['list']) > 0:
        print("[\x1b[0;32m+\x1b[0m] 您的课程列表:")
        for i, course in enumerate(courses['list']):
            print(f"  {i + 1}. [{course['course_id']}] {course['course_name']} - {course['description']}")

        # 默认选择第一门课程
        selected_course = courses['list'][0]['course_id']

        # 获取课程的作业列表
        homeworks = requester.get_homeworks_list(selected_course)
        if homeworks and 'list' in homeworks and len(homeworks['list']) > 0:

            # 按截止日期排序作业列表
            sorted_homeworks = sorted(homeworks['list'],
                                      key=lambda hw: hw.get('nextDate', '9999-12-31 23:59:59'))

            # 定义一个工作函数来获取作业详情
            def fetch_homework_detail(hw):
                """为单个作业获取详细信息的工作函数"""
                hw_id = hw['homeworkId']
                hw_details = requester.get_homework_info(hw_id, selected_course)
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

            now = datetime.now()

            print("[\x1b[0;32m+\x1b[0m] 该课程的作业列表(按截止日期排序):")

            header = "  {:<3} | {:<15} | {:<8} | {:<8} | {:<10} | {:<7} | {:<21}".format(
                "ID", "Name", "Status", "Problems", "Completion", "Score", "Due Date"
            )
            print(header)
            print("-" * len(header))  # 分隔线长度与表头一致

            # 打印作业列表
            for hw in enriched_homeworks:
                # 获取基本信息
                hw_id = hw['homeworkId']
                hw_name = hw['homeworkName']
                due_date = hw.get('nextDate', 'No Due Date')
                problems_count = hw.get('problemsCount', 0)

                # 初始默认值
                status = "Unknown"
                completion = "0%"
                score = "0/0"

                # 根据state字段判断状态
                # state: 1=未开始, 2=进行中, 3=已截止, 4=已完成
                state = hw.get('state', 0)
                if state == 1:
                    status = "\x1b[0;33mPending\x1b[0m"
                elif state == 2:
                    status = "\x1b[0;36mActive\x1b[0m"
                elif state == 3:
                    status = "\x1b[0;31mClosed\x1b[0m"
                elif state == 4:
                    status = "\x1b[0;32mFinished\x1b[0m"

                # 判断截止时间
                if due_date != 'No Due Date':
                    due_datetime = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
                    if now > due_datetime and state == 2:
                        status = "\x1b[0;31mExpired\x1b[0m"

                # 从详细信息中提取完成度和得分
                if 'details' in hw and hw['details']:
                    details = hw['details']

                    # 提取分数信息
                    if 'currentScore' in details and 'totalScore' in details:
                        current = details.get('currentScore', 0)
                        total = details.get('totalScore', 100.0)
                        score = f"{current}/{int(total)}"

                        # 基于完成率计算完成度
                        if 'attemptRate' in details:
                            attempt_rate = details.get('attemptRate', 0)
                            completion = f"{int(attempt_rate)}%"

                        # 如果分数是满分，更新状态
                        if current == total and total > 0:
                            status = "\x1b[0;32mComplete\x1b[0m"

                # 输出格式化的作业信息行，保证对齐
                print("  {:<3} | {:<15} | {:<8} | {:<8} | {:<10} | {:<7} | {:<21}".format(
                    hw_id, hw_name, status, problems_count, completion, score, due_date
                ))

            # 用户输入作业ID
            print("\n请输入要查看的作业ID(直接回车查看最近作业):", end='')
            user_input = input().strip()

            # 如果用户没有输入，选择第一个作业
            if not user_input:
                selected_hw = enriched_homeworks[0]['homeworkId']
            else:
                try:
                    selected_hw = int(user_input)
                    # 验证输入的作业ID是否存在
                    hw_exists = any(hw['homeworkId'] == selected_hw for hw in enriched_homeworks)
                    if not hw_exists:
                        print(f"[\x1b[0;33m!\x1b[0m] 警告: 输入的作业ID {selected_hw} 不在列表中，但仍将尝试获取")
                except ValueError:
                    print("[\x1b[0;31mx\x1b[0m] 无效的输入，请输入数字ID")
                    return

            # 用户选择作业后，获取问题列表
            if selected_hw:
                # 获取作业问题列表
                print(f"\n[\x1b[0;36m!\x1b[0m] 获取作业ID{selected_hw}的题目列表...")
                problems_list = requester.get_homework_problems(selected_hw, selected_course)

                if problems_list and 'list' in problems_list and problems_list['list']:

                    # 定义函数以获取题目详细信息
                    def fetch_problem_detail(problem):
                        """为单个问题获取详细信息的工作函数"""
                        problem_id = problem.get('problemId', 'Unknown')

                        # 获取问题详情
                        problem_info = requester.get_problem_info(problem_id, selected_hw, selected_course)
                        if problem_info:
                            problem['details'] = problem_info
                        else:
                            problem['details'] = {}

                        # 获取提交记录
                        submission_records = requester.get_problem_submission_records(problem_id, selected_hw,
                                                                                      selected_course)
                        if submission_records and 'list' in submission_records and len(submission_records['list']) > 0:
                            problem['submission_records'] = submission_records['list']
                        else:
                            problem['submission_records'] = []

                        return problem

                    # 使用多线程获取每个题目的详细信息
                    original_problems = problems_list['list']
                    problem_results = {}  # 使用字典存储结果，以保持顺序

                    max_workers = min(10, len(original_problems))  # 最多10个线程

                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # 提交所有题目的详情请求到线程池，并记录原始索引
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
                                problem_results[index] = problem

                    # 按原始顺序重建题目列表
                    enriched_problems = [problem_results[i] for i in range(len(original_problems))]

                    # 修改问题列表显示部分
                    # 显示问题列表
                    print("\r[\x1b[0;32m+\x1b[0m] 请求成功，作业中的问题列表:")

                    # 定义表头
                    print(" {:<2} | {:<25} | {:<5} | {:<10} | {:<15}".format(
                        "No.", "Problem Name", "Status", "Difficulty", "Time Limit"
                    ))
                    print("-" * 70)  # 增加分隔线长度

                    for i, problem in enumerate(enriched_problems):
                        problem_name = problem.get('problemName', 'Unknown')
                        details = problem.get('details', {})

                        # 提取状态信息
                        status = "Not Attempted"
                        status_color = "\x1b[0;37m"  # 默认浅灰色

                        if 'submission_records' in problem and problem['submission_records']:
                            # 获取最新提交
                            latest = problem['submission_records'][0]
                            result_state = latest.get('resultState', '')
                            status, status_color = records_status_color(result_state)

                        colored_status = f"{status_color}{status}\x1b[0m"

                        # 提取难度
                        difficulty = details.get('difficulty', 0)
                        difficulty_levels = ["Unknown", "Noob", "Easy", "Normal", "Hard", "Demon"]
                        difficulty_text = difficulty_levels[min(difficulty, 5)]

                        # 提取时间限制
                        time_limit = "Unknown"
                        if 'timeLimit' in details and 'Java' in details['timeLimit']:
                            time_limit = f"{details['timeLimit']['Java']} ms"

                        # 基本格式，先不带颜色
                        base_line = " {:<2}  | {:<25} | {:<5} | {:<10} | {:<15}".format(
                            i + 1, problem_name, status, difficulty_text, time_limit
                        )

                        # 根据难度添加颜色代码，但保持格式
                        if difficulty == 1:
                            colored_diff = f"\x1b[0;36mNoob\x1b[0m"  # 青色 - Noob
                        elif difficulty == 2:
                            colored_diff = f"\x1b[0;32mEasy\x1b[0m"  # 绿色 - Easy
                        elif difficulty == 3:
                            colored_diff = f"\x1b[0;33mNormal\x1b[0m"  # 黄色 - Normal
                        elif difficulty == 4:
                            colored_diff = f"\x1b[0;31mHard\x1b[0m"  # 红色 - Hard
                        elif difficulty == 5:
                            colored_diff = f"\x1b[0;35mDemon\x1b[0m"  # 紫色 - Demon
                        else:
                            colored_diff = "Unknown"

                        # 构造包含颜色的行，使用固定位置替换文本
                        parts = base_line.split("|")
                        parts[2] = " " + colored_status + " " * (7 - len(status))  # 状态列
                        parts[3] = " " + colored_diff + " " * (11 - len(difficulty_text))  # 难度列

                        colored_line = "|".join(parts)
                        print(colored_line)

                    # 用户选择题目
                    print("\n请选择要查看的题目编号(1-{0})，或输入0返回上一级:".format(len(enriched_problems)), end='')
                    problem_input = input().strip()

                    if problem_input == '0':
                        print("[\x1b[0;36m!\x1b[0m] 返回上一级...")
                        return

                    try:
                        problem_index = int(problem_input) - 1
                        if 0 <= problem_index < len(enriched_problems):
                            selected_problem = enriched_problems[problem_index]
                            problem_id = selected_problem['problemId']

                            # 使用已获取的题目详情，不再重新请求
                            problem_info = selected_problem.get('details', {})

                            if problem_info:
                                print(f"\n{'-' * 40}")
                                print(f"题目编号: {problem_index + 1}")
                                print(f"题目名称: {selected_problem['problemName']}")

                                # 显示题目的其他信息
                                print(f"{'-' * 40}")
                                print(f"题目类型: {problem_info.get('problemType', '未知')}")

                                # 显示时间限制
                                if 'timeLimit' in problem_info:
                                    time_limits = problem_info['timeLimit']
                                    print("时间限制: ", end='')
                                    for lang, limit in time_limits.items():
                                        print(f": {limit} ms")

                                # 显示内存限制
                                if 'memoryLimit' in problem_info:
                                    memory_limits = problem_info['memoryLimit']
                                    print("内存限制: ", end='')
                                    for lang, limit in memory_limits.items():
                                        print(f"{limit} MB")

                                # 显示IO模式
                                io_mode = problem_info.get('ioMode', 0)
                                io_mode_text = "标准输入输出" if io_mode == 0 else "文件输入输出"
                                print(f"IO模式: {io_mode_text}")

                                # 显示难度 - 题目详情部分
                                difficulty = problem_info.get('difficulty', 0)
                                difficulty_text = ["未知", "入门", "简单", "普通", "困难", "魔鬼"][min(difficulty, 5)]
                                print(f"难度等级: {difficulty_text}")

                                # 显示标签
                                if 'publicTags' in problem_info and problem_info['publicTags']:
                                    print("公开标签:", ", ".join(problem_info['publicTags']))

                                print(f"{'-' * 40}")
                                print("[\x1b[0;36m!\x1b[0m]获取最近提交记录中...", end='')
                                submission_records = requester.get_problem_submission_records(problem_id, selected_hw,
                                                                                              selected_course)

                                if submission_records and 'list' in submission_records and submission_records['list']:
                                    records = submission_records['list']
                                    records_count = min(5, len(records))  # 最多显示5条记录

                                    print(f"\r[\x1b[0;32m+\x1b[0m]最近 {records_count} 条提交记录:")

                                    # 创建表头 - 使用与作业列表相同的风格
                                    header = " {:<6} | {:<5} | {:<19} | {:<8}".format(
                                        "Status", "Score", "Submit Time", "Record ID"
                                    )
                                    print(header)
                                    print("-" * len(header))  # 分隔线长度与表头一致

                                    # 显示记录
                                    for i in range(records_count):
                                        record = records[i]
                                        result_state = record.get('resultState', 'Unknown')
                                        score = record.get('score', 0)
                                        submission_time = record.get('submissionTime', 'Unknown')
                                        record_id = record.get('recordId', 'Unknown')

                                        # 获取状态的颜色文本
                                        result_colored = f"{records_status_color(result_state)[1]}{result_state}\x1b[0m"

                                        # 使用与作业列表相同的格式化方式
                                        line = " {:<6} | {:<5} | {:<19} | {:<8}".format(
                                            result_state, score, submission_time, record_id
                                        )

                                        # 使用替换的方式，将普通状态文本替换为带颜色的文本
                                        # 这样不会影响原始格式和对齐
                                        line = line.replace(result_state, result_colored, 1)

                                        print(line)
                                else:
                                    print("没有找到提交记录或获取记录失败")

                                # 询问用户是否要保存题目内容到本地
                                print("\n是否将题目内容保存到本地? (y/n):", end='')
                                save_choice = input().strip().lower()

                                if not save_choice or save_choice == 'y':
                                    print(f"[\x1b[0;36m!\x1b[0m] 正在保存题目内容到本地...")
                                    file_path = save_problem_to_file(selected_problem, selected_course, selected_hw)
                                    if file_path:
                                        print(f"\r[\x1b[0;32m+\x1b[0m] 题目内容已保存到: {file_path}")
                                    else:
                                        print("[\x1b[0;31mx\x1b[0m] 题目内容保存失败")

                                print(f"{'-' * 80}")
                            else:
                                print("[\x1b[0;31mx\x1b[0m] 题目详情不可用")
                        else:
                            print("[\x1b[0;31mx\x1b[0m] 无效的题目编号")
                    except ValueError:
                        print("[\x1b[0;31mx\x1b[0m] 请输入有效的数字")
                else:
                    print("[\x1b[0;31mx\x1b[0m] 获取题目列表失败或列表为空")
            else:
                print("[\x1b[0;31mx\x1b[0m] 未选择有效的作业")
        else:
            print("[\x1b[0;31mx\x1b[0m] 无法获取作业列表或列表为空")
    else:
        print("[\x1b[0;31mx\x1b[0m] 无法获取课程列表或列表为空")

if __name__ == "__main__":
    main()
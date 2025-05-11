import requests
import os
import re
import json
from datetime import datetime
from pickle import dump, load

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
            if response.status_code == 401 or response.status_code == 200:
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

    def submit_homework(self, homework_id, problem_id, course_id, file_paths):
        """提交Java作业到OJ平台"""
        # 检查CSRF令牌是否存在
        if not self.csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 没有CSRF令牌，无法发送提交请求")
            return False

        # 导入必要的库
        from utils.file_handlers import read_java_file

        files_dict = {}
        if not file_paths: # 确保 file_paths 不为空
            print("[\x1b[0;31mx\x1b[0m] 没有提供Java文件路径")
            return None

        print(f"[\x1b[0;36m!\x1b[0m] 读取Java文件中...")
        for file_path in file_paths:
            java_content = read_java_file(file_path)
            if not java_content:
                print(f"[\x1b[0;31mx\x1b[0m] 无法读取Java文件: {file_path}")
                return None 

            # 提取带扩展名的文件名
            file_name = os.path.basename(file_path)
            files_dict[file_name] = java_content
        
        if not files_dict: # 如果所有文件都读取失败
            print("[\x1b[0;31mx\x1b[0m] 无法读取任何Java文件内容")
            return None

        # 准备files JSON结构
        files_json = json.dumps(files_dict)

        # 准备API URL
        url = f"{self.base_url}/api/homework/submit/objective/"

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
            'problemId': problem_id,
            'courseId': course_id,
            'language': '3',  # 将语言从 '2' 改为 '3'，可能单文件是2，多文件是3
            'subGroup': 'false',
            'files': files_json
        }

        # 发送请求
        print(f"[\x1b[0;36m!\x1b[0m] 正在提交Java作业...")
        response = self.session.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            try:
                result = response.json()
                if 'recordId' in result:
                    print(f"[\x1b[0;32m+\x1b[0m] 提交成功！记录ID: {result.get('recordId')}")
                    return result
                else:
                    print("[\x1b[0;31mx\x1b[0m] 提交响应缺少recordId")
                    return None
            except json.JSONDecodeError:
                print("[\x1b[0;31mx\x1b[0m] 响应不是JSON格式")
                return None
        else:
            print(f"[\x1b[0;31mx\x1b[0m] 提交请求失败，HTTP状态码: {response.status_code}")
            print(response.text)
            return None

    def get_submission_result(self, record_id, course_id, homework_id):
        """获取提交记录的批改结果

        Args:
            record_id: 提交记录ID
            course_id: 课程ID
            homework_id: 作业ID

        Returns:
            批改结果的JSON数据，如果请求失败则返回None
        """
        if not self.csrf_token:
            print("[\x1b[0;31mx\x1b[0m] 没有CSRF令牌，无法发送请求")
            return None

        url = f"{self.base_url}/api/record/result/"

        # 设置请求头
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': self.csrf_token,
            'Referer': f"{self.base_url}/course/{course_id}/homework/{homework_id}/record/{record_id}",
            'Origin': self.base_url,
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        # 设置请求数据
        data = {
            'recordId': record_id,
            'courseId': course_id,
            'homeworkId': homework_id
        }

        # 发送请求
        response = self.session.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            try:
                result = response.json()
                return result
            except json.JSONDecodeError:
                print("[\x1b[0;31mx\x1b[0m] 响应不是JSON格式")
                return None
        else:
            print(f"[\x1b[0;31mx\x1b[0m] 请求失败，HTTP状态码: {response.status_code}")
            return None
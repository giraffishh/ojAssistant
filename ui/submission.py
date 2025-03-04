import os
import sys
import time
import hashlib


def get_file_hash(content=None, file_path=None):
    """
    计算文件或内容的SHA-256哈希值

    Args:
        content: 文件内容字符串
        file_path: 文件路径

    Returns:
        哈希值，如果参数无效则返回None
    """
    if content is not None:  # 优先使用内容参数
        try:
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"[\x1b[0;31mx\x1b[0m] 计算内容哈希值时出错: {e}")
            return None

    elif file_path is not None and os.path.exists(file_path):  # 其次使用文件路径
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return hashlib.sha256(f.read().encode('utf-8')).hexdigest()
        except Exception as e:
            print(f"[\x1b[0;31mx\x1b[0m] 计算文件哈希值时出错: {e}")
            return None

    return None


def handle_submission(requester, problem, course_id, homework_id):
    """处理Java文件的选择和提交。自动使用工作目录中的Main.java文件。

    Returns:
        False: 提交失败或取消
        dict: 包含提交结果信息的字典，其中all_correct键表示是否全部通过
    """
    # 导入配置
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from config import WORK_DIRECTORY
    except ImportError:
        print("[\x1b[0;31mx\x1b[0m] 未找到config.py文件，使用当前目录作为工作目录")
        WORK_DIRECTORY = "."

    # 确保course_id和homework_id是字符串，而不是字典
    if isinstance(course_id, dict) and 'id' in course_id:
        course_id = course_id['id']
    if isinstance(homework_id, dict) and 'id' in homework_id:
        homework_id = homework_id['id']

    print(f"\n{'-' * 40}")
    print(f"提交题目解答: {problem['title'] if 'title' in problem else problem['problemName']}")
    print(f"{'-' * 40}")

    # 自动查找Main.java文件
    default_file = os.path.join(WORK_DIRECTORY, "Main.java")
    if os.path.exists(default_file):
        print(f"[\x1b[0;32m+\x1b[0m] 找到默认文件: {default_file}")
        use_default = input("是否使用此文件? (y/n，默认y): ").strip().lower() or 'y'

        if use_default == 'y':
            file_path = default_file
        else:
            # 用户选择输入其他文件路径
            file_path = get_java_file_path()
            if not file_path:
                return False
    else:
        print(f"[\x1b[0;33m!\x1b[0m] 在工作目录({WORK_DIRECTORY})中未找到作业的文件")
        file_path = get_java_file_path()
        if not file_path:
            return False

    # 读取当前文件内容
    from utils.file_handlers import read_java_file
    current_file_content = read_java_file(file_path)
    if not current_file_content:
        print(f"[\x1b[0;31mx\x1b[0m] 无法读取文件内容，提交取消")
        return False

    # 计算当前文件的哈希值
    current_file_hash = get_file_hash(content=current_file_content)
    if not current_file_hash:
        print(f"[\x1b[0;31mx\x1b[0m] 无法计算文件哈希值，提交取消")
        return False

    # 查找上一次提交记录中的代码
    last_submitted_code = None
    last_submission_time = None
    last_record_id = None

    if 'submission_records' in problem and problem['submission_records']:
        # 获取最近一次提交记录
        for record in problem['submission_records']:
            if 'code' in record and record['code']:
                # 找到Java文件的代码
                for code_file, code_content in record['code'].items():
                    if code_file.endswith('.java'):
                        last_submitted_code = code_content
                        last_submission_time = record.get('submissionTime', 'Unknown')
                        last_record_id = record.get('recordId', 'Unknown')
                        break
                if last_submitted_code:
                    break  # 找到代码后跳出循环

    # 如果找到上次提交的代码，计算它的哈希并比较
    if last_submitted_code:
        last_code_hash = get_file_hash(content=last_submitted_code)

        if last_code_hash and last_code_hash == current_file_hash:
            print(f"\n[\x1b[0;31m!\x1b[0m] 检测到文件内容与上一次提交相同，请在修改后及时保存(Ctrl+S)，或开启自动保存功能")
            print(f"上次提交时间: {last_submission_time}")
            print(f"上次提交ID: {last_record_id}")
            print(f"当前文件: {file_path}")
            print(f"[\x1b[0;31mx\x1b[0m] 提交已取消\n")
            return False

    # 确认提交
    print(f"\n准备提交:")
    print(f"- 题目: {problem['title'] if 'title' in problem else problem['problemName']}")
    print(f"- 文件: {file_path}")
    confirm = input("确认提交? (y/n，默认y): ").strip().lower() or 'y'
    if confirm != 'y':
        print("[\x1b[0;33m!\x1b[0m] 已取消提交")
        return False

    # 提交解答
    result = requester.submit_homework(
        homework_id,
        problem['problemId'],
        course_id,
        file_path
    )

    # 如果提交成功并获取到record_id，则等待并显示批改结果
    if result and 'recordId' in result:
        grading_result = wait_and_show_grading_result(requester, result['recordId'], course_id, homework_id, problem)
        return grading_result

    return False


def wait_and_show_grading_result(requester, record_id, course_id, homework_id, problem):
    """等待并显示批改结果，使用表格形式

    Args:
        requester: OJ请求实例
        record_id: 提交记录ID
        course_id: 课程ID
        homework_id: 作业ID
        problem: 问题对象

    Returns:
        包含提交结果的字典，其中all_correct表示是否全部通过
    """
    from ui.display import display_grading_result

    print(f"\n[\x1b[0;36m!\x1b[0m] 等待系统批改中...")

    # 尝试获取时间限制信息
    time_limit = None
    if 'details' in problem and 'timeLimit' in problem['details'] and 'Java' in problem['details']['timeLimit']:
        time_limit = int(problem['details']['timeLimit']['Java'])

    # 如果无法获取具体时间限制，使用默认值
    if not time_limit:
        time_limit = 2000  # 默认1000毫秒

    # 根据时间限制计算等待时间，给系统足够的时间批改
    # 初始等待时间设为时间限制（毫秒转秒）
    wait_time = (time_limit) / 1000

    # 最多尝试10次
    for attempt in range(1, 11):
        print(f"\r[\x1b[0;36m!\x1b[0m] 等待批改结果 ({attempt}/10)...", end='')
        time.sleep(wait_time)

        # 获取批改结果
        result = requester.get_submission_result(record_id, course_id, homework_id)

        if not result:
            print("[\x1b[0;31mx\x1b[0m] 获取批改结果失败")
            return {'all_correct': False}

        # 检查是否还在批改中
        if result['resultState'] == 'JG':
            # 增加下一次等待时间
            wait_time = min(wait_time * 1.5, 5)  # 最长等待10秒
            continue

        # 添加记录ID到结果中，以便显示
        result['recordId'] = record_id

        # 使用display.py中的函数显示批改结果
        display_grading_result(result)

        # 检查所有测试用例是否都通过
        all_correct = True
        for test_result in result['resultList']:
            if test_result['state'] != 'AC':
                all_correct = False
                break

        # 返回结果以及是否全部通过的标志
        return {
            'result': result,
            'all_correct': all_correct and result['resultState'] == 'AC'
        }

    # 如果尝试次数用完仍未完成批改
    print("[\x1b[0;31mx\x1b[0m] 批改超时，请稍后在OJ平台上查看结果")
    return {'all_correct': False}


def get_java_file_path():
    """获取Java文件路径"""
    while True:
        file_path = input("请输入Java文件路径（输入'q'退出）: ")

        if file_path.lower() == 'q':
            print("[\x1b[0;33m!\x1b[0m] 已取消提交")
            return None

        if not os.path.exists(file_path):
            print("[\x1b[0;31mx\x1b[0m] 找不到文件，请重试。")
            continue

        if not file_path.lower().endswith('.java'):
            print("[\x1b[0;31mx\x1b[0m] 请选择Java文件（.java）")
            continue

        return file_path
import os
import sys
import time


def handle_submission(requester, problem, course_id, homework_id):
    """处理Java文件的选择和提交。自动使用工作目录中的Main.java文件。"""

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
        print(f"[\x1b[0;33m!\x1b[0m] 在工作目录({WORK_DIRECTORY})中未找到Main.java文件")
        file_path = get_java_file_path()
        if not file_path:
            return False

    # 确认提交
    print(f"\n准备提交:")
    print(f"- 题目: {problem['title'] if 'title' in problem else problem['problemName']}")
    print(f"- 文件: {file_path}")
    confirm = input("确认提交？(y/n): ")
    if confirm.lower() != 'y':
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
        wait_and_show_grading_result(requester, result['recordId'], course_id, homework_id, problem)

    return result is not None


def wait_and_show_grading_result(requester, record_id, course_id, homework_id, problem):
    """等待并显示批改结果，使用表格形式

    Args:
        requester: OJ请求实例
        record_id: 提交记录ID
        course_id: 课程ID
        homework_id: 作业ID
        problem: 问题对象
    """
    from ui.display import display_grading_result

    # 尝试获取时间限制信息
    time_limit = None
    if 'details' in problem and 'timeLimit' in problem['details'] and 'Java' in problem['details']['timeLimit']:
        time_limit = int(problem['details']['timeLimit']['Java'])

    # 如果无法获取具体时间限制，使用默认值
    if not time_limit:
        time_limit = 1000  # 默认1000毫秒

    # 根据时间限制计算等待时间，给系统足够的时间批改
    # 初始等待时间设为时间限制的2倍（毫秒转秒）+ 1秒缓冲
    wait_time = (time_limit * 2) / 1000 + 1

    # 最多尝试10次
    for attempt in range(1, 11):
        print(f"[\x1b[0;36m!\x1b[0m] 等待系统批改结果 ({attempt}/10)...")
        time.sleep(wait_time)

        # 获取批改结果
        result = requester.get_submission_result(record_id, course_id, homework_id)

        if not result:
            print("[\x1b[0;31mx\x1b[0m] 获取批改结果失败")
            return

        # 检查是否还在批改中
        if result['resultState'] == 'JG':
            print("[\x1b[0;33m!\x1b[0m] 系统仍在批改中，继续等待...")
            # 增加下一次等待时间
            wait_time = min(wait_time * 1.5, 10)  # 最长等待10秒
            continue

        # 添加记录ID到结果中，以便显示
        result['recordId'] = record_id

        # 使用display.py中的函数显示批改结果
        display_grading_result(result)
        return

    # 如果尝试次数用完仍未完成批改
    print("[\x1b[0;31mx\x1b[0m] 批改超时，请稍后在OJ平台上查看结果")


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
from utils import records_status_color, save_problem_to_file
from datetime import datetime
import re


def display_courses(requester):
    """获取并显示课程列表"""
    print(f"\n[\x1b[0;36m!\x1b[0m] 获取课程列表...")
    courses = requester.get_my_courses()

    if courses and 'list' in courses and len(courses['list']) > 0:
        print("[\x1b[0;32m+\x1b[0m] 您的课程列表:")
        for i, course in enumerate(courses['list']):
            print(f"  {i + 1}. [{course['course_id']}] {course['course_name']} - {course['description']}")
        return courses
    else:
        print("[\x1b[0;31mx\x1b[0m] 无法获取课程列表或列表为空")
        return None

def display_homeworks(enriched_homeworks):
    """格式化显示作业列表

    Args:
        enriched_homeworks: 包含详细信息的作业列表

    Returns:
        布尔值，表示是否成功显示作业列表
    """
    if not enriched_homeworks:
        print("[\x1b[0;31mx\x1b[0m] 没有可显示的作业")
        return False

    now = datetime.now()
    print("[\x1b[0;32m+\x1b[0m] 该课程的作业列表(按截止日期排序):")

    # 表头
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
        status_color = ""
        completion = "0%"
        score = "0/0"

        # 根据state字段判断状态
        # state: 1=未开始, 2=进行中, 3=已截止, 4=已完成
        state = hw.get('state', 0)
        if state == 1:
            status = "Pending"
            status_color = "\x1b[0;33m"
        elif state == 2:
            status = "Active"
            status_color = "\x1b[0;36m"
        elif state == 3:
            status = "Closed"
            status_color = "\x1b[0;31m"
        elif state == 4:
            status = "Finished"
            status_color = "\x1b[0;32m"

        # 判断截止时间
        if due_date != 'No Due Date':
            due_datetime = datetime.strptime(due_date, '%Y-%m-%d %H:%M:%S')
            if now > due_datetime and state == 2:
                status = "Expired"
                status_color = "\x1b[0;31m"

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
                    status = "Complete"
                    status_color = "\x1b[0;32m"

        # 将状态文本转换为带颜色的版本
        colored_status = f"{status_color}{status}\x1b[0m" if status_color else status

        # 先输出格式化的行，不带颜色（用于正确对齐）
        row = "  {:<3} | {:<15} | {:<8} | {:<8} | {:<10} | {:<7} | {:<21}".format(
            hw_id, hw_name, status, problems_count, completion, score, due_date
        )

        # 替换状态文本为彩色版本
        if status_color:
            row = row.replace(status, colored_status, 1)

        print(row)

    return True

def display_problems_list(enriched_problems):
    """格式化显示问题列表，包括提交状态

    Args:
        enriched_problems: 包含详细信息和提交记录的问题列表

    Returns:
        布尔值，表示是否成功显示问题列表
    """
    if not enriched_problems:
        print("[\x1b[0;31mx\x1b[0m] 没有可显示的题目")
        return False

    # 显示问题列表
    print("\r[\x1b[0;32m+\x1b[0m] 当前作业中的题目列表:")

    # 定义表头 - 更新表头以包含状态列
    print(" {:<2} | {:<30} | {:<13} | {:<10} | {:<15}".format(
        "No.", "Problem Name", "Status", "Difficulty", "Time Limit"
    ))
    print("-" * 85)  # 增加分隔线长度

    for i, problem in enumerate(enriched_problems):
        problem_name = re.sub(r'[^\w\s]', '', problem.get('problemName', 'Unknown'))
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
        if 'timeLimit' in details and isinstance(details['timeLimit'], dict):
            if 'Java' in details['timeLimit']:
                time_limit = f"{details['timeLimit']['Java']} ms"
            elif 'Junit' in details['timeLimit']:  # Check for Junit if Java is not present
                time_limit = f"{details['timeLimit']['Junit']} ms"
            elif details['timeLimit']:  # Fallback to the first available time limit
                first_lang = next(iter(details['timeLimit']))
                time_limit = f"{details['timeLimit'][first_lang]} ms ({first_lang})"

        # 基本格式，先不带颜色
        base_line = " {:<2}  | {:<30} | {:<13} | {:<10} | {:<15}".format(
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
        parts[2] = " " + colored_status + " " * (14 - len(status))  # 状态列
        parts[3] = " " + colored_diff + " " * (11 - len(difficulty_text))  # 难度列

        colored_line = "|".join(parts)
        print(colored_line)

    return True


def display_problems_info(enriched_problems, selected_course, selected_homework):
    """处理用户选择问题并展示详细信息，包括提交记录和保存选项

    Args:
        enriched_problems: 包含详细信息的问题列表
        selected_course: 选中的课程对象或课程ID
        selected_homework: 选中的作业对象或作业ID

    Returns:
        选择的问题对象，如果用户没有选择或退出则返回None
    """
    if not enriched_problems:
        return None

    # 获取课程ID和作业ID（处理对象或直接ID两种情况）
    course_id = selected_course['id'] if isinstance(selected_course, dict) else selected_course
    homework_id = selected_homework['id'] if isinstance(selected_homework, dict) else selected_homework

    # 用户选择问题
    print("\n请选择要查看的题目编号(1-{0})，或输入0返回上一级:".format(len(enriched_problems)), end='')
    problem_input = input().strip()

    if problem_input == '0':
        print("[\x1b[0;36m!\x1b[0m] 返回上一级...")
        return None

    try:
        problem_index = int(problem_input) - 1
        if 0 <= problem_index < len(enriched_problems):
            selected_problem = enriched_problems[problem_index]
            problem_id = selected_problem['problemId']

            # 使用已获取的问题详情，不再重新请求
            problem_info = selected_problem.get('details', {})

            if problem_info:
                # 显示题目基本信息
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
                        print(f"{lang}: {limit} ms")

                # 显示内存限制
                if 'memoryLimit' in problem_info:
                    memory_limits = problem_info['memoryLimit']
                    print("内存限制: ", end='')
                    for lang, limit in memory_limits.items():
                        print(f"{lang}: {limit} MB")

                # 显示IO模式
                io_mode = problem_info.get('ioMode', 0)
                io_mode_text = "标准输入输出" if io_mode == 0 else "文件输入输出"
                print(f"IO模式: {io_mode_text}")

                # 显示难度 - 题目详情部分
                difficulty = problem_info.get('difficulty', 0)
                difficulty_levels = ["未知", "入门", "简单", "普通", "困难", "魔鬼"]
                difficulty_text = difficulty_levels[min(difficulty, 5)]

                # 创建彩色难度文本
                difficulty_color = ""
                if difficulty == 1:
                    difficulty_color = "\x1b[0;36m"  # 青色 - 入门
                elif difficulty == 2:
                    difficulty_color = "\x1b[0;32m"  # 绿色 - 简单
                elif difficulty == 3:
                    difficulty_color = "\x1b[0;33m"  # 黄色 - 普通
                elif difficulty == 4:
                    difficulty_color = "\x1b[0;31m"  # 红色 - 困难
                elif difficulty == 5:
                    difficulty_color = "\x1b[0;35m"  # 紫色 - 魔鬼

                colored_difficulty = f"{difficulty_color}{difficulty_text}\x1b[0m" if difficulty_color else difficulty_text
                print(f"难度等级: {colored_difficulty}")

                # 显示标签
                if 'publicTags' in problem_info and problem_info['publicTags']:
                    print("公开标签:", ", ".join(problem_info['publicTags']))

                # 显示提交记录
                print(f"{'-' * 40}")

                # 使用已经获取的提交记录
                if 'submission_records' in selected_problem and selected_problem['submission_records']:
                    records = selected_problem['submission_records']
                    from config import MAX_RECORDS_TO_SHOW
                    records_count = min(MAX_RECORDS_TO_SHOW, len(records))  # 最多显示5条记录

                    print(f"\n[\x1b[0;32m+\x1b[0m] 最近 {records_count} 条提交记录:")

                    # 创建表头 - 使用与作业列表相同的风格
                    header = " {:<6} | {:<5} | {:<19} | {:<8}".format(
                        "Status", "Score", "Submit Time", "Record ID"
                    )
                    print(header)
                    print("-" * 60)  # 分隔线长度与表头一致

                    # 显示记录
                    for i in range(records_count):
                        record = records[i]
                        result_state = record.get('resultState', 'Unknown')
                        score = record.get('score', 0)
                        submission_time = record.get('submissionTime', 'Unknown')
                        record_id = record.get('recordId', 'Unknown')

                        # 获取状态的颜色和文本，但先不合并
                        status, status_color = records_status_color(result_state)
                        colored_status = f"{status_color}{status}\x1b[0m" if status_color else status

                        # 先创建没有颜色的行用于对齐
                        line = " {:<6} | {:<5} | {:<19} | {:<8}".format(
                            status, score, submission_time, record_id
                        )

                        # 替换普通状态文本为带颜色的文本
                        if status_color:
                            line = line.replace(status, colored_status, 1)

                        print(line)
                else:
                    print("[\x1b[0;33m!\x1b[0m] 没有找到提交记录")

                return selected_problem  # 返回选择的问题对象
            else:
                print("[\x1b[0;31mx\x1b[0m] 题目详情不可用")
                return None
        else:
            print("[\x1b[0;31mx\x1b[0m] 无效的题目编号")
            return None
    except ValueError:
        print("[\x1b[0;31mx\x1b[0m] 请输入有效的数字")
        return None

def display_grading_result(result):
    """显示批改结果，以表格形式展示

    Args:
        result: 批改结果数据

    Returns:
        无返回值
    """
    from utils.formatters import records_status_color

    # 批改完成，显示结果
    print(f"\n\n{'-' * 60}")
    print(f"批改结果 - 提交ID: {result.get('recordId', '')}")

    # 显示基本信息
    status, status_color = records_status_color(result['resultState'])
    print(f"题目: {result['problemName']}")
    print(f"状态: {status_color}{result['resultState']}\x1b[0m")
    print(f"得分: {result['score']}")
    print(f"提交时间: {result['submissionTime']}")
    print(f"{'-' * 60}")

    # 显示详细结果 - 表格形式
    print("\n[\x1b[0;36m!\x1b[0m]测试用例结果:")

    # 表头
    header = " {:<3} | {:<8} | {:<17} | {:<10} | {:<12} | {:<27}".format(
        "No.", "Status", "Test Case", "Time(ms)", "Memory(MB)", "Message"
    )
    print(header)
    print("-" * (len(header) + 2))  # Adjust separator length

    # 表格内容
    for idx, test_result in enumerate(result['resultList']):
        status = test_result['state']
        title_orig = test_result['title']
        time_used = test_result['time']
        memory_used = test_result['memory']
        message_orig = test_result['message'] if test_result['message'] else "N/A"

        # Sanitize title and message by replacing newlines and carriage returns with a space
        title_orig = title_orig.replace('\n', ' ').replace('\r', ' ')
        message_orig = message_orig.replace('\n', ' ').replace('\r', ' ')

        # 根据状态设置颜色
        _, status_color = records_status_color(status)
        status_colored = f"{status_color}{status:<6}\x1b[0m"  # Pad status for color replacement

        # Truncate title and message to fit column width
        title_display = (title_orig[:14] + "...") if len(title_orig) > 17 else title_orig
        message_display = (message_orig[:24] + "...") if len(message_orig) > 27 else message_orig

        # 使用表格格式输出, ensure status has fixed width for replacement
        plain_status_for_align = f"{status:<6}"

        row_format = " {:<3} | {:<8} | {:<17} | {:<10} | {:<12} | {:<27}"

        # Construct the row with plain status first for alignment, then replace with colored
        temp_row = row_format.format(
            idx + 1,
            plain_status_for_align,
            title_display,
            time_used,
            memory_used,
            message_display
        )

        # Replace the plain status part with the colored status part
        final_row = temp_row.replace(plain_status_for_align, status_colored, 1)

        print(final_row)

    # 如果有消息太长，显示完整版本
    for idx, test_result in enumerate(result['resultList']):
        message_orig = test_result['message']
        if len(message_orig) > 27:
            print(f"\n测试用例 {idx + 1} ({test_result['title']}) 完整消息:")
            print(f"  {message_orig}")

    print("-" * (len(header) + 2))  # Adjust separator length
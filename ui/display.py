from utils import records_status_color, save_problem_to_file
from datetime import datetime

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
    print("\r[\x1b[0;32m+\x1b[0m] 请求成功，作业中的题目列表:")

    # 定义表头 - 更新表头以包含状态列
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

    return True


def display_problems_info(enriched_problems, course_id, homework_id):
    """处理用户选择问题并展示详细信息，包括提交记录和保存选项

    Args:
        enriched_problems: 包含详细信息的问题列表
        course_id: 课程ID，用于保存文件
        homework_id: 作业ID，用于保存文件

    Returns:
        布尔值，表示操作是否成功
    """
    if not enriched_problems:
        return False

    # 用户选择问题
    print("\n请选择要查看的题目编号(1-{0})，或输入0返回上一级:".format(len(enriched_problems)), end='')
    problem_input = input().strip()

    if problem_input == '0':
        print("[\x1b[0;36m!\x1b[0m] 返回上一级...")
        return False

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
                difficulty_text = ["未知", "入门", "简单", "普通", "困难", "魔鬼"][min(difficulty, 5)]
                print(f"难度等级: {difficulty_text}")

                # 显示标签
                if 'publicTags' in problem_info and problem_info['publicTags']:
                    print("公开标签:", ", ".join(problem_info['publicTags']))

                # 显示提交记录 - 这部分从原代码直接集成过来
                print(f"{'-' * 40}")

                # 使用已经获取的提交记录
                if 'submission_records' in selected_problem and selected_problem['submission_records']:
                    records = selected_problem['submission_records']
                    records_count = min(5, len(records))  # 最多显示5条记录

                    print(f"[\x1b[0;32m+\x1b[0m] 最近 {records_count} 条提交记录:")

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
                    print("[\x1b[0;33m!\x1b[0m] 没有找到提交记录")

                # 询问用户是否要保存题目内容到本地
                print("\n是否将题目内容保存到本地? (y/n):", end='')
                save_choice = input().strip().lower()

                if not save_choice or save_choice == 'y':
                    print(f"[\x1b[0;36m!\x1b[0m] 正在保存题目内容到本地...")
                    file_path = save_problem_to_file(selected_problem, course_id, homework_id)
                    if file_path:
                        print(f"[\x1b[0;32m+\x1b[0m] 题目内容已保存到: {file_path}")
                    else:
                        print("[\x1b[0;31mx\x1b[0m] 题目内容保存失败")

                print(f"{'-' * 80}")
                return True
            else:
                print("[\x1b[0;31mx\x1b[0m] 题目详情不可用")
                return False
        else:
            print("[\x1b[0;31mx\x1b[0m] 无效的题目编号")
            return False
    except ValueError:
        print("[\x1b[0;31mx\x1b[0m] 请输入有效的数字")
        return False
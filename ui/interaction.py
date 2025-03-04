def select_course(courses, auto_select_first=True):
    """处理课程选择逻辑

    Args:
        courses: 课程列表数据
        auto_select_first: 是否自动选择第一门课程

    Returns:
        selected_course_id: 选择的课程ID，如果选择失败则返回None
    """
    if not courses or 'list' not in courses or not courses['list']:
        return None

    if auto_select_first:
        # 默认选择第一门课程
        selected_course = courses['list'][0]['course_id']
        course_name = courses['list'][0]['course_name']
        return selected_course

    # 如果需要手动选择课程，可以在这里扩展代码
    # 例如：让用户输入课程编号
    print("\n请输入要查看的课程序号(1-{})，或直接回车选择第一门课程:".format(len(courses['list'])))
    user_input = input().strip()

    if not user_input:  # 用户直接按回车
        selected_course = courses['list'][0]['course_id']
        print(f"\n[\x1b[0;36m!\x1b[0m] 选择第一门课程: {courses['list'][0]['course_name']} [{selected_course}]")
        return selected_course

    try:
        index = int(user_input) - 1
        if 0 <= index < len(courses['list']):
            selected_course = courses['list'][index]['course_id']
            print(f"\n[\x1b[0;36m!\x1b[0m] 已选择课程: {courses['list'][index]['course_name']} [{selected_course}]")
            return selected_course
        else:
            print("[\x1b[0;31mx\x1b[0m] 无效的课程序号")
            return None
    except ValueError:
        print("[\x1b[0;31mx\x1b[0m] 无效的输入，请输入数字")
        return None

def select_homework(enriched_homeworks):
    """处理用户选择作业的逻辑

    Args:
        enriched_homeworks: 包含详细信息的作业列表

    Returns:
        selected_hw: 用户选择的作业ID，如果选择失败则返回None
    """
    if not enriched_homeworks:
        return None

    # 用户输入作业ID
    print("\n请输入要查看的作业ID(直接回车默认查看最近作业):", end='')
    user_input = input().strip()

    # 如果用户没有输入，选择第一个作业（最近的）
    if not user_input:
        selected_hw = enriched_homeworks[0]['homeworkId']
        return selected_hw
    else:
        try:
            selected_hw = int(user_input)
            # 验证输入的作业ID是否存在
            hw_exists = any(hw['homeworkId'] == selected_hw for hw in enriched_homeworks)
            if not hw_exists:
                print(f"[\x1b[0;33m!\x1b[0m] 警告: 输入的作业ID {selected_hw} 不在列表中，但仍将尝试获取")
            return selected_hw
        except ValueError:
            print("[\x1b[0;31mx\x1b[0m] 无效的输入，请输入数字ID")
            return None


def interact_with_problems(enriched_problems, selected_course, selected_homework, requester):
    """处理用户与问题的交互，包括查看详情和提交作业

    Args:
        enriched_problems: 包含详细信息的问题列表
        selected_course: 选中的课程对象或课程ID
        selected_homework: 选中的作业对象或作业ID
        requester: OJ请求实例

    Returns:
        bool: True表示成功处理，False表示应该返回上一级
    """
    from ui.display import display_problems_info, display_problems_list
    from ui.submission import handle_submission
    from utils.file_handlers import save_problem_to_file

    # 获取课程ID和作业ID（处理对象或直接ID两种情况）
    course_id = selected_course['id'] if isinstance(selected_course, dict) else selected_course
    homework_id = selected_homework['id'] if isinstance(selected_homework, dict) else selected_homework

    while True:
        display_problems_list(enriched_problems)

        # 用户选择问题并查看详情
        selected_problem = display_problems_info(enriched_problems, selected_course, selected_homework)

        # 如果用户没有选择问题或返回上一级
        if not selected_problem:
            return False  # 明确返回False，表示应返回上一级

        # 当用户选择了题目后，给出选项
        while True:
            print("\n请选择操作: (直接回车默认选项为提交作业）")
            print("1. 保存题目到本地")
            print("2. 提交作业")
            print("0. 返回题目列表")

            choice = input("请输入选项编号: ").strip() or '2'

            if choice == '0':
                # 返回题目列表
                break

            elif choice == '1':
                # 保存题目到本地
                print(f"[\x1b[0;36m!\x1b[0m] 正在保存题目内容到本地...")
                file_path = save_problem_to_file(selected_problem, course_id, homework_id)
                if file_path:
                    print(f"[\x1b[0;32m+\x1b[0m] 题目内容已保存到: {file_path}")
                else:
                    print("[\x1b[0;31mx\x1b[0m] 题目内容保存失败")

                # 保存后继续显示选项
                continue

            elif choice == '2':
                # 提交作业
                print(f"[\x1b[0;36m!\x1b[0m] 准备提交作业...")
                result = handle_submission(requester, selected_problem, course_id, homework_id)

                # 只有当提交没有取消时才刷新题目状态
                if result:
                    # 重新获取问题列表和记录，以显示最新状态
                    print(f"[\x1b[0;36m!\x1b[0m] 正在刷新题目状态...")
                    from services import fetch_and_process_problems
                    updated_problems = fetch_and_process_problems(requester, selected_homework, selected_course)
                    if updated_problems:
                        enriched_problems = updated_problems
                        print(f"[\x1b[0;32m+\x1b[0m] 题目状态已更新")

                    # 检查提交结果
                    if isinstance(result, dict) and result.get('all_correct', False):
                        # 如果全部正确，返回题目列表
                        print(f"[\x1b[0;32m+\x1b[0m] 恭喜！该题目已全部通过，返回题目列表")
                        break
                    else:
                        # 如果不全对，继续显示选项
                        print(f"[\x1b[0;33m!\x1b[0m] 题目未完全通过，继续尝试")
                        continue

            else:
                print("[\x1b[0;31mx\x1b[0m] 无效的选项，请重新选择")
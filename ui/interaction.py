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
    print("\n请输入要查看的作业ID(直接回车查看最近作业):", end='')
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
import os
import sys
import time
import hashlib

from config import WORK_DIRECTORY


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


def get_java_file_paths(work_dir):
    """
    获取用户指定的Java文件路径列表.
    - 用户可以输入逗号分隔的文件名/路径 (相对于工作目录或绝对路径). 用户可以省略 .java 扩展名.
    - 用户可以输入单个目录路径 (将使用该目录下的所有 .java 文件).
    - 用户可以直接按 Enter:
        - 如果工作目录下有 Main.java, 则使用 Main.java.
        - 否则, 如果工作目录下有其他 .java 文件, 则使用所有这些 .java 文件.
        - 否则, 提示无文件并重新提示.
    - 输入 'q' 退出.
    """
    while True:
        paths_input_str = input(
            f"输入Java文件名/路径 (多个用','分隔), 或一个目录, 或按Enter使用工作目录下的文件 (q退出):\n"
            f"(工作目录: {work_dir})\n> "
        ).strip()

        if paths_input_str.lower() == 'q':
            print("[\x1b[0;33m!\x1b[0m] 已取消选择文件")
            return None

        selected_files = []

        if not paths_input_str:  # 用户按下 Enter
            print(f"[\x1b[0;36m!\x1b[0m] 检查工作目录 '{work_dir}'...")
            main_java_path = os.path.join(work_dir, "Main.java")
            
            # 确保 work_dir 存在且是目录
            java_files_in_work_dir = []
            if os.path.isdir(work_dir):
                java_files_in_work_dir = [
                    os.path.join(work_dir, f) for f in os.listdir(work_dir)
                    if f.lower().endswith(".java") and os.path.isfile(os.path.join(work_dir, f))
                ]
            else:
                print(f"[\x1b[0;31mx\x1b[0m] 工作目录 '{work_dir}' 不存在或不是一个目录。")
                continue


            if os.path.exists(main_java_path) and os.path.isfile(main_java_path):
                print(f"[\x1b[0;32m+\x1b[0m] 找到并选择默认文件: {main_java_path}")
                selected_files.append(os.path.abspath(main_java_path))
            elif java_files_in_work_dir:
                print(f"[\x1b[0;32m+\x1b[0m] 未找到 Main.java，选择工作目录中所有 .java 文件:")
                for f_path in java_files_in_work_dir:
                    abs_f_path = os.path.abspath(f_path)
                    print(f"  - {abs_f_path}")
                    selected_files.append(abs_f_path)
            else:
                print(f"[\x1b[0;33m!\x1b[0m] 工作目录 '{work_dir}' 中未找到 Main.java 或其他 .java 文件。请重新输入。")
                continue 
        
        elif os.path.isdir(paths_input_str): # 输入是目录
            print(f"[\x1b[0;36m!\x1b[0m] 扫描目录 '{paths_input_str}' 中的 .java 文件...")
            dir_path = os.path.abspath(paths_input_str) # 使用绝对路径
            found_in_dir = False
            for item in os.listdir(dir_path):
                if item.lower().endswith(".java"):
                    full_path = os.path.join(dir_path, item)
                    if os.path.isfile(full_path):
                        selected_files.append(full_path)
                        found_in_dir = True
            if not found_in_dir:
                print(f"[\x1b[0;33m!\x1b[0m] 在目录 '{dir_path}' 中未找到 .java 文件。请重新输入。")
                continue 
        
        else: # 输入是逗号分隔的文件列表
            potential_paths_str = [p.strip() for p in paths_input_str.split(',')]
            temp_selected_files = []
            all_input_items_resolved = True # 标志以跟踪列表中的所有 p_str 是否都已解析

            for p_str_input_item in potential_paths_str:
                if not p_str_input_item: # 跳过空字符串（例如，如果用户输入 "file1,,file2"）
                    continue

                resolved_for_item = False
                
                # 要尝试的文件名候选列表
                filename_candidates_to_try = [p_str_input_item]
                if not p_str_input_item.lower().endswith(".java"):
                    filename_candidates_to_try.append(p_str_input_item + ".java")

                for filename_candidate in filename_candidates_to_try:
                    path_to_check = filename_candidate
                    if not os.path.isabs(filename_candidate):
                        path_to_check = os.path.join(work_dir, filename_candidate)
                    
                    abs_path_to_check = os.path.abspath(path_to_check)

                    if os.path.isfile(abs_path_to_check) and abs_path_to_check.lower().endswith(".java"):
                        temp_selected_files.append(abs_path_to_check)
                        resolved_for_item = True
                        break # 找到了此 p_str_input_item 的有效文件
                
                if not resolved_for_item:
                    print(f"[\x1b[0;31mx\x1b[0m] 输入项 '{p_str_input_item}' 无法解析为有效的 .java 文件。")
                    all_input_items_resolved = False
                    break # 如果一项无效，则停止处理此列表
            
            if not all_input_items_resolved:
                 print("[\x1b[0;31mx\x1b[0m] 输入的列表中包含无法解析的文件。请重新输入。")
                 continue
            selected_files = temp_selected_files

        if selected_files:
            # 删除重复项同时保留顺序
            selected_files = list(dict.fromkeys(selected_files))
            print(f"[\x1b[0;32m+\x1b[0m] 已选择文件:")
            for f_path in selected_files:
                print(f"  - {f_path}")
            return selected_files
        elif not paths_input_str: # 如果是空输入且未找到文件，则已在上面处理并 continue
            pass
        else: # 如果输入非空但未选择任何文件 (例如，无效的逗号分隔列表或空目录)
            print(f"[\x1b[0;33m!\x1b[0m] 未选择任何有效的 .java 文件。请重新输入。")
            # 循环将继续


def handle_submission(requester, problem, course_id, homework_id):
    """处理Java文件的选择和提交。支持多个Java文件。"""
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

    selected_file_paths = get_java_file_paths(WORK_DIRECTORY)
    if not selected_file_paths:
        print("[\x1b[0;33m!\x1b[0m] 未选择文件，提交取消")
        return False

    # 读取当前文件内容并计算哈希值
    from utils.file_handlers import read_java_file
    current_files_content_hashes = {}
    for file_path in selected_file_paths:
        content = read_java_file(file_path)
        if not content:
            print(f"[\x1b[0;31mx\x1b[0m] 无法读取文件内容: {file_path}，提交取消")
            return False
        
        file_hash = get_file_hash(content=content)
        if not file_hash:
            print(f"[\x1b[0;31mx\x1b[0m] 无法计算文件哈希值: {file_path}，提交取消")
            return False
        
        filename_key = os.path.basename(file_path)  # 使用带扩展名的文件名作为键
        current_files_content_hashes[filename_key] = file_hash

    # 查找上一次提交记录中的代码哈希
    last_submission_files_hashes = {}
    last_submission_time = None
    last_record_id = None

    if 'submission_records' in problem and problem['submission_records'] and len(problem['submission_records']) > 0:
        latest_record = problem['submission_records'][0]
        if 'code' in latest_record and latest_record['code']: 
            # 假设 API 返回的 code 字典的键也是带扩展名的文件名
            for filename_key_from_api, code_content in latest_record['code'].items():
                last_code_hash = get_file_hash(content=code_content)
                if last_code_hash:
                    last_submission_files_hashes[filename_key_from_api] = last_code_hash
            
            if last_submission_files_hashes:
                last_submission_time = latest_record.get('submissionTime', 'Unknown')
                last_record_id = latest_record.get('recordId', 'Unknown')

    # 比较当前文件哈希和上次提交的文件哈希
    # 仅当文件名集合和每个文件的哈希都相同时才认为是重复提交
    if current_files_content_hashes and last_submission_files_hashes:
        # 检查文件名集合是否相同 (键现在是带扩展名的)
        if sorted(current_files_content_hashes.keys()) == sorted(last_submission_files_hashes.keys()):
            all_hashes_match = True
            for filename_key, current_hash in current_files_content_hashes.items():  # filename_key 是带扩展名的
                if last_submission_files_hashes.get(filename_key) != current_hash:  # 使用相同的键格式进行比较
                    all_hashes_match = False
                    break
            
            if all_hashes_match:
                print(f"\n[\x1b[0;31m!\x1b[0m] 检测到提交的文件内容与上一次提交完全相同。")
                print(f"上次提交时间: {last_submission_time}")
                print(f"上次提交ID: {last_record_id}")
                print(f"当前提交文件: {', '.join(os.path.basename(f) for f in selected_file_paths)}")
                print(f"[\x1b[0;31mx\x1b[0m] 提交已取消。请在修改后保存文件。")
                return False

    # 确认提交
    print(f"\n准备提交:")
    print(f"- 题目: {problem['title'] if 'title' in problem else problem['problemName']}")
    print(f"- 文件: {', '.join(os.path.basename(f) for f in selected_file_paths)}") # 显示所有选定文件的基本名称
    confirm = input("确认提交? (y/n，默认y): ").strip().lower() or 'y'
    if confirm != 'y':
        print("[\x1b[0;33m!\x1b[0m] 已取消提交")
        return False

    # 提交解答
    result = requester.submit_homework(
        homework_id,
        problem['problemId'],
        course_id,
        selected_file_paths # 传递文件路径列表
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
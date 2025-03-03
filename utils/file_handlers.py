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

def read_java_file(file_path):
    """读取Java文件内容。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"[\x1b[0;31mx\x1b[0m] 读取文件错误: {e}")
        return None
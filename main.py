from services import OJRequester, handle_login, fetch_and_process_homeworks, fetch_and_process_problems
from ui import display_courses, display_homeworks, display_problems_list, select_course, select_homework, interact_with_problems

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 主函数
def main():
    # 创建一个OJ请求实例
    requester = OJRequester()

    # 处理登录
    if not handle_login(requester):
        return  # 如果登录失败，退出程序

    # 获取并显示课程列表
    courses = display_courses(requester)
    if not courses:
        return  # 如果无法获取课程列表，退出程序

    # 选择课程
    selected_course = select_course(courses, auto_select_first=True)
    if not selected_course:
        return  # 如果无法选择课程，退出程序

    while True:
        # 获取作业列表并处理
        enriched_homeworks = fetch_and_process_homeworks(requester, selected_course)
        if not enriched_homeworks:
            return  # 如果无法获取作业列表，退出程序

        # 显示作业列表
        if not display_homeworks(enriched_homeworks):
            return  # 如果无法显示作业列表，退出程序

        # 用户选择作业
        selected_homework = select_homework(enriched_homeworks)
        if not selected_homework:
            return  # 如果用户没有选择有效的作业，退出程序

        # 获取问题列表并处理，包括获取提交记录
        enriched_problems = fetch_and_process_problems(requester, selected_homework, selected_course)
        if not enriched_problems:
            return  # 如果无法获取问题列表，退出程序

        # 处理与问题的交互（查看详情和提交作业）
        if interact_with_problems(enriched_problems, selected_course, selected_homework, requester):
            return  # 正常退出
        # 如果返回False，则继续外层循环，即返回到作业列表

if __name__ == "__main__":
    main()
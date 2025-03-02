"""UI模块，提供格式化显示与交互功能"""

from .display import display_courses, display_homeworks, display_problems_list, display_problems_info
from .interaction import select_course, select_homework

# 定义当使用 from ui import * 时导入的内容
__all__ = [
    'display_courses', 'display_homeworks', 'display_problems_info',
    'select_course', 'select_homework', 'display_problems_list'
]
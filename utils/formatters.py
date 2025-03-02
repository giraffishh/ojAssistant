def records_status_color(result_state):
    if result_state == 'AC':
        status = "AC"
        status_color = "\x1b[0;32m"  # 绿色
    elif result_state == 'WA':
        status = "WA"
        status_color = "\x1b[0;31m"  # 红色
    elif result_state == 'RE':
        status = "RE"
        status_color = "\x1b[0;35m"  # 紫色
    elif result_state == 'CE':
        status = "CE"
        status_color = "\x1b[0;33m"  # 黄红色
    elif result_state == 'TLE':
        status = "TLE"
        status_color = "\x1b[0;91m"  # 橙红色
    elif result_state == 'MLE':
        status = "MLE"
        status_color = "\x1b[0;91m"  # 橙红色
    else:
        status = result_state
        status_color = ''
    return status, status_color
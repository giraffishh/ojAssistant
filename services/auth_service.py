import config

def handle_login(requester):
    """处理登录流程，尝试使用本地cookies或执行CAS登录"""
    # 尝试先加载cookies
    login_successful = False
    if requester.load_cookies():
        # 验证cookies是否仍然有效
        if requester.check_cookies_status():
            login_successful = True
            print("[\x1b[0;32m+\x1b[0m] 使用本地cookies登录成功")

    # 如果cookies无效或未找到，执行新的登录
    if not login_successful:

        username = config.USERNAME
        password = config.PASSWORD

        if requester.cas_login(username, password):
            print("[\x1b[0;32m+\x1b[0m] CAS 登录成功")
            # 保存新的cookies
            requester.save_cookies()
            return True
        else:
            print("[\x1b[0;31mx\x1b[0m] CAS 登录失败")
            return False

    return login_successful
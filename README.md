# OjAssistant
🍀SustechJcoder平台助手

### ✨ 主要功能

**Jcoder的CLI客户端**
* 获取作业内容及相关统计数据、提交历史等内容
* 便捷上传作业到Jcoder

**TodoList:**
* 获取题目对应的Junit单元测试模拟OJ进行代码测试

### 📌 项目结构
```
ojAssistant/
├── main.py                 # 主入口点
├── services/               # 服务层
│   ├── __init__.py
│   ├── auth_service.py     # 认证相关服务
│   ├── data_service.py     # 数据获取服务
│   └── requester.py        # API通信服务
├── ui/
│   ├── __init__.py
│   ├── display.py          # 显示功能
│   ├── submission.py       # 上传作业功能
│   └── interaction.py      # 用户交互功能

├── utils/
│   ├── __init__.py
│   ├── formatters.py       # 格式化相关函数
│   └── file_handlers.py    # 文件操作函数
└── config.py               # 配置信息
```

**请合理地正确使用脚本，用于不正当用途[（如暴力刷答案](https://github.com/JCoder-Pro/FeedBack/issues/6)或[接入AI生成作业答案自动完成作业）](https://api-docs.deepseek.com/zh-cn/)等后果自负**
***
### 🎨 开始使用
需要在`config.py`中添加你的CAS账号和密码用于登录OJ

项目依赖`Python`和`requests`库
```bash
pip install requests
```
在你工作的IDE中新建一个终端
```bash
cd ./ojAssistant  # 切换到脚本所在目录
python main.py
```

>更多相关设置配置见`config.py`

***

[Jcoder项目地址](https://github.com/liuxukun2000/JCoder)

Jcoder裁判系统的Java环境：
* Java version: 11
* Java(Junit) version: 17.0.4
* Junit version: 5

欢迎提Issus和PullRequests来帮助大家更方便地提交作业

# OjAssistant
🍀SustechJcoder平台助手 v1.2.1

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

### ✨ 主要功能

**Jcoder的CLI客户端**
* 获取作业内容及相关统计数据、提交历史等内容，下载题目内容到本地
* 便捷上传作业到Jcoder
* 获取题目对应的经检验的Junit单元测试模拟OJ进行代码测试

> 欢迎大家贡献出完整的测试用例，帮助大家更好地完成作业

### 🔧 开始使用

**一条命令完成脚本的安装/更新与配置**
```cmd
powershell -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.githubusercontent.com/giraffishh/ojAssistant/main/setup.ps1'))"
```

然后在Intellij中新建的终端中只需输入`oja`即可启动脚本

>更多相关设置配置见`config.py`
> Intellij中Junit依赖安装参考<https://www.jetbrains.com/help/idea/junit.html#intellij>中的`add dependencies`部分


**问题排除**

如果出现访问超时，可以替换成以下命令
```cmd
powershell -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://raw.gitmirror.com/giraffishh/ojAssistant/main/setup.ps1'))"
```

如果PowerShell的策略过于严格不允许脚本运行，请**以管理员身份运行**PowerShell

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 🎨相关设置

| 设置选项                 | 释义                                   |
|----------------------| -------------------------------------- |
| COOKIES_FILE         | 临时登陆凭证存放路径                   |
| WORK_DIRECTORY       | 你的Java作业如Main.java所在路径        |
| AUTO_SELECT_COURSE   | 是否自动进入课程界面                   |
| AUTO_SELECT_HOMEWORK | 是否自动进入作业界面                   |
| MAX_RECORDS_TO_SHOW  | 在作业详情页显示的最大历史提交记录数量 |



***

[Jcoder项目地址](https://github.com/liuxukun2000/JCoder)

Jcoder裁判系统的Java环境：
* Java version: 11
* Java(Junit) version: 17.0.4
* Junit version: 5

欢迎提Issus和PullRequests来帮助大家更方便地提交作业

### ✏️部分功能截图

**课程和作业列表**
***
![课程和作业列表](https://s1.imagehub.cc/images/2025/03/04/ca392616ad66b78bb92fed34fbf1cc2f.png)

**作业中题目列表**
***
![作业中题目列表](https://s1.imagehub.cc/images/2025/03/04/cd8879c71c09ce9711243581f18fb3b5.png)

**题目详情信息**
***
![题目详情信息](https://s1.imagehub.cc/images/2025/03/04/09ace8fea5e148a104719aaa7c22c7d5.png)

**下载题目内容到本地**
***
![下载题目内容到本地](https://s1.imagehub.cc/images/2025/03/04/55afbf82feae457d2bee1bb0ff205d2d.png)

**防止重复提交**
***
![防止重复提交](https://s1.imagehub.cc/images/2025/03/04/a8c3ef9599adc2d04a8d5aafa89c4ddc.png)

**提交作业获取测试结果**
***
![提交作业获取测试结果](https://s1.imagehub.cc/images/2025/03/04/917244e8b7a7966e0843cc168e4a0074.png)

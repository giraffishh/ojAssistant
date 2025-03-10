# OjAssistant
🍀SustechJcoder平台助手 v1.0.0

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

> Intellij中Junit依赖安装参考<https://www.jetbrains.com/help/idea/junit.html#intellij>

> 欢迎大家贡献出完整的测试用例，帮助大家更好地完成作业

### 🎨 开始使用
需要在`config.py`中添加你的CAS账号和密码用于登录OJ，并修改WORK_DIRECTORY为Java作业所在目录

项目只依赖`Python`和`requests`库
```bash
pip install requests
```
在你工作的IDE中新建一个终端
```bash
cd ./ojAssistant  # 切换到脚本所在目录
python main.py  #启动脚本
```
想要更加便捷地使用可以在PowerShell`$PROFILE`中添加函数
```
function oja {
	python "填入存放脚本主函数的绝对路径如C:\\ojAssistant\main.py"
}
```
文件保存为`Microsoft.PowerShell_profile.ps1`

放在以下路径中`C:\Users\你的用户名\Documents\PowerShell\Microsoft.PowerShell_profile.ps1`

然后刷新`$PROFILE`并重启终端
```bash
. $PROFILE
```

然后在终端中只需输入`oja`即可启动脚本

>更多相关设置配置见`config.py`

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

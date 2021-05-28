# SHU-course-helper
我就是最强捡漏王
### 安装依赖
```shell
pip install -r requirements.txt
```
### 运行
格式
```shell
py CourseHelper.py [学号] [密码] [学期季节]
```
例如
```shell
py CourseHelper.py 19120000 Psswrd123 春
```
### 目前实现的功能
- 导出
  - 个人信息
  - 课程信息
  - 课程表
  - 选课排名
  - csv 和 json 格式可选
- 抢课
  - 抢课逻辑：鉴于频繁发送选课请求容易被封禁，脚本采用了“重复查询——出现余位——选课”的逻辑，避免封禁


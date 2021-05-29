# SHU-course-helper
我就是最强捡漏王
### 安装依赖
```shell
pip install -r requirements.txt
```

### 输入个人信息
打开 `information.json`
```json
{
    "self_info": {
        "stu_id": "",       // 学号
        "password": "",     // 密码
        "term_season": ""   // 学期对应的季节，如 “秋”
    },
    "course_info": [
      // 若要抢课，以列表形式给出课程号和教师号
        [
            "",   // 课程号
            ""    // 教师号
        ],
        // 若有多门，继续添加列表即可
        [
            "",
            ""
        ]
    ]
}
```
### 运行
```shell
py main.py
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


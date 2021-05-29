from CourseHelper import CourseHelper
import json


with open(r'infomation.json') as file_obj:
    info = json.load(file_obj)
# 配置例
STU_ID = info['self_info']['stu_id']  # 学号
PASSWORD = info['self_info']['password']  # 密码
TERM_SEASON = info['self_info']['term_season']  # 学期季节
COURSE_INFO = info['course_info']  # 抢课表

xk = CourseHelper(STU_ID, PASSWORD, TERM_SEASON, path='data')

msg = """
1. 获取选课排名
2. 获取个人信息
3. 获取课程信息
4. 获取课程表
5. 抢课 
6. 退出
"""

while True:
    print(msg)
    choice = input('选择需要进行的操作: ')
    if choice == '1':
        xk.get_rank_list(save_type='csv')  # 获取选课排名
    elif choice == '2':
        xk.get_stu_info(save_type='csv')  # 获取个人信息
    elif choice == '3':
        xk.get_course_info(save_type='csv')  # 获取课程信息
    elif choice == '4':
        xk.get_course_table(save_type='csv')  # 获取课程表
    elif choice == '5':
        xk.grab_course_thread(COURSE_INFO)
    elif choice == '6':
        break
    else:
        print('?')

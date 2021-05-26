
import os
import re
import time
import sys
import requests
from lxml import etree
import pandas as pd
from encrypt import encrypt
from Logger import logger
import threading


class CourseHelper:
    def __init__(self, stu_id: str, password: str, term_season: str, path: str = ''):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36"
        }
        self.path = os.getcwd() if not path else path
        # 用来保持登录状态的相关属性
        self.login_url = "https://oauth.shu.edu.cn/login/eyJ0aW1lc3RhbXAiOjE2MjE2MDUzMTQ1ODcxMTM5MDMsInJlc3BvbnNlVHlwZSI6ImNvZGUiLCJjbGllbnRJZCI6InlSUUxKZlVzeDMyNmZTZUtOVUN0b29LdyIsInNjb3BlIjoiIiwicmVkaXJlY3RVcmkiOiJodHRwOi8veGsuYXV0b2lzcC5zaHUuZWR1LmNuL3Bhc3Nwb3J0L3JldHVybiIsInN0YXRlIjoiIn0="
        self.term_index_url = 'http://xk.autoisp.shu.edu.cn/Home/TermIndex'
        self.select_url = "http://xk.autoisp.shu.edu.cn/Home/TermSelect"
        self.stu_id = stu_id
        self.password = password
        self.term_season = term_season
        self.pubkey = '''-----BEGIN PUBLIC KEY-----
    MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDl/aCgRl9f/4ON9MewoVnV58OL
    OU2ALBi2FKc5yIsfSpivKxe7A6FitJjHva3WpM7gvVOinMehp6if2UNIkbaN+plW
    f5IwqEVxsNZpeixc4GsbY9dXEk3WtRjwGSyDLySzEESH/kpJVoxO7ijRYqU+2oSR
    wTBNePOk1H+LRQokgQIDAQAB
    -----END PUBLIC KEY-----'''
        self.session = requests.Session()
        # 获取选课信息url
        self.rank_list_url = 'http://xk.autoisp.shu.edu.cn/StudentQuery/QueryEnrollRankList'
        self.course_table_url = 'http://xk.autoisp.shu.edu.cn/StudentQuery/QueryCourseTablePrint'
        self.course_selection_url = 'http://xk.autoisp.shu.edu.cn/CourseSelectionStudent/CourseSelectionSave'
        self.course_search_url = 'http://xk.autoisp.shu.edu.cn/CourseSelectionStudent/QueryCourseCheck'
        # 初始化动作
        self.login()
        self.select_term()

    def login(self):
        """
        登录选课网站
        """
        post_data = {
            "username": self.stu_id,
            "password": encrypt(self.password, self.pubkey),  # 密码经过加密
        }
        logger.info('尝试登录...用户名: {}, 密码: {}, 加密后的密码: {}', self.stu_id, self.password, encrypt(self.password, self.pubkey))
        try:
            response = self.session.post(
                self.login_url, data=post_data, headers=self.headers
            )
        except ConnectionError as e:
            logger.Error('校网波动! {}', e)
        if '学期选择' in response.text:
            logger.info('登陆成功!')
        else:
            logger.error('登陆失败!')
            raise RuntimeError('账号登陆失败!')

    def select_term(self):
        """
        选择学期
        :param term_season: 学期所在季节, 春夏秋冬
        """
        logger.info('选择{}季学期', self.term_season)
        # 解析 termid
        term_index_response = self.session.get(self.term_index_url, headers=self.headers)
        selector = etree.HTML(term_index_response.text)
        term_tag_list = selector.xpath('//form[@method="post"]//tr')
        term_id = ''
        for term_tag in term_tag_list:
            if self.term_season in term_tag.xpath('./td/text()')[0]:
                term_id = term_tag.xpath('./@value')[0]

        if not term_id:
            logger.error('找不到对应学期!')
            raise RuntimeError('找不到对应学期!')
        else:
            # 维持会话
            post_data = {"termid": term_id}
            response = self.session.post(
                self.select_url, data=post_data, headers=self.headers
            )

    def save_to_path(self, df, name='unknown', type='csv'):
        """
        保存信息表
        :param df: 信息表
        :param name: 文件名
        :param type: 文件的保存类型, csv或json
        """
        if not os.path.exists(self.path):
            os.mkdir(self.path)
        if type == 'csv':
            complete_path = self.path + '\\'+name+'.csv'
            df.to_csv(complete_path,
                      index=False,
                      encoding="utf-8-sig")
            logger.info('已保存至 ' + complete_path)
        elif type == 'json':
            complete_path = self.path + '\\'+name+'.json'
            df.to_json(complete_path,
                       orient='records', force_ascii=False)
            logger.info('已保存至 ' + complete_path)
        else:
            logger.warning('文件{}的保存格式不正确!', name)

    def get_rank_list(self, save_type='') -> pd.DataFrame:
        """
        获取选课排名
        :param save_type: 保存格式, 若空则不保存
        :return: 选课排名表
        """
        response = self.session.get(self.rank_list_url, headers=self.headers)
        selector = etree.HTML(response.text)
        course_elements = selector.xpath('//tr[@name="rowclass"]')
        course_list = []
        for course_element in course_elements:
            course_list.append([field.strip() for field in course_element.xpath('./td/text()')])
        # switch to DataFrame
        columns = ['课程号', '课程名', '教师号', '教师名', '容量', '已选人数', '排名']
        df = pd.DataFrame(course_list, columns=columns)
        if save_type:
            logger.info('保存选课排名')
            self.save_to_path(df, name=self.term_season + '季学期 选课排名', type=save_type)
        return df

    def get_stu_info(self, save_type='') -> pd.DataFrame:
        """
        获取个人信息
        :param save_type: 保存格式, 若空则不保存
        :return: 个人信息
        """
        response = self.session.get(self.course_table_url, headers=self.headers)
        selector = etree.HTML(response.text)
        # 获取学生信息
        stu_info_list = [field.strip().strip('：') for field in selector.xpath('//td[@style="color: Blue;"]/text()') if field.strip().strip('：')]
        stu_credit_raw = selector.xpath('//table[@class="tblnoborder"]//tr/td[@colspan="20"]/text()')[0]  # 获取学分
        stu_info_list.append(re.search('Total credit：(\d+\.\d+)', stu_credit_raw).group(1))

        # switch to DataFrame
        stu_info_columns = ['学号', '姓名', '性别', '年级', '学院', '校区', '学分']
        try:
            stu_info_df = pd.DataFrame([stu_info_list], columns=stu_info_columns)
            if save_type:
                logger.info('保存个人信息')
                self.save_to_path(stu_info_df, name=self.term_season + '季学期 个人信息', type=save_type)
            return stu_info_df
        except:
            logger.warning('个人信息保存失败')
            return pd.DataFrame()

    def get_course_info(self, save_type='') -> pd.DataFrame:
        """
        获取课程详细信息
        :param save_type: 保存格式, 若空则不保存
        :return: 课程详细信息
        """
        response = self.session.get(self.course_table_url, headers=self.headers)
        selector = etree.HTML(response.text)

        # 获取课程信息
        try:
            course_info_element = selector.xpath(
                '//table[@class="tblnoborder"]')[0]
        except:
            logger.warning(
                'xpath 获取不到课程信息!将 response.text 打印:{}', response.text)
            return pd.Dataframe()
        course_info_element = selector.xpath('//table[@class="tblnoborder"]')[0]
        course_info_list = []
        for one_piece in course_info_element.xpath('.//tr[@name="rowclass"]'):
            # 记录一门课程的字段信息
            course_info_list.append([field.xpath('./text()')[0].strip() if field.xpath('./text()') else '' for field in one_piece.xpath('./td')])
            # 相当于
            # one_piece_list = []
            # for field in one_piece.xpath('./td'):
            #     if field.xpath('./text()'):
            #         one_piece_list.append(field.xpath('./text()')[0].strip())
            #     else:
            #         one_piece_list.append('')
            # course_info_list.append(one_piece_list)
        # switch to DataFrame
        course_info_columns = ['#', '课程号', '课程名', '学分', '教师号', '教师姓名', '上课时间', '上课地点', '答疑时间', '答疑地点', '校区']

        try:
            course_info_df = pd.DataFrame(course_info_list, columns=course_info_columns)
            if save_type:
                logger.info('保存课程信息')
                self.save_to_path(course_info_df, name=self.term_season + '季学期 课程信息', type=save_type)

            return course_info_df
        except:
            logger.warning('课程信息保存失败')
            return pd.DataFrame()

    def get_course_table(self, save_type='') -> pd.DataFrame:
        """
        获取课程表
        :param save_type: 保存格式, 若空则不保存
        :return: 课程表
        """
        response = self.session.get(self.course_table_url, headers=self.headers)
        selector = etree.HTML(response.text)
        # 获取课程表
        try:
            course_table_element = selector.xpath(
                '//table[@class="tblnoborder"]')[1]
        except:
            logger.warning('xpath 解析课程表失败!')

        course_table_list = []
        for one_piece in course_table_element.xpath('.//tr[@name="rowweek"]'):
            # 记录课程表的一行信息
            course_table_list.append([field.strip().replace('\n', '').replace(' ', '') for field in one_piece.xpath('./td/text()')])
        # switch to DataFrame
        course_table_columns = ['#', '上课时间', '一', '二', '三', '四', '五', '六', '日']

        try:
            course_table_df = pd.DataFrame(course_table_list, columns=course_table_columns)
            if save_type:
                logger.info('保存课程表')
                self.save_to_path(course_table_df, name=self.term_season + '季学期 课程表', type=save_type)
            return course_table_df
        except:
            logger.warning('课程表保存失败')
            return pd.DataFrame()

    def choose_course(self, course_info: list) -> list:
        """
        发送选课请求
        :param course_info: 课程信息, 形如 [['08305008', '1002'], ['08306146', '1002']]
        :return: 选课反馈信息 
        """
        course_id = []
        teacher_id = []
        for course in course_info:
            course_id.append(course[0])
            teacher_id.append(course[1])

        post_data = {
            'cids': course_id,
            'tnos': teacher_id
        }
        response = self.session.post(self.course_selection_url, data=post_data, headers=self.headers)
        if '学生限制登录' in response.text:
            logger.error('账号被限制登录!')
            raise RuntimeError('账号被限制登录!')
        if '选课时间未到' in response.text:
            logger.error('选课时间未到!')
            raise RuntimeError('选课时间未到!')
        selector = etree.HTML(response.text)
        # 判断是否选课成功
        try:
            selection_feedback_element = selector.xpath('//tr')[1:-1]  # 掐头去尾
            feedback_course_info = []
            for course in selection_feedback_element:
                feedback_course_info.append([field.strip() for field in course.xpath('.//td/text()')])
            for feedback_course in feedback_course_info:
                logger.info(feedback_course[1]+' '+feedback_course[3]+' '+feedback_course[4]+' '+feedback_course[2]+' '+feedback_course[-1])  # TODO use logger
            return feedback_course_info
        except:
            logger.error('未知错误, 选课操作失败! 具体返回页面如下: ')
            logger.info(response.text)
            return []

    def is_full(self, course_id: str, teacher_id: str) -> bool:
        """
        判断某课程是否满人
        :param cource_id: 课程号
        :param teacher_id: 教师号
        :return: 是否满人的布尔值
        """
        post_data = {
            "CID": course_id,
            "TeachNo": teacher_id,
            'IsNotFull': 'true',
            "PageIndex": '1',
            "PageSize": '10'
        }
        response = self.session.post(self.course_search_url, data=post_data, headers=self.headers)
        if '未查询到符合条件的数据！' in response.text:
            return False
        else:
            return True

    def grab_course(self, course_id: str, teacher_id: str, interval: float = 0.3):
        """
        抢课
        :param cource_id: 课程号
        :param teacher_id: 教师号
        :param interval: 查询间隔时间
        """
        count = 1
        while True:
            logger.info('课程号 {}, 教师号 {}: 第 {} 次查询', course_id, teacher_id, count)
            count += 1
            if self.is_full(course_id, teacher_id):
                feedback = self.choose_course([[course_id, teacher_id]])
                logger.info('课程人数有空余!尝试选课')
                if '成功' in feedback[0][-1]:
                    logger.info('抢课成功! 终止抢课循环')
                    break
            time.sleep(interval)

    def grab_course_thread(self, course_info: list):
        """
        多线程选课
        :param course_info: 课程信息, 形如 [['08305008', '1002'], ['08306146', '1001']]
        """
        grabbers = []
        for course_piece in course_info:
            grabber = threading.Thread(target=self.grab_course, args=(course_piece[0], course_piece[1],))
            grabbers.append(grabber)
        for grabber in grabbers:
            grabber.start()

    def switch2dict(self, df):
        if not df.empty:
            return df.to_dict(orient='records')
        else:
            return {}


if __name__ == '__main__':
    # 配置例
    STU_ID = sys.argv[1]  # 学号
    PASSWORD = sys.argv[2]  # 密码
    TERM_SEASON = sys.argv[3]  # 学期季节

    xk = CourseHelper(STU_ID, PASSWORD, TERM_SEASON, path='data')

    # 获取信息例
    # xk.get_rank_list(save_type='csv')  # 获取选课排名
    # xk.get_stu_info(save_type='csv')  # 获取个人信息
    # xk.get_course_info(save_type='csv')  # 获取课程信息
    # xk.get_course_table(save_type='csv')  # 获取课程表

    # 手动选课例
    # course_info = [['08305008', '1001'], ['08305008', '1002']]  # 添加想要选的课程
    # xk.choose_course(course_info)  # 发送选课请求

    # 抢课例
    # xk.grab_course('08305008', '1002')  # 添加想要抢的课程, 开始抢课

    # 多门课程抢课例
    # course_info = [['08305008', '1002'], ['08306146', '1001']]
    # xk.grab_course_thread(course_info)

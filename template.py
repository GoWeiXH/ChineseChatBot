"""
    针对机器人的人格信息

    根据输入语句，利用正则表达式匹配问句，

    随机从配置好的答案中输出结果。

    输入语句多模板、输出语句多模板

"""

import xml.etree.ElementTree as et
from random import choice
import re


class Template:
    SELF_TEMP_FILE = 'config/robot_template.xml'

    def __init__(self):
        self.template = self.load_temp_file()
        self.robot_info = self.load_robot_info()
        self.question_count = self.init_count()
        self.temps = self.template.findall('temp')
        self.default_answer = self.get_default('default')
        self.exceed_answer = self.get_default('exceed')

    def init_count(self):
        """相同问题提问次数"""
        return dict().fromkeys(self.robot_info.keys(), 0)

    def load_robot_info(self):
        """加载机器人的人格信息"""
        robot_info_dict = dict()
        robot_info = self.template.find('robot_info')
        for info in robot_info:
            robot_info_dict[info.tag] = info.text
        return robot_info_dict

    def load_temp_file(self):
        """加载模板的 xml 文件"""
        root = et.parse(self.SELF_TEMP_FILE)
        return root

    def get_default(self, item):
        return self.template.find(item)

    def search_answer(self, question):
        """在模板中匹配答案"""
        global match_temp
        match_temp = None
        flag = False
        for temp in self.temps:
            temp_id = temp.attrib.get('id')

            # 根据相同问题已经提问次数返回不同警告
            count = self.question_count.get(temp_id)
            if (count >= 3) and (count < 5):
                self.question_count[temp_id] += 1
                return choice(self.exceed_answer).text
            elif count == 5:
                self.question_count[temp_id] += 1
                return self.template.find('limit//l1').text
            elif count >= 6:
                self.question_count[temp_id] += 1
                return self.template.find('limit//l2').text

            # 搜索匹配的相关答案
            qs = temp.find('question').findall('q')
            for q in qs:
                result = re.search(q.text, question)
                if result:
                    match_temp = temp
                    # 匹配到后更改 标记
                    flag = True
                    self.question_count[temp_id] += 1
                    break
            if flag:
                # 如果已经找打答案则跳出循环
                break

        if match_temp:
            a_s = match_temp.find('answer').findall('a')
            answer = choice(a_s).text
            return answer.format(**self.robot_info)
        else:
            return None


# _q = '介绍一下你'
# template = Template()
# answer = template.get_answer(_q)
# print(answer)

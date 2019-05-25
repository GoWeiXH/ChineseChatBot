"""
    模板匹配模块

    根据输入语句，计算与模板的相似度：

        1. 计算与问句的相似度
        2. 计算与答案的相关度

    输出相似度最高的答案。

    输入语句多模板、输出语句多模板

"""

import xml.etree.ElementTree as et
from random import choice
import re


class Template:
    SELF_TEMP_FILE = 'QA_temp/robot_template.xml'

    def __init__(self):
        self.template = self.load_temp_file()
        self.robot_info = self.load_robot_info()
        self.question_count = self.init_count()
        self.temps = self.template.findall('temp')
        self.default_answer = self.get_default('default')
        self.exceed_answer = self.get_default('exceed')

    def init_count(self):
        return dict().fromkeys(self.robot_info.keys(), 0)

    def load_robot_info(self):
        robot_info_dict = dict()
        robot_info = self.template.find('robot_info')
        for info in robot_info:
            robot_info_dict[info.tag] = info.text
        return robot_info_dict

    def load_temp_file(self):
        root = et.parse(self.SELF_TEMP_FILE)
        return root

    def get_default(self, item):
        return self.template.find(item)

    def get_answer(self, question):
        global match_temp
        match_temp = None
        flag = False
        for temp in self.temps:
            temp_id = temp.attrib.get('id')

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

            qs = temp.find('question').findall('q')
            for q in qs:
                result = re.search(q.text, question)
                if result:
                    match_temp = temp
                    flag = True
                    self.question_count[temp_id] += 1
                    break
            if flag:
                break

        if match_temp:
            a_s = match_temp.find('answer').findall('a')
            answer = choice(a_s).text
        else:
            answer = choice(self.default_answer).text

        return answer.format(**self.robot_info)


# _q = '介绍一下你的爱好'
# template = Template()
# answer = template.get_answer(_q)
# print(answer)

"""
    层级过滤器，将输入语句先后通过模板、搜索、生成、互联网等模块，

    如果搜索到答案，则返回不再继续执行

    如果没有获得答案，则交给下一层处理

    如果最终没有获得相关答案则返回默认答案
"""

from xml.etree import ElementTree as et
from random import choice
from urllib.error import HTTPError

from internet import SogouSpider
from template import Template
from search import Search


class LayerFilter:

    DEFAULT_PATH = 'config/default_answer.xml'

    SOGOU_SWITCH = False

    def __init__(self):
        self.default_answers = self.get_default()
        self.template = Template()
        self.search = Search()
        self.sogou = SogouSpider()

    def get_default(self):
        """加载默认答案"""
        answers = list()
        root = et.parse(self.DEFAULT_PATH)
        a_s = root.find('default').findall('a')
        for a in a_s:
            answers.append(a.text)
        return answers

    def get_answer(self, question):
        """获取答案"""

        # 互联网模式是否开启
        if question == 'Robot-单机模式':
            self.SOGOU_SWITCH = False
            return '联网模式关闭'

        if question == 'Robot-联网模式':
            self.SOGOU_SWITCH = True
            return '联网模式启动'

        # 先经过模板层处理
        answer = self.template.search_answer(question)
        if answer:
            return answer

        # 经过搜索层处理
        answer = self.search.search_answer(question)
        if answer:
            return answer

        # 如果联网模式开启，则进入联网搜索模块处理
        if self.SOGOU_SWITCH:
            try:
                answer = self.sogou.get_answer(question)
            except HTTPError as e:
                print(e)
                answer = input()
            if answer:
                return answer

        # 如果最终没有答案，则随机选择默认答案输出
        return choice(self.default_answers)

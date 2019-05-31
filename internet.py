"""
利用 Sogou 问问的接口获取问答语料库
"""

from urllib.parse import quote_plus
from urllib.request import Request
from urllib import request
from random import choice
import re

from bs4 import BeautifulSoup


class SogouSpider:

    DOMAIN = 'https://www.sogou.com/'

    # 搜索问题的链接
    QUERY_URL = 'https://www.sogou.com/sogou?query={0}&ie=utf8&insite=wenwen.sogou.com'

    # 获取相似问题的链接
    EXTEND_URL = 'https://wenwenfeedapi.sogou.com/sgapi/web/related_search_new?key={0}'

    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) "
                             "AppleWebKit/600.5.17 (KHTML, like Gecko) "
                             "Version/8.0.5 Safari/600.5.17"}

    def get_html(self, url):
        """
        不使用代理 ip
        """
        req = Request(url, headers=self.HEADERS)
        response = request.urlopen(req, timeout=3)
        html = response.read().decode('utf8')  # 读取后数据为 bytes，需用 utf-8 进行解码
        html = BeautifulSoup(html, 'html.parser')
        return html

    def collect_answers(self, query):
        """
        从搜索结果页面中收集答案
        """
        query = quote_plus(query)
        query_url = self.QUERY_URL.format(query)
        html = self.get_html(query_url)
        answer_list = html.select('.vrwrap')
        return answer_list

    def extract_skip_url(self, url):
        """
        从跳转页面中提取出目标 url
        """
        html = self.get_html(url)
        skip_url = html.select('meta')[1].attrs.get('content')
        skip_url = re.findall("URL=\\\'(.+)", skip_url)[0][:-1]
        return skip_url

    def extract_answer(self, answer_list):
        """
        提取问题的最佳答案
        将问题内容、标签、答案内容整合成一条数据
        """

        new_list = list()
        for answer in answer_list:

            a = answer.select_one('.vrTitle a')

            # 获取跳转链接
            link = self.DOMAIN + a.attrs.get('href')
            url = self.extract_skip_url(link)
            html = self.get_html(url)

            # 获取问题标题与标签
            section = html.select('.main .section')[0]
            title = re.sub(r'[\?？]+', '', section.select_one('#question_title span').text)
            tag = section.select_one('.tags a').text

            # 获取答案相关
            section = html.select('.main .section')[1]
            content = section.select_one('#bestAnswers .replay-info pre')
            if content is None:
                content = section.select_one('.replay-section.answer_item .replay-info pre')
            content = content.text
            content = re.sub(r'\s+', '', content)  # 去除空格字符，包括：\r \n \r\n \t 空格

            # 构建成一条答案，并添加至答案结果列表
            answer = {'title': title, 'tag': tag, 'content': content}
            new_list.append(answer)
        return choice(new_list[:2])

    def get_answer(self, query):
        answers = self.collect_answers(query)
        answer = self.extract_answer(answers).get('content')
        answer = answer.split('。')[0].split('！')[0]
        answer = re.sub(r'["“”]', '', answer) + '。'
        return answer

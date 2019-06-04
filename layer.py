import xml.etree.ElementTree as et
from urllib.parse import quote_plus
from urllib.request import Request
from urllib import request
from collections import Counter
from random import choice
import itertools
import logging
import json
import os
import re

from bs4 import BeautifulSoup
import numpy as np
import jieba

from kg_index.medical.search_key_word import *
from config.path_config import *
from factory import WordWorker


class BaseLayer:
    """基础父类"""

    def __init__(self, log=True):
        self.logger = logging.getLogger()
        if not log:
            self.close_log()

    def close_log(self):
        self.logger.setLevel(logging.ERROR)

    def print_log(self, msg):
        self.logger.warning(msg)

    def search_answer(self, question):
        ...


class Template(BaseLayer):
    """
        针对机器人的人格信息，根据输入语句，利用正则表达式匹配问句，

        输出配置好的答案。

    """

    def __init__(self):
        super(Template, self).__init__()
        self.template = self.load_temp_file()
        self.robot_info = self.load_robot_info()
        self.temps = self.template.findall('temp')
        self.default_answer = self.get_default('default')
        self.exceed_answer = self.get_default('exceed')
        self.print_log('Template layer is ready.')

    def load_robot_info(self):
        """加载机器人的人格信息"""
        robot_info_dict = dict()
        robot_info = self.template.find('robot_info')
        for info in robot_info:
            robot_info_dict[info.tag] = info.text
        return robot_info_dict

    @staticmethod
    def load_temp_file():
        """加载模板的 xml 文件"""
        root = et.parse(SELF_TEMP_FILE)
        return root

    def get_default(self, item):
        """获取默认回复答案"""
        return self.template.find(item)

    def search_answer(self, question):
        """在模板中匹配答案"""
        global match_temp
        match_temp = None
        flag = False
        for temp in self.temps:

            # 搜索匹配的相关答案
            qs = temp.find('question').findall('q')
            for q in qs:
                result = re.search(q.text, question)
                if result:
                    match_temp = temp
                    # 匹配到后更改 标记
                    flag = True
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


class CorpusSearch(BaseLayer):
    THRESHOLD = 0.7

    def __init__(self):
        super(CorpusSearch, self).__init__()
        ww = WordWorker()
        self.inverse = ww.inverse
        self.question_list = ww.question_list
        self.answer_list = ww.answer_list
        self.print_log('CorpusSearch layer is ready.')

    @staticmethod
    def cosine_sim(a, b):
        """计算两个句子的 余弦相似度"""
        a_words = Counter(a)
        b_words = Counter(b)

        # 建立两个句子的 字典 vocabulary
        all_words = b_words.copy()
        all_words.update(a_words - b_words)
        all_words = set(all_words)

        # 生成句子向量
        a_vec, b_vec = list(), list()
        for w in all_words:
            a_vec.append(a_words.get(w, 0))
            b_vec.append(b_words.get(w, 0))

        # 计算余弦相似度值
        a_vec = np.array(a_vec)
        b_vec = np.array(b_vec)
        a__ = np.sqrt(np.sum(np.square(a_vec)))
        b__ = np.sqrt(np.sum(np.square(b_vec)))
        cos_sim = np.dot(a_vec, b_vec) / (a__ * b__)

        return round(cos_sim, 4)

    def search_answer(self, question):
        # 分词后，各词都出现在了哪些文档中
        search_list = list()
        q_words = jieba.lcut(question)
        for q_word in q_words:
            index = self.inverse.get(q_word, list())
            search_list += index

        if not search_list:
            return None

        # 统计包含问句中词汇次数最多的 3 个文档
        count_list = Counter(search_list)
        count_list = count_list.most_common(3)
        result_sim = list()
        for i, _ in count_list:
            q = self.question_list[i]
            sim = self.cosine_sim(q_words, q)
            result_sim.append((i, sim))

        # 根据两两的余弦相似度选出最相似的问句
        result = max(result_sim, key=lambda x: x[1])

        # 如果相似度低于阈值，则返回 None
        if result[1] > self.THRESHOLD:
            answer = ''.join(self.answer_list[result[0]])
            return answer
        else:
            return None


class MedicalSearch(BaseLayer):
    """
    医疗图形数据库
    """

    def __init__(self, data_path, entities, main_index):
        super(MedicalSearch, self).__init__()
        self.__make_dirs()
        self.data_path = data_path
        self.entities = entities
        self.main_index = main_index
        self.entity_dict = self.load_node()
        self.relation_dict = self.load_edge()
        self.data_index = self.load_index_data()
        self.region_key_words = key_word_dict
        self.print_log('MedicalSearch layer is ready.')

    @staticmethod
    def __make_dirs():
        """创建存储路径"""
        if not os.path.exists(MEDICAL_ENTITY_BASE_PATH):
            os.makedirs(MEDICAL_ENTITY_BASE_PATH)
        if not os.path.exists(MEDICAL_RELATION_INDEX_PATH):
            os.makedirs(MEDICAL_RELATION_INDEX_PATH)

    @staticmethod
    def __read(file_path, encoding='utf-8'):
        """读取 json 数据"""
        with open(file_path, 'r', encoding=encoding) as file:
            if file_path.endswith('.json'):
                data = json.load(file)
            else:
                file = os.path.split(file_path)[-1]
                raise TypeError(f"The type of file must be json, but got: '{file}'")
            return data

    def build_node(self, file_path, entities):
        """
        构建实体的名称集合作为 key，并按序号作为 value
        """

        self.print_log('Start building Entity_Node...')

        # 建立各实体的字典索引
        data_list = self.__read(file_path)
        entity_dict = dict.fromkeys(entities)
        for k in entity_dict.keys():
            entity_dict[k] = set()

        # 获取各实体的名称集合
        for k in entities:
            for data in data_list.values():
                d = data.get(k)
                if isinstance(d, list):
                    entity_dict[k] |= set(d)
                elif isinstance(d, str):
                    entity_dict[k].add(d)
                elif not d:
                    continue
                else:
                    raise TypeError(f'Entity type must be str or list, bu got: {type(d)}')

        # 生成实体及其索引，并分别保存到相应文件
        for entity in entity_dict.keys():
            entity_path = f'{MEDICAL_ENTITY_BASE_PATH}{entity}.json'
            with open(entity_path, 'w', encoding='utf-8') as file:
                keys = list(entity_dict[entity])
                data = dict(zip(keys, range(len(keys))))
                json.dump(data, file, ensure_ascii=False)
                self.print_log(f'\tnode_{entity}.json')

            entity_inv_path = f'{MEDICAL_ENTITY_BASE_PATH}{entity}_inv.json'
            with open(entity_inv_path, 'w', encoding='utf-8') as file:
                inv_data = dict(zip(data.values(), data.keys()))
                json.dump(inv_data, file, ensure_ascii=False)
                self.print_log(f'\t{entity}_inv.json')

        self.print_log('Entity_Node built successfully.')

    def build_edge(self, file_path, entities):
        """
        利用倒排索引构建关系，作为图的边

        (将实体之间的倒排索引在逻辑上视为有向图的边)

        """

        self.print_log('Start building Relation_Edge...')

        # 读取数据
        with open(file_path, 'r', encoding='utf-8') as file:
            data_list = json.load(file)

        # 生成需要构建关系的实体的排列
        for e1, e2 in itertools.permutations(entities, 2):

            # e1 代表倒排索引中的 key
            file_path = f'{MEDICAL_ENTITY_BASE_PATH}{e1}.json'
            with open(file_path, 'r', encoding='utf-8') as file:
                keys = json.load(file)
                for k in keys.keys():
                    keys[k] = list()

            # e2 代表倒排索引中的 value
            file_path = f'{MEDICAL_ENTITY_BASE_PATH}{e2}.json'
            with open(file_path, 'r', encoding='utf-8') as file:
                values = json.load(file)

            # 初始化倒排索引字典
            inverse_dict = dict.fromkeys(keys)
            for k in inverse_dict.keys():
                inverse_dict[k] = list()

            # 对于每条数据，利用倒排索引记录 e1 与 e2 实体名称的共现情况
            # 即获得：(其中, {a,b,c}∈e1，{1,2,3}∈e2)
            #       {a: [1, 2],
            #        b: [2],
            #        c: [1, 3]}
            for data in data_list.values():
                key = data[e1]
                value = data[e2]

                # 如果 e1,e2 的取值类型为 str，则直接从实体索引中寻找对应 value
                # 如果取值类型为 list，则展开遍历，再从实体索引中寻找对应 value
                if isinstance(key, str):
                    if isinstance(value, list):
                        for v in value:
                            index = values[v]
                            inverse_dict[key].append(index)
                    elif isinstance(value, str):
                        index = values[value]
                        inverse_dict[key].append(index)
                elif isinstance(key, list):
                    for k in key:
                        if isinstance(value, list):
                            for v in value:
                                index = values[v]
                                inverse_dict[k].append(index)
                        elif isinstance(value, str):
                            index = values[value]
                            inverse_dict[k].append(index)

            # 并保存倒排索引为关系文件
            relation_path = f'{MEDICAL_RELATION_INDEX_PATH}{e1}_{e2}.json'
            with open(relation_path, 'w', encoding='utf-8') as file:
                json.dump(inverse_dict, file, ensure_ascii=False)
                self.print_log(f'\t{e1}_{e2}.json')

        self.print_log('Relationship built successfully.')

    def build_graph(self):
        """
        以实体建立为结点，以关系建立为边
        """
        self.print_log('------')
        self.build_node(self.data_path, self.entities)
        self.print_log('------')
        self.build_edge(self.data_path, self.entities)

    @staticmethod
    def load_node():
        """加载所有结点，从保存实体的文件中读取"""
        entity_dict = dict()
        entity_file_list = os.listdir(MEDICAL_ENTITY_BASE_PATH)
        for entity in entity_file_list:
            entity_name = entity.split('.')[0]
            file_path = MEDICAL_ENTITY_BASE_PATH + entity
            with open(file_path, 'r', encoding='utf-8') as file:
                entity_dict[entity_name] = json.load(file)
        return entity_dict

    @staticmethod
    def load_edge():
        """加载所有边，从保存关系的文件中读取"""
        relation_dict = dict()
        relation_file_list = os.listdir(MEDICAL_RELATION_INDEX_PATH)
        for relation in relation_file_list:
            entity_name = relation.split('.')[0]
            file_path = MEDICAL_RELATION_INDEX_PATH + relation
            with open(file_path, 'r', encoding='utf-8') as file:
                relation_dict[entity_name] = json.load(file)
        return relation_dict

    def load_index_data(self):
        """加载以 main_index 为索引的所有数据"""
        return self.__read(MEDICAL_ORIGIN_INDEX_PATH)

    @staticmethod
    def __unfold_and_select(data, select):
        """
        以组合的方式展开 {key: [a, b]} 形式的数据
        并对数据以 select 进行过滤
        """
        index_entity = set()

        # 一个问题领域，包含多个条件取交集
        for i, s in enumerate(select):
            item_set = set(data[s])
            if i == 0:
                index_entity = item_set
            else:
                index_entity &= item_set

        return index_entity

    def search_by_entity(self, condition):
        """
        根据实体条件进行搜索

        condition = {'name': ['jack', 'tom'],
                     'category': ['A', 'B']}

        """

        index_set = set()
        for i, item in enumerate(condition):
            # 如果已经指定 main_index 则无需搜索
            if item == self.main_index:
                continue
            else:
                # 根据 condition 搜索其对应的 main_index
                rel = self.relation_dict[f'{item}_{self.main_index}']

            index_entity_item = self.__unfold_and_select(rel, condition[item])
            if index_set and index_entity_item:
                index_set &= index_entity_item
            elif not index_set and index_entity_item:
                index_set = index_entity_item
            else:
                continue

        # 将搜索到的 main_index 通过倒排索引获得对应的名称
        result = list()
        k = self.main_index + '_inv'
        main_index_inv = self.entity_dict[k]
        for i in index_set:
            result.append(main_index_inv[str(i)])

        # 如果指定了 main_index 则与搜索结果取交集
        if condition[self.main_index]:
            result = list(set(result) | set(condition[self.main_index]))

        return result

    def parse_question(self, question):
        """解析问句，获取问句所询问的领域（实体），并提取出各领域的搜索值"""

        # 通过领域关键词确定问题所问领域
        region = self.main_index
        for region_name, values in self.region_key_words.items():
            for v in values:
                if v in question:
                    region = region_name

        extract_item = dict.fromkeys(self.entities)
        for k in extract_item:
            extract_item[k] = list()

        # 从实体中确定搜索值
        jieba.load_userdict(MEDICAL_SPECIAL_WORDS_PATH)
        q_words = jieba.lcut(question)
        for entity in self.entities:
            for q_word in q_words:
                if q_word in self.entity_dict[entity]:
                    extract_item[entity].append(q_word)

        return region, extract_item

    def format_answer(self, name, region):
        """格式化答案"""

        # 根据实体名称获取该实体的相关属性、关系
        entity = self.data_index[name]
        name = entity.get(self.main_index)

        # 获取各属性值并处理成字符串
        category = '、'.join(entity.get('category', '无'))
        symptom = '、'.join(entity.get('symptom', '无'))
        acompany = '、'.join(entity.get('acompany', '无'))
        recommand_drug = '、'.join(entity.get('recommand_drug', '无'))
        common_drug = '、'.join(entity.get('common_drug', '无'))
        drug = '、'.join((common_drug, recommand_drug))
        check = '、'.join(entity.get('check', '无'))
        cure_way = '、'.join(entity.get('cure_way', '无'))
        do_eat = '、'.join(entity.get('do_eat', '无'))
        not_eat = '、'.join(entity.get('not_eat', '无'))

        cause = entity.get('cause', '未知')
        prevent = entity.get('prevent', '无')
        easy_get = entity.get('easy_get', '无')
        get_prob = entity.get('get_prob', '无')
        get_way = entity.get('get_way', '无')
        cured_prob = entity.get('cured_prob', '无')
        cure_lasttime = entity.get('cure_lasttime', '无')

        # 根据不同的领域返回不同格式的答案
        if region == self.main_index:
            answer = f'{name}： \n·所属科室：{category} \n·症状表现：{symptom} \n·易患人群：{easy_get} \n·传染途径：{get_way} \n·（可以通过 疾病名称+病因、预防等继续查询）'
        elif region == 'symptom':
            answer = f'{name}的症状：{symptom}等'
        elif region == 'prevent':
            answer = f'{name}的预防方法：{prevent}'
        elif region == 'cause':
            answer = f'{name}的病因：{cause}'
        elif region == 'acompany':
            answer = f'{name}的并发症：{acompany}等'
        elif region == 'eat':
            answer = f'{name}推荐饮食：{do_eat}等；\n 不宜（忌口）: {not_eat}等'
        elif region == 'drug':
            answer = f'{name}的可用药物：{drug}等'
        elif region == 'easy_get':
            answer = f'{easy_get}易患 {name}'
        elif region == 'get_prob':
            answer = f'{name}患病率为：{get_prob}'
        elif region == 'check':
            answer = f'{name}检查方法有：{check}等'
        elif region == 'cure_way':
            answer = f'{name}的治疗方法有：{cure_way}等'
        elif region == 'acompany':
            answer = f'{name}的并发症有：{acompany}等'
        elif region == 'cured_prob':
            answer = f'{name}的治愈率为：{cured_prob}'
        elif region == 'cure_lasttime':
            answer = f'{name}的治疗周期为：{cure_lasttime}'
        else:
            answer = None
        return answer

    def search_answer(self, question):
        """搜索答案"""

        region, extract_item = self.parse_question(question)
        name_result = self.search_by_entity(extract_item)
        if name_result:
            # 如果结果中只包含一个 main_index 则输出其详细信息
            if len(name_result) == 1:
                name = name_result[0]
                answer = self.format_answer(name, region)
            # 如果结果中包含多个，则返回列表，等待输入确定的 main_index
            else:
                name_list = '、'.join(name_result)
                answer = f'根据描述，您可能的疾病为（输入疾病名称可查看其详细信息）：\n{name_list}'
            return answer
        return None


class Generate(BaseLayer):
    """
        生成模型

        利用 DL 模型对输入语句进行预测

            1. Seq2Seq
            2. Bin-Seq2Seq
            3. Seq2Seq + Attention
            4. （可以尝试机器学习方法）

    """


class InterNet(BaseLayer):
    """
    利用 Sogou 问问的接口获取问答语料库
    """

    DOMAIN = 'https://www.sogou.com/'

    # 搜索问题的链接
    QUERY_URL = 'https://www.sogou.com/sogou?query={0}&ie=utf8&insite=wenwen.sogou.com'

    # 获取相似问题的链接
    EXTEND_URL = 'https://wenwenfeedapi.sogou.com/sgapi/web/related_search_new?key={0}'

    HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) "
                             "AppleWebKit/600.5.17 (KHTML, like Gecko) "
                             "Version/8.0.5 Safari/600.5.17"}

    def __init__(self):
        super(InterNet, self).__init__()
        self.print_log('InterNet layer is ready.')

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

    def search_answer(self, query):
        """搜索答案"""

        answers = self.collect_answers(query)
        answer = self.extract_answer(answers).get('content')
        answer = answer.split('。')[0].split('！')[0]
        answer = re.sub(r'["“”]', '', answer) + '。'
        return answer

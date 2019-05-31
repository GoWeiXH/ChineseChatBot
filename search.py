"""
    内容检索

    从语料库中针对问句进行检索

        1. 完全 DL 模型进行检索
        2. 倒排索引 + DL 检索 √
        3. 先利用某方法召回部分结果，再对结果进行检索
        4. 数据库检索
        5. 知识图谱检索

"""

from collections import Counter
import itertools
import logging
import json
import os

import numpy as np
import jieba

from process import WordFactory
from config import *


class Search:

    THRESHOLD = 0.6

    def __init__(self):
        wf = WordFactory()
        self.inverse = wf.inverse
        self.question_list = wf.question_list
        self.answer_list = wf.answer_list

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


class KnowGraph:
    """
    图形数据库
    """

    def __init__(self, data_path, entities, main_index, log=True):
        self.__make_dirs()
        self.logger = logging.getLogger()
        if not log:
            self.close_log()

        self.data_path = data_path
        self.entities = entities
        self.main_index = main_index
        self.entity_dict = self.load_node()
        self.relation_dict = self.load_edge()

    def close_log(self):
        self.logger.setLevel(logging.ERROR)

    def __print_log(self, msg):
        self.logger.warning(msg)

    @staticmethod
    def __make_dirs():
        if not os.path.exists(ENTITY_BASE_PATH):
            os.makedirs(ENTITY_BASE_PATH)
        if not os.path.exists(RELATION_INDEX_PATH):
            os.makedirs(RELATION_INDEX_PATH)

    @staticmethod
    def __read(file_path, encoding='utf-8'):
        with open(file_path, 'r', encoding=encoding) as file:
            if file_path.endswith('.json'):
                data = json.load(file)
            # elif file_path.endswith('.csv'):
            #     data = list(csv.reader(file))
            else:
                file = os.path.split(file_path)[-1]
                raise TypeError(f"The type of file must be json, but got: '{file}'")
            return data

    @staticmethod
    def __change(file_path, encoding='utf-8'):
        with open(file_path, 'r', encoding=encoding) as file:
            data = list(json.load(file).get('data'))

        with open(file_path, 'w', encoding=encoding) as file:
            json.dump(data, file, ensure_ascii=False)

    def build_node(self, file_path, entities):
        """
        构建实体的名称集合作为 key，并按序号作为 value
        """

        self.__print_log('Start building Entity_Node...')

        # 建立各实体的字典索引
        data_list = self.__read(file_path)
        entity_dict = dict.fromkeys(entities)
        for k in entity_dict.keys():
            entity_dict[k] = set()

        # 获取各实体的名称集合
        for k in entities:
            for data in data_list:
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
            entity_path = f'{ENTITY_BASE_PATH}{entity}.json'
            with open(entity_path, 'w', encoding='utf-8') as file:
                keys = list(entity_dict[entity])
                data = dict(zip(keys, range(len(keys))))
                json.dump(data, file, ensure_ascii=False)
                self.__print_log(f'\tnode_{entity}.json')

            entity_inv_path = f'{ENTITY_BASE_PATH}{entity}_inv.json'
            with open(entity_inv_path, 'w', encoding='utf-8') as file:
                inv_data = dict(zip(data.values(), data.keys()))
                json.dump(inv_data, file, ensure_ascii=False)
                self.__print_log(f'\t{entity}_inv.json')

        self.__print_log('Entity_Node built successfully.')

    def build_edge(self, file_path, entities):
        """
        利用倒排索引构建关系，作为图的边

        (将实体之间的倒排索引在逻辑上视为有向图的边)

        """

        self.__print_log('Start building Relation_Edge...')

        # 读取数据
        with open(file_path, 'r', encoding='utf-8') as file:
            data_list = json.load(file)

        # 生成需要构建关系的实体的排列
        for e1, e2 in itertools.permutations(entities, 2):

            # e1 代表倒排索引中的 key
            file_path = f'{ENTITY_BASE_PATH}{e1}.json'
            with open(file_path, 'r', encoding='utf-8') as file:
                keys = json.load(file)
                for k in keys.keys():
                    keys[k] = list()

            # e2 代表倒排索引中的 value
            file_path = f'{ENTITY_BASE_PATH}{e2}.json'
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
            for data in data_list:
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
            relation_path = f'{RELATION_INDEX_PATH}{e1}_{e2}.json'
            with open(relation_path, 'w', encoding='utf-8') as file:
                json.dump(inverse_dict, file, ensure_ascii=False)
                self.__print_log(f'\tedge_{e1}_{e2}.json')

        self.__print_log('Relationship built successfully.')

    def build_graph(self):
        """
        以实体建立为结点，以关系建立为边
        """
        self.__print_log('------')
        self.build_node(self.data_path, self.entities)
        self.__print_log('------')
        self.build_edge(self.data_path, self.entities)

    @staticmethod
    def load_node():
        entity_dict = dict()
        entity_file_list = os.listdir(ENTITY_BASE_PATH)
        for entity in entity_file_list:
            entity_name = entity.split('.')[0]
            file_path = ENTITY_BASE_PATH + entity
            with open(file_path, 'r', encoding='utf-8') as file:
                entity_dict[entity_name] = json.load(file)
        return entity_dict

    @staticmethod
    def load_edge():
        relation_dict = dict()
        relation_file_list = os.listdir(RELATION_INDEX_PATH)
        for relation in relation_file_list:
            entity_name = relation.split('.')[0]
            file_path = RELATION_INDEX_PATH + relation
            with open(file_path, 'r', encoding='utf-8') as file:
                relation_dict[entity_name] = json.load(file)
        return relation_dict

    def __unfold_and_select(self, data, select, mod):
        index_entity = set()

        if mod == '&':
            for i, s in enumerate(select):
                item_set = set(data[s])
                if i == 0:
                    index_entity = item_set
                else:
                    index_entity &= item_set

        if mod == '|':
            for key, values in data.items():
                for s, t in itertools.product([key], values):
                    if select is not None and s not in select:
                        continue
                    else:
                        index_entity.add(t)
        return index_entity

    def search_by_entity(self, condition, mod='&'):
        index_set = set()
        for i, item in enumerate(condition):
            entity_item = list(item.keys())[0]
            if entity_item == self.main_index:
                continue
            else:
                rel = self.relation_dict[f'{entity_item}_{self.main_index}']
            index_entity_item = self.__unfold_and_select(rel, item[entity_item], mod=mod)
            if i == 0:
                index_set = index_entity_item
            else:
                index_set &= index_entity_item

        result = list()
        k = self.main_index + '_inv'
        main_index_inv = self.entity_dict[k]
        for i in index_set:
            result.append(main_index_inv[str(i)])

        return result


# search = Search()
# search.inverse_index('在吗')
# search.run()
# answer = search.search_answer('我刚吃完饭')
# print(answer)
# search.cosine_sim('今天天气真好', '今天天气真好')

# path = 'knowledge_data/medical.json'
# entity_list = ['name', 'category', 'symptom', 'check']
# kg = KnowGraph(path, entity_list, 'name')
# gd.close_log()
# kg.build_graph()

# e1 = {'category': ['泌尿外科']}
# e2 = {'symptom': ['腹水', '低血压']}
# result = kg.search_by_entity([e2], mod='&')
# print(result)

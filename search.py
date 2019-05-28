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

import numpy as np
import jieba

from process import Vocabulary

jieba.setLogLevel('INFO')


class Search:

    THRESHOLD = 0.6

    def __init__(self):
        vocabulary = Vocabulary()
        self.inverse = vocabulary.inverse
        self.zip_data = vocabulary.load_seq_qa()
        self.question_list = self.zip_data[0]
        self.answer_list = self.zip_data[1]

    @staticmethod
    def cosine_sim(a, b):
        """计算两个句子的 余弦相似度"""
        a_words = Counter(jieba.lcut(a))
        b_words = Counter(jieba.lcut(b))

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
            sim = self.cosine_sim(question, q)
            result_sim.append((i, sim))

        # 根据两两的余弦相似度选出最相似的问句
        result = max(result_sim, key=lambda x: x[1])

        # 如果相似度低于阈值，则返回 None
        if result[1] > self.THRESHOLD:
            return self.answer_list[result[0]]
        else:
            return None


# search = Search()
# search.inverse_index('在吗')
# search.run()
# answer = search.search_answer('我刚吃完饭')
# print(answer)
# search.cosine_sim('今天天气真好', '今天天气真好')

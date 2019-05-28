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
import json

import numpy as np
import jieba

jieba.setLogLevel('INFO')


class Search:

    SPECIAL_WORDS_PATH = 'config/special_words.txt'

    BASE_QA_PATH = 'corpus/'

    SEQ_QA_PATH = BASE_QA_PATH + 'conversation_test.txt'

    SPLIT_QA_PATH = [BASE_QA_PATH + 'english_movie_q.json',
                     BASE_QA_PATH + 'english_movie_a.json']

    THRESHOLD = 0.6

    def __init__(self):
        self.load_special_words()
        self.zip_data = self.inverse_index()
        self.words_dict = self.zip_data[0]
        self.question_list = self.zip_data[1]
        self.answer_list = self.zip_data[2]

    def load_special_words(self):
        """加载固定词语，禁止分词"""
        jieba.load_userdict(self.SPECIAL_WORDS_PATH)

    def load_seq_qa(self):
        """从序列语料库中加载语料"""
        q_list = list()
        a_list = list()
        with open(self.SEQ_QA_PATH, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if i % 2 == 0:
                    q_list.append(line)
                if i % 2 == 1:
                    a_list.append(line)

        return q_list, a_list

    def load_split_qa(self):
        """从问题、答案两个语料库文件中加载语料"""
        split_qa = list()
        for item in self.SPLIT_QA_PATH:
            corpus = json.load(open(item, 'r', encoding='utf-8'))
            split_qa.append(corpus.get('data'))

        q_list, a_list = split_qa
        return q_list, a_list

    def inverse_index(self):
        """建立倒排索引"""
        q_list, a_list = self.load_seq_qa()
        qw_list = list()
        vocabulary = set()

        # 对每个问句分词，并利用空列表初始化，生成字(词)典
        for q in q_list:
            # words = jieba.lcut_for_search(q)
            words = jieba.lcut(q, cut_all=True)
            qw_list.append(words)
            vocabulary |= set(words)
        word_dict = dict.fromkeys(vocabulary)
        for k in word_dict.keys():
            word_dict[k] = list()

        # 记录出现相应的词的文档，建立倒排索引
        for i, qw in enumerate(qw_list):
            for w in qw:
                word_dict[w].append(i)

        return word_dict, q_list, a_list

    def cosine_sim(self, a, b):
        """计算两个句子的 余弦相似度"""
        a_words = Counter(jieba.lcut(a, cut_all=True))
        b_words = Counter(jieba.lcut(b, cut_all=True))

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
        q_words = jieba.lcut(question, cut_all=True)
        for q_word in q_words:
            index = self.words_dict.get(q_word, list())
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

"""
    对语句进行特征工程处理

    --> 清洗：去空格、去标点、去除停用词

    --> 分词：按照不同模式进行分词、特殊字典

    --> 标注：词性标注、语义角色标注、命名实体识别

    --> 分析：依存句法分析、语义依存树/图分析、

    --> 过滤：剔除敏感词汇、剔除不雅词汇

    --> 数值化：构建词向量、生成句子向量

    --> 特征提取：提取关键词、判断主题类型、构建其他特征

    --> 句子长度约束：补全短句，删减长句（或直接拒绝）

"""

import urllib.request
import urllib.parse
import hashlib
import base64
import json
import time
import re

import jieba

from config import *


jieba.setLogLevel('INFO')


class Vocabulary:

    def __init__(self):
        self.load_special_words()
        self.vocab = self.get_vocab()
        self.inverse = self.get_inverse()

    @staticmethod
    def load_special_words():
        """加载固定词语，禁止分词"""
        jieba.load_userdict(SPECIAL_WORDS_PATH)

    @staticmethod
    def load_seq_qa():
        """从序列语料库中加载语料"""
        q_list = list()
        a_list = list()
        with open(SEQ_CORPUS_PATH, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if i % 2 == 0:
                    q_list.append(line)
                if i % 2 == 1:
                    a_list.append(line)
        return q_list, a_list

    @staticmethod
    def load_split_qa():
        """从问题、答案两个语料库文件中加载语料"""
        split_qa = list()
        for item in SPLIT_CORPUS_PATH:
            corpus = json.load(open(item, 'r', encoding='utf-8'))
            split_qa.append(corpus.get('data'))

        q_list, a_list = split_qa
        return q_list, a_list

    def build_vocab(self):
        """建立字典，键为词、值为序号"""
        q_list, _ = self.load_seq_qa()
        qw_list = list()
        vocab = set()

        # 对每个问句分词
        for q in q_list:
            q = re.sub(r'[0-9]*', '', q)
            words = jieba.lcut(q)
            qw_list.append(words)
            vocab |= set(words)

        word_dict = dict(zip(vocab, range(len(vocab))))
        word_dict['<end>'] = -1
        word_dict['<start>'] = -2

        with open(VOCABULARY_PATH, 'w', encoding='utf-8') as f:
            json.dump(word_dict, f, ensure_ascii=False)
        print(f'字典构建完成！--- {VOCABULARY_PATH}')

    @staticmethod
    def get_vocab():
        """读取字典"""
        with open(VOCABULARY_PATH, 'r', encoding='utf-8') as f:
            vocab = json.load(f)
        return vocab

    def build_inverse(self):
        """构建倒排索引"""
        vocab = self.get_vocab()
        q_list, _ = self.load_seq_qa()
        inverse_index_dict = dict().fromkeys(vocab.keys())
        for k in inverse_index_dict:
            inverse_index_dict[k] = list()

        # 记录出现相应的词的文档，建立倒排索引
        for i, qw in enumerate(q_list):
            qw = re.sub(r'[0-9]*', '', qw)
            qw = jieba.lcut(qw)
            for w in qw:
                inverse_index_dict[w].append(i)

        with open(INVERSE_INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump(inverse_index_dict, f, ensure_ascii=False)
        print(f'倒排索引构建完成！ --- {INVERSE_INDEX_PATH}')

    @staticmethod
    def get_inverse():
        """读取倒排索引"""
        with open(INVERSE_INDEX_PATH, 'r', encoding='utf-8') as f:
            inverse_index = json.load(f)
        return inverse_index


class LTProcess:
    """LTP 云平台相关功能"""

    URL = "http://ltpapi.xfyun.cn/v1/{func}"

    # 开放平台应用ID
    X_APPID = "5cea61f2"

    # 开放平台应用接口秘钥
    API_KEY = "bce45c6ce0be6075e45c6b33f5b38945"

    def get_response(self, text, func):
        param = {"type": "dependent"}
        x_param = base64.b64encode(json.dumps(param).replace(' ', '').encode('utf-8'))
        body = urllib.parse.urlencode({'text': text}).encode('utf-8')
        x_time = str(int(time.time()))
        ori_str = self.API_KEY.encode('utf-8') + str(x_time).encode('utf-8') + x_param
        x_checksum = hashlib.md5(ori_str).hexdigest()
        x_header = {'X-Appid': self.X_APPID,
                    'X-CurTime': x_time,
                    'X-Param': x_param,
                    'X-CheckSum': x_checksum}
        url = self.URL.format(func=func)
        req = urllib.request.Request(url, body, x_header)
        result = urllib.request.urlopen(req)
        result = result.read().decode('utf-8')
        print(result)
        return result

    def cut_segment(self, text):
        """分词"""
        return self.get_response(text, 'cws').get('data').get('word')

    def pos_segment(self, text):
        """词性标注"""
        item = 'pos'
        words = self.cut_segment(text)
        pos = self.get_response(text, item).get('data').get(item)
        return zip(words, pos)

    def get_result(self, text, func):
        """
        各种服务接口调用
            ke：关键词提取
        """
        return self.get_response(text, func).get('data').get(func)


# vocabulary = Vocabulary()
# vocabulary.build_vocab()
# vocabulary.build_inverse()

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
import logging
import base64
import json
import time
import re

from gensim.models import Word2Vec
import jieba

from config.path_config import *


class WordWorker:

    pad = 0
    start = 1
    end = 2

    def __init__(self, log=True):
        self.logger = logging.getLogger()
        if not log:
            self.close_log()
        self.load_special_words()
        self.vocab = self.get_vocab()
        self.inverse = self.get_inverse()
        self.zip_QA = self.load_seq_qa()
        self.question_list = self.zip_QA[0]
        self.answer_list = self.zip_QA[1]
        self.qa_list = self.concat_qa()

    def close_log(self):
        self.logger.setLevel(logging.ERROR)

    def print_log(self, msg):
        self.logger.warning(msg)

    @staticmethod
    def load_special_words():
        """加载固定词语，禁止分词"""
        jieba.load_userdict(SPECIAL_WORDS_PATH)
        jieba.load_userdict(MEDICAL_SPECIAL_WORDS_PATH)

    @staticmethod
    def load_seq_qa():
        """从序列语料库中加载语料"""
        q_list = list()
        a_list = list()
        with open(SEQ_CORPUS_PATH, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                line = re.sub(r'[0-9]*', '', line)
                line = jieba.lcut(line)
                if i % 2 == 0:
                    q_list.append(line)
                if i % 2 == 1:
                    a_list.append(line)
        return q_list, a_list

    def concat_qa(self):
        """将每轮的问句与回答进行拼接"""
        qa_list = [q + a for q, a in zip(self.question_list, self.answer_list)]
        return qa_list

    def build_vocab(self):
        """根据问句建立字典，键为词、值为序号"""
        q_list, _ = self.load_seq_qa()
        vocab = set()

        # 对每个问句分词
        for q in q_list:
            vocab |= set(q)

        word_dict = dict(zip(vocab, range(3, len(vocab)+3)))
        word_dict['<pos>'] = self.pad
        word_dict['<end>'] = self.end
        word_dict['<start>'] = self.start

        with open(VOCABULARY_PATH, 'w', encoding='utf-8') as f:
            json.dump(word_dict, f, ensure_ascii=False)
        self.print_log('Vocabulary is completed.')

    @staticmethod
    def get_vocab():
        """读取字典"""
        with open(VOCABULARY_PATH, 'r', encoding='utf-8') as f:
            vocab = json.load(f)
        return vocab

    def build_inverse(self):
        """根据问句构建倒排索引"""
        vocab = self.get_vocab()
        q_list, _ = self.load_seq_qa()
        inverse_index_dict = dict().fromkeys(vocab.keys())
        for k in inverse_index_dict:
            inverse_index_dict[k] = list()

        # 记录出现相应的词的文档，建立倒排索引
        for i, qw in enumerate(q_list):
            for w in qw:
                inverse_index_dict[w].append(i)

        with open(INVERSE_INDEX_PATH, 'w', encoding='utf-8') as f:
            json.dump(inverse_index_dict, f, ensure_ascii=False)
        self.print_log('Inverse index is completed.')

    @staticmethod
    def get_inverse():
        """读取倒排索引"""
        with open(INVERSE_INDEX_PATH, 'r', encoding='utf-8') as f:
            inverse_index = json.load(f)
        return inverse_index

    def sent2vec(self, ml=0, limit=999):
        """将句子转换成句子向量，每个词以数字表示"""

        # 获取句子最大长度
        max_len = ml
        q_list = list()
        for q in self.question_list:
            q_len = len(q)

            # 提出超过长度限制的语句
            if q_len > limit:
                continue
            max_len = q_len if q_len > max_len else max_len

            # 将词转化未数字索引
            q_words = list(map(lambda k: self.vocab[k], q))
            q_list.append(q_words)

        max_len += 1  # 考虑 <end> 标签

        # 以 添加 <end> 标签，并用 <pos> 标签填补
        def to_vec(sents):
            for sent in sents:
                d = max_len - len(sent)
                yield sent + [self.end] + [self.pad] * d

        return to_vec(q_list)

    def build_word2vec(self, skip_gram=False):
        word2vec = Word2Vec(self.qa_list, size=100, sg=skip_gram, min_count=1)
        word2vec.save(WORD2VEC_MODEL_PATH)
        self.print_log(f'Word2Vec 训练完成！ --- {WORD2VEC_MODEL_PATH}')

    def get_word2vec(self):
        word2vec = Word2Vec.load(WORD2VEC_MODEL_PATH)
        self.print_log('Word2Vec 加载完成！')
        return word2vec


class LTPWorker:
    """LTP 云平台相关功能"""

    URL = "http://ltpapi.xfyun.cn/v1/{func}"

    # 开放平台应用ID
    X_APPID = "******"

    # 开放平台应用接口秘钥
    API_KEY = "******"

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


# wf = WordFactory()
# wf.build_vocab()
# wf.build_inverse()
# vecs = wf.sent2vec()
# print(list(vecs))
# wf.build_word2vec()
# w2v = wf.get_word2vec()
# result = w2v.most_similar('鼠标')
# print(result)

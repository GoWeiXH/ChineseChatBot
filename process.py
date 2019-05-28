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

import time
import urllib.request
import urllib.parse
import json
import hashlib
import base64


class LTProcess:

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

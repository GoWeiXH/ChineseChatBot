import json

from process import LTProcess


def ttt():
    sent = '我是中央情报局的一员'
    sent = '怎么才能把电脑里的垃圾文件删除'

    ltp = LTProcess()

    result = ltp.get_result(sent, 'ke')
    print(result)


def change():
    corpus = json.load(open('corpus/english_movie_qa.json', 'r', encoding='utf-8'))
    data = corpus.get('data')

    q_list = list()
    a_list = list()
    for datum in data:
        q_list.append(datum['q'])
        a_list.append(datum['a'])

    json.dump({'data': q_list}, open('corpus/english_movie_q.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump({'data': a_list}, open('corpus/english_movie_a.json', 'w', encoding='utf-8'), ensure_ascii=False)


def load():
    q_corpus = json.load(open('corpus/english_movie_q.json', 'r', encoding='utf-8'))
    a_corpus = json.load(open('corpus/english_movie_a.json', 'r', encoding='utf-8'))

    print('')


# change()

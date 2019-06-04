import json

from factory import LTPWorker


def ttt():
    sent = '我是中央情报局的一员'
    sent = '怎么才能把电脑里的垃圾文件删除'

    ltp = LTPWorker()

    result = ltp.get_result(sent, 'ke')
    print(result)


def change():
    corpus = json.load(open('data_corpus/english_movie_qa.json', 'r', encoding='utf-8'))
    data = corpus.get('data')

    q_list = list()
    a_list = list()
    for datum in data:
        q_list.append(datum['q'])
        a_list.append(datum['a'])

    json.dump({'data': q_list}, open('data_corpus/english_movie_q.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump({'data': a_list}, open('data_corpus/english_movie_a.json', 'w', encoding='utf-8'), ensure_ascii=False)


def load():
    q_corpus = json.load(open('data_corpus/english_movie_q.json', 'r', encoding='utf-8'))
    a_corpus = json.load(open('data_corpus/english_movie_a.json', 'r', encoding='utf-8'))

    print('')


def change_json(file_path, encoding='utf-8'):
    with open(file_path, 'r', encoding=encoding) as file:
        data = list(json.load(file).get('data'))

    with open(file_path, 'w', encoding=encoding) as file:
        json.dump(data, file, ensure_ascii=False)


def json_process():
    data_dict = dict()
    file_path = '../data_knowledge/medical.json'
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # '' (2446283377968)
    key_list = ['do_eat', 'not_eat', 'recommand_eat', 'recommand_drug', 'common_drug']

    for d in data:
        if not all([key in d for key in key_list]):
            continue
        del d['_id']
        del d['drug_detail']
        index = d.get('name')
        data_dict[index] = d

    p = '../kg_index/origin_index.json'
    with open(p, 'w', encoding='utf-8') as file:
        json.dump(data_dict, file, ensure_ascii=False)


def make_sp_word():
    import os

    dirs = os.listdir('../kg_index/medical/entity_node/')

    for d in dirs:
        if 'inv' not in d:
            p = f'../kg_index/medical/entity_node/{d}'
            with open(p, 'r', encoding='utf-8') as file:
                data = list(json.load(file).keys())

            p = '../kg_index/medical/special_words.txt'
            with open(p, 'a', encoding='utf-8', newline='\n') as file:
                for l in data:
                    file.write(l + '\n')


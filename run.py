from filter import LayerFilter


def main():
    layer_filter = LayerFilter()
    print('你好~\n')
    while True:
        question = input()
        if question == '再见':
            break
        answer = layer_filter.get_answer(question)
        print(answer)
    print('再见')
    print('我去睡觉了...')
    # print('Robot is going to sleep...')


def test():

    question = '你吃饭了吗'

    layer_filter = LayerFilter()
    answer = layer_filter.get_answer(question)
    print(answer)


if __name__ == '__main__':
    # main()
    test()

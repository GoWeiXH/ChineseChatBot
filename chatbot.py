"""
    问答机器人

    --> 人格初始化

    --> 输入：问题语句 Q

    --> 经过各模块处理

    --> 输出：回答语句 A

"""

from itchat.content import TEXT
import itchat

from filter import LayerFilter


layer_filter = LayerFilter()
white_list = []


def to_log(question, answer):
    with open('config/chat_log.txt', 'a', encoding='utf-8') as f:
        log_content = f'Q:{question}---A:{answer} \n'
        print(log_content)
        f.write(log_content)


def answer_test():

    @itchat.msg_register(TEXT, isGroupChat=True)
    def group_reply(msg):
        is_at = msg.isAt
        if is_at:
            question = msg.text
            print(question)
            answer = layer_filter.get_answer(question)
            to_log(question, answer)
            answer = '@' + msg.ActualNickName + ' ' + answer
            msg.user.send(answer)

    @itchat.msg_register(TEXT, isFriendChat=True, isGroupChat=False, isMpChat=False)
    def single_reply(msg):
        question = msg.text
        answer = layer_filter.get_answer(question)
        to_log(question, answer)
        msg.user.send(answer)

    itchat.auto_login(True)
    itchat.run()


answer_test()

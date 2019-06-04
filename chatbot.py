"""
    问答机器人

    --> 输入：问题语句 Q

    --> 输出：回答语句 A

"""

import time

from itchat.content import TEXT
import itchat

from filter import LayerFilter


class WXChatBot:
    """机器人类，拥有联网（微信）以及本地两种聊天模式"""

    def __init__(self):
        self.layer_filter = LayerFilter()
        self.white_list = []

    @classmethod
    def to_log(cls, question, answer):
        with open('config/chat_log.txt', 'a', encoding='utf-8') as f:
            log_content = f'Q:{question}---A:{answer} \n'
            print(log_content)
            f.write(log_content)

    def inter_start(self):
        """联网聊天模式"""

        @itchat.msg_register(TEXT, isGroupChat=True)
        def group_reply(msg):
            is_at = msg.isAt
            if is_at:
                question = msg.text
                print(question)
                answer = self.layer_filter.get_answer(question)
                self.to_log(question, answer)
                answer = '@' + msg.ActualNickName + ' ' + answer
                msg.user.send(answer)

        @itchat.msg_register(TEXT, isFriendChat=True, isGroupChat=False, isMpChat=False)
        def single_reply(msg):
            question = msg.text
            answer = self.layer_filter.get_answer(question)
            self.to_log(question, answer)
            msg.user.send(answer)

        itchat.auto_login(True)
        itchat.run()

    def local_start(self):
        """本地聊天模式"""

        time.sleep(0.2)
        print('我们开始聊天吧~')
        while True:
            question = input('>> ')
            if question == '关机':
                print('好的，下次再见~')
                break
            answer = self.layer_filter.get_answer(question)
            print(answer)

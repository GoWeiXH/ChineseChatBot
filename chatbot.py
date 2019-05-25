"""
    问答机器人

    --> 人格初始化

    --> 输入：问题语句 Q

    --> 经过各模块处理

    --> 输出：回答语句 A

"""

from itchat.content import TEXT
import itchat

from template import Template


def answer_test():

    @itchat.msg_register(TEXT, isFriendChat=True, isGroupChat=False, isMpChat=False)
    def simple_reply(msg):
        template = Template()
        answer = template.get_answer(msg.text)
        return answer

    itchat.auto_login(True)
    itchat.run()


answer_test()

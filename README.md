## 中文 问答 / 聊天机器人

一个利用模板匹配、问题检索、联网搜索、以及答案生成等方法，完成问答交互的中文聊天机器人。

- #### 项目介绍

    1. 模板匹配：利用 XML 文件配置相关人格等固定信息，根据正则表达式匹配答案
    2. 问题检索：利用倒排索引搜索问题，用余弦相似度筛选答案
    3. 联网搜索：利用搜狗问问的搜索引擎对问题进行实时搜索
    4. 答案生成：利用 Seq2Seq 模型以及机器学习方法生成答案（尚未加入该模块）
    
    问答处理是层级线性的，处理流程如下：
    - 首先将问题送入模板匹配模块，匹配到后会从答案中随机返回。如果没有匹配到答案则送入下一模块
    - 进入检索模块，并根据问题相似度选出匹配问题的答案，如果没有匹配到则送入下一模块
    - 到联网搜索模块，意味着本地语料库没有匹配答案，则根据搜狗问问的接口搜索答案
    

- #### 代码组织结构
    
    - template.py 是模板匹配模块    
    - search.py 是问题检索模块
    - generate.py 是答案生成模块（尚未添加功能）
    - internet.py 是联网搜索模块
    - process.py 是处理模块，提供分词、提取关键字、清洗词句等功能
    - score.py 是打分模块，对个模块的答案进行评分处理（尚未添加）
    - filter.py 是层级处理模块，主要控制各模块的顺序运行（添加 score.py 会加入 re-rank 机制）
    - run.py 本地单机聊天测试
    - chatbot.py 登陆微信，线上自动聊天测试


- #### 运行方法
    
    1. 调用 filter.py 中的 get_answer()<br>
    <pre><code>
    from filter import LayerFilter
    question = '你好'
    layer_filter = LayerFilter()
    answer = layer_filter.get_answer(question)
    print(answer)
    
    >>> 你好~，你是哪位
    </code></pre>
    
    2. 运行 chatbot.py 中的 answer_test()<br>
    <pre><code>
    answer_test()
    </code></pre>
   
- #### config 文件

    - default_answer.xml 配置了默认答案，当没有联网的情况下且未找到匹配答案时返回默认答案<br>
    需要注意的是，<robot_info>下的 tag 名称要与 <temp id='name'>的 id 值一致<br>
    例如：
   '''
    <root>
        <robot_info>
            <age>18<age>
        </robot_info>
        <temp id='age'>
            ...
        </temp>
    </root>
    '''
    - robot_template.xml 配置了机器人的固定人格信息即相应回答
    - special_words.txt 配置了特殊不想被且分开的词汇

- #### 聊天数据

    保存在 corpus/conversation_text.txt 中<br>
    形如：
    <pre><code>
    你好
    你好，你是哪位
    在吗
    在，怎么了？
    </code></pre>
    

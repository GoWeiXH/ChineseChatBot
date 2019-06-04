

def extract_question():
    with open('question_to_learn.txt', 'a', encoding='utf-8') as file:
        questions = list()
        with open('data_corpus/chat_log.txt', 'r', encoding='utf-8') as f:
            for line in f:
                question = line.split('---')[0][2:]
                questions.append(question)
        for line in questions:
            file.write(line + '\n')


# extract_question()

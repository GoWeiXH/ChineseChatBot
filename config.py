BASE_CORPUS_PATH = 'corpus/'

SEQ_CORPUS_PATH = BASE_CORPUS_PATH + 'conversation_test.txt'

SPLIT_CORPUS_PATH = [BASE_CORPUS_PATH + 'english_movie_q.json',
                     BASE_CORPUS_PATH + 'english_movie_a.json']

BASE_CONFIG = 'config/'

VOCABULARY_PATH = BASE_CONFIG + 'vocab_from_q.json'

SPECIAL_WORDS_PATH = BASE_CONFIG + 'special_words.txt'

INVERSE_INDEX_PATH = BASE_CONFIG + 'inverse_index.json'

SELF_TEMP_FILE = BASE_CONFIG + 'robot_template.xml'

DEFAULT_PATH = BASE_CONFIG + 'default_answer.xml'

WORD2VEC_MODEL_PATH = BASE_CONFIG + 'word2vec.model'

BASE_INDEX_PATH = 'kg_index/'

ENTITY_BASE_PATH = BASE_INDEX_PATH + 'entity_node/'

RELATION_INDEX_PATH = BASE_INDEX_PATH + 'relation_edge/'

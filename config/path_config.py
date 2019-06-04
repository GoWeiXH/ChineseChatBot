# 语料库文件存储路径
BASE_CORPUS_PATH = 'data_corpus/'

SEQ_CORPUS_PATH = BASE_CORPUS_PATH + 'conversation_test.txt'

SPLIT_CORPUS_PATH = [BASE_CORPUS_PATH + 'english_movie_q.json',
                     BASE_CORPUS_PATH + 'english_movie_a.json']

# 配置数据文件的存储路径
BASE_CONFIG = 'config/'

VOCABULARY_PATH = BASE_CONFIG + 'vocab_from_q.json'

SPECIAL_WORDS_PATH = BASE_CONFIG + 'special_words.txt'

INVERSE_INDEX_PATH = BASE_CONFIG + 'inverse_index.json'

SELF_TEMP_FILE = BASE_CONFIG + 'robot_template.xml'

DEFAULT_PATH = BASE_CONFIG + 'default_answer.xml'

WORD2VEC_MODEL_PATH = BASE_CONFIG + 'word2vec.model'

# 知识图谱的基础存储路径
BASE_INDEX_PATH = 'kg_index/'

# 医药领域知识图谱的存储路径
MEDICAL_BASE_INDEX_PATH = BASE_INDEX_PATH + 'medical/'

MEDICAL_SPECIAL_WORDS_PATH = MEDICAL_BASE_INDEX_PATH + 'special_words.txt'

MEDICAL_ORIGIN_INDEX_PATH = MEDICAL_BASE_INDEX_PATH + 'origin_index.json'

MEDICAL_ENTITY_BASE_PATH = MEDICAL_BASE_INDEX_PATH + 'entity_node/'

MEDICAL_RELATION_INDEX_PATH = MEDICAL_BASE_INDEX_PATH + 'relation_edge/'

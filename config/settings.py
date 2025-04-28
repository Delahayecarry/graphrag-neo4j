"""
集中管理项目所有配置项和环境变量
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(ROOT_DIR, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')

# Neo4j数据库配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# OpenAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# 嵌入模型配置
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", OPENAI_API_KEY)
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "https://api.openai.com/v1/embeddings")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")

# 知识图谱配置
NODE_LABELS = ["Document", "Person", "Organization", "Location", "Concept", "Event"]
REL_TYPES = ["MENTIONS", "RELATED_TO", "PART_OF", "LOCATED_IN", "CREATED_BY"]

# 索引配置
VECTOR_INDEX_NAME = "text_embeddings"
VECTOR_EMBEDDING_DIMENSIONS = 1536
VECTOR_SIMILARITY_FUNCTION = "cosine"

# 可视化配置
VIZ_OUTPUT_DIR = os.path.join(ROOT_DIR, 'output')
os.makedirs(VIZ_OUTPUT_DIR, exist_ok=True)

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s" 
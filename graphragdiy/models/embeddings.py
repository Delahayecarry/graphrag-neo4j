"""
嵌入模型管理模块
"""

import logging
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from config import settings

logger = logging.getLogger(__name__)

class EmbeddingManager:
    """嵌入模型管理类"""
    
    def __init__(self, model_name=None, api_key=None, base_url=None):
        """
        初始化嵌入模型管理器
        
        Args:
            model_name (str, optional): 模型名称
            api_key (str, optional): API密钥
            base_url (str, optional): API基础URL
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.api_key = api_key or settings.EMBEDDING_API_KEY
        self.base_url = base_url or settings.EMBEDDING_URL
        
        self.embedder = self._initialize_embedder()
        
    def _initialize_embedder(self):
        """初始化嵌入模型实例"""
        try:
            embedder = OpenAIEmbeddings(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info("成功初始化嵌入模型")
            return embedder
        except Exception as e:
            logger.error(f"初始化嵌入模型失败: {str(e)}")
            raise
    
    def get_embedder(self):
        """获取嵌入模型实例"""
        return self.embedder
    
    def embed_text(self, text):
        """
        对文本进行嵌入
        
        Args:
            text (str): 要嵌入的文本
            
        Returns:
            list: 嵌入向量
        """
        try:
            return self.embedder.embed_text(text)
        except Exception as e:
            logger.error(f"文本嵌入失败: {str(e)}")
            raise

# 默认嵌入模型管理器实例，用于全局共享
default_embedding_manager = None

def get_embedding_manager():
    """获取默认嵌入模型管理器实例"""
    global default_embedding_manager
    if default_embedding_manager is None:
        default_embedding_manager = EmbeddingManager()
    return default_embedding_manager 
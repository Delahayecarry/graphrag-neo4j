"""
检索器管理模块
"""

import logging
from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
from config import settings
from graphragdiy.database.neo4j_connector import get_connector
from graphragdiy.models.embeddings import get_embedding_manager

logger = logging.getLogger(__name__)

class RetrieverManager:
    """检索器管理类"""
    
    def __init__(self, db_connector=None, embedding_manager=None):
        """
        初始化检索器管理器
        
        Args:
            db_connector: 数据库连接器
            embedding_manager: 嵌入模型管理器
        """
        self.db_connector = db_connector or get_connector()
        self.embedding_manager = embedding_manager or get_embedding_manager()
        
        self.driver = self.db_connector.get_driver()
        self.embedder = self.embedding_manager.get_embedder()
        
        # 预定义的检索查询
        self.default_retrieval_query = """
        // 1. 以向量相似度获取初始Chunk节点
        WITH node AS chunk
        
        // 2. 从Chunk遍历到实体，然后获取相关关系
        MATCH (chunk)<-[:FROM_CHUNK]-()-[relList:!FROM_CHUNK]-{1,2}()
        UNWIND relList AS rel
        
        // 3. 收集文本块和关系
        WITH collect(DISTINCT chunk) AS chunks,
             collect(DISTINCT rel) AS rels
        
        // 4. 格式化返回上下文
        RETURN '=== 文本块 ===\n' + apoc.text.join([c in chunks | c.text], '\n---\n') + 
               '\n\n=== 知识图谱关系 ===\n' +
               apoc.text.join([r in rels | startNode(r).name + ' - ' + type(r) + 
               '(' + coalesce(r.details, '') + ')' + ' -> ' + endNode(r).name ], 
               '\n---\n') AS info
        """
    
    def create_vector_retriever(self, index_name=None, return_properties=None):
        """
        创建基础向量检索器
        
        Args:
            index_name (str, optional): 索引名称
            return_properties (list, optional): 返回属性列表
            
        Returns:
            VectorRetriever: 向量检索器
        """
        index_name = index_name or settings.VECTOR_INDEX_NAME
        return_properties = return_properties or ["text"]
        
        try:
            retriever = VectorRetriever(
                self.driver,
                index_name=index_name,
                embedder=self.embedder,
                return_properties=return_properties
            )
            logger.info("成功创建向量检索器")
            return retriever
        except Exception as e:
            logger.error(f"创建向量检索器失败: {str(e)}")
            raise
    
    def create_vector_cypher_retriever(self, index_name=None, retrieval_query=None):
        """
        创建向量+Cypher检索器
        
        Args:
            index_name (str, optional): 索引名称
            retrieval_query (str, optional): 检索查询
            
        Returns:
            VectorCypherRetriever: 向量+Cypher检索器
        """
        index_name = index_name or settings.VECTOR_INDEX_NAME
        retrieval_query = retrieval_query or self.default_retrieval_query
        
        try:
            retriever = VectorCypherRetriever(
                self.driver,
                index_name=index_name,
                embedder=self.embedder,
                retrieval_query=retrieval_query
            )
            logger.info("成功创建向量+Cypher检索器")
            return retriever
        except Exception as e:
            logger.error(f"创建向量+Cypher检索器失败: {str(e)}")
            raise
    
    def setup_retrievers(self):
        """
        设置所有检索器
        
        Returns:
            tuple: (向量检索器, 向量+Cypher检索器)
        """
        try:
            vector_retriever = self.create_vector_retriever()
            vector_cypher_retriever = self.create_vector_cypher_retriever()
            
            logger.info("成功设置所有检索器")
            return vector_retriever, vector_cypher_retriever
        except Exception as e:
            logger.error(f"设置检索器失败: {str(e)}")
            raise

# 默认检索器管理器实例，用于全局共享
default_retriever_manager = None

def get_retriever_manager():
    """获取默认检索器管理器实例"""
    global default_retriever_manager
    if default_retriever_manager is None:
        default_retriever_manager = RetrieverManager()
    return default_retriever_manager 
"""
索引管理模块
"""

import logging
from neo4j_graphrag.indexes import create_vector_index
from config import settings
from graphragdiy.database.neo4j_connector import get_connector

logger = logging.getLogger(__name__)

class IndexManager:
    """索引管理类"""
    
    def __init__(self, db_connector=None):
        """
        初始化索引管理器
        
        Args:
            db_connector: 数据库连接器
        """
        self.db_connector = db_connector or get_connector()
        self.driver = self.db_connector.get_driver()
    
    def create_vector_index(self, name=None, label=None, property_name=None, 
                          dimensions=None, similarity_function=None):
        """
        创建向量索引
        
        Args:
            name (str, optional): 索引名称
            label (str, optional): 节点标签
            property_name (str, optional): 属性名称
            dimensions (int, optional): 向量维度
            similarity_function (str, optional): 相似度函数
        """
        name = name or settings.VECTOR_INDEX_NAME
        label = label or "Chunk"
        property_name = property_name or "embedding"
        dimensions = dimensions or settings.VECTOR_EMBEDDING_DIMENSIONS
        similarity_function = similarity_function or settings.VECTOR_SIMILARITY_FUNCTION
        
        try:
            create_vector_index(
                self.driver, 
                name=name, 
                label=label,
                embedding_property=property_name, 
                dimensions=dimensions, 
                similarity_fn=similarity_function
            )
            logger.info(f"成功创建向量索引: {name}")
        except Exception as e:
            logger.error(f"创建向量索引失败: {str(e)}")
            raise
    
    def create_fulltext_index(self, name="entity_index", label="__Entity__", properties=None):
        """
        创建全文索引
        
        Args:
            name (str, optional): 索引名称
            label (str, optional): 节点标签
            properties (list, optional): 属性列表
        """
        properties = properties or ["name"]
        properties_str = ", ".join([f"e.{prop}" for prop in properties])
        
        try:
            query = f"""
            CREATE FULLTEXT INDEX {name} IF NOT EXISTS 
            FOR (e:{label}) 
            ON EACH [{properties_str}]
            """
            self.db_connector.execute_query(query)
            logger.info(f"成功创建全文索引: {name}")
        except Exception as e:
            logger.error(f"创建全文索引失败: {str(e)}")
            raise
    
    def create_all_indexes(self):
        """创建所有必要的索引"""
        try:
            # 创建向量索引
            self.create_vector_index()
            
            # 创建实体全文索引
            self.create_fulltext_index()
            
            logger.info("成功创建所有索引")
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise

# 默认索引管理器实例，用于全局共享
default_index_manager = None

def get_index_manager():
    """获取默认索引管理器实例"""
    global default_index_manager
    if default_index_manager is None:
        default_index_manager = IndexManager()
    return default_index_manager 
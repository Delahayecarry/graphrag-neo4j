"""
Neo4j数据库连接器，管理与Neo4j数据库的连接和交互
"""

import logging
from neo4j import GraphDatabase
from config import settings

logger = logging.getLogger(__name__)

class Neo4jConnector:
    """Neo4j数据库连接器类"""
    
    def __init__(self, uri=None, username=None, password=None):
        """
        初始化Neo4j连接器
        
        Args:
            uri (str, optional): Neo4j数据库URI
            username (str, optional): 用户名
            password (str, optional): 密码
        """
        self.uri = uri or settings.NEO4J_URI
        self.username = username or settings.NEO4J_USERNAME
        self.password = password or settings.NEO4J_PASSWORD
        self.driver = None
        self.connect()
    
    def connect(self):
        """建立与Neo4j数据库的连接"""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
            logger.info(f"成功连接到Neo4j数据库: {self.uri}")
        except Exception as e:
            logger.error(f"连接Neo4j数据库失败: {str(e)}")
            raise
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            logger.info("已关闭Neo4j数据库连接")
    
    def get_driver(self):
        """获取数据库驱动实例"""
        return self.driver
    
    def execute_query(self, query, parameters=None):
        """
        执行Cypher查询
        
        Args:
            query (str): Cypher查询语句
            parameters (dict, optional): 查询参数

        Returns:
            neo4j.Result: 查询结果
        """
        if not self.driver:
            self.connect()
            
        try:
            return self.driver.execute_query(query, parameters or {})
        except Exception as e:
            logger.error(f"执行查询失败: {str(e)}")
            raise
    
    def create_vector_index(self, name, label, property_name, dimensions, similarity_function):
        """
        创建向量索引
        
        Args:
            name (str): 索引名称
            label (str): 节点标签
            property_name (str): 嵌入属性名
            dimensions (int): 嵌入维度
            similarity_function (str): 相似度函数，如"cosine"
        """
        try:
            query = f"""
            CREATE VECTOR INDEX {name} IF NOT EXISTS
            FOR (n:{label})
            ON (n.{property_name})
            OPTIONS {{indexConfig: {{
                `vector.dimensions`: {dimensions},
                `vector.similarity_function`: '{similarity_function}'
            }}}}
            """
            self.execute_query(query)
            logger.info(f"成功创建向量索引: {name}")
        except Exception as e:
            logger.error(f"创建向量索引失败: {str(e)}")
            raise

# 默认连接器实例，用于全局共享
default_connector = None

def get_connector():
    """获取默认连接器实例"""
    global default_connector
    if default_connector is None:
        default_connector = Neo4jConnector()
    return default_connector 
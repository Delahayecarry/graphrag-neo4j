"""
索引管理模块
支持Neo4j和graphrag官方命令行两种索引构建方式
"""

import os
import logging
import subprocess
from typing import Optional
from neo4j_graphrag.indexes import create_vector_index
from config import settings
from graphragdiy.database.neo4j_connector import get_connector

logger = logging.getLogger(__name__)

class IndexManager:
    """索引管理类"""
    
    def __init__(self, db_connector=None, mode="neo4j"):
        """
        初始化索引管理器
        
        Args:
            db_connector: Neo4j数据库连接器（仅neo4j模式需要）
            mode (str): 索引模式，可选 "neo4j" 或 "graphrag"
        """
        self.mode = mode
        if mode == "neo4j":
            self.db_connector = db_connector or get_connector()
            self.driver = self.db_connector.get_driver()
    
    def create_vector_index(self, name=None, label=None, property_name=None, 
                          dimensions=None, similarity_function=None):
        """创建向量索引（Neo4j模式）"""
        if self.mode != "neo4j":
            raise ValueError("此方法仅支持neo4j模式")
            
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
        """创建全文索引（Neo4j模式）"""
        if self.mode != "neo4j":
            raise ValueError("此方法仅支持neo4j模式")
        
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
    
    def setup_graphrag_workspace(self, root_dir: str) -> bool:
        """
        设置graphrag工作目录并初始化配置
        
        Args:
            root_dir (str): graphrag工作目录路径
            
        Returns:
            bool: 是否成功
        """
        if self.mode != "graphrag":
            raise ValueError("此方法仅支持graphrag模式")
            
        try:
            # 创建工作目录
            os.makedirs(os.path.join(root_dir, "input"), exist_ok=True)
            
            # 运行graphrag init命令
            result = subprocess.run(
                ["graphrag", "init", "--root", root_dir],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("graphrag工作目录初始化成功")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"graphrag工作目录初始化失败: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"graphrag工作目录初始化失败: {str(e)}")
            return False

    def run_graphrag_index(self, root_dir: str) -> bool:
        """
        运行graphrag index命令
        
        Args:
            root_dir (str): graphrag工作目录路径
            
        Returns:
            bool: 是否成功
        """
        if self.mode != "graphrag":
            raise ValueError("此方法仅支持graphrag模式")
            
        try:
            # 运行graphrag index命令
            result = subprocess.run(
                ["graphrag", "index", "--root", root_dir],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("graphrag索引构建成功")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"graphrag索引构建失败: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"graphrag索引构建失败: {str(e)}")
            return False
    
    def create_all_indexes(self, root_dir: Optional[str] = None):
        """
        根据模式创建所有必要的索引
        
        Args:
            root_dir (str, optional): graphrag工作目录路径（仅graphrag模式需要）
        """
        try:
            if self.mode == "neo4j":
                # 创建Neo4j索引
                self.create_vector_index()
                self.create_fulltext_index()
                logger.info("成功创建所有Neo4j索引")
            else:
                # 使用graphrag命令创建索引
                if not root_dir:
                    raise ValueError("graphrag模式需要提供root_dir参数")
                    
                # 先初始化工作目录
                if not self.setup_graphrag_workspace(root_dir):
                    raise Exception("graphrag工作目录初始化失败")
                    
                # 运行索引构建
                if not self.run_graphrag_index(root_dir):
                    raise Exception("graphrag索引构建失败")
                    
        except Exception as e:
            logger.error(f"创建索引失败: {str(e)}")
            raise

# 默认索引管理器实例，用于全局共享
default_index_manager = None

def get_index_manager(mode="neo4j"):
    """
    获取默认索引管理器实例
    
    Args:
        mode (str): 索引模式，可选 "neo4j" 或 "graphrag"
    """
    global default_index_manager
    if default_index_manager is None:
        default_index_manager = IndexManager(mode=mode)
    return default_index_manager 
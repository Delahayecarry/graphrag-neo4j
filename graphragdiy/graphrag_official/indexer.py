"""
graphrag官方库索引构建模块
"""

import os
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from graphrag.index import Indexer
    from graphrag.config import Config as GraphragConfig
    GRAPHRAG_AVAILABLE = True
except ImportError:
    GRAPHRAG_AVAILABLE = False
    logger.warning("graphrag官方库未安装")


class GraphragIndexer:
    """graphrag官方库索引构建器"""
    
    def __init__(self, root_dir: str):
        """
        初始化graphrag索引构建器
        
        Args:
            root_dir (str): graphrag工作目录路径
        """
        if not GRAPHRAG_AVAILABLE:
            raise ImportError("graphrag官方库未安装，请先安装: pip install graphrag")
            
        self.root_dir = root_dir
        self.input_dir = os.path.join(root_dir, "input")
        os.makedirs(self.input_dir, exist_ok=True)
        
        # 初始化graphrag配置
        self.config = GraphragConfig(root_dir=root_dir)
        self.indexer = Indexer(self.config)
    
    def process_files(self, file_paths: List[str]) -> bool:
        """
        处理文件并构建索引
        
        Args:
            file_paths (List[str]): 要处理的文件路径列表
            
        Returns:
            bool: 是否成功
        """
        try:
            logger.info("开始处理文件...")
            
            # 复制文件到input目录
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                dest_path = os.path.join(self.input_dir, file_name)
                with open(file_path, 'r', encoding='utf-8') as src, \
                     open(dest_path, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                logger.info(f"已复制文件: {file_path} -> {dest_path}")
            
            # 运行索引构建
            logger.info("开始构建索引...")
            self.indexer.run()
            
            logger.info("索引构建完成")
            return True
            
        except Exception as e:
            logger.error(f"索引构建失败: {str(e)}")
            return False
    
    @staticmethod
    def is_available() -> bool:
        """检查graphrag官方库是否可用"""
        return GRAPHRAG_AVAILABLE
    
    def get_query_commands(self) -> List[str]:
        """
        获取查询命令示例
        
        Returns:
            List[str]: 查询命令列表
        """
        return [
            f"graphrag query --root {self.root_dir} --method global --query \"您的问题\"",
            f"graphrag query --root {self.root_dir} --method local --query \"您的问题\""
        ]


def create_indexer(root_dir: str) -> Optional[GraphragIndexer]:
    """
    创建graphrag索引构建器
    
    Args:
        root_dir (str): graphrag工作目录路径
        
    Returns:
        Optional[GraphragIndexer]: 索引构建器实例，如果官方库未安装则返回None
    """
    if not GRAPHRAG_AVAILABLE:
        return None
    return GraphragIndexer(root_dir) 
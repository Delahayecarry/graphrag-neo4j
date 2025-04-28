"""
知识图谱构建器模块
"""

import os
import logging
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from config import settings
from graphragdiy.database.neo4j_connector import get_connector
from graphragdiy.models.llm import get_llm_manager
from graphragdiy.models.embeddings import get_embedding_manager

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:
    """知识图谱构建器类"""
    
    def __init__(self, entities=None, relations=None, from_pdf=False):
        """
        初始化知识图谱构建器
        
        Args:
            entities (list, optional): 实体类型列表
            relations (list, optional): 关系类型列表
            from_pdf (bool, optional): 是否处理PDF文件
        """
        self.entities = entities or settings.NODE_LABELS
        self.relations = relations or settings.REL_TYPES
        self.from_pdf = from_pdf
        
        # 获取必要组件
        self.db_connector = get_connector()
        self.llm_manager = get_llm_manager()
        self.embedding_manager = get_embedding_manager()
        
        self.driver = self.db_connector.get_driver()
        self.llm = self.llm_manager.get_llm()
        self.embedder = self.embedding_manager.get_embedder()
        
        # 初始化KG构建流程
        self.kg_builder = self._initialize_kg_builder()
        
    def _initialize_kg_builder(self):
        """初始化知识图谱构建流程"""
        try:
            kg_builder = SimpleKGPipeline(
                llm=self.llm,
                driver=self.driver,
                embedder=self.embedder,
                entities=self.entities,
                relations=self.relations,
                from_pdf=self.from_pdf
            )
            logger.info("成功初始化知识图谱构建流程")
            return kg_builder
        except Exception as e:
            logger.error(f"初始化知识图谱构建流程失败: {str(e)}")
            raise
    
    async def build_from_file(self, file_path):
        """
        从文件构建知识图谱
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            dict: 处理结果
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            logger.info(f"开始处理文件: {file_path}")
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # 使用文本内容构建知识图谱
            result = await self.build_from_text(text)
            
            logger.info(f"文件处理完成: {file_path}")
            return result
        except Exception as e:
            logger.error(f"构建知识图谱失败: {str(e)}")
            raise
    
    async def build_from_text(self, text):
        """
        从文本构建知识图谱
        
        Args:
            text (str): 文本内容
            
        Returns:
            dict: 处理结果
        """
        try:
            logger.info(f"开始处理文本 (长度: {len(text)}字符)")
            result = await self.kg_builder.run_async(text=text)
            logger.info("文本处理完成")
            return result
        except Exception as e:
            logger.error(f"构建知识图谱失败: {str(e)}")
            raise
    
    async def build_from_files(self, file_paths):
        """
        从多个文件构建知识图谱
        
        Args:
            file_paths (list): 文件路径列表
            
        Returns:
            list: 处理结果列表
        """
        results = []
        for file_path in file_paths:
            try:
                result = await self.build_from_file(file_path)
                results.append({"file": file_path, "success": True, "result": result})
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {str(e)}")
                results.append({"file": file_path, "success": False, "error": str(e)})
        
        return results

# 默认知识图谱构建器实例，用于全局共享
default_kg_builder = None

def get_kg_builder(from_pdf=False):
    """获取默认知识图谱构建器实例"""
    global default_kg_builder
    if default_kg_builder is None:
        default_kg_builder = KnowledgeGraphBuilder(from_pdf=from_pdf)
    return default_kg_builder 
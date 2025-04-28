"""
GraphRAG系统实现模块
"""

import logging
from neo4j_graphrag.generation.graphrag import GraphRAG
from graphragdiy.models.llm import get_llm_manager
from graphragdiy.knowledge_graph.retriever import get_retriever_manager
from graphragdiy.rag.templates import get_template_manager

logger = logging.getLogger(__name__)

class GraphRAGSystem:
    """GraphRAG系统类"""
    
    def __init__(self, llm_manager=None, retriever_manager=None, template_manager=None):
        """
        初始化GraphRAG系统
        
        Args:
            llm_manager: LLM管理器
            retriever_manager: 检索器管理器
            template_manager: 模板管理器
        """
        self.llm_manager = llm_manager or get_llm_manager()
        self.retriever_manager = retriever_manager or get_retriever_manager()
        self.template_manager = template_manager or get_template_manager()
        
        self.llm = self.llm_manager.get_llm()
        self.retrievers = self.retriever_manager.setup_retrievers()
        self.vector_retriever, self.vector_cypher_retriever = self.retrievers
        
        # 创建RAG实例
        self.rag_instances = self._create_rag_instances()
        self.vector_rag, self.vector_cypher_rag = self.rag_instances
    
    def _create_rag_instances(self):
        """创建RAG实例"""
        try:
            # 获取默认提示模板
            prompt_template = self.template_manager.get_template('chinese')
            
            # 创建GraphRAG实例
            vector_rag = GraphRAG(
                llm=self.llm, 
                retriever=self.vector_retriever, 
                prompt_template=prompt_template
            )
            
            vector_cypher_rag = GraphRAG(
                llm=self.llm, 
                retriever=self.vector_cypher_retriever, 
                prompt_template=prompt_template
            )
            
            logger.info("成功创建GraphRAG实例")
            return vector_rag, vector_cypher_rag
        except Exception as e:
            logger.error(f"创建GraphRAG实例失败: {str(e)}")
            raise
    
    def search(self, query, use_graph=True, top_k=5, template_name=None):
        """
        执行GraphRAG搜索
        
        Args:
            query (str): 查询文本
            use_graph (bool, optional): 是否使用图增强检索
            top_k (int, optional): 返回结果数量
            template_name (str, optional): 提示模板名称
            
        Returns:
            dict: 搜索结果
        """
        try:
            # 选择检索器
            rag = self.vector_cypher_rag if use_graph else self.vector_rag
            
            # 如果指定了模板，更新RAG实例的提示模板
            if template_name:
                template = self.template_manager.get_template(template_name)
                rag.prompt_template = template
            
            # 执行搜索
            result = rag.search(query, retriever_config={'top_k': top_k})
            
            logger.info(f"成功执行搜索: '{query}'")
            return result
        except Exception as e:
            logger.error(f"执行搜索失败: {str(e)}")
            raise
    
    def compare_search(self, query, top_k=5):
        """
        比较基础向量检索和图增强检索的结果
        
        Args:
            query (str): 查询文本
            top_k (int, optional): 返回结果数量
            
        Returns:
            tuple: (基础检索结果, 图增强检索结果)
        """
        try:
            # 基础向量检索
            vector_result = self.vector_rag.search(query, retriever_config={'top_k': top_k})
            
            # 图增强检索
            graph_result = self.vector_cypher_rag.search(query, retriever_config={'top_k': top_k})
            
            logger.info(f"成功执行比较搜索: '{query}'")
            return vector_result, graph_result
        except Exception as e:
            logger.error(f"执行比较搜索失败: {str(e)}")
            raise

# 默认GraphRAG系统实例，用于全局共享
default_graph_rag_system = None

def get_graph_rag_system():
    """获取默认GraphRAG系统实例"""
    global default_graph_rag_system
    if default_graph_rag_system is None:
        default_graph_rag_system = GraphRAGSystem()
    return default_graph_rag_system 
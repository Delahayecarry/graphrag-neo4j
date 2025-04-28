"""
RAG提示模板模块
"""

import logging
from neo4j_graphrag.generation import RagTemplate

logger = logging.getLogger(__name__)

class TemplateManager:
    """RAG提示模板管理类"""
    
    # 预定义的提示模板
    DEFAULT_TEMPLATE = '''
    根据下面的上下文回答问题。只使用上下文中的信息回答，不要添加不在上下文中的信息。

    # 问题:
    {query_text}

    # 上下文:
    {context}

    # 回答:
    '''
    
    CHINESE_TEMPLATE = '''
    根据以下提供的上下文资料，请回答用户的问题。请仅使用上下文中包含的信息，不要添加未在上下文中提及的内容。

    # 问题:
    {query_text}

    # 上下文资料:
    {context}

    # 回答:
    '''
    
    ENGLISH_TEMPLATE = '''
    Answer the question based on the context provided below. Use only information from the context and do not add information not present in the context.

    # Question:
    {query_text}

    # Context:
    {context}

    # Answer:
    '''
    
    DETAILED_TEMPLATE = '''
    基于以下上下文资料回答问题。请详细分析上下文中的信息，并给出完整、准确的回答。
    只使用上下文中包含的信息，不要添加任何未在上下文中明确提及的内容。

    # 用户问题:
    {query_text}

    # 上下文资料:
    {context}

    # 详细分析与回答:
    '''
    
    def __init__(self):
        """初始化模板管理器"""
        self.templates = {
            'default': self.create_template(self.DEFAULT_TEMPLATE),
            'chinese': self.create_template(self.CHINESE_TEMPLATE),
            'english': self.create_template(self.ENGLISH_TEMPLATE),
            'detailed': self.create_template(self.DETAILED_TEMPLATE)
        }
    
    def create_template(self, template_text, expected_inputs=None):
        """
        创建RAG提示模板
        
        Args:
            template_text (str): 模板文本
            expected_inputs (list, optional): 预期输入列表
            
        Returns:
            RagTemplate: RAG提示模板
        """
        expected_inputs = expected_inputs or ['query_text', 'context']
        return RagTemplate(template=template_text, expected_inputs=expected_inputs)
    
    def get_template(self, template_name='default'):
        """
        获取指定名称的模板
        
        Args:
            template_name (str): 模板名称
            
        Returns:
            RagTemplate: RAG提示模板
        """
        if template_name not in self.templates:
            logger.warning(f"模板 '{template_name}' 不存在，使用默认模板")
            return self.templates['default']
        return self.templates[template_name]
    
    def add_template(self, name, template_text, expected_inputs=None):
        """
        添加新模板
        
        Args:
            name (str): 模板名称
            template_text (str): 模板文本
            expected_inputs (list, optional): 预期输入列表
        """
        self.templates[name] = self.create_template(template_text, expected_inputs)
        logger.info(f"添加模板: {name}")

# 默认模板管理器实例，用于全局共享
default_template_manager = None

def get_template_manager():
    """获取默认模板管理器实例"""
    global default_template_manager
    if default_template_manager is None:
        default_template_manager = TemplateManager()
    return default_template_manager 
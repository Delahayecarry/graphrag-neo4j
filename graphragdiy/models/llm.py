"""
大语言模型(LLM)管理模块
"""

import logging
from neo4j_graphrag.llm import OpenAILLM
from config import settings

logger = logging.getLogger(__name__)

class LLMManager:
    """大语言模型管理类"""
    
    def __init__(self, model_name=None, api_key=None, base_url=None, model_params=None):
        """
        初始化LLM管理器
        
        Args:
            model_name (str, optional): 模型名称
            api_key (str, optional): API密钥
            base_url (str, optional): API基础URL
            model_params (dict, optional): 模型参数
        """
        self.model_name = model_name or settings.OPENAI_MODEL
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        
        self.model_params = model_params or {
            "response_format": {"type": "json_object"},
            "temperature": 0
        }
        
        self.llm = self._initialize_llm()
        
    def _initialize_llm(self):
        """初始化LLM实例"""
        try:
            llm = OpenAILLM(
                model_name=self.model_name,
                model_params=self.model_params,
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"成功初始化LLM模型: {self.model_name}")
            return llm
        except Exception as e:
            logger.error(f"初始化LLM模型失败: {str(e)}")
            raise
    
    def get_llm(self):
        """获取LLM实例"""
        return self.llm

# 默认LLM管理器实例，用于全局共享
default_llm_manager = None

def get_llm_manager():
    """获取默认LLM管理器实例"""
    global default_llm_manager
    if default_llm_manager is None:
        default_llm_manager = LLMManager()
    return default_llm_manager 
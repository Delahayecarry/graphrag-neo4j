"""
graphrag官方库集成模块
"""

import os
import logging
import subprocess
import shutil
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

# 检查graphrag命令是否可用
try:
    result = subprocess.run(["graphrag", "--help"], 
                           capture_output=True, 
                           check=False)
    GRAPHRAG_AVAILABLE = result.returncode == 0
except FileNotFoundError:
    GRAPHRAG_AVAILABLE = False
    logger.warning("graphrag命令不可用，请先安装graphrag包")

class GraphragIndexer:
    """graphrag官方命令行工具封装类"""
    
    def __init__(self, root_dir: str):
        """
        初始化graphrag索引构建器
        
        Args:
            root_dir (str): graphrag工作目录路径
        """
        if not GRAPHRAG_AVAILABLE:
            raise ImportError("graphrag命令不可用，请先安装graphrag包：pip install graphrag")
            
        self.root_dir = root_dir
        self.input_dir = os.path.join(root_dir, "input")
        os.makedirs(self.input_dir, exist_ok=True)
    
    def setup_workspace(self) -> bool:
        """
        初始化graphrag工作空间
        
        Returns:
            bool: 是否成功
        """
        try:
            # 检查是否已经初始化
            config_path = os.path.join(self.root_dir, "graphrag.json")
            
            if os.path.exists(config_path):
                logger.info(f"工作目录 {self.root_dir} 已初始化，跳过初始化步骤")
                
                # 即使跳过初始化，也复制环境变量文件
                project_env_path = os.path.join(os.getcwd(), ".env")
                workspace_env_path = os.path.join(self.root_dir, ".env")
                
                if os.path.exists(project_env_path):
                    shutil.copy2(project_env_path, workspace_env_path)
                    logger.info(f"已复制环境变量文件: {project_env_path} -> {workspace_env_path}")
                
                # 复制并覆盖settings.yaml文件
                project_settings_path = os.path.join(os.getcwd(), "settings.yaml")
                workspace_settings_path = os.path.join(self.root_dir, "settings.yaml")
                
                if os.path.exists(project_settings_path):
                    shutil.copy2(project_settings_path, workspace_settings_path)
                    logger.info(f"已复制并覆盖配置文件: {project_settings_path} -> {workspace_settings_path}")
                
                return True
            
            # 如果未初始化，运行graphrag init命令
            result = subprocess.run(
                ["graphrag", "init", "--root", self.root_dir],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("graphrag工作空间初始化成功")
            
            # 复制项目根目录的.env文件到工作目录
            # 这将覆盖graphrag init生成的.env文件
            project_env_path = os.path.join(os.getcwd(), ".env")
            workspace_env_path = os.path.join(self.root_dir, ".env")
            
            if os.path.exists(project_env_path):
                shutil.copy2(project_env_path, workspace_env_path)
                logger.info(f"已复制环境变量文件: {project_env_path} -> {workspace_env_path}")
            
            # 复制并覆盖settings.yaml文件
            # 这将覆盖graphrag init生成的settings.yaml文件
            project_settings_path = os.path.join(os.getcwd(), "settings.yaml")
            workspace_settings_path = os.path.join(self.root_dir, "settings.yaml")
            
            if os.path.exists(project_settings_path):
                shutil.copy2(project_settings_path, workspace_settings_path)
                logger.info(f"已复制并覆盖配置文件: {project_settings_path} -> {workspace_settings_path}")
                
            return True
        except subprocess.CalledProcessError as e:
            # 检查错误是否是"项目已初始化"
            if "Project already initialized" in e.stderr:
                logger.info(f"工作目录 {self.root_dir} 已初始化，跳过初始化步骤")
                
                # 即使跳过初始化，也复制环境变量文件
                project_env_path = os.path.join(os.getcwd(), ".env")
                workspace_env_path = os.path.join(self.root_dir, ".env")
                
                if os.path.exists(project_env_path):
                    shutil.copy2(project_env_path, workspace_env_path)
                    logger.info(f"已复制环境变量文件: {project_env_path} -> {workspace_env_path}")
                
                # 复制并覆盖settings.yaml文件
                project_settings_path = os.path.join(os.getcwd(), "settings.yaml")
                workspace_settings_path = os.path.join(self.root_dir, "settings.yaml")
                
                if os.path.exists(project_settings_path):
                    shutil.copy2(project_settings_path, workspace_settings_path)
                    logger.info(f"已复制并覆盖配置文件: {project_settings_path} -> {workspace_settings_path}")
                
                return True
            
            logger.error(f"graphrag工作空间初始化失败: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"graphrag工作空间初始化失败: {str(e)}")
            return False
    
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
            
            # 初始化工作空间
            self.setup_workspace()  # 不再检查返回值，因为即使已初始化也要继续
            
            # 运行索引构建
            # 为了确保使用正确的环境变量，我们将当前的环境变量传递给子进程
            env = os.environ.copy()
            
            result = subprocess.run(
                ["graphrag", "index", "--root", self.root_dir],
                capture_output=True,
                text=True,
                check=True,
                env=env  # 使用当前进程的环境变量
            )
            
            logger.info("graphrag索引构建成功")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"graphrag索引构建失败: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"graphrag索引构建失败: {str(e)}")
            return False
    
    def run_query(self, query: str, method: str = "global") -> str:
        """
        运行graphrag查询
        
        Args:
            query (str): 查询文本
            method (str): 查询方法，可选 "global" 或 "local"
            
        Returns:
            str: 查询结果
        """
        try:
            # 使用当前进程的环境变量
            env = os.environ.copy()
            
            result = subprocess.run(
                ["graphrag", "query", "--root", self.root_dir, 
                 "--method", method, "--query", query],
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"graphrag查询失败: {e.stderr}")
            return f"查询失败: {e.stderr}"
        except Exception as e:
            logger.error(f"graphrag查询失败: {str(e)}")
            return f"查询失败: {str(e)}"
    
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

# 导出函数，创建索引器实例
def indexer(root_dir: str) -> Optional[GraphragIndexer]:
    """
    创建graphrag索引构建器
    
    Args:
        root_dir (str): graphrag工作目录路径
        
    Returns:
        Optional[GraphragIndexer]: 索引构建器实例，如果graphrag不可用则返回None
    """
    if not GRAPHRAG_AVAILABLE:
        return None
    return GraphragIndexer(root_dir)
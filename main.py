"""
GraphRAG-Neo4j 主程序入口
基于Neo4j的知识图谱增强检索生成系统
"""

import os
import sys
import asyncio
import logging
import time
from tqdm import tqdm
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("graphrag.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# 导入自定义模块
from graphragdiy.database.neo4j_connector import get_connector
from graphragdiy.models.llm import get_llm_manager
from graphragdiy.models.embeddings import get_embedding_manager
from graphragdiy.knowledge_graph.builder import get_kg_builder
from graphragdiy.knowledge_graph.indexer import get_index_manager
from graphragdiy.knowledge_graph.retriever import get_retriever_manager
from graphragdiy.rag.graph_rag import get_graph_rag_system
from graphragdiy.visualization.graph_visualizer import get_visualizer
from config import settings


async def process_files(file_paths, kg_builder):
    """处理多个文件，构建知识图谱"""
    results = []
    
    print("\n📚 开始处理文档并构建知识图谱...")
    
    # 使用tqdm创建进度条
    progress_bar = tqdm(file_paths, desc="处理文件", unit="文件")
    
    for file_path in progress_bar:
        try:
            progress_bar.set_description(f"处理文件: {os.path.basename(file_path)}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                results.append({"file": file_path, "success": False, "error": "文件不存在"})
                continue
                
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            # 处理文件内容构建知识图谱
            result = await kg_builder.build_from_text(text)
            
            results.append({"file": file_path, "success": True, "result": result})
            logger.info(f"成功处理文件: {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
            results.append({"file": file_path, "success": False, "error": str(e)})
    
    success_count = sum(1 for r in results if r['success'])
    
    print(f"\n✅ 文档处理完成 ({success_count}/{len(file_paths)} 成功)")
    
    return results


async def main():
    try:
        print("\n🚀 GraphRAG-Neo4j 启动中...")
        start_time = time.time()
        
        # 加载环境变量
        load_dotenv()
        
        # 初始化组件
        print("\n⚙️ 初始化系统组件...")
        
        # 连接数据库
        db_connector = get_connector()
        logger.info("已连接到Neo4j数据库")
        
        # 初始化LLM
        llm_manager = get_llm_manager()
        logger.info("LLM初始化完成")
        
        # 初始化嵌入模型
        embedding_manager = get_embedding_manager()
        logger.info("嵌入模型初始化完成")
        
        # 初始化知识图谱构建器
        kg_builder = get_kg_builder()
        logger.info("知识图谱构建器初始化完成")
        
        # 设置要处理的文件
        data_dir = settings.RAW_DATA_DIR
        file_paths = []
        
        # 列出data目录中的文本文件
        for file in os.listdir(data_dir):
            if file.endswith('.txt'):
                file_paths.append(os.path.join(data_dir, file))
        
        if not file_paths:
            print(f"\n⚠️  警告: 在 {data_dir} 目录中没有找到文本文件")
            logger.warning(f"在 {data_dir} 目录中没有找到文本文件")
        else:
            # 处理文件并构建知识图谱
            results = await process_files(file_paths, kg_builder)
        
        # 创建索引
        print("\n🔍 创建向量和全文索引...")
        index_manager = get_index_manager()
        index_manager.create_all_indexes()
        logger.info("索引创建完成")
        
        # 设置检索器
        print("\n🔎 配置检索器...")
        retriever_manager = get_retriever_manager()
        vector_retriever, vector_cypher_retriever = retriever_manager.setup_retrievers()
        logger.info("检索器配置完成")
        
        # 初始化RAG系统
        print("\n🧠 初始化GraphRAG系统...")
        rag_system = get_graph_rag_system()
        logger.info("GraphRAG系统初始化完成")
        
        # 可视化知识图谱
        print("\n📊 生成知识图谱可视化...")
        visualizer = get_visualizer()
        
        # 创建交互式HTML可视化
        html_path = visualizer.create_interactive_graph(
            file_name="knowledge_graph.html",
            limit=1000  # 限制节点数量以提高性能
        )
        print(f"📈 交互式图表已保存至: {html_path}")
        
        # 创建静态PNG可视化
        png_path = visualizer.create_static_graph(
            file_name="knowledge_graph.png",
            limit=500  # 静态图表节点数量更少以提高可读性
        )
        print(f"🖼️ 静态图表已保存至: {png_path}")
        
        # 导出CSV数据
        nodes_path, edges_path = visualizer.export_csv_files()
        print(f"📄 CSV数据已导出至: {nodes_path}, {edges_path}")
        
        # 系统准备完成，开始交互模式
        end_time = time.time()
        setup_time = end_time - start_time
        print(f"\n✨ 系统初始化完成! (用时: {setup_time:.2f}秒)")
        
        # 交互式问答循环
        print("\n💬 进入交互式问答模式 (输入'exit'退出)")
        while True:
            query = input("\n🔍 请输入您的问题: ")
            if query.lower() in ['exit', 'quit', '退出']:
                break
                
            print("\n🔄 正在处理查询...")
            
            # 使用基础向量检索
            vector_start = time.time()
            vector_result = rag_system.search(query, use_graph=False)
            vector_time = time.time() - vector_start
            
            # 使用图增强检索
            graph_start = time.time()
            graph_result = rag_system.search(query, use_graph=True)
            graph_time = time.time() - graph_start
            
            print("\n📝 基础向量检索结果:")
            print(f"⏱️  处理时间: {vector_time:.2f}秒")
            print(f"{vector_result.answer}")
            
            print("\n📝 图增强检索结果:")
            print(f"⏱️  处理时间: {graph_time:.2f}秒")
            print(f"{graph_result.answer}")
            
        print("\n👋 感谢使用GraphRAG-Neo4j系统!")
        
    except Exception as e:
        logger.error(f"系统运行出错: {str(e)}")
        print(f"\n❌ 错误: {str(e)}")
        raise
    finally:
        # 关闭数据库连接
        if 'db_connector' in locals():
            db_connector.close()
            logger.info("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(main())
"""
Graphrag模式的GraphRAG系统
基于官方graphrag库的知识图谱增强检索生成系统
"""

import os
import sys
import asyncio
import logging
import time
import click
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
from graphragdiy.visualization.graph_visualizer import get_visualizer
from graphragdiy.visualization.graph_3d_visualizer import get_3d_visualizer
from graphragdiy.graphrag_official import indexer, GRAPHRAG_AVAILABLE
from config import settings

async def process_files(graphrag_indexer, file_paths):
    """处理多个文件，使用graphrag构建知识图谱"""
    results = []
    
    print("\n📚 开始处理文档并构建知识图谱...")
    
    # 使用tqdm创建进度条
    progress_bar = tqdm(file_paths, desc="处理文件", unit="文件")
    
    for file_path in progress_bar:
        try:
            file_name = os.path.basename(file_path)
            progress_bar.set_description(f"处理文件: {file_name}")
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                results.append({"file": file_path, "success": False, "error": "文件不存在"})
                continue
                
            # 复制文件到graphrag工作目录
            dest_path = os.path.join(graphrag_indexer.input_dir, file_name)
            with open(file_path, 'r', encoding='utf-8') as src, \
                 open(dest_path, 'w', encoding='utf-8') as dst:
                content = src.read()
                dst.write(content)
                
            results.append({"file": file_path, "success": True})
            logger.info(f"成功处理文件: {file_path}")
            
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
            results.append({"file": file_path, "success": False, "error": str(e)})
    
    success_count = sum(1 for r in results if r['success'])
    print(f"\n✅ 文档处理完成 ({success_count}/{len(file_paths)} 成功)")
    return results

async def graphrag_mode(data_dir, root_dir):
    """graphrag官方库模式的主要处理流程"""
    try:
        print("\n🚀 启动graphrag官方模式...")
        start_time = time.time()
        
        # 设置要处理的文件
        file_paths = []
        
        # 列出data目录中的文本文件
        if os.path.exists(data_dir):
            for file in os.listdir(data_dir):
                if file.endswith('.txt'):
                    file_paths.append(os.path.join(data_dir, file))
        
        if not file_paths:
            print(f"\n⚠️  警告: 在 {data_dir} 目录中没有找到文本文件")
            logger.warning(f"在 {data_dir} 目录中没有找到文本文件")
            return
        
        # 创建graphrag索引构建器
        print(f"\n⚙️  初始化graphrag工作目录: {root_dir}")
        graphrag_indexer = indexer(root_dir)
        if not graphrag_indexer:
            print("\n❌ 错误: 无法创建graphrag索引构建器")
            return
        
        # 使用进度条处理文件
        await process_files(graphrag_indexer, file_paths)
        
        # 初始化工作空间
        print("\n🔧 配置graphrag工作空间...")
        setup_success = graphrag_indexer.setup_workspace()
        if not setup_success:
            print("\n⚠️  警告: graphrag工作空间配置遇到问题，将尝试继续")
            
        # 运行索引构建
        print("\n🔍 开始构建知识图谱索引...")
        print("这可能需要几分钟时间，请耐心等待...")
        
        # 使用当前进程的环境变量
        index_start = time.time()
        index_success = False
        
        with tqdm(total=100, desc="构建索引", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            # 模拟进度，因为graphrag命令没有进度报告
            for i in range(10):
                pbar.update(5)
                time.sleep(0.5)
            
            # 启动索引构建
            index_process = asyncio.create_subprocess_exec(
                "graphrag", "index", "--root", root_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                # 创建子进程
                process = await index_process
                
                # 更新进度条到50%
                pbar.update(25)
                
                # 等待进程完成
                stdout, stderr = await process.communicate()
                
                # 检查返回码
                if process.returncode == 0:
                    index_success = True
                    # 完成进度条
                    pbar.update(50)
                else:
                    logger.error(f"graphrag索引构建失败: {stderr.decode()}")
                    # 停止在75%
                    pbar.update(25)
            except Exception as e:
                logger.error(f"运行graphrag index命令失败: {str(e)}")
                pbar.update(25)  # 停止在75%
        
        if index_success:
            index_time = time.time() - index_start
            print(f"\n✅ 索引构建完成! (用时: {index_time:.2f}秒)")
            
            # 计算总耗时
            end_time = time.time()
            setup_time = end_time - start_time
            print(f"\n✨ graphrag索引构建完成! (总用时: {setup_time:.2f}秒)")
            
            # 可视化知识图谱
            print("\n📊 生成知识图谱可视化...")
            
            # 创建可视化目录
            viz_output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(viz_output_dir, exist_ok=True)
            
            # visualizer = get_visualizer(mode='neo4j', root_dir=root_dir)
            
            # # 创建交互式HTML可视化
            # with tqdm(total=100, desc="生成交互式HTML可视化", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            #     pbar.update(20)
            #     html_path = visualizer.create_interactive_graph(
            #         file_name="knowledge_graph.html",
            #         limit=10000  # 限制节点数量以提高性能
            #     )
            #     pbar.update(80)
            
            # if html_path:
            #     print(f"📈 交互式图表已保存至: {html_path}")
            # else:
            #     print("⚠️ 创建交互式图表失败")
            
            # # 创建静态PNG可视化
            # with tqdm(total=100, desc="生成静态PNG可视化", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            #     pbar.update(20)
            #     png_path = visualizer.create_static_graph(
            #         file_name="knowledge_graph.png",
            #         limit=5000  # 静态图表节点数量更少以提高可读性
            #     )
            #     pbar.update(80)
            
            # if png_path:
            #     print(f"🖼️ 静态图表已保存至: {png_path}")
            # else:
            #     print("⚠️ 创建静态图表失败")
            
            # 创建3D可视化
            print("\n🌟 生成知识图谱可视化...")
            # 使用兼容层，确保使用graphrag模式而不是neo4j模式
            visualizer_3d = get_3d_visualizer(
                mode='graphrag',  # 确保使用graphrag模式
                root_dir=root_dir,
                output_dir=viz_output_dir,
                db_connector=None  # 显式设置为None，避免尝试使用Neo4j
            )
            
            # 并行生成2D和3D可视化
            print("\n🔸 生成3D可视化...")
            html_3d_path = visualizer_3d.create_3d_visualization(
                file_name="knowledge_graph_3d.html",
                limit=10000,  # 3D可视化的节点数量限制
                mode="graphrag"  # 明确传递mode参数，确保使用graphrag模式
            )
            
            # 创建2D可视化
            print("\n🔹 生成2D可视化...")
            html_2d_path = visualizer_3d.create_2d_visualization(
                file_name="knowledge_graph_2d.html",
                limit=10000,  # 2D可视化的节点数量限制
                mode="graphrag"  # 明确传递mode参数，确保使用graphrag模式
            )
            
            # 显示可视化结果路径
            if html_3d_path:
                print(f"🎮 3D交互式图表已保存至: {html_3d_path}")
            else:
                print("⚠️ 创建3D可视化失败")
                
            if html_2d_path:
                print(f"📊 2D交互式图表已保存至: {html_2d_path}")
            else:
                print("⚠️ 创建2D可视化失败")
                
            # 提供使用说明
            print("\n💡 提示: 2D图表提供更好的节点关系概览，3D图表能展示更复杂的空间关系")
            
            # # 导出CSV数据
            # with tqdm(total=100, desc="导出CSV数据", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
            #     pbar.update(30)
            #     nodes_path, edges_path = visualizer.export_csv_files()
            #     pbar.update(70)
            
            # if nodes_path and edges_path:
            #     print(f"📄 CSV数据已导出至: {nodes_path}, {edges_path}")
            # else:
            #     print("⚠️ 导出CSV数据失败")
            
            # 添加交互式查询
            print("\n💬 进入graphrag交互式查询模式 (输入'exit'退出)")
            while True:
                query = input("\n🔍 请输入您的问题: ")
                if query.lower() in ['exit', 'quit', '退出']:
                    break
                    
                print("\n🔄 正在处理查询...")
                
                # 使用graphrag global查询
                with tqdm(total=100, desc="Global查询", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
                    pbar.update(10)
                    global_start = time.time()
                    global_result = graphrag_indexer.run_query(query, method="global")
                    global_time = time.time() - global_start
                    pbar.update(90)
                
                # 使用graphrag local查询
                with tqdm(total=100, desc="Local查询", bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt}') as pbar:
                    pbar.update(10)
                    local_start = time.time()
                    local_result = graphrag_indexer.run_query(query, method="local")
                    local_time = time.time() - local_start
                    pbar.update(90)
                
                print("\n📝 Global查询结果:")
                print(f"⏱️  处理时间: {global_time:.2f}秒")
                print(f"{global_result}")
                
                print("\n📝 Local查询结果:")
                print(f"⏱️  处理时间: {local_time:.2f}秒")
                print(f"{local_result}")
            
            print("\n👋 感谢使用GraphRAG系统!")
            
        else:
            print("\n❌ graphrag索引构建失败")
            print("\n💡 或者您也可以手动使用以下命令:")
            for cmd in graphrag_indexer.get_query_commands():
                print(f"   {cmd}")
            
    except Exception as e:
        logger.error(f"graphrag模式运行出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        print(f"\n❌ 错误: {str(e)}")
        raise

@click.command()
@click.option('--data-dir', default=settings.RAW_DATA_DIR,
              help='输入数据目录路径，包含要处理的文本文件')
@click.option('--root-dir', default='./ragtest',
              help='graphrag模式的工作目录路径')
def main(data_dir, root_dir):
    """Graphrag模式的GraphRAG系统"""
    # 加载环境变量
    load_dotenv()
    
    if not GRAPHRAG_AVAILABLE:
        print("\n❌ 错误: graphrag官方库未安装，无法使用graphrag模式")
        print("请先安装graphrag: pip install graphrag")
        return
    
    try:
        asyncio.run(graphrag_mode(data_dir, root_dir))
    except KeyboardInterrupt:
        print("\n\n👋 程序已终止")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {str(e)}")
        raise

if __name__ == "__main__":
    main() 
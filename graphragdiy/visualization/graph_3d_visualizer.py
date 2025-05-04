"""
知识图谱3D可视化模块
"""

import os
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

class Graph3DVisualizer:
    """知识图谱3D可视化类"""
    
    def __init__(self, db_connector=None, output_dir=None, root_dir=None):
        """
        初始化知识图谱3D可视化器
        
        Args:
            db_connector: 数据库连接器
            output_dir (str, optional): 输出目录
            root_dir (str, optional): graphrag工作目录路径
        """
        self.db_connector = db_connector
        self.output_dir = output_dir or os.path.join(os.getcwd(), "output")
        self.root_dir = root_dir
        
        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _read_parquet_files(self, directory):
        """
        读取指定目录下的所有Parquet文件并合并
        
        Args:
            directory (str): 包含Parquet文件的目录路径
            
        Returns:
            pd.DataFrame: 合并后的DataFrame
        """
        try:
            if not os.path.exists(directory):
                logger.warning(f"目录不存在: {directory}")
                return pd.DataFrame()
                
            dataframes = []
            files = [f for f in os.listdir(directory) if f.endswith('.parquet')]
            
            if not files:
                logger.warning(f"在目录 {directory} 中未找到Parquet文件")
                return pd.DataFrame()
            
            # 使用tqdm创建进度条
            for filename in tqdm(files, desc="读取Parquet文件", unit="文件"):
                file_path = os.path.join(directory, filename)
                try:
                    df = pd.read_parquet(file_path)
                    
                    # 检查DataFrame是否包含必要的列
                    if 'source' in df.columns and 'target' in df.columns:
                        dataframes.append(df)
                        logger.info(f"已读取Parquet文件: {file_path}")
                    elif 'source' in df.columns and 'destination' in df.columns:
                        # 如果是graphrag生成的relationships文件，重命名列
                        df = df.rename(columns={'destination': 'target'})
                        dataframes.append(df)
                        logger.info(f"已读取并转换relationships文件: {file_path}")
                    elif 'source_id' in df.columns and 'target_id' in df.columns:
                        # 另一种可能的列名
                        df = df.rename(columns={'source_id': 'source', 'target_id': 'target'})
                        dataframes.append(df)
                        logger.info(f"已读取并转换source_id/target_id文件: {file_path}")
                except Exception as e:
                    logger.warning(f"读取Parquet文件出错: {file_path}: {str(e)}")
                
            if not dataframes:
                logger.warning(f"在目录 {directory} 中未找到包含所需列的Parquet文件")
                return pd.DataFrame()
                
            return pd.concat(dataframes, ignore_index=True)
        except Exception as e:
            logger.error(f"读取Parquet文件出错: {str(e)}")
            return pd.DataFrame()
    
    def _clean_dataframe(self, df):
        """
        清理DataFrame，移除无效的行并转换数据类型
        
        Args:
            df (pd.DataFrame): 输入DataFrame
            
        Returns:
            pd.DataFrame: 清理后的DataFrame
        """
        if df.empty:
            return df
            
        # 删除source和target列中的空值
        df = df.dropna(subset=['source', 'target'])
        
        # 确保source和target是字符串类型
        df['source'] = df['source'].astype(str)
        df['target'] = df['target'].astype(str)
        
        # 移除重复的边
        df = df.drop_duplicates(subset=['source', 'target'])
        
        return df
    
    def _create_knowledge_graph(self, df):
        """
        从DataFrame创建知识图谱
        
        Args:
            df (pd.DataFrame): 包含边数据的DataFrame
            
        Returns:
            nx.DiGraph: NetworkX有向图
        """
        G = nx.DiGraph()
        
        # 使用tqdm创建进度条
        for _, row in tqdm(df.iterrows(), total=len(df), desc="构建图", unit="边"):
            source = row['source']
            target = row['target']
            
            # 提取除source和target外的所有属性
            attributes = {k: v for k, v in row.items() if k not in ['source', 'target']}
            
            # 添加边和属性
            G.add_edge(source, target, **attributes)
        
        logger.info(f"已创建图：节点数={G.number_of_nodes()}, 边数={G.number_of_edges()}")
        return G
    
    def _create_node_link_trace(self, G, pos):
        """
        创建节点和边的3D轨迹
        
        Args:
            G (nx.DiGraph): NetworkX图
            pos (dict): 节点的3D坐标
            
        Returns:
            tuple: (edge_trace, node_trace)
        """
        # 创建边的轨迹
        edge_x, edge_y, edge_z = [], [], []
        edge_text = []
        edge_colors = []
        
        # 创建颜色映射字典，为不同类型的边分配不同颜色
        edge_type_colors = {}
        distinct_colors = px.colors.qualitative.Dark24  # 使用对比度更高的配色方案
        
        # 使用tqdm创建进度条
        for i, edge in enumerate(tqdm(G.edges(data=True), desc="构建边轨迹", unit="边")):
            x0, y0, z0 = pos[edge[0]]
            x1, y1, z1 = pos[edge[1]]
            
            # 创建直线连接，确保可见性
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_z.extend([z0, z1, None])
            
            # 获取边类型信息
            edge_type = edge[2].get('type', '')
            if isinstance(edge_type, str) and len(edge_type) > 0:
                edge_text.append(edge_type)
                
                # 为不同类型的边分配不同颜色
                if edge_type not in edge_type_colors:
                    color_idx = len(edge_type_colors) % len(distinct_colors)
                    edge_type_colors[edge_type] = distinct_colors[color_idx]
                
                # 每条边使用统一颜色（三个点：起点、终点、None）
                edge_colors.extend([edge_type_colors[edge_type]] * 3)
            else:
                edge_text.append('关系')
                # 使用明显的颜色，增加不透明度
                edge_colors.extend(['rgba(100,100,100,0.8)'] * 3)
        
        # 创建自定义的边轨迹，确保边线可见
        edge_trace = go.Scatter3d(
            x=edge_x, y=edge_y, z=edge_z,
            line=dict(
                color=edge_colors, 
                width=4,  # 增加线宽，使边更容易看到
            ),
            hoverinfo='text',
            text=edge_text,
            mode='lines',
            opacity=0.9,  # 增加不透明度
            showlegend=False
        )
        
        # 创建节点的轨迹
        node_x, node_y, node_z = [], [], []
        node_text = []
        node_colors = []
        node_sizes = []
        node_symbols = []
        node_hover_text = []
        
        # 创建节点类型颜色映射
        node_type_colors = {}
        node_color_scale = px.colors.qualitative.Plotly
        
        # 计算节点的度来设置大小
        degrees = dict(G.degree())
        max_degree = max(degrees.values()) if degrees else 1
        min_degree = min(degrees.values()) if degrees else 1
        
        # 使用tqdm创建进度条
        for node in tqdm(G.nodes(data=True), desc="构建节点轨迹", unit="节点"):
            x, y, z = pos[node[0]]
            node_x.append(x)
            node_y.append(y)
            node_z.append(z)
            
            # 获取节点属性，构建悬停文本
            node_label = node[0]
            node_type = node[1].get('type', node[1].get('labels', 'unknown'))
            node_name = node[1].get('name', node_label)
            
            # 为每种节点类型分配颜色
            if isinstance(node_type, str):
                if node_type not in node_type_colors:
                    color_idx = len(node_type_colors) % len(node_color_scale)
                    node_type_colors[node_type] = node_color_scale[color_idx]
                node_colors.append(node_type_colors[node_type])
            else:
                node_colors.append('rgba(50,50,100,0.9)')  # 使用更鲜明的颜色
            
            # 根据节点度数设置大小，使重要节点更大
            degree = degrees.get(node[0], 0)
            size_factor = 8 + 15 * (degree - min_degree) / (max_degree - min_degree + 0.01)  # 增加最小尺寸
            node_sizes.append(size_factor)
            
            # 设置节点形状，根据节点类型使用不同符号
            # Plotly 3D散点图的符号选项较少，通常只有'circle', 'square', 'diamond', 'cross', 'x'
            symbols = ['circle', 'square', 'diamond', 'cross', 'x']
            if isinstance(node_type, str):
                symbol_idx = hash(node_type) % len(symbols)
                node_symbols.append(symbols[symbol_idx])
            else:
                node_symbols.append('circle')
            
            # 构建格式良好的悬停文本
            hover_text = f"<b>{node_name}</b><br>"
            hover_text += f"<i>Type:</i> {node_type}<br>"
            hover_text += f"<i>ID:</i> {node_label}<br>"
            hover_text += f"<i>Connections:</i> {degree}<br>"
            
            # 添加其他属性到悬停文本
            for key, value in node[1].items():
                if key not in ['name', 'type', 'labels', 'embedding', 'vector'] and isinstance(value, (str, int, float)):
                    # 确保值不是太长的文本
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:97] + "..."
                    hover_text += f"<i>{key}:</i> {value}<br>"
                    
            node_hover_text.append(hover_text)
            
            # 简短的节点文本标签
            node_text.append(node_name)
        
        # 创建自定义节点轨迹
        node_trace = go.Scatter3d(
            x=node_x, y=node_y, z=node_z,
            mode='markers+text',
            text=node_text,
            textposition="bottom center",
            textfont=dict(
                family="Arial",
                size=12,  # 增加文字大小
                color="rgba(0,0,0,0.9)"  # 增加文字对比度
            ),
            hoverinfo='text',
            hovertext=node_hover_text,
            marker=dict(
                size=node_sizes,
                color=node_colors,
                symbol=node_symbols,
                line=dict(width=1.5, color='rgba(255,255,255,0.8)'),  # 加粗边框
                opacity=0.95  # 增加不透明度
            )
        )
        
        # 创建图例
        legend_traces = []
        for edge_type, color in edge_type_colors.items():
            legend_trace = go.Scatter3d(
                x=[None], y=[None], z=[None],
                mode='lines',
                name=f'关系: {edge_type}',
                line=dict(color=color, width=6),  # 增加图例线宽
                showlegend=True
            )
            legend_traces.append(legend_trace)
        
        for node_type, color in node_type_colors.items():
            legend_trace = go.Scatter3d(
                x=[None], y=[None], z=[None],
                mode='markers',
                name=f'节点: {node_type}',
                marker=dict(color=color, size=12),  # 增加图例标记大小
                showlegend=True
            )
            legend_traces.append(legend_trace)
        
        return [edge_trace, node_trace] + legend_traces
    
    def _fetch_graph_data_neo4j(self, limit=1000, node_labels=None, rel_types=None):
        """
        从Neo4j获取图数据
        
        Args:
            limit (int): 最大节点数量
            node_labels (list): 节点标签过滤
            rel_types (list): 关系类型过滤
            
        Returns:
            pd.DataFrame: 边DataFrame
        """
        if not self.db_connector:
            logger.error("Neo4j连接器未初始化")
            return pd.DataFrame()
            
        # 构建节点标签过滤条件
        label_filter = ""
        if node_labels and len(node_labels) > 0:
            label_list = [f":{label}" for label in node_labels]
            label_filter = " OR ".join([f"n{label}" for label in label_list])
            label_filter = f"WHERE {label_filter} "
        
        # 构建关系类型过滤条件
        rel_filter = ""
        if rel_types and len(rel_types) > 0:
            rel_list = [f":{rel_type}" for rel_type in rel_types]
            rel_filter = "|".join(rel_list)
            rel_filter = f"[r{rel_filter}]"
        else:
            rel_filter = "[r]"
        
        # 获取节点
        node_query = f"""
        MATCH (n)
        {label_filter}
        RETURN n
        LIMIT {limit}
        """
        
        try:
            node_result = self.db_connector.execute_query(node_query)
            
            # 提取节点ID
            node_ids = [record["n"].element_id for record in node_result.records]
            
            # 获取关系
            rel_query = f"""
            MATCH (n)-{rel_filter}->(m)
            WHERE id(n) in $node_ids AND id(m) in $node_ids
            RETURN id(n) as source, id(m) as target, type(r) as type
            """
            
            rel_result = self.db_connector.execute_query(rel_query, {"node_ids": node_ids})
            
            # 转换为DataFrame
            edges_data = []
            for record in rel_result.records:
                edge = {
                    'source': str(record["source"]),
                    'target': str(record["target"]),
                    'type': record["type"]
                }
                edges_data.append(edge)
                
            return pd.DataFrame(edges_data)
        except Exception as e:
            logger.error(f"从Neo4j获取图数据失败: {str(e)}")
            return pd.DataFrame()
    
    def _fetch_graph_data_graphrag(self):
        """
        从graphrag获取图数据
        
        Returns:
            pd.DataFrame: 边DataFrame
        """
        if not self.root_dir:
            logger.error("graphrag工作目录未指定")
            return pd.DataFrame()
            
        # 尝试从多个可能的位置查找数据文件
        possible_data_files = [
            # 1. 标准的graphrag输出目录中的文件
            os.path.join(self.root_dir, "output", "relationships.parquet"),
            os.path.join(self.root_dir, "output", "edges.parquet"),
            os.path.join(self.root_dir, "output", "graph_data.parquet"),
            # 2. root目录下的文件
            os.path.join(self.root_dir, "relationships.parquet"),
            os.path.join(self.root_dir, "edges.parquet"),
            # 3. output目录下的文件
            os.path.join(self.output_dir, "edges.csv"),
            os.path.join(self.output_dir, "relationships.csv"),
            os.path.join(self.output_dir, "relationships.parquet"),
            # 4. 当前工作目录下的文件
            os.path.join(os.getcwd(), "output", "edges.csv"),
            os.path.join(os.getcwd(), "output", "relationships.parquet")
        ]
        
        print(f"🔍 正在尝试查找图数据文件...")
        
        # 尝试读取可能的数据文件
        for file_path in possible_data_files:
            if os.path.exists(file_path):
                print(f"🔍 发现数据文件: {file_path}")
                try:
                    # 根据文件扩展名判断如何读取
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path)
                    else:  # .parquet
                        df = pd.read_parquet(file_path)
                        
                    # 检查数据是否有效
                    if df.empty:
                        logger.warning(f"文件为空: {file_path}")
                        continue
                    
                    # 列名规范化映射
                    column_mappings = {
                        'destination': 'target',
                        'dst': 'target',
                        'target_id': 'target',
                        'to': 'target',
                        'to_id': 'target',
                        'end': 'target',
                        
                        'src': 'source',
                        'source_id': 'source',
                        'from': 'source',
                        'from_id': 'source',
                        'start': 'source',
                        
                        'relationship': 'type',
                        'relation': 'type',
                        'rel_type': 'type',
                        'edge_type': 'type',
                    }
                    
                    # 重命名列
                    for old_col, new_col in column_mappings.items():
                        if old_col in df.columns and new_col not in df.columns:
                            df = df.rename(columns={old_col: new_col})
                        
                    # 处理列名
                    if 'source' in df.columns and 'target' in df.columns:
                        logger.info(f"已读取数据文件: {file_path}，共{len(df)}行")
                        print(f"✅ 成功读取图数据，共{len(df)}行")
                        
                        # 确保type列存在
                        if 'type' not in df.columns:
                            # 尝试从其他列获取关系类型
                            for col in df.columns:
                                if col.lower() in ['relationship', 'relation', 'predicate', 'rel_type', 'edge_type']:
                                    df['type'] = df[col]
                                    print(f"📝 从列 '{col}' 获取关系类型")
                                    break
                            else:
                                # 如果找不到关系类型列，使用默认值
                                df['type'] = '关联'
                                print(f"📝 未找到关系类型列，使用默认值 '关联'")
                        
                        return df
                except Exception as e:
                    logger.warning(f"读取文件失败 {file_path}: {str(e)}")
                    print(f"⚠️ 读取文件失败: {str(e)}")
        
        # 如果单个文件读取失败，尝试读取目录中的所有Parquet文件
        possible_dirs = [
            os.path.join(self.root_dir, "output"),
            self.root_dir,
            self.output_dir,
            os.path.join(os.getcwd(), "output")
        ]
        
        for directory in possible_dirs:
            if not os.path.exists(directory):
                continue
                
            print(f"🔍 尝试从目录读取数据: {directory}")
            df = self._read_parquet_files(directory)
            
            if not df.empty:
                print(f"✅ 成功从目录读取图数据，共{len(df)}行")
                return df
        
        # 生成示例数据作为最后的备选
        try:
            print("⚠️ 未能找到图数据，生成示例数据用于演示...")
            df = self._generate_sample_data()
            if not df.empty:
                print(f"✅ 已生成示例图数据，共{len(df)}行")
                return df
        except Exception as e:
            logger.error(f"生成示例数据失败: {str(e)}")
            
        print("❌ 无法获取有效的图数据")
        return pd.DataFrame()
        
    def _generate_sample_data(self):
        """生成示例图数据用于展示"""
        # 创建10个节点和15条边的小型示例图
        nodes = [f"节点{i}" for i in range(10)]
        edges = []
        
        # 创建一些连接
        for i in range(9):
            edges.append({"source": f"节点{i}", "target": f"节点{i+1}", "type": "连接到"})
        
        # 添加一些交叉连接
        edges.append({"source": "节点0", "target": "节点5", "type": "引用"})
        edges.append({"source": "节点1", "target": "节点7", "type": "引用"})
        edges.append({"source": "节点2", "target": "节点6", "type": "属于"})
        edges.append({"source": "节点3", "target": "节点8", "type": "包含"})
        edges.append({"source": "节点4", "target": "节点9", "type": "关联"})
        edges.append({"source": "节点5", "target": "节点2", "type": "依赖"})
        
        return pd.DataFrame(edges)
    
    def create_3d_visualization(self, file_name="knowledge_graph_3d.html", limit=1000,
                               mode="neo4j", node_labels=None, rel_types=None):
        """
        创建3D交互式知识图谱可视化
        
        Args:
            file_name (str): 输出文件名
            limit (int): 最大节点数量限制
            mode (str): 数据源模式，'neo4j' 或 'graphrag'
            node_labels (list): 节点标签过滤（仅Neo4j模式）
            rel_types (list): 关系类型过滤（仅Neo4j模式）
            
        Returns:
            str: 输出文件路径，如果失败则返回None
        """
        try:
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)
            output_path = os.path.join(self.output_dir, file_name)
            
            # 根据模式获取图数据
            print(f"🔄 正在获取{mode}模式的图数据...")
            if mode == "neo4j":
                df = self._fetch_graph_data_neo4j(limit, node_labels, rel_types)
            else:  # graphrag模式
                df = self._fetch_graph_data_graphrag()
            
            # 检查数据是否有效
            if df.empty:
                logger.error("无法获取有效的图数据")
                print("❌ 无法获取有效的图数据，无法创建可视化")
                return None
            
            # 清理数据
            print("🔄 正在处理图数据...")
            df = self._clean_dataframe(df)
            
            if df.empty:
                logger.warning("清理后的数据为空")
                print("❌ 清理后的图数据为空，无法创建可视化")
                return None
            
            # 创建知识图谱
            print("🔄 正在构建知识图谱...")
            G = self._create_knowledge_graph(df)
            
            if G.number_of_nodes() == 0:
                logger.warning("图为空，无法可视化")
                print("❌ 图为空，无法创建可视化")
                return None
            
            # 限制节点数量
            if G.number_of_nodes() > limit:
                print(f"⚠️ 图节点数量({G.number_of_nodes()})超过限制({limit})，将进行截断")
                nodes = list(G.nodes())[:limit]
                G = G.subgraph(nodes).copy()
            
            # 创建3D布局
            print("🔄 正在生成3D布局...")
            # 使用改进的3D布局算法，增加k值使节点分布更均匀
            pos = nx.spring_layout(G, dim=3, k=3/(G.number_of_nodes()**0.4), iterations=70, seed=42)
            
            # 创建节点和边的轨迹
            print("🔄 正在生成可视化元素...")
            traces = self._create_node_link_trace(G, pos)
            
            # 创建更现代化的图表
            fig = go.Figure(data=traces)
            
            # 更新3D场景布局 - 更现代的设计
            fig.update_layout(
                scene=dict(
                    xaxis=dict(
                        showticklabels=False, 
                        showgrid=False, 
                        zeroline=False, 
                        showbackground=True,
                        backgroundcolor='rgba(240,240,240,0.95)',
                        title=''
                    ),
                    yaxis=dict(
                        showticklabels=False, 
                        showgrid=False, 
                        zeroline=False, 
                        showbackground=True,
                        backgroundcolor='rgba(240,240,240,0.95)',
                        title=''
                    ),
                    zaxis=dict(
                        showticklabels=False, 
                        showgrid=False, 
                        zeroline=False, 
                        showbackground=True,
                        backgroundcolor='rgba(240,240,240,0.95)',
                        title=''
                    ),
                    bgcolor='rgba(240,240,240,0.95)',
                    aspectmode='cube'
                ),
                scene_camera=dict(
                    eye=dict(x=1.8, y=1.8, z=1.5),
                    up=dict(x=0, y=0, z=1),
                    center=dict(x=0, y=0, z=0)
                ),
                title=dict(
                    text="3D知识图谱可视化",
                    x=0.5,
                    y=0.98,
                    font=dict(
                        size=24,
                        family="Arial",
                        color="rgba(50,50,50,0.9)"
                    )
                ),
                margin=dict(t=100, b=0, l=0, r=0),
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1
                ),
                paper_bgcolor='rgba(255,255,255,1)',
                plot_bgcolor='rgba(255,255,255,1)',
                showlegend=True,
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Arial"
                )
            )
            
            # 添加注释和辅助信息
            fig.add_annotation(
                text="由GraphRAG DIY生成",
                xref="paper", yref="paper",
                x=0.01, y=0.01,
                showarrow=False,
                font=dict(
                    family="Arial",
                    size=12,
                    color="rgba(150,150,150,0.9)"
                )
            )
            
            # 添加控制面板说明
            fig.add_annotation(
                text="拖动旋转 | 滚轮缩放 | 双击重置视图",
                xref="paper", yref="paper",
                x=0.99, y=0.01,
                showarrow=False,
                align="right",
                font=dict(
                    family="Arial",
                    size=12,
                    color="rgba(150,150,150,0.9)"
                )
            )
            
            # 添加更多的交互配置
            config = {
                'displayModeBar': True,
                'scrollZoom': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['toImage', 'resetCameraLastSave'],
                'modeBarButtonsToAdd': ['drawline', 'eraseshape']
            }
            
            # 保存为HTML文件
            print("🔄 正在保存可视化结果...")
            fig.write_html(
                output_path,
                include_plotlyjs='cdn',
                include_mathjax='cdn',
                full_html=True,
                config=config
            )
            
            logger.info(f"成功创建3D交互式知识图谱: {output_path}")
            print(f"🎮 3D交互式图表已保存至: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"创建3D可视化失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"❌ 创建3D可视化失败: {str(e)}")
            return None

    def create_2d_visualization(self, file_name="knowledge_graph_2d.html", limit=1000,
                               mode="graphrag", node_labels=None, rel_types=None):
        """
        创建2D交互式知识图谱可视化
        
        Args:
            file_name (str): 输出文件名
            limit (int): 最大节点数量限制
            mode (str): 数据源模式，'neo4j' 或 'graphrag'
            node_labels (list): 节点标签过滤（仅Neo4j模式）
            rel_types (list): 关系类型过滤（仅Neo4j模式）
            
        Returns:
            str: 输出文件路径，如果失败则返回None
        """
        try:
            # 确保正确导入所需的库
            import networkx as nx
            import numpy as np
            import plotly.graph_objects as go
            import plotly.express as px
            
            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)
            output_path = os.path.join(self.output_dir, file_name)
            
            # 根据模式获取图数据
            print(f"🔄 正在获取{mode}模式的图数据...")
            if mode == "neo4j":
                df = self._fetch_graph_data_neo4j(limit, node_labels, rel_types)
            else:  # graphrag模式
                df = self._fetch_graph_data_graphrag()
            
            # 检查数据是否有效
            if df.empty:
                logger.error("无法获取有效的图数据")
                print("❌ 无法获取有效的图数据，无法创建可视化")
                return None
            
            # 清理数据
            print("🔄 正在处理图数据...")
            df = self._clean_dataframe(df)
            
            if df.empty:
                logger.warning("清理后的数据为空")
                print("❌ 清理后的图数据为空，无法创建可视化")
                return None
            
            # 创建知识图谱
            print("🔄 正在构建知识图谱...")
            G = self._create_knowledge_graph(df)
            
            if G.number_of_nodes() == 0:
                logger.warning("图为空，无法可视化")
                print("❌ 图为空，无法创建可视化")
                return None
            
            # 限制节点数量
            if G.number_of_nodes() > limit:
                print(f"⚠️ 图节点数量({G.number_of_nodes()})超过限制({limit})，将进行截断")
                nodes = list(G.nodes())[:limit]
                G = G.subgraph(nodes).copy()
            
            # 创建2D布局
            print("🔄 正在生成2D布局...")
            pos = nx.spring_layout(G, k=0.5/np.sqrt(G.number_of_nodes()), seed=42)
            
            # 创建2D图表
            fig = go.Figure()
            
            # 为不同类型的边创建不同颜色
            edge_types = {}
            edge_colors = px.colors.qualitative.Dark24
            
            # 添加边
            print("🔄 正在构建边...")
            for i, (source, target, data) in enumerate(G.edges(data=True)):
                x0, y0 = pos[source]
                x1, y1 = pos[target]
                edge_type = data.get('type', '关联')
                
                # 为每种边类型分配颜色
                if edge_type not in edge_types:
                    color_idx = len(edge_types) % len(edge_colors)
                    edge_types[edge_type] = edge_colors[color_idx]
                
                color = edge_types[edge_type]
                
                # 计算稍微弯曲的边线以避免重叠
                curve_factor = 0.2
                if i % 2 == 0:
                    # 计算向量的法线
                    dx = x1 - x0
                    dy = y1 - y0
                    norm = np.sqrt(dx*dx + dy*dy)
                    if norm > 0:
                        # 正交向量
                        nx = -dy / norm
                        ny = dx / norm
                        # 控制点
                        cx = (x0 + x1) / 2 + curve_factor * nx
                        cy = (y0 + y1) / 2 + curve_factor * ny
                    else:
                        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                else:
                    # 计算向量的法线 (反方向)
                    dx = x1 - x0
                    dy = y1 - y0
                    norm = np.sqrt(dx*dx + dy*dy)
                    if norm > 0:
                        # 反方向的正交向量
                        nx = dy / norm
                        ny = -dx / norm
                        # 控制点
                        cx = (x0 + x1) / 2 + curve_factor * nx
                        cy = (y0 + y1) / 2 + curve_factor * ny
                    else:
                        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                
                # 创建二次贝塞尔曲线
                t = np.linspace(0, 1, 50)
                # 贝塞尔曲线公式: B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
                bx = (1-t)**2 * x0 + 2*(1-t)*t * cx + t**2 * x1
                by = (1-t)**2 * y0 + 2*(1-t)*t * cy + t**2 * y1
                
                edge_trace = go.Scatter(
                    x=bx, y=by,
                    line=dict(width=2, color=color),
                    hoverinfo='text',
                    text=edge_type,
                    mode='lines',
                    showlegend=False,
                    opacity=0.8
                )
                fig.add_trace(edge_trace)
                
                # 添加箭头表示有向边
                arrow_size = 0.03
                # 获取曲线末端的切线方向
                end_idx = -2  # 倒数第二个点，避免最后一点可能的数值问题
                dx = bx[end_idx] - bx[end_idx-1]
                dy = by[end_idx] - by[end_idx-1]
                norm = np.sqrt(dx*dx + dy*dy)
                if norm > 0:
                    ux = dx / norm
                    uy = dy / norm
                else:
                    ux, uy = 0, 0
                
                # 箭头尖端
                tip_x = bx[-1]
                tip_y = by[-1]
                
                # 箭头两侧点
                arrow_x = [
                    tip_x - arrow_size * (ux + 0.5*uy),
                    tip_x,
                    tip_x - arrow_size * (ux - 0.5*uy),
                ]
                arrow_y = [
                    tip_y - arrow_size * (uy - 0.5*ux),
                    tip_y,
                    tip_y - arrow_size * (uy + 0.5*ux),
                ]
                
                # 添加箭头
                arrow_trace = go.Scatter(
                    x=arrow_x, y=arrow_y,
                    line=dict(width=2, color=color),
                    fill='toself',
                    fillcolor=color,
                    hoverinfo='none',
                    mode='lines',
                    showlegend=False,
                    opacity=0.8
                )
                fig.add_trace(arrow_trace)
            
            # 添加节点
            print("🔄 正在构建节点...")
            node_types = {}
            node_colors = px.colors.qualitative.Plotly
            node_x = []
            node_y = []
            node_text = []
            node_color = []
            node_size = []
            hover_texts = []
            
            # 计算节点度数范围
            degrees = dict(G.degree())
            max_degree = max(degrees.values()) if degrees else 1
            min_degree = min(degrees.values()) if degrees else 1
            
            for node, data in G.nodes(data=True):
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                # 获取节点类型和名称
                node_type = data.get('type', data.get('labels', 'unknown'))
                node_name = data.get('name', node)
                node_text.append(node_name)
                
                # 为每种节点类型分配颜色
                if node_type not in node_types:
                    color_idx = len(node_types) % len(node_colors)
                    node_types[node_type] = node_colors[color_idx]
                
                node_color.append(node_types[node_type])
                
                # 根据连接数调整节点大小
                degree = degrees.get(node, 0)
                size = 15 + 20 * (degree - min_degree) / (max_degree - min_degree + 0.01)
                node_size.append(size)
                
                # 准备悬停文本
                hover_text = f"<b>{node_name}</b><br>"
                hover_text += f"<i>类型:</i> {node_type}<br>"
                hover_text += f"<i>ID:</i> {node}<br>"
                hover_text += f"<i>连接数:</i> {degree}<br>"
                
                # 添加其他属性
                for key, val in data.items():
                    if key not in ['name', 'type', 'labels', 'embedding', 'vector']:
                        if isinstance(val, str) and len(val) > 100:
                            val = val[:97] + "..."
                        hover_text += f"<i>{key}:</i> {val}<br>"
                
                hover_texts.append(hover_text)
            
            # 添加节点到图表
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                marker=dict(
                    size=node_size,
                    color=node_color,
                    line=dict(width=1.5, color='white')
                ),
                text=node_text,
                textposition="bottom center",
                hoverinfo="text",
                hovertext=hover_texts,
                showlegend=False
            )
            fig.add_trace(node_trace)
            
            # 添加图例
            for edge_type, color in edge_types.items():
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='lines',
                    name=f'关系: {edge_type}',
                    line=dict(color=color, width=3),
                    showlegend=True
                ))
            
            for node_type, color in node_types.items():
                fig.add_trace(go.Scatter(
                    x=[None], y=[None],
                    mode='markers',
                    name=f'节点: {node_type}',
                    marker=dict(color=color, size=10),
                    showlegend=True
                ))
            
            # 更新布局
            fig.update_layout(
                title=dict(
                    text="2D知识图谱可视化",
                    x=0.5,
                    y=0.98,
                    font=dict(
                        size=24,
                        family="Arial",
                        color="rgba(50,50,50,0.9)"
                    )
                ),
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="rgba(0,0,0,0.2)",
                    borderwidth=1
                ),
                margin=dict(t=100, b=20, l=20, r=20),
                hovermode='closest',
                paper_bgcolor='white',
                plot_bgcolor='#f9f9f9',
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False
                ),
                annotations=[
                    dict(
                        text="由GraphRAG DIY生成",
                        xref="paper", yref="paper",
                        x=0.01, y=0.01,
                        showarrow=False,
                        font=dict(
                            family="Arial",
                            size=12,
                            color="rgba(150,150,150,0.9)"
                        )
                    ),
                    dict(
                        text="拖动节点重新定位 | 滚轮缩放 | 双击重置视图",
                        xref="paper", yref="paper",
                        x=0.99, y=0.01,
                        showarrow=False,
                        align="right",
                        font=dict(
                            family="Arial",
                            size=12,
                            color="rgba(150,150,150,0.9)"
                        )
                    )
                ]
            )
            
            # 保存为HTML文件
            print("🔄 正在保存可视化结果...")
            config = {
                'displayModeBar': True,
                'scrollZoom': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['toImage', 'resetCameraLastSave'],
                'modeBarButtonsToAdd': ['drawline', 'eraseshape'],
                'editable': True  # 允许拖动节点
            }
            
            fig.write_html(
                output_path,
                include_plotlyjs='cdn',
                include_mathjax='cdn',
                full_html=True,
                config=config
            )
            
            logger.info(f"成功创建2D交互式知识图谱: {output_path}")
            print(f"🎮 2D交互式图表已保存至: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"创建2D可视化失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            print(f"❌ 创建2D可视化失败: {str(e)}")
            return None

# 获取3D可视化器函数
def get_3d_visualizer(mode='graphrag', root_dir=None, db_connector=None, output_dir=None):
    """
    创建3D可视化器实例
    
    Args:
        mode (str): 可视化模式，'neo4j' 或 'graphrag'
        root_dir (str, optional): graphrag工作目录路径
        db_connector: 数据库连接器
        output_dir (str, optional): 输出目录
        
    Returns:
        Graph3DVisualizer: 3D可视化器实例
    """
    # 将默认模式改为graphrag
    if mode == 'graphrag':
        if not root_dir:
            logger.warning("graphrag模式未指定root_dir参数，使用默认值")
            root_dir = './ragtest'
        # 确保在graphrag模式下不传递db_connector
        return Graph3DVisualizer(db_connector=None, output_dir=output_dir, root_dir=root_dir)
    else:
        return Graph3DVisualizer(db_connector=db_connector, output_dir=output_dir)

# 主函数示例
def main():
    """
    主函数，用于独立运行时测试可视化功能
    """
    try:
        # 默认使用graphrag模式
        root_dir = './ragtest'
        if os.path.exists(root_dir):
            print("🚀 启动3D可视化器示例...")
            visualizer = get_3d_visualizer(mode='graphrag', root_dir=root_dir)
            visualizer.create_3d_visualization(file_name="knowledge_graph_3d.html", limit=5000)
        else:
            print(f"❌ 错误: 目录 {root_dir} 不存在")
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    main() 
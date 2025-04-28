"""
知识图谱可视化模块
"""

import os
import logging
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib
from pyvis.network import Network
from config import settings
from graphragdiy.database.neo4j_connector import get_connector
import colorsys

logger = logging.getLogger(__name__)

class GraphVisualizer:
    """知识图谱可视化类"""
    
    def __init__(self, db_connector=None, output_dir=None):
        """
        初始化知识图谱可视化器
        
        Args:
            db_connector: 数据库连接器
            output_dir (str, optional): 输出目录
        """
        self.db_connector = db_connector or get_connector()
        self.output_dir = output_dir or settings.VIZ_OUTPUT_DIR
        
        # 设置中文字体支持
        try:
            matplotlib.rcParams['font.family'] = ['Source Han Sans CN', 'sans-serif']
        except:
            matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'Microsoft YaHei', 'Arial Unicode MS']
            matplotlib.rcParams['axes.unicode_minus'] = False
    
    def _fetch_graph_data(self, limit=1000, node_labels=None, rel_types=None):
        """
        从Neo4j获取图数据
        
        Args:
            limit (int, optional): 限制节点数量
            node_labels (list, optional): 节点标签过滤
            rel_types (list, optional): 关系类型过滤
            
        Returns:
            tuple: (nodes, relationships)
        """
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
        
        node_result = self.db_connector.execute_query(node_query)
        
        # 获取关系
        rel_query = f"""
        MATCH (n)-{rel_filter}->(m)
        WHERE id(n) in $node_ids AND id(m) in $node_ids
        RETURN n, r, m
        """
        
        # 提取节点ID
        node_ids = [record["n"].element_id for record in node_result.records]
        
        rel_result = self.db_connector.execute_query(rel_query, {"node_ids": node_ids})
        
        return node_result.records, rel_result.records
    
    def _create_networkx_graph(self, nodes, relationships):
        """
        创建NetworkX图
        
        Args:
            nodes: 节点数据
            relationships: 关系数据
            
        Returns:
            nx.DiGraph: NetworkX有向图
        """
        G = nx.DiGraph()
        
        # 添加节点
        for record in nodes:
            node = record["n"]
            node_id = node.element_id
            node_labels = list(node.labels)
            
            # 处理节点属性
            node_attrs = dict(node.items())
            
            # 确保节点有名称
            if "name" not in node_attrs:
                for key, value in node_attrs.items():
                    if key != "embedding" and isinstance(value, str) and len(value) < 100:
                        node_attrs["name"] = value
                        break
            
            if "name" not in node_attrs:
                node_attrs["name"] = f"Node-{node_id}"
            
            # 添加标签信息
            node_attrs["labels"] = ";".join(node_labels)
            
            # 添加节点
            G.add_node(node_id, **node_attrs)
        
        # 添加边
        for record in relationships:
            start_node = record["n"]
            rel = record["r"]
            end_node = record["m"]
            
            start_id = start_node.element_id
            end_id = end_node.element_id
            rel_type = rel.type
            
            # 处理关系属性
            rel_attrs = dict(rel.items())
            rel_attrs["type"] = rel_type
            
            # 添加边
            G.add_edge(start_id, end_id, **rel_attrs)
        
        return G
    
    def _generate_color_palette(self, n):
        """
        生成和谐的颜色调色板
        
        Args:
            n (int): 需要的颜色数量
            
        Returns:
            list: 颜色列表
        """
        colors = []
        for i in range(n):
            # 使用黄金比例来生成均匀分布的色相值
            hue = (i * 0.618033988749895) % 1
            # 使用固定的饱和度和明度以确保颜色的和谐性
            saturation = 0.6 + (i % 3) * 0.1  # 在0.6-0.8之间变化
            value = 0.85 - (i % 3) * 0.1      # 在0.65-0.85之间变化
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            # 转换为十六进制颜色代码
            hex_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
            )
            colors.append(hex_color)
        return colors

    def create_interactive_graph(self, file_name="knowledge_graph.html", limit=1000, 
                               node_labels=None, rel_types=None, height="800px", width="100%"):
        """
        创建交互式知识图谱
        
        Args:
            file_name (str, optional): 输出文件名
            limit (int, optional): 限制节点数量
            node_labels (list, optional): 节点标签过滤
            rel_types (list, optional): 关系类型过滤
            height (str, optional): 图表高度
            width (str, optional): 图表宽度
            
        Returns:
            str: 输出文件路径
        """
        try:
            # 获取图数据
            nodes, relationships = self._fetch_graph_data(limit, node_labels, rel_types)
            
            # 创建NetworkX图
            G = self._create_networkx_graph(nodes, relationships)
            
            # 创建Pyvis网络对象，使用优雅的背景色
            nt = Network(height=height, width=width, bgcolor="#fafafa", 
                        font_color="#2c3e50", directed=True)
            
            # 配置物理布局参数以获得更流畅的动画效果
            nt.barnes_hut(
                spring_length=200,
                spring_strength=0.015,
                damping=0.09,
                gravity=-2000
            )
            
            # 获取节点类型并生成和谐的颜色方案
            node_types = {}
            for node, attrs in G.nodes(data=True):
                labels = attrs.get('labels', '')
                primary_label = labels.split(';')[0] if labels else 'Unknown'
                if primary_label not in node_types:
                    node_types[primary_label] = len(node_types)
            
            # 使用新的颜色生成方法
            colors = self._generate_color_palette(len(node_types))
            color_map = {label: colors[i] for i, label in enumerate(node_types.keys())}
            
            # 添加节点，使用改进的视觉效果
            for node_id, attrs in G.nodes(data=True):
                node_name = attrs.get('name', f"Node-{node_id}")
                labels = attrs.get('labels', '')
                primary_label = labels.split(';')[0] if labels else 'Unknown'
                
                # 创建现代风格的工具提示
                title = f"""
                <div style='
                    background-color: rgba(255, 255, 255, 0.95);
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    max-width: 300px;
                    font-family: "Helvetica Neue", Arial, sans-serif;
                '>
                    <div style='
                        font-size: 16px;
                        font-weight: 600;
                        color: {color_map[primary_label]};
                        margin-bottom: 8px;
                    '>{node_name}</div>
                    <div style='
                        font-size: 14px;
                        color: #666;
                        margin-bottom: 12px;
                    '><span style='color: #999'>类型:</span> {primary_label}</div>
                    <div style='font-size: 14px; color: #666;'>
                """
                
                # 添加属性到工具提示
                for attr_key, attr_val in attrs.items():
                    if attr_key not in ['name', 'labels'] and not attr_key == 'embedding':
                        if attr_val and len(str(attr_val)) < 100:
                            title += f"<div style='margin: 4px 0;'><span style='color: #999'>{attr_key}:</span> {attr_val}</div>"
                
                title += "</div></div>"
                
                # 添加节点到网络，使用改进的视觉样式
                nt.add_node(
                    node_id,
                    label=node_name,
                    title=title,
                    color={
                        'background': color_map[primary_label],
                        'border': self._adjust_color(color_map[primary_label], -0.2),
                        'highlight': {
                            'background': self._adjust_color(color_map[primary_label], 0.1),
                            'border': self._adjust_color(color_map[primary_label], -0.1)
                        }
                    },
                    font={'color': '#ffffff', 'size': 14},
                    size=30,
                    borderWidth=2,
                    shadow={'enabled': True, 'size': 5, 'x': 2, 'y': 2}
                )
            
            # 添加边，使用优雅的样式
            for u, v, attrs in G.edges(data=True):
                edge_type = attrs.get('type', '')
                nt.add_edge(
                    u, v,
                    title=f"<div style='padding: 8px; background: rgba(255,255,255,0.9); border-radius: 4px;'>{edge_type}</div>",
                    label=edge_type,
                    arrows={
                        'to': {
                            'enabled': True,
                            'scaleFactor': 0.5,
                            'type': 'arrow'
                        }
                    },
                    color={'color': '#666666', 'highlight': '#333333'},
                    width=1.5,
                    smooth={'type': 'curvedCW', 'roundness': 0.2}
                )
            
            # 设置交互选项
            nt.set_options("""
            {
                "nodes": {
                    "shape": "dot",
                    "scaling": {
                        "min": 20,
                        "max": 60,
                        "label": { "min": 14, "max": 30, "drawThreshold": 12, "maxVisible": 20 }
                    },
                    "font": {
                        "size": 14,
                        "face": "Arial"
                    }
                },
                "edges": {
                    "length": 200,
                    "width": 1.5,
                    "smooth": {
                        "type": "curvedCW",
                        "roundness": 0.2
                    },
                    "font": {
                        "size": 12,
                        "align": "middle"
                    },
                    "color": {"inherit": "both"},
                    "arrows": {
                        "to": {"enabled": true, "scaleFactor": 0.5}
                    }
                },
                "physics": {
                    "stabilization": {
                        "enabled": true,
                        "iterations": 1000,
                        "updateInterval": 50
                    },
                    "barnesHut": {
                        "gravitationalConstant": -2000,
                        "springLength": 200,
                        "springConstant": 0.015,
                        "damping": 0.09,
                        "avoidOverlap": 0.1
                    }
                },
                "interaction": {
                    "hover": true,
                    "tooltipDelay": 200,
                    "hideEdgesOnDrag": true,
                    "navigationButtons": true,
                    "keyboard": true,
                    "zoomView": true
                }
            }
            """)
            
            # 保存为HTML文件
            output_path = os.path.join(self.output_dir, file_name)
            nt.save_graph(output_path)
            
            # 增强HTML可视化效果
            self._enhance_html_visualization(output_path, node_types, color_map, G)
            
            logger.info(f"成功创建交互式知识图谱: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"创建交互式知识图谱失败: {str(e)}")
            raise
    
    def _adjust_color(self, hex_color, factor):
        """
        调整颜色的明度
        
        Args:
            hex_color (str): 十六进制颜色代码
            factor (float): 调整因子 (-1.0 到 1.0)
            
        Returns:
            str: 调整后的十六进制颜色代码
        """
        # 转换十六进制到RGB
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # 转换到HSV
        hsv = colorsys.rgb_to_hsv(rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0)
        
        # 调整明度
        new_v = max(0, min(1, hsv[2] * (1 + factor)))
        
        # 转换回RGB
        rgb = colorsys.hsv_to_rgb(hsv[0], hsv[1], new_v)
        
        # 转换回十六进制
        return "#{:02x}{:02x}{:02x}".format(
            int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255)
        )

    def _enhance_html_visualization(self, html_path, node_types, color_map, G):
        """
        增强HTML可视化效果
        
        Args:
            html_path (str): HTML文件路径
            node_types (dict): 节点类型字典
            color_map (dict): 颜色映射
            G (nx.DiGraph): 图对象
        """
        try:
            with open(html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # 添加现代化的样式和字体
            modern_styles = """
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #fafafa;
                    color: #2c3e50;
                }
                
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.1);
                    padding: 24px;
                }
                
                .header {
                    margin-bottom: 24px;
                    padding-bottom: 16px;
                    border-bottom: 1px solid #eee;
                }
                
                .title {
                    font-size: 24px;
                    font-weight: 600;
                    color: #1a202c;
                    margin: 0 0 8px 0;
                }
                
                .stats {
                    display: flex;
                    gap: 24px;
                    margin-bottom: 24px;
                    flex-wrap: wrap;
                }
                
                .stat-card {
                    background: white;
                    border-radius: 8px;
                    padding: 16px;
                    flex: 1;
                    min-width: 200px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                }
                
                .stat-title {
                    font-size: 14px;
                    color: #64748b;
                    margin-bottom: 8px;
                }
                
                .stat-value {
                    font-size: 24px;
                    font-weight: 600;
                    color: #1a202c;
                }
                
                .legend {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 12px;
                    margin-bottom: 24px;
                }
                
                .legend-item {
                    display: flex;
                    align-items: center;
                    padding: 8px 12px;
                    background: white;
                    border-radius: 6px;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
                }
                
                .color-dot {
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    margin-right: 8px;
                }
                
                .legend-label {
                    font-size: 14px;
                    color: #4a5568;
                }
                
                .legend-count {
                    margin-left: 8px;
                    padding: 2px 6px;
                    background: #f1f5f9;
                    border-radius: 4px;
                    font-size: 12px;
                    color: #64748b;
                }
                
                #mynetwork {
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
                }
                
                .vis-tooltip {
                    font-family: 'Inter', sans-serif !important;
                    border-radius: 8px !important;
                    box-shadow: 0 4px 16px rgba(0,0,0,0.1) !important;
                }
            </style>
            """
            
            # 在head标签中添加样式
            html_content = html_content.replace('</head>', f'{modern_styles}</head>')
            
            # 创建统计信息和图例HTML
            stats_html = f"""
            <div class="container">
                <div class="header">
                    <h1 class="title">知识图谱可视化</h1>
                </div>
                
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-title">节点总数</div>
                        <div class="stat-value">{G.number_of_nodes()}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">关系总数</div>
                        <div class="stat-value">{G.number_of_edges()}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-title">节点类型数</div>
                        <div class="stat-value">{len(node_types)}</div>
                    </div>
                </div>
                
                <div class="legend">
            """
            
            # 添加图例项
            for label in node_types.keys():
                count = sum(1 for _, attr in G.nodes(data=True) 
                          if attr.get('labels', '').startswith(label))
                stats_html += f"""
                    <div class="legend-item">
                        <span class="color-dot" style="background-color: {color_map[label]}"></span>
                        <span class="legend-label">{label}</span>
                        <span class="legend-count">{count}</span>
                    </div>
                """
            
            stats_html += """
                </div>
            </div>
            """
            
            # 在body开始处添加统计信息
            html_content = html_content.replace('<body>', f'<body>{stats_html}')
            
            # 写回文件
            with open(html_path, 'w', encoding='utf-8') as file:
                file.write(html_content)
                
        except Exception as e:
            logger.error(f"增强HTML可视化失败: {str(e)}")
    
    def create_static_graph(self, file_name="knowledge_graph.png", limit=1000, 
                          node_labels=None, rel_types=None, figsize=(16, 12)):
        """
        创建静态知识图谱图像
        
        Args:
            file_name (str, optional): 输出文件名
            limit (int, optional): 限制节点数量
            node_labels (list, optional): 节点标签过滤
            rel_types (list, optional): 关系类型过滤
            figsize (tuple, optional): 图像尺寸
            
        Returns:
            str: 输出文件路径
        """
        try:
            # 获取图数据
            nodes, relationships = self._fetch_graph_data(limit, node_labels, rel_types)
            
            # 创建NetworkX图
            G = self._create_networkx_graph(nodes, relationships)
            
            # 获取节点类型的统计信息，用于分配不同颜色
            node_types = {}
            for node, attrs in G.nodes(data=True):
                labels = attrs.get('labels', '')
                primary_label = labels.split(';')[0] if labels else 'Unknown'
                if primary_label not in node_types:
                    node_types[primary_label] = len(node_types)
            
            # 创建颜色映射
            colors = ["#3da4ab", "#f26d5b", "#c64191", "#7a306c", "#ffce30", 
                    "#8ac6d1", "#fe7f2d", "#619b8a", "#233d4d", "#fcca46"]
            color_map = {label: colors[i % len(colors)] for i, label in enumerate(node_types.keys())}
            
            # 绘制静态图
            plt.figure(figsize=figsize)
            pos = nx.spring_layout(G, k=0.8, iterations=100, seed=42)
            
            # 根据节点类型分配颜色
            node_colors = []
            for node in G.nodes():
                labels = G.nodes[node].get('labels', '')
                primary_label = labels.split(';')[0] if labels else 'Unknown'
                node_colors.append(color_map.get(primary_label, "#7eb0d5"))
            
            # 绘制节点
            nx.draw_networkx_nodes(G, pos, node_size=800, node_color=node_colors, alpha=0.8)
            
            # 绘制边
            nx.draw_networkx_edges(G, pos, width=1.2, alpha=0.6, 
                                edge_color='gray', arrows=True, arrowsize=15)
            
            # 添加节点标签
            node_labels = {node: G.nodes[node].get('name', f"Node-{node}") for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels=node_labels, 
                                  font_size=8, font_family='sans-serif')
            
            # 添加边标签
            edge_labels = {(u, v): G.edges[u, v].get('type', '') for u, v in G.edges()}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, 
                                       font_size=6, alpha=0.7)
            
            plt.title('知识图谱可视化', fontsize=20)
            plt.axis('off')
            
            # 保存图像
            output_path = os.path.join(self.output_dir, file_name)
            plt.savefig(output_path, format='png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"成功创建静态知识图谱: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"创建静态知识图谱失败: {str(e)}")
            raise
    
    def export_csv_files(self, nodes_file="nodes.csv", edges_file="edges.csv", 
                       limit=1000, node_labels=None, rel_types=None):
        """
        导出CSV文件
        
        Args:
            nodes_file (str, optional): 节点文件名
            edges_file (str, optional): 边文件名
            limit (int, optional): 限制节点数量
            node_labels (list, optional): 节点标签过滤
            rel_types (list, optional): 关系类型过滤
            
        Returns:
            tuple: (节点文件路径, 边文件路径)
        """
        try:
            # 获取图数据
            nodes, relationships = self._fetch_graph_data(limit, node_labels, rel_types)
            
            # 创建NetworkX图
            G = self._create_networkx_graph(nodes, relationships)
            
            # 导出节点CSV
            nodes_path = os.path.join(self.output_dir, nodes_file)
            with open(nodes_path, 'w', encoding='utf-8', newline='') as f:
                f.write("id,name,type\n")
                for node_id, attrs in G.nodes(data=True):
                    name = attrs.get('name', f"Node-{node_id}")
                    labels = attrs.get('labels', '')
                    primary_label = labels.split(';')[0] if labels else 'Unknown'
                    f.write(f"{node_id},{name},{primary_label}\n")
            
            # 导出边CSV
            edges_path = os.path.join(self.output_dir, edges_file)
            with open(edges_path, 'w', encoding='utf-8', newline='') as f:
                f.write("source,target,relationship\n")
                for u, v, attrs in G.edges(data=True):
                    rel_type = attrs.get('type', '')
                    f.write(f"{u},{v},{rel_type}\n")
            
            logger.info(f"成功导出CSV文件: {nodes_path}, {edges_path}")
            return nodes_path, edges_path
        except Exception as e:
            logger.error(f"导出CSV文件失败: {str(e)}")
            raise

# 默认可视化器实例，用于全局共享
default_visualizer = None

def get_visualizer():
    """获取默认可视化器实例"""
    global default_visualizer
    if default_visualizer is None:
        default_visualizer = GraphVisualizer()
    return default_visualizer 
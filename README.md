# GraphRAG-Neo4j

基于Neo4j的知识图谱增强检索生成系统（Graph-enhanced RAG）

## 项目简介

GraphRAG-Neo4j 是一个结合知识图谱与检索增强生成（RAG）的系统，通过Neo4j图数据库和大语言模型（LLM）提供更精准的信息检索和问答能力。该项目在传统RAG系统基础上引入知识图谱，利用实体关系增强检索质量，实现更深层次的语义理解和推理能力。

### 核心特点

- **知识图谱自动构建**：从文本文档自动提取实体与关系，构建结构化知识图谱
- **图增强检索**：结合向量相似度与图结构关系进行多维度检索
- **优雅的可视化**：提供美观、交互式的知识图谱可视化，支持自适应布局和动态交互
- **模块化设计**：灵活的组件架构，支持自定义扩展

## 系统架构

项目基于`neo4j_graphrag`核心库构建，并通过`graphrag`模块提供更高级的抽象与扩展：

```
graphrag-neo4j/
├── config/               # 配置管理
├── graphrag/             # 扩展模块
│   ├── database/         # 数据库连接管理
│   ├── models/           # 模型管理(LLM, 嵌入模型)
│   ├── knowledge_graph/  # 知识图谱构建与索引
│   ├── rag/              # RAG实现
│   └── visualization/    # 可视化功能
├── data/                 # 数据文件
├── examples/             # 使用示例
├── scripts/              # 辅助脚本
├── utils/                # 工具函数
├── env-expample          # 环境变量示例文件
├── main.py               # 主程序入口
└── pyproject.toml        # 项目配置
```

## 安装与配置

### 环境要求

- Python 3.8+
- Neo4j 5.0+（支持向量索引）
- APOC插件（用于图数据处理）
- uv（现代化Python包管理工具）

### 安装步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/username/graphrag-neo4j.git
   cd graphrag-neo4j
   ```

2. 安装 uv（如果尚未安装）
   ```bash
   # 使用 curl 安装
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # 或使用 pip 安装
   pip install uv
   ```

3. 创建并激活虚拟环境
   ```bash
   uv venv
   source .venv/bin/activate  # Linux/macOS
   # 或
   .venv\Scripts\activate     # Windows
   ```

4. 安装依赖
   ```bash
   uv pip install -r requirements.txt
   ```

5. 配置环境变量
   复制环境变量示例文件并修改：
   ```bash
   cp env-expample .env
   ```
   
   编辑`env-example`文件，配置以下参数,配置完成请重命名为`.env`：
   ```
   # Neo4j数据库配置
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password

   # OpenAI配置
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4-turbo

   # 嵌入模型配置
   EMBEDDING_API_KEY=your_embedding_api_key
   EMBEDDING_URL=https://api.openai.com/v1/embeddings
   EMBEDDING_MODEL=text-embedding-ada-002
   ```

## 使用方法

### 快速开始

1. 知识图谱构建
   ```python
   from graphrag.knowledge_graph.builder import get_kg_builder
   import asyncio

   async def build_kg():
       kg_builder = get_kg_builder()
       result = await kg_builder.build_from_file("path/to/document.txt")
       print(f"构建结果: {result}")

   asyncio.run(build_kg())
   ```

2. 索引创建
   ```python
   from graphrag.knowledge_graph.indexer import get_index_manager

   index_manager = get_index_manager()
   index_manager.create_all_indexes()
   ```

3. RAG问答
   ```python
   from graphrag.rag.graph_rag import get_graph_rag_system

   rag_system = get_graph_rag_system()
   
   # 基础向量检索
   result = rag_system.search("您的问题", use_graph=False)
   print(f"基础检索答案: {result.answer}")
   
   # 图增强检索
   result = rag_system.search("您的问题", use_graph=True)
   print(f"图增强检索答案: {result.answer}")
   
   # 比较两种检索结果
   basic_result, graph_result = rag_system.compare_search("您的问题")
   ```

4. 知识图谱可视化
   ```python
   from graphrag.visualization.graph_visualizer import get_visualizer

   visualizer = get_visualizer()
   
   # 创建交互式HTML可视化
   html_path = visualizer.create_interactive_graph(
       height="800px",  # 设置图表高度
       width="100%",    # 设置图表宽度
       node_labels=["Person", "Organization"],  # 可选的节点类型过滤
       rel_types=["WORKS_FOR", "KNOWS"]        # 可选的关系类型过滤
   )
   print(f"交互式图表已保存至: {html_path}")
   
   # 创建静态PNG图像
   png_path = visualizer.create_static_graph(
       figsize=(16, 12),  # 设置图像尺寸
       node_labels=None,  # 显示所有节点类型
       rel_types=None     # 显示所有关系类型
   )
   print(f"静态图表已保存至: {png_path}")
   ```

### 可视化特性

知识图谱可视化模块提供了丰富的功能和优雅的视觉效果：

- **智能布局**：采用优化的力导向算法，自动调整节点位置，避免重叠
- **和谐配色**：使用基于黄金比例的配色方案，确保视觉美感
- **交互体验**：
  - 节点悬停显示详细信息
  - 平滑的缩放和拖拽
  - 关系曲线优化
  - 节点分类图例
  - 实时统计信息
- **响应式设计**：适配不同屏幕尺寸，支持移动设备
- **可定制性**：支持自定义节点样式、关系样式和布局参数

### 运行示例程序

```bash
python main.py
```

查看更多示例代码请参考`examples`目录。

## 高级功能

### 自定义知识图谱架构

可以在`config/settings.py`中自定义实体类型和关系类型：

```python
# 知识图谱配置
NODE_LABELS = ["Document", "Person", "Organization", "Location", "Concept", "Event"]
REL_TYPES = ["MENTIONS", "RELATED_TO", "PART_OF", "LOCATED_IN", "CREATED_BY"]
```

### 自定义提示模板

可以通过模板管理器创建和使用自定义提示模板：

```python
from graphrag.rag.templates import get_template_manager

template_manager = get_template_manager()
template_manager.add_template(
    "custom_template", 
    """
    基于以下上下文资料，请用简洁的语言回答问题。
    
    问题: {query_text}
    
    上下文资料:
    {context}
    
    简洁回答:
    """
)

# 使用自定义模板
rag_system = get_graph_rag_system()
result = rag_system.search("您的问题", template_name="custom_template")
```

### 可视化配置

可以通过传递参数来自定义可视化效果：

```python
visualizer = get_visualizer()

# 自定义交互式可视化
html_path = visualizer.create_interactive_graph(
    height="800px",
    width="100%",
    node_labels=["Person", "Organization"],
    rel_types=["WORKS_FOR", "KNOWS"],
    # 高级配置选项
    options={
        "nodes": {
            "shape": "dot",
            "size": 30,
            "font": {"size": 14},
            "shadow": True
        },
        "edges": {
            "smooth": {"type": "curvedCW"},
            "arrows": {"to": {"enabled": True}},
            "color": {"inherit": "both"}
        },
        "physics": {
            "stabilization": {"iterations": 1000},
            "barnesHut": {
                "springLength": 200,
                "springConstant": 0.015,
                "damping": 0.09
            }
        }
    }
)
```

## 贡献指南

欢迎贡献代码、报告问题或提出新功能建议。请遵循以下步骤：

1. Fork 本仓库
2. 创建新分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'Add some feature'`)
4. 推送到分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

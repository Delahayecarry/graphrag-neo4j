# GraphRAG-Neo4j

基于Neo4j的知识图谱增强检索生成系统（Graph-enhanced RAG），支持Neo4j和graphrag官方库两种模式。

## 项目简介

GraphRAG-Neo4j 是一个结合知识图谱与检索增强生成（RAG）的系统，通过Neo4j图数据库和大语言模型（LLM）提供更精准的信息检索和问答能力。该项目在传统RAG系统基础上引入知识图谱，利用实体关系增强检索质量，实现更深层次的语义理解和推理能力。

### 核心特点

- **知识图谱自动构建**：从文本文档自动提取实体与关系，构建结构化知识图谱
- **图增强检索**：结合向量相似度与图结构关系进行多维度检索
- **优雅的可视化**：提供美观、交互式的知识图谱可视化，支持自适应布局和动态交互
- **双模式支持**：同时支持Neo4j模式和graphrag官方命令行模式
- **模块化设计**：灵活的组件架构，支持自定义扩展

## 系统架构

项目基于`neo4j_graphrag`核心库和`graphrag`官方库构建：

```
graphrag-neo4j/
├── config/                       # 配置管理
├── graphragdiy/                  # 核心模块
│   ├── database/                 # 数据库连接管理
│   ├── models/                   # 模型管理(LLM, 嵌入模型)
│   ├── knowledge_graph/          # 知识图谱构建与索引
│   ├── rag/                      # RAG实现
│   ├── visualization/            # 可视化功能
│   └── graphrag_official/        # graphrag官方库集成
├── data/                         # 数据文件
├── output/                       # 输出文件
├── examples/                     # 使用示例
├── scripts/                      # 辅助脚本
├── utils/                        # 工具函数
├── main.py                       # 主程序入口
├── env-expample                  # 环境变量示例文件
└── pyproject.toml                # 项目配置
```

## 安装与配置

### 环境要求

- Python 3.10+
- Neo4j 5.0+（仅Neo4j模式需要，支持向量索引）
- APOC插件（仅Neo4j模式需要，用于图数据处理）
- uv（现代化Python包管理工具）

### 安装步骤

1. 克隆仓库
   ```bash
   git clone https://github.com/your-username/graphrag-neo4j.git
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
   uv pip install -e .  # 安装项目及其依赖
   ```

5. 配置环境变量
   复制环境变量示例文件并修改：
   ```bash
   cp env-expample .env
   ```
   
   编辑`.env`文件，配置以下参数：
   ```
   # Neo4j数据库配置
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_password

   # OpenAI配置
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4-turbo
   OPENAI_TEMPERATURE=0.7
   OPENAI_MAX_TOKENS=4096
   OPENAI_TOP_P=1.0

   # 嵌入模型配置
   EMBEDDING_API_KEY=your_embedding_api_key
   EMBEDDING_URL=https://api.openai.com/v1/embeddings
   EMBEDDING_MODEL=text-embedding-ada-002
   ```

## 使用方法

### 运行模式

项目支持两种模式：

1. **Neo4j模式**：使用Neo4j数据库存储知识图谱和向量索引
   ```bash
   uv run neo4j_main.py 
   ```

2. **graphrag官方模式**：使用graphrag官方命令行工具
   ```bash
   uv run graphrag_main.py
   ```

### 命令行参数

- `--mode`: 运行模式，可选 `neo4j` 或 `graphrag`，默认为 `neo4j`
- `--data-dir`: 输入数据目录路径，包含要处理的文本文件
- `--root-dir`: graphrag模式的工作目录路径，默认为 `./ragtest`

### 交互式问答

无论使用哪种模式，构建索引后都会自动进入交互式问答模式，您可以直接输入问题进行查询。

```
🔍 请输入您的问题: 什么是知识图谱？

🔄 正在处理查询...

📝 基础向量检索结果:
⏱️  处理时间: 1.25秒
知识图谱是一种结构化的知识表示方法...

📝 图增强检索结果:
⏱️  处理时间: 1.76秒
知识图谱是一种将实体和它们之间的关系以图结构形式组织的数据库...
```

### 编程接口

#### Neo4j模式

1. 知识图谱构建
   ```python
   from graphragdiy.knowledge_graph.builder import get_kg_builder
   import asyncio

   async def build_kg():
       kg_builder = get_kg_builder()
       result = await kg_builder.build_from_file("path/to/document.txt")
       print(f"构建结果: {result}")

   asyncio.run(build_kg())
   ```

2. 索引创建
   ```python
   from graphragdiy.knowledge_graph.indexer import get_index_manager

   index_manager = get_index_manager(mode="neo4j")
   index_manager.create_all_indexes()
   ```

3. RAG问答
   ```python
   from graphragdiy.rag.graph_rag import get_graph_rag_system

   rag_system = get_graph_rag_system()
   
   # 基础向量检索
   result = rag_system.search("您的问题", use_graph=False)
   print(f"基础检索答案: {result.answer}")
   
   # 图增强检索
   result = rag_system.search("您的问题", use_graph=True)
   print(f"图增强检索答案: {result.answer}")
   ```

#### graphrag官方模式

```python
from graphragdiy.graphrag_official import indexer

# 创建graphrag索引构建器
graphrag_indexer = indexer("./ragtest")

# 处理文件并构建索引
graphrag_indexer.process_files(["path/to/document.txt"])

# 运行查询
result = graphrag_indexer.run_query("您的问题", method="global")
print(result)
```

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
from graphragdiy.rag.templates import get_template_manager

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

### 知识图谱可视化

```python
from graphragdiy.visualization.graph_visualizer import get_visualizer

visualizer = get_visualizer()

# 创建交互式HTML可视化
html_path = visualizer.create_interactive_graph(
    file_name="knowledge_graph.html",
    limit=1000,  # 限制节点数量
    node_labels=["Person", "Organization"],  # 可选的节点类型过滤
    rel_types=["WORKS_FOR", "KNOWS"]        # 可选的关系类型过滤
)

# 创建静态PNG图像
png_path = visualizer.create_static_graph(
    file_name="knowledge_graph.png",
    limit=500  # 限制节点数量
)

# 导出CSV数据
nodes_path, edges_path = visualizer.export_csv_files(
    nodes_file="nodes.csv",
    edges_file="edges.csv"
)
```

## 开发与贡献

### 使用uv进行依赖管理

项目使用uv替代传统的pip进行依赖管理，以获得更好的性能和可靠性：

```bash
# 安装指定包
uv pip install package-name

# 安装当前项目
uv pip install -e .

# 更新依赖
uv pip install -U package-name

# 查看已安装包
uv pip freeze
```

### 添加新功能

1. 创建并切换到新分支
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. 实现功能并提交
   ```bash
   git add .
   git commit -m "Add your feature description"
   ```

3. 推送分支并创建合并请求
   ```bash
   git push origin feature/your-feature-name
   ```

## 许可证

MIT

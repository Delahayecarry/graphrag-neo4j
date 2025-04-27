# 1. 导入必要库
import os
import asyncio
from neo4j import GraphDatabase
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.retrievers import VectorRetriever, VectorCypherRetriever
from neo4j_graphrag.indexes import create_vector_index
from neo4j_graphrag.generation import RagTemplate
from neo4j_graphrag.generation.graphrag import GraphRAG

# 2. 设置环境变量和连接参数
os.environ["OPENAI_API_KEY"] = "sk-proj-1234567890"
NEO4J_URI = "neo4j://localhost:7687"  # 或者您的AuraDB URI
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "your_password"

# 3. 连接到Neo4j数据库
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# 4. 设置LLM和嵌入模型
llm = OpenAILLM(
    model_name="gpt-4o",
    model_params={
        "response_format": {"type": "json_object"},
        "temperature": 0
    }
)
embedder = OpenAIEmbeddings()

# 5. 定义知识图谱schema
node_labels = ["Document", "Person", "Organization", "Location", "Concept", "Event"]
rel_types = ["MENTIONS", "RELATED_TO", "PART_OF", "LOCATED_IN", "CREATED_BY"]

# 6. 创建知识图谱构建流程
kg_builder = SimpleKGPipeline(
    llm=llm,
    driver=driver,
    embedder=embedder,
    entities=node_labels,
    relations=rel_types,
    from_pdf=False  # 如果处理PDF文件，设置为True
)

# 7. 构建知识图谱(异步方式)
async def build_knowledge_graph(file_path):
    result = await kg_builder.run_async(file_path=file_path)
    print(f"处理结果: {result}")

# 8. 创建向量索引
def create_indexes():
    create_vector_index(
        driver, 
        name="text_embeddings", 
        label="Chunk",
        embedding_property="embedding", 
        dimensions=1536, 
        similarity_fn="cosine"
    )
    # 创建实体全文索引
    driver.execute_query(
        "CREATE FULLTEXT INDEX entity_index IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.name]"
    )

# 9. 设置检索器
def setup_retrievers():
    # 基础向量检索
    vector_retriever = VectorRetriever(
        driver,
        index_name="text_embeddings",
        embedder=embedder,
        return_properties=["text"]
    )
    
    # 向量+图遍历增强检索
    vector_cypher_retriever = VectorCypherRetriever(
        driver,
        index_name="text_embeddings",
        embedder=embedder,
        retrieval_query="""
        // 1. 以向量相似度获取初始Chunk节点
        WITH node AS chunk
        
        // 2. 从Chunk遍历到实体，然后获取相关关系
        MATCH (chunk)<-[:FROM_CHUNK]-()-[relList:!FROM_CHUNK]-{1,2}()
        UNWIND relList AS rel
        
        // 3. 收集文本块和关系
        WITH collect(DISTINCT chunk) AS chunks,
             collect(DISTINCT rel) AS rels
        
        // 4. 格式化返回上下文
        RETURN '=== 文本块 ===\n' + apoc.text.join([c in chunks | c.text], '\n---\n') + 
               '\n\n=== 知识图谱关系 ===\n' +
               apoc.text.join([r in rels | startNode(r).name + ' - ' + type(r) + 
               '(' + coalesce(r.details, '') + ')' + ' -> ' + endNode(r).name ], 
               '\n---\n') AS info
        """
    )
    
    return vector_retriever, vector_cypher_retriever

# 10. 创建GraphRAG实例
def create_rag_instances(retrievers):
    vector_retriever, vector_cypher_retriever = retrievers
    
    # 定义提示模板
    rag_template = RagTemplate(template='''
    根据下面的上下文回答问题。只使用上下文中的信息回答，不要添加不在上下文中的信息。

    # 问题:
    {query_text}

    # 上下文:
    {context}

    # 回答:
    ''', expected_inputs=['query_text', 'context'])
    
    # 创建GraphRAG实例
    vector_rag = GraphRAG(
        llm=llm, 
        retriever=vector_retriever, 
        prompt_template=rag_template
    )
    
    vector_cypher_rag = GraphRAG(
        llm=llm, 
        retriever=vector_cypher_retriever, 
        prompt_template=rag_template
    )
    
    return vector_rag, vector_cypher_rag

# 主函数
async def main():
    # 构建知识图谱
    pdf_files = ["your_document1.pdf", "your_document2.pdf"]
    for file in pdf_files:
        await build_knowledge_graph(file)
    
    # 创建索引
    create_indexes()
    
    # 设置检索器
    retrievers = setup_retrievers()
    
    # 创建RAG实例
    rag_instances = create_rag_instances(retrievers)
    
    # 测试查询
    vector_rag, vector_cypher_rag = rag_instances
    query = "您的问题"
    
    print("基础向量检索结果:")
    print(vector_rag.search(query, retriever_config={'top_k': 5}).answer)
    
    print("\n向量+图遍历增强检索结果:")
    print(vector_cypher_rag.search(query, retriever_config={'top_k': 5}).answer)

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())
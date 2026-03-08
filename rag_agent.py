"""
LangGraph-based RAG pipeline for agricultural advisory system.
Handles retrieval, LLM generation, and structured response formatting.
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, BaseMessage

from config import settings
from logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger("rag_agent")

# =========================
# Initialize Components
# =========================


def initialize_embeddings() -> HuggingFaceEmbeddings:
    """Initialize HuggingFace embeddings model."""
    try:
        logger.info(
            "Initializing embeddings",
            extra={"model": settings.EMBEDDING_MODEL}
        )
        embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        logger.info("Embeddings initialized successfully")
        return embeddings
    except Exception as e:
        logger.error(f"Failed to initialize embeddings: {str(e)}")
        raise


def initialize_vector_store(embeddings: HuggingFaceEmbeddings) -> FAISS:
    """Initialize FAISS vector store."""
    try:
        if not Path(settings.VECTOR_DB_PATH).exists():
            logger.error(
                f"Vector database not found at {settings.VECTOR_DB_PATH}"
            )
            raise FileNotFoundError(
                f"Vector database not found: {settings.VECTOR_DB_PATH}"
            )
        
        logger.info(
            "Loading vector database",
            extra={"path": settings.VECTOR_DB_PATH}
        )
        vector_store = FAISS.load_local(
            settings.VECTOR_DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        logger.info("Vector database loaded successfully")
        return vector_store
    except Exception as e:
        logger.error(f"Failed to load vector database: {str(e)}")
        raise


def initialize_llm() -> ChatGroq:
    """Initialize Groq LLM."""
    try:
        if not settings.GROQ_API_KEY:
            logger.error("GROQ_API_KEY not set in environment")
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        logger.info(
            "Initializing Groq LLM",
            extra={"model": settings.GROQ_MODEL, "temperature": settings.LLM_TEMPERATURE}
        )
        llm = ChatGroq(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            temperature=settings.LLM_TEMPERATURE,
        )
        logger.info("Groq LLM initialized successfully")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {str(e)}")
        raise


# Initialize components
try:
    embeddings = initialize_embeddings()
    vector_store = initialize_vector_store(embeddings)
    llm = initialize_llm()
except Exception as e:
    logger.critical(f"Failed to initialize RAG components: {str(e)}")
    raise

# =========================
# System Prompt
# =========================

SYSTEM_PROMPT = """
You are an AI Agricultural Advisory Assistant.

Your task is to provide clear, structured, and well-organized farming advice.

When responding:
- Do NOT dump raw retrieved text.
- Rewrite the answer in clean, structured format.
- Use headings and bullet points.
- Keep paragraphs short and readable.
- Organize answers into sections such as:
    - Overview
    - Step-by-step Guidelines
    - Important Notes
    - Best Practices

Always make the response clean and professional.
"""

sys_msg = SystemMessage(content=SYSTEM_PROMPT)

# =========================
# Retriever Tool
# =========================

# =========================
# Retriever Tool
# =========================

@tool
def retriever(query: str) -> str:
    """
    Retrieve relevant farming documents from the vector database.
    Uses semantic similarity to find the most relevant documents.
    """
    try:
        logger.info(
            "Retrieving documents",
            extra={"query": query, "k": settings.RETRIEVER_K}
        )
        
        docs = vector_store.similarity_search(query, k=settings.RETRIEVER_K)
        
        logger.info(
            "Documents retrieved successfully",
            extra={"num_docs": len(docs), "query": query}
        )
        
        return "\n\n".join(doc.page_content for doc in docs)
    
    except Exception as e:
        logger.error(
            f"Error during retrieval: {str(e)}",
            extra={"query": query, "error": str(e)}
        )
        raise


tools = [retriever]
llm_with_tool = llm.bind_tools(tools)

# =========================
# Assistant Node
# =========================

def assistant_node(state: MessagesState) -> Dict[str, Any]:
    """
    Assistant node: processes messages and generates responses.
    Invokes LLM with tool binding capabilities.
    """
    try:
        logger.info(
            "Processing message in assistant node",
            extra={"num_messages": len(state.get("messages", []))}
        )
        
        response = llm_with_tool.invoke([sys_msg] + state["messages"])
        
        logger.info("Assistant response generated successfully")
        return {"messages": response}
    
    except Exception as e:
        logger.error(
            f"Error in assistant node: {str(e)}",
            extra={"error": str(e)}
        )
        raise


# =========================
# Build LangGraph
# =========================

def build_rag_graph() -> Any:
    """Build and compile the RAG LangGraph."""
    
    try:
        logger.info("Building RAG graph")
        
        builder = StateGraph(MessagesState)
        
        builder.add_node("assistant", assistant_node)
        builder.add_node("tools", ToolNode(tools))
        
        builder.add_edge(START, "assistant")
        builder.add_conditional_edges("assistant", tools_condition)
        builder.add_edge("tools", "assistant")
        
        graph = builder.compile()
        
        logger.info("RAG graph built and compiled successfully")
        return graph
    
    except Exception as e:
        logger.error(f"Error building RAG graph: {str(e)}")
        raise


# Build the graph
try:
    graph = build_rag_graph()
except Exception as e:
    logger.critical(f"Failed to build RAG graph: {str(e)}")
    raise


# =========================
# Public API Functions
# =========================

def query_rag(question: str) -> Dict[str, Any]:
    """
    Query the RAG system with a farming question.
    
    Args:
        question: The farming question to answer
        
    Returns:
        Dictionary with answer and metadata
    """
    
    try:
        logger.info("Processing RAG query", extra={"question": question})
        
        result = graph.invoke({
            "messages": [{"role": "user", "content": question}]
        })
        
        answer = result["messages"][-1].content if result.get("messages") else ""
        
        logger.info(
            "RAG query completed successfully",
            extra={
                "question": question,
                "answer_length": len(answer),
                "num_messages": len(result.get("messages", [])),
            }
        )
        
        return {
            "question": question,
            "answer": answer,
            "status": "success",
        }
    
    except Exception as e:
        logger.error(
            f"Error processing RAG query: {str(e)}",
            extra={"question": question, "error": str(e)}
        )
        return {
            "question": question,
            "answer": f"Error: {str(e)}",
            "status": "error",
        }

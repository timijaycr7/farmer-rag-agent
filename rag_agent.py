import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage

# =========================
# Load Embeddings & Vector DB
# =========================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

vectorStore = FAISS.load_local(
    "farmer_vector_db",
    embeddings,
    allow_dangerous_deserialization=True
)

# =========================
# Load Groq LLM
# =========================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0
)

# =========================
# System Prompt (Guardrails)
# =========================

sys_prompt = """
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

sys_msg = SystemMessage(content=sys_prompt)

# =========================
# Retriever Tool
# =========================

@tool
def retriever(query: str) -> str:
    """
    Retrieve relevant farming documents from the vector database.
    """
    docs = vectorStore.similarity_search(query, k=5)
    return "\n\n".join(doc.page_content for doc in docs)

tools = [retriever]
llm_with_tool = llm.bind_tools(tools)

# =========================
# Assistant Node
# =========================

def assistant(state: MessagesState):
    response = llm_with_tool.invoke([sys_msg] + state["messages"])
    return {"messages": response}

# =========================
# Build LangGraph
# =========================

builder = StateGraph(MessagesState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

graph = builder.compile()
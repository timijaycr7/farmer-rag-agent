from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from rag_agent import graph
import os

app = FastAPI(title="Farmer RAG Agent", description="AI-powered agricultural advisory system")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class Query(BaseModel):
    question: str

@app.get("/")
def root():
    """Serve the main chat interface"""
    return FileResponse("static/index.html")

@app.post("/ask")
def ask(q: Query):
    """Ask a farming question and get AI-powered answers from agricultural documents"""
    result = graph.invoke({
        "messages": [HumanMessage(content=q.question)]
    })

    return {
        "answer": result["messages"][-1].content
    }
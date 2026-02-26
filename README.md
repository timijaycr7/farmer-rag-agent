# Farmer RAG Agent

<img width="803" height="708" alt="image" src="https://github.com/user-attachments/assets/9273bfb6-689f-4daa-af77-666ab99d37b1" />


An AI-powered agricultural advisory system that combines retrieval-augmented generation (RAG) with a clean chat UI. It answers farming questions using a local FAISS vector database of agricultural documents and a Groq-hosted LLM, then presents the response in a structured, readable format.

## What This Project Does

- Accepts farming questions through a web chat interface or API.
- Retrieves relevant agriculture content from a local FAISS vector store.
- Uses a Groq LLM to generate concise, structured advice.
- Renders responses with markdown formatting for easy reading.

## How It Works

1. **User asks a question** in the UI or via the `/ask` API.
2. **Retriever tool** searches the FAISS vector store for related documents.
3. **LLM response** is generated using a system prompt that enforces clean structure and readability.
4. **Frontend renders** markdown into headings, lists, tables, and code blocks.

## Tech Stack

- **Streamlit** for the web UI
- **LangGraph + LangChain** for tool-augmented generation
- **FAISS** as the local vector database
- **HuggingFace Embeddings** for semantic search
- **Groq LLM** for response generation

## Project Structure

```
app.py                  # Streamlit app
rag_agent.py            # LangGraph RAG pipeline
farmer_vector_db/       # FAISS vector store
requirements.txt        # Python dependencies
```

## Requirements

- Python 3.10+
- A Groq API key

## Setup

1. **Create a `.env` file** in the project root:

```
GROQ_API_KEY=your_api_key_here
```

2. **Install dependencies:**

```
pip install -r requirements.txt
```

3. **Run the app:**

```
streamlit run app.py
```

4. **Open the app:**

```
http://localhost:8501
```


## License

This project is provided as-is for educational and research use.

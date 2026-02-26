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

- **FastAPI** for the web server and API endpoints
- **LangGraph + LangChain** for tool-augmented generation
- **FAISS** as the local vector database
- **HuggingFace Embeddings** for semantic search
- **Groq LLM** for response generation
- **Static HTML/CSS/JS** frontend with markdown rendering

## Project Structure

```
app.py                  # FastAPI app and API endpoints
rag_agent.py            # LangGraph RAG pipeline
static/index.html       # Chat UI
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

3. **Run the server:**

```
uvicorn app:app --host 0.0.0.0 --port 8000
```

4. **Open the app:**

```
http://localhost:8000
```

## API Usage

POST `/ask`

**Request body:**

```json
{
	"question": "How can I improve soil fertility?"
}
```

**Response:**

```json
{
	"answer": "Overview..."
}
```


## License

This project is provided as-is for educational and research use.

import streamlit as st
from langchain_core.messages import HumanMessage
from rag_agent import graph

# Page configuration
st.set_page_config(
    page_title="Farmer RAG Agent",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("🌾 Farmer RAG Agent")
st.markdown("*Your AI-Powered Agricultural Advisory Assistant*")
st.divider()

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about farming, agriculture, and crop management..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            try:
                result = graph.invoke({
                    "messages": [HumanMessage(content=prompt)]
                })
                response = result["messages"][-1].content
                st.markdown(response)
                
                # Add assistant message to history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error: {str(e)}")
                error_msg = f"Sorry, there was an error processing your question: {str(e)}"
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
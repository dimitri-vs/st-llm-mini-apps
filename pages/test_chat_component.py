import streamlit as st
from components.chat_component import chat_component
from utils.anthropic_llm import stream_anthropic_completion

st.title("Chat Component Test")

# Initialize session state with pre-existing messages
if "messages" not in st.session_state:
    st.session_state.messages = [
        # {"role": "user", "content": "Tell me a joke."},
        # {"role": "assistant", "content": "Here's a classic:\n\nWhy don't scientists trust atoms? Because they make up everything! 😄"}
    ]

# Render the chat component

chat_component(
    messages_key="messages",
    response_stream=stream_anthropic_completion
)


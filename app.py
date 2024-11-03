import streamlit as st
from auth import check_password # if you want to use auth.py for authentication
from dotenv import load_dotenv
from build_info import BUILD_TIMESTAMP
from utils.anthropic_llm import stream_anthropic_completion
import os

# Load environment variables
load_dotenv()


st.set_page_config(
    page_title="Streamlit Landing Page App",
    page_icon="🛬",
    layout="wide"
)

st.success("👈 See various example apps in the sidebar")

st.title("🛬 App Landing Page")

# Initialize session state to create variables that persist across reruns
if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.title("💬 Claude Chat Demo")

# put the chat into a scrollable container
# an alternative option would be to nest everything under `with st.container(): ...`
chat_container = st.container(border=True, height=500)

# Display previous messages
for msg in st.session_state.messages:
    chat_container.chat_message(msg["role"]).write(msg["content"])

# Create empty placeholders for new messages
user_placeholder = chat_container.empty()
asst_placeholder = chat_container.empty()

# Get user input
user_prompt = chat_container.chat_input("Message Claude...")
if user_prompt:
    # Display user message
    user_placeholder.chat_message("user").write(user_prompt)
    asst_placeholder = asst_placeholder.chat_message("assistant").empty()

    # Prepare messages for Anthropic API format
    messages = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in st.session_state.messages
    ]
    messages.append({"role": "user", "content": user_prompt})

    # Stream the response
    response_content = ""
    for chunk in stream_anthropic_completion(messages):
        response_content += chunk
        asst_placeholder.write(response_content)

    # Save the conversation
    st.session_state.messages.extend([
        {"role": "user", "content": user_prompt},
        {"role": "assistant", "content": response_content}
    ])

st.markdown(f"<div style='text-align: center; color: gray; font-size: 0.8em; margin: -1em 0 -1em 0; line-height: 1;'>App Version: {BUILD_TIMESTAMP}</div>", unsafe_allow_html=True)

import os

import streamlit as st
from dotenv import load_dotenv

# from auth import check_password # if you want to use auth.py for authentication
from components.version_info import show_version_info
from build_info import BUILD_TIMESTAMP
from utils.anthropic_llm import stream_anthropic_completion

# Load environment variables
load_dotenv()


st.set_page_config(
    page_title="Streamlit Landing Page App",
    page_icon="🛬",
    layout="wide"
)

show_version_info() # Show version info in sidebar

# Initialize session state to create variables that persist across reruns
if "messages" not in st.session_state:
    st.session_state["messages"] = []

st.title("💬 Claude Chat Demo")

# Add delete last exchange button
col1, col2 = st.columns([0.85, 0.15])
with col2:
    if st.button("🗑️ Delete Last", disabled=len(st.session_state.messages) < 2):
        # Remove last two messages (user + assistant)
        st.session_state.messages = st.session_state.messages[:-2]
        st.rerun()

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
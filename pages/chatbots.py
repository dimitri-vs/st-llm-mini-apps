import streamlit as st
from auth import check_password # if you want to use auth.py for authentication
from utils import stream_chat_completion, get_chat_completion

# Constants
MODEL = "gpt-4-1106-preview"

st.set_page_config(
    page_title="Streamlit Chat Demo",
    page_icon="💬",
    layout="wide"
)

# Authenticate user (optional, see `auth.py`)
# if not check_password():
#     st.stop()

# Initialize session state to create variables that persist across reruns
if "messages" not in st.session_state:
    # Initialize the session state
    st.session_state["messages"] = []


st.title("💬 Streamlit Chat Demo")

# put the chat into a scrollable container
# an alternative option would be to nest everything under `with st.container(): ...`
chat_container = st.container(border=True, height=500)

# display previous messages, if any
for msg in st.session_state.messages:
        chat_container.chat_message(msg["role"]).write(msg["content"])

# create empty position placeholders for new messages
user_placeholder = chat_container.empty()
asst_placeholder = chat_container.empty()

user_prompt = chat_container.chat_input(f"Message {MODEL}...")
if user_prompt:
    user_placeholder.chat_message("user").write(user_prompt)
    asst_placeholder = asst_placeholder.chat_message("assistant").empty()
    # send msg thread + user msg, stream response and update msg thread
    messages = st.session_state.messages
    messages.append({"role": "user", "content": user_prompt})
    response_content = asst_placeholder.write_stream(
        stream_chat_completion(MODEL, messages)
    )
    messages.append({"role": "assistant", "content": response_content})